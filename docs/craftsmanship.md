# Craftsmanship — Ingénierie logicielle & automatisation

> Comment nous fabriquons le logiciel : gestion de projet, environnement de dev, contrôle de version, intégration continue, sécurité du code. Objectif : une **pipeline de développement streamlinée et optimisée** pour un binôme.

← Retour au [README](../README.md)

---

## 1. Chaîne d'outils

```
JIRA  ──(MCP)──▶  VSCode + IA  ──▶  GitHub  ──▶  GitHub Actions  ──▶  Azure
(planif.)         (dev assisté IA)   (source)      (CI/CD + sécurité)   (déploiement)
   ▲                                     │
   └───────────── traçabilité ticket ◀───┘
              (smart commits : "BIZ-12 ...")
```

Chaque maillon a un rôle unique et **automatise** le passage au suivant. Un développeur ne fait que coder dans VSCode et ouvrir une PR ; le reste est automatisé.

> **Choix de l'assistant IA** — deux options équivalentes, voir détail en [section 3.1](#31-choix-de-lassistant-ia).

## 2. JIRA — Gestion de projet

### 2.1 Organisation

- **Projet JIRA** : `BIZ` (clé courte → préfixe des branches et commits).
- **Méthode** : Kanban léger (binôme) avec un board simple `À faire → En cours → En revue → Done`.
- **Découpage** : **Epics** (ex. *Score de pertinence*, *Génération BP*, *Base MySQL*, *Frontend*, *Agents IA*) → **Stories** → **Sous-tâches**.
- **Definition of Done** attachée à chaque story (cf. [`AI-rules.md`](./AI-rules.md)).

### 2.2 Convention de référencement

Toute branche, commit et PR référence un ticket : `BIZ-12`. Cela donne une **traçabilité totale** ticket ↔ code.

```
feature/BIZ-12-calcul-score-pondere
fix/BIZ-27-json-mal-forme-agent-financier
```

### 2.3 Serveur MCP vers JIRA (dev assisté IA)

Nous connectons l'assistant IA à JIRA via un **serveur MCP** (Model Context Protocol). Bénéfice : l'IA peut **lire le contexte d'un ticket**, **mettre à jour son statut** et **créer des sous-tâches** sans quitter l'éditeur.

> **Compatibilité** : le serveur MCP est nativement supporté par **Claude Code** (Option A). Avec **GitHub Copilot** (Option B), le support MCP est disponible en mode agent depuis Copilot Chat — vérifier la version de l'extension.

