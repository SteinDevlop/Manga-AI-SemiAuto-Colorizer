/* SUMI Page Detail — ver una página subida y sus máscaras de análisis. */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, API_BASE } from "../api/client";
import type { Page, Mask, CharacterAppearance } from "../types";

export default function PageDetail() {
  const { pageId } = useParams<{ pageId: string }>();
  const navigate = useNavigate();
  const [page, setPage] = useState<Page | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!pageId) return;
    setLoading(true);
    // Obtener la página (no hay endpoint directo por pageId, usamos listado del proyecto)
    // Como no tenemos endpoint por pageId individual, intentamos obtener el análisis directamente
    api.get<any>(`/analysis/${pageId}`)
      .then((data) => {
        setAnalysis(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [pageId]);

  const goBack = () => navigate("/projects");

  if (loading) {
    return (
      <section className="screen is-active" id="screen-page-detail">
        <div className="page-head">
          <div>
            <span className="eyebrow">02 / Page Detail</span>
            <h1 className="h1">Page <em>Details</em></h1>
          </div>
        </div>
        <p style={{ color: "var(--ink-muted)" }}>Loading page…</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="screen is-active" id="screen-page-detail">
        <div className="page-head">
          <div>
            <span className="eyebrow">02 / Page Detail</span>
            <h1 className="h1">Page <em>Details</em></h1>
          </div>
        </div>
        <p style={{ color: "#c0392b" }}>{error}</p>
        <button type="button" className="btn btn-vermilion" onClick={goBack}>
          Back to Projects
        </button>
      </section>
    );
  }

  if (!analysis) {
    return (
      <section className="screen is-active" id="screen-page-detail">
        <div className="page-head">
          <div>
            <span className="eyebrow">02 / Page Detail</span>
            <h1 className="h1">Page <em>Details</em></h1>
          </div>
        </div>
        <p style={{ color: "var(--ink-muted)" }}>No analysis found for this page.</p>
        <button type="button" className="btn btn-vermilion" onClick={goBack}>
          Back to Projects
        </button>
      </section>
    );
  }

  return (
    <section className="screen is-active" id="screen-page-detail">
      <div className="page-head">
        <div>
          <span className="eyebrow">02 / Page Detail</span>
          <h1 className="h1">Page <em>Details</em></h1>
        </div>
        <button type="button" className="btn btn-outline btn-sm" onClick={goBack}>
          ← Back to Projects
        </button>
      </div>

      <div className="panel-box">
        <span className="eyebrow">Page Information</span>
        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 10, fontSize: 0.84 }}>
          <div>
            <strong>Page ID:</strong>
            <span className="mono-label">{pageId}</span>
          </div>
          <div>
            <strong>Analysis ID:</strong>
            <span className="mono-label">{analysis.id}</span>
          </div>
          <div>
            <strong>Status:</strong>
            {analysis.estado === "APPROVED" ? (
              <span className="badge badge-done">Approved</span>
            ) : (
              <span className="badge badge-review">{analysis.estado}</span>
            )}
          </div>
          <div>
            <strong>Confidence:</strong> {analysis.confianza_global ?? "n/a"}
          </div>
          <div>
            <strong>Model:</strong> {analysis.version_modelo ?? "n/a"}
          </div>
        </div>
      </div>

      <div className="panel-box" style={{ marginTop: 24 }}>
        <span className="eyebrow">Panels</span>
        <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12 }}>
          {(analysis.panels || []).map((panel: any) => (
            <div key={panel.id} className="panel-box" style={{ padding: 12, border: "1px solid var(--border)", borderRadius: 6 }}>
              <strong>Panel #{panel.numero_orden}</strong>
              <p>{panel.x}, {panel.y}, {panel.ancho}×{panel.alto}</p>
              <p>Confidence: {(panel.confianza_deteccion ?? 0).toFixed(2)}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="panel-box" style={{ marginTop: 24 }}>
        <span className="eyebrow">Characters</span>
        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          {(analysis.characters || []).map((character: any) => (
            <div key={character.id} className="panel-box" style={{ padding: 12, border: "1px solid var(--border)", borderRadius: 6 }}>
              <strong>{character.nombre}</strong>
              <p>Confidence: {(character.confianza_identidad ?? 0).toFixed(2)}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="panel-box" style={{ marginTop: 24 }}>
        <span className="eyebrow">Masks</span>
        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          {(analysis.masks || []).map((mask: any) => (
            <div key={mask.id} className="panel-box" style={{ padding: 12, border: "1px solid var(--border)", borderRadius: 6, display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ width: 48, height: 48, border: "1px solid var(--border)", borderRadius: 4, background: "#1e293b" }} />
              <div>
                <strong>{mask.tipo_mascara}</strong>
                <p>{mask.ancho}×{mask.alto}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
