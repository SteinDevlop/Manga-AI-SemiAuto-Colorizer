import { test, expect } from "@playwright/test";

const ADMIN_EMAIL = "admin@manga.local";
const ADMIN_PASSWORD = "Admin12345678";

test.describe("Diagnóstico: crear proyecto", () => {
  test("verificar qué pasa al crear proyecto", async ({ page }) => {
    const errores: Array<{ url: string; status: number }> = [];
    page.on("response", (resp) => {
      if (resp.status() >= 400) {
        errores.push({ url: resp.url(), status: resp.status() });
      }
    });

    // Login
    await page.goto("/login", { waitUntil: "domcontentloaded" });
    await page.locator('input[id="login-email"]').fill(ADMIN_EMAIL);
    await page.locator('input[id="login-password"]').fill(ADMIN_PASSWORD);
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Ir a Projects
    await page.goto("/projects", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: "test-results/diag-proyectos-antes.png" });

    // Llenar formulario
    await page.locator('input[id="nuevo-proyecto-nombre"]').fill(
      "Proyecto Diagnóstico"
    );
    await page.locator('input[placeholder="Descripción (opcional)"]').fill("Test");
    await page.screenshot({ path: "test-results/diag-formulario-llenado.png" });

    // Hacer clic en Crear proyecto
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(5000);
    await page.screenshot({ path: "test-results/diag-despues-clic.png" });

    console.log("URL después del clic:", page.url());
    console.log("Errores de red:", JSON.stringify(errores, null, 2));

    // Verificar si hay mensaje de error
    const msgError = page.getByText(/error|Error|ya existe|Ya existe/i);
    console.log("¿Hay mensaje de error?:", (await msgError.count()) > 0);

    if (page.url().includes("/projects/")) {
      console.log("✅ Redirigió a proyecto");
    } else {
      console.log("❌ No redirigió, sigue en:", page.url());
    }
  });
});
