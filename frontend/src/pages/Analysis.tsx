/** Analysis screen: page image, detected panels, characters, and proposed masks. */

import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Analysis } from "../types";

type Panel = {
  id: string;
  page_id: string;
  numero_orden: number;
  x: number;
  y: number;
  ancho: number;
  alto: number;
  confianza_deteccion: number | null;
};

type Character = {
  id: string;
  nombre: string;
  descripcion: string | null;
  confianza_identidad: number | null;
};

type Appearance = {
  id: string;
  page_id: string;
  character_id: string;
  panel_id: string | null;
  confianza_deteccion: number | null;
};

type Mask = {
  id: string;
  appearance_id: string;
  tipo_mascara: string;
  ruta_archivo: string;
  hash_sha256: string;
  ancho: number | null;
  alto: number | null;
};

type AnalysisDetail = Analysis & {
  panels: Panel[];
  characters: Character[];
  appearances: Appearance[];
  masks: Mask[];
};

export function Analysis(): JSX.Element {
  const { analysisId } = useParams<{ analysisId: string }>();
  const [analysis, setAnalysis] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!analysisId) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.get<AnalysisDetail>(`/analyses/${analysisId}`)
      .then((data) => {
        if (!cancelled) {
          setAnalysis(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load analysis.");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [analysisId]);

  const appearancesByCharacter = (characterId: string): Appearance[] =>
    (analysis?.appearances ?? []).filter((a) => a.character_id === characterId);

  const masksByAppearance = (appearanceId: string): Mask[] =>
    (analysis?.masks ?? []).filter((m) => m.appearance_id === appearanceId);

  const panelStyle = (panel: Panel): React.CSSProperties => ({
    position: "absolute",
    left: panel.x * 100,
    top: panel.y * 100,
    width: panel.ancho * 100,
    height: panel.alto * 100,
    border: "2px solid #38bdf8",
    boxSizing: "border-box",
  });

  if (loading) {
    return (
      <div className="page analysis">
        <h1>Analysis</h1>
        <p>Loading analysis...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page analysis">
        <h1>Analysis</h1>
        <div className="alert alert-error">{error}</div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="page analysis">
        <h1>Analysis</h1>
        <p>No analysis data available.</p>
      </div>
    );
  }

  return (
    <div className="page analysis">
      <h1>Page analysis</h1>
      <p className="meta">
        Analysis {analysis.id} &middot; Page {analysis.page_id} &middot;
        Status: {analysis.estado}
      </p>

      <section className="analysis-image">
        <h2>Page image</h2>
        <div className="image-frame">
          <img
            src={`/api/v1/pages/${analysis.page_id}/image`}
            alt="Page image"
            style={{ maxWidth: "100%", height: "auto", display: "block" }}
          />
          {analysis.panels.map((panel) => (
            <div
              key={panel.id}
              className="panel-overlay"
              style={panelStyle(panel)}
              title={`Panel ${panel.numero_orden}`}
            >
              <span className="panel-order">{panel.numero_orden}</span>
              <span className="panel-confidence">
                {(panel.confianza_deteccion ?? 0) * 100}%
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className="analysis-characters">
        <h2>Detected characters</h2>
        {analysis.characters.length === 0 ? (
          <p>No characters detected.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Identity confidence</th>
                <th>Appearances</th>
              </tr>
            </thead>
            <tbody>
              {analysis.characters.map((character) => (
                <tr key={character.id}>
                  <td>{character.nombre}</td>
                  <td>
                    {(character.confianza_identidad ?? 0) * 100}%
                  </td>
                  <td>
                    {appearancesByCharacter(character.id).map((appearance) => (
                      <div key={appearance.id} className="appearance-chip">
                        Panel {appearance.panel_id ?? "-"} &middot;
                        {(appearance.confianza_deteccion ?? 0) * 100}%
                      </div>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="analysis-masks">
        <h2>Proposed masks</h2>
        {analysis.masks.length === 0 ? (
          <p>No masks proposed.</p>
        ) : (
          <div className="mask-grid">
            {analysis.masks.map((mask) => (
              <div key={mask.id} className="mask-card">
                <img
                  src={`/api/v1/artifacts/${mask.id}/preview`}
                  alt={`Mask ${mask.tipo_mascara}`}
                  className="mask-thumb"
                />
                <div className="mask-info">
                  <p className="mask-type">{mask.tipo_mascara}</p>
                  <p className="mask-dimensions">
                    {mask.ancho ?? "-"} x {mask.alto ?? "-"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
