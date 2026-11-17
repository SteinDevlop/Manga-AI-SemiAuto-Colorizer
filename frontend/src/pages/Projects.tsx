/* Projects — listado de proyectos con portada real, etapa y estado. */
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

const STAGE_ORDER: string[] = ["upload", "analysis", "character", "mask", "approve", "colorize", "export"];

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

const statusConf: Record<string, { className: string; text: string }> = {
  en_progreso: { className: "badge badge-running", text: "En progreso" },
  completado: { className: "badge badge-done", text: "Completado" },
  con_error: { className: "badge badge-failed", text: "Con error" },
  procesando: { className: "badge badge-running", text: "Procesando" },
};

const projectCover = (p: ProjectCard) => {
  if (p.portada) return p.portada;
  return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='400'><rect width='300' height='400' fill='%23efece4'/><rect x='16' y='16' width='268' height='120' fill='%23fff' stroke='%23111' stroke-width='2'/><rect x='16' y='148' width='268' height='236' fill='%23fff' stroke='%23111' stroke-width='2'/></svg>";
};

export default function Projects() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectCard[]>([]);
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  // Filtros
  const [filtroEstado, setFiltroEstado] = useState("");
  const [filtroEtapa, setFiltroEtapa] = useState("");
  const [busqueda, setBusqueda] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoaded(false);
    api.listProjects()
      .then((data) => {
        if (!cancelled) setProjects(data);
      })
      .catch(() => {
        if (!cancelled) setError("No se pudo cargar la lista de proyectos.");
      })
      .finally(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => { cancelled = true; };
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
      navigate(`/projects/${(created as { id: string }).id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error creando proyecto");
    } finally {
      setCreating(false);
    }
  };

  const filtered = projects.filter((p) => {
    const matchEstado = filtroEstado ? p.status === filtroEstado : true;
    const matchEtapa = filtroEtapa ? p.current_stage === filtroEtapa : true;
    const matchBusq = busqueda ? p.nombre.toLowerCase().includes(busqueda.toLowerCase()) : true;
    return matchEstado && matchEtapa && matchBusq;
  });

  const estados = Array.from(new Set(projects.map((p) => p.status))).sort();
  const etapas = Array.from(new Set(projects.map((p) => p.current_stage)))
    .sort((a, b) => STAGE_ORDER.indexOf(a) - STAGE_ORDER.indexOf(b));

  return (
    <section className="screen is-active" id="screen-projects">
      <div className="page-head">
        <div>
          <span className="eyebrow">Projects</span>
          <h1 className="h1">Projects</h1>
          <p style={{ color: "var(--ink-muted)", marginTop: 4 }}>
            Todos tus proyectos de colorización con su portada, etapa y estado.
          </p>
        </div>
        <button type="button" className="btn-vermilion" onClick={handleCreate}>
          + Nuevo proyecto
        </button>
      </div>

      {error && (
        <p style={{ color: "#c0392b", fontSize: 0.85, margin: "8px 0" }}>
          Error: {error}
        </p>
      )}

      {/* Filtros y búsqueda */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginBottom: 20 }}>
        <input
          type="text"
          placeholder="Buscar por nombre…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          style={{ padding: "8px 12px", fontSize: "0.82rem", border: "1px solid var(--border)", background: "var(--surface)", flex: 1, minWidth: 220 }}
        />
        <select
          value={filtroEstado}
          onChange={(e) => setFiltroEstado(e.target.value)}
          style={{ padding: "8px 12px", fontSize: "0.82rem", border: "1px solid var(--border)", background: "var(--surface)" }}
        >
          <option value="">Todos los estados</option>
          {estados.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={filtroEtapa}
          onChange={(e) => setFiltroEtapa(e.target.value)}
          style={{ padding: "8px 12px", fontSize: "0.82rem", border: "1px solid var(--border)", background: "var(--surface)" }}
        >
          <option value="">Todas las etapas</option>
          {etapas.map((s) => (
            <option key={s} value={s}>
              {stageLabel(s)}
            </option>
          ))}
        </select>
      </div>

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
      ) : filtered.length === 0 ? (
        <div className="panel-box" style={{ textAlign: "center", padding: "64px 24px", border: "1px solid var(--border)", borderRadius: 12, background: "var(--surface)" }}>
          <span className="eyebrow">Sin proyectos</span>
          <h2 className="h1" style={{ marginBottom: 12 }}>
            {projects.length === 0 ? "Crea tu primer proyecto" : "No coincide con los filtros"}
          </h2>
          <p style={{ color: "var(--ink-muted)", maxWidth: 440, margin: "0 auto 24px" }}>
            {projects.length === 0
              ? "Una vez creado, importa páginas y comienza el flujo de colorización."
              : "Ajusta los filtros o busca por nombre."}
          </p>
          <button type="button" className="btn-vermilion" onClick={handleCreate}>
            Crear proyecto
          </button>
        </div>
      ) : (
        <div className="grid-3" style={{ marginBottom: 32 }}>
          {filtered.map((p) => (
            <article key={p.id} className="project-card" onClick={() => navigate(`/projects/${p.id}`)} style={{ cursor: "pointer", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden", background: "var(--surface)", transition: "box-shadow .2s" }}>
              <div className="project-thumb" style={{ width: "100%", height: 200, overflow: "hidden", background: "var(--surface)" }}>
                <img src={projectCover(p)} alt={`Portada de ${p.nombre}`} style={{ width: "100%", height: "100%", objectFit: "contain", display: "block" }} />
              </div>
              <div style={{ padding: 14 }}>
                <strong style={{ display: "block", fontSize: 1 }}>{p.nombre}</strong>
                <div style={{ display: "flex", gap: 8, alignItems: "center", fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)", marginTop: 6 }}>
                  <span className={statusConf[p.status]?.className || "badge"} style={{ fontSize: 0.68 }}>{statusConf[p.status]?.text || p.status}</span>
                  <span>{stageLabel(p.current_stage)}</span>
                  <span>{p.progreso}%</span>
                </div>
                {p.descripcion && (
                  <p style={{ fontSize: 0.78, color: "var(--ink-muted)", marginTop: 6, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{p.descripcion}</p>
                )}
                <div style={{ marginTop: 10, fontFamily: "var(--font-mono)", fontSize: 0.7, color: "var(--ink-muted)" }}>
                  Actualizado {new Date(p.updated_at || p.created_at || "").toLocaleDateString()}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
