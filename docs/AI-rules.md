# AI-Rules — Forcer les bonnes pratiques de notre IA de développement

> Setup et fichiers à créer pour **contraindre et optimiser** l'IA (Claude dans VSCode) afin qu'elle produise, **pour chaque feature**, du code respectant nos standards : commentaires utiles, tests unitaires, documentation, et branching GitHub correct.

← Retour au [README](../README.md)

---

## 1. Principe

L'IA est un co-développeur puissant mais qui, **sans cadre**, prend des libertés : code non testé, doc absente, commits anarchiques. La solution : **matérialiser nos règles dans des fichiers versionnés** que l'IA lit automatiquement. Les règles deviennent ainsi **part du dépôt**, pas de la mémoire d'un humain.

Deux distinctions importantes :
- **Distinguer deux IA** : (1) *Claude dans VSCode* qui **nous aide à coder** (cadré par ce document) ; (2) *Claude dans le produit* qui **génère les business plans** (cadré côté backend, cf. [`architecture.md`](./architecture.md) §7).
- **Distinguer instructions et automatisation** : un fichier de règles *oriente* l'IA, mais ce qui **force** réellement (tests, lint, sécurité) ce sont les **hooks Git + GitHub Actions** (cf. [`craftsmanship.md`](./craftsmanship.md)). Les deux se complètent.

## 2. Fichiers à créer

| Fichier | Rôle | Qui le lit |
|---|---|---|
| `CLAUDE.md` (racine) | Règles de projet pour Claude : standards, structure, DoD | Claude (VSCode) |
| `.github/copilot-instructions.md` | Mêmes règles pour GitHub Copilot (compat.) | Copilot |
| `.editorconfig` | Indentation, fins de ligne homogènes | Éditeur |
| `ruff.toml` / `pyproject.toml` | Règles de lint et format | Ruff / CI |
| `.pre-commit-config.yaml` | Hooks bloquants avant commit | Git |
| `.vscode/mcp.json` | Connexion MCP JIRA | VSCode |
| `tests/` + `pytest.ini` | Cadre de test | pytest / CI |
| `.github/pull_request_template.md` | Definition of Done en checklist | Auteur PR |

## 3. `CLAUDE.md` — Le contrat principal

Fichier racine lu automatiquement par Claude à chaque session. Contenu recommandé :

```markdown
# CLAUDE.md — Règles de développement BizPlan-IA

## Stack
- Backend : Python 3.12, FastAPI, Pydantic v2, SQLAlchemy, MySQL.
- IA produit : Azure AI Foundry (inférence `chat/completions`), modèle configurable, sorties JSON validées.
- Tests : pytest. Lint/format : Ruff. Types : mypy.

## Règles NON négociables — pour CHAQUE feature
1. TESTS : toute fonction de logique métier a des tests unitaires pytest.
   Couverture minimale 80 %. Le score de pertinence est testé sur ses
   bornes (0, 100) et un cas chiffré de référence.
2. DOCUMENTATION : chaque fonction publique a une docstring (style Google)
   décrivant args, retour, exceptions. Le README/docs sont mis à jour si
   le comportement visible change.
3. COMMENTAIRES : commenter le POURQUOI (décision, contrainte métier),
   jamais le QUOI évident. Pas de commentaire mort ni de code commenté.
4. TYPAGE : annotations de type partout ; pas de `Any` non justifié.
5. VALIDATION : toute entrée externe (formulaire, sortie IA) passe par un
   modèle Pydantic. L'IA produit ne calcule jamais le score final.
6. BRANCHING : travailler sur une branche feature/BIZ-xx-...
   (jamais sur main). Commits Conventional Commits avec la clé ticket.
   Une PR par feature, relue par l'autre membre du binôme.
7. SÉCURITÉ : aucun secret en dur. Lire les clés via variables
   d'environnement / Key Vault. Ne jamais logger de secret.

## Structure du repo
- app/        : code FastAPI (routers, services, agents IA, scoring)
- app/services/ai/ : agents IA (description, analyste, financier, rédacteur, synthèse, évaluateur)
- app/static/ : frontend web (HTML/CSS/JS) servi par FastAPI
- migrations/ : migrations Alembic versionnées ; db/schema.sql pour référence
- scripts/    : utilitaires (seed.py, jira, probes)
- tests/      : miroir de app/
- docs/       : documentation

## Workflow attendu de l'IA
- Avant de coder : lire le ticket JIRA (via MCP) et résumer les critères
  d'acceptation.
- Proposer un plan court, puis implémenter.
- Écrire le code ET ses tests dans la même PR.
- Lancer mentalement la checklist DoD (section ci-dessous) avant de
  conclure.

## Definition of Done (par feature)
- [ ] Code typé, lint Ruff vert, mypy vert
- [ ] Tests unitaires écrits et verts, couverture >= 80 %
- [ ] Docstrings sur les fonctions publiques
- [ ] Aucun secret commité (push protection vert)
- [ ] Branche feature/BIZ-xx, commits conventionnels, PR ouverte
- [ ] Doc mise à jour si nécessaire
- [ ] Ticket JIRA passé en "En revue"
```

