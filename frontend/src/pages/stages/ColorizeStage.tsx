/* Etapa Colorize dentro de un proyecto.
 *
 * Lanza y sigue el trabajo de colorización usando el `analysis_id` vigente
 * del proyecto (defecto 0.9).
 */
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import type { ProjectDetail } from "../../components/ProjectLayout";

export function ColorizeStage() {
  const { id: projectIdParam } = useParams<{ id: string }>();
  const projectId = projectIdParam ?? "";
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [pollTimer, setPollTimer] = useState<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api.getProject(projectId)
      .then((p: any) => {
        if (cancelled) return;
        setProject(p);
        const analysisId = p.pages?.[0]?.analysis_id;
        if (analysisId) {
          loadJobForAnalysis(analysisId);
        } else {
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setError("No se pudo cargar el proyecto.");
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
      if (pollTimer) clearInterval(pollTimer);
    };
  }, [projectId, pollTimer]);

  const loadJobForAnalysis = async (analysisId: string) => {
    try {
      const jobs = await api.listColorizations();
      const j = jobs.find((x: any) => x.analysis_id === analysisId);
      if (j) setJob(j);
    } catch {
      // Ignorar al cargar; se reintenta al lanzar.
    } finally {
      if (!pollTimer) setLoading(false);
    }
  };

  const startPolling = (jobId: string) => {
    if (pollTimer) clearInterval(pollTimer);
    const t = setInterval(async () => {
      try {
        const j = await api.getColorization(jobId);
        setJob(j);
        if (j.estado === "completed" || j.estado === "failed" || j.estado === "error") {
          clearInterval(t);
          setPollTimer(null);
        }
      } catch {
        // Ignorar errores de polling.
      }
    }, 3000);
    setPollTimer(t);
  };

  const handleLaunch = async () => {
    const analysisId = project?.pages?.[0]?.analysis_id;
    if (!analysisId) {
      setError("No hay análisis aprobado. Completa Aprobación primero.");
      return;
    }
    setRunning(true);
    setError(null);
    try {
      const created = await api.createColorization(analysisId);
      setJob(created);
      startPolling(created.job_id);
    } catch (err) {
      setRunning(false);
      setError(err instanceof Error ? err.message : "Error al lanzar la colorización.");
    }
  };

  const analysisId = project?.pages?.[0]?.analysis_id ?? null;
  const isTerminal = job?.estado === "completed" || job?.estado === "failed" || job?.estado === "error";

  if (loading) {
    return <div style={{ padding: 40, textAlign: "center", color: "var(--ink-muted)" }}>Cargando colorización…</div>;
  }
  if (error) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "#c0392b" }}>
        {error}<br />
        <button type="button" className="btn btn-outline" onClick={() => navigate(`/projects/${projectId}/approve`)}>
          Ir a Aprobación
        </button>
      </div>
    );
  }
  if (!project) return null;

  return (
    <section className="screen is-active" id="screen-colorize">
      <div className="page-head">
        <div>
          <span className="eyebrow">6. Colorize</span>
          <h1 className="h1">Colorización</h1>
          <p style={{ color: "var(--ink-muted)", marginTop: 6 }}>
            Lanza el trabajo de colorización sobre el análisis aprobado.
            Usa el `analysis_id` vigente del proyecto.
          </p>
        </div>
      </div>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 20 }}>
        <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Estado</span>
          <strong>{job?.estado ?? "—"}</strong>
        </div>
        <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Progreso</span>
          <strong>{job?.progreso ?? 0}%</strong>
        </div>
        <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>analysis_id</span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, wordBreak: "break-all" }}>{analysisId}</span>
        </div>
      </div>

      {job?.mensaje && (
        <p style={{ color: "var(--ink-muted)", fontSize: 0.85, marginBottom: 12 }}>{job.mensaje}</p>
      )}

      {!job && (
        <div style={{ display: "flex", gap: 10 }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => navigate(`/projects/${projectId}/approve`)}
            disabled={!analysisId}
          >
            Volver a Aprobación
          </button>
          <button
            type="button"
            className="btn-vermilion"
            disabled={running || !analysisId}
            onClick={handleLaunch}
          >
            {running ? "Lanzando…" : "Lanzar colorización"}
          </button>
        </div>
      )}

      {job && !isTerminal && (
        <div style={{ marginTop: 16 }}>
          <div style={{ height: 6, background: "var(--border)", borderRadius: 3, overflow: "hidden", marginBottom: 6 }}>
            <div style={{ width: `${job.progreso}%`, height: "100%", background: "var(--vermilion)" }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: 0.75, color: "var(--ink-muted)" }}>
            <span>{job.progreso}%</span>
            <span>Actualizando…</span>
          </div>
        </div>
      )}

      {job && isTerminal && job.estado === "completed" && (
        <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
          <button type="button" className="btn-vermilion" onClick={() => navigate(`/projects/${projectId}/export`)}>
            Ir a Exportar →
          </button>
        </div>
      )}
    </section>
  );
}
