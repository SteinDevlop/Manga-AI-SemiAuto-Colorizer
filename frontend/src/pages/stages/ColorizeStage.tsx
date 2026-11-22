/* Etapa Colorize dentro de un proyecto.
 *
 * Lanza y sigue el trabajo de colorización usando el `analysis_id` vigente
 * del proyecto (defecto 0.9).
 */
import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import type { ProjectDetail } from "../../components/ProjectLayout";

export function ColorizeStage({ onComplete }: { onComplete?: () => void }) {
  const { id: projectIdParam } = useParams<{ id: string }>();
  const projectId = projectIdParam ?? "";
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [models, setModels] = useState<any[]>([]);
  const [selectedModelId, setSelectedModelId] = useState("");
  const [resultImageUrl, setResultImageUrl] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastProjectIdRef = useRef<string | null>(null);
  const stopPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = null;
  };

  useEffect(() => {
    if (!projectId) return;
    // Evitar re-fetch si ya cargamos este proyecto.
    if (lastProjectIdRef.current === projectId && project) return;

    let cancelled = false;
    setLoading(true);
    api.listModels("colorizacion").then(result => {
      if (cancelled) return;
      const compatible = result.items.filter((m: any) => m.is_active && (m.formato === "pt" || m.formato === "onnx"));
      setModels(compatible);
      setSelectedModelId(compatible.find((m: any) => m.is_default)?.id || compatible[0]?.id || "");
    }).catch(() => { if (!cancelled) setModels([]); });
    api.getProject(projectId)
      .then((p: any) => {
        if (cancelled) return;
        setProject(p);
        lastProjectIdRef.current = projectId;
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
      stopPolling();
    };
  }, [projectId]);

  const loadJobForAnalysis = async (analysisId: string) => {
    try {
      const jobs = await api.listColorizations();
      const j = jobs.find((x: any) => x.analysis_id === analysisId);
      if (j) setJob(j);
    } catch {
      // Ignorar al cargar; se reintenta al lanzar.
    } finally {
      setLoading(false);
    }
  };

  const startPolling = (jobId: string) => {
    stopPolling();
    const t = setInterval(async () => {
      try {
        const j = await api.getColorization(jobId);
        setJob(j);
        if (j.estado === "completed" || j.estado === "failed" || j.estado === "cancelled" || j.estado === "error") {
          stopPolling();
          setRunning(false);
        }
      } catch {
        // Ignorar errores de polling.
      }
    }, 3000);
    pollRef.current = t;
  };

  const handleLaunch = async () => {
    const analysisId = project?.pages?.[0]?.analysis_id;
    if (!analysisId) {
      setError("No hay análisis aprobado. Completa Aprobación primero.");
      return;
    }
    if (!models.length || !selectedModelId) {
      setError("No hay un modelo de colorización activo compatible. Activa o registra un modelo PyTorch (.pt) en Model Registry.");
      return;
    }
    setRunning(true);
    setError(null);
    setResultImageUrl(null);
    try {
      const created = await api.createColorization(analysisId, selectedModelId);
      setJob(created);
      startPolling(created.job_id);
    } catch (err) {
      setRunning(false);
      setError(err instanceof Error ? err.message : "Error al lanzar la colorización.");
    }
  };

  // Cargar imagen de resultado cuando el job se completa (render en la web, no solo descarga)
  useEffect(() => {
    if (!job || job.estado !== "completed" || resultImageUrl) return;
    if (!job.job_id) return;
    let cancelled = false;
    api.downloadColorization(job.job_id)
      .then((blob) => {
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        setResultImageUrl(url);
      })
      .catch((err) => {
        console.warn("No se pudo cargar la imagen de resultado:", err);
      });
    return () => { cancelled = true; };
  }, [job, resultImageUrl]);

  // Revocar URL de objeto al desmontar o cuando cambie el resultado
  useEffect(() => {
    return () => {
      if (resultImageUrl) URL.revokeObjectURL(resultImageUrl);
    };
  }, [resultImageUrl]);

  const analysisId = project?.pages?.[0]?.analysis_id ?? null;
  const isTerminal = job?.estado === "completed" || job?.estado === "failed" || job?.estado === "cancelled" || job?.estado === "error";

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
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Estado</span>
          <strong>{job?.estado ?? "—"}</strong>
        </div>
        <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Progreso</span>
          <strong>{job?.progreso ?? 0}%</strong>
        </div>
        <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>analysis_id</span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", wordBreak: "break-all" }}>{analysisId}</span>
        </div>
      </div>

      <div className="panel-box" style={{ marginBottom: 16 }}>
        <label htmlFor="colorization-model" style={{ display: "block", marginBottom: 8 }}>Modelo activo del Model Registry</label>
        {models.length > 0 ? <select id="colorization-model" value={selectedModelId} onChange={e => setSelectedModelId(e.target.value)} style={{ width: "100%", maxWidth: 480, padding: 10 }}>
          {models.map(model => <option key={model.id} value={model.id}>{model.nombre} · {model.version}{model.is_default ? " · predeterminado" : ""}</option>)}
        </select> : <p role="alert" style={{ color: "#b45309", margin: 0 }}>No hay modelos activos compatibles para colorización. El motor requiere un modelo local (.pt o .onnx). <button type="button" className="btn btn-outline btn-sm" onClick={() => navigate("/models")}>Abrir Model Registry</button></p>}
      </div>

      {job?.mensaje && (
        <p style={{ color: "var(--ink-muted)", fontSize: "0.85rem", marginBottom: 12 }}>{job.mensaje}</p>
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
            disabled={running || !analysisId || !selectedModelId}
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
          <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--ink-muted)" }}>
            <span>{job.progreso}%</span>
            <span>Actualizando…</span>
          </div>
        </div>
      )}

      {job && isTerminal && job.estado === "completed" && (
        <div style={{ marginTop: 16 }}>
          {resultImageUrl && (
            <div style={{ border: "1px solid var(--border)", borderRadius: 8, padding: 12, background: "var(--surface)", maxWidth: "100%", overflow: "auto", marginBottom: 12 }}>
              <img src={resultImageUrl} alt="Resultado de colorización" style={{ maxWidth: "100%", maxHeight: 500, objectFit: "contain", display: "block", margin: "0 auto" }} />
            </div>
          )}
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button type="button" className="btn-vermilion" onClick={() => onComplete?.()}>
              Guardar resultado y continuar a Exportar →
            </button>
            <button
              type="button"
              className="btn btn-outline"
              onClick={() => {
                const link = document.createElement("a");
                link.href = resultImageUrl || "";
                link.download = `colorizacion-${job.job_id?.slice(0, 8)}.png`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
              }}
              disabled={!resultImageUrl}
            >
              Descargar resultado
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
