/* SUMI Mask Editor — ver máscaras de segmentación de un análisis. */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, API_BASE } from "../api/client";
import type { CharacterAppearance } from "../types";

export default function Masks() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [maskVisible, setMaskVisible] = useState(true);

  useEffect(() => {
    if (!analysisId) return;
    setLoading(true);
    api.get<any>(`/analysis/${analysisId}`)
      .then((data) => {
        setAnalysis(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load analysis.");
        setLoading(false);
      });
  }, [analysisId]);

  const goBack = () => navigate("/projects");

  if (loading) {
    return (
      <section className="screen is-active" id="screen-masks">
        <div className="page-head">
          <div>
            <span className="eyebrow">05 // Segmentation & Mask Review</span>
            <h1 className="h1">Loading masks…</h1>
          </div>
        </div>
        <p style={{ color: "var(--ink-muted)" }}>Loading mask data…</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="screen is-active" id="screen-masks">
        <div className="page-head">
          <div>
            <span className="eyebrow">05 // Segmentation & Mask Review</span>
            <h1 className="h1">Mask Editor</h1>
          </div>
        </div>
        <p style={{ color: "#c0392b" }}>{error}</p>
        <button type="button" className="btn btn-vermilion" onClick={goBack}>
          Back to Projects
        </button>
      </section>
    );
  }

  if (!analysis || !analysis.masks || analysis.masks.length === 0) {
    return (
      <section className="screen is-active" id="screen-masks">
        <div className="page-head">
          <div>
            <span className="eyebrow">05 // Segmentation & Mask Review</span>
            <h1 className="h1">Mask Editor</h1>
          </div>
          <button type="button" className="btn btn-outline btn-sm" onClick={goBack}>
            ← Back to Projects
          </button>
        </div>
        <div className="panel-box" style={{ textAlign: "center", padding: "64px 24px" }}>
          <span className="eyebrow">No Masks</span>
          <h2 className="h1">No masks detected in this analysis.</h2>
          <p style={{ color: "var(--ink-muted)", maxWidth: 440, margin: "0 auto 24px" }}>
            Run analysis on a page first to generate segmentation masks.
          </p>
        </div>
      </section>
    );
  }

  const appearances = analysis.appearances || [];

  return (
    <section className="screen is-active" id="screen-masks">
      <div className="page-head">
        <div>
          <span className="eyebrow">05 // Segmentation & Mask Review</span>
          <h1 className="h1">Mask Editor — Analysis {(analysisId ?? "").slice(0, 8)}…</h1>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setMaskVisible((v) => !v)}
          >
            {maskVisible ? "Hide Mask Overlay" : "Show Mask Overlay"}
          </button>
          <button type="button" className="btn btn-outline btn-sm" onClick={goBack}>
            ← Back to Projects
          </button>
        </div>
      </div>

      <div className="grid-2" style={{ gridTemplateColumns: "1fr 320px" }}>
        <div className="viewer-canvas">
          <div className="viewer-art-wrap">
            <svg viewBox="0 0 360 480" preserveAspectRatio="xMidYMid slice">
              <rect width="360" height="480" fill="#faf9f6" />
              <rect x="18" y="18" width="324" height="200" fill="#e8e5dc" stroke="#111" strokeWidth="2" />
              <path d="M90 218 L120 110 Q140 90 170 90 Q200 90 215 115 L235 218 Z" fill="#111" />
              <circle cx="155" cy="72" r="24" fill="#d8d4ca" stroke="#111" strokeWidth="2" />
            </svg>
            <svg
              className={`mask-overlay ${maskVisible ? "" : "is-hidden"}`}
              id="maskOverlaySvg"
              viewBox="0 0 360 480"
            >
              {analysis.masks.map((mask: any, idx: number) => (
                <path
                  key={mask.id}
                  d={`M${20 + idx * 60} 218 L${50 + idx * 60} 110 Q${70 + idx * 60} 90 ${100 + idx * 60} 90 Q${130 + idx * 60} 90 ${145 + idx * 60} 115 L${165 + idx * 60} 218 Z`}
                  fill="#315bea"
                  fillOpacity={0.6}
                />
              ))}
            </svg>
          </div>
        </div>

        <div className="panel-box">
          <span className="eyebrow">Active Mask Layers</span>
          <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
            {analysis.masks.map((mask: any) => {
              const appearance = appearances.find((a: CharacterAppearance) => a.id === mask.appearance_id);
              return (
                <div key={mask.id} className="char-row is-selected" style={{ marginTop: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <strong>{mask.tipo_mascara}</strong>
                      <span className="mono-label">{mask.id.slice(0, 8)}…</span>
                    </div>
                    <span className="dot" style={{ background: "var(--electric)" }} />
                  </div>
                  <p style={{ fontSize: "0.82rem", color: "var(--ink-muted)", margin: "4px 0 0 0" }}>
                    {appearance?.character_id ? `Character ${appearance.character_id.slice(0, 8)}…` : "Unknown character"}
                    {mask.ancho && mask.alto ? ` · ${mask.ancho}×${mask.alto}` : ""}
                  </p>
                </div>
              )
            })}
          </div>
          <p style={{ fontSize: "0.82rem", color: "var(--ink-muted)", margin: "16px 0" }}>
            Verify segmentation boundaries before locking configuration. You may upload a corrected PNG mask artifact if needed.
          </p>
          <label className="btn btn-outline btn-sm" style={{ width: "100%", justifyContent: "center", cursor: "pointer" }}>
            Replace Mask Artifact
            <input type="file" accept="image/png" hidden />
          </label>
        </div>
      </div>
    </section>
  );
}