Configuration MCP (extrait, voir [`How-to-setup.md`](./How-to-setup.md) pour l'installation) :

```json
// .vscode/mcp.json
{
  "servers": {
    "jira": {
      "command": "npx",
      "args": ["-y", "@atlassian/mcp-server-jira"],
      "env": {
        "JIRA_URL": "https://<votre-domaine>.atlassian.net",
        "JIRA_EMAIL": "${env:JIRA_EMAIL}",
        "JIRA_API_TOKEN": "${env:JIRA_API_TOKEN}"
      }
    }
  }
}
```

Exemples d'usage en langage naturel :
- *« Récupère les critères d'acceptation de BIZ-12 et implémente le calcul du score. »*
- *« Passe BIZ-12 en "En revue" et résume ce que j'ai fait dans un commentaire. »*

> ⚠️ Le `JIRA_API_TOKEN` n'est **jamais** commité : il vit dans une variable d'environnement locale / Key Vault.

## 3. VSCode — Environnement de développement

### 3.1 Choix de l'assistant IA

Deux options sont supportées — choisissez selon votre accès :

#### Option A — Claude Code + plugin VSCode *(recommandé pour ce projet)*

| Avantage | Détail |
|---|---|
| Contexte long (200 k tokens) | Lit tout le repo d'un coup |
| Intégration MCP native | Connecte JIRA, GitHub, Azure sans friction |
| Mode « agentique » | Peut exécuter des commandes terminal, créer des fichiers |
| Plugin VSCode | Extension **Claude** (Anthropic) → chat + inline edit |

Installation : `npm install -g @anthropic-ai/claude-code` puis activer l'extension **Claude** dans VSCode.  
Authentification : variable `ANTHROPIC_API_KEY` dans `.env.local` (jamais commitée).

#### Option B — GitHub Copilot (licence scolaire GitHub Education)

| Avantage | Détail |
|---|---|
| Gratuit pour étudiants | Via **GitHub Education** → [education.github.com](https://education.github.com) |
| Natif VSCode | Extensions **GitHub Copilot** + **Copilot Chat** |
| Inline completion | Suggestions en temps réel dans l'éditeur |
| Copilot Chat | Interface conversationnelle dans le panneau latéral VSCode |

Activation : demander le pack étudiant sur [education.github.com/pack](https://education.github.com/pack) (validation par email ou carte étudiante). Une fois approuvé, Copilot est disponible gratuitement via l'extension VSCode.

> ⚠️ Les deux options peuvent coexister dans VSCode, mais **une seule** doit être configurée comme assistant principal pour garder le workflow cohérent.

### 3.2 Extensions standardisées

Extensions standardisées pour le binôme (fichier `.vscode/extensions.json` versionné) :

| Extension | Usage |
|---|---|
| Python + Pylance | Typage, IntelliSense |
| Ruff | Lint + format ultra-rapide |
| **Claude** *(Option A)* ou **GitHub Copilot** *(Option B)* | Dev assisté IA (cf. [`AI-rules.md`](./AI-rules.md)) |
| GitLens | Historique et blame |
| MySQL | Requêtes et inspection de la base |
| Docker | Build/inspection des images conteneur |
| YAML | Édition des workflows GitHub Actions |

Réglages partagés via `.vscode/settings.json` : format à la sauvegarde, Ruff comme formatter, exclusions de fichiers. Tout l'éditeur est ainsi **identique des deux côtés** du binôme.

## 4. GitHub — Contrôle de version

### 4.1 Stratégie de branches (branching)

**Trunk-based léger** avec branches de feature courtes :

- `main` : toujours déployable, **protégée**.
- `feature/BIZ-xx-...`, `fix/BIZ-xx-...` : éphémères, fusionnées par PR puis supprimées.
- Pas de branche `develop` (sur-ingénierie pour un binôme).

### 4.2 Règles de protection de `main`

- ❌ **Pas de push direct** sur `main`.
- ✅ **1 revue approuvée** obligatoire (l'autre membre du binôme).
- ✅ **Tous les checks CI verts** (tests, lint, sécurité) avant merge.
- ✅ Branche à jour avec `main` avant merge.
- ✅ Historique **linéaire** (squash & merge).

### 4.3 Convention de commits

**Conventional Commits** + référence ticket :

```
feat(score): ajoute la normalisation min-max des critères  (BIZ-12)
fix(agent-financier): corrige le JSON mal formé sur scénario haut  (BIZ-27)
docs(readme): complète la section architecture
test(score): couvre les bornes 0 et 100
```

Le préfixe permet de **générer automatiquement le changelog** et de classer le travail.

### 4.4 Pull Request

Template de PR versionné (`.github/pull_request_template.md`) imposant : lien JIRA, description, captures, checklist (tests passés, doc à jour, pas de secret). Voir la *Definition of Done* dans [`AI-rules.md`](./AI-rules.md).

## 5. GitHub Actions — CI/CD

Pipeline déclenchée à chaque PR et à chaque merge sur `main`. Objectif : **rapide, parallèle, bloquante sur l'essentiel**.

### 5.1 Workflow CI (`.github/workflows/ci.yml`)

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements-dev.txt
      - name: Lint & format
        run: ruff check . && ruff format --check .
      - name: Type check
        run: mypy app/
      - name: Tests unitaires + couverture
        run: pytest --cov=app --cov-report=xml --cov-fail-under=80

  build-image:
    needs: quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image API
        run: docker build -t bizplan-api:${{ github.sha }} .
```

### 5.2 Workflow de déploiement (`.github/workflows/deploy.yml`)

Sur merge `main` : build de l'image → push vers **Azure Container Registry** → déploiement sur **Azure Container Apps**. Authentification via **OIDC** (federated credentials), **sans secret stocké**.

```yaml
name: Deploy
on:
  push:
    branches: [main]
permissions:
  id-token: write          # OIDC vers Azure, pas de secret
  contents: read
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - run: az acr build -r bizplanacr -t bizplan-api:${{ github.sha }} .
      - run: az containerapp update -n bizplan-api -g rg-bizplan \
               --image bizplanacr.azurecr.io/bizplan-api:${{ github.sha }}
```

### 5.3 Optimisations de pipeline

- **Cache** des dépendances pip et des layers Docker → builds plus rapides.
- **Jobs parallèles** (lint, types, tests indépendants).
- **Fail fast** : la qualité bloque avant le build inutile.
- **Concurrency** : annule les runs obsolètes d'une même PR.
- **Path filters** : ne relance pas tout si seul un `.md` change.

## 6. Sécurité du code — GitHub Advanced Security

La sécurité est **automatisée et intégrée** à la pipeline (« shift-left »).

### 6.1 Composants activés

| Fonction | Rôle | Sortie |
|---|---|---|
| **CodeQL** (SAST) | Analyse statique : injections, secrets, vulnérabilités logiques | Alertes dans l'onglet *Security* + annotations PR |
| **Secret scanning** + **push protection** | Détecte/bloque clés API, tokens commités (ex. `ANTHROPIC_API_KEY`) | Blocage du push, alerte |
| **Dependency review** + **Dependabot** | Vulnérabilités dans les dépendances ; PR de mise à jour auto | PR automatiques, blocage si CVE critique en PR |

### 6.2 Workflow CodeQL (`.github/workflows/codeql.yml`)

```yaml
name: CodeQL
on:
  push: { branches: [main] }
  pull_request:
  schedule: [{ cron: "0 6 * * 1" }]   # scan hebdo
jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions: { security-events: write }
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with: { languages: python, javascript }
      - uses: github/codeql-action/analyze@v3
```

### 6.3 Le « report » Advanced Security

L'onglet **Security** de GitHub centralise un **rapport** consolidé : alertes CodeQL (par sévérité), secrets détectés, vulnérabilités de dépendances, et leur **résolution dans le temps**. C'est notre **preuve de sécurité** pour la soutenance : on montre un dépôt sans alerte critique, avec scans datés et Dependabot actif.

> Règle binôme : **aucune alerte critique/haute non traitée** ne peut rester sur `main`. Une alerte = un ticket JIRA `BIZ-xx` + une PR de correction.

## 7. Pipeline de dev de bout en bout (résumé)

```
1. JIRA : on prend un ticket BIZ-xx
2. VSCode : l'assistant IA lit le ticket via MCP (Claude Code ou Copilot) et code la feature
3. Branche feature/BIZ-xx ; commits Conventional Commits
4. Push → push protection (secrets) bloque si fuite
5. PR ouverte → CI : lint + types + tests + CodeQL + Dependency review
6. Revue par l'autre membre du binôme (1 approbation requise)
7. Squash & merge sur main (checks verts obligatoires)
8. Deploy auto vers Azure Container Apps (OIDC, sans secret)
9. JIRA : ticket passé en Done (via smart commit ou MCP)
```

Résultat : **un seul geste manuel** (coder + relire), tout le reste est automatisé, tracé et sécurisé.

---

← [architecture.md](./architecture.md) · Suite : [`AI-rules.md`](./AI-rules.md)
