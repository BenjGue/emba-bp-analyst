// @ts-check
"use strict";

/**
 * Création automatique de tickets JIRA sur échec E2E (BIZ-39).
 *
 * Lit le rapport JSON Playwright (results.json), extrait les scénarios en
 * échec, puis crée dans JIRA :
 *   1. un ticket de BUG décrivant les scénarios en échec (étapes, lien run CI) ;
 *   2. un ticket de CORRECTIF (Tâche préfixée « TECH — ») lié au bug.
 *
 * Aucun secret n'est codé en dur : tout provient des variables d'environnement
 * (fournies par GitHub Secrets dans le workflow e2e.yml).
 *
 * Variables attendues :
 *   - JIRA_BASE_URL     (ex. https://ionis-stm-team-ek7kwlup.atlassian.net)
 *   - JIRA_EMAIL        e-mail du compte JIRA
 *   - JIRA_API_TOKEN    jeton d'API Atlassian
 *   - JIRA_PROJECT_KEY  clé projet (défaut: BIZ)
 *   - JIRA_BUG_ISSUETYPE   type d'issue bug (défaut: Tâche)
 *   - JIRA_TASK_ISSUETYPE  type d'issue tâche (défaut: Tâche)
 *   - RUN_URL           URL du run GitHub Actions (audit)
 *   - RESULTS_PATH      chemin du results.json (défaut: results.json)
 */

const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.JIRA_BASE_URL;
const EMAIL = process.env.JIRA_EMAIL;
const TOKEN = process.env.JIRA_API_TOKEN;
const PROJECT_KEY = process.env.JIRA_PROJECT_KEY || "BIZ";
const BUG_ISSUETYPE = process.env.JIRA_BUG_ISSUETYPE || "Tâche";
const TASK_ISSUETYPE = process.env.JIRA_TASK_ISSUETYPE || "Tâche";
const RUN_URL = process.env.RUN_URL || "(run CI non renseigné)";
const RESULTS_PATH = process.env.RESULTS_PATH || "results.json";

/** Parcourt l'arbre des suites Playwright et collecte les tests en échec. */
function collectFailures(report) {
  /** @type {{title: string, error: string}[]} */
  const failures = [];

  const visitSpec = (spec, ancestry) => {
    for (const t of spec.tests || []) {
      const status = t.status || (t.results || []).at(-1)?.status;
      const ok = status === "expected" || status === "passed";
      if (ok) continue;
      const lastResult = (t.results || []).at(-1) || {};
      const errMessage =
        (lastResult.error && lastResult.error.message) ||
        (lastResult.errors && lastResult.errors[0] && lastResult.errors[0].message) ||
        "Échec sans message d'erreur détaillé.";
      failures.push({
        title: [...ancestry, spec.title].filter(Boolean).join(" › "),
        error: String(errMessage).replace(/\u001b\[[0-9;]*m/g, "").slice(0, 1500),
      });
    }
  };

  const visitSuite = (suite, ancestry) => {
    const nextAncestry = suite.title ? [...ancestry, suite.title] : ancestry;
    for (const spec of suite.specs || []) visitSpec(spec, nextAncestry);
    for (const child of suite.suites || []) visitSuite(child, nextAncestry);
  };

  for (const suite of report.suites || []) visitSuite(suite, []);
  return failures;
}

/** Construit un paragraphe ADF. */
function adfParagraph(text) {
  return { type: "paragraph", content: [{ type: "text", text }] };
}

/** Construit un bloc de code ADF. */
function adfCodeBlock(text) {
  return {
    type: "codeBlock",
    attrs: {},
    content: [{ type: "text", text }],
  };
}

/** Description ADF du ticket de bug. */
function buildBugDescription(failures) {
  const content = [
    adfParagraph(
      "Échec(s) détecté(s) automatiquement par la suite E2E Playwright " +
        "après un déploiement sur main.",
    ),
    adfParagraph(`Run CI : ${RUN_URL}`),
    {
      type: "heading",
      attrs: { level: 3 },
      content: [{ type: "text", text: "Scénarios en échec" }],
    },
  ];
  for (const f of failures) {
    content.push(adfParagraph(`• ${f.title}`));
    content.push(adfCodeBlock(f.error));
  }
  content.push(
    adfParagraph(
      "Artefacts (rapport HTML, traces, vidéos) disponibles dans les " +
        "artefacts du run CI ci-dessus.",
    ),
  );
  return { type: "doc", version: 1, content };
}

/** Description ADF du ticket de correctif. */
function buildFixDescription(bugKey, failures) {
  return {
    type: "doc",
    version: 1,
    content: [
      adfParagraph(
        `Corriger la (les) régression(s) remontée(s) par le bug ${bugKey} ` +
          "(échec E2E après merge sur main).",
      ),
      adfParagraph(`Scénarios concernés : ${failures.length}.`),
      adfParagraph(`Run CI : ${RUN_URL}`),
    ],
  };
}

async function createIssue(fields) {
  const auth = Buffer.from(`${EMAIL}:${TOKEN}`).toString("base64");
  const res = await fetch(`${BASE_URL}/rest/api/3/issue`, {
    method: "POST",
    headers: {
      Authorization: `Basic ${auth}`,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ fields }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Création JIRA échouée (${res.status}) : ${detail}`);
  }
  return res.json();
}

async function main() {
  if (!BASE_URL || !EMAIL || !TOKEN) {
    console.error(
      "Variables JIRA manquantes (JIRA_BASE_URL / JIRA_EMAIL / JIRA_API_TOKEN). " +
        "Abandon sans créer de ticket.",
    );
    process.exit(0);
  }

  const resultsFile = path.resolve(RESULTS_PATH);
  if (!fs.existsSync(resultsFile)) {
    console.error(`Rapport Playwright introuvable : ${resultsFile}. Abandon.`);
    process.exit(0);
  }

  const report = JSON.parse(fs.readFileSync(resultsFile, "utf-8"));
  const failures = collectFailures(report);
  if (failures.length === 0) {
    console.log("Aucun échec E2E détecté : aucun ticket créé.");
    return;
  }

  const shortDate = new Date().toISOString().slice(0, 16).replace("T", " ");
  const bug = await createIssue({
    project: { key: PROJECT_KEY },
    summary: `BUG — Échec E2E Playwright (${failures.length} scénario(s)) — ${shortDate}`,
    issuetype: { name: BUG_ISSUETYPE },
    description: buildBugDescription(failures),
  });
  console.log(`Bug créé : ${bug.key}`);

  const fix = await createIssue({
    project: { key: PROJECT_KEY },
    summary: `TECH — Corriger l'échec E2E ${bug.key}`,
    issuetype: { name: TASK_ISSUETYPE },
    description: buildFixDescription(bug.key, failures),
  });
  console.log(`Correctif créé : ${fix.key}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
