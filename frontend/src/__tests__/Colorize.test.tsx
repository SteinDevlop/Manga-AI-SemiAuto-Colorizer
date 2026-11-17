import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppProvider } from "../context/AppContext";
import Colorize from "../pages/Colorize";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe("Colorize", () => {
  it("renderiza la etapa de colorización sin crash", () => {
    vi.mocked(api.get).mockResolvedValueOnce([]);

    const { container } = render(
      <AppProvider>
        <MemoryRouter>
          <Colorize />
        </MemoryRouter>
      </AppProvider>
    );

    expect(container).toBeTruthy();
  });
});
