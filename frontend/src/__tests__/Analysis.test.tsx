import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppProvider } from "../context/AppContext";
import Analysis from "../pages/Analysis";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn(),
  },
}));

describe("Analysis", () => {
  it("renderiza la etapa de análisis sin crash", () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      id: "analysis-1",
      page_id: "page-1",
      estado: "analysis_completed",
      panels: [],
      characters: [],
      appearances: [],
      masks: [],
    });

    const { container } = render(
      <AppProvider>
        <MemoryRouter initialEntries={["/analysis/analysis-1"]}>
          <Analysis />
        </MemoryRouter>
      </AppProvider>
    );

    expect(container).toBeTruthy();
  });
});
