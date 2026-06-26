# Agents IA — Rôles et prompts

> Documentation de référence de la couche IA (EPIC 3). Décrit chaque agent, son
> rôle, son prompt système, ses entrées/sorties et son orchestration.
>
> **Sources de vérité** :
> [`app/services/ai/prompts.py`](../app/services/ai/prompts.py) (prompts système),
> [`app/services/ai/agents.py`](../app/services/ai/agents.py) (agents),
> [`app/services/ai/description.py`](../app/services/ai/description.py),
> [`app/services/ai/evaluation.py`](../app/services/ai/evaluation.py),
> [`app/services/generation.py`](../app/services/generation.py) (orchestration),
> [`app/schemas/ai.py`](../app/schemas/ai.py) (schémas de sortie).

## Principe directeur

> **« L'IA rédige et raisonne, le backend valide et calcule. »**

- L'IA ne produit **jamais** de chiffre financier ni de score : ceux-ci sont
  calculés de façon déterministe par le backend, puis seulement **commentés**
  par l'IA.
- Chaque agent qui retourne des données structurées impose un **JSON strict**,
  validé ensuite par un schéma Pydantic. Une réponse non conforme lève
  `AiResponseError`.
- En cas d'échec d'un agent durant la génération, le service **retombe
  automatiquement** sur un mode déterministe (template) pour toujours produire
  un livrable.

## Contexte commun (`_CONTEXTE`)

Rappelé en tête de **chaque** prompt système :

```text
Tu assistes le groupe La Poste dans l'évaluation de projets internes. Tu écris
un français professionnel, sobre et factuel. Tu n'inventes jamais de chiffres
financiers : ceux-ci sont calculés par le backend.
```

## Client d'inférence

Tous les agents passent par le contrat `AiClient.complete(system, user, json_mode, max_tokens)`
([`app/services/ai/client.py`](../app/services/ai/client.py)). En production,
`FoundryClient` cible le endpoint `chat/completions` d'Azure AI Foundry
(`temperature = 0.4`), agnostique au modèle (Claude Sonnet, GPT, …). Changer de
modèle ne demande qu'une modification de configuration. `json_mode=True` ajoute
`response_format: {"type": "json_object"}`.

---

## Vue d'ensemble des agents

| Agent | Ticket | Prompt système | Fonction | `json_mode` | Schéma de sortie | Persistance |
|-------|--------|----------------|----------|:-----------:|------------------|:-----------:|
| Description | BIZ-37 | `DESCRIPTION_SYSTEM` | `draft_description` | ❌ (texte) | `DescriptionDraftResponse` | Non |
| Évaluateur | BIZ-56 | `EVALUATEUR_SYSTEM` | `run_evaluateur` / `suggest_dimensions` | ✅ | `EvaluateurOutput` | Non |
| Analyste | BIZ-15 | `ANALYSTE_SYSTEM` | `run_analyste` | ✅ | `AnalysteOutput` | Via BP |
| Financier | BIZ-16 | `FINANCIER_SYSTEM` | `run_financier` | ✅ | `FinancierOutput` | Via BP |
| Rédacteur | BIZ-17 | `REDACTEUR_SYSTEM` | `run_redacteur` | ✅ | `RedacteurOutput` | Via BP |
| Synthèse | BIZ-18 | `SYNTHESE_SYSTEM` | `run_synthese` | ✅ | `SyntheseOutput` | Via BP |

---

## 1. Agent Description — BIZ-37

**Rôle.** À partir de quelques idées brutes saisies par le porteur, reformuler
et structurer l'intégralité du texte en une description de projet claire,
professionnelle et synthétique. Endpoint sans persistance : le texte pré-remplit
le formulaire de création. Le backend **borne** ensuite la sortie à 1000
caractères (`ProjectCreate.description`).

**Prompt système (`DESCRIPTION_SYSTEM`).**

```text
<_CONTEXTE>
Rôle : à partir des idées brutes fournies par un porteur de projet, tu
reformules et structures l'intégralité du texte en une description de projet
claire, professionnelle et synthétique.
Contraintes : 1 à 3 courts paragraphes, 600 caractères maximum, pas de titre,
pas de liste à puces, pas de Markdown. Tu restes fidèle aux idées fournies sans
en ajouter de nouvelles. Réponds uniquement par le texte de la description.
```

**Prompt utilisateur** (assemblé par `_build_user_prompt`) :

```text
Direction concernée : <direction>
Nom du projet : <nom>           # ligne présente seulement si nom fourni
Idées clés à développer :
<idees>
```

- **Entrée** : `DescriptionDraftRequest` (`idees` 1–2000 car., `direction`, `nom` optionnel).
- **Sortie** : `DescriptionDraftResponse` (`description`, texte libre borné à 1000 car.).
- **Mode** : `json_mode=False` (texte brut).
- **Exposé via** : `POST /projects/draft-description`.

