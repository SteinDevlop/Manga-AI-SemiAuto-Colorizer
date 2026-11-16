/** Barra de navegación principal de la aplicación. */

import { Link } from "react-router-dom";

export function Navbar(): JSX.Element {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">Manga Colorizer</Link>
      </div>
      <div className="navbar-links">
        <Link to="/">Proyectos</Link>
        <Link to="/upload">Subir página</Link>
        <Link to="/history">Historial</Link>
      </div>
    </nav>
  );
}
