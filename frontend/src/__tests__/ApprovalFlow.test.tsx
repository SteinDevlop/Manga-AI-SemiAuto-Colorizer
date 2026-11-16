import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { Approve } from "../pages/Approve";
import { MemoryRouter } from "react-router-dom";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe("Approve", () => {
  it("muestra análisis y permite aprobar", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      id: "analysis-1",
      estado: "REVIEW_REQUIRED",
      characters: [],
    });
    vi.mocked(api.post).mockResolvedValueOnce({ estado: "APPROVED" });

    render(
      <MemoryRouter initialEntries={"/approve/analysis-1"}>
        <Approve />
      </MemoryRouter>
    );

    expect(screen.getByText("Cargando análisis...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Aprobar análisis")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/aprobado/i)).toBeInTheDocument();
    });
  });
});
