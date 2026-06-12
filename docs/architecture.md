# Architecture — BizPlan-IA

> Architecture **agentic** déployée sur **Microsoft Azure**, optimisée pour la génération automatisée de business plans et le scoring de pertinence.
> Ce document explique **nos choix** et **nos arbitrages** (critère d'évaluation : *« Capacité à expliquer les choix : architecture, arbitrages, limites »*).

← Retour au [README](../README.md)

---

## 1. Principes directeurs

1. **Séparation des responsabilités** : l'IA *rédige et raisonne*, le backend *valide et calcule*. Le score de pertinence est calculé **côté code** (déterministe, auditable), jamais par l'IA seule.
2. **Services managés d'abord** : on ne gère pas de serveurs. On consomme du PaaS Azure pour réduire la charge ops d'un binôme.
3. **JSON partout** : contrat d'interface strict entre frontend, backend, IA et base. Validation systématique (Pydantic).
4. **L'IA ne hallucine pas de données** : interdiction d'inférer des chiffres non fournis (contrainte du cas). Tout est tracé et validé.
5. **Coût maîtrisé** : démonstrateur académique → on privilégie les tiers gratuits/serverless et l'extinction à la demande.

## 2. Vue d'ensemble

```
                         ┌─────────────────────────────────────────────┐
                         │                  AZURE                        │
                         │                                               │
  Utilisateur            │  ┌────────────────┐    ┌──────────────────┐  │
  (navigateur)  ───────▶ │  │ Azure Static   │    │ Azure Container  │  │
                         │  │ Web Apps       │───▶│ Apps (FastAPI)   │  │
                         │  │ (frontend)     │◀───│  backend + API   │  │
                         │  └────────────────┘    └────────┬─────────┘  │
                         │                                  │            │
                         │         ┌────────────────────────┼─────────┐ │
                         │         ▼                         ▼         │ │
                         │  ┌──────────────┐      ┌────────────────────┐│
                         │  │ Azure DB for │      │  Azure AI Foundry  ││
                         │  │ MySQL        │      │  Agent Service     ││
                         │  │ Flexible Srv │      │  (orchestration)   ││
                         │  └──────────────┘      └─────────┬──────────┘│
                         │                                  │           │
                         │  ┌──────────────┐      ┌─────────▼──────────┐│
                         │  │ Key Vault    │      │ Modèle Claude      ││
                         │  │ (secrets/clés)│     │ (Sonnet 4.6 via API)││
                         │  └──────────────┘      └────────────────────┘│
                         │                                               │
                         │  ┌──────────────┐  ┌──────────────────────┐  │
                         │  │ Blob Storage │  │ Application Insights  │  │
                         │  │ (exports PDF)│  │ + Azure Monitor (obs.)│  │
                         │  └──────────────┘  └──────────────────────┘  │
                         └─────────────────────────────────────────────┘
```

## 3. L'architecture agentic

### 3.1 Pourquoi des agents spécialisés plutôt qu'un seul prompt géant ?

Un business plan complet en 10 sections + scénarios + score + note CODIR est trop hétérogène pour un appel monolithique. Le découper en **agents spécialisés** apporte :

- **Qualité** : chaque agent a un prompt système focalisé sur une tâche → meilleure fiabilité.
- **Robustesse** : on valide la sortie JSON de chaque agent isolément ; un échec est rejoué localement.
- **Parallélisme** : analyse, scénarios et tableau financier peuvent être produits en parallèle.
- **Coût/latence maîtrisés** : on choisit le bon modèle par tâche (raisonnement vs rédaction).
- **Traçabilité** : chaque étape est loggée → on explique au CODIR *comment* le score et le BP ont été produits.

### 3.2 Les agents

| Agent | Mission | Entrée | Sortie JSON |
|---|---|---|---|
| **Orchestrateur** | Pilote le flux, gère erreurs/retries, agrège | Projet brut | Statut + résultats consolidés |
| **Agent Analyste** | Forces / faiblesses / risques / opportunités | Données projet + base | `{forces[], faiblesses[], risques[], opportunites[]}` |
| **Agent Financier** | Tableau financier + 3 scénarios (bas/médian/haut) | Hypothèses financières | `{tableau[], scenarios{bas,median,haut}}` |
| **Agent Scoring** | *Assiste* la qualification des critères qualitatifs ; le **calcul final reste côté backend** | Données + analyse | `{criteres{...}}` (normalisés, non pondérés) |
| **Agent Rédacteur BP** | Business plan structuré en 10 sections | Tout le contexte | `{sections{resume_exec, ...}}` |
| **Agent Synthèse CODIR** | Note d'une page pour le comité | BP + score | `{synthese_codir}` |

> **Garde-fou clé** : l'Agent Scoring ne **calcule pas** le score (risque d'hallucination). Il qualifie les critères qualitatifs (ex. alignement stratégique) en s'appuyant uniquement sur les données fournies ; le **backend applique la formule pondérée** de façon déterministe. C'est notre arbitrage principal : *l'IA juge, le code arbitre*.

