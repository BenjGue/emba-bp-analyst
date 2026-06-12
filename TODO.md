# TODO — Suivi des tâches & journal d'actions

> **Convention de statut** : `[ ]` À faire · `[~]` En cours · `[x]` Terminé · `[!]` Bloqué  
> **Journal** : chaque action terminée est horodatée en bas de section pour permettre une reprise sur erreur.

---

## 1. Craftsmanship — Infrastructure de dev

### Tâches

- [ ] Créer `.vscode/mcp.json` (serveur MCP JIRA)
- [ ] Créer `.vscode/extensions.json` (extensions standardisées du binôme)
- [ ] Créer `.vscode/settings.json` (réglages partagés : Ruff, format on save, exclusions)
- [ ] Créer `.github/workflows/ci.yml` (lint + types + tests + CodeQL)
- [ ] Créer `.github/workflows/deploy.yml` (build → ACR → Azure Container Apps via OIDC)
- [ ] Créer `.github/workflows/codeql.yml` (SAST hebdomadaire)
- [ ] Créer `.github/pull_request_template.md` (template PR avec checklist)
- [ ] Créer `Dockerfile` (image API Python)
- [ ] Configurer les secrets GitHub (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID)
- [ ] Configurer les règles de protection de branche `main` sur GitHub
- [ ] Valider le choix d'assistant IA (Option A : Claude Code / Option B : GitHub Copilot Education)

### Journal

| Date | Action | Résultat |
|---|---|---|
| 2026-06-12 | Création du fichier `craftsmanship.md` | ✅ Documenté |
| 2026-06-12 | Ajout section choix assistant IA (Claude Code vs Copilot Education) | ✅ Documenté |
| 2026-06-12 | Mise à jour `How-to-setup.md` : section §3 remplacée par choix Option A/B, §7 et §8 alignés | ✅ Terminé |
| 2026-06-12 | Mise à jour `How-to-setup.md` : arbre de décision assistant IA (Claude Code CLI+addon vs Copilot Education + démarche Nadine), Azure géré par Brice, MySQL local supprimé (→ Azure dev) | ✅ Terminé |
| 2026-06-12 | Remplacement placeholders `<org>/bizplan-ia` → `BenjGue/emba-bp-analyst` dans README et How-to-setup | ✅ Terminé |
| 2026-06-12 | Premier commit + push sur `github.com/BenjGue/emba-bp-analyst` (7 fichiers, commit `82c2e27`) | ✅ Terminé |

---

## 2. Architecture — Infrastructure technique

### Tâches

- [ ] Valider le schéma d'architecture final (cf. `architecture.md`)
- [ ] Provisionner le Resource Group Azure (`rg-bizplan`)
- [ ] Créer l'Azure Container Registry (`bizplanacr`)
- [ ] Créer l'Azure Container Apps environment
- [ ] Créer la base MySQL (Azure Database for MySQL Flexible Server)
- [ ] Configurer les variables d'environnement dans Container Apps
- [ ] Mettre en place le Key Vault pour les secrets (ANTHROPIC_API_KEY, etc.)
- [ ] Configurer les federated credentials OIDC (GitHub → Azure)
- [ ] Valider la connectivité Container Apps ↔ MySQL

### Journal

| Date | Action | Résultat |
|---|---|---|
| 2026-06-12 | Création du fichier `architecture.md` | ✅ Documenté |

---

## 3. Business & User Stories

### Epics

#### Epic 1 — Score de pertinence
- [ ] BIZ-xx : Définir les critères de scoring (pondération)
- [ ] BIZ-xx : Implémenter le calcul du score normalisé (min-max)
- [ ] BIZ-xx : Tests unitaires score (bornes 0 et 100)
- [ ] BIZ-xx : Exposer l'endpoint `/score` via l'API

#### Epic 2 — Génération du Business Plan
- [ ] BIZ-xx : Définir la structure du BP (sections, format)
- [ ] BIZ-xx : Implémenter l'agent de génération (LLM + contexte)
- [ ] BIZ-xx : Générer le document final (PDF / Markdown)
- [ ] BIZ-xx : Tests d'intégration génération BP

#### Epic 3 — Base de données MySQL
- [ ] BIZ-xx : Définir le schéma de données (tables, relations)
- [ ] BIZ-xx : Écrire les migrations (Alembic ou SQL brut)
- [ ] BIZ-xx : Valider les requêtes d'accès via l'ORM
- [ ] BIZ-xx : Seeddata de test

#### Epic 4 — Frontend
- [ ] BIZ-xx : Définir les maquettes / wireframes
- [ ] BIZ-xx : Scaffolding du projet frontend
- [ ] BIZ-xx : Connecter le frontend à l'API
- [ ] BIZ-xx : Tests E2E (Playwright ou Cypress)

#### Epic 5 — Agents IA
- [ ] BIZ-xx : Définir l'architecture multi-agents
- [ ] BIZ-xx : Implémenter l'agent financier
- [ ] BIZ-xx : Implémenter l'agent marché
- [ ] BIZ-xx : Orchestration et chaînage des agents
- [ ] BIZ-xx : Évaluation qualité des outputs agents

### Journal

| Date | Action | Résultat |
|---|---|---|
| 2026-06-12 | Initialisation des Epics dans TODO | ✅ Draft |

---

## 4. Documentation & Livrables

### Tâches

- [ ] Compléter `README.md` (navigation, prérequis, quickstart)
- [ ] Compléter `How-to-setup.md` (installation MCP, variables d'env, etc.)
- [ ] Compléter `livrable.md`
- [ ] Compléter `AI-rules.md` (Definition of Done, règles agents IA)
- [ ] Préparer la soutenance (slides, demo live)

### Journal

| Date | Action | Résultat |
|---|---|---|
| 2026-06-12 | Fichiers `craftsmanship.md`, `architecture.md`, `AI-rules.md`, `How-to-setup.md`, `livrable.md` créés | ✅ Draft |

---

## 🔴 Bloquants & points d'attention

| # | Description | Dépendance | Statut |
|---|---|---|---|
| 1 | Choix définitif de l'assistant IA (Claude Code vs Copilot) | Accès licences binôme | En attente |
| 2 | Numéros de tickets JIRA (BIZ-xx) non encore assignés | Création du projet JIRA | En attente |
| 3 | Secrets Azure non provisionnés | Accès souscription Azure | En attente |
