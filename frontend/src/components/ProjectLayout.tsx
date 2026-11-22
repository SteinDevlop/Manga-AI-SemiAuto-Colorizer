/* Layout de proyecto: stepper interno del pipeline y guarda de ruta.
 *
 * El pipeline (Upload → Analysis → Character → Mask → Approve → Colorize →
 * Export) vive dentro de cada proyecto. Esta se renderiza bajo
 * /projects/:id/:stage dentro del Layout global.
 */
import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, API_BASE } from "../api/client";
import { StagePlaceholder } from "./StagePlaceholder";
import { Upload } from "../pages/Upload";
import { AnalysisStage } from "../pages/stages/AnalysisStage";
import { ApproveStage } from "../pages/stages/ApproveStage";
import { ColorizeStage } from "../pages/stages/ColorizeStage";
import { ExportStage } from "../pages/stages/ExportStage";
import { CharacterStage } from "../pages/stages/CharacterStage";
import { MaskStage } from "../pages/stages/MaskStage";

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
  if (p) {
    const url = p.startsWith("/files/") ? API_BASE.replace(/\/api\/v1\/?$/, "") + p : p;
    return url;
  }
  return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='260'><rect width='200' height='260' fill='%23efece4'/><rect x='12' y='12' width='176' height='104' fill='%23fff' stroke='%23111' stroke-width='2'/><rect x='12' y='128' width='176' height='120' fill='%23fff' stroke='%23111' stroke-width='2'/></svg>";
};

export type ProjectDetail = {
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
  const navigateRef = useRef(navigate);
  navigateRef.current = navigate;
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [coverCoverError, setCoverCoverError] = useState(false);
  const [transitioning, setTransitioning] = useState(false);
  const lastProjectIdRef = useRef<string | null>(null);

  // Efecto 1: cargar proyecto cuando cambie el ID del proyecto o la etapa.
  // Necesario para que, tras subir una imagen en /upload y navegar a /analysis,
  // se recargue el proyecto y se vea el page_id recién creado.
  useEffect(() => {
    if (!projectId) return;

    let cancelled = false;
    setLoading(true);
    api.getProject(projectId)
      .then((p) => {
        if (cancelled) return;
        setProject(p);
        lastProjectIdRef.current = projectId;
        setLoading(false);
      })
      .catch(() => {
        if (!cancelled) {
          setError("No se pudo cargar el proyecto.");
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, [projectId, stageParam]);

  // Efecto 2: guardia de ruta y redirección cuando cambie la etapa solicitada
  // y ya tengamos el proyecto cargado.
  useEffect(() => {
    if (!project || !stageParam || !projectId) return;

    const currentIdx = STAGE_ORDER.indexOf(project.current_stage);
    const targetIdx = STAGE_ORDER.indexOf(stageParam);
    let allowed = false;
    if (targetIdx === -1) {
      allowed = false;
    } else if (stageParam === project.current_stage) {
      allowed = true;
    } else if (stageParam === "upload" && project.stage_progress.includes("upload")) {
      // Upload no es retornable una vez completada.
      allowed = false;
    } else if (project.stage_progress.includes(stageParam) && targetIdx < currentIdx) {
      // Retroceso a etapa completada y previa.
      allowed = true;
    }
    if (!allowed) {
      navigateRef.current(`/projects/${projectId}/${project.current_stage}`, { replace: true });
    }
  }, [stageParam, projectId, project]);

  // Redirigir /projects/:id (sin stage) a la etapa actual una vez cargado.
  useEffect(() => {
    if (!project || stageParam || !projectId) return;
    navigateRef.current(`/projects/${projectId}/${project.current_stage}`, { replace: true });
  }, [project, projectId]);

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

  const handleComplete = async () => {
    if (!projectId || transitioning || project.status === "completado") return;
    setTransitioning(true);
    setError(null);
    try {
      const updated = await api.transitionStage(projectId, "complete", project.current_stage);
      setProject((prev) => (prev ? { ...prev, ...updated } : prev));
      navigate(`/projects/${projectId}/${updated.current_stage}`, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo avanzar de etapa.");
    } finally {
      setTransitioning(false);
    }
  };

  const handleRegress = (to: string) => {
    if (!projectId) return;
    api.transitionStage(projectId, "regress", to)
      .then((updated) => {
        setProject((prev) => (prev ? { ...prev, ...updated } : prev));
        navigate(`/projects/${projectId}/${to}`);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "No se pudo retroceder de etapa.");
      });
  };

  const isClickable = (s: string) => {
    if (s === project.current_stage) return false;
    if (s === "upload" && isCompleted(s)) return false; // no retornable
    return isCompleted(s) && STAGE_ORDER.indexOf(s) < currentIdx;
  };

  // Mapa de etapa -> componente. Character y Mask consumen sus endpoints HTTP
  // y muestran la configuración/revisión persistida del análisis.
  const stageComponentMap: Record<string, React.ComponentType<any>> = {
    upload: Upload as any,
    analysis: AnalysisStage,
    character: CharacterStage,
    mask: MaskStage,
    approve: ApproveStage,
    colorize: ColorizeStage,
    export: ExportStage,
  };
  const StageComponent = stageComponentMap[stageParam ?? project.current_stage] ?? StagePlaceholder;

  return (
    <div className="project-layout" style={{ display: "flex", flexDirection: "column", gap: 16, padding: 24 }}>
      {/* Encabezado del proyecto */}
      <header style={{ display: "flex", gap: 16, alignItems: "center", borderBottom: "1px solid var(--border)", paddingBottom: 12 }}>
        <img
          src={coverCoverError || !project.portada ? projectCover(null) : projectCover(project.portada)}
          alt="Portada"
          onError={() => setCoverCoverError(true)}
          style={{ width: 72, height: 96, objectFit: "contain", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 6 }}
        />
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--ink-muted)", marginBottom: 4 }}>
            <span className={statusConf[project.status]?.className || "badge"} style={{ fontSize: "0.68rem" }}>{statusConf[project.status]?.text || project.status}</span>
            <span>{project.progreso}%</span>
          </div>
          <h1 style={{ margin: 0, fontSize: "1.25rem" }}>{project.nombre}</h1>
          <p style={{ margin: 4, color: "var(--ink-muted)", fontSize: "0.9rem" }}>
            Etapa actual: <strong>{stageLabel(project.current_stage)}</strong> — {STAGE_DESCRIPTION[project.current_stage]}
          </p>
        </div>

      </header>

      {/* Stepper interno */}
      <section style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 16, background: "var(--surface)" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--ink-muted)", marginBottom: 10 }}>
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
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.65rem" }}>{i + 1}</span>
                <span style={{ marginLeft: 6, fontSize: "0.8rem", fontWeight: active || completed ? 600 : 400 }}>{stageLabel(s)}</span>
              </button>
            );
          })}
        </div>
      </section>

      {/* Contenido de la etapa */}
      {error && <p role="alert" style={{ color: "#c0392b", margin: 0 }}>{error}</p>}
      <main style={{ flex: 1 }}>
        <StageComponent
          stage={stageParam ?? project.current_stage}
          isCurrent={!(stageParam && stageParam !== project.current_stage)}
          onComplete={handleComplete}
          transitioning={transitioning}
        />
      </main>
    </div>
  );
}
