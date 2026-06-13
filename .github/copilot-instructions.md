# GitHub Copilot — Instructions personnalisées pour ce projet

> Ce fichier est lu automatiquement par GitHub Copilot Chat pour contextualiser ses suggestions.

## Projet

**BizPlan-IA** — Outil de création automatisée de Business Plans pour évaluer la pertinence de projets internes (La Poste). Stack : **Python 3.12 / FastAPI / SQLAlchemy / MySQL / Azure Container Apps**.

## Langage & style

- Tout le code est en **Python 3.12**, avec typage strict (`from __future__ import annotations`).
- Formatage : **Ruff** (line-length 100, double quotes). Ne jamais produire de code qui ferait échouer `ruff check` ou `ruff format --check`.
- **Conventional Commits** obligatoires : `feat(scope):`, `fix(scope):`, `docs:`, `test:`, `chore:`. Toujours référencer le ticket JIRA : `(BIZ-xx)`.
- Nommage : snake_case pour variables/fonctions, PascalCase pour classes, SCREAMING_SNAKE pour constantes.

## Architecture

- `app/` — code source FastAPI (routers, services, models, schemas)
- `tests/` — tests pytest (miroir de `app/`)
- Un endpoint = un fichier router + un fichier service + un fichier schema Pydantic
- Pas de logique métier dans les routers — déléguer aux services

## Règles de sécurité (OWASP)

- **Jamais** de secret en dur dans le code (clés API, mots de passe, tokens).
- Toujours utiliser `pydantic-settings` pour lire les variables d'environnement.
- Valider toutes les entrées utilisateur avec des modèles Pydantic.
- Utiliser des requêtes paramétrées (SQLAlchemy ORM) — jamais de SQL brut avec f-strings.

## Tests

- Couverture minimale : **80%**.
- Chaque fonction publique a au moins un test unitaire.
- Les tests d'intégration utilisent `httpx.AsyncClient` avec `pytest-asyncio`.
- Nommer les tests : `test_<ce_que_ça_fait>_<condition>_<résultat_attendu>`.

## Ce que Copilot doit faire par défaut

1. Proposer du code avec **annotations de type complètes**.
2. Ajouter des **docstrings** sur toutes les fonctions/classes publiques (style Google).
3. Ne jamais utiliser `Any` sauf si justifié par un commentaire.
4. Générer le test unitaire correspondant si on crée une fonction de service.
5. Respecter la **Definition of Done** : code typé, testé, documenté, sans alerte Ruff.

## Gestion de projet — JIRA (obligatoire pour chaque US)

> Projet JIRA : `BIZ` sur `https://ionis-stm-team-ek7kwlup.atlassian.net`.
> Le workflow de chaque US **doit** être tracé dans JIRA pour permettre l'audit des actions et de la logique d'implémentation.

### Cycle de vie d'une User Story

Pour **chaque** US implémentée, Copilot doit, dans l'ordre :

1. **Avant de coder** — passer le ticket en **En cours** (transition `21`).
2. **Si un travail technique non prévu apparaît** (bug, dette, correctif infra) — **créer un nouveau ticket technique** de type `Tâche` préfixé `TECH —`, et le référencer dans les commits.
3. **Après l'implémentation** — ajouter un **commentaire d'implémentation** sur le ticket décrivant : la logique retenue, les fichiers créés/modifiés (avec leur rôle), la couverture de tests, le n° de PR et le résultat du déploiement. Ce commentaire est **obligatoire** et sert de trace.
4. **Une fois la PR mergée et le déploiement vert** — passer le ticket en **Terminé** (transition `31`).

### Comment agir sur JIRA

- **Lecture / recherche / création** : utiliser les outils MCP Atlassian (`create-jira-issue`, `get-jira-issue`, `search-jira-issues`, `update-jira-issue`).
  - `create-jira-issue` : la `description` doit être une **chaîne simple** ; `issuetype.name` en français (`Tâche`, `Story`, `Epic`).
  - `update-jira-issue` : la `description` doit être au format **ADF** (`{type:"doc",version:1,content:[…]}`).
- **Changement de statut et ajout de commentaire** : l'outil MCP **ne gère pas** ces actions. Utiliser l'API REST Atlassian (Basic auth via `JIRA_EMAIL` / `JIRA_API_TOKEN`, variables d'environnement utilisateur) :
  - Transition : `POST /rest/api/3/issue/{KEY}/transitions` avec `{ "transition": { "id": "<11|21|31>" } }` — IDs : **11** = À faire, **21** = En cours, **31** = Terminé.
  - Commentaire : `POST /rest/api/3/issue/{KEY}/comment` avec un corps ADF. Utiliser le script [`scripts/jira-add-comment.ps1`](../scripts/jira-add-comment.ps1).

### Git & PR (rappel lié au ticket)

- Une branche par US : `feat/biz-<n>-<slug>` (ou `fix/…`, `chore/…`).
- Commits **Conventional Commits** référençant le ticket : `feat(scope): … (BIZ-xx)`.
- PR vers `main` (protégée) — merge en **squash** seulement après CI verte (lint + types + tests + build + CodeQL).
