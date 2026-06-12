# How-to-setup — Installation de l'environnement

> Procédure pas à pas pour installer **tout ce qui est nécessaire** au projet. Certaines étapes sont réservées à **Brice** (admin), d'autres à **Mauricette** uniquement, les autres sont à faire par les **deux membres**.

> **Pas de test en local** — la base de données tourne sur l'environnement Azure `dev`. On pousse directement via la pipeline CI/CD.

← Retour au [README](./README.md)

---

## 0. Pré-requis & vue d'ensemble

| À créer / installer | Qui | Coût |
|---|---|---|
| Compte **GitHub** | Les deux | Gratuit |
| Compte **Atlassian / JIRA** | Brice (admin) | Gratuit (≤ 10 users) |
| **Assistant IA** — voir §3 | Les deux (choix individuel) | Voir §3 |
| Compte **Azure** | **Brice crée et invite Mauricette** | Couvert par la souscription |
| **VSCode** | Les deux | Gratuit |
| **Python 3.12** | Les deux | Gratuit |
| **Git**, **Node.js** | Les deux | Gratuit |
| ~~MySQL local~~ | ~~Non applicable~~ | — |

Temps estimé : **30–45 min**.

---

## 1. Créer un compte GitHub

1. Aller sur **https://github.com** → *Sign up*.
2. Choisir un identifiant pro, vérifier l'email.
3. (Recommandé) Activer la **2FA** (Settings → Password and authentication).
4. Le dépôt **`emba-bp-analyst`** est **privé** : `https://github.com/BenjGue/emba-bp-analyst`.
   - **Benjamin** : aller dans *Settings → Collaborators → Add people* et saisir l'identifiant GitHub de Mauricette pour lui donner accès.
   - **Mauricette** : communiquer ton identifiant GitHub à Benjamin, puis accepter l'invitation reçue par email.
5. Activer **GitHub Advanced Security** sur le dépôt (Settings → Code security) : *CodeQL*, *Secret scanning + push protection*, *Dependabot*.

