import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { Colorize } from "../pages/Colorize";
import { MemoryRouter } from "react-router-dom";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe("Colorize", () => {
  it("muestra estado pendiente antes de iniciar", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      id: "analysis-1",
      estado: "APPROVED",
    });
    vi.mocked(api.post).mockResolvedValueOnce({
      id: "job-1",
      estado: "pending",
      progreso: 0,
    });

    render(
      <MemoryRouter initialEntries={"/colorize/analysis-1"}>
        <Colorize />
      </MemoryRouter>
    );

    expect(screen.getByText("Iniciar colorización")).toBeInTheDocument();
  });
});
