-- Schéma relationnel BizPlan-IA (MySQL 8) — BIZ-22
-- DDL idempotent : recrée le schéma applicatif complet.
-- Source de vérité du schéma : les migrations Alembic (migrations/versions/,
-- BIZ-29), appliquées automatiquement au démarrage. Ce fichier documente le
-- modèle et sert au provisionnement manuel / aux revues.

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS projects (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    nom                 VARCHAR(200)  NOT NULL,
    description         VARCHAR(1000) NOT NULL,
    direction           VARCHAR(100)  NOT NULL,
    duree_estimee_mois  INT           NOT NULL,
    created_at          DATETIME      NOT NULL,
    INDEX ix_projects_direction (direction)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS financial_assumptions (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    project_id              INT      NOT NULL,
    investissement_initial  DOUBLE   NOT NULL,
    revenus_annuels         DOUBLE   NOT NULL,
    couts_annuels           DOUBLE   NOT NULL,
    delai_rentabilite_mois  INT      NOT NULL,
    created_at              DATETIME NOT NULL,
    UNIQUE KEY uq_financial_project (project_id),
    CONSTRAINT fk_financial_project FOREIGN KEY (project_id)
        REFERENCES projects (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS strategic_assessments (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    project_id           INT      NOT NULL,
    rentabilite          INT      NOT NULL,
    alignement           INT      NOT NULL,
    risque               INT      NOT NULL,
    impact_operationnel  INT      NOT NULL,
    impact_social        INT      NOT NULL,
    faisabilite          INT      NOT NULL,
    created_at           DATETIME NOT NULL,
    UNIQUE KEY uq_assessment_project (project_id),
    CONSTRAINT fk_assessment_project FOREIGN KEY (project_id)
        REFERENCES projects (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS scores (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    project_id  INT      NOT NULL,
    total       DOUBLE   NOT NULL,
    dimensions  JSON     NOT NULL,
    created_at  DATETIME NOT NULL,
    INDEX ix_scores_project (project_id),
    CONSTRAINT fk_score_project FOREIGN KEY (project_id)
        REFERENCES projects (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS business_plans (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    project_id      INT         NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'generated',
    sections        JSON        NOT NULL,
    synthese_codir  TEXT        NOT NULL,
    created_at      DATETIME    NOT NULL,
    UNIQUE KEY uq_bp_project (project_id),
    CONSTRAINT fk_bp_project FOREIGN KEY (project_id)
        REFERENCES projects (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS scenarios (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    project_id  INT         NOT NULL,
    type        VARCHAR(20) NOT NULL,
    data        JSON        NOT NULL,
    created_at  DATETIME    NOT NULL,
    INDEX ix_scenarios_project (project_id),
    CONSTRAINT fk_scenario_project FOREIGN KEY (project_id)
        REFERENCES projects (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS financial_imports (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    project_id    INT          NOT NULL,
    filename      VARCHAR(255) NOT NULL,
    content_type  VARCHAR(100) NOT NULL,
    size_bytes    INT          NOT NULL,
    content       MEDIUMBLOB   NOT NULL,
    uploaded_at   DATETIME     NOT NULL,
    UNIQUE KEY uq_import_project (project_id),
    CONSTRAINT fk_import_project FOREIGN KEY (project_id)
        REFERENCES projects (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- BIZ-32 : tableau financier détaillé (temps en lignes, catégories en colonnes).
CREATE TABLE IF NOT EXISTS financial_statements (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    project_id   INT          NOT NULL,
    period_unit  VARCHAR(20)  NOT NULL,
    periods      JSON         NOT NULL,
    depenses     JSON         NOT NULL,
    recettes     JSON         NOT NULL,
    agregats     JSON         NOT NULL,
    created_at   DATETIME     NOT NULL,
    UNIQUE KEY uq_statement_project (project_id),
    CONSTRAINT fk_statement_project FOREIGN KEY (project_id)
        REFERENCES projects (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- BIZ-88 : catalogues de référence partagés (indépendants des projets),
-- exploités par l'IA pour analyser et comparer les projets.
CREATE TABLE IF NOT EXISTS risk_types (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    code             VARCHAR(50)  NOT NULL,
    libelle          VARCHAR(150) NOT NULL,
    categorie        VARCHAR(50)  NOT NULL,
    description      VARCHAR(500) NOT NULL,
    severite_defaut  INT          NOT NULL,
    UNIQUE KEY uq_risk_type_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS opportunity_types (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    code           VARCHAR(50)  NOT NULL,
    libelle        VARCHAR(150) NOT NULL,
    categorie      VARCHAR(50)  NOT NULL,
    description    VARCHAR(500) NOT NULL,
    impact_defaut  INT          NOT NULL,
    UNIQUE KEY uq_opportunity_type_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS strategic_parameters (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    code         VARCHAR(50)  NOT NULL,
    libelle      VARCHAR(150) NOT NULL,
    dimension    VARCHAR(50)  NOT NULL,
    description  VARCHAR(500) NOT NULL,
    poids        DOUBLE       NOT NULL,
    UNIQUE KEY uq_strategic_parameter_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS financial_hypotheses (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    code           VARCHAR(50)  NOT NULL,
    libelle        VARCHAR(150) NOT NULL,
    categorie      VARCHAR(50)  NOT NULL,
    unite          VARCHAR(20)  NOT NULL,
    valeur_defaut  DOUBLE       NOT NULL,
    description    VARCHAR(500) NOT NULL,
    UNIQUE KEY uq_financial_hypothesis_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
