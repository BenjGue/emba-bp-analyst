# Session Handoff — BizPlan-IA

> **But de ce fichier** : permettre de reprendre le travail à froid (nouvelle session, autre poste, autre personne) **sans rien re-découvrir**. Il décrit comment l'app tourne, où elle est déployée, l'architecture, l'outillage (JIRA/MCP), les commandes utiles et l'état courant.
>
> Dernière mise à jour : **2026-06-15**.

---

## 1. TL;DR — l'essentiel en 10 lignes

- **Projet** : BizPlan-IA — création automatisée de Business Plans + scoring de pertinence de projets internes (La Poste). Démonstrateur académique EMBA/Epitech.
- **Stack** : Python 3.12 / **FastAPI** / SQLAlchemy / SQLite (dev) ou **MySQL** (cible Azure) / front statique (HTML/CSS/JS vanilla) servi par FastAPI.
- **L'app tourne en PROD sur Azure Container Apps** (pas en local) :
  **https://bizplan-api-dev.salmondune-1b29666f.westeurope.azurecontainerapps.io**
- **Déploiement** : push sur `main` → GitHub Actions `deploy.yml` → build ACR → `az containerapp update`.
- **E2E** : Playwright (`e2e/`) ciblant l'URL Azure ; lancé auto après chaque déploiement (`e2e.yml`).
- **Suivi projet** : **JIRA** projet `BIZ` via MCP Atlassian + API REST (transitions/commentaires).
- **État** : tout le backlog (Epics 1→6) est implémenté et mergé. Restent : BIZ-39 (E2E, *En cours*), BIZ-29 (migrations/persistance prod), BIZ-27 (secret scanning), BIZ-32 (doublon de BIZ-36, à fermer).

---

## 2. Où tourne l'application

### 2.1 Production (Azure)
- **URL publique** : https://bizplan-api-dev.salmondune-1b29666f.westeurope.azurecontainerapps.io
- **Health check** : `GET /health` → `{ "status": "ok" }`
- **UI** : `/` (single-page app servie depuis `app/static/index.html`)
- **OpenAPI / Swagger** : `/docs`

### 2.2 Ressources Azure (toutes dans un seul Resource Group)
| Ressource | Nom | Rôle |
|---|---|---|
| Resource Group | `rg-bizplan-dev` | Conteneur de tout l'environnement dev |
| Container Registry | `acrbizplandev` (`acrbizplandev.azurecr.io`) | Images Docker de l'API |
| Container Apps Env | `bizplan-env-dev` | Environnement d'exécution |
| Container App | `bizplan-api-dev` | L'API FastAPI (image `bizplan-api:<sha>`) |
| MySQL Flexible Server | `bizplan-mysql-dev` (db `bizplan`, admin `bizplanadmin`) | Base relationnelle cible |
| Key Vault | `bizplan-kv-dev` | Secrets (DATABASE_URL, clés IA) |
| Région | `westeurope` | — |

> Provisionnement complet via [`infra/provision.sh`](../infra/provision.sh) (`bash infra/provision.sh dev westeurope`). Suppression : `az group delete --name rg-bizplan-dev --yes --no-wait`.

### 2.3 Lancer en local (pour debug uniquement)
L'app **n'a pas besoin** de tourner en local — la cible est Azure. Mais si besoin de reproduire :

```powershell
# Depuis la racine du repo, venv déjà présent dans .venv
$env:DATABASE_URL = "sqlite:///./bizplan.db"   # SQLite par défaut, aucune dépendance externe
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# UI : http://127.0.0.1:8000/   ·   Docs : http://127.0.0.1:8000/docs
```

- Python local : **3.14** dans `.venv` (le projet cible 3.12 mais 3.14 fonctionne pour les tests).
- `ai_enabled=False` par défaut → la génération de BP retombe en **mode template déterministe** (aucun appel réseau, pas de clé IA requise). Voir `app/config.py`.

---

## 3. Architecture (résumé opérationnel)

> Détail complet et arbitrages dans [`docs/architecture.md`](./architecture.md).

- **Principe clé** : *l'IA rédige et raisonne, le backend valide et calcule*. Le **score de pertinence est calculé côté code** (déterministe, auditable), jamais par l'IA.
- **Frontend** : `app/static/` (`index.html`, `app.js`, `style.css`) — SPA vanilla, routeur minimal, wizard 4 étapes (Projet → Finances → Stratégie → Récap).
- **Backend FastAPI** : `app/`
  - `main.py` — assemble l'app, monte `/static`, sert `/`.
  - `config.py` — `pydantic-settings` (env `.env.local`, jamais commité).
  - `db.py` — engine SQLAlchemy + `init_db()` au lifespan.
  - `routers/` — `health.py`, `projects.py` (gros du CRUD + score + génération + export + import xlsx), `score.py`.
  - `services/` — logique métier : `projects.py`, `financials.py`, `scoring.py`, `generation.py`, `export.py`, `imports.py`, et `services/ai/` (client httpx, agents, prompts, description assistée).
  - `schemas/` — modèles Pydantic (validation entrée/sortie).
  - `models/` — modèles SQLAlchemy.