## 4. Hooks pré-commit — Ce qui *force* réellement

Les règles de `CLAUDE.md` *orientent* ; les hooks **bloquent**. `.pre-commit-config.yaml` :

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff          # lint, bloque si erreur
      - id: ruff-format   # format auto
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
  - repo: local
    hooks:
      - id: pytest-check
        name: tests unitaires
        entry: pytest -q
        language: system
        pass_filenames: false
      - id: no-secrets
        name: détection de secrets
        entry: detect-secrets-hook
        language: system
```

Activation : `pre-commit install`. Désormais, **impossible de commiter** du code non formaté, non typé, sans tests verts, ou contenant un secret — y compris le code généré par l'IA.

## 5. Tests unitaires — Cadre

- **Miroir de structure** : `tests/test_scoring.py` teste `app/scoring.py`.
- **Cas obligatoires pour le score** : borne basse (0), borne haute (100), cas chiffré de référence (validation de la pondération 30/20/20/10/10/10), entrée incomplète (erreur attendue).
- **Agents IA** : tests sur la **validation des sorties** (JSON conforme au schéma), avec réponses IA *mockées* — on ne teste pas le modèle, on teste **notre robustesse** face à ses sorties (y compris JSON mal formé).
- **Seuil CI** : `--cov-fail-under=80` bloque la PR sous 80 %.

## 6. Documentation — Cadre

- **Docstrings** style Google sur toute fonction/classe publique.
- **`docs/`** : décisions d'architecture (ADR courts), schéma de données, catalogue des prompts.
- **README à jour** : tout changement de comportement visible met à jour la doc dans la même PR (vérifié en checklist DoD).
- **Catalogue des prompts** versionné dans `app/agents/prompts/` : chaque prompt système est un fichier, testable et relisible (livrable « prompts documentés », cf. [`livrable.md`](./livrable.md)).

## 7. Branching imposé à l'IA

L'IA doit **toujours** :
1. Vérifier qu'elle n'est pas sur `main` (`git branch --show-current`).
2. Créer/se placer sur `feature/BIZ-xx-description`.
3. Committer en Conventional Commits avec la clé ticket.
4. Ouvrir une PR, jamais merger directement.

Ces étapes sont rappelées dans `CLAUDE.md` ; la **protection de branche** GitHub (cf. [`craftsmanship.md`](./craftsmanship.md) §4.2) les **rend obligatoires** même si l'IA oublie.

## 8. Règles pour l'IA *produit* (génération des BP)

Distinctes du dev, mais documentées ici pour cohérence. Imposées **côté backend** :

- Réponses **structurées en JSON** uniquement.
- **Prompts paramétrés** avec variables dynamiques (jamais de concaténation sauvage).
- Style **neutre, professionnel, non prescriptif**.
- **Interdiction d'inférer** des données non fournies.
- **Validation systématique** de chaque réponse (schéma + cohérence métier).
- Gestion explicite des erreurs : JSON mal formé, hallucination, recommandation incohérente, donnée absente (cf. [`architecture.md`](./architecture.md) §7).

## 9. En résumé : 3 niveaux de garantie

| Niveau | Mécanisme | Force de contrainte |
|---|---|---|
| **Orientation** | `CLAUDE.md`, `copilot-instructions.md` | L'IA *sait* quoi faire |
| **Blocage local** | pre-commit (Ruff, mypy, pytest, secrets) | Impossible de commiter hors normes |
| **Blocage distant** | GitHub Actions + protection de branche + Advanced Security | Impossible de merger hors normes |

La combinaison des trois garantit que **même du code généré rapidement par l'IA** respecte nos standards avant d'atteindre `main`.

---

← [craftsmanship.md](./craftsmanship.md) · Suite : [`livrable.md`](./livrable.md)
