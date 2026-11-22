/* Etapa Analysis dentro de un proyecto.
 *
 * Muestra el resultado del análisis de la página usando el `analysis_id`
 * vigente entregado por el detalle del proyecto (defecto 0.9: nunca se reusa
 * el `page_id` donde el backend espera un `analysis_id`).
 */
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import type { ProjectDetail } from "../../components/ProjectLayout";

export function AnalysisStage({ onComplete }: { onComplete?: () => void }) {
  const { id: projectIdParam, stage: stageParam } = useParams<{ id: string; stage: string }>();
  const projectId = projectIdParam ?? "";
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    setLoading(true);
    api.getProject(projectId)
      .then((p: any) => {
        if (cancelled) return;
        setProject(p);
        const analysisId = p.pages?.[0]?.analysis_id;
        if (analysisId) {
          loadAnalysis(analysisId);
        } else {
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setError("No se pudo cargar el proyecto.");
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [projectId, stageParam]);

  const loadAnalysis = async (analysisId: string) => {
    try {
      const data = await api.getAnalysis(analysisId);
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar el análisis.");
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    setRunning(true);
    setError(null);
    try {
      // Re-fetch del proyecto para obtener el page_id más actualizado
      const fresh = await api.getProject(projectId);
      setProject(fresh);
      const pageId = fresh.pages?.[0]?.page_id;
      if (!pageId) {
        setError("Primero sube una imagen en la etapa de Subida para poder ejecutar el análisis.");
        setRunning(false);
        return;
      }
      // POST /api/v1/analysis/{page_id} — aquí SÍ va page_id (regla 0.9).
      const json = await api.post<any>(`/analysis/${pageId}`);
      setAnalysis(json);
      setRunning(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al ejecutar el análisis.");
      setRunning(false);
    }
  };

  const analysisId = analysis?.analysis_id ?? project?.pages?.[0]?.analysis_id ?? null;
  const puedeContinuar = !!analysis && !!analysis.analysis_id;

  if (loading) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "var(--ink-muted)" }}>
        Cargando análisis…
      </div>
    );
  }
  if (error) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "#c0392b" }}>
        {error}<br />
        <button type="button" className="btn btn-outline" onClick={() => navigate(`/projects/${projectId}`)}>
          Volver al proyecto
        </button>
      </div>
    );
  }
  if (!project) {
    return null;
  }

  return (
    <section className="screen is-active" id="screen-analysis">
      <div className="page-head">
        <div>
          <span className="eyebrow">2. Analysis</span>
          <h1 className="h1">Análisis de la página</h1>
          <p style={{ color: "var(--ink-muted)", marginTop: 6 }}>
            Paneles, personajes y máscaras detectados. El análisis usa el
            `analysis_id` vigente del proyecto.
          </p>
        </div>
        {!analysis && (
          <button
            type="button"
            className="btn-vermilion"
            disabled={running || analysis || !project}
            onClick={handleRunAnalysis}
          >
            {running ? "Analizando…" : "Ejecutar análisis"}
          </button>
        )}
      </div>

      {analysis && (
        <>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 20 }}>
            <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Estado</span>
              <strong>{analysis.estado}</strong>
            </div>
            <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Paneles</span>
              <strong>{analysis.panels?.length ?? 0}</strong>
            </div>
            <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Personajes</span>
              <strong>{analysis.characters?.length ?? 0}</strong>
            </div>
            <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Máscaras</span>
              <strong>{analysis.masks?.length ?? 0}</strong>
            </div>
            <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>analysis_id</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", wordBreak: "break-all" }}>{analysisId}</span>
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--ink-muted)", marginBottom: 6, display: "block" }}>Personajes detectados</span>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              {analysis.characters?.map((c: any) => (
                <div key={c.id} style={{ border: "1px solid var(--border)", padding: "8px 12px", borderRadius: 6, background: "var(--surface)", display: "flex", flexDirection: "column", gap: 4, minWidth: 140 }}>
                  <strong>{c.nombre}</strong>
                  <span style={{ fontSize: "0.75rem", color: "var(--ink-muted)" }}>confianza {(c.confianza_identidad ?? 0).toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--ink-muted)", marginBottom: 6, display: "block" }}>Máscaras</span>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              {analysis.masks?.map((m: any) => (
                <div key={m.id} style={{ border: "1px solid var(--border)", padding: "8px 12px", borderRadius: 6, background: "var(--surface)", display: "flex", flexDirection: "column", gap: 4, minWidth: 140 }}>
                  <strong>{m.tipo_mascara}</strong>
                  <span style={{ fontSize: "0.75rem", color: "var(--ink-muted)" }}>{m.appearance_id.slice(0, 6)}…</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 20, display: "flex", gap: 10 }}>
            <button type="button" className="btn btn-vermilion" disabled={!puedeContinuar} onClick={() => onComplete?.()}>
              Guardar análisis y continuar a personajes →
            </button>
          </div>
        </>
      )}
    </section>
  );
}
