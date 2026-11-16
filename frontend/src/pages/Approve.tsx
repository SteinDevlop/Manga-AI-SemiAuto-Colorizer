/** Pantalla de flujo de aprobación: revisar y aprobar el análisis antes de colorizar. */

import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Analysis, Character, CharacterAttribute, CharacterPalette } from "../types";

type CharacterDetail = Character & {
  attributes: CharacterAttribute[];
  palettes: CharacterPalette[];
};

type ApproveView = {
  analysis: Analysis | null;
  characters: CharacterDetail[];
  loading: boolean;
  error: string | null;
  approved: boolean;
};

const initialView: ApproveView = {
  analysis: null,
  characters: [],
  loading: true,
  error: null,
  approved: false,
};

export function Approve() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [view, setView] = useState<ApproveView>(initialView);

  const load = useCallback(async () => {
    if (!id) return;
    setView((v) => ({ ...v, loading: true, error: null }));
    try {
      const analysis = await api.get<Analysis>(`/analyses/${id}`);
      let characters: Character[] = [];
      try {
        characters = await api.get<Character[]>(`/analyses/${id}/characters`);
      } catch {
        // Endpoint may not exist yet in P7; render without character detail.
        characters = [];
      }
      setView({
        analysis,
        characters: characters.map((c) => ({ ...c, attributes: [], palettes: [] })),
        loading: false,
        error: null,
        approved: analysis.estado === "APPROVED",
      });
    } catch (err) {
      setView((v) => ({
        ...v,
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load analysis",
      }));
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleApprove = async () => {
    if (!id) return;
    setView((v) => ({ ...v, loading: true, error: null }));
    try {
      await api.post(`/analyses/${id}/approve`);
      setView((v) => ({
        ...v,
        loading: false,
        approved: true,
        analysis: v.analysis ? { ...v.analysis, estado: "APPROVED" } : null,
      }));
    } catch (err) {
      setView((v) => ({
        ...v,
        loading: false,
        error: err instanceof Error ? err.message : "Failed to approve analysis",
      }));
    }
  };

  const goToColorize = () => {
    if (!id || !view.approved) return;
    navigate(`/colorize/${id}`);
  };

  if (view.loading) {
    return (
      <div className="page approve" style={{ padding: 2 }}>
        <p>Loading analysis...</p>
      </div>
    );
  }

  if (view.error) {
    return (
      <div className="page approve" style={{ padding: 2 }}>
        <p>{view.error}</p>
      </div>
    );
  }

  const analysis = view.analysis;
  if (!analysis) {
    return (
      <div className="page approve" style={{ padding: 2 }}>
        <p>Analysis not found.</p>
      </div>
    );
  }

  return (
    <div className="page approve" style={{ padding: 2, maxWidth: 900 }}>
      <h1>Approve analysis</h1>
      <p>Review the detected characters, attributes and palettes before colorizing.</p>

      <section style={{ marginBottom: 1.5 }}>
        <h2>Analysis</h2>
        <p>Id: {analysis.id}</p>
        <p>Page: {analysis.page_id}</p>
        <p>Status: {analysis.estado}</p>
        <p>Confidence: {analysis.confianza_global ?? "n/a"}</p>
      </section>

      <section style={{ marginBottom: 1.5 }}>
        <h2>Characters</h2>
        {view.characters.length === 0 ? (
          <p>No characters detected.</p>
        ) : (
          view.characters.map((character) => (
            <article
              key={character.id}
              style={{
                border: "1px solid #334155",
                borderRadius: 0.5,
                padding: 1,
                marginBottom: 0.75,
                backgroundColor: "#1e293b",
              }}
            >
              <h3 style={{ margin: "0 0 0.5rem 0" }}>{character.nombre}</h3>
              <p>Confidence: {character.confianza_identidad ?? "n/a"}</p>

              <section style={{ marginTop: 0.75 }}>
                <h4>Attributes</h4>
                {character.attributes.length === 0 ? (
                  <p>No attributes.</p>
                ) : (
                  <ul style={{ paddingLeft: 1.2, margin: 0 }}>
                    {character.attributes.map((attr) => (
                      <li key={attr.id}>
                        {attr.nombre_atributo}: {attr.valor_sugerido ?? "n/a"}
                        <span
                          style={{
                            marginLeft: 0.5,
                            fontSize: 0.85,
                            padding: "0.1em 0.4em",
                            borderRadius: 0.25,
                            backgroundColor: attr.esta_aprobado ? "#166534" : "#454d5c",
                            color: "#ffffff",
                          }}
                        >
                          {attr.esta_aprobado ? "approved" : "pending"}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              <section style={{ marginTop: 0.75 }}>
                <h4>Palettes</h4>
                {character.palettes.length === 0 ? (
                  <p>No palettes.</p>
                ) : (
                  <ul style={{ paddingLeft: 1.2, margin: 0 }}>
                    {character.palettes.map((palette) => (
                      <li key={palette.id}>
                        {palette.nombre_color}: {palette.valor_hex ?? "n/a"}
                        <span
                          style={{
                            marginLeft: 0.5,
                            fontSize: 0.85,
                            padding: "0.1em 0.4em",
                            borderRadius: 0.25,
                            backgroundColor: palette.esta_aprobado ? "#166534" : "#454d5c",
                            color: "#ffffff",
                          }}
                        >
                          {palette.esta_aprobado ? "approved" : "pending"}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </article>
          ))
        )}
      </section>

      <div style={{ display: "flex", gap: 0.75, alignItems: "center" }}>
        <button
          onClick={handleApprove}
          disabled={view.loading || view.approved}
          style={{
            padding: "0.6rem 1.2rem",
            fontSize: 1,
            cursor: view.approved || view.loading ? "default" : "pointer",
            opacity: view.approved || view.loading ? 0.5 : 1,
          }}
        >
          {view.approved ? "Approved" : "Approve analysis"}
        </button>
        <button
          onClick={goToColorize}
          disabled={!view.approved}
          style={{
            padding: "0.6rem 1.2rem",
            fontSize: 1,
            cursor: !view.approved ? "default" : "pointer",
            opacity: !view.approved ? 0.5 : 1,
          }}
        >
          Go to colorization
        </button>
      </div>
    </div>
  );
}
