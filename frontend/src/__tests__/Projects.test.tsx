import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import Projects from "../pages/Projects";
import { MemoryRouter } from "react-router-dom";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe("Projects", () => {
  it("muestra lista de proyectos cargados desde la API", async () => {
    vi.mocked(api.get).mockResolvedValueOnce([
      { id: "1", nombre: "Proyecto A", descripcion: "Desc", created_at: "2026-01-01", updated_at: "2026-01-01" },
    ]);

    render(
      <MemoryRouter>
        <Projects />
      </MemoryRouter>
    );

    expect(screen.getByText("Loading projects...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Proyecto A")).toBeInTheDocument();
      expect(screen.getByText("Desc")).toBeInTheDocument();
    });
  });
});
