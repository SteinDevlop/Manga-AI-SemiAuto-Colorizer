import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Home } from "../pages/Home";

describe("Home", () => {
  it("muestra el título y el mensaje de bienvenida", () => {
    render(<Home />);
    expect(screen.getByText("Proyectos")).toBeInTheDocument();
    expect(screen.getByText(/No hay proyectos aún/)).toBeInTheDocument();
  });
});
