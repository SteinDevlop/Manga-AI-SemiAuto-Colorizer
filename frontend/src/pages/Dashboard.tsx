/* Dashboard de Star Colorizing — datos reales del endpoint de métricas. */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

type ProjectCard = {
  id: string;
  nombre: string;
  descripcion: string | null;
  created_at: string | null;
  updated_at: string | null;
  tipo: string | null;
  portada: string | null;
  current_stage: string;
  status: string;
  progreso: number;
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectCard[]>([]);
  const [metrics, setMetrics] = useState<{
    total_proyectos: number;
    proyectos_por_estado: Record<string, number>;
    proyectos_por_etapa: Record<string, number>;
    jobs: { total: number; activos: number; completados: number; fallidos: number };
    ultimos_proyectos: Array<{
      id: string;
      nombre: string;
      current_stage: string;
      status: string;
      portada: string | null;
      updated_at: string | null;
    }>;
  } | null>(null);
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoaded(false);
    Promise.all([
      api.listProjects(),
      api.getMetrics(),
    ])
      .then(([list, metr]) => {
        if (!cancelled) {
          setProjects(list);
          setMetrics(metr);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("No se pudo cargar el panel. Intenta de nuevo más tarde.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setCreating(true);
    try {
      const created = await api.createProject(nombre.trim(), descripcion.trim() || undefined);
      setProjects([created as unknown as ProjectCard, ...projects]);
      setNombre("");
      setDescripcion("");
      navigate(`/projects/${created.id}`);
    } catch (err) {
      const code = (err as { cause?: { code?: string } })?.cause?.code;
      setError(
        code === "conflict"
          ? "Ya existe un proyecto con ese nombre. Elige otro nombre."
          : err instanceof Error ? err.message : "Error creando proyecto",
      );
    } finally {
      setCreating(false);
    }
  };

  const stageLabel = (s: string) => {
    const labels: Record<string, string> = {
      upload: "Subida",
      analysis: "Análisis",
      character: "Personajes",
      mask: "Máscara",
      approve: "Aprobación",
      colorize: "Colorización",
      export: "Exportar",
    };
    return labels[s] || s;
  };

  const statusBadge = (status: string) => {
    const conf: Record<string, string> = {
      en_progreso: "badge badge-running",
      completado: "badge badge-done",
      con_error: "badge badge-failed",
      procesando: "badge badge-running",
    };
    return conf[status] || "badge";
  };

  const projectCover = (p: ProjectCard) => {
    if (p.portada) return p.portada;
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='400'><rect width='300' height='400' fill='%23efece4'/><rect x='16' y='16' width='268' height='120' fill='%23fff' stroke='%23111' stroke-width='2'/><rect x='16' y='148' width='268' height='236' fill='%23fff' stroke='%23111' stroke-width='2'/></svg>";
  };

  return (
    <section className="screen is-active" id="screen-dashboard">
      <div className="page-head">
        <div>
          <span className="eyebrow">Dashboard</span>
          <h1 className="h1">Panel de control</h1>
          <p style={{ color: "var(--ink-muted)", marginTop: 6 }}>
            Resumen del estado de tus proyectos y trabajos de colorización.
          </p>
        </div>
        <button type="button" className="btn-vermilion" onClick={() => navigate("/projects")}>
          + Nuevo proyecto
        </button>
      </div>

      {error && (
        <p style={{ color: "#c0392b", fontSize: "0.85rem", margin: "8px 0" }}>
          Error: {error}
        </p>
      )}

      {!loaded ? (
        <p style={{ color: "var(--ink-muted)" }}>Cargando panel…</p>
      ) : (
        <>
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

          <span className="eyebrow" style={{ marginBottom: 12 }}>
            Métricas
          </span>
          <div className="summary-strip" style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 32 }}>
            <div className="summary-cell" style={{ flex: 1, minWidth: 160, border: "1px solid var(--border)", padding: 16, borderRadius: 8, background: "var(--surface)" }}>
              <span className="eyebrow" style={{ display: "block", marginBottom: 6, fontSize: "0.75rem" }}>Total de proyectos</span>
              <div className="summary-val" style={{ fontSize: "1.5rem", fontWeight: 700 }}>{metrics?.total_proyectos ?? 0}</div>
            </div>
            <div className="summary-cell" style={{ flex: 1, minWidth: 160, border: "1px solid var(--border)", padding: 16, borderRadius: 8, background: "var(--surface)" }}>
              <span className="eyebrow" style={{ display: "block", marginBottom: 6, fontSize: "0.75rem" }}>Jobs activos</span>
              <div className="summary-val" style={{ fontSize: "1.5rem", fontWeight: 700 }}>{metrics?.jobs.activos ?? 0}</div>
            </div>
            <div className="summary-cell" style={{ flex: 1, minWidth: 160, border: "1px solid var(--border)", padding: 16, borderRadius: 8, background: "var(--surface)" }}>
              <span className="eyebrow" style={{ display: "block", marginBottom: 6, fontSize: "0.75rem" }}>Jobs completados</span>
              <div className="summary-val" style={{ fontSize: "1.5rem", fontWeight: 700 }}>{metrics?.jobs.completados ?? 0}</div>
            </div>
            <div className="summary-cell" style={{ flex: 1, minWidth: 160, border: "1px solid var(--border)", padding: 16, borderRadius: 8, background: "var(--surface)" }}>
              <span className="eyebrow" style={{ display: "block", marginBottom: 6, fontSize: "0.75rem" }}>Jobs fallidos</span>
              <div className="summary-val" style={{ fontSize: "1.5rem", fontWeight: 700 }}>{metrics?.jobs.fallidos ?? 0}</div>
            </div>
          </div>

          <span className="eyebrow" style={{ marginBottom: 12 }}>
            Proyectos por etapa
          </span>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 32 }}>
            {Object.entries(metrics?.proyectos_por_etapa ?? {}).map(([stage, count]) => (
              <div key={stage} style={{ border: "1px solid var(--border)", padding: "10px 16px", borderRadius: 8, background: "var(--surface)", display: "flex", justifyContent: "space-between", alignItems: "center", minWidth: 140 }}>
                <span>{stageLabel(stage)}</span>
                <span style={{ fontWeight: 700 }}>{count}</span>
              </div>
            ))}
            {!metrics || Object.keys(metrics.proyectos_por_etapa).length === 0 && metrics.total_proyectos === 0 && (
              <div style={{ border: "1px solid var(--border)", padding: "10px 16px", borderRadius: 8, background: "var(--surface)", color: "var(--ink-muted)", fontSize: "0.85rem" }}>
                Sin proyectos aún.
              </div>
            )}
          </div>

          <span className="eyebrow" style={{ marginBottom: 12 }}>
            Proyectos recientes
          </span>
          {projects.length === 0 ? (
            <div className="panel-box" style={{ textAlign: "center", padding: "64px 24px", border: "1px solid var(--border)", borderRadius: 12, background: "var(--surface)" }}>
              <span className="eyebrow">Sin proyectos aún</span>
              <h2 className="h1" style={{ marginBottom: 12 }}>Crea tu primer proyecto</h2>
              <p style={{ color: "var(--ink-muted)", maxWidth: 440, margin: "0 auto 24px" }}>
                Importa páginas de manga en blanco y negro, valida identidades y máscaras, y genera láminas colorizadas.
              </p>
              <button type="button" className="btn-vermilion" onClick={() => navigate("/projects")}>
                Crear tu primer proyecto
              </button>
            </div>
          ) : (
            <div className="grid-3" style={{ marginBottom: 32 }}>
              {projects.map((p) => (
                <article key={p.id} className="project-card" onClick={() => navigate(`/projects/${p.id}`)} style={{ cursor: "pointer" }}>
                  <div className="project-thumb" style={{ position: "relative", width: "100%", height: 200, overflow: "hidden", borderRadius: 8, border: "1px solid var(--border)", background: "var(--surface)" }}>
                    <img src={projectCover(p)} alt={`Portada de ${p.nombre}`} style={{ width: "100%", height: "100%", objectFit: "contain", background: "var(--surface)" }} />
                    <span className="exhibit-pill" style={{ position: "absolute", bottom: 8, left: 8 }}>
                      <span className="on-ink">Original Ink</span>
                      <span className="on-color">Color</span>
                    </span>
                  </div>
                  <div style={{ marginTop: 10 }}>
                    <strong style={{ display: "block" }}>{p.nombre}</strong>
                    <div style={{ display: "flex", gap: 10, alignItems: "center", fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--ink-muted)" }}>
                      <span className={statusBadge(p.status)} style={{ fontSize: "0.7rem" }}>{p.status}</span>
                      <span>{stageLabel(p.current_stage)}</span>
                      <span>{p.progreso}%</span>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
