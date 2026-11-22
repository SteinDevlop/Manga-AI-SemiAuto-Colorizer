import { test, expect } from "@playwright/test";

const ADMIN_EMAIL = "admin@manga.local";
const ADMIN_PASSWORD = "Admin12345678";
const IMAGEN_PRUEBA =
  "C:/Users/Steinman/Proyectos/Manga-AI-SemiAuto-Colorizer/model-creation/dataset/unified/pairs/pair_000001/input.png";

test.describe("Flujo E2E humano: login → subir → ejecutar análisis → aprobar → colorizar", () => {
  test("usuario completa todo el pipeline verificando cada paso en pantalla", async ({
    page,
  }) => {
    const errores: Array<{ url: string; status: number }> = [];
    page.on("response", (resp) => {
      if (resp.status() >= 400) {
        errores.push({ url: resp.url(), status: resp.status() });
      }
    });

    // ── PASO 1: Login ──
    await page.goto("/login", { waitUntil: "networkidle" });
    await page.locator('input[id="login-email"]').fill(ADMIN_EMAIL);
    await page.locator('input[id="login-password"]').fill(ADMIN_PASSWORD);
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // ── PASO 2: Crear proyecto ──
    const timestamp = Date.now();
    const nombreProyecto = `E2E-Humano-${timestamp}`;
    await page.goto("/projects", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    await page.locator('input[id="nuevo-proyecto-nombre"]').fill(nombreProyecto);
    await page
      .locator('input[placeholder="Descripción (opcional)"]')
      .fill("Prueba E2E humana con imagen real");
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(3000);
    await expect(page).toHaveURL(/\/projects\/[^/]+/, { timeout: 15000 });
    const proyectoUrl = page.url();
    const proyectoId = proyectoUrl.split("/projects/")[1].split("/")[0];
    expect(proyectoId).toBeTruthy();
    console.log("PROYECTO ID:", proyectoId);

    // ── PASO 3: Subir imagen ──
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
      path: "test-results/e2e-humano-03-upload.png",
      fullPage: true,
    });

    // Verificar "Subida completada"
    await expect(
      page.getByText("Subida completada")
    ).toBeVisible({ timeout: 10000 });
    console.log("✅ PASO 3: Imagen subida correctamente");

    // ── PASO 4: Ir a Análisis (botón, no URL directa) ──
    await page.getByRole("button", { name: /Ir a Análisis/ }).click();
    await expect(page).toHaveURL(/\/analysis/, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: "test-results/e2e-humano-04-analysis-before-execute.png",
      fullPage: true,
    });
    console.log("✅ PASO 4: Navegó a etapa Analysis");

    // ── PASO 5: Ejecutar análisis ──
    const btnEjecutar = page.locator(
      'button:has-text("Ejecutar análisis"), button:has-text("Analizar")'
    );
    expect(btnEjecutar).toBeVisible();
    await btnEjecutar.first().click();
    await page.waitForTimeout(8000);  // Dar tiempo al análisis mock

    await page.screenshot({
      path: "test-results/e2e-humano-05-analysis-after-execute.png",
      fullPage: true,
    });

    // Verificar que apareció el análisis (deberían verse personajes, máscaras, etc.)
    const tieneDatosAnalisis =
      (await page.getByText(/Personajes/i).count()) > 0 ||
      (await page.getByText(/Máscaras/i).count()) > 0 ||
      (await page.getByText(/Paneles/i).count()) > 0 ||
      (await page.getByText(/analysis_id/i).count()) > 0;
    console.log("¿Tiene datos de análisis?:", tieneDatosAnalisis);
    expect(tieneDatosAnalisis).toBe(true);
    console.log("✅ PASO 5: Análisis ejecutado con datos visibles");

    // ── PASO 6: Ir a Aprobación (botón, no URL directa) ──
    await page.getByRole("button", { name: /Ir a Aprobación/ }).click();
    await expect(page).toHaveURL(/\/approve/, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: "test-results/e2e-humano-06-approve-before.png",
      fullPage: true,
    });
    console.log("✅ PASO 6: Navegó a etapa Approve");

    // ── PASO 7: Verificar que el análisis se ve en Approve ──
    const tienePersonajesEnApprove =
      (await page.getByText(/personajes/i).count()) > 0 ||
      (await page.getByText(/confianza/i).count()) > 0;
    console.log("¿Tiene personajes en Approve?:", tienePersonajesEnApprove);
    expect(tienePersonajesEnApprove).toBe(true);

    // ── PASO 8: Aprobar análisis ──
    const btnAprobar = page.locator(
      'button:has-text("Aprobar análisis y continuar a Colorizar")'
    );
    expect(btnAprobar).toBeVisible();
    await btnAprobar.first().click();
    await page.waitForTimeout(3000);

    await page.screenshot({
      path: "test-results/e2e-humano-08-approve-after.png",
      fullPage: true,
    });
    console.log("✅ PASO 8: Análisis aprobado");

    // ── PASO 9: Verificar que navegó a Colorize ──
    await expect(page).toHaveURL(/\/colorize/, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: "test-results/e2e-humano-09-colorize.png",
      fullPage: true,
    });
    console.log("✅ PASO 9: En etapa Colorize");

    // ── PASO 10: Verificar errores de red ──
    console.log("Errores de red capturados:", JSON.stringify(errores, null, 2));
    expect(errores).toEqual([]);

    console.log("✅ FLUJO COMPLETO VALIDADO: login → subir → análisis → aprobar → colorizar");
  });
});
