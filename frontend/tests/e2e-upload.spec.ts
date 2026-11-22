import { test, expect } from "@playwright/test";

const PROJECT_ID = "bb8a908f-efee-428f-af0a-c7cd45c864c7";
const ADMIN_EMAIL = "admin@manga.local";
const ADMIN_PASSWORD = "Admin12345678";

test.describe("Flujo E2E: login + subir página sin 413 ni congelado", () => {
  test("login y entrar a /projects/:id/upload sin quedarse en Cargando…", async ({
    page,
  }) => {
    const peticiones: Array<{ url: string; status: number | null; method: string }> = [];
    page.on("request", (req) => {
      peticiones.push({ url: req.url(), status: null, method: req.method() });
    });
    page.on("response", (resp) => {
      const idx = peticiones.findIndex((p) => p.url === resp.url() && p.status === null);
      if (idx >= 0) {
        peticiones[idx].status = resp.status();
      }
    });

    // 1. Ir a login y autenticarse por UI
    await page.goto("/login", { waitUntil: "domcontentloaded" });
    await page.locator('input[id="login-email"]').fill(ADMIN_EMAIL);
    await page.locator('input[id="login-password"]').fill(ADMIN_PASSWORD);
    await page.locator('button[type="submit"]').click();

    // Después del login, debería redirigir a /dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // 2. Navegar al proyecto en etapa upload
    await page.goto(`/projects/${PROJECT_ID}/upload`, {
      waitUntil: "domcontentloaded",
    });

    // 3. Esperar a que desaparezca "Cargando proyecto…" (máx 15s)
    try {
      await expect(
        page.getByText("Cargando proyecto…")
      ).not.toBeVisible({ timeout: 15000 });
    } catch {
      await page.screenshot({
        path: "test-results/e2e-upload-fail.png",
        fullPage: true,
      });
      console.log("=== PETICIONES DE RED ===");
      peticiones.forEach((p) => console.log(`${p.method} ${p.url} -> ${p.status}`));
      const html = await page.content();
      console.log("=== HTML (primeros 3000 chars) ===");
      console.log(html.substring(0, 3000));
      throw new Error(
        `La página sigue en Cargando proyecto… después de 15s.\n` +
          `Peticiones: ${JSON.stringify(peticiones, null, 2)}`
      );
    }

    await page.waitForTimeout(1000);
    await page.screenshot({
      path: "test-results/e2e-upload-diagnostico.png",
      fullPage: true,
    });

    const tieneInput = (await page.locator('input[type="file"]').count()) > 0;
    const tieneCompletada = (await page.getByText("Subida completada").count()) > 0;
    const tieneError = (await page.getByText(/No se pudo cargar el proyecto/).count()) > 0;
    const tieneLoading = (await page.getByText("Cargando proyecto…").count()) > 0;

    console.log("Estado de la página:", {
      tieneInput,
      tieneCompletada,
      tieneError,
      tieneLoading,
      peticiones: peticiones.length,
    });

    if (tieneError) {
      throw new Error("El proyecto no se pudo cargar.");
    }

    if (tieneLoading) {
      throw new Error("La página sigue en Cargando proyecto… después de 16s");
    }

    expect(tieneInput || tieneCompletada).toBe(true);
  });
});