---

## 2. Agent Évaluateur — BIZ-56

**Rôle.** À partir des données du projet (description, direction, durée, et
hypothèses financières si fournies), proposer une note entière **0–10** pour
chacune des **6 dimensions stratégiques**, justifier chaque note en une phrase
et rédiger une synthèse globale (2 à 4 phrases). Pour `risque`, la note
représente la **maîtrise** du risque (10 = le mieux maîtrisé). Le backend
**borne** les notes dans `[0, 10]` (`_clamp`) puis calcule le score de façon
déterministe (`compute_score`). Endpoint sans persistance : la proposition
pré-remplit l'écran d'évaluation.

**Prompt système (`EVALUATEUR_SYSTEM`).**

```text
<_CONTEXTE>
Rôle : agent Évaluateur. À partir des informations du projet (description,
direction, durée, et données financières si fournies), tu proposes une note
entière de 0 (très faible) à 10 (excellent) pour chacune des 6 dimensions
stratégiques. Pour la dimension 'risque', la note représente la MAÎTRISE du
risque (10 = risque le mieux maîtrisé).
Tu justifies chaque note en une phrase concise et tu rédiges une synthèse
globale (2 à 4 phrases) expliquant ta logique d'évaluation.
Réponds STRICTEMENT en JSON valide avec EXACTEMENT ces clés :
{"rentabilite": 0, "alignement": 0, "risque": 0, "impact_operationnel": 0,
"impact_social": 0, "faisabilite": 0, "justifications": {"rentabilite": "",
"alignement": "", "risque": "", "impact_operationnel": "", "impact_social": "",
"faisabilite": ""}, "synthese": ""}.
Les 6 notes sont des entiers entre 0 et 10. Aucun texte hors du JSON.
```

**Prompt utilisateur** (assemblé par `run_evaluateur`) :

```text
Projet : <nom>
Direction : <direction>
Durée estimée : <duree_estimee_mois> mois
Données financières (calculées par le backend) : <JSON financials | "non renseignées">
Description : <description>
```

- **Entrée** : nom, description, direction, durée, `financials` optionnel.
- **Sortie** : `EvaluateurOutput` → ré-emballée en `DimensionSuggestion`
  (notes bornées + justifications + synthèse + `ScoreResponse` déterministe).
- **Mode** : `json_mode=True`.
- **Exposé via** : `POST /projects/{id}/dimensions/suggest`.

---

## 3. Agent Analyste — BIZ-15

**Rôle.** Produire une analyse stratégique du projet : forces, faiblesses,
risques, opportunités (2 à 4 éléments par catégorie). Première étape de la chaîne
de génération du business plan.

**Prompt système (`ANALYSTE_SYSTEM`).**

```text
<_CONTEXTE>
Rôle : agent Analyste. Tu produis une analyse stratégique du projet.
Réponds STRICTEMENT en JSON valide avec les clés suivantes, chacune étant une
liste de 2 à 4 chaînes courtes :
{"forces": [], "faiblesses": [], "risques": [], "opportunites": []}.
Aucun texte hors du JSON.
```

**Prompt utilisateur** (assemblé par `run_analyste`) :

```text
Projet : <nom>
Direction : <direction>
Durée estimée : <duree_estimee_mois> mois
Description : <description>
```

- **Sortie** : `AnalysteOutput` (`forces`, `faiblesses`, `risques`, `opportunites`).
- **Mode** : `json_mode=True`.
- **Usage** : la cartographie des risques enrichit la section « Analyse des
  risques » du BP ; l'analyse est aussi transmise à l'agent Rédacteur.

---

## 4. Agent Financier — BIZ-16

**Rôle.** Commenter **qualitativement** les scénarios financiers (bas, médian,
haut) **déjà calculés** par le backend. L'agent ne recalcule rien et n'invente
aucun chiffre.

**Prompt système (`FINANCIER_SYSTEM`).**

```text
<_CONTEXTE>
Rôle : agent Financier. Les chiffres (revenus, coûts, ROI, retour sur
investissement) te sont FOURNIS et sont déjà calculés ; tu ne les modifies pas
et n'en inventes pas d'autres. Tu rédiges un commentaire qualitatif.
Réponds STRICTEMENT en JSON valide :
{"analyse_globale": "", "scenario_bas": "", "scenario_median": "",
"scenario_haut": ""}. Chaque valeur est une phrase concise. Aucun texte hors du
JSON.
```

**Prompt utilisateur** (assemblé par `run_financier`) :

```text
Voici les scénarios financiers déjà calculés (ne pas recalculer, seulement
commenter) :
<JSON scenarios>
```

