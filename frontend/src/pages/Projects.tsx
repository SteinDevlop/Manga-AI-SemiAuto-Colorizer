/* SUMI Projects — project list connected to the API. */
import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../api/client";
import { useApp } from "../context/AppContext";

const badgeConfig: Record<string, { className: string; text: string }> = {
  review: { className: "badge badge-review", text: "Review Required" },
  done: { className: "badge badge-done", text: "Completed" },
  running: { className: "badge badge-running", text: "Analyzing" },
};

export default function Projects() {
  const [projects, setProjects] = useState<Array<{ id: string; nombre: string; descripcion: string | null; created_at: string | null }>>([]);
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const navigate = useNavigate();
  const { setProjectId, setAnalysisId, setJobId } = useApp();

  useEffect(() => {
    api.listProjects()
      .then((data: any[]) => setProjects(data))
      .catch(() => setProjects([]))
      .finally(() => setLoaded(true));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setCreating(true);
    try {
      const created = await api.createProject(nombre.trim(), descripcion.trim() || undefined);
      setProjects([created, ...projects]);
      setNombre("");
      setDescripcion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error creando proyecto");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteProject = async (projectId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setError(null);
    if (!window.confirm("¿Estás seguro de que quieres eliminar este proyecto? Esta acción no se puede deshacer.")) {
      return;
    }
    try {
      await api.deleteProject(projectId);
      setProjects(projects.filter(p => p.id !== projectId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error eliminando proyecto");
    }
  };

  return (
    <section className="screen is-active" id="screen-project">
      <div className="page-head">
        <div>
          <span className="eyebrow">02 // Project Workspace</span>
          <h1 className="h1">Projects</h1>
          <p style={{ color: "var(--ink-muted)", marginTop: 4 }}>
            Manage your manga colorization projects.
          </p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => navigate("/upload")}>
          + Import Pages
        </button>
      </div>

      {error && (
        <p style={{ color: "#c0392b", fontSize: 0.85, margin: "8px 0" }}>
          Error: {error}
        </p>
      )}

      <form onSubmit={handleCreate} style={{ marginBottom: 28, display: "flex", gap: 10, flexWrap: "wrap" }}>
        <input
          type="text"
          placeholder="Nombre del proyecto"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          required
          style={{ padding: "9px 18px", fontSize: "0.82rem", border: "1px solid var(--border)", background: "var(--surface)", flex: 1, minWidth: 200 }}
        />
        <input
          type="text"
          placeholder="Descripción (opcional)"
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          style={{ padding: "9px 18px", fontSize: "0.82rem", border: "1px solid var(--border)", background: "var(--surface)", flex: 1, minWidth: 200 }}
        />
        <button type="submit" className="btn btn-vermilion" disabled={creating}>
          {creating ? "Creando…" : "Crear proyecto"}
        </button>
      </form>

      {!loaded ? (
        <p style={{ color: "var(--ink-muted)" }}>Cargando proyectos…</p>
      ) : projects.length === 0 ? (
        <div className="panel-box" style={{ textAlign: "center", padding: "64px 24px" }}>
          <span className="eyebrow">No Projects Yet</span>
          <h2 className="h1" style={{ marginBottom: 12 }}>
            Create your first project above.
          </h2>
          <p style={{ color: "var(--ink-muted)", maxWidth: 440, margin: "0 auto 24px" }}>
            Once created, import pages and begin the colorization workflow.
          </p>
        </div>
      ) : (
        <div className="grid-3" id="pagesGrid">
          {projects.map((p) => (
            <article key={p.id} className="project-card" onClick={() => {
              setProjectId(p.id);
              setAnalysisId(null);
              setJobId(null);
              navigate(`/upload?project=${p.id}`);
            }}>
              <div className="project-thumb">
                <svg viewBox="0 0 300 400" preserveAspectRatio="xMidYMid slice">
                  <rect width="300" height="400" fill="#fff" />
                  <rect x="16" y="16" width="268" height="120" fill="#efece4" stroke="#111" strokeWidth="2" />
                  <rect x="16" y="148" width="268" height="236" fill="#efece4" stroke="#111" strokeWidth="2" />
                  <path d="M0 150 L70 95 L140 130 L230 80 L320 135 L320 200 L0 200 Z" fill="#111111" />
                </svg>
                <span className="exhibit-pill">
                  <span className="on-ink">Original Ink</span>
                  <span className="on-color">SUMI Color</span>
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong>{p.nombre}</strong>
                <span className={badgeConfig.review.className}>{badgeConfig.review.text}</span>
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 0.7, color: "var(--ink-muted)" }}>
                {p.descripcion || "Sin descripción"}
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button type="button" className="btn btn-outline btn-sm" onClick={(ev) => {
                  ev.stopPropagation();
                  setProjectId(p.id);
                  setAnalysisId(null);
                  setJobId(null);
                  navigate(`/projects/${p.id}`);
                }}>
                  Abrir proyecto →
                </button>
                <button type="button" className="btn btn-outline btn-sm" style={{ color: "#c0392b", borderColor: "#c0392b" }} onClick={(ev) => {
                  handleDeleteProject(p.id, ev);
                }}>
                  Delete
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
