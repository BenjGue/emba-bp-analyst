# Livrables — BizPlan-IA

> Tous les livrables attendus pour le Projet 2, chacun relié aux **critères d'évaluation** du cas. Sert de checklist de soutenance.

← Retour au [README](../README.md)

---

## 1. Synthèse des livrables (exigés par le cas)

| # | Livrable | Statut | Responsable |
|---|---|---|---|
| L1 | **Base MySQL** fictive (schéma + données) | ☐ | Mauricette |
| L2 | **Score de pertinence** (modèle + calcul) | ☐ | Mauricette |
| L3 | **Interface web** (démonstrateur) | ☐ | Mauricette / Benjamin |
| L4 | **Prompts documentés** (catalogue) | ☐ | Benjamin |
| L5 | **Vidéo de démonstration** | ☐ | Binôme |
| L6 | **Rapport final** | ☐ | Binôme |

---

## 2. L1 — Base MySQL fictive

**Objectif** : permettre à l'IA d'analyser et comparer les projets.

### Volumétrie imposée
- **5 à 10 projets** fictifs.
- **30 à 50 hypothèses financières**.
- **20 paramètres stratégiques**.
- **10 risques types** + **10 opportunités types**.
- **10 profils de porteurs** de projet.

### Schéma minimal (tables imposées)

```sql
-- Table projets
CREATE TABLE projets (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nom VARCHAR(150) NOT NULL,
  type VARCHAR(80),            -- RH, service_numerique, logistique, app_client, territorial
  porteur_id INT,
  forme_juridique VARCHAR(120),
  date_creation DATE,
  descriptif TEXT,
  FOREIGN KEY (porteur_id) REFERENCES porteurs(id)
);

CREATE TABLE hypotheses_financieres (
  id INT PRIMARY KEY AUTO_INCREMENT,
  projet_id INT NOT NULL,
  categorie VARCHAR(60),       -- salaires, materiel, logiciel, fiscalite, recette_1...
  nature ENUM('depense','recette'),
  montant DECIMAL(12,2),
  periode VARCHAR(20),         -- mensuel / annuel
  FOREIGN KEY (projet_id) REFERENCES projets(id)
);

CREATE TABLE parametres_strategiques (
  id INT PRIMARY KEY AUTO_INCREMENT,
  projet_id INT NOT NULL,
  alignement_groupe TINYINT,   -- 1 à 5
  impact_branche TINYINT,
  avantage_concurrentiel TINYINT,
  valeur_sociale TINYINT,
  impact_environnemental TINYINT,
  FOREIGN KEY (projet_id) REFERENCES projets(id)
);

CREATE TABLE risques (
  id INT PRIMARY KEY AUTO_INCREMENT,
  projet_id INT,
  type VARCHAR(40),            -- technique, humain, reglementaire
  description TEXT,
  gravite TINYINT,             -- 1 à 5
  probabilite TINYINT          -- 1 à 5
);

CREATE TABLE opportunites (
  id INT PRIMARY KEY AUTO_INCREMENT,
  projet_id INT,
  description TEXT,
  potentiel TINYINT            -- 1 à 5
);

CREATE TABLE scenarios (
  id INT PRIMARY KEY AUTO_INCREMENT,
  projet_id INT NOT NULL,
  type ENUM('bas','median','haut'),
  ca_annuel DECIMAL(12,2),
  ebitda DECIMAL(12,2),
  resultat_exploitation DECIMAL(12,2),
  FOREIGN KEY (projet_id) REFERENCES projets(id)
);

CREATE TABLE porteurs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nom VARCHAR(120),
  branche VARCHAR(80),
  maturite TINYINT             -- 1 à 5 (maturité du porteur)
);

CREATE TABLE scores (
  id INT PRIMARY KEY AUTO_INCREMENT,
  projet_id INT NOT NULL,
  total TINYINT,               -- 0 à 100
  detail_json JSON,            -- ventilation par dimension
  calcule_le DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Projets fictifs de référence
1. Outil RH interne.
2. Service numérique pour les facteurs (autour de Facteo / smartphone).
3. Innovation logistique d'optimisation de la livraison.
4. Application client.
5. Projet territorial.

**Critère d'évaluation visé** : *Qualité de la base MySQL (structure, cohérence, réalisme).*

---

## 3. L2 — Score de pertinence

**Objectif** : score final **0–100** intégrant au moins **6 dimensions**.

### Dimensions et pondération

| Dimension | Critères sous-jacents | Pondération |
|---|---|---|
| Rentabilité | RoI, délai de retour sur investissement | **30 %** |
| Alignement stratégique | Alignement Groupe, impact branches | **20 %** |
| Risque | Risque technique + risque humain | **20 %** |
| Impact opérationnel | Ressources, complexité, dépendances | **10 %** |
| Impact social / environnemental | Valeur sociale, impact environnemental | **10 %** |
| Faisabilité technique | Maturité techno, maturité du porteur | **10 %** |

### Formule

```
1. Normalisation min-max de chaque critère sur [0,1]
   (le risque est inversé : risque élevé → score faible)