- **Entrée** : `scenarios` (dict des 3 scénarios calculés).
- **Sortie** : `FinancierOutput` (`analyse_globale`, `scenario_bas`, `_median`, `_haut`).
- **Mode** : `json_mode=True`.
- **Usage** : `analyse_globale` enrichit la section « Hypothèses et scénarios
  financiers » du BP.

---

## 5. Agent Rédacteur — BIZ-17

**Rôle.** Rédiger le contenu rédactionnel du business plan en **10 sections**
(2 à 5 phrases chacune), sans inventer de chiffre. Reçoit en contexte le score,
les scénarios calculés et l'analyse stratégique de l'agent Analyste.

**Prompt système (`REDACTEUR_SYSTEM`).**

```text
<_CONTEXTE>
Rôle : agent Rédacteur. Tu produis le contenu rédactionnel d'un business plan en
10 sections. Réponds STRICTEMENT en JSON valide avec EXACTEMENT ces clés
(valeurs = texte rédigé, 2 à 5 phrases chacune) :
{"resume_executif": "", "presentation_projet": "", "analyse_marche": "",
"proposition_valeur": "", "modele_economique": "", "plan_operationnel": "",
"analyse_risques": "", "hypotheses_financieres": "", "impact_strategique": "",
"recommandation": ""}.
N'invente aucun chiffre. Aucun texte hors du JSON.
```

**Prompt utilisateur** (assemblé par `run_redacteur`) :

```text
Projet : <nom>
Direction : <direction>
Durée estimée : <duree_estimee_mois> mois
Score de pertinence (calculé par le backend) : <score>/100 | "non calculé"
Description : <description>
Analyse stratégique : <JSON AnalysteOutput>
Scénarios financiers (calculés) : <JSON scenarios>
```

- **Sortie** : `RedacteurOutput` (10 sections). Les clés sont mappées vers les
  titres affichés via `_SECTION_TITLES`.
- **Mode** : `json_mode=True`.

| Clé schéma | Titre de section affiché |
|------------|--------------------------|
| `resume_executif` | Résumé exécutif |
| `presentation_projet` | Présentation du projet |
| `analyse_marche` | Analyse du marché et du contexte |
| `proposition_valeur` | Proposition de valeur |
| `modele_economique` | Modèle économique |
| `plan_operationnel` | Plan opérationnel |
| `analyse_risques` | Analyse des risques |
| `hypotheses_financieres` | Hypothèses et scénarios financiers |
| `impact_strategique` | Impact stratégique et RSE |
| `recommandation` | Recommandation et prochaines étapes |

---

## 6. Agent Synthèse — BIZ-18

**Rôle.** Rédiger une note de synthèse d'**une page** à destination du comité de
direction (CODIR), à partir du résumé exécutif et de la recommandation produits
par l'agent Rédacteur.

**Prompt système (`SYNTHESE_SYSTEM`).**

```text
<_CONTEXTE>
Rôle : agent Synthèse. Tu rédiges une note de synthèse à destination du comité
de direction (CODIR), tenant sur une page. Réponds STRICTEMENT en JSON valide :
{"synthese_codir": ""}. La valeur est un texte de 4 à 8 phrases, sans Markdown.
Aucun texte hors du JSON.
```

**Prompt utilisateur** (assemblé par `run_synthese`) :

```text
Projet : <nom>
Direction : <direction>
Score de pertinence : <score>/100 | "non calculé"
Résumé exécutif : <resume_executif>
Recommandation : <recommandation>
```

- **Sortie** : `SyntheseOutput` (`synthese_codir`).
- **Mode** : `json_mode=True`.

---

## Orchestration de la génération du business plan

`generate_business_plan` ([`app/services/generation.py`](../app/services/generation.py))
calcule d'abord les **scénarios** et le **score** (backend), puis :

- **Mode IA** (`ai_enabled` actif, `_generate_with_ai`) — chaîne séquentielle :

  ```mermaid
  flowchart LR
      A[Backend: scénarios + score] --> B[Analyste]
      B --> C[Financier]
      C --> D[Rédacteur]
      D --> E[Synthèse]
      E --> F[Assemblage des sections + note CODIR]
  ```

  Statut résultant : `generated_ai`.

- **Mode déterministe** (repli, ou `ai_enabled` inactif) — sections et note CODIR
  produites par template à partir des seules données saisies. Statut : `generated`.

> Si **un seul** agent échoue (`AiError`), toute la génération bascule en mode
> déterministe afin de toujours renvoyer un livrable.

## Validation des sorties (`agents._parse`)

1. `_extract_json` isole le bloc entre la première `{` et la dernière `}`
   (tolère un encadrement Markdown ```` ```json ````).
2. `json.loads` puis `model.model_validate` contre le schéma Pydantic cible.
3. En cas d'échec (`JSONDecodeError` ou `ValidationError`) → `AiResponseError`,
   convertie en HTTP 502 côté router, ou déclenchant le repli déterministe lors
   de la génération.
