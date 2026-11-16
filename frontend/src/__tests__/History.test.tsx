import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { History } from "../pages/History";
import { MemoryRouter } from "react-router-dom";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn(),
  },
}));

describe("History", () => {
  it("muestra lista de trabajos y enlace de descarga", async () => {
    vi.mocked(api.get).mockResolvedValueOnce([
      {
        id: "job-1",
        analysis_id: "analysis-1",
        estado: "completed",
        progreso: 100,
        ruta_resultado: "/data/results/job-1.png",
      },
    ]);

    render(
      <MemoryRouter>
        <History />
      </MemoryRouter>
    );

    expect(screen.getByText("Cargando historial...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("job-1")).toBeInTheDocument();
      expect(screen.getByText("100%")).toBeInTheDocument();
      expect(screen.getByText("Descargar")).toBeInTheDocument();
    });
  });
});