> Étudiants : **GitHub Student Developer Pack** (https://education.github.com) débloque des avantages gratuits.

---

## 2. Créer un compte JIRA (Atlassian)

1. Aller sur **https://www.atlassian.com/software/jira** → *Get it free*.
2. Créer un site : `https://<votre-domaine>.atlassian.net`.
3. Créer un **projet** de clé **`BIZ`** (type Kanban).
4. Inviter le binôme (Settings → People).
5. **Générer un token API** (pour le MCP, §8) :
   - https://id.atlassian.com/manage-profile/security/api-tokens → *Create API token* → copier et conserver en lieu sûr.

---

## 3. Configurer l'assistant IA — arbre de décision

> **→ As-tu un compte Claude Code payant ?**
> - **Oui** → [Option A — Claude Code](#option-a--claude-code-compte-payant)
> - **Non** → [Option B — GitHub Copilot Education (gratuit étudiant)](#option-b--github-copilot-education-gratuit)

---

### Option A — Claude Code *(compte payant)*

Claude Code est **à la fois un outil en ligne de commande autonome ET un add-on VSCode**. Tu n'es pas obligé de rester dans VSCode : tu peux lancer `claude` directement dans un terminal et piloter tout le projet depuis là. Mais l'extension VSCode est disponible pour ceux qui préfèrent rester dans l'éditeur.

**Modes d'usage :**

| Mode | Comment | Quand l'utiliser |
|---|---|---|
| **CLI autonome** | `claude` dans un terminal (hors VSCode) | Sessions longues, refactoring massif, agentic |
| **Extension VSCode** | Chat + inline edit directement dans l'éditeur | Au quotidien en codant |

**Installation :**

1. Aller sur **https://console.anthropic.com** → créer un compte et ajouter des crédits.
2. **API Keys** → *Create Key* → copier la clé (`sk-ant-...`).
3. Installer Claude Code :
   ```bash
   npm install -g @anthropic-ai/claude-code
   claude --version   # vérification
   ```
4. (Optionnel mais recommandé) Installer l'extension VSCode :
   - ID : `anthropic.claude-vscode`
   - Ou : VSCode → Extensions → chercher *Claude*
5. Stocker la clé dans `.env.local` (jamais commitée) :
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

> ✅ L'intégration MCP JIRA (§8) fonctionne nativement avec Claude Code.

---

### Option B — GitHub Copilot Education *(gratuit, à privilégier si pas de Claude Code)*

> **Situation de Mauricette** : pas de compte Copilot entreprise disponible pour le moment. La licence étudiante GitHub Education est **la voie à suivre**.

**Prérequis : obtenir un certificat de scolarité**
- Brice a demandé à **Nadine** d'envoyer à Mauricette un **certificat de scolarité** (requis pour valider la demande GitHub Education).
- Vérifier réception du document avant de commencer les étapes ci-dessous.

**Étapes :**

1. S'assurer que le compte GitHub est bien créé (§1).
2. Aller sur **https://education.github.com/pack** → *Get student benefits*.
3. Cliquer **Get student benefits** → sélectionner *Student*.
4. Soumettre la preuve de scolarité :
   - Photo/scan du **certificat de scolarité** (reçu de Nadine)
   - Ou email scolaire `@univ-...` si disponible
5. Attendre la validation : **quelques heures à 2 jours** ouvrés.
6. Une fois le mail de confirmation reçu, aller dans **GitHub.com → Settings → Copilot → Enable**.
7. Installer dans VSCode :
   - Extension **GitHub Copilot** (`GitHub.copilot`)
   - Extension **GitHub Copilot Chat** (`GitHub.copilot-chat`)

> ⚠️ Le support du serveur MCP JIRA (§8) avec Copilot nécessite Copilot Chat en mode **Agent** — activer le mode agent dans le panneau Copilot Chat.

---

## 4. Compte Azure *(géré par Brice — rien à faire pour Mauricette)*

> **Mauricette** : tu recevras une **invitation par email** sur ton adresse GitHub pour rejoindre la souscription Azure. Accepte l'invitation, c'est tout.

**Actions réservées à Brice :**

1. Créer le Resource Group : `az group create -n rg-bizplan -l westeurope`
2. Provisionner les services (Container Apps, MySQL Flexible, Key Vault) — voir [`architecture.md`](./architecture.md)
3. Inviter Mauricette : *Azure Portal → Subscriptions → Access control (IAM) → Add → Contributor*
4. Partager la **connection string** de la base MySQL `dev` de manière sécurisée (via Key Vault ou message chiffré — **jamais par email en clair**)

**Mauricette, une fois invitée :**

```bash
winget install Microsoft.AzureCLI   # Windows
az login                             # connexion avec ton compte Microsoft lié à GitHub
az account show                      # vérifier que rg-bizplan est visible
```

---

## 5. Installer les outils de base

### Git
- Windows : `winget install Git.Git` · macOS : `brew install git` · Linux : `sudo apt install git`
- Configurer : `git config --global user.name "Prénom Nom"` et `git config --global user.email "...@..."`

### Python 3.12
- Windows : `winget install Python.Python.3.12` · macOS : `brew install python@3.12` · Linux : `sudo apt install python3.12 python3.12-venv`
- Vérifier : `python --version`

### Node.js (pour le serveur MCP)
- `winget install OpenJS.NodeJS.LTS` / `brew install node` / via nvm. Vérifier : `node --version`

### Docker
- Installer **Docker Desktop** (https://docker.com) — nécessaire pour builder l'image de l'API.

---

## 6. MySQL *(pas d'installation locale — base sur Azure)*

> Pas de MySQL à installer en local. La base de données tourne sur **Azure Database for MySQL Flexible Server** (environnement `dev`).
> La connection string est fournie par Brice et à stocker dans `.env.local` :
>
> ```
> DATABASE_URL=mysql+pymysql://<user>:<password>@<host>.mysql.database.azure.com/bizplan?ssl_ca=DigiCertGlobalRootG2.crt.pem
> ```
>
> Le certificat SSL Azure est à télécharger ici : https://dl.cacerts.digicert.com/DigiCertGlobalRootG2.crt.pem

---

## 7. Installer VSCode et les extensions

1. Télécharger **VSCode** : https://code.visualstudio.com
2. Installer les extensions (ou accepter les recommandations via `.vscode/extensions.json`) :

   **Extensions communes (tous les membres) :**
   - **Python** + **Pylance**
   - **Ruff**
   - **GitLens**
   - **Docker**
   - **YAML**

   **Extension IA — selon votre option (§3) :**
   | Option | Extension(s) à installer |
   |---|---|
   | A — Claude Code | `anthropic.claude-vscode` (Claude) |
   | B — GitHub Copilot | `GitHub.copilot` + `GitHub.copilot-chat` |

3. Ouvrir le dossier du projet : les réglages partagés (`.vscode/settings.json`) s'appliquent automatiquement.

---

## 8. Configurer le serveur MCP vers JIRA

Permet à l'assistant IA (dans VSCode) de lire/écrire les tickets JIRA. Voir aussi [`craftsmanship.md`](./craftsmanship.md) §2.3.

> **Option A (Claude Code)** : support MCP natif, fonctionne immédiatement.  
> **Option B (GitHub Copilot)** : activer le mode **Agent** dans Copilot Chat, puis ajouter le serveur MCP.

1. Exporter les variables d'environnement (ne pas les committer) :
   ```bash
   # ~/.bashrc, ~/.zshrc ou variables d'env Windows
   export JIRA_EMAIL="vous@exemple.com"
   export JIRA_API_TOKEN="<token créé à l'étape 2.5>"
   ```
2. Créer `.vscode/mcp.json` :
   ```json
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
3. Recharger VSCode. Tester dans Claude : *« Liste mes tickets JIRA ouverts du projet BIZ. »*

---

## 9. Cloner et configurer le projet

```bash
git clone https://github.com/BenjGue/emba-bp-analyst.git
cd emba-bp-analyst

# Environnement Python
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Variables d'environnement locales (ne jamais commiter ce fichier)
cp .env.example .env.local
# Éditer .env.local :
#   ANTHROPIC_API_KEY=sk-ant-...     ← Option A uniquement (Claude Code)
#   DATABASE_URL=mysql+pymysql://...  ← connection string Azure dev (fournie par Brice)

# Hooks qualité (lint, types, tests, secrets) — cf. AI-rules.md
pre-commit install
```

---

## 10. Lancer le backend en local *(connexion vers Azure dev)*

```bash
# Le backend se connecte à la base Azure dev via DATABASE_URL dans .env.local
uvicorn app.main:app --reload
# → http://localhost:8000/docs  (documentation OpenAPI auto)
```

> Pas de base locale — toutes les requêtes partent vers l'environnement Azure `dev`. Les migrations de schéma sont exécutées via la pipeline CI/CD.

---

## 11. Vérification finale (checklist)

**Brice :**
- [ ] Dépôt GitHub créé, Advanced Security activé, Mauricette invitée
- [ ] Projet JIRA `BIZ` créé, Mauricette invitée, token API généré
- [ ] Azure : Resource Group + services provisionnés, Mauricette invitée en Contributor
- [ ] Connection string MySQL dev partagée de manière sécurisée

**Mauricette :**
- [ ] Certificat de scolarité reçu de Nadine
- [ ] `git --version`, `python --version`, `node --version` répondent
- [ ] Compte GitHub créé, invitation dépôt acceptée
- [ ] Assistant IA configuré : **Option A** (Claude Code installé + `ANTHROPIC_API_KEY` dans `.env.local`) **ou Option B** (GitHub Copilot Education validé + extensions VSCode installées)
- [ ] Invitation Azure acceptée, `az login` réussi, `rg-bizplan` visible
- [ ] `.env.local` renseigné avec `DATABASE_URL` Azure dev
- [ ] VSCode + extensions installées, MCP JIRA répond
- [ ] `uvicorn` démarre, `/docs` accessible sur `localhost:8000`

Si tous les points sont cochés, l'environnement est prêt. Reprendre le flux de travail décrit dans [`craftsmanship.md`](./craftsmanship.md) §7.

---

← [livrable.md](./livrable.md) · Retour au [README](./README.md)
