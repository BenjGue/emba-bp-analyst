// @ts-check
const { test, expect } = require("@playwright/test");

/**
 * Tests exploratoires UI (cas négatifs + limites) contre l'app déployée.
 *
 * Objectif : débusquer des bugs front-end au-delà du happy-path
 * (validation formulaire, navigation wizard, suppression, filtre dashboard,
 * gestion d'erreur IA, échappement XSS, erreurs console).
 *
 * Chaque test nettoie les projets qu'il crée via l'API REST.
 */

/** Supprime un projet par son id via l'API. */
async function deleteProject(request, baseURL, id) {
  if (id == null) return;
  await request.delete(`${baseURL}/projects/${id}`).catch(() => {});
}

/** Récupère l'id du dernier projet créé portant ce nom (via l'API liste). */
async function findProjectIdByName(request, baseURL, nom) {
  const res = await request.get(`${baseURL}/projects`);
  if (!res.ok()) return null;
  const list = await res.json();
  const match = list.filter((p) => p.nom === nom);
  return match.length ? match[match.length - 1].id : null;
}

test.describe("Exploratoire UI BizPlan-IA", () => {
  let consoleErrors = [];

  test.beforeEach(({ page }) => {
    consoleErrors = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("pageerror", (err) => consoleErrors.push(String(err)));
  });

  test("dashboard se charge sans erreur console", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("#view")).toBeVisible();
    // Le bouton de création doit être atteignable.
    await expect(page.locator('[data-nav="wizard"]').first()).toBeVisible();
    expect(consoleErrors, `Erreurs console: ${consoleErrors.join(" | ")}`).toEqual([]);
  });

  test("validation : soumission formulaire vide affiche des erreurs", async ({ page }) => {
    await page.goto("/");
    await page.locator('[data-nav="wizard"]').first().click();
    await expect(page.locator("#f-nom")).toBeVisible();
    // On vide les champs et on tente de continuer.
    await page.locator("#f-nom").fill("");
    await page.locator("#f-desc").fill("");
    await page.locator("#next").click();
    // Un message d'erreur de champ doit s'afficher (et rester à l'étape 1).
    await expect(page.locator("#err-nom")).toBeVisible();
    await expect(page.locator("#f-desc")).toBeVisible();
    expect(consoleErrors, `Erreurs console: ${consoleErrors.join(" | ")}`).toEqual([]);
  });

  test("validation : message d'erreur disparaît après correction", async ({ page }) => {
    await page.goto("/");
    await page.locator('[data-nav="wizard"]').first().click();
    await page.locator("#f-nom").fill("");
    await page.locator("#next").click();
    await expect(page.locator("#err-nom")).toBeVisible();
    // Correction
    await page.locator("#f-nom").fill("Projet corrigé");
    await page.locator("#f-desc").fill("Description suffisante pour valider le formulaire.");
    await page.locator("#next").click();
    // On doit passer à l'étape finances.
    await expect(page.locator("#f-inv")).toBeVisible();
  });

  test("wizard : le bouton Précédent conserve les saisies", async ({ page, request, baseURL }) => {
    const nom = `E2E Back ${Date.now()}`;
    await page.goto("/");
    await page.locator('[data-nav="wizard"]').first().click();
    await page.locator("#f-nom").fill(nom);
    await page.locator("#f-desc").fill("Description de test navigation arrière du wizard.");
    await page.locator("#f-duree").fill("24");
    await page.locator("#next").click();
    // Étape finances -> retour
    await expect(page.locator("#f-inv")).toBeVisible();
    await page.locator("#prev").click();
    // Le nom doit être conservé.
    await expect(page.locator("#f-nom")).toHaveValue(nom);
    // cleanup : aucun projet créé tant qu'on n'a pas validé l'étape 1 -> rien à supprimer
    const id = await findProjectIdByName(request, baseURL, nom);
    await deleteProject(request, baseURL, id);
  });

  test("assistance IA : reformater sans description affiche un toast d'erreur", async ({ page }) => {
    await page.goto("/");
    await page.locator('[data-nav="wizard"]').first().click();
    // Le champ description est vide -> le bouton de reformatage refuse et avertit.
    await page.locator("#ai-reformat").click();
    await expect(page.locator("#toast")).toBeVisible();
    await expect(page.locator("#toast")).toHaveClass(/error/);
  });

  test("assistance IA : échec backend géré proprement (pas de crash)", async ({ page }) => {
    await page.goto("/");
    await page.locator('[data-nav="wizard"]').first().click();
    await page.locator("#f-desc").fill("casiers connectés bureau de poste, livraison J+1");
    await page.locator("#ai-reformat").click();
    // L'IA est désactivée côté serveur -> toast d'erreur attendu, l'app reste utilisable.
    await expect(page.locator("#toast")).toBeVisible({ timeout: 20000 });
    await expect(page.locator("#f-nom")).toBeVisible();
  });

  test("XSS : un nom contenant du HTML est échappé dans le dashboard", async ({
    page,
    request,
    baseURL,
  }) => {
    const marker = `xss-${Date.now()}`;
    const nom = `<img src=x onerror="window.__xss=1">${marker}`;
    const res = await request.post(`${baseURL}/projects`, {
      data: {
        nom,
        description: "Projet test échappement XSS.",
        direction: "Numérique",
        duree_estimee_mois: 12,
      },
    });
    const id = (await res.json()).id;
    try {
      await page.goto("/");
      // Le texte brut (avec balise) doit apparaître comme texte, pas exécuté.
      await expect(page.getByText(marker, { exact: false })).toBeVisible();
      const flag = await page.evaluate(() => window.__xss);
      expect(flag, "Le HTML injecté ne doit pas s'exécuter").toBeFalsy();
    } finally {
      await deleteProject(request, baseURL, id);
    }
  });

  test("dashboard : filtre par direction", async ({ page, request, baseURL }) => {
    const nom = `E2E Filtre ${Date.now()}`;
    const res = await request.post(`${baseURL}/projects`, {
      data: {
        nom,
        description: "Projet test filtre direction.",
        direction: "Geopost",
        duree_estimee_mois: 12,
      },
    });
    const id = (await res.json()).id;
    try {
      await page.goto("/");
      await expect(page.locator("#filter-direction")).toBeVisible();
      await page.locator("#filter-direction").selectOption("Geopost");
      await expect(page.getByText(nom)).toBeVisible();
      // Un filtre sur une autre direction doit masquer le projet.
      await page.locator("#filter-direction").selectOption("La Banque Postale");
      await expect(page.getByText(nom)).toHaveCount(0);
    } finally {
      await deleteProject(request, baseURL, id);
    }
  });

  test("suppression : un projet supprimé disparaît du dashboard", async ({
    page,
    request,
    baseURL,
  }) => {
    const nom = `E2E Suppr ${Date.now()}`;
    const res = await request.post(`${baseURL}/projects`, {
      data: {
        nom,
        description: "Projet test suppression depuis le dashboard.",
        direction: "Numérique",
        duree_estimee_mois: 12,
      },
    });
    const id = (await res.json()).id;
    let deleted = false;
    try {
      await page.goto("/");
      const row = page.locator(`[data-project="${id}"]`);
      await expect(row).toBeVisible();
      // Accepter la confirmation native.
      page.on("dialog", (d) => d.accept());
      await row.locator(".btn-delete").click();
      await expect(page.locator(`[data-project="${id}"]`)).toHaveCount(0);
      deleted = true;
    } finally {
      if (!deleted) await deleteProject(request, baseURL, id);
    }
  });
});
