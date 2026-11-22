/* Layout de la aplicación Star Colorizing.
 *
 * Shell global: sidebar (sticky) + columna principal. Solo contiene secciones
 * globales (Workspace) y System. El pipeline (Upload → Export) vive dentro de
 * cada proyecto, no fuera de él, por lo que aquí no hay barra de pasos ni
 * sección Pipeline del sidebar.
 */
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const WORKSPACE_ITEMS = [
  { id: "dashboard", label: "Dashboard", path: "/" },
  { id: "projects", label: "Projects", path: "/projects" },
  { id: "results", label: "Results & Exports", path: "/results" },
  { id: "jobs", label: "Colorization Jobs", path: "/jobs" },
  { id: "models", label: "Model Registry", path: "/models" },
  { id: "settings", label: "Settings", path: "/settings" },
];

// System se mantiene sin cambios (sin ítems de pipeline).
const SYSTEM_ITEMS: Array<{ id: string; label: string; path: string }> = [];

export function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();

  const isActive = (path: string) => {
    if (path === "/") {
      return location.pathname === "/";
    }
    return location.pathname === path || location.pathname.startsWith(`${path}/`);
  };

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <button
            className="brand-button"
            aria-label="Ir a Projects"
            onClick={() => navigate("/projects")}
          >
            <span className="brand-seal" aria-hidden="true">
              墨
            </span>
            <div>
              <div className="brand-name">Star Colorizing</div>
              <div className="brand-sub">Studio</div>
            </div>
          </button>
        </div>

        <div className="nav-group-label">Workspace</div>
        {WORKSPACE_ITEMS.map((item) => (
          <button
            key={`workspace-${item.id}`}
            className={`nav-item ${isActive(item.path) ? "is-active" : ""}`}
            data-nav={item.id}
            onClick={() => navigate(item.path)}
          >
            {item.label}
          </button>
        ))}

        <div className="nav-group-label">System</div>
        {SYSTEM_ITEMS.map((item) => (
          <button
            key={`system-${item.id}`}
            className="nav-item"
            data-nav={item.id}
            onClick={() => navigate(item.path)}
          >
            {item.label}
          </button>
        ))}
      </aside>

      {/* Main Column */}
      <div className="main-col">
        {/* Top Bar */}
        <header className="topbar">
          <div className="breadcrumbs">
            <span>Star Colorizing</span>{" "}
            <strong>
              {location.pathname === "/"
                ? "Dashboard"
                : location.pathname.split("/").pop() ?? "Studio"}
            </strong>
          </div>
          <div className="topbar-right" style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ color: "var(--ink-muted)", fontSize: "0.85rem" }}>{user?.email}</span>
            <button className="btn btn-outline btn-sm" onClick={() => { signOut(); navigate("/login", { replace: true }); }}>Cerrar sesión</button>
            <button className="btn btn-vermilion btn-sm" onClick={() => navigate("/projects")}>+ Nuevo proyecto</button>
          </div>
        </header>

        <main className="workspace">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
