/* SUMI Analysis Studio — análisis real conectado a la API. */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, API_BASE } from "../api/client";
import type { Project } from "../types";

export default function Analysis() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    if (!analysisId) return;
    api.get<any>(`/analysis/${analysisId}`)
      .then((data) => {
        setAnalysis(data);
        setLoading(false);
      })
      .catch((err) => {
        // Si no existe, se puede crear desde la subida (flujo pendiente)
        setLoading(false);
      });
  }, [analysisId]);

  const runAnalysis = async () => {
    setAnalyzing(true);
    try {
      const data = await api.post<any>(`/analysis/${analysisId}`, {});
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  };

  const approve = async () => {
    try {
      await api.post<any>(`/analysis/${analysisId}/approve`, {});
      navigate(`/colorize/${analysisId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed.");
    }
  };

  return (
    <section className="screen is-active" id="screen-analysis">
      <div className="page-head">
        <div>
          <span className="eyebrow">03 // Computer Vision Inspection</span>
          <h1 className="h1">Analysis <em>Studio</em> — {analysisId}</h1>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          {!analysis && (
            <button type="button" className="btn btn-primary" onClick={runAnalysis} disabled={analyzing}>
              {analyzing ? "Analyzing…" : "Run Analysis"}
            </button>
          )}
          {analysis && analysis.estado !== "APPROVED" && (
            <button type="button" className="btn btn-vermilion" onClick={approve}>
              Approve for Colorization
            </button>
          )}
          {analysis && analysis.estado === "APPROVED" && (
            <button type="button" className="btn btn-primary" onClick={() => navigate(`/colorize/${analysisId}`)}>
              Go to Colorize
            </button>
          )}
        </div>
      </div>

      {error && <p style={{ color: "#c0392b", fontSize: 0.85, margin: "8px 0" }}>Error: {error}</p>}

      {analysis && (
        <div className="grid-3" style={{ marginTop: 20 }}>
          <div className="panel-box">
            <span className="eyebrow">Panels</span>
            <p>{analysis.panels?.length ?? 0} detected</p>
          </div>
          <div className="panel-box">
            <span className="eyebrow">Characters</span>
            <p>{analysis.characters?.length ?? 0} detected</p>
          </div>
          <div className="panel-box">
            <span className="eyebrow">Masks</span>
            <p>{analysis.masks?.length ?? 0} created</p>
          </div>
        </div>
      )}
    </section>
  );
}
