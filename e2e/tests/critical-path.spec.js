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

    // 1bis. Première action du wizard : choix du mode de saisie (BIZ-60).
    // On choisit l'import Excel pour valider la présence de l'affordance.
    await expect(page.locator("#choice-manual")).toBeVisible();
    await expect(page.locator("#choice-import")).toBeVisible();
    await page.locator("#choice-import").click();

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

    // 8. Retour au tableau de bord : la ligne du projet expose aussi un
    //    telechargement PDF direct, sans ouvrir la fiche projet (BIZ-97).
    await page.locator('[data-nav="dashboard"]').first().click();
    const row = page.locator(`.project-row`, { hasText: nomProjet });
    await expect(row).toBeVisible();
    const rowPdf = row.locator(".row-pdf");
    await expect(rowPdf).toBeVisible();
    expect(await rowPdf.getAttribute("href")).toContain(
      "/export?format=pdf",
    );
  });

  test("accueil : page d'accueil par défaut puis accès au tableau de bord et au wizard", async ({
    page,
  }) => {
    // Au chargement, l'application affiche la page d'accueil (BIZ-98) et non
    // le tableau de bord : le hero et ses deux accès sont visibles.
    await page.goto("/");
    await expect(page.locator(".hero")).toBeVisible();
    await expect(
      page.locator('.hero-actions [data-nav="wizard"]'),
    ).toBeVisible();
    await expect(
      page.locator('.hero-actions [data-nav="dashboard"]'),
    ).toBeVisible();

    // Le lien « Tableau de bord » mène bien au tableau de bord.
    await page.locator('.app-nav [data-nav="dashboard"]').click();
    await expect(
      page.getByRole("heading", { name: "Tableau de bord" }),
    ).toBeVisible();

    // Retour à l'accueil via la marque, puis ouverture du wizard.
    await page.locator('[data-nav="home"]').first().click();
    await expect(page.locator(".hero")).toBeVisible();
    await page.locator('.hero-actions [data-nav="wizard"]').click();
    await expect(page.locator("#choice-manual")).toBeVisible();
  });

  test("choix du mode : saisie manuelle masque l'import, import l'affiche", async ({
    page,
  }) => {
    // Vérifie que le choix import/manuel est bien la première action du
    // wizard et qu'il conditionne l'affichage du bloc d'import Excel (BIZ-60).
    await page.goto("/");
    await page.locator('[data-nav="wizard"]').first().click();

    // Mode « Saisie manuelle » : pas de bloc d'import à l'étape Finances.
    await page.locator("#choice-manual").click();
    await expect(page.locator("#f-nom")).toBeVisible();
    await page.locator("#f-nom").fill(`E2E Manuel ${Date.now()}`);
    await page
      .locator("#f-desc")
      .fill("Projet de test vérifiant le mode de saisie manuelle.");
    await page.locator("#f-duree").fill("12");
    await page.locator("#next").click();
    await expect(page.locator("#f-inv")).toBeVisible();
    await expect(page.locator("#xlsx-import")).toHaveCount(0);

    // Retour à l'écran de choix puis bascule en mode « Import Excel ».
    await page.locator("#prev").click();
    await expect(page.locator("#back-choice")).toBeVisible();
    await page.locator("#back-choice").click();
    await page.locator("#choice-import").click();
    await page.locator("#next").click();
    await expect(page.locator("#xlsx-import")).toBeVisible();
  });
});
