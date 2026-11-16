/* SUMI Layout — app shell: sidebar (sticky) + main col, topbar, pipeline stepper. */

import { Outlet, useLocation } from "react-router-dom";

const NAV_ITEMS = [
  { id: "dashboard", label: "01 / Dashboard", path: "/" },
  { id: "projects", label: "02 / Projects", path: "/projects" },
  { id: "analysis", label: "04 / Analysis Studio", path: "/analysis/:analysisId" },
  { id: "characters", label: "05 / Character & Color", path: "/editor/:characterId" },
  { id: "masks", label: "06 / Mask Editor", path: "/editor/:characterId" },
  { id: "review", label: "07 / Review & Approval", path: "/approve/:analysisId" },
  { id: "colorize", label: "08 / Colorize Center", path: "/colorize/:analysisId" },
  { id: "results", label: "09 / Results & Export", path: "/history" },
  { id: "jobs", label: "Colorization Jobs", path: "/history" },
  { id: "models", label: "10 / Model Registry", path: "/history" },
  { id: "settings", label: "11 / Settings", path: "/history" },
];

const PIPE_STEPS = [
  { id: "projects", label: "1. Upload", done: true },
  { id: "analysis", label: "2. Analysis", done: false },
  { id: "characters", label: "3. Characters", done: false },
  { id: "masks", label: "4. Masks", done: false },
  { id: "review", label: "5. Approve", done: false },
  { id: "colorize", label: "6. Colorize", done: false, disabled: true },
  { id: "results", label: "7. Export", done: false, disabled: true },
];

export function Layout() {
  const location = useLocation();

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-seal" aria-hidden="true">
            墨
          </span>
          <div>
            <div className="brand-name">SUMI</div>
            <div className="brand-sub">STUDIO v1.0</div>
          </div>
        </div>

        <div className="nav-group-label">Workspace</div>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${location.pathname.startsWith(item.path.replace("/:analysisId", "").replace("/:characterId", "")) || item.id === "dashboard" && location.pathname === "/" ? "is-active" : ""}`}
            data-nav={item.id}
          >
            {item.label}
          </button>
        ))}

        <div className="nav-group-label">Page Pipeline</div>
        {PIPE_STEPS.map((step) => (
          <button
            key={step.id}
            className={`nav-item ${step.done ? "is-active" : ""} ${step.disabled ? "" : ""}`}
            disabled={step.disabled}
            data-nav={step.id}
          >
            {step.label}
          </button>
        ))}

        <div className="nav-group-label">System</div>
        {NAV_ITEMS.slice(8).map((item) => (
          <button key={item.id} className="nav-item" data-nav={item.id}>
            {item.label}
          </button>
        ))}
      </aside>

      {/* Main Column */}
      <div className="main-col">
        {/* Top Bar */}
        <header className="topbar">
          <div className="breadcrumbs">
            <span>SUMI Studio</span> /{" "}
            <strong>
              {location.pathname === "/" ? "Dashboard" : location.pathname.split("/").pop() ?? "Studio"}
            </strong>
          </div>
          <div className="topbar-right">
            <span className="badge badge-review">Review Required</span>
            <button className="btn btn-outline btn-sm">Toggle Empty State</button>
            <button className="btn btn-vermilion btn-sm">+ New Project</button>
          </div>
        </header>

        {/* Pipeline Stepper */}
        <nav className="pipeline-bar" aria-label="Colorization Pipeline">
          {PIPE_STEPS.map((step, i) => (
            <>
              <button
                className={`pipe-step ${step.done ? "is-done" : ""} ${step.disabled ? "" : ""}`}
                disabled={step.disabled}
                data-nav={step.id}
              >
                {step.label}
              </button>
              {i < PIPE_STEPS.length - 1 && <span className="pipe-sep">→</span>}
            </>
          ))}
        </nav>

        <main className="workspace">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
