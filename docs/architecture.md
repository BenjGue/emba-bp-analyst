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
  Utilisateur            │              ┌──────────────────────────────┐ │
  (navigateur)  ───────▶ │              │ Azure Container Apps         │ │
                         │              │ (FastAPI)                    │ │
                         │              │ • sert le frontend (/, /static)│
                         │              │ • API + orchestration agents │ │
                         │              └────────┬─────────────────────┘ │
                         │                                  │            │
                         │         ┌────────────────────────┼─────────┐ │
                         │         ▼                         ▼         │ │
                         │  ┌──────────────┐      ┌────────────────────┐│
                         │  │ Azure DB for │      │  Azure AI Foundry  ││
                         │  │ MySQL        │      │  (inférence :      ││
                         │  │ Flexible Srv │      │  chat/completions) ││
                         │  └──────────────┘      └─────────┬──────────┘│
                         │                                  │           │
                         │  ┌──────────────┐      ┌─────────▼──────────┐│
                         │  │ Key Vault    │      │ Modèle configurable││
                         │  │ (secrets/clés)│     │ (agnostique : GPT…) ││
                         │  └──────────────┘      └────────────────────┘│
                         │                                               │
                         │  ┌─────────────────────────────────────────┐ │
                         │  │ (Roadmap — non provisionné aujourd'hui) │ │
                         │  │ Blob Storage · Application Insights/Mon. │ │
                         │  └─────────────────────────────────────────┘ │
                         └─────────────────────────────────────────────┘
```

> **Note d'implémentation.** Le frontend (`app/static/`) est servi **par l'app
> FastAPI elle-même** (`StaticFiles` + route `GET /`) depuis la Container App :
> il n'y a **pas** d'Azure Static Web Apps. Les exports (Markdown/PDF) sont
> générés **à la volée** via `GET /projects/{id}/export` — **pas** de Blob
> Storage. **Blob Storage** et **Application Insights/Azure Monitor** sont des
> pistes d'évolution **non encore provisionnées** (cf. [`infra/provision.sh`](../infra/provision.sh)).

## 3. L'architecture agentic

### 3.1 Pourquoi des agents spécialisés plutôt qu'un seul prompt géant ?

Un business plan complet en 11 sections + scénarios + score + note CODIR est trop hétérogène pour un appel monolithique. Le découper en **agents spécialisés** apporte :

- **Qualité** : chaque agent a un prompt système focalisé sur une tâche → meilleure fiabilité.
- **Robustesse** : on valide la sortie JSON de chaque agent isolément ; en cas d'échec, le service **retombe sur un mode déterministe** (template) pour toujours produire un livrable.
- **Séparation IA / calcul** : l'IA rédige et raisonne ; les chiffres (scénarios, score) sont calculés **par le code** puis seulement commentés.
- **Coût/latence maîtrisés** : prompts courts et ciblés, modèle configurable selon la tâche.
- **Traçabilité** : chaque étape est loggée → on explique au CODIR *comment* le score et le BP ont été produits.

### 3.2 Les agents (implémentation réelle)

> **L'orchestration n'est pas un agent.** C'est du **code** applicatif
> ([`app/services/generation.py`](../app/services/generation.py) :
> `_generate_content` / `_generate_with_ai`) qui enchaîne les agents **de manière
> séquentielle**, valide chaque sortie JSON (Pydantic) et bascule sur un repli
> déterministe en cas d'erreur. Il n'existe **pas** d'« agent Scoring » : le score
> est calculé par le code ([`app/services/scoring.py`](../app/services/scoring.py)).

**6 agents IA**, chacun avec un prompt système dédié ([`app/services/ai/prompts.py`](../app/services/ai/prompts.py)) :

| Agent | Ticket | Mission | Sortie JSON validée |
|---|---|---|---|
| **Description** | BIZ-37 | Reformule des idées brutes en description de projet (endpoint d'aide à la saisie) | `DescriptionDraftResponse` |
| **Évaluateur** | BIZ-56 | *Propose* une note 0–10 pour chacune des **6 dimensions** ; le **score reste calculé par le backend** | `EvaluateurOutput` |
| **Analyste** | BIZ-15 | Forces / faiblesses / risques / opportunités / actions correctives | `AnalysteOutput` |
| **Financier** | BIZ-16 | **Commente** les scénarios (bas/médian/haut) déjà *calculés par le backend* — ne recalcule rien | `FinancierOutput` |
| **Rédacteur BP** | BIZ-17 | Rédige le business plan en **11 sections** | `RedacteurOutput` |
| **Synthèse CODIR** | BIZ-18 | Note d'une page pour le comité | `SyntheseOutput` |

> La génération complète du BP enchaîne **4** de ces agents (Analyste → Financier → Rédacteur → Synthèse). Les agents **Description** et **Évaluateur** sont exposés par des endpoints dédiés (aide à la saisie / suggestion des notes), hors de la chaîne de génération.

> **Garde-fou clé** : aucun agent ne **calcule** le score (risque d'hallucination). L'Évaluateur *propose* les notes des 6 dimensions à partir des seules données fournies ; le **backend applique la formule pondérée** de façon déterministe et bornée. C'est notre arbitrage principal : *l'IA juge, le code arbitre*.

### 3.3 Flux d'orchestration (séquentiel, côté code)

```
1. Backend reçoit le projet (JSON validé Pydantic)
2. Persistance MySQL (projet + hypothèses + risques)
3. Backend calcule les SCÉNARIOS financiers (déterministe, _build_scenarios)
4. Backend calcule le SCORE (déterministe, scoring.py) si non déjà présent
5. L'orchestrateur (code) enchaîne EN SÉQUENCE :
      Agent Analyste → Agent Financier (commente) → Agent Rédacteur → Agent Synthèse
6. Validation JSON de chaque sortie ; repli déterministe (template) si un agent échoue
7. Persistance des résultats (MySQL) ; export Markdown/PDF généré à la volée (`GET /export`)
8. Réponse au frontend : score, BP (11 sections), scénarios, synthèse, recommandations
```

### 3.4 Azure AI Foundry — rôle retenu

**Azure AI Foundry** (anciennement Azure AI Studio) est utilisé ici comme **endpoint d'inférence** (`chat/completions`), pas comme orchestrateur. Ce qu'il apporte pour notre cas :

- **Modèle managé et agnostique** : un seul déploiement, modèle interchangeable (Claude, GPT…) par configuration.
- **Observabilité** : journalisation applicative des appels (l'intégration Application Insights/Azure Monitor est une piste d'évolution, non encore provisionnée).
- **Sécurité** : identités managées (Managed Identity) → pas de clé en dur, accès Key Vault.
- **Sorties JSON structurées** : `response_format: json_object`, validées ensuite côté backend (Pydantic).

**Arbitrage / choix retenu** : l'**orchestration des agents est applicative** (code FastAPI dans [`app/services/generation.py`](../app/services/generation.py)), et **non** déléguée à l'Agent Service de Foundry. Ce choix nous donne un contrôle total du flux (séquence, validation JSON, repli déterministe) et évite une dépendance à une couche d'orchestration managée. Foundry reste responsable de l'inférence et de l'observabilité.

## 4. Services Azure retenus

| Service | Rôle | Pourquoi ce choix | Alternative écartée |
|---|---|---|---|
| **Azure Container Apps** | Héberge l'API FastAPI **et sert le frontend** (`app/static/` via `StaticFiles` + `GET /`) | Serverless, scale-to-zero (coût quasi nul au repos), pas de gestion K8s ; une seule origine front+API | App Service (moins flexible pour conteneurs) ; AKS (trop lourd pour un binôme)
| **Azure Database for MySQL – Flexible Server** | Base relationnelle | MySQL imposé ; *Flexible* = arrêt/démarrage planifié → économies | Container MySQL auto-géré (pas de sauvegardes managées) |
| **Azure AI Foundry** | Endpoint d'inférence (`chat/completions`) des agents | Managé, observable, modèle agnostique, Managed Identity | Agent Service de Foundry pour l'orchestration (écarté : orchestration applicative préférée) |
| **Azure Key Vault** | Secrets : connexion MySQL (`DATABASE-URL`), clé IA (`AI_API_KEY` si non Entra ID) | Aucune clé dans le code/`.env` en prod ; rotation | Variables d'env en clair (insuffisant en sécurité) |
| **Azure Container Registry** | Images Docker de l'API | S'intègre à Container Apps + GitHub Actions | Docker Hub (moins intégré IAM Azure) |
| **Managed Identity** | Auth service-à-service sans secret | Élimine les clés statiques entre services | Service principals + secrets (rotation pénible) |

> **Pistes d'évolution (non provisionnées à ce jour, cf. [`infra/provision.sh`](../infra/provision.sh)) :** **Azure Static Web Apps** (si on voulait séparer le front), **Azure Blob Storage** (si on voulait persister les exports plutôt que les générer à la volée), **Application Insights + Azure Monitor** (observabilité centralisée).

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
- HTTPS partout (TLS managé par Container Apps).
- Principe du moindre privilège sur les rôles RBAC Azure.
- Pas de données réelles La Poste : **jeu de données 100 % fictif**.

## 9. Limites assumées

- Démonstrateur, **pas production** : pas de multi-tenant, pas de SSO entreprise.
- Le score reste un **outil d'aide** à la décision, pas un verdict automatique.
- Dépendance à la disponibilité du modèle d'inférence (gérée par retries + repli déterministe).
- Coût IA proportionnel au nombre de générations (mitigé par cache des sorties par projet).

---

← [README](../README.md) · Suite : [`craftsmanship.md`](./craftsmanship.md)
