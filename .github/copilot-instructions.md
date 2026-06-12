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
