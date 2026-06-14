// @ts-check
const { test, expect } = require("@playwright/test");

/**
 * Parcours critique de bout en bout (BIZ-39).
 *
 * Couvre la chaîne de valeur complète de BizPlan-IA :
 *   1. création d'un projet via le wizard ;
 *   2. saisie des hypothèses financières (+ présence de l'import Excel) ;
 *   3. notation des dimensions stratégiques et calcul du score ;
 *   4. génération du business plan ;
 *   5. export du business plan (Markdown / PDF).
 */
test.describe("Parcours critique BizPlan-IA", () => {
  test("création projet → finances → score → génération → export", async ({
    page,
  }) => {
    const nomProjet = `E2E Smoke ${Date.now()}`;

    // 1. Accueil puis ouverture du wizard.
    await page.goto("/");
    await page.locator('[data-nav="wizard"]').first().click();

    // 2. Étape projet.
    await expect(page.locator("#f-nom")).toBeVisible();
    await page.locator("#f-nom").fill(nomProjet);
    await page
      .locator("#f-desc")
      .fill(
        "Projet de test automatisé end-to-end validant le parcours complet " +
          "de création de business plan.",
      );
    await page.locator("#f-duree").fill("12");
    await page.locator("#next").click();

    // 3. Étape finances : présence de l'import Excel (BIZ-36) + valeurs par défaut.
    await expect(page.locator("#f-inv")).toBeVisible();
    await expect(page.locator("#xlsx-import")).toBeVisible();
    await page.locator("#f-inv").fill("100000");
    await page.locator("#f-rev").fill("80000");
    await page.locator("#f-cout").fill("30000");
    await page.locator("#f-delai").fill("36");
    await page.locator("#next").click();

    // 4. Étape dimensions stratégiques : on garde les curseurs par défaut.
    await expect(
      page.getByRole("button", { name: /Calculer le score/ }),
    ).toBeVisible();
    await page.locator("#next").click();

    // 5. Récapitulatif : le score sur 100 est affiché.
    await expect(page.locator(".gauge")).toBeVisible();
    await expect(page.getByText("/ 100")).toBeVisible();

    // 6. Génération du business plan.
    await page.locator("#gen").click();
    await expect(page.getByText("Business plan généré")).toBeVisible();

    // 7. La fiche projet affiche le business plan et ses liens d'export.
    await expect(
      page.getByRole("heading", { name: nomProjet }),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: /Markdown/ }),
    ).toBeVisible();

    const pdfLink = page.getByRole("link", { name: /PDF/ });
    await expect(pdfLink).toBeVisible();
    const href = await pdfLink.getAttribute("href");
    expect(href).toContain("/export?format=pdf");
  });
});
