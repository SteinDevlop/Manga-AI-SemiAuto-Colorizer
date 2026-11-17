import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppProvider } from "../context/AppContext";
import History from "../pages/History";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn(),
    listColorizations: vi.fn(),
  },
}));

describe("History", () => {
  it("renderiza la página de historial/resultados sin crash", () => {
    vi.mocked(api.listColorizations).mockResolvedValueOnce([]);

    const { container } = render(
      <AppProvider>
        <MemoryRouter>
          <History />
        </MemoryRouter>
      </AppProvider>
    );

    expect(container).toBeTruthy();
  });
});
