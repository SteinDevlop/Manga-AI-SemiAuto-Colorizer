import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import History from "../pages/History";

describe("Results", () => {
  it("shows results page with export button", () => {
    render(<History />);
    expect(screen.getByText("Download Colorized Image")).toBeInTheDocument();
  });
});