- **Multi-agents IA (EPIC 3)** : Orchestrateur + Analyste + Financier + Scoring (assiste seulement) + Rédacteur BP (10 sections) + Synthèse CODIR. Cible : Azure AI Foundry Agent Service ; **plan B** = orchestration applicative directe. Actuellement la génération est en **mode template** (mock déterministe) tant que `ai_enabled=False`.

### Endpoints principaux (`/projects`)
| Méthode | Chemin | Rôle |
|---|---|---|
| POST | `/projects` | Créer un projet |
| GET | `/projects` | Lister (dashboard, filtre `?direction=`) |
| GET/PUT/DELETE | `/projects/{id}` | Lire / modifier / supprimer |
| POST | `/projects/draft-description` | Description assistée IA (502 si IA off→AiResponseError) |
| PUT/GET | `/projects/{id}/financials` | Hypothèses financières |
| POST/GET | `/projects/{id}/financials/import[/file]` | Import Excel (.xlsx) + re-téléchargement |
| PUT | `/projects/{id}/dimensions` | Saisir dimensions + calcule le score |
| POST/GET | `/projects/{id}/score` | Calculer/persister / lire le score |
| POST | `/projects/{id}/generate` | Générer le BP (400 si finances absentes) |
| GET | `/projects/{id}/bp` | Lire le BP |
| GET | `/projects/{id}/export?format=md\|pdf` | Export |

### Règles de validation utiles (Pydantic)
- `nom` 1–200 car., `description` 1–1000 car., `direction` ∈ enum fixe, `duree_estimee_mois` 1–600.
- Finances : montants `>= 0`, `delai_rentabilite_mois` 1–600.
- Dimensions : 6 critères entiers 0–10 (rentabilite, alignement, risque, impact_operationnel, impact_social, faisabilite).
- Pondérations score : Rentabilité 30 %, Alignement 20 %, Risque 20 %, Impact op. 10 %, Impact social 10 %, Faisabilité 10 %.

---

## 4. CI/CD (GitHub Actions)

Repo : **github.com/BenjGue/emba-bp-analyst**. Branche protégée : `main` (squash merge après CI verte).

| Workflow | Fichier | Déclencheur | Rôle |
|---|---|---|---|
| CI | `.github/workflows/ci.yml` | PR / push | Ruff (lint+format), mypy, pytest, build, CodeQL |
| Deploy | `.github/workflows/deploy.yml` | `push: main` | OIDC Azure → `az acr build` → `az containerapp update` |
| E2E | `.github/workflows/e2e.yml` | après `Deploy` réussi / manuel | Playwright contre `vars.E2E_BASE_URL` ; sur échec → crée tickets JIRA via `e2e/scripts/report-failures.js` |
| CodeQL | `.github/workflows/codeql.yml` | hebdo | SAST |

