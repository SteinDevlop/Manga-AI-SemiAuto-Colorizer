import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import Colorize from "../pages/Colorize";

describe("Colorize", () => {
  it("shows colorization center with start button", () => {
    render(<Colorize />);
    expect(screen.getByText("Start Colorization Job")).toBeInTheDocument();
  });
});
