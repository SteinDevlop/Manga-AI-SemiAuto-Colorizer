import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppProvider } from "../context/AppContext";
import Projects from "../pages/Projects";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    listProjects: vi.fn(),
    createProject: vi.fn(),
    deleteProject: vi.fn(),
  },
}));

describe("Projects", () => {
  it("muestra lista de proyectos cargados desde la API", async () => {
    vi.mocked(api.listProjects).mockResolvedValueOnce([
      { id: "1", nombre: "Proyecto A", descripcion: "Desc", created_at: "2026-01-01", updated_at: "2026-01-01", tipo: null, portada: null, current_stage: "upload", status: "en_progreso", progreso: 0 },
    ]);

    render(
      <AppProvider>
        <MemoryRouter>
          <Projects />
        </MemoryRouter>
      </AppProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Proyecto A")).toBeInTheDocument();
    });
  });

  it("renderiza estado vacío cuando no hay proyectos", async () => {
    vi.mocked(api.listProjects).mockResolvedValueOnce([]);

    render(
      <AppProvider>
        <MemoryRouter>
          <Projects />
        </MemoryRouter>
      </AppProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Sin proyectos")).toBeInTheDocument();
    });
  });
});
