import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import Home from "../pages/Home";

describe("Home", () => {
  it("muestra el héroe con el título principal", () => {
    render(<Home />);
    expect(screen.getByText("Color changes everything.")).toBeInTheDocument();
  });
});
