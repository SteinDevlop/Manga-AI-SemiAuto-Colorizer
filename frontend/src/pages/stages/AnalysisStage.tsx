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

export function AnalysisStage() {
  const { id: projectIdParam } = useParams<{ id: string }>();
  const projectId = projectIdParam ?? "";
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
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
  }, [projectId]);

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
    if (!project?.pages?.[0]?.page_id) return;
    setRunning(true);
    setError(null);
    try {
      // POST /api/v1/analysis/{page_id} — aquí SÍ va page_id (regla 0.9).
      const data = await (fetch as any)(`${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"}/analysis/${project.pages[0].page_id}`, {
        method: "POST",
      });
      const json = await data.json();
      setAnalysis(json);
      // Refrescar el proyecto para obtener el nuevo analysis_id vigente.
      const updated = await api.getProject(projectId);
      setProject(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al ejecutar el análisis.");
    } finally {
      setRunning(false);
    }
  };

  const analysisId = analysis?.analysis_id ?? project?.pages?.[0]?.analysis_id ?? null;

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
            disabled={running}
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
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Estado</span>
              <strong>{analysis.estado}</strong>
            </div>
            <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Paneles</span>
              <strong>{analysis.panels?.length ?? 0}</strong>
            </div>
            <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Personajes</span>
              <strong>{analysis.characters?.length ?? 0}</strong>
            </div>
            <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Máscaras</span>
              <strong>{analysis.masks?.length ?? 0}</strong>
            </div>
            <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>analysis_id</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, wordBreak: "break-all" }}>{analysisId}</span>
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.75, color: "var(--ink-muted)", marginBottom: 6, display: "block" }}>Personajes detectados</span>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              {analysis.characters?.map((c: any) => (
                <div key={c.id} style={{ border: "1px solid var(--border)", padding: "8px 12px", borderRadius: 6, background: "var(--surface)", display: "flex", flexDirection: "column", gap: 4, minWidth: 140 }}>
                  <strong>{c.nombre}</strong>
                  <span style={{ fontSize: 0.75, color: "var(--ink-muted)" }}>confianza {(c.confianza_identidad ?? 0).toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.75, color: "var(--ink-muted)", marginBottom: 6, display: "block" }}>Máscaras</span>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              {analysis.masks?.map((m: any) => (
                <div key={m.id} style={{ border: "1px solid var(--border)", padding: "8px 12px", borderRadius: 6, background: "var(--surface)", display: "flex", flexDirection: "column", gap: 4, minWidth: 140 }}>
                  <strong>{m.tipo_mascara}</strong>
                  <span style={{ fontSize: 0.75, color: "var(--ink-muted)" }}>{m.appearance_id.slice(0, 6)}…</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 20, display: "flex", gap: 10 }}>
            <button type="button" className="btn btn-vermilion" onClick={() => navigate(`/projects/${projectId}/approve`)}>
              Ir a Aprobación →
            </button>
          </div>
        </>
      )}
    </section>
  );
}
