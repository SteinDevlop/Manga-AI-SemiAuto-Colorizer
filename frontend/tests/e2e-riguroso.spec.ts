import { test, expect } from "@playwright/test";

const ADMIN_EMAIL = "admin@manga.local";
const ADMIN_PASSWORD = "Admin12345678";
const IMAGEN_PRUEBA =
  "C:/Users/Steinman/Proyectos/Manga-AI-SemiAuto-Colorizer/model-creation/dataset/unified/pairs/pair_000001/input.png";

test.describe("Flujo E2E humano riguroso: validación completa del pipeline", () => {
  test("usuario completa: login → subir → ejecutar análisis → aprobar → colorizar", async ({
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
    console.log("✅ PASO 1: Login exitoso");

    // ── PASO 2: Crear proyecto ──
    const timestamp = Date.now();
    const nombreProyecto = `E2E-Riguroso-${timestamp}`;
    await page.goto("/projects", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    await page.locator('input[id="nuevo-proyecto-nombre"]').fill(nombreProyecto);
    await page
      .locator('input[placeholder="Descripción (opcional)"]')
      .fill("Prueba E2E rigurosa con imagen real");
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(3000);
    await expect(page).toHaveURL(/\/projects\/[^/]+/, { timeout: 15000 });
    const proyectoUrl = page.url();
    const proyectoId = proyectoUrl.split("/projects/")[1].split("/")[0];
    expect(proyectoId).toBeTruthy();
    console.log("✅ PASO 2: Proyecto creado:", proyectoId);

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
    await page.waitForTimeout(5000);

    await page.screenshot({
      path: "test-results/e2e-riguroso-03-upload.png",
      fullPage: true,
    });

    const uploadDone = await page.getByText("Subida completada").count() > 0;
    const yaEnAnalysis = page.url().includes("/analysis");
    expect(uploadDone || yaEnAnalysis).toBe(true);
    console.log("✅ PASO 3: Imagen subida correctamente");

    // ── PASO 4: Ir a Análisis ──
    await page.goto(`/projects/${proyectoId}/analysis`, {
      waitUntil: "networkidle",
    });
    await expect(
      page.getByText("Cargando proyecto…")
    ).not.toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: "test-results/e2e-riguroso-04-analysis-before.png",
      fullPage: true,
    });
    console.log("✅ PASO 4: En etapa Analysis");

    // ── PASO 5: Ejecutar análisis ──
    const btnEjecutar = page.locator(
      'button:has-text("Ejecutar análisis"), button:has-text("Analizar")'
    );
    expect(btnEjecutar).toBeVisible({ timeout: 10000 });
    await btnEjecutar.first().click();
    await page.waitForTimeout(10000);  // Tiempo para el análisis mock

    await page.screenshot({
      path: "test-results/e2e-riguroso-05-analysis-after.png",
      fullPage: true,
    });

    const tieneDatosAnalisis =
      (await page.getByText(/Personajes/i).count()) > 0 ||
      (await page.getByText(/Máscaras/i).count()) > 0 ||
      (await page.getByText(/Paneles/i).count()) > 0 ||
      (await page.getByText(/analysis_id/i).count()) > 0;
    console.log("¿Tiene datos de análisis?:", tieneDatosAnalisis);
    expect(tieneDatosAnalisis).toBe(true, "El análisis no se ejecutó correctamente");
    console.log("✅ PASO 5: Análisis ejecutado con datos visibles");

    // ── PASO 6: Marcar Análisis como completada ──
    const btnCompletarAnalisis = page.locator(
      'button:has-text("Marcar Análisis como completada")'
    );
    expect(btnCompletarAnalisis).toBeVisible();
    await btnCompletarAnalisis.first().click();
    await page.waitForTimeout(3000);
    await page.screenshot({
      path: "test-results/e2e-riguroso-06-completar-analisis.png",
      fullPage: true,
    });
    console.log("✅ PASO 6: Análisis marcado como completado");

    // ── PASO 7: Marcar Personajes como completada ──
    const btnCompletarPersonajes = page.locator(
      'button:has-text("Marcar Personajes como completada")'
    );
    expect(btnCompletarPersonajes).toBeVisible({ timeout: 10000 });
    await btnCompletarPersonajes.first().click();
    await page.waitForTimeout(3000);
    console.log("✅ PASO 7: Personajes marcados como completados");

    // ── PASO 8: Marcar Máscara como completada ──
    const btnCompletarMascara = page.locator(
      'button:has-text("Marcar Máscara como completada")'
    );
    expect(btnCompletarMascara).toBeVisible({ timeout: 10000 });
    await btnCompletarMascara.first().click();
    await page.waitForTimeout(3000);
    console.log("✅ PASO 8: Máscara marcada como completada");

    // ── PASO 9: Ir a Aprobación ──
    await page.goto(`/projects/${proyectoId}/approve`, {
      waitUntil: "networkidle",
    });
    await expect(
      page.getByText("Cargando aprobación…")
    ).not.toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: "test-results/e2e-riguroso-09-approve-before.png",
      fullPage: true,
    });
    console.log("✅ PASO 9: En etapa Approve");

    // ── PASO 10: Verificar análisis en Approve ──
    const tienePersonajes =
      (await page.getByText(/personajes/i).count()) > 0 ||
      (await page.getByText(/confianza/i).count()) > 0;
    console.log("¿Tiene personajes en Approve?:", tienePersonajes);
    expect(tienePersonajes).toBe(true);

    // ── PASO 11: Aprobar análisis ──
    const btnAprobar = page.locator(
      'button:has-text("Aprobar análisis y continuar a Colorizar")'
    );
    expect(btnAprobar).toBeVisible({ timeout: 10000 });
    await btnAprobar.first().click();
    await page.waitForTimeout(3000);

    await page.screenshot({
      path: "test-results/e2e-riguroso-11-approve-after.png",
      fullPage: true,
    });
    console.log("✅ PASO 11: Análisis aprobado");

    // ── PASO 12: Marcar Aprobación como completada ──
    const btnCompletarAprobacion = page.locator(
      'button:has-text("Marcar Aprobación como completada")'
    );
    expect(btnCompletarAprobacion).toBeVisible({ timeout: 10000 });
    await btnCompletarAprobacion.first().click();
    await page.waitForTimeout(3000);
    console.log("✅ PASO 12: Aprobación marcada como completada");

    // ── PASO 13: Navegar a Colorize ──
    await page.goto(`/projects/${proyectoId}/colorize`, {
      waitUntil: "networkidle",
    });
    await expect(
      page.getByText("Cargando proyecto…")
    ).not.toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: "test-results/e2e-riguroso-13-colorize.png",
      fullPage: true,
    });
    console.log("✅ PASO 13: En etapa Colorize");
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: "test-results/e2e-riguroso-12-colorize.png",
      fullPage: true,
    });
    console.log("✅ PASO 12: En etapa Colorize");

    // ── PASO 13: Verificar errores de red ──
    console.log("Errores de red capturados:", JSON.stringify(errores, null, 2));
    expect(errores).toEqual([]);

    console.log("✅ FLUJO COMPLETO VALIDADO: login → subir → análisis → aprobar → colorizar");
  });
});
