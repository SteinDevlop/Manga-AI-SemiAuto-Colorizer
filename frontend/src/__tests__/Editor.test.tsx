import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import Editor from "../pages/Editor";
import { MemoryRouter } from "react-router-dom";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}));

describe("Editor", () => {
  it("muestra atributos del personaje con valores sugeridos", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      id: "char-1",
      nombre: "Protagonista",
      atributos: [
        {
          id: "attr-1",
          nombre_atributo: "cabello",
          valor_sugerido: "negro",
          confianza_sugerencia: 0.8,
          esta_aprobado: false,
        },
      ],
      paletas: [],
    });

    render(
      <MemoryRouter initialEntries={["/editor/char-1"]}>
        <Editor />
      </MemoryRouter>
    );

    expect(screen.getByText("Loading character...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("cabello")).toBeInTheDocument();
      expect(screen.getByText("negro")).toBeInTheDocument();
      expect(screen.getByText("80%")).toBeInTheDocument();
    });
  });
});
