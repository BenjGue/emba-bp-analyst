# Rapport de tests — BizPlan-IA (campagne complète)

> Campagne de test exécutée le **2026-06-15** contre l'application **déployée sur Azure Container Apps**
> (`https://bizplan-api-dev.salmondune-1b29666f.westeurope.azurecontainerapps.io`).
> Objectif : valider en profondeur les parcours, la validation des entrées, les codes d'erreur et la logique métier ; remonter les bugs dans JIRA.

---

## 1. Synthèse

| Suite | Cas | PASS | FAIL |
|---|---|---|---|
| E2E Playwright — parcours critique (`critical-path.spec.js`) | 1 | 1 | 0 |
| Sonde API — validations / limites / métier (`scripts/api_probe.py`) | 34 | 34 | 0 |
| Exploratoire UI Playwright (`exploratory.spec.js`) | 9 | 8 | **1** |
| **Total** | **44** | **43** | **1** |

**Verdict** : le backend (validation Pydantic, codes HTTP, calcul de score, garde-fous IA, import Excel) est **robuste** — 100 % des sondes passent. Un **défaut front-end** sur la navigation arrière du wizard a été identifié, avec **deux symptômes** dont un d'intégrité de données.

---

## 2. Périmètre testé

### 2.1 Backend / API (34 assertions — toutes PASS)
- **Création projet** : nom vide / > 200, description > 1000, durée 0 / 601 / négative, direction invalide, champs manquants → tous **422** attendus.
- **404** : `GET/DELETE` projet inexistant, score/bp inexistants, `generate` projet inexistant ; id non entier → **422**.
- **Financials** : investissement négatif, délai 0 / 601 → **422** ; valeurs valides → **200**.
- **Génération** : sans hypothèses financières → **400** ; avec → **201**.
- **Dimensions / score** : note 11 / -1, dimension manquante → **422**.
- **Logique de score** : toutes notes à 0 ⇒ **total = 0** ; toutes à 10 ⇒ **total = 100** (bornage + pondération corrects).
- **Export** : `md` → 200, `pdf` → 200 (`application/pdf`), format invalide → **422**.
- **Assistance IA** (désactivée en prod) : `draft-description` → **503** (garde-fou correct, pas de fuite).
- **Import Excel** : fichier corrompu / non-xlsx → **422**.
- **Sécurité** : un nom contenant du HTML est accepté côté API et **échappé** côté UI (pas d'exécution).

### 2.2 Front-end / UI (9 scénarios — 8 PASS, 1 FAIL)
- Dashboard se charge sans erreur console — PASS
- Validation : formulaire vide affiche les erreurs de champ — PASS
- Validation : l'erreur disparaît après correction — PASS
- **Wizard : « Précédent » conserve les saisies — FAIL** (voir §3)
- Assistance IA sans idée → toast d'erreur — PASS
- Assistance IA, échec backend géré sans crash — PASS
- XSS : nom HTML échappé dans le dashboard — PASS
- Dashboard : filtre par direction — PASS
- Suppression : le projet disparaît du dashboard — PASS

---

## 3. Bugs identifiés

### BUG-1 — Le bouton « Précédent » du wizard perd les saisies **et crée des projets en double**

- **Sévérité** : Élevée (intégrité de données + UX).
- **Composant** : `app/static/app.js` — fonction `stepProject()` (ligne 199), handler de `#next` (ligne 285), retour `#prev` (ligne 323).
- **Symptôme A (perte de données)** : à l'étape 2 (Finances), cliquer « ‹ Précédent » revient à l'étape 1 mais **le nom et la description sont vidés** et la durée est réinitialisée à 12. `stepProject()` reconstruit le formulaire sans repeupler depuis `state.project`.
- **Symptôme B (doublons en base)** : le handler de « Continuer › » exécute **toujours** `state.project = await api("POST", "", payload)`. Revenir en arrière puis ré-avancer **POST un nouveau projet** au lieu de mettre à jour l'existant → **projets orphelins dupliqués**.
- **Reproduction (confirmée)** :
  1. Tableau de bord → « Créer un projet ».
  2. Saisir nom + description + durée 24 → « Continuer › ».
  3. À l'étape Finances → « ‹ Précédent ».
  4. Constater les champs vidés (Symptôme A). Re-saisir → « Continuer › ».
  5. Vérification API : **2 projets** portant le même nom existent (Symptôme B — mesuré).
- **Attendu** :
  - Revenir en arrière **conserve** les valeurs déjà saisies.
  - Ré-avancer **met à jour** le projet existant (`PUT /projects/{id}`) au lieu d'en créer un nouveau ; un seul enregistrement par parcours.
- **Piste de correction** : rendre `stepProject()` *state-aware* (pré-remplir `#f-nom`, `#f-desc`, `#f-dir`, `#f-duree` depuis `state.project` si présent) ; dans le handler `#next`, faire `PUT /{id}` si `state.project` existe, sinon `POST`.
- **Preuves** : `e2e/test-results/…/test-failed-1.png` (capture), vidéo `video.webm`, run `exploratory.spec.js` (test #4).

> Note : les deux symptômes partagent la **même cause racine** (`stepProject()` non *state-aware*) et **le même correctif** → traités dans un seul ticket avec deux critères d'acceptation.

---

## 4. Recommandations

1. Corriger BUG-1 (ticket JIRA créé).
2. **Industrialiser ces tests** : ajouter `exploratory.spec.js` à la suite E2E CI (BIZ-39) — la couverture passait d'1 happy-path à 10 scénarios.
3. Intégrer la sonde API (`scripts/api_probe.py`) en *smoke test* post-déploiement.
4. Ajouter une contrainte d'unicité applicative (ou un garde-fou) pour éviter les projets dupliqués côté serveur, en défense en profondeur.

---

## 5. Comment rejouer la campagne

```powershell
# 1. E2E + exploratoire (cible Azure par défaut)
cd e2e
npx playwright test                       # toute la suite
npx playwright test exploratory.spec.js   # uniquement l'exploratoire
npx playwright show-report

# 2. Sonde API (négatifs + limites + métier)
cd ..
.\.venv\Scripts\python.exe scripts\api_probe.py
```
