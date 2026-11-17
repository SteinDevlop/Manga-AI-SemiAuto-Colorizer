/* Layout de proyecto: stepper interno del pipeline y guarda de ruta.
 *
 * El pipeline (Upload → Analysis → Character → Mask → Approve → Colorize →
 * Export) vive dentro de cada proyecto. Esta se renderiza bajo
 * /projects/:id/:stage dentro del Layout global.
 */
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { StagePlaceholder } from "./StagePlaceholder";

export const STAGE_ORDER: string[] = [
  "upload",
  "analysis",
  "character",
  "mask",
  "approve",
  "colorize",
  "export",
];

const STAGE_DESCRIPTION: Record<string, string> = {
  upload: "Sube la imagen original del manga. Tras completarse, no se puede deshacer.",
  analysis: "Análisis de paneles, personajes y máscaras de la página.",
  character: "Selecciona y gestiona los personajes detectados.",
  mask: "Edita las máscaras de segmentación de cada personaje.",
  approve: "Revisa y aprueba el análisis antes de colorizar.",
  colorize: "Lanza el trabajo de colorización y haz el seguimiento.",
  export: "Descarga el resultado final del proyecto.",
};

const STAGE_LABEL: Record<string, string> = {
  upload: "Subida",
  analysis: "Análisis",
  character: "Personajes",
  mask: "Máscara",
  approve: "Aprobación",
  colorize: "Colorizar",
  export: "Exportar",
};

const stageLabel = (s: string) => STAGE_LABEL[s] || s;

const statusConf: Record<string, { className: string; text: string }> = {
  en_progreso: { className: "badge badge-running", text: "En progreso" },
  completado: { className: "badge badge-done", text: "Completado" },
  con_error: { className: "badge badge-failed", text: "Con error" },
  procesando: { className: "badge badge-running", text: "Procesando" },
};

const projectCover = (p: string | null) => {
  if (p) return p;
  return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='260'><rect width='200' height='260' fill='%23efece4'/><rect x='12' y='12' width='176' height='104' fill='%23fff' stroke='%23111' stroke-width='2'/><rect x='12' y='128' width='176' height='120' fill='%23fff' stroke='%23111' stroke-width='2'/></svg>";
};

type ProjectDetail = {
  id: string;
  nombre: string;
  descripcion: string | null;
  tipo: string | null;
  portada: string | null;
  current_stage: string;
  status: string;
  stage_progress: string[];
  progreso: number;
  pages: Array<{
    page_id: string;
    nombre_archivo_original: string;
    ruta_archivo: string;
    estado: string;
    analysis_id: string | null;
    analysis_estado: string | null;
  }>;
};

