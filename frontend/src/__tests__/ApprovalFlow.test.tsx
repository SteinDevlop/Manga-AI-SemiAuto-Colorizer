import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Review from "../pages/Review";

describe("Review", () => {
  it("shows review page with approval button", () => {
    render(
      <MemoryRouter initialEntries={["/approve/analysis-1"]}>
        <Review />
      </MemoryRouter>
    );
    expect(screen.getByText("Approve Color Configuration")).toBeInTheDocument();
  });
});
