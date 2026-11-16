import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import Analysis from "../pages/Analysis";
import { MemoryRouter } from "react-router-dom";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn(),
  },
}));

describe("Analysis", () => {
  it("muestra análisis con paneles y personajes", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      id: "analysis-1",
      page_id: "page-1",
      estado: "analysis_completed",
      panels: [
        { id: "panel-1", numero_orden: 1, x: 0, y: 0, ancho: 100, alto: 100, confianza_deteccion: 0.9 },
      ],
      characters: [
        { id: "char-1", nombre: "Protagonista", confianza_identidad: 0.95 },
      ],
      appearances: [],
      masks: [],
    });

    render(
      <MemoryRouter initialEntries={["/analysis/analysis-1"]}>
        <Analysis />
      </MemoryRouter>
    );

        expect(screen.getByText("Detected Identities")).toBeInTheDocument();

    await waitFor(() => {
          expect(screen.getByText("Detected Identities")).toBeInTheDocument();
      expect(screen.getByText("98%")).toBeInTheDocument();
    });
  });
});
