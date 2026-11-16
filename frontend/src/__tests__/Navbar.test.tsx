import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Navbar } from "../components/Navbar";
import { MemoryRouter } from "react-router-dom";

describe("Navbar", () => {
  it("renderiza los enlaces de navegación", () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );
    expect(screen.getByText("Manga Colorizer")).toBeInTheDocument();
    expect(screen.getByText("Proyectos")).toBeInTheDocument();
    expect(screen.getByText("Subir página")).toBeInTheDocument();
    expect(screen.getByText("Historial")).toBeInTheDocument();
  });
});
