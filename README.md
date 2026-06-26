# BizPlan-IA — Outil de création automatisée de Business Plan pour La Poste

<!-- Badges de statut : générés à la volée par GitHub Actions / shields.io -->
[![CI](https://github.com/BenjGue/emba-bp-analyst/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/BenjGue/emba-bp-analyst/actions/workflows/ci.yml)
[![CodeQL / SAST](https://github.com/BenjGue/emba-bp-analyst/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/BenjGue/emba-bp-analyst/actions/workflows/codeql.yml)
[![Deploy](https://github.com/BenjGue/emba-bp-analyst/actions/workflows/deploy.yml/badge.svg?branch=main)](https://github.com/BenjGue/emba-bp-analyst/actions/workflows/deploy.yml)
[![E2E](https://github.com/BenjGue/emba-bp-analyst/actions/workflows/e2e.yml/badge.svg)](https://github.com/BenjGue/emba-bp-analyst/actions/workflows/e2e.yml)
[![Security → JIRA](https://github.com/BenjGue/emba-bp-analyst/actions/workflows/security-to-jira.yml/badge.svg)](https://github.com/BenjGue/emba-bp-analyst/actions/workflows/security-to-jira.yml)
[![Couverture des tests](https://img.shields.io/badge/couverture-96.87%25-brightgreen)](https://github.com/BenjGue/emba-bp-analyst/actions/workflows/ci.yml)
[![Dernier build](https://img.shields.io/github/last-commit/BenjGue/emba-bp-analyst/main?label=dernier%20build)](https://github.com/BenjGue/emba-bp-analyst/commits/main)
[![Python](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Ruff](https://img.shields.io/badge/style-ruff-261230?logo=ruff&logoColor=white)](https://docs.astral.sh/ruff/)

> Démonstrateur d'IA générative qui assiste un porteur de projet dans la création d'un **business plan complet, chiffré et argumenté**, et qui produit un **score de pertinence (0–100)** pour aider le comité de direction (CODIR) de La Poste à **prioriser** ses projets.

**Projet 2 — Executive MBA EPITECH (Promotion 2026)**
**Binôme :** Benjamin Guérin & Mauricette

---

## 1. Le problème métier

La Poste, entreprise à mission, évalue en permanence de nombreux projets internes (innovation, digitalisation, intrapreneuriat, RH, projets territoriaux…). Chaque projet exige un business plan structuré pour que le CODIR statue sur :

- la **faisabilité**,
- la **rentabilité**,
- l'**alignement stratégique**,
- l'**impact opérationnel**,
- les **risques**,
- le **coût d'opportunité** par rapport aux autres projets.

Or aujourd'hui, la construction d'un business plan est **longue**, **hétérogène** selon les équipes, **dépendante de compétences financières inégales** et **difficile à comparer** d'un projet à l'autre.

## 2. Notre solution

Un **démonstrateur web** où :

1. Le porteur de projet **saisit les informations clés** (formulaire).
2. L'outil **calcule automatiquement un score de pertinence** sur 6 dimensions.
3. Une **architecture multi-agents** (**6 agents IA**, orchestrés **par le code** — service FastAPI, l'inférence étant servie par **Azure AI Foundry**) génère un **business plan complet en 11 sections**.
4. L'IA propose **3 scénarios financiers** (bas, médian, haut).
5. L'IA rédige une **note de synthèse CODIR** d'une page.
6. Le manager **télécharge / copie** la synthèse et consulte un **tableau de bord** comparatif.

### Le score de pertinence (cœur de la valeur)

Score final **0–100**, agrégé sur **6 dimensions pondérées** :

| Dimension | Pondération |
|---|---|
| Rentabilité (RoI, délai de retour) | 30 % |
| Alignement stratégique | 20 % |
| Risque (technique + humain) | 20 % |
| Impact opérationnel | 10 % |
| Impact social / environnemental | 10 % |
| Faisabilité technique | 10 % |

> Formule : **normalisation** de chaque critère sur [0,1] → **pondération** → somme → mise à l'échelle sur 100. Détail et exemple chiffré dans [`livrable.md`](./docs/livrable.md).

> Seuils de recommandation (calculés côté backend) : **≥ 70 → Go** (pertinence élevée) · **40–69 → Go conditionnel** · **< 40 → No-Go en l'état**.

## 3. Stack technique

| Couche | Technologie | Justification |
|---|---|---|
| **Frontend** | HTML/CSS/JS léger (`app/static/`, servi par FastAPI) | Rapide à démontrer, zéro friction, une seule origine front+API |
| **Backend / API** | Python **FastAPI** | Async, typage Pydantic (validation JSON native), OpenAPI auto |
| **Base de données** | **MySQL** | Imposé par le cas ; projets/hypothèses/scénarios relationnels |
| **IA générative** | **Azure AI Foundry** (inférence `chat/completions`, modèle **configurable/agnostique** : Claude, GPT…) + orchestration multi-agents **applicative** (backend FastAPI) | Qualité de rédaction, sorties JSON structurées, indépendance vis-à-vis du fournisseur de modèle |
| **Format d'échange** | **JSON structuré** (entrée/sortie) | Intégration backend, validation systématique |
| **Hébergement** | **Microsoft Azure** (services managés) | Scalabilité, sécurité, services IA natifs |

L'architecture détaillée (agents spécialisés, services Azure, justification des choix) est dans [`architecture.md`](./docs/architecture.md).

## 4. Architecture en bref

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────────────┐
│   Frontend   │────▶│  API FastAPI     │────▶│  Orchestrateur d'agents │
│ (formulaire) │◄────│ (validation JSON)│◄────│  (backend FastAPI)      │
└──────────────┘     └────────┬─────────┘     └───────────┬─────────────┘
                              │                            │ appels chat/completions
                     ┌────────▼─────────┐    ┌─────────────▼──────────────┐
                     │   MySQL (Azure)  │    │ Azure AI Foundry           │
                     │ projets, scénarios│   │ (1 déploiement de modèle) │
                     │ hypothèses, risques│  │ 6 agents (prompts dédiés) :│
                     └─────────────────┘    │ • Description (pré-saisie)  │
                                             │ • Évaluateur (6 notes)     │
   Le score est calculé de façon             │ • Analyste                 │
   100 % déterministe (scoring.py),          │ • Financier (commentaire)  │
   ce n'est pas un agent IA.                 │ • Rédacteur BP (11 sec.)   │
   L'orchestration est du code               │ • Synthèse CODIR           │
   (generation.py), pas un agent.            └────────────────────────────┘
```

## 5. Documentation du projet

Ce README est le point d'entrée. Il pointe vers sept documents spécialisés :

| Document | Contenu |
|---|---|
| 📐 [`architecture.md`](./docs/architecture.md) | Architecture **agentic**, déploiement **Azure**, services managés, **Azure AI Foundry**, justification des arbitrages |
| 🗺️ [`diagrammes.md`](./docs/diagrammes.md) | **Diagrammes** Mermaid : infrastructure Azure, workflow métier (génération du BP), workflow de développement (JIRA → prod) |
| 🛠️ [`craftsmanship.md`](./docs/craftsmanship.md) | Ingénierie logicielle & automatisation : **JIRA**, **VSCode + serveur MCP JIRA**, **GitHub**, **GitHub Actions**, sécurité du code, **GitHub Advanced Security**, pipeline streamliné |
| 🤖 [`AI-rules.md`](./docs/AI-rules.md) | Setup & fichiers pour **forcer les bonnes pratiques IA** : commentaires, tests unitaires, documentation, branching par feature |
| 📦 [`livrable.md`](./docs/livrable.md) | **Tous les livrables attendus**, mappés aux critères d'évaluation |
| ⚙️ [`How-to-setup.md`](./docs/How-to-setup.md) | **Installation** de tout l'environnement : comptes (GitHub, JIRA, Azure AI Foundry, Azure), VSCode, Python, MySQL, MCP |
| 📋 [`backlog.md`](./docs/backlog.md) | **6 Epics · 21 User Stories · 94 points** — critères d'acceptation complets, ordre de développement par sprint |

## 6. Organisation du binôme

| Rôle | Benjamin | Mauricette |
|---|---|---|
| **Lead** | Backend / IA / Architecture Azure | Frontend / Score de pertinence / Base MySQL |
| **Backup** | Revue des PR frontend | Revue des PR backend |

> Règle d'or : **tout passe par une Pull Request relue par l'autre** (cf. [`craftsmanship.md`](./docs/craftsmanship.md)). Aucun merge direct sur `main`.

## 7. Périmètre

**Obligatoire** : score de pertinence · base MySQL · génération auto du BP · analyse IA (forces/faiblesses/risques) · interface web simple · note CODIR.

**Optionnel (si temps)** : visualisations avancées (radar, heatmap) · simulation d'impact d'une décision · analyse d'un fichier Excel · chatbot d'aide au porteur de projet.

## 8. Démarrage rapide

```bash
# 1. Cloner (détails dans How-to-setup.md)
git clone https://github.com/BenjGue/emba-bp-analyst.git
cd emba-bp-analyst

# 2. Environnement Python
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt

# 3. Configuration (optionnelle en local : SQLite par défaut, IA désactivée)
#    Créer un fichier .env.local pour activer MySQL et/ou l'IA Azure AI Foundry :
#      DATABASE_URL=mysql+pymysql://UTILISATEUR:MOT_DE_PASSE@HOTE/bizplan  # pragma: allowlist secret
#      AI_ENABLED=true
#      AI_ENDPOINT=...  AI_DEPLOYMENT=...  AI_API_KEY=...  (ou AI_USE_ENTRA_ID=true)

# 4. Base de données : migrations Alembic + jeu de données de démo
alembic upgrade head            # (auto au démarrage si MySQL ; SQLite créé à la volée)
python scripts/seed.py          # données fictives de démonstration

# 5. Lancer l'application (API + frontend servis ensemble)
uvicorn app.main:app --reload
#   Frontend : http://127.0.0.1:8000/      ·  API docs : http://127.0.0.1:8000/docs
```

Procédure complète d'installation : [`How-to-setup.md`](./docs/How-to-setup.md).

## 9. Serveur MCP Jira (GitHub Copilot Agent Mode)

Le serveur MCP Atlassian est configuré dans [`.vscode/mcp.json`](./.vscode/mcp.json) et partagé dans le dépôt. Il permet à GitHub Copilot en mode Agent de lire et créer des tickets Jira directement depuis VS Code.

### Prérequis : token API Atlassian

1. Générez un token sur <https://id.atlassian.com/manage-profile/security/api-tokens>
2. Exécutez le script de configuration **(une seule fois par poste)** :

```powershell
# Dans un terminal PowerShell, à la racine du projet
.\scripts\setup-jira-mcp.ps1
```

Le script enregistre `JIRA_EMAIL` et `JIRA_API_TOKEN` en variables d'environnement **persistantes** (niveau utilisateur Windows). Ces variables ne sont jamais commitées.

3. **Redémarrez VS Code** pour que les variables soient chargées.
4. Lancez le serveur : `Ctrl+Shift+P` → **MCP: Start Server** → **jira**.

> ⚠️ Ne jamais mettre de token en dur dans le code ni dans `.vscode/mcp.json`.

---

*BizPlan-IA — Executive MBA EPITECH P2026 — Benjamin Guérin & Mauricette.*
