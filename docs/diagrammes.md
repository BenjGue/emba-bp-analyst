# Diagrammes d'architecture — BizPlan-IA

> Trois vues complémentaires du système : **infrastructure** (déploiement Azure),
> **workflow métier** (parcours de génération du business plan) et **workflow de
> développement** (de JIRA à la production). Diagrammes au format **Mermaid**
> (rendu natif sur GitHub / VS Code).

← Retour au [README](../README.md) · Voir aussi [`architecture.md`](./architecture.md) · [`craftsmanship.md`](./craftsmanship.md)

---

## 1. Infrastructure (déploiement Azure)

Vue des services managés Azure et de leur chaîne de déploiement depuis GitHub.
L'API FastAPI est conteneurisée sur **Azure Container Apps** (scale-to-zero) ;
l'orchestration des agents est **applicative** (code FastAPI), l'inférence étant
servie par **Azure AI Foundry** (`chat/completions`, **modèle agnostique**). Les
secrets vivent dans **Key Vault**, l'authentification inter-services repose sur
des **identités managées**.

```mermaid
flowchart TB
    user["👤 Utilisateur (navigateur)"]

    subgraph GH["GitHub"]
      repo["Repo emba-bp-analyst"]
      actions["GitHub Actions (CI/CD)"]
    end

    subgraph AZ["Microsoft Azure"]
      subgraph FRONT["Présentation"]
        swa["Azure Static Web Apps<br/>frontend HTML/CSS/JS"]
      end
      subgraph COMPUTE["Calcul"]
        aca["Azure Container Apps<br/>bizplan-api-dev — FastAPI<br/>scale 0 → 3"]
        acr["Azure Container Registry<br/>images Docker"]
      end
      subgraph AISVC["IA générative"]
        foundry["Azure AI Foundry<br/>inférence chat/completions"]
        claude["Modèle configurable (agnostique)<br/>Claude, GPT… via API"]
      end
      subgraph DATA["Données & secrets"]
        mysql[("Azure DB for MySQL<br/>Flexible Server")]
        kv["Azure Key Vault<br/>secrets / clés"]
        blob["Azure Blob Storage<br/>exports PDF / JSON"]
      end
      subgraph OBS["Observabilité"]
        appi["Application Insights<br/>+ Azure Monitor"]
      end
      mi(["Managed Identity"])
    end

    user --> swa
    swa <--> aca
    actions -->|push image| acr
    acr --> aca
    actions -->|OIDC deploy| aca
    aca --> mysql
    aca --> foundry
    foundry --> claude
    aca --> blob
    aca -. secrets .-> kv
    aca --> appi
    foundry --> appi
    mi -. auth .- aca
    mi -. auth .- kv
```

---

## 2. Workflow métier (génération du business plan)

Du formulaire du porteur de projet jusqu'à la décision du CODIR. Point clé :
**l'IA juge, le code arbitre** — le score de pertinence est calculé côté backend
de façon déterministe, jamais par l'IA.

```mermaid
flowchart TD
    A["👤 Porteur de projet<br/>saisit le projet (formulaire)"] --> B["API FastAPI<br/>validation Pydantic (JSON)"]
    B --> C[("MySQL<br/>projet + hypothèses + risques")]
    B --> D{"Orchestrateur (code FastAPI)<br/>generation.py — séquentiel"}
    B --> S["⚙️ Calcul des SCÉNARIOS financiers<br/>backend déterministe (bas / médian / haut)"]
    D --> E["Agent Analyste<br/>forces / faiblesses / risques / opportunités / actions"]
    E --> F["Agent Financier<br/>commente les scénarios (ne recalcule rien)"]
    S --> F
    F --> G["⚙️ Calcul du SCORE — backend déterministe<br/>6 dimensions pondérées → 0–100"]
    G --> H["Agent Rédacteur BP<br/>business plan en 11 sections"]
    H --> I["Agent Synthèse CODIR<br/>note d'une page"]
    I --> J["Validation JSON ; repli déterministe si un agent échoue"]
    J --> K[("Persistance des résultats (MySQL)")]
    J --> L["Export (Blob Storage)<br/>PDF / JSON"]
    K --> M["📊 Tableau de bord comparatif<br/>+ recommandations Go / No-Go"]
    L --> M
    M --> N["👔 CODIR — priorisation des projets"]
```

---

## 3. Workflow de développement (de JIRA à la production)

Chaîne d'outils streamlinée pour le binôme : chaque maillon automatise le passage
au suivant. Traçabilité totale ticket ↔ code via les *smart commits* `BIZ-xx`.
Un échec E2E après déploiement **crée automatiquement** les tickets de bug et de
correctif dans JIRA.

```mermaid
flowchart LR
    subgraph PLAN["Planification"]
      jira["JIRA — projet BIZ<br/>Epics → Stories → Sous-tâches"]
    end
    subgraph DEV["Développement assisté IA"]
      vscode["VSCode + IA<br/>(Copilot / Claude + MCP JIRA)"]
      branch["Branche feature/BIZ-xx"]
    end
    subgraph GHUB["GitHub"]
      pr["Pull Request<br/>1 revue + checks verts"]
      main["main — protégée (squash & merge)"]
    end
    subgraph PIPE["GitHub Actions"]
      ci["CI — Ruff + mypy + pytest (≥ 80%)"]
      sec["Sécurité — CodeQL + secret scanning"]
      build["Build image Docker"]
      deploy["Deploy OIDC → ACR → Container Apps"]
      e2e["E2E Playwright<br/>après déploiement"]
    end
    subgraph AZ["Azure"]
      app["bizplan-api-dev (live)"]
    end

    jira -->|MCP : lecture ticket / statut| vscode
    vscode --> branch
    branch --> pr
    pr --> ci
    ci --> sec
    sec --> build
    pr -->|merge squash| main
    main --> build
    build --> deploy
    deploy --> app
    deploy --> e2e
    e2e -->|✅ succès| done["Ticket → Terminé"]
    e2e -->|❌ échec| bug["Création auto :<br/>ticket BUG - + correctif TECH —"]
    bug --> jira
    done --> jira
    vscode -. smart commits BIZ-xx .-> pr
```

---

*BizPlan-IA — Executive MBA EPITECH P2026 — Benjamin Guérin & Mauricette.*
