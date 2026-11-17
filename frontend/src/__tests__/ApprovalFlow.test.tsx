import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppProvider } from "../context/AppContext";
import Review from "../pages/Review";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe("Review", () => {
  it("renderiza la página de aprobación sin crash", () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      id: "analysis-1",
      page_id: "page-1",
      estado: "APPROVED",
      characters: [],
      masks: [],
      confianza_global: 0.9,
    });

    const { container } = render(
      <AppProvider>
        <MemoryRouter initialEntries={["/approve/analysis-1"]}>
          <Review />
        </MemoryRouter>
      </AppProvider>
    );

    expect(container).toBeTruthy();
  });
});
