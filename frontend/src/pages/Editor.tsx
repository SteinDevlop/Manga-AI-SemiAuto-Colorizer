/* SUMI Character & Color Editor — edita atributos y paletas de un análisis. */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, API_BASE } from "../api/client";
import type { Character, CharacterAttribute, CharacterAppearance } from "../types";

export default function Editor() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

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

  const handleSave = async (characterId: string, attributeName: string, value: string) => {
    setSaving(true);
    try {
      await api.patch<any>(`/characters/${characterId}/attributes/${attributeName}`, { valor_aprobado: value });
    } catch (err) {
      console.warn("Attribute update endpoint not available yet:", err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <section className="screen is-active" id="screen-characters">
        <div className="page-head">
          <div>
            <span className="eyebrow">04 // Character & Color</span>
            <h1 className="h1">Loading editor…</h1>
          </div>
        </div>
        <p style={{ color: "var(--ink-muted)" }}>Loading character data…</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="screen is-active" id="screen-characters">
        <div className="page-head">
          <div>
            <span className="eyebrow">04 // Character & Color</span>
            <h1 className="h1">Editor</h1>
          </div>
        </div>
        <p style={{ color: "#c0392b" }}>{error}</p>
        <button type="button" className="btn btn-vermilion" onClick={() => navigate("/projects")}>
          Back to Projects
        </button>
      </section>
    );
  }

  if (!analysis) {
    return (
      <section className="screen is-active" id="screen-characters">
        <div className="page-head">
          <div>
            <span className="eyebrow">04 // Character & Color</span>
            <h1 className="h1">Editor</h1>
          </div>
        </div>
        <p>No analysis data available.</p>
        <button type="button" className="btn btn-vermilion" onClick={() => navigate("/projects")}>
          Back to Projects
        </button>
      </section>
    );
  }

  const characters = analysis.characters || [];
  const appearances = analysis.appearances || [];

  return (
    <section className="screen is-active" id="screen-characters">
      <div className="page-head">
        <div>
          <span className="eyebrow">04 // Character & Color</span>
          <h1 className="h1">Character Editor — Analysis {(analysisId ?? "").slice(0, 8)}…</h1>
        </div>
        <button type="button" className="btn btn-outline btn-sm" onClick={() => navigate("/projects")}>
          ← Back to Projects
        </button>
      </div>

      {characters.length === 0 ? (
        <div className="panel-box" style={{ textAlign: "center", padding: "64px 24px" }}>
          <span className="eyebrow">No Characters</span>
          <h2 className="h1">No characters detected in this analysis.</h2>
          <p style={{ color: "var(--ink-muted)", maxWidth: 440, margin: "0 auto 24px" }}>
            Run analysis on a page first to detect characters and their attributes.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {characters.map((character: Character) => {
            const charAppearances = appearances.filter((a: CharacterAppearance) => a.character_id === character.id);
            return (
              <div key={character.id} className="panel-box" style={{ marginBottom: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <div>
                    <strong>{character.nombre}</strong>
                    <span className="mono-label">{character.id.slice(0, 8)}…</span>
                  </div>
                  <span className={`badge ${character.confianza_identidad && character.confianza_identidad > 0.8 ? "badge-done" : "badge-review"}`}>
                    {(character.confianza_identidad ?? 0).toFixed(2)} confidence
                  </span>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 12 }}>
                  {character.attributes?.map((attr: CharacterAttribute) => (
                    <div key={attr.id} style={{ border: "1px solid var(--border)", borderRadius: 6, padding: 12, background: "#1e293b" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                        <strong>{attr.nombre_atributo}</strong>
                        <span className={`badge ${attr.esta_aprobado ? "badge-done" : "badge-review"}`}>
                          {attr.esta_aprobado ? "Approved" : "Pending"}
                        </span>
                      </div>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <input
                          type="text"
                          value={attr.valor_aprobado ?? attr.valor_sugerido ?? ""}
                          onChange={(e) => handleSave(character.id, attr.nombre_atributo, e.target.value)}
                          placeholder={attr.valor_sugerido ?? "n/a"}
                          disabled={attr.esta_aprobado}
                          style={{ flex: 1, padding: "6px 10px", border: "1px solid var(--border)", borderRadius: 4, background: "#0f172a", color: "#fff" }}
                        />
                        <span className="mono-label">{attr.valor_sugerido ?? "n/a"}</span>
                      </div>
                    </div>
                  ))}
                  {!character.attributes || character.attributes.length === 0 && (
                    <div style={{ gridColumn: "1 / -1", textAlign: "center", color: "var(--ink-muted)", fontSize: "0.85rem" }}>
                      No attributes detected for this character.
                    </div>
                  )}
                </div>

                {charAppearances.length > 0 && (
                  <div style={{ marginTop: 12, borderTop: "1px solid var(--border)", paddingTop: 12 }}>
                    <span className="eyebrow">Appearances ({charAppearances.length})</span>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 6 }}>
                      {charAppearances.map((appearance: CharacterAppearance) => (
                        <div key={appearance.id} style={{ padding: 8, background: "#0f172a", borderRadius: 4, fontSize: "0.85rem", color: "var(--ink-muted)" }}>
                          Appearance {appearance.id.slice(0, 8)}…{appearance.panel_id ? ` · Panel ${appearance.panel_id.slice(0, 8)}…` : ""}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