- **Auth Azure** : OIDC (federated credentials), **aucun secret Azure stocké**. Secrets GitHub : `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.
- **Secrets JIRA pour le workflow E2E** : `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` (GitHub Secrets). Variable : `E2E_BASE_URL`.

---

## 5. Tests

### 5.1 Tests unitaires / intégration (pytest)
```powershell
.\.venv\Scripts\python.exe -m pytest          # tous les tests
.\.venv\Scripts\python.exe -m pytest --cov=app # avec couverture (cible >= 80 %)
```
Tests dans `tests/` (miroir de `app/`).

### 5.2 E2E Playwright (`e2e/`)
- **Cible par défaut** : l'URL Azure (voir `e2e/playwright.config.js`, `BASE_URL`). Surcharge via `E2E_BASE_URL`.
- Lancer contre la prod Azure :
  ```powershell
  cd e2e
  npm ci            # première fois
  npx playwright install --with-deps chromium
  npx playwright test            # cible l'URL Azure par défaut
  npx playwright show-report     # rapport HTML
  ```
- Lancer contre un local : `$env:E2E_BASE_URL="http://127.0.0.1:8000"; npx playwright test`
- **Couverture actuelle = 1 seul test happy-path** (`e2e/tests/critical-path.spec.js`) : création → finances → score → génération → export. **Pas de cas d'erreur / négatifs / dashboard / suppression.** À étendre.
- Le `e2e/results.json` peut afficher `skipped: 1` si la cible n'était pas joignable lors du dernier run.

---

## 6. JIRA (suivi obligatoire par US) + MCP

> Détails et snippets dans [memory `/memories/repo/jira.md`] et [`.github/copilot-instructions.md`](../.github/copilot-instructions.md).

- **Instance** : https://ionis-stm-team-ek7kwlup.atlassian.net (FR) — **projet `BIZ`**.
- **Auth** : variables d'environnement utilisateur Windows `JIRA_EMAIL` + `JIRA_API_TOKEN` (Basic auth).

### 6.1 Lecture / recherche / création / update
Outils **MCP Atlassian** :
- `mcp_atlassian_search-jira-issues` (JQL, ex. `project = BIZ ORDER BY status`).
- `mcp_atlassian_get-jira-issue`, `create-jira-issue`, `update-jira-issue`.
- **Pièges** :
  - `create-jira-issue` → `description` = **string simple** ; `issuetype.name` en **français** (`Tâche`, `Story`, `Epic`). « Task » échoue.
  - `update-jira-issue` → `description` au format **ADF** (`{type:"doc",version:1,content:[...]}`).

### 6.2 Transitions de statut & commentaires (NON gérés par MCP)
Utiliser l'**API REST** (`POST /rest/api/3/issue/{KEY}/transitions` et `.../comment`). IDs de transition du workflow BIZ :
- **11** = À faire · **21** = En cours · **31** = Terminé.

Snippet PowerShell (transition) :
```powershell
$e=[Environment]::GetEnvironmentVariable("JIRA_EMAIL","User"); $t=[Environment]::GetEnvironmentVariable("JIRA_API_TOKEN","User")
$b64=[Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$e`:$t"))
$h=@{Authorization="Basic $b64";"Content-Type"="application/json"}
Invoke-RestMethod -Uri "https://ionis-stm-team-ek7kwlup.atlassian.net/rest/api/3/issue/BIZ-XX/transitions" -Method Post -Headers $h -Body (@{transition=@{id="31"}}|ConvertTo-Json)
```
Commentaire d'implémentation : script [`scripts/jira-add-comment.ps1`](../scripts/jira-add-comment.ps1) `-IssueKey BIZ-XX -CommentJsonPath file.json` (corps ADF).

### 6.3 Cycle de vie obligatoire d'une US
1. Avant de coder → transition **21** (En cours).
2. Travail technique imprévu → créer un ticket **`TECH —`** (type `Tâche`), le référencer dans les commits.
3. Après implémentation → **commentaire ADF** (logique, fichiers créés/modifiés, couverture tests, n° PR, résultat déploiement).
4. PR mergée + déploiement vert → transition **31** (Terminé).

### 6.4 Setup MCP (si la session repart de zéro)
- Config : `.vscode/mcp.json` (serveur `atlassian-mcp@latest`).
- Script d'onboarding : [`scripts/setup-jira-mcp.ps1`](../scripts/setup-jira-mcp.ps1). Voir aussi `docs/How-to-setup.md`.

---

## 7. Conventions de dev (rappel)

- **Ruff** (line-length 100, double quotes) — `ruff check` + `ruff format --check` doivent passer.
- Typage strict (`from __future__ import annotations`), docstrings Google sur le public, pas de `Any` non justifié.
- **Conventional Commits** + réf. ticket : `feat(scope): … (BIZ-xx)`.
- Branche par US : `feat/biz-<n>-<slug>`. PR vers `main` (squash, CI verte requise).
- **Sécurité** : aucun secret en dur ; `pydantic-settings` ; ORM paramétré ; validation Pydantic à la frontière.

---

## 8. État courant & reste à faire (au 2026-06-15)

### Implémenté & mergé (JIRA = Terminé)
- Epic 1 (saisie projet/finances/dimensions/récap), Epic 2 (score), Epic 3 (agents IA, mode template), Epic 4 (consultation/export/dashboard), Epic 5 (schéma/seed/scaffolding), Epic 6 (CI/CD/deploy). Plus BIZ-30/31/33/34/35/36/37/38 (validations, suppression, description IA, import Excel, socle IA).
- Dernières stories (git) : **BIZ-39** (E2E auto), **BIZ-36** (import Excel), **BIZ-37 + BIZ-14→18** (Epic 3 IA).

### Ouvert (reste à faire)
| Ticket | Statut | Sujet |
|---|---|---|
| **BIZ-39** | En cours | E2E Playwright auto après merge + tickets bug auto (mergé #11, à passer en Terminé) |
| **BIZ-29** | À faire | TECH — migrations Alembic + persistance prod (Key Vault / MySQL) |
| **BIZ-27** | À faire | US-6.3 — secret scanning (detect-secrets + push protection) |
| **BIZ-32** | À faire | **Doublon de BIZ-36** (import Excel déjà fait) → à fermer |

### Pistes de qualité identifiées
- **E2E trop léger** : un seul happy-path. Ajouter cas négatifs (validation, suppression, dashboard, échec IA/export), comme l'exige BIZ-39 (« parcours critiques » au pluriel).
- **TODO.md racine est obsolète** : son tableau d'Epics dit encore « À démarrer » pour du travail terminé.

---

## 9. Fichiers à consulter en priorité au redémarrage
1. Ce fichier — [`docs/SESSION-HANDOFF.md`](./SESSION-HANDOFF.md)
2. [`docs/architecture.md`](./architecture.md) — architecture & arbitrages
3. [`docs/backlog.md`](./backlog.md) — Epics/US + critères d'acceptation
4. [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) — règles projet (JIRA, sécurité, tests)
5. [memory `/memories/repo/jira.md`] — mémoire JIRA (transitions, pièges MCP)
6. [`infra/provision.sh`](../infra/provision.sh) — provisionnement Azure
