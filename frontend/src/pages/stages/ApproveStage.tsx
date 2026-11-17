/* Etapa Approve dentro de un proyecto.
 *
 * Resumen del análisis para aprobar antes de colorizar. Usa el `analysis_id`
 * vigente del proyecto (defecto 0.9).
 */
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import type { ProjectDetail } from "../../components/ProjectLayout";

export function ApproveStage() {
  const { id: projectIdParam } = useParams<{ id: string }>();
  const projectId = projectIdParam ?? "";
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api.getProject(projectId)
      .then((p: any) => {
        if (cancelled) return;
        setProject(p);
        const analysisId = p.pages?.[0]?.analysis_id;
        if (analysisId) {
          api.getAnalysis(analysisId)
            .then((data: any) => { if (!cancelled) setAnalysis(data); })
            .catch(() => { if (!cancelled) setError("No se pudo cargar el análisis."); })
            .finally(() => { if (!cancelled) setLoading(false); });
        } else {
          setLoading(false);
          setError("Este proyecto aún no tiene un análisis. Completa la etapa Analysis primero.");
        }
      })
      .catch(() => {
        if (!cancelled) setError("No se pudo cargar el proyecto.");
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [projectId]);

  const handleApprove = async () => {
    const analysisId = analysis?.analysis_id;
    if (!analysisId) {
      setError("No hay análisis para aprobar.");
      return;
    }
    setApproving(true);
    setError(null);
    try {
      await api.approveAnalysis(analysisId);
      navigate(`/projects/${projectId}/colorize`);
    } catch (err) {
      setApproving(false);
      setError(err instanceof Error ? err.message : "Error al aprobar el análisis.");
    }
  };

  if (loading) {
    return <div style={{ padding: 40, textAlign: "center", color: "var(--ink-muted)" }}>Cargando aprobación…</div>;
  }
  if (error) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "#c0392b" }}>
        {error}<br />
        <button type="button" className="btn btn-outline" onClick={() => navigate(`/projects/${projectId}/analysis`)}>
          Ir a Análisis
        </button>
      </div>
    );
  }
  if (!project || !analysis) return null;

  return (
    <section className="screen is-active" id="screen-approve">
      <div className="page-head">
        <div>
          <span className="eyebrow">5. Approve</span>
          <h1 className="h1">Aprobar análisis</h1>
          <p style={{ color: "var(--ink-muted)", marginTop: 6 }}>
            Revisa los personajes y máscaras detectados antes de colorizar.
            Usa el `analysis_id` vigente del proyecto.
          </p>
        </div>
      </div>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 20 }}>
        <div style={{ border: "1px solid var(--border)", padding: 14, borderRadius: 8, background: "var(--surface)", flex: 1, minWidth: 150 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)", display: "block", marginBottom: 4 }}>Estado análisis</span>
          <strong>{analysis.estado}</strong>
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
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.72, wordBreak: "break-all" }}>{analysis.analysis_id}</span>
        </div>
      </div>

      <div style={{ marginBottom: 20 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.75, color: "var(--ink-muted)", marginBottom: 6, display: "block" }}>Resumen para aprobar</span>
        <ul style={{ listStyle: "none", padding: 0, margin: 0, maxWidth: 560 }}>
          {analysis.characters?.map((c: any) => (
            <li key={c.id} style={{ borderBottom: "1px solid var(--border)", padding: "10px 0", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 0.9 }}>
              <span>{c.nombre}</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 0.75, color: "var(--ink-muted)" }}>{((c.confianza_identidad ?? 0) * 100).toFixed(0)}% confianza</span>
            </li>
          ))}
          {analysis.characters?.length === 0 && (
            <li style={{ color: "var(--ink-muted)", padding: "10px 0" }}>Sin personajes detectados.</li>
          )}
        </ul>
      </div>

      <div style={{ display: "flex", gap: 10 }}>
        <button
          type="button"
          className="btn btn-outline"
          disabled={approving}
          onClick={() => navigate(`/projects/${projectId}/analysis`)}
        >
          Volver a Análisis
        </button>
        <button
          type="button"
          className="btn-vermilion"
          disabled={approving || analysis.estado !== "APPROVED" && analysis.estado !== "approved"}
          onClick={handleApprove}
        >
          {approving ? "Aprobando…" : "Aprobar análisis y continuar a Colorizar"}
        </button>
      </div>
    </section>
  );
}