### 3.3 Flux d'orchestration

```
1. Backend reçoit le projet (JSON validé Pydantic)
2. Persistance MySQL (projet + hypothèses + risques)
3. Orchestrateur lance EN PARALLÈLE :
      ├─ Agent Analyste
      └─ Agent Financier (scénarios)
4. Backend calcule le SCORE (déterministe) à partir des critères + sortie analyste
5. Agent Rédacteur BP (utilise analyse + finances + score)
6. Agent Synthèse CODIR (utilise BP + score)
7. Validation JSON de chaque sortie ; retry ciblé si malformé
8. Persistance des résultats + génération export (Blob Storage)
9. Réponse au frontend : score, BP, scénarios, synthèse, recommandations
```

### 3.4 Azure AI Foundry Agent Service — utilité

**Azure AI Foundry** (anciennement Azure AI Studio) fournit un **Agent Service** managé qui apporte, pour notre cas :

- **Hébergement et orchestration** des agents sans gérer d'infra.
- **Threads & état** : conservation du contexte d'une session porteur de projet.
- **Tool calling** intégré : un agent peut interroger MySQL ou Blob Storage via des outils déclarés.
- **Observabilité native** : traces par agent dans Application Insights.
- **Sécurité** : identités managées (Managed Identity) → pas de clé en dur, accès Key Vault.
- **Connexion modèle** : Claude via Anthropic API (ou via le catalogue de modèles Foundry).

**Arbitrage / limite** : Foundry ajoute de la valeur sur l'orchestration et l'observabilité, mais introduit une dépendance et une courbe d'apprentissage. **Plan B** assumé : pour le démonstrateur, l'orchestration peut être faite **directement dans FastAPI** avec le SDK Anthropic (appels async + `asyncio.gather`). On documente les deux chemins et on choisit Foundry si le temps le permet, sinon orchestration applicative.

## 4. Services Azure retenus

| Service | Rôle | Pourquoi ce choix | Alternative écartée |
|---|---|---|---|
| **Azure Container Apps** | Héberge l'API FastAPI (conteneur) | Serverless, scale-to-zero (coût quasi nul au repos), pas de gestion K8s | App Service (moins flexible pour conteneurs) ; AKS (trop lourd pour un binôme) |
| **Azure Static Web Apps** | Sert le frontend + routes API | Tier gratuit, CI/CD GitHub intégré, CDN | VM nginx (sur-ingénierie) |
| **Azure Database for MySQL – Flexible Server** | Base relationnelle | MySQL imposé ; *Flexible* = arrêt/démarrage planifié → économies | Container MySQL auto-géré (pas de sauvegardes managées) |
| **Azure AI Foundry – Agent Service** | Orchestration des agents Claude | Managé, observable, tool-calling, Managed Identity | Orchestration 100 % applicative (notre plan B) |
| **Azure Key Vault** | Secrets : `ANTHROPIC_API_KEY`, conn. MySQL | Aucune clé dans le code/`.env` en prod ; rotation | Variables d'env en clair (insuffisant en sécurité) |
| **Azure Blob Storage** | Stockage des exports (PDF/JSON de synthèse) | Pas cher, URLs signées (SAS) pour le téléchargement | Stockage en base (mauvaise pratique) |
| **Application Insights + Azure Monitor** | Observabilité, traces agents, alertes | Diagnostiquer hallucinations/latence ; KPI démo | Logs fichiers (non centralisés) |
| **Azure Container Registry** | Images Docker de l'API | S'intègre à Container Apps + GitHub Actions | Docker Hub (moins intégré IAM Azure) |
| **Managed Identity** | Auth service-à-service sans secret | Élimine les clés statiques entre services | Service principals + secrets (rotation pénible) |

