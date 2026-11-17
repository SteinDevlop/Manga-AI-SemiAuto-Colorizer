/* Etapa Export dentro de un proyecto.
 *
 * Muestra el resultado final de la colorización y permite descargarlo.
 * Usa el `analysis_id` vigente del proyecto para encontrar el job
 * de colorización (defecto 0.9).
 */
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import type { ProjectDetail } from "../../components/ProjectLayout";

export function ExportStage() {
  const { id: projectIdParam } = useParams<{ id: string }>();
  const projectId = projectIdParam ?? "";
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api.getProject(projectId)
      .then((p: any) => {
        if (cancelled) return;
        setProject(p);
        const analysisId = p.pages?.[0]?.analysis_id;
        if (analysisId) {
          api.listColorizations()
            .then((jobs) => {
              if (cancelled) return;
              const j = jobs.find((x: any) => x.analysis_id === analysisId);
              setJob(j ?? null);
            })
            .catch(() => { if (!cancelled) setError("No se pudieron cargar los trabajos de colorización."); })
            .finally(() => { if (!cancelled) setLoading(false); });
        } else {
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setError("No se pudo cargar el proyecto.");
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [projectId]);

  const handleDownload = () => {
    if (!job?.ruta_resultado) {
      setError("No hay resultado disponible para descargar.");
      return;
    }
    const base = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
    // Extraer job_id de la ruta del job (el detalle trae job_id).
    const jobId = job.job_id;
    window.location.href = `${base}/colorizations/${jobId}/result`;
  };

  const analysisId = project?.pages?.[0]?.analysis_id ?? null;

  if (loading) {
    return <div style={{ padding: 40, textAlign: "center", color: "var(--ink-muted)" }}>Cargando exportación…</div>;
  }
  if (error) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "#c0392b" }}>
        {error}<br />
        <button type="button" className="btn btn-outline" onClick={() => navigate(`/projects/${projectId}/colorize`)}>
          Ir a Colorizar
        </button>
      </div>
    );
  }
  if (!project) return null;

  const done = job?.estado === "completed" && job?.ruta_resultado;

  return (
    <section className="screen is-active" id="screen-export">
      <div className="page-head">
        <div>
          <span className="eyebrow">7. Export</span>
          <h1 className="h1">Exportar resultado</h1>
          <p style={{ color: "var(--ink-muted)", marginTop: 6 }}>
            Descarga la página colorizada final. Resultado del job vinculado al
            `analysis_id` del proyecto.
          </p>
        </div>
      </div>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 20 }}>
        <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Estado del job</span>
          <strong>{job?.estado ?? "—"}</strong>
        </div>
        <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>analysis_id</span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, wordBreak: "break-all" }}>{analysisId}</span>
        </div>
      </div>

      {done ? (
        <div style={{ border: "1px solid var(--border)", padding: 24, borderRadius: 10, background: "var(--surface)", textAlign: "center", marginBottom: 20 }}>
          <p style={{ marginBottom: 12, color: "var(--ink-muted)" }}>Resultado listo para descargar</p>
          <button type="button" className="btn-vermilion" onClick={handleDownload}>
            Descargar resultado
          </button>
        </div>
      ) : job ? (
        <div style={{ color: "var(--ink-muted)", textAlign: "center", marginBottom: 20 }}>
          <p>El resultado aún no está disponible (estado: {job.estado}).</p>
          {job.mensaje && <p style={{ fontSize: 0.85 }}>{job.mensaje}</p>}
        </div>
      ) : (
        <div style={{ color: "var(--ink-muted)", textAlign: "center", marginBottom: 20 }}>
          <p>No hay un trabajo de colorización para este análisis.</p>
        </div>
      )}

      <div style={{ display: "flex", gap: 10 }}>
        <button type="button" className="btn btn-outline" onClick={() => navigate(`/projects/${projectId}/colorize`)}>
          Volver a Colorizar
        </button>
        <button type="button" className="btn btn-outline" onClick={() => navigate(`/projects/${projectId}`)}>
          Volver al proyecto
        </button>
      </div>
    </section>
  );
}
