/** Diseño base: navbar + área de contenido. */

import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";

export function Layout(): JSX.Element {
  return (
    <div className="layout">
      <Navbar />
      <main className="layout-content">
        <Outlet />
      </main>
    </div>
  );
}
