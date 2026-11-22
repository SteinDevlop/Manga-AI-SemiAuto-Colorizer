import { test, expect } from "@playwright/test";

const ADMIN_EMAIL = "admin@manga.local";
const ADMIN_PASSWORD = "Admin12345678";

test.describe("Diagnóstico detallado: crear proyecto", () => {
  test("verificar estado de la página al crear proyecto", async ({ page }) => {
    // Login
    await page.goto("/login", { waitUntil: "domcontentloaded" });
    await page.locator('input[id="login-email"]').fill(ADMIN_EMAIL);
    await page.locator('input[id="login-password"]').fill(ADMIN_PASSWORD);
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Ir a Projects
    await page.goto("/projects", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: "test-results/diag2-antes-llenar.png" });

    // Ver qué inputs existen
    const inputs = page.locator("input");
    console.log("Número de inputs:", await inputs.count());

    // Llenar nombre
    await page.locator('input[id="nuevo-proyecto-nombre"]').fill(
      "Proyecto Diag2"
    );
    await page.locator('input[placeholder="Descripción (opcional)"]').fill("Test");
    await page.screenshot({ path: "test-results/diag2-despues-llenar.png" });

    // Ver si el botón está habilitado
    const btn = page.locator('button[type="submit"]');
    console.log("Botón visible:", await btn.isVisible());
    console.log("Botón habilitado:", await btn.isEnabled());
    console.log("Texto del botón:", await btn.textContent());

    // Hacer clic
    await btn.click();
    await page.waitForTimeout(5000);
    await page.screenshot({ path: "test-results/diag2-despues-clic.png" });

    console.log("URL final:", page.url());

    // Verificar si hay mensajes de error
    const textoPagina = await page.textContent("body");
    console.log("¿Contiene 'error'?:", textoPagina.toLowerCase().includes("error"));
    console.log("¿Contiene 'Creando'?:", textoPagina.includes("Creando"));
  });
});
