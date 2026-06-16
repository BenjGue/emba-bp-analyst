"use strict";

// -------- Constantes métier --------
const DIRECTIONS = [
  "Services-Courrier-Colis",
  "La Banque Postale",
  "La Poste Groupe",
  "Réseau La Poste",
  "Geopost",
  "Numérique",
];

const DIMENSIONS = [
  ["rentabilite", "Rentabilité"],
  ["alignement", "Alignement stratégique"],
  ["risque", "Maîtrise du risque"],
  ["impact_operationnel", "Impact opérationnel"],
  ["impact_social", "Impact social"],
  ["faisabilite", "Faisabilité"],
];

const view = document.getElementById("view");

// Jeton de rendu : chaque navigation incrémente ce compteur. Les vues
// asynchrones (dashboard, fiche projet) capturent le jeton courant avant leur
// appel API et vérifient, une fois la réponse reçue, qu'une autre vue n'a pas
// été demandée entre-temps. Sans ce garde-fou, une réponse API lente (cold
// start Azure) écrase la vue affichée par l'utilisateur (BIZ-53).
let activeRender = 0;

function beginRender() {
  return ++activeRender;
}

function isStaleRender(token) {
  return token !== activeRender;
}

// -------- Utilitaires API --------
async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(`/projects${path}`, opts);
  if (!res.ok) {
    let detail = `Erreur ${res.status}`;
    try {
      const data = await res.json();
      if (data.detail) {
        detail =
          typeof data.detail === "string"
            ? data.detail
            : data.detail.map((e) => e.msg).join(", ");
      }
    } catch (_) {
      /* corps non JSON */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

// -------- Helpers UI --------
function toast(message, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.className = isError ? "toast error" : "toast";
  el.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (el.hidden = true), 3200);
}

function scoreClass(score) {
  if (score === null || score === undefined) return "na";
  if (score >= 70) return "score-vert";
  if (score >= 40) return "score-orange";
  return "score-rouge";
}

function scoreColor(score) {
  if (score >= 70) return "var(--vert)";
  if (score >= 40) return "var(--orange)";
  return "var(--rouge)";
}

function recommendation(score) {
  if (score >= 70) return "✅ Go — projet pertinent";
  if (score >= 40) return "🟠 Go conditionnel — à arbitrer";
  return "🔴 No-Go — pertinence insuffisante";
}

function spinner() {
  view.innerHTML = '<div class="spinner"></div>';
}

function euro(n) {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(n);
}

function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

// -------- Vue : tableau de bord --------
async function renderDashboard(direction = "") {
  const token = beginRender();
  spinner();
  let projects;
  try {
    const q = direction ? `?direction=${encodeURIComponent(direction)}` : "";
    projects = await api("GET", `${q}`);
  } catch (e) {
    if (isStaleRender(token)) return;
    toast(e.message, true);
    projects = [];
  }
  // Une autre vue a été demandée pendant l'appel API : ne pas l'écraser.
  if (isStaleRender(token)) return;

  const tpl = document.getElementById("tpl-dashboard").content.cloneNode(true);
  const select = tpl.getElementById("filter-direction");
  select.appendChild(el(`<option value="">Toutes les directions</option>`));
  for (const d of DIRECTIONS) {
    const opt = el(`<option>${d}</option>`);
    if (d === direction) opt.selected = true;
    select.appendChild(opt);
  }
  select.addEventListener("change", () => renderDashboard(select.value));

  const list = tpl.getElementById("dashboard-list");
  if (!projects.length) {
    list.appendChild(
      el(
        `<div class="empty"><p>Aucun projet pour le moment.</p>
         <button class="btn btn-primary" data-nav="wizard">Créer le premier projet</button></div>`,
      ),
    );
  } else {
    for (const p of projects) {
      const cls = scoreClass(p.score_total);
      const badge =
        p.score_total === null
          ? `<div class="score-badge na">N/A</div>`
          : `<div class="score-badge ${cls}">${Math.round(p.score_total)}</div>`;
      const bpTag = p.has_business_plan
        ? `<span class="tag bp">BP généré</span>`
        : "";
      const row = el(`
        <div class="project-row" data-project="${p.id}">
          ${badge}
          <div class="row-main">
            <h3>${escapeHtml(p.nom)}</h3>
            <div class="meta"><span class="tag">${escapeHtml(p.direction)}</span> ${bpTag}</div>
          </div>
          <button class="btn-delete" type="button" title="Supprimer le projet"
                  aria-label="Supprimer le projet ${escapeHtml(p.nom)}">🗑</button>
        </div>`);
      const delBtn = row.querySelector(".btn-delete");
      delBtn.addEventListener("click", async (ev) => {
        ev.stopPropagation();
        if (!confirm(`Supprimer définitivement le projet « ${p.nom} » ?`)) return;
        try {
          await api("DELETE", `/${p.id}`);
          toast("Projet supprimé");
          renderDashboard(direction);
        } catch (e) {
          toast(e.message, true);
        }
      });
      row.addEventListener("click", () => renderDetail(p.id));
      list.appendChild(row);
    }
  }

  view.innerHTML = "";
  view.appendChild(tpl);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

// Libellés d'affichage des postes du tableau financier détaillé (BIZ-32).
const STATEMENT_LABELS = {
  salaires: "Salaires",
  achat_materiel: "Achat matériel",
  achat_logiciel: "Achat logiciel",
  charges_fiscales: "Charges fiscales",
  frais_administratifs: "Frais administratifs",
  frais_bancaires: "Frais bancaires",
  achats_divers: "Achats divers",
  autres_depenses: "Autres dépenses",
  total_depenses: "Total dépenses",
  nombre_clients: "Nombre de clients",
  recette_produit_1: "Recette produit/service 1",
  recette_produit_2: "Recette produit/service 2",
  recette_produit_3: "Recette produit/service 3",
  recette_produit_4: "Recette produit/service 4",
  chiffre_affaires: "Chiffre d'affaires",
  marge_brute: "Marge brute",
  ebe: "EBE",
  resultat_exploitation: "Résultat d'exploitation",
  ebitda: "EBITDA",
};

// Restitue le tableau financier détaillé importé dans #statement-preview (BIZ-32).
function renderStatement(stmt) {
  const host = document.getElementById("statement-preview");
  if (!host) return;
  if (!stmt || !stmt.periods || !stmt.periods.length) {
    host.innerHTML = "";
    return;
  }
  const fmt = (v) => Number(v).toLocaleString("fr-FR");
  const headerCells = stmt.periods.map((p) => `<th>${escapeHtml(p)}</th>`).join("");
  const section = (title, series) => {
    const keys = Object.keys(series || {});
    if (!keys.length) return "";
    const rows = keys
      .map((key) => {
        const label = STATEMENT_LABELS[key] || key;
        const cells = series[key].map((v) => `<td>${fmt(v)}</td>`).join("");
        return `<tr><th class="row-label">${escapeHtml(label)}</th>${cells}</tr>`;
      })
      .join("");
    return `<tr class="group-row"><th colspan="${stmt.periods.length + 1}">${title}</th></tr>${rows}`;
  };
  host.innerHTML = `
    <div class="statement-wrap">
      <p class="form-hint">Tableau importé — granularité : ${escapeHtml(stmt.period_unit)}.</p>
      <div class="table-scroll">
        <table class="statement-table">
          <thead><tr><th>Poste</th>${headerCells}</tr></thead>
          <tbody>
            ${section("Dépenses", stmt.depenses)}
            ${section("Recettes", stmt.recettes)}
            ${section("Agrégats", stmt.agregats)}
          </tbody>
        </table>
      </div>
    </div>`;
}

// -------- Vue : assistant de création --------
function renderWizard() {
  // Invalide tout rendu asynchrone en cours (dashboard/fiche) afin qu'une
  // réponse API tardive n'écrase pas l'assistant (BIZ-53). Le jeton est
  // réutilisé par les étapes asynchrones (proposition IA des notes, BIZ-56).
  const renderToken = beginRender();
  const state = {
    project: null,
    financials: null,
    score: null,
    // Saisies de l'étape 1 conservées pour la navigation Précédent/Continuer
    // (BIZ-40) : restituées à chaque rendu de l'étape Projet.
    form: {
      nom: "",
      description: "",
      direction: DIRECTIONS[0],
      duree: "12",
    },
  };
  let step = 1;

  function steps() {
    const labels = ["Projet", "Finances", "Stratégie", "Récap"];
    return `<div class="steps">${labels
      .map((l, i) => {
        const n = i + 1;
        const c = n < step ? "done" : n === step ? "active" : "";
        return `<div class="step ${c}">${n}. ${l}</div>`;
      })
      .join("")}</div>`;
  }

  function shell(inner, headerAction = "") {
    view.innerHTML = `
      <button class="back" data-nav="dashboard">‹ Retour au tableau de bord</button>
      <div class="wizard-head">
        <h2>Nouveau projet</h2>
        ${headerAction}
      </div>
      ${steps()}
      <div class="card">${inner}</div>`;
  }

  function stepProject() {
    shell(
      `
      <label class="field">Nom du projet <span class="req" aria-hidden="true">*</span>
        <input id="f-nom" maxlength="200" required aria-required="true"
               placeholder="Ex. Casiers connectés en bureau de poste" />
        <small class="field-error" id="err-nom" hidden></small>
      </label>
      <label class="field">Description <span class="req" aria-hidden="true">*</span>
        <textarea id="f-desc" maxlength="1000" required aria-required="true"
                  placeholder="Écrivez librement vos idées ; le bouton ✨ en haut à droite les reformate."></textarea>
        <small class="field-error" id="err-desc" hidden></small>
        <small class="form-hint">L'IA reformule l'intégralité du champ ; vous pourrez relire et ajuster.</small>
      </label>
      <div class="grid-2">
        <label class="field">Direction concernée <span class="req" aria-hidden="true">*</span>
          <select id="f-dir">${DIRECTIONS.map((d) => `<option>${d}</option>`).join("")}</select>
        </label>
        <label class="field">Durée estimée (mois) <span class="req" aria-hidden="true">*</span>
          <input id="f-duree" type="number" min="1" max="120" value="12" required aria-required="true" />
          <small class="field-error" id="err-duree" hidden></small>
        </label>
      </div>
      <p class="form-hint"><span class="req" aria-hidden="true">*</span> Champs obligatoires</p>
      <div class="btn-row">
        <button class="btn btn-primary" id="next">Continuer ›</button>
      </div>`,
      `<button type="button" class="btn btn-ghost btn-ai" id="ai-reformat"
               title="Reformater la description avec l'IA">✨ Reformater avec l'IA</button>`,
    );

    // Restitue les saisies précédentes (navigation Précédent/Continuer, BIZ-40).
    document.getElementById("f-nom").value = state.form.nom;
    document.getElementById("f-desc").value = state.form.description;
    document.getElementById("f-dir").value = state.form.direction;
    document.getElementById("f-duree").value = state.form.duree;

    // Mémorise chaque saisie en continu pour la conserver entre les étapes.
    function captureForm() {
      state.form.nom = val("f-nom");
      state.form.description = val("f-desc");
      state.form.direction = val("f-dir");
      state.form.duree = val("f-duree");
    }
    for (const id of ["f-nom", "f-desc", "f-dir", "f-duree"]) {
      document.getElementById(id).addEventListener("input", captureForm);
    }

    // Bouton IA (en haut à droite du titre) : reformate tout le champ
    // description en place à partir de son contenu actuel (BIZ-55).
    document.getElementById("ai-reformat").onclick = async () => {
      const description = val("f-desc");
      if (!description) {
        toast("Saisissez d'abord une description à reformater.", true);
        return;
      }
      const btn = document.getElementById("ai-reformat");
      btn.disabled = true;
      const label = btn.textContent;
      btn.textContent = "⏳ Reformatage en cours…";
      try {
        const res = await api("POST", "/draft-description", {
          idees: description,
          direction: val("f-dir"),
          nom: val("f-nom") || null,
        });
        document.getElementById("f-desc").value = res.description;
        state.form.description = res.description;
        toast("Description reformatée par l'IA — relisez-la avant de continuer.");
      } catch (e) {
        toast(e.message, true);
      } finally {
        btn.disabled = false;
        btn.textContent = label;
      }
    };

    document.getElementById("next").onclick = async () => {
      const nom = val("f-nom");
      const description = val("f-desc");
      const dureeRaw = val("f-duree");
      const duree = Number(dureeRaw);

      const errors = {};
      if (!nom) errors["nom"] = "Le nom du projet est obligatoire.";
      else if (nom.length > 200) errors["nom"] = "Le nom ne doit pas dépasser 200 caractères.";
      if (!description) errors["desc"] = "La description est obligatoire.";
      else if (description.length > 1000)
        errors["desc"] = "La description ne doit pas dépasser 1000 caractères.";
      if (!dureeRaw || !Number.isFinite(duree) || !Number.isInteger(duree))
        errors["duree"] = "Indiquez une durée en mois (nombre entier).";
      else if (duree < 1 || duree > 120)
        errors["duree"] = "La durée doit être comprise entre 1 et 120 mois.";

      if (!applyFieldErrors(["nom", "desc", "duree"], errors)) return;

      const payload = {
        nom: nom,
        description: description,
        direction: val("f-dir"),
        duree_estimee_mois: duree,
      };
      // Conserve les saisies pour un éventuel retour à cette étape (BIZ-40).
      captureForm();
      try {
        // Réutilise le projet déjà créé si l'on revient sur cette étape, pour
        // éviter de créer des doublons à chaque clic sur « Continuer » (BIZ-40).
        if (state.project) {
          state.project = await api("PUT", `/${state.project.id}`, payload);
        } else {
          state.project = await api("POST", "", payload);
        }
        step = 2;
        stepFinancials();
      } catch (e) {
        toast(e.message, true);
      }
    };
  }

  function stepFinancials() {
    shell(`
      <p class="muted">Hypothèses financières du projet.</p>
      <div class="ai-assist">
        <label class="field">Importer un fichier Excel (.xlsx)
          <input id="f-xlsx" type="file" accept=".xlsx,.xlsm" />
        </label>
        <button type="button" class="btn btn-ghost" id="xlsx-import">⬆️ Importer depuis Excel</button>
        <small class="form-hint">Le fichier doit contenir les lignes : investissement initial, revenus annuels, coûts annuels, délai de rentabilité. Les colonnes pluriannuelles sont moyennées.</small>
        <button type="button" class="btn btn-ghost" id="xlsx-import-detailed">📊 Importer un tableau détaillé</button>
        <small class="form-hint">Format détaillé (cf. spécification) : le temps en lignes (semaines/mois/années) et les catégories en colonnes — dépenses, recettes, agrégats. Les hypothèses sont dérivées automatiquement.</small>
        <div id="statement-preview"></div>
      </div>
      <div class="grid-2">
        <label class="field">Investissement initial (€)
          <input id="f-inv" type="number" min="0" value="100000" />
        </label>
        <label class="field">Revenus annuels attendus (€)
          <input id="f-rev" type="number" min="0" value="80000" />
        </label>
        <label class="field">Coûts annuels (€)
          <input id="f-cout" type="number" min="0" value="30000" />
        </label>
        <label class="field">Délai de rentabilité visé (mois)
          <input id="f-delai" type="number" min="1" max="600" value="36" />
        </label>
      </div>
      <div class="btn-row">
        <button class="btn btn-ghost" id="prev">‹ Précédent</button>
        <button class="btn btn-primary" id="next">Continuer ›</button>
      </div>`);

    document.getElementById("prev").onclick = stepProject;
    document.getElementById("xlsx-import").onclick = async () => {
      const input = document.getElementById("f-xlsx");
      const file = input.files && input.files[0];
      if (!file) {
        toast("Sélectionnez d'abord un fichier Excel.", true);
        return;
      }
      const btn = document.getElementById("xlsx-import");
      btn.disabled = true;
      const label = btn.textContent;
      btn.textContent = "⏳ Import en cours…";
      try {
        const form = new FormData();
        form.append("file", file);
        const res = await fetch(`/projects/${state.project.id}/financials/import`, {
          method: "POST",
          body: form,
        });
        if (!res.ok) {
          let detail = `Erreur ${res.status}`;
          try {
            const data = await res.json();
            if (data.detail) detail = data.detail;
          } catch (_) {
            /* corps non JSON */
          }
          throw new Error(detail);
        }
        const data = await res.json();
        const f = data.financials;
        document.getElementById("f-inv").value = f.investissement_initial;
        document.getElementById("f-rev").value = f.revenus_annuels;
        document.getElementById("f-cout").value = f.couts_annuels;
        document.getElementById("f-delai").value = f.delai_rentabilite_mois;
        toast("Données importées — vérifiez les valeurs avant de continuer.");
      } catch (e) {
        toast(e.message, true);
      } finally {
        btn.disabled = false;
        btn.textContent = label;
      }
    };
    document.getElementById("xlsx-import-detailed").onclick = async () => {
      const input = document.getElementById("f-xlsx");
      const file = input.files && input.files[0];
      if (!file) {
        toast("Sélectionnez d'abord un fichier Excel.", true);
        return;
      }
      const btn = document.getElementById("xlsx-import-detailed");
      btn.disabled = true;
      const label = btn.textContent;
      btn.textContent = "⏳ Import en cours…";
      try {
        const form = new FormData();
        form.append("file", file);
        const res = await fetch(`/projects/${state.project.id}/financials/import-detailed`, {
          method: "POST",
          body: form,
        });
        if (!res.ok) {
          let detail = `Erreur ${res.status}`;
          try {
            const data = await res.json();
            if (data.detail) detail = data.detail;
          } catch (_) {
            /* corps non JSON */
          }
          throw new Error(detail);
        }
        const data = await res.json();
        const f = data.financials;
        document.getElementById("f-inv").value = f.investissement_initial;
        document.getElementById("f-rev").value = f.revenus_annuels;
        document.getElementById("f-cout").value = f.couts_annuels;
        document.getElementById("f-delai").value = f.delai_rentabilite_mois;
        renderStatement(data.statement);
        toast("Tableau détaillé importé — hypothèses dérivées, vérifiez les valeurs.");
      } catch (e) {
        toast(e.message, true);
      } finally {
        btn.disabled = false;
        btn.textContent = label;
      }
    };
    document.getElementById("next").onclick = async () => {
      const payload = {
        investissement_initial: Number(val("f-inv")),
        revenus_annuels: Number(val("f-rev")),
        couts_annuels: Number(val("f-cout")),
        delai_rentabilite_mois: Number(val("f-delai")),
      };
      try {
        state.financials = await api(
          "PUT",
          `/${state.project.id}/financials`,
          payload,
        );
        step = 3;
        stepDimensions();
      } catch (e) {
        toast(e.message, true);
      }
    };
  }

  function stepDimensions() {
    const token = renderToken;
    // État mutable partagé : la proposition IA arrive de façon asynchrone et
    // enrichit le formulaire déjà affiché (BIZ-56).
    const aiState = { suggestion: null };
    renderDimensionsForm(aiState);

    // L'IA propose les notes à partir des inputs de la partie A. Le formulaire
    // est déjà rendu (curseurs à 5, bouton « Calculer le score » présent) : on
    // l'enrichit dès la réponse reçue. En cas d'IA désactivée (503) ou de
    // réponse inexploitable (502), on reste en saisie manuelle.
    api("POST", `/${state.project.id}/dimensions/suggest`)
      .then((suggestion) => {
        if (isStaleRender(token) || !document.getElementById("d-rentabilite")) return;
        aiState.suggestion = suggestion;
        applySuggestion(suggestion);
      })
      .catch(() => {
        if (isStaleRender(token)) return;
        const box = document.getElementById("ai-synthese-box");
        if (box) {
          box.className = "ai-synthese ai-synthese--off";
          box.innerHTML =
            "<strong>IA indisponible</strong>" +
            "<p>Renseignez manuellement chaque dimension (0 à 10).</p>";
        }
      });
  }

  function applySuggestion(suggestion) {
    const justifs = suggestion.justifications || {};
    for (const [key] of DIMENSIONS) {
      const v = Number(suggestion.dimensions[key]);
      const input = document.getElementById(`d-${key}`);
      const output = document.getElementById(`o-${key}`);
      const hint = document.getElementById(`hint-${key}`);
      if (input) {
        input.value = String(v);
        input.dataset.ai = String(v);
      }
      if (output) output.textContent = String(v);
      if (hint) {
        hint.textContent = `IA : ${v}/10${justifs[key] ? ` — ${justifs[key]}` : ""}`;
      }
    }
    const box = document.getElementById("ai-synthese-box");
    if (box) {
      box.className = "ai-synthese";
      box.innerHTML = `<strong>✨ Logique de l'IA</strong><p>${escapeHtml(
        suggestion.synthese || "",
      )}</p>`;
    }
    const wrap = document.getElementById("justif-wrap");
    if (wrap) wrap.hidden = true;
  }

  function renderDimensionsForm(aiState) {
    const sliders = DIMENSIONS.map(
      ([key, label]) => `
        <label class="field">${label} : <output id="o-${key}">5</output> / 10
          <input id="d-${key}" type="range" min="0" max="10" value="5" data-ai=""
                 oninput="document.getElementById('o-${key}').textContent=this.value" />
          <small class="ai-note-hint" id="hint-${key}"></small>
        </label>`,
    ).join("");

    shell(`
      <div class="ai-synthese" id="ai-synthese-box">
        <strong>✨ Évaluation par l'IA</strong>
        <p>⏳ L'IA évalue le projet à partir des informations saisies…</p>
      </div>
      <p class="muted">L'IA propose ces notes ; ajustez-les si nécessaire (avec justification).</p>
      ${sliders}
      <label class="field" id="justif-wrap" hidden="">
        Justification de vos modifications
        <textarea id="f-justif" maxlength="2000"
                  placeholder="Expliquez pourquoi vous modifiez les notes proposées par l'IA."></textarea>
        <small class="field-error" id="err-justif" hidden></small>
      </label>
      <div class="btn-row">
        <button class="btn btn-ghost" id="prev">‹ Précédent</button>
        <button class="btn btn-accent" id="next">Calculer le score ›</button>
      </div>`);

    // Affiche le champ de justification dès qu'une note diffère de la
    // proposition de l'IA (BIZ-56).
    function isModified() {
      if (!aiState.suggestion) return false;
      return DIMENSIONS.some(([key]) => {
        const input = document.getElementById(`d-${key}`);
        return input.dataset.ai !== "" && Number(input.value) !== Number(input.dataset.ai);
      });
    }
    function refreshJustif() {
      const wrap = document.getElementById("justif-wrap");
      if (aiState.suggestion) wrap.hidden = !isModified();
    }
    for (const [key] of DIMENSIONS) {
      document.getElementById(`d-${key}`).addEventListener("input", refreshJustif);
    }

    document.getElementById("prev").onclick = stepFinancials;
    document.getElementById("next").onclick = async () => {
      const payload = {};
      for (const [key] of DIMENSIONS) payload[key] = Number(val(`d-${key}`));

      const justification = val("f-justif").trim();
      const modified = isModified();
      const errors = {};
      if (modified && !justification) {
        errors["justif"] = "Justifiez la modification des notes proposées par l'IA.";
      }
      if (!applyFieldErrors(["justif"], errors)) return;

      if (aiState.suggestion) payload["ai_synthese"] = aiState.suggestion.synthese || null;
      if (justification) payload["justification"] = justification;

      try {
        state.score = await api("PUT", `/${state.project.id}/dimensions`, payload);
        step = 4;
        stepRecap();
      } catch (e) {
        toast(e.message, true);
      }
    };
  }

  function stepRecap() {
    const s = state.score.total;
    shell(`
      <div class="score-hero">
        <div class="gauge" style="background:${scoreColor(s)}">
          <strong>${Math.round(s)}</strong><span>/ 100</span>
        </div>
        <div>
          <h3>${escapeHtml(state.project.nom)}</h3>
          <p class="reco" style="color:${scoreColor(s)}">${recommendation(s)}</p>
          <p class="muted">${escapeHtml(state.project.direction)} · ${state.project.duree_estimee_mois} mois</p>
        </div>
      </div>
      <div class="btn-row">
        <button class="btn btn-ghost" data-project="${state.project.id}" id="see">Voir la fiche</button>
        <button class="btn btn-accent" id="gen">⚙️ Générer le business plan</button>
      </div>`);

    document.getElementById("see").onclick = () =>
      renderDetail(state.project.id);
    document.getElementById("gen").onclick = async () => {
      try {
        await api("POST", `/${state.project.id}/generate`);
        toast("Business plan généré");
        renderDetail(state.project.id);
      } catch (e) {
        toast(e.message, true);
      }
    };
  }

  stepProject();
}

function val(id) {
  return document.getElementById(id).value.trim();
}

// Affiche les messages d'erreur par champ et place le focus sur le premier
// champ invalide. Retourne true si aucune erreur (formulaire valide).
function applyFieldErrors(fields, errors) {
  let firstInvalid = null;
  for (const f of fields) {
    const input = document.getElementById(`f-${f}`);
    const errEl = document.getElementById(`err-${f}`);
    const message = errors[f];
    if (message) {
      if (errEl) {
        errEl.textContent = message;
        errEl.hidden = false;
      }
      if (input) {
        input.setAttribute("aria-invalid", "true");
        input.classList.add("invalid");
      }
      if (!firstInvalid) firstInvalid = input;
    } else {
      if (errEl) {
        errEl.textContent = "";
        errEl.hidden = true;
      }
      if (input) {
        input.removeAttribute("aria-invalid");
        input.classList.remove("invalid");
      }
    }
  }
  if (firstInvalid) {
    firstInvalid.focus();
    return false;
  }
  return true;
}

// -------- Vue : fiche projet --------
async function renderDetail(projectId) {
  const token = beginRender();
  spinner();
  let project, score, bp, financials;
  try {
    project = await api("GET", `/${projectId}`);
  } catch (e) {
    if (isStaleRender(token)) return;
    toast(e.message, true);
    return renderDashboard();
  }
  score = await api("GET", `/${projectId}/score`).catch(() => null);
  bp = await api("GET", `/${projectId}/bp`).catch(() => null);
  financials = await api("GET", `/${projectId}/financials`).catch(() => null);
  // Une autre vue a été demandée pendant les appels API : ne pas l'écraser.
  if (isStaleRender(token)) return;

  let html = `
    <button class="back" data-nav="dashboard">‹ Tableau de bord</button>
    <div class="section-head">
      <div>
        <h2>${escapeHtml(project.nom)}</h2>
        <p class="muted"><span class="tag">${escapeHtml(project.direction)}</span> · ${project.duree_estimee_mois} mois</p>
      </div>
    </div>
    <div class="card"><p>${escapeHtml(project.description)}</p></div>`;

  if (financials) {
    html += `
      <div class="card">
        <h3>Hypothèses financières</h3>
        <div class="grid-2">
          <p class="muted">Investissement initial<br><strong>${euro(financials.investissement_initial)}</strong></p>
          <p class="muted">Revenus annuels<br><strong>${euro(financials.revenus_annuels)}</strong></p>
          <p class="muted">Coûts annuels<br><strong>${euro(financials.couts_annuels)}</strong></p>
          <p class="muted">Délai de rentabilité visé<br><strong>${financials.delai_rentabilite_mois} mois</strong></p>
        </div>
      </div>`;
  }

  if (score) {
    html += scoreCard(score);
  } else {
    html += `<div class="card empty">Aucun score calculé pour ce projet.</div>`;
  }

  if (bp) {
    html += businessPlanCard(bp);
  } else {
    html += `
      <div class="card">
        <h3>Business plan</h3>
        <p class="muted">Aucun business plan généré.</p>
        <div class="btn-row"><button class="btn btn-accent" id="gen">⚙️ Générer le business plan</button></div>
      </div>`;
  }

  view.innerHTML = html;

  const gen = document.getElementById("gen");
  if (gen) {
    gen.onclick = async () => {
      try {
        await api("POST", `/${projectId}/generate`);
        toast("Business plan généré");
        renderDetail(projectId);
      } catch (e) {
        toast(e.message, true);
      }
    };
  }
  wireBpToc();
}

function scoreCard(score) {
  const s = score.total;
  const dims = DIMENSIONS.map(([key, label]) => {
    const d = score.dimensions[key];
    if (!d) return "";
    return `
      <div class="dim">
        <div class="dim-head"><span class="name">${label}</span>
          <span>${d.note}/10 · pondéré ${(d.contribution).toFixed(1)}</span></div>
        <div class="bar"><span style="width:${d.note * 10}%"></span></div>
      </div>`;
  }).join("");
  return `
    <div class="card">
      <div class="score-hero">
        <div class="gauge" style="background:${scoreColor(s)}">
          <strong>${Math.round(s)}</strong><span>/ 100</span>
        </div>
        <div>
          <h3>Score de pertinence</h3>
          <p class="reco" style="color:${scoreColor(s)}">${recommendation(s)}</p>
        </div>
      </div>
      <div class="dims">${dims}</div>
    </div>`;
}

function businessPlanCard(bp) {
  const entries = Object.entries(bp.sections);
  const toc = entries
    .map(
      ([key], i) =>
        `<a href="#sec-${i}" data-sec="sec-${i}">${escapeHtml(prettyKey(key))}</a>`,
    )
    .join("");
  const sections = entries
    .map(
      ([key, content], i) => `
        <div class="bp-section" id="sec-${i}">
          <h3>${escapeHtml(prettyKey(key))}</h3>
          <p>${escapeHtml(content)}</p>
        </div>`,
    )
    .join("");

  let scenarios = "";
  if (bp.scenarios && bp.scenarios.length) {
    const keys = Object.keys(bp.scenarios[0].data);
    scenarios = `
      <table class="scenarios">
        <thead><tr><th>Indicateur</th>${bp.scenarios
          .map((s) => `<th>${escapeHtml(s.type)}</th>`)
          .join("")}</tr></thead>
        <tbody>${keys
          .map(
            (k) =>
              `<tr><td>${escapeHtml(prettyKey(k))}</td>${bp.scenarios
                .map(
                  (s) =>
                    `<td>${new Intl.NumberFormat("fr-FR", {
                      maximumFractionDigits: 1,
                    }).format(s.data[k])}</td>`,
                )
                .join("")}</tr>`,
          )
          .join("")}</tbody>
      </table>`;
  }

  const synth = bp.synthese_codir
    ? `<div class="bp-section"><h3>Synthèse CODIR</h3><p>${escapeHtml(
        bp.synthese_codir,
      )}</p></div>`
    : "";

  return `
    <div class="card">
      <div class="section-head">
        <h3>Business plan <span class="tag bp">${escapeHtml(bp.status)}</span></h3>
        <div class="btn-row" style="margin:0">
          <a class="btn btn-ghost" href="/projects/${bp.project_id}/export?format=md">⬇ Markdown</a>
          <a class="btn btn-ghost" href="/projects/${bp.project_id}/export?format=pdf">⬇ PDF</a>
        </div>
      </div>
      <div class="bp-layout">
        <nav class="bp-toc">${toc}</nav>
        <div>
          ${scenarios}
          ${sections}
          ${synth}
        </div>
      </div>
    </div>`;
}

function prettyKey(key) {
  const s = key.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function wireBpToc() {
  const links = document.querySelectorAll(".bp-toc a");
  links.forEach((a) =>
    a.addEventListener("click", (ev) => {
      ev.preventDefault();
      const target = document.getElementById(a.dataset.sec);
      if (target) target.scrollIntoView({ behavior: "smooth" });
      links.forEach((l) => l.classList.remove("active"));
      a.classList.add("active");
    }),
  );
}

// -------- Routeur minimal --------
document.addEventListener("click", (ev) => {
  const nav = ev.target.closest("[data-nav]");
  if (!nav) return;
  const dest = nav.dataset.nav;
  if (dest === "dashboard") renderDashboard();
  else if (dest === "wizard") renderWizard();
});

renderDashboard();
