# TODO — Suivi des tâches & journal d'actions

> **Convention de statut** : `[ ]` À faire · `[~]` En cours · `[x]` Terminé · `[!]` Bloqué
> **Journal** : chaque action terminée est horodatée en bas de section pour permettre une reprise sur erreur.

---

## 1. Craftsmanship — Infrastructure de dev

### Tâches

- [x] Créer `.vscode/mcp.json` (serveur MCP JIRA)
- [x] Créer `.vscode/extensions.json` (extensions standardisées du binôme)
- [x] Créer `.vscode/settings.json` (réglages partagés : Ruff, format on save, exclusions)
- [x] Créer `.github/workflows/ci.yml` (lint + types + tests + CodeQL)
- [x] Créer `.github/workflows/deploy.yml` (build → ACR → Azure Container Apps via OIDC)
- [x] Créer `.github/workflows/codeql.yml` (SAST hebdomadaire)
- [x] Créer `.github/pull_request_template.md` (template PR avec checklist)
- [x] Créer `.github/copilot-instructions.md` (instructions GitHub Copilot)
- [x] Créer `Dockerfile` (image API Python, multi-stage, non-root)
- [x] Créer `pyproject.toml` (Ruff, mypy, pytest config)
- [x] Créer `requirements.txt` + `requirements-dev.txt`
- [x] Créer `.pre-commit-config.yaml` (Ruff, mypy, detect-secrets)
- [x] Créer `.gitignore` + `.env.example`
- [x] Configurer les secrets GitHub (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID)
- [x] Configurer les règles de protection de branche `main` sur GitHub
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
| 2026-06-12 | Implémentation craftsmanship : `.gitignore`, `.env.example`, `pyproject.toml`, `requirements*.txt`, `.vscode/` (settings, extensions, mcp), `.github/copilot-instructions.md`, `.github/pull_request_template.md`, `.pre-commit-config.yaml`, `Dockerfile`, `.github/workflows/` (ci, deploy, codeql) | ✅ Terminé |
| 2026-06-12 | Réorganisation : déplacement des .md dans `docs/`, mise à jour des liens internes | ✅ Terminé |
| 2026-06-12 | Création `infra/provision.sh` : provisionnement complet Azure en 1 script (RG, ACR, MySQL, Key Vault, Container Apps, OIDC) | ✅ Terminé |
| 2026-06-13 | Provisionnement Azure exécuté (RG, ACR, Key Vault, MySQL, Container Apps Env + App) + secrets GitHub + 2 federated credentials OIDC (`ref:refs/heads/main` et `environment:dev`) | ✅ Terminé |
| 2026-06-13 | Fix `deploy.yml` : suppression de l'étape `curl` (cert DigiCert déjà versionné, exit 60) — commit `f67e3f5` | ✅ Terminé |
| 2026-06-13 | Fix pull ACR : identité managée system-assigned du Container App + rôle AcrPull + `containerapp registry set --identity system` | ✅ Terminé |
| 2026-06-13 | **Déploiement Azure opérationnel** : `/health` répond `{status: ok}` sur https://bizplan-api-dev.salmondune-1b29666f.westeurope.azurecontainerapps.io | ✅ Terminé |

---

## 2. Architecture — Infrastructure technique

### Tâches

- [ ] Valider le schéma d'architecture final (cf. `docs/architecture.md`)
- [x] Créer le script de provisionnement Azure (`infra/provision.sh`)
- [x] **Exécuter** `bash infra/provision.sh dev` (par Benjamin)
- [x] Ajouter les secrets GitHub Actions (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID)
- [ ] Récupérer la `DATABASE_URL` depuis Key Vault et la partager avec Mauricette
- [ ] Configurer les variables d'environnement dans Container Apps (via Key Vault reference)
- [ ] Valider la connectivité Container Apps ↔ MySQL

### Journal

| Date | Action | Résultat |
|---|---|---|
| 2026-06-12 | Création du fichier `architecture.md` | ✅ Documenté |

---

## 3. Business & User Stories

> Backlog détaillé (Epics + US + critères d'acceptation) dans [`docs/backlog.md`](./docs/backlog.md).

### Statut global

| Epic | Stories | Points | Statut |
|---|---|---|---|
| Epic 1 — Saisie formulaire | 4 | 15 | ⬜ À démarrer |
| Epic 2 — Score de pertinence | 3 | 11 | ⬜ À démarrer |
| Epic 3 — Génération BP (agents IA) | 5 | 34 | ⬜ À démarrer |
| Epic 4 — Consultation & export | 3 | 13 | ⬜ À démarrer |
| Epic 5 — Infrastructure & données | 3 | 13 | ⬜ À démarrer |
| Epic 6 — Qualité & sécurité | 3 | 8 | ✅ En place (CI/CD, secrets) |

### Sprint 0 — Socle technique (priorité immédiate)

- [x] US-5.3 : Scaffolding FastAPI (`app/`, `GET /health`, config pydantic-settings)
- [ ] US-5.1 : Schéma MySQL + migrations (`db/schema.sql`)
- [x] US-6.1 : Valider pipeline CI opérationnelle (lint + tests + build)
- [x] US-6.2 : Valider pipeline déploiement Azure (OIDC → Container Apps)
- [ ] US-6.3 : Secrets — valider detect-secrets + push protection GitHub

### Sprint 1 — Core métier

- [ ] US-1.1 : Formulaire — informations générales projet
- [ ] US-1.2 : Formulaire — hypothèses financières
- [ ] US-1.3 : Formulaire — dimensions stratégiques (6 curseurs)
- [x] US-2.1 : Calcul score de pertinence (déterministe, 6 dimensions pondérées)
- [x] US-2.2 : Endpoint `POST /projects/{id}/score`

### Sprint 2 — Agents IA

- [ ] US-3.1 : Orchestrateur Azure AI Foundry
- [ ] US-3.3 : Agent Financier (3 scénarios)
- [ ] US-3.2 : Agent Analyste (marché + contexte)
- [ ] US-3.4 : Agent Rédacteur (BP 10 sections)
- [ ] US-3.5 : Agent Synthèse (note CODIR)

### Sprint 3 — UX & consultation

- [ ] US-1.4 : Écran récapitulatif avant soumission
- [ ] US-2.3 : Affichage score + graphique radar
- [ ] US-4.1 : Consultation BP dans l'interface
- [ ] US-4.2 : Export BP (PDF + Markdown) + note CODIR
- [ ] US-4.3 : Tableau de bord comparatif multi-projets

### Sprint 4 — Données & soutenance

- [ ] US-5.2 : Jeu de données fictives La Poste (5–10 projets seed)
- [ ] Préparer démo live pour soutenance

### Journal

| Date | Action | Résultat |
|---|---|---|
| 2026-06-12 | Initialisation des Epics dans TODO | ✅ Draft |
| 2026-06-12 | Création `docs/backlog.md` : 6 Epics, 21 US, 94 points, critères d'acceptation complets | ✅ Terminé |

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
| 2 | Numéros de tickets JIRA (BIZ-xx) non encore assignés | Création du projet JIRA | ✅ Levé (import effectué) |
| 3 | Secrets Azure non provisionnés | Accès souscription Azure | ✅ Levé (provisionné le 2026-06-13) |
