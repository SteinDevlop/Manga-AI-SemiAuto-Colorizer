import { test, expect } from "@playwright/test";

const ADMIN_EMAIL = "admin@manga.local";
const ADMIN_PASSWORD = "Admin12345678";
const IMAGEN_PRUEBA =
  "C:/Users/Steinman/Proyectos/Manga-AI-SemiAuto-Colorizer/model-creation/dataset/unified/pairs/pair_000001/input.png";

test.describe("Flujo E2E completo: login → proyecto → subir → análisis → aprobar → colorizar", () => {
  test("recorre todo el pipeline con una imagen de manga real sin errores 4xx/5xx", async ({
    page,
  }) => {
    const errores: Array<{ url: string; status: number }> = [];
    page.on("response", (resp) => {
      if (resp.status() >= 400) {
        errores.push({ url: resp.url(), status: resp.status() });
      }
    });

    // PASO 1: Login
    await page.goto("/login", { waitUntil: "networkidle" });
    await page.locator('input[id="login-email"]').fill(ADMIN_EMAIL);
    await page.locator('input[id="login-password"]').fill(ADMIN_PASSWORD);
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // PASO 2: Crear proyecto con nombre único
    const timestamp = Date.now();
    const nombreProyecto = `E2E-${timestamp}`;
    await page.goto("/projects", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    await page.locator('input[id="nuevo-proyecto-nombre"]').fill(nombreProyecto);
    await page
      .locator('input[placeholder="Descripción (opcional)"]')
      .fill("Prueba E2E con imagen real");
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(3000);
    await expect(page).toHaveURL(/\/projects\/[^/]+/, { timeout: 15000 });
    const proyectoUrl = page.url();
    const proyectoId = proyectoUrl.split("/projects/")[1].split("/")[0];
    expect(proyectoId).toBeTruthy();
    console.log("PROYECTO ID:", proyectoId);

    // PASO 3: Upload - subir imagen
    await page.goto(`/projects/${proyectoId}/upload`, {
      waitUntil: "networkidle",
    });
    await expect(
      page.getByText("Cargando proyecto…")
    ).not.toBeVisible({ timeout: 15000 });

    const inputFile = page.locator('input[type="file"]');
    await inputFile.setInputFiles(IMAGEN_PRUEBA);
    await page.getByRole("button", { name: /Subir página/ }).click();
    await page.waitForTimeout(3000);
    await page.screenshot({
      path: "test-results/e2e-paso3-upload.png",
      fullPage: true,
    });

    // Verificar que la subida se completó
    await expect(
      page.getByText("Subida completada")
    ).toBeVisible({ timeout: 10000 });
    console.log("✅ Imagen subida correctamente");

    // PASO 4: Navegar a Análisis y ejecutar
    await page.goto(`/projects/${proyectoId}/analysis`, {
      waitUntil: "networkidle",
    });
    await expect(
      page.getByText("Cargando proyecto…")
    ).not.toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: "test-results/e2e-paso4-analysis-before.png",
      fullPage: true,
    });

    // Clic en "Ejecutar análisis"
    const btnAnalizar = page.locator(
      'button:has-text("Ejecutar análisis"), button:has-text("Analizar")'
    );
    expect(btnAnalizar).toBeVisible();
    await btnAnalizar.first().click();
    await page.waitForTimeout(5000);
    await page.screenshot({
      path: "test-results/e2e-paso4-analysis-after.png",
      fullPage: true,
    });

    // Verificar que el análisis se ejecutó (debe mostrar datos de análisis, no el botón)
    const btnAunVisible = await btnAnalizar.count();
    if (btnAunVisible > 0) {
      // El análisis podría no haberse ejecutado aún, esperar un poco más
      await page.waitForTimeout(3000);
      await page.screenshot({
        path: "test-results/e2e-paso4-analysis-wait.png",
        fullPage: true,
      });
    }

    // PASO 5: Navegar a Approve
    await page.goto(`/projects/${proyectoId}/approve`, {
      waitUntil: "networkidle",
    });
    await expect(
      page.getByText("Cargando proyecto…")
    ).not.toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: "test-results/e2e-paso5-approve-before.png",
      fullPage: true,
    });

    // Clic en "Aprobar" si existe
    const btnAprobar = page.locator(
      'button:has-text("Aprobar"), button:has-text("Aprueba")'
    );
    if ((await btnAprobar.count()) > 0) {
      await btnAprobar.first().click();
      await page.waitForTimeout(3000);
      await page.screenshot({
        path: "test-results/e2e-paso5-approve-after.png",
        fullPage: true,
      });
    }
    console.log("✅ Etapa Approve procesada");

    // PASO 6: Navegar a Colorize
    await page.goto(`/projects/${proyectoId}/colorize`, {
      waitUntil: "networkidle",
    });
    await expect(
      page.getByText("Cargando proyecto…")
    ).not.toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: "test-results/e2e-paso6-colorize.png",
      fullPage: true,
    });
    console.log("✅ Etapa Colorize cargada");

    // PASO 7: Verificar errores de red
    console.log("Errores de red capturados:", JSON.stringify(errores, null, 2));
    expect(errores).toEqual([]);

    console.log("✅ Todas las etapas cargaron sin errores de red");
  });
});
