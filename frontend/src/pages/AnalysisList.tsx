/* SUMI Analysis List — selecciona una página para analizar. */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Page } from "../types";

export default function AnalysisList() {
  const [pages, setPages] = useState<Page[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    api.get<Page[]>("/api/v1/pages/00000000-0000-0000-0000-000000000000")
      .then(() => { /* endpoint no existe, fallback */ })
      .catch(() => {
        // No hay endpoint para listar páginas por proyecto directamente
        setLoading(false);
        setError("No hay endpoint para listar páginas por proyecto. Ve a Upload primero.");
      });
  }, []);

  if (loading) {
    return (
      <section className="screen is-active" id="screen-analysis-list">
        <div className="page-head">
          <div>
            <span className="eyebrow">03 // Analysis</span>
            <h1 className="h1">Cargando páginas…</h1>
          </div>
        </div>
        <p style={{ color: "var(--ink-muted)" }}>Cargando páginas del proyecto…</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="screen is-active" id="screen-analysis-list">
        <div className="page-head">
          <div>
            <span className="eyebrow">03 // Analysis</span>
            <h1 className="h1">Análisis de Página</h1>
          </div>
        </div>
        <div className="panel-box" style={{ textAlign: "center", padding: "64px 24px" }}>
          <span className="eyebrow">Selecciona una página</span>
          <h2 className="h1">{error}</h2>
          <p style={{ color: "var(--ink-muted)", maxWidth: 440, margin: "0 auto 24px" }}>
            Primero sube una página desde Upload, luego podrás analizarla aquí.
          </p>
          <button type="button" className="btn btn-vermilion" onClick={() => navigate("/upload")}>
            Ir a Upload
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="screen is-active" id="screen-analysis-list">
      <div className="page-head">
        <div>
          <span className="eyebrow">03 // Analysis</span>
          <h1 className="h1">Seleccionar Página</h1>
        </div>
      </div>

      {pages.length === 0 && (
        <div className="panel-box" style={{ textAlign: "center", padding: "64px 24px" }}>
          <span className="eyebrow">Sin Páginas</span>
          <h2 className="h1">No hay páginas subidas aún.</h2>
          <p style={{ color: "var(--ink-muted)", maxWidth: 440, margin: "0 auto 24px" }}>
            Sube una página desde Upload para poder analizarla.
          </p>
          <button type="button" className="btn btn-vermilion" onClick={() => navigate("/upload")}>
            Ir a Upload
          </button>
        </div>
      )}

      {pages.length > 0 && (
        <div className="grid-3" id="pagesGrid">
          {pages.map((page) => (
            <article key={page.id} className="project-card" onClick={() => navigate(`/analysis/${page.id}`)}>
              <div className="project-thumb">
                <svg viewBox="0 0 300 400" preserveAspectRatio="xMidYMid slice">
                  <rect width="300" height="400" fill="#fff" />
                  <rect x="16" y="16" width="268" height="120" fill="#efece4" stroke="#111" strokeWidth="2" />
                  <rect x="16" y="148" width="268" height="236" fill="#efece4" stroke="#111" strokeWidth="2" />
                  <path d="M0 150 L70 95 L140 130 L230 80 L320 135 L320 200 L0 200 Z" fill="#111111" />
                </svg>
                <span className="exhibit-pill">
                  <span className="on-ink">Original Ink</span>
                  <span className="on-color">SUMI Color</span>
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong>{page.nombre_archivo_original}</strong>
                <span className="badge badge-review">{page.estado}</span>
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "var(--ink-muted)" }}>
                {page.hash_sha256?.slice(0, 16)}…
              </div>
              <button type="button" className="btn btn-outline btn-sm" onClick={(ev) => {
                ev.stopPropagation();
                navigate(`/analysis/${page.id}`);
              }}>
                Analizar →
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
