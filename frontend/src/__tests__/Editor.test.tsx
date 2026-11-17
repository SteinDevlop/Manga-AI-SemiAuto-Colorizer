import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppProvider } from "../context/AppContext";
import Editor from "../pages/Editor";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}));

describe("Editor", () => {
  it("renderiza el editor de personaje sin crash", () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      id: "char-1",
      nombre: "Protagonista",
      atributos: [],
      paletas: [],
    });

    const { container } = render(
      <AppProvider>
        <MemoryRouter initialEntries={["/editor/char-1"]}>
          <Editor />
        </MemoryRouter>
      </AppProvider>
    );

    expect(container).toBeTruthy();
  });
});
