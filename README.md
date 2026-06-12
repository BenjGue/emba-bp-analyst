# BizPlan-IA — Outil de création automatisée de Business Plan pour La Poste

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
3. Une **architecture d'agents IA (Claude)** génère un **business plan complet en 10 sections**.
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

## 3. Stack technique

| Couche | Technologie | Justification |
|---|---|---|
| **Frontend** | HTML/CSS/JS léger (option Streamlit pour le proto) | Rapide à démontrer, zéro friction |
| **Backend / API** | Python **FastAPI** | Async, typage Pydantic (validation JSON native), OpenAPI auto |
| **Base de données** | **MySQL** | Imposé par le cas ; projets/hypothèses/scénarios relationnels |
| **IA générative** | **Claude (Sonnet 4.6)** via API + **Azure AI Foundry Agents** | Qualité de rédaction, sorties JSON structurées, orchestration multi-agents |
| **Format d'échange** | **JSON structuré** (entrée/sortie) | Intégration backend, validation systématique |
| **Hébergement** | **Microsoft Azure** (services managés) | Scalabilité, sécurité, services IA natifs |

L'architecture détaillée (agents spécialisés, services Azure, justification des choix) est dans [`architecture.md`](./docs/architecture.md).

## 4. Architecture en bref

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────────────┐
│   Frontend   │────▶│  API FastAPI     │────▶│  Orchestrateur d'agents │
│ (formulaire) │◀────│ (validation JSON)│◀────│   (Azure AI Foundry)    │
└──────────────┘     └────────┬─────────┘     └───────────┬─────────────┘
                              │                            │
                     ┌────────▼─────────┐    ┌─────────────▼──────────────┐
                     │   MySQL (Azure)  │    │ Agents spécialisés Claude  │
                     │ projets, scénarios│   │ • Analyste                 │
                     │ hypothèses, risques│  │ • Financier (scénarios)    │
                     └──────────────────┘    │ • Scoring                  │
                                             │ • Rédacteur BP (10 sec.)   │
                                             │ • Synthèse CODIR           │
                                             └────────────────────────────┘
```

## 5. Documentation du projet

Ce README est le point d'entrée. Il pointe vers cinq documents spécialisés :

| Document | Contenu |
|---|---|
| 📐 [`architecture.md`](./docs/architecture.md) | Architecture **agentic**, déploiement **Azure**, services managés, **Azure AI Foundry**, justification des arbitrages |
| 🛠️ [`craftsmanship.md`](./docs/craftsmanship.md) | Ingénierie logicielle & automatisation : **JIRA**, **VSCode + serveur MCP JIRA**, **GitHub**, **GitHub Actions**, sécurité du code, **GitHub Advanced Security**, pipeline streamliné |
| 🤖 [`AI-rules.md`](./docs/AI-rules.md) | Setup & fichiers pour **forcer les bonnes pratiques IA** : commentaires, tests unitaires, documentation, branching par feature |
| 📦 [`livrable.md`](./docs/livrable.md) | **Tous les livrables attendus**, mappés aux critères d'évaluation |
| ⚙️ [`How-to-setup.md`](./docs/How-to-setup.md) | **Installation** de tout l'environnement : comptes (GitHub, JIRA, Anthropic, Azure), VSCode, Python, MySQL, MCP |

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
# 1. Cloner et configurer (détails dans How-to-setup.md)
git clone https://github.com/BenjGue/emba-bp-analyst.git
cd emba-bp-analyst

# 2. Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # renseigner ANTHROPIC_API_KEY, MySQL, Azure

# 3. Base de données
mysql -u root -p < db/schema.sql && mysql -u root -p < db/seed.sql

# 4. Lancer l'API
uvicorn app.main:app --reload

# 5. Frontend
open frontend/index.html    # ou : streamlit run frontend/app.py
```

Procédure complète d'installation : [`How-to-setup.md`](./docs/How-to-setup.md).

---

*BizPlan-IA — Executive MBA EPITECH P2026 — Benjamin Guérin & Mauricette.*