## 5. Modèle de données (MySQL)

Tables minimales imposées par le cas + relations :

```
projets ──1:N──▶ hypotheses_financieres
   │
   ├──1:N──▶ parametres_strategiques
   ├──1:N──▶ risques
   ├──1:N──▶ opportunites
   ├──1:N──▶ scenarios            (bas / médian / haut)
   └──1:N──▶ scores               (résultat du calcul, historisé)
```

Volumétrie cible du jeu fictif : **5–10 projets**, **30–50 hypothèses financières**, **20 paramètres stratégiques**, **10 risques** + **10 opportunités** types, **10 profils de porteurs**. Détail du schéma dans [`livrable.md`](./livrable.md).

## 6. Contrats d'interface (JSON)

**Entrée (extrait de payload minimal)** :

```json
{
  "projet": { "nom": "Facteo+", "type": "service_numerique", "porteur": "DSI Courrier" },
  "hypotheses_financieres": [
    { "categorie": "salaires", "montant_mensuel": 45000, "duree_mois": 12 }
  ],
  "risques": [ { "type": "technique", "gravite": 3, "probabilite": 2 } ],
  "parametres_strategiques": { "alignement_groupe": 4, "impact_branche": 3 }
}
```

**Sortie attendue** :

```json
{
  "score": { "total": 78, "details": { "rentabilite": 24, "alignement": 16, "risque": 14, "...": 24 } },
  "business_plan": { "sections": { "resume_exec": "…", "description": "…" } },
  "scenarios": { "bas": {}, "median": {}, "haut": {} },
  "synthese_codir": "…",
  "recommandations": [ "…" ]
}
```

## 7. Gestion des erreurs IA (exigence du cas)

| Risque | Mitigation |
|---|---|
| **JSON mal formé** | Validation Pydantic + *retry* avec consigne de reformatage ; en dernier recours, parsing tolérant + rejet propre |
| **Hallucination** | Prompt système « interdiction d'inférer des données non fournies » + validation croisée backend (montants ∈ hypothèses saisies) |
| **Recommandations incohérentes** | Règles métier de cohérence côté backend (ex. score bas ⇒ pas de reco « Go » sans réserve) |
| **Données absentes** | Champs obligatoires bloqués côté formulaire + valeurs `null` explicites jamais inventées par l'IA |

## 8. Sécurité (résumé)

- Secrets en **Key Vault**, jamais commités (cf. secret scanning dans [`craftsmanship.md`](./craftsmanship.md)).
- **Managed Identity** entre services Azure.
- HTTPS partout (TLS managé par Static Web Apps / Container Apps).
- Principe du moindre privilège sur les rôles RBAC Azure.
- Pas de données réelles La Poste : **jeu de données 100 % fictif**.

## 9. Limites assumées

- Démonstrateur, **pas production** : pas de multi-tenant, pas de SSO entreprise.
- Le score reste un **outil d'aide** à la décision, pas un verdict automatique.
- Dépendance à la disponibilité de l'API Claude (gérée par retries + circuit-breaker simple).
- Coût IA proportionnel au nombre de générations (mitigé par cache des sorties par projet).

---

← [README](../README.md) · Suite : [`craftsmanship.md`](./craftsmanship.md)
