## 🔗 Ticket JIRA

<!-- Lien obligatoire -->
**BIZ-** : https://<votre-domaine>.atlassian.net/browse/BIZ-

---

## 📋 Description

<!-- Qu'est-ce qui a été modifié et pourquoi ? -->

---

## 🧪 Tests

- [ ] Tests unitaires ajoutés / mis à jour
- [ ] `pytest --cov=app --cov-fail-under=80` passe au vert en local
- [ ] Aucun test existant cassé

## ✅ Checklist Definition of Done

- [ ] Code typé (`from __future__ import annotations`, pas de `Any` non justifié)
- [ ] Docstrings Google sur toutes les fonctions/classes publiques
- [ ] `ruff check . && ruff format --check .` sans erreur
- [ ] `mypy app/` sans erreur
- [ ] Aucun secret en dur (clé API, mot de passe, token)
- [ ] Documentation mise à jour si nécessaire (README, How-to-setup, etc.)

## 🔐 Sécurité

- [ ] Aucune nouvelle dépendance vulnérable (Dependabot vérifie automatiquement)
- [ ] Entrées utilisateur validées par Pydantic
- [ ] Requêtes SQL via ORM uniquement (pas de f-string SQL)

## 📸 Captures / démo *(si applicable)*

<!-- Screenshots, curl, ou logs illustrant le changement -->