2. Agrégation par dimension (moyenne des critères normalisés)
3. Score = Σ (dimension_normalisée × pondération) × 100
4. Arrondi entier, borné [0,100]
```

### Exemple chiffré (Facteo+)

| Dimension | Score normalisé | × Pondération | Contribution |
|---|---|---|---|
| Rentabilité | 0,80 | 0,30 | 24,0 |
| Alignement | 0,80 | 0,20 | 16,0 |
| Risque (inversé) | 0,70 | 0,20 | 14,0 |
| Impact opérationnel | 0,60 | 0,10 | 6,0 |
| Impact social/env. | 0,90 | 0,10 | 9,0 |
| Faisabilité | 0,90 | 0,10 | 9,0 |
| **TOTAL** | | | **78 / 100** |

> Le calcul est **déterministe, côté backend** (jamais délégué à l'IA) et **testé** sur ses bornes (cf. [`AI-rules.md`](./AI-rules.md) §5).

**Critère d'évaluation visé** : *Qualité du score de pertinence (cohérence, pondération, justification).*

---

## 4. L3 — Interface web (démonstrateur fonctionnel)

Le démonstrateur **raconte une histoire utilisateur** :

1. Le porteur **saisit** les informations clés (formulaire).
2. L'outil **calcule** automatiquement le score.
3. L'IA **génère** le business plan complet (11 sections).
4. L'IA **propose** 3 scénarios (bas / médian / haut).
5. L'IA **rédige** la note de synthèse CODIR.
6. Le manager **télécharge / copie** la synthèse.

### Composants obligatoires
- ☐ Formulaire de saisie.
- ☐ Calcul automatique du score.
- ☐ Analyse IA (forces, faiblesses, risques).
- ☐ Export texte (synthèse).
- ☐ Tableau de bord simple (comparaison de projets).

### Options (si temps)
- Visualisations avancées (radar, heatmap).
- Simulation d'impact d'une décision.
- Analyse automatique d'un fichier Excel.
- Chatbot d'aide au porteur de projet.

**Critère d'évaluation visé** : *Qualité du démonstrateur (ergonomie, fluidité, stabilité).*

---

## 5. L4 — Prompts documentés

Catalogue versionné (`app/agents/prompts/`), un fichier par prompt, avec variables dynamiques.

### Les prompts attendus

| Prompt | Rôle | Sortie |
|---|---|---|
| **Analyse de projet** | Identifie forces / faiblesses à partir des données saisies | JSON |
| **Génération du business plan** | BP structuré en **11 sections** | JSON |
| **Scénarios financiers** | 3 scénarios : bas, médian, haut | JSON |
| **Note CODIR** | Synthèse 1 page pour le comité | Texte/JSON |
| **Identification des risques** | Risques + criticité | JSON |
| **Actions correctives** | Recommandations actionnables | JSON |

### Les 11 sections du business plan
1. Résumé exécutif
2. Présentation du projet
3. Analyse du marché et du contexte
4. Analyse concurrentielle
5. Proposition de valeur
6. Modèle économique
7. Plan opérationnel
8. Analyse des risques
9. Hypothèses et scénarios financiers
10. Impact stratégique et RSE
11. Recommandation et prochaines étapes

### Contraintes imposées à chaque prompt
- Sortie **JSON structuré**.
- Variables **paramétrées** (pas de texte en dur).
- Style **neutre, professionnel, non prescriptif**.
- **Interdiction d'inférer** des données non fournies.

**Critère d'évaluation visé** : *Qualité des prompts (structure, robustesse, pertinence).*

---

## 6. L5 — Vidéo de démonstration

- Durée cible : **5 à 8 min**.
- Déroulé : problème métier → saisie d'un projet → score → BP généré → scénarios → note CODIR → tableau de bord comparatif → mot sur l'architecture/arbitrages.
- Pédagogie : montrer **un Go** et **un No-Go** pour illustrer l'aide à la priorisation.

**Critère d'évaluation visé** : *Qualité de la vidéo de démonstration (clarté, pédagogie).*

---

## 7. L6 — Rapport final

Doit couvrir et **expliquer les choix** :
- Modèle de score (dimensions, pondération, formule, exemple chiffré).
- Architecture technique et **arbitrages** (cf. [`architecture.md`](./architecture.md)).
- Conception des prompts.
- Limites du démonstrateur.
- Bilan binôme et répartition.

**Critère d'évaluation visé** : *Capacité à expliquer les choix (architecture, arbitrages, limites)* et *Qualité du business plan généré.*

---

## 8. Récapitulatif périmètre

| Obligatoire | Optionnel |
|---|---|
| Score de pertinence | Visualisations avancées (radar, heatmap) |
| Base MySQL | Simulation d'impact d'une décision |
| Génération auto du business plan | Analyse automatique d'un fichier Excel |
| Analyse IA (forces, faiblesses, risques) | Chatbot d'aide au porteur de projet |
| Interface web simple | |
| Note de synthèse CODIR | |

---

← [AI-rules.md](./AI-rules.md) · Suite : [`How-to-setup.md`](./How-to-setup.md)
