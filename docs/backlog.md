# Backlog — Epics & User Stories BizPlan-IA

> Document de référence synchronisé avec JIRA (projet [`BIZ`](https://ionis-stm-team-ek7kwlup.atlassian.net/jira/software/projects/BIZ/boards)).
> Format : **Epic → Story → Critères d'acceptation**.
> Import JIRA effectué le 2026-06-13 — numéros `BIZ-xx` assignés.

← Retour au [README](../README.md)

---

## Conventions

- **Epic** : thème fonctionnel ou technique autonome (2–4 semaines de travail)
- **Story** : fonctionnalité utilisateur livrée en < 3 jours, testable de bout en bout
- **Critères d'acceptation (CA)** : conditions binaires (passe / échoue) qui définissent le Done
- **Priorité** : 🔴 Must-have · 🟡 Should-have · 🟢 Nice-to-have
- **Points** : estimation relative (Fibonacci)

---

## [BIZ-1] EPIC 1 — Saisie du projet (formulaire)

> Le porteur de projet saisit les informations de son projet via un formulaire web structuré.

**Priorité :** 🔴 Must-have

---

### [BIZ-7] US-1.1 — Saisir les informations générales du projet
**En tant que** porteur de projet,  
**Je veux** renseigner le nom, la description, la direction concernée et l'horizon temporel du projet,  
**Afin de** créer un dossier de projet dans le système.

**Points :** 3  
**Critères d'acceptation :**
- [ ] Le formulaire contient : nom (obligatoire, max 200 car.), description (obligatoire, max 1000 car.), direction (liste déroulante fixe), durée estimée (mois, entier > 0)
- [ ] La soumission sans champ obligatoire affiche un message d'erreur explicite
- [ ] Un projet créé est persisté en base et retourne un `project_id`
- [ ] La réponse API est < 500 ms

---

### [BIZ-8] US-1.2 — Saisir les hypothèses financières
**En tant que** porteur de projet,  
**Je veux** renseigner les hypothèses financières clés (investissement, revenus, coûts),  
**Afin que** l'IA puisse calculer les scénarios financiers.

**Points :** 5  
**Critères d'acceptation :**
- [ ] Champs : investissement initial (€), revenus annuels estimés (€), coûts opérationnels annuels (€), délai de retour estimé (mois)
- [ ] Tous les montants sont des entiers positifs validés côté API (Pydantic)
- [ ] Les hypothèses sont liées au `project_id`
- [ ] Un projet sans hypothèses financières ne peut pas déclencher la génération du BP

---

### [BIZ-9] US-1.3 — Saisir les dimensions stratégiques
**En tant que** porteur de projet,  
**Je veux** évaluer mon projet sur 6 dimensions stratégiques via des curseurs ou échelles,  
**Afin que** le score de pertinence soit calculé.

**Points :** 5  
**Critères d'acceptation :**
- [ ] 6 dimensions avec score de 0 à 10 : Rentabilité, Alignement stratégique, Risque, Impact opérationnel, Impact social/environnemental, Faisabilité technique
- [ ] Chaque dimension a un label et une infobulle d'aide à la saisie
- [ ] Les valeurs sont validées (entier 0–10) côté API
- [ ] La sauvegarde partielle est possible (reprise de session)

---

### [BIZ-10] US-1.4 — Visualiser et modifier le projet avant soumission
**En tant que** porteur de projet,  
**Je veux** revoir toutes mes saisies sur un écran récapitulatif avant de lancer la génération,  
**Afin de** corriger les erreurs avant de consommer des crédits IA.

**Points :** 2  
**Critères d'acceptation :**
- [ ] Écran récapitulatif affiche toutes les sections (général, financier, stratégique)
- [ ] Bouton « Modifier » ramène sur la section concernée
- [ ] Bouton « Lancer la génération » déclenche l'appel API `/generate`
- [ ] Le récapitulatif est accessible après génération (lecture seule)

---

## [BIZ-2] EPIC 2 — Score de pertinence

> Calcul déterministe et auditable du score de pertinence (0–100) à partir des données saisies.

**Priorité :** 🔴 Must-have

---

### [BIZ-11] US-2.1 — Calculer le score de pertinence
**En tant que** système backend,  
**Je veux** calculer un score normalisé sur 6 dimensions pondérées,  
**Afin de** fournir une note objective et comparable entre projets.

**Points :** 5  
**Critères d'acceptation :**
- [ ] Formule : normalisation [0,1] de chaque dimension → pondération → somme → ×100
- [ ] Pondérations : Rentabilité 30%, Alignement 20%, Risque 20%, Impact opérationnel 10%, Impact social 10%, Faisabilité 10%
- [ ] Score minimum 0, maximum 100 (bornage strict)
- [ ] Tests unitaires couvrent les cas limites : toutes notes à 0, toutes à 10, notes mixtes
- [ ] Le calcul est déterministe : mêmes entrées → même sortie
- [ ] Résultat persisté en base avec horodatage

---

### [BIZ-12] US-2.2 — Exposer le score via l'API
**En tant que** frontend,  
**Je veux** appeler `POST /projects/{id}/score` et recevoir le score détaillé,  
**Afin d'** afficher le résultat et le détail par dimension.

**Points :** 3  
**Critères d'acceptation :**
- [ ] Endpoint `POST /projects/{id}/score` retourne `{ total: 72, dimensions: { rentabilite: 8.4, ... } }`
- [ ] Réponse en < 200 ms (calcul pur Python, pas d'IA)
- [ ] Erreur 404 si `project_id` inexistant
- [ ] Erreur 422 si dimensions manquantes
- [ ] Schéma de réponse documenté dans OpenAPI

---

### [BIZ-13] US-2.3 — Afficher le score et le détail par dimension
**En tant que** porteur de projet,  
**Je veux** voir mon score global et la contribution de chaque dimension,  
**Afin de** comprendre les leviers d'amélioration.

**Points :** 3  
**Critères d'acceptation :**
- [ ] Score global affiché en grand (0–100) avec code couleur (rouge < 40, orange 40–69, vert ≥ 70)
- [ ] Graphique radar ou barres horizontales par dimension
- [ ] Chaque dimension affiche : note brute (0–10), score pondéré, pondération appliquée
- [ ] Score accessible depuis le tableau de bord comparatif

---

## [BIZ-3] EPIC 3 — Génération du Business Plan (agents IA)

> Architecture multi-agents (6 agents IA, orchestrés par le code) pour générer un BP complet en 11 sections, 3 scénarios financiers et une note CODIR.

**Priorité :** 🔴 Must-have

---

### [BIZ-14] US-3.1 — Orchestrer la génération multi-agents
**En tant que** système backend,  
**Je veux** déclencher une séquence d'agents spécialisés pour produire le BP,  
**Afin de** garantir la qualité et la cohérence de chaque section.

**Points :** 8  
**Critères d'acceptation :**
- [ ] L'orchestrateur **applicatif** (code FastAPI, `generation.py`) déclenche les agents dans l'ordre défini (séquentiel)
- [ ] Chaque agent reçoit le contexte du projet + les sorties des agents précédents
- [ ] En cas d'échec d'un agent, **repli déterministe** (template) pour toujours produire un livrable
- [ ] Chaque appel agent est loggé (input, output, durée, tokens) dans Application Insights
- [ ] Timeout global de génération : 5 minutes

---

### [BIZ-15] US-3.2 — Générer l'analyse de marché et du contexte
**En tant que** agent Analyste,  
**Je veux** produire une analyse du contexte projet (marché, enjeux, positionnement),  
**Afin que** les sections stratégiques du BP soient fondées.

**Points :** 5  
**Critères d'acceptation :**
- [ ] Sortie JSON structurée : `{ marche: string, enjeux: string[], positionnement: string }`
- [ ] L'agent n'invente pas de données chiffrées non fournies (prompt contraint)
- [ ] Longueur : 200–400 mots par section
- [ ] Test : réponse JSON valide sur 3 projets de types différents

---

### [BIZ-16] US-3.3 — Générer les 3 scénarios financiers
**En tant que** agent Financier,  
**Je veux** produire 3 scénarios (pessimiste, réaliste, optimiste) à partir des hypothèses saisies,  
**Afin que** le CODIR dispose d'une projection financière.

**Points :** 8  
**Critères d'acceptation :**
- [ ] 3 scénarios : pessimiste (×0,7 revenus, ×1,2 coûts), réaliste (×1), optimiste (×1,3 revenus, ×0,9 coûts)
- [ ] Chaque scénario : revenus N, N+1, N+2 ; coûts ; EBITDA ; délai de retour
- [ ] Les calculs sont effectués côté Python (pas par l'IA) à partir des hypothèses
- [ ] L'IA rédige uniquement le commentaire narratif de chaque scénario
- [ ] Sortie JSON valide et persistée en base

---

### [BIZ-17] US-3.4 — Générer le Business Plan en 11 sections
**En tant que** agent Rédacteur,  
**Je veux** produire un BP structuré en 11 sections à partir de toutes les données,  
**Afin de** fournir un document complet et professionnel.

**Points :** 8  
**Critères d'acceptation :**
- [ ] 11 sections : 1. Résumé exécutif, 2. Présentation du projet, 3. Analyse du marché et du contexte, 4. Analyse concurrentielle, 5. Proposition de valeur, 6. Modèle économique, 7. Plan opérationnel, 8. Analyse des risques, 9. Hypothèses et scénarios financiers, 10. Impact stratégique et RSE, 11. Recommandation et prochaines étapes
- [ ] Chaque section : 2 à 5 phrases rédigées
- [ ] Aucun chiffre inventé : tous les montants proviennent des hypothèses saisies
- [ ] Sortie JSON structurée, mappée vers les titres affichés (`_SECTION_TITLES`)
- [ ] Tests : validation de structure (11 sections présentes) sur 3 projets

---

### [BIZ-18] US-3.5 — Générer la note de synthèse CODIR
**En tant que** agent Synthèse,  
**Je veux** produire une note d'une page résumant le projet pour le CODIR,  
**Afin que** les décideurs disposent d'un résumé décisionnel.

**Points :** 5  
**Critères d'acceptation :**
- [ ] Note ≤ 500 mots
- [ ] Structure : contexte (2 phrases), recommandation (✅/⚠️/❌ + justification), score, top 3 risques, top 3 opportunités, prochaines étapes
- [ ] La recommandation est cohérente avec le score (score ≥ 70 → ✅, 40–69 → ⚠️, < 40 → ❌)
- [ ] Tone : formel, neutre, pas de conditionnel non justifié

---

## [BIZ-4] EPIC 4 — Consultation et export

> Le porteur de projet et le CODIR consultent les résultats et exportent les documents.

**Priorité :** 🔴 Must-have

---

### [BIZ-19] US-4.1 — Consulter le Business Plan généré
**En tant que** porteur de projet,  
**Je veux** lire le BP généré dans l'interface web,  
**Afin de** vérifier le contenu avant export.

**Points :** 3  
**Critères d'acceptation :**
- [ ] Le BP s'affiche section par section dans l'interface
- [ ] Navigation entre sections (sommaire cliquable)
- [ ] Le BP est accessible en lecture depuis un lien stable (`/projects/{id}/bp`)
- [ ] Indicateur de statut de génération (en cours / terminé / erreur)

---

### [BIZ-20] US-4.2 — Exporter le BP et la note CODIR
**En tant que** porteur de projet,  
**Je veux** télécharger le BP et la note CODIR,  
**Afin de** les partager hors de l'outil.

**Points :** 5  
**Critères d'acceptation :**
- [ ] Export Markdown (.md) du BP complet disponible
- [ ] Export PDF du BP (via conversion server-side ou navigateur)
- [ ] Export de la note CODIR en texte brut
- [ ] Nom de fichier : `bizplan-{nom-projet}-{date}.pdf`
- [ ] Export déclenche un log (qui, quand, quel projet)

---

### [BIZ-21] US-4.3 — Tableau de bord comparatif multi-projets
**En tant que** manager CODIR,  
**Je veux** voir tous les projets avec leur score sur une seule vue,  
**Afin de** prioriser les projets soumis.

**Points :** 5  
**Critères d'acceptation :**
- [ ] Tableau : nom projet, direction, score (0–100), date soumission, statut BP
- [ ] Tri par score décroissant par défaut
- [ ] Filtre par direction
- [ ] Code couleur scores (rouge/orange/vert)
- [ ] Lien vers le BP de chaque projet

---

## [BIZ-5] EPIC 5 — Infrastructure & données de test

> Socle technique : base de données, migrations, données fictives, scaffolding applicatif.

**Priorité :** 🔴 Must-have

---

### [BIZ-22] US-5.1 — Définir et créer le schéma de base de données
**En tant que** développeur,  
**Je veux** un schéma MySQL normalisé pour stocker projets, hypothèses, scores et BP,  
**Afin que** toutes les données soient persistées et requêtables.

**Points :** 5  
**Critères d'acceptation :**
- [ ] Tables : `projects`, `financial_assumptions`, `strategic_dimensions`, `scores`, `business_plans`, `scenarios`
- [ ] Clés étrangères + contraintes d'intégrité
- [ ] Script SQL de création versionné dans `db/schema.sql`
- [ ] Migration Alembic (ou SQL versionné) applicable en CI/CD
- [ ] Aucun champ `TEXT` non borné pour les entrées utilisateur

---

### [BIZ-23] US-5.2 — Créer le jeu de données fictives (seed)
**En tant que** développeur,  
**Je veux** un jeu de 5–10 projets fictifs représentatifs La Poste,  
**Afin de** démontrer l'outil en soutenance avec des données réalistes.

**Points :** 3  
**Critères d'acceptation :**
- [ ] 5 projets minimum couvrant des directions différentes (RH, Digital, Logistique, Finance, RSE)
- [ ] Chaque projet a ses hypothèses financières et ses dimensions stratégiques complètes
- [ ] Les projets ont des scores variés (au moins 1 rouge, 1 orange, 2 verts)
- [ ] Script `db/seed.sql` idempotent (peut être rejoué sans duplication)

---

### [BIZ-24] US-5.3 — Scaffolding de l'application FastAPI
**En tant que** développeur,  
**Je veux** la structure de base de l'application Python/FastAPI avec les modules principaux,  
**Afin que** les US fonctionnelles puissent être développées de façon cohérente.

**Points :** 5  
**Critères d'acceptation :**
- [ ] Structure : `app/main.py`, `app/routers/`, `app/services/`, `app/models/`, `app/schemas/`
- [ ] `GET /health` retourne `{ status: "ok" }` avec code 200
- [ ] `GET /docs` expose l'OpenAPI auto-générée
- [ ] Config chargée via `pydantic-settings` depuis `.env.local`
- [ ] Tests unitaires présents pour le healthcheck
- [ ] `ruff check`, `mypy app/`, `pytest` passent au vert

---

## [BIZ-6] EPIC 6 — Qualité & sécurité (transverse)

> Stories techniques transverses garantissant la qualité tout au long du projet.

**Priorité :** 🔴 Must-have

---

### [BIZ-25] US-6.1 — Pipeline CI opérationnelle
**En tant que** développeur,  
**Je veux** que chaque PR déclenche automatiquement lint, types, tests et build Docker,  
**Afin de** détecter les régressions immédiatement.

**Points :** 3  
**Critères d'acceptation :**
- [ ] `.github/workflows/ci.yml` déclenché sur chaque PR et push main
- [ ] Jobs : `ruff check`, `ruff format --check`, `mypy`, `pytest --cov 80%`, `docker build`
- [ ] Merge bloqué si l'un des jobs échoue
- [ ] Durée CI < 5 minutes

---

### [BIZ-26] US-6.2 — Pipeline de déploiement automatique
**En tant que** développeur,  
**Je veux** qu'un merge sur `main` déploie automatiquement l'API sur Azure Container Apps,  
**Afin d'** avoir un environnement `dev` toujours à jour.

**Points :** 3  
**Critères d'acceptation :**
- [ ] `.github/workflows/deploy.yml` déclenché sur push `main`
- [ ] Authentification OIDC (pas de secret Azure stocké)
- [ ] Image taguée avec le SHA du commit
- [ ] Vérification de santé post-déploiement (`az containerapp show`)
- [ ] Rollback possible en re-déployant l'image précédente

---

### [BIZ-27] US-6.3 — Aucun secret en clair dans le code
**En tant que** développeur,  
**Je veux** que les secrets soient détectés et bloqués avant tout push,  
**Afin d'** éviter toute fuite d'informations sensibles.

**Points :** 2  
**Critères d'acceptation :**
- [ ] `detect-secrets` configuré en hook pre-commit
- [ ] GitHub Secret scanning + push protection activés sur le repo
- [ ] `.env.local` dans `.gitignore`
- [ ] `ANTHROPIC_API_KEY` et `DATABASE_URL` stockés dans Azure Key Vault en prod
- [ ] Test : tentative de commit avec une fausse clé → blocage

---

## Récapitulatif du backlog

| Epic | Stories | Points total | Priorité |
|---|---|---|---|
| Epic 1 — Saisie formulaire | 4 | 15 | 🔴 Must |
| Epic 2 — Score de pertinence | 3 | 11 | 🔴 Must |
| Epic 3 — Génération BP (agents IA) | 5 | 34 | 🔴 Must |
| Epic 4 — Consultation & export | 3 | 13 | 🔴 Must |
| Epic 5 — Infrastructure & données | 3 | 13 | 🔴 Must |
| Epic 6 — Qualité & sécurité | 3 | 8 | 🔴 Must |
| **TOTAL** | **21 stories** | **94 points** | |

---

## Ordre de développement suggéré

```
Sprint 0 (infra) : US-5.3 → US-5.1 → US-6.1 → US-6.2 → US-6.3
Sprint 1 (core)  : US-1.1 → US-1.2 → US-1.3 → US-2.1 → US-2.2
Sprint 2 (IA)    : US-3.1 → US-3.3 → US-3.2 → US-3.4 → US-3.5
Sprint 3 (UX)    : US-1.4 → US-2.3 → US-4.1 → US-4.2 → US-4.3
Sprint 4 (data)  : US-5.2 + démo soutenance
```

---

← [README](../README.md) · [architecture.md](./architecture.md) · [craftsmanship.md](./craftsmanship.md)
