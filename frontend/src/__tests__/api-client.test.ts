import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { api } from "../api/client";

const originalFetch = global.fetch;

beforeEach(() => {
  global.fetch = vi.fn();
});

afterEach(() => {
  global.fetch = originalFetch;
  sessionStorage.clear();
  vi.restoreAllMocks();
});

describe("api client", () => {
  it("get hace fetch con la URL correcta y devuelve JSON", async () => {
    const data = [{ id: "1", nombre: "Proyecto 1" }];
    vi.mocked(global.fetch).mockResolvedValueOnce(
      new Response(JSON.stringify(data), { status: 200 })
    );

    const result = await api.get<typeof data>("/projects");

    // Un GET no debe enviar Content-Type (evita preflight CORS innecesario).
    const [url, init] = vi.mocked(global.fetch).mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/v1/projects");
    expect((init.headers as Record<string, string>)["Content-Type"]).toBeUndefined();
    expect(result).toEqual(data);
  });

  it("post envía body como JSON", async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ id: "2" }), { status: 201 })
    );

    await api.post("/projects", { nombre: "Nuevo" });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/projects"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ nombre: "Nuevo" }),
        headers: expect.objectContaining({ "Content-Type": "application/json" }),
      })
    );
  });

  it("adjunta el Bearer token a las peticiones autenticadas", async () => {
    sessionStorage.setItem("sumi_access_token", "test-token");
    vi.mocked(global.fetch).mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    await api.get("/projects");
    const [, init] = vi.mocked(global.fetch).mock.calls[0] as [string, RequestInit];
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer test-token");
  });

  it("lanza error cuando la respuesta no es OK", async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({ code: "not_found", message: "No encontrado" }),
        { status: 404 }
      )
    );

    await expect(api.get("/projects/999")).rejects.toThrow("No encontrado");
  });
});