export function ProjectLayout() {
  const { id: projectId, stage: stageParam } = useParams<{ id: string; stage: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [redirectTo, setRedirectTo] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api.getProject(projectId)
      .then((p) => {
        if (cancelled) return;
        setProject(p);
        // Redirigir /projects/:id (sin stage) a la etapa actual.
        if (!stageParam) {
          setRedirectTo(`/projects/${projectId}/${p.current_stage}`);
          return;
        }
        // Guarda de ruta para /projects/:id/:stage.
        const currentIdx = STAGE_ORDER.indexOf(p.current_stage);
        const targetIdx = STAGE_ORDER.indexOf(stageParam);
        let allowed = false;
        if (targetIdx === -1) {
          allowed = false;
        } else if (stageParam === p.current_stage) {
          allowed = true;
        } else if (stageParam === "upload" && p.stage_progress.includes("upload")) {
          // Upload no es retornable una vez completada.
          allowed = false;
        } else if (p.stage_progress.includes(stageParam) && targetIdx < currentIdx) {
          // Retroceso a etapa completada y previa.
          allowed = true;
        }
        if (!allowed) {
          setRedirectTo(`/projects/${projectId}/${p.current_stage}`);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("No se pudo cargar el proyecto.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [projectId, stageParam]);

  if (redirectTo) {
    navigate(redirectTo, { replace: true });
    return null;
  }

  if (loading) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "var(--ink-muted)" }}>
        Cargando proyecto…
      </div>
    );
  }

  if (error || !project) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "#c0392b" }}>
        {error || "Proyecto no encontrado."}
        <br />
        <button
          type="button"
          className="btn btn-outline"
          onClick={() => navigate("/projects")}
        >
          Volver a Projects
        </button>
      </div>
    );
  }

  const currentIdx = STAGE_ORDER.indexOf(project.current_stage);
  const progress = project.stage_progress ?? [];
  const isCompleted = (s: string) => progress.includes(s);
  const isPending = (s: string) => !isCompleted(s) && STAGE_ORDER.indexOf(s) > currentIdx;

  const handleComplete = () => {
    api.transitionStage(projectId, "complete", project.current_stage)
      .then((updated) => {
        setProject((prev) => (prev ? { ...prev, ...updated } : prev));
      })
      .catch(() => {
        setError("No se pudo avanzar de etapa.");
      });
  };

  const handleRegress = (to: string) => {
    api.transitionStage(projectId, "regress", to)
      .then((updated) => {
        setProject((prev) => (prev ? { ...prev, ...updated } : prev));
        navigate(`/projects/${projectId}/${to}`);
      })
      .catch(() => {
        setError("No se pudo retroceder de etapa.");
      });
  };

  const isClickable = (s: string) => {
    if (s === project.current_stage) return false;
    if (s === "upload" && isCompleted(s)) return false; // no retornable
    return isCompleted(s) && STAGE_ORDER.indexOf(s) < currentIdx;
  };

  return (
    <div className="project-layout" style={{ display: "flex", flexDirection: "column", gap: 16, padding: 24 }}>
      {/* Encabezado del proyecto */}
      <header style={{ display: "flex", gap: 16, alignItems: "center", borderBottom: "1px solid var(--border)", paddingBottom: 12 }}>
        <img src={projectCover(project.portada)} alt="Portada" style={{ width: 72, height: 96, objectFit: "contain", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 6 }} />
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)", marginBottom: 4 }}>
            <span className={statusConf[project.status]?.className || "badge"} style={{ fontSize: 0.68 }}>{statusConf[project.status]?.text || project.status}</span>
            <span>{project.progreso}%</span>
          </div>
          <h1 style={{ margin: 0, fontSize: 1.25 }}>{project.nombre}</h1>
          <p style={{ margin: 4, color: "var(--ink-muted)", fontSize: 0.9 }}>
            Etapa actual: <strong>{stageLabel(project.current_stage)}</strong> — {STAGE_DESCRIPTION[project.current_stage]}
          </p>
        </div>
        <button
          type="button"
          className="btn btn-vermilion"
          onClick={handleComplete}
          disabled={project.status === "completado"}
        >
          {project.status === "completado" ? "Completado" : `Marcar {stageLabel(project.current_stage)} como completada`}
        </button>
      </header>

      {/* Stepper interno */}
      <section style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 16, background: "var(--surface)" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 0.75, color: "var(--ink-muted)", marginBottom: 10 }}>
          Flujo del proyecto
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {STAGE_ORDER.map((s, i) => {
            const completed = isCompleted(s);
            const active = s === project.current_stage;
            const clickable = isClickable(s);
            const cls = completed
              ? "step step-done"
              : active
              ? "step step-active"
              : "step step-pending";
            return (
              <button
                key={s}
                type="button"
                className={cls}
                disabled={!clickable && !active}
                onClick={() => clickable && handleRegress(s)}
                title={clickable ? `Retroceder a ${stageLabel(s)}` : active ? "Etapa actual" : "Etapa pendiente"}
              >
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.65 }}>{i + 1}</span>
                <span style={{ marginLeft: 6, fontSize: 0.8, fontWeight: active || completed ? 600 : 400 }}>{stageLabel(s)}</span>
              </button>
            );
          })}
        </div>
      </section>

      {/* Contenido de la etapa */}
      <main style={{ flex: 1 }}>
        <StagePlaceholder
          stage={stageParam ?? project.current_stage}
          isCurrent={!(stageParam && stageParam !== project.current_stage)}
          onComplete={handleComplete}
        />
      </main>
    </div>
  );
}
