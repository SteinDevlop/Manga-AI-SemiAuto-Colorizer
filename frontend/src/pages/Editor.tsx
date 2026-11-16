/** Character and palette editor: review attributes, palettes, and approve suggestions. */

import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Character, CharacterAttribute, CharacterPalette } from "../types";

const ATTRIBUTE_NAMES = ["skin", "hair", "eyes", "clothing", "accessories"] as const;

const PALETTE_COLORS = [
  { name: "color_base", label: "Base color" },
  { name: "sombras", label: "Shadows" },
  { name: "luces", label: "Lights" },
] as const;

type AttributeRow = CharacterAttribute & {
  suggestedValue: string;
  uncertainty: number;
};

type PaletteRow = CharacterPalette & {
  hexValue: string;
};

export function Editor(): JSX.Element {
  const { characterId } = useParams<{ characterId: string }>();
  const [character, setCharacter] = useState<Character | null>(null);
  const [attributes, setAttributes] = useState<AttributeRow[]>([]);
  const [palettes, setPalettes] = useState<PaletteRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!characterId) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.get<Character>(`/characters/${characterId}`)
      .then((data) => {
        if (!cancelled) {
          setCharacter(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load character.");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [characterId]);

  const initializeRows = (): void {
    if (!character) return;
    const attributeRows: AttributeRow[] = ATTRIBUTE_NAMES.map((name) => ({
      id: "",
      character_id: character.id,
      nombre_atributo: name,
      valor_sugerido: undefined,
      valor_aprobado: undefined,
      esta_aprobado: false,
      confianza_sugerencia: undefined,
      suggestedValue: "",
      uncertainty: 0,
    }));
    const paletteRows: PaletteRow[] = PALETTE_COLORS.map((color) => ({
      id: "",
      character_id: character.id,
      nombre_color: color.name,
      valor_hex: undefined,
      esta_aprobado: false,
      hexValue: "",
    }));
    setAttributes(attributeRows);
    setPalettes(paletteRows);
  };

  useEffect(() => {
    if (character) {
      initializeRows();
    }
  }, [character]);

  const isSaving = (key: string): boolean => saving.has(key);

  const handleAttributeChange = (
    row: AttributeRow,
    event: React.ChangeEvent<HTMLInputElement>,
  ): void => {
    const updated = { ...row, valor_aprobado: event.target.value };
    setAttributes((current) =>
      current.map((r) =>
        r.nombre_atributo === row.nombre_atributo ? updated : r,
      ),
    );
  };

  const handlePaletteChange = (
    row: PaletteRow,
    event: React.ChangeEvent<HTMLInputElement>,
  ): void => {
    const updated = { ...row, valor_hex: event.target.value };
    setPalettes((current) =>
      current.map((r) => (r.nombre_color === row.nombre_color ? updated : r)),
    );
  };

  const handleApproveAttribute = async (row: AttributeRow): Promise<void> => {
    if (!row.valor_sugerido) {
      setError("Nothing to approve: no suggested value.");
      return;
    }
    const key = `attribute:${row.nombre_atributo}`;
    setSaving((current) => new Set([...current, key]));
    setError(null);
    try {
      await api.patch<CharacterAttribute>(
        `/characters/${characterId}/attributes/${row.nombre_atributo}/approve`,
        {},
      );
      setAttributes((current) =>
        current.map((r) =>
          r.nombre_atributo === row.nombre_atributo
            ? { ...r, valor_aprobado: r.valor_sugerido, esta_aprobado: true }
            : r,
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to approve attribute.",
      );
    } finally {
      setSaving((current) => {
        const next = new Set(current);
        next.delete(key);
        return next;
      });
    }
  };

  const handleApprovePalette = async (row: PaletteRow): Promise<void> => {
    if (!row.valor_hex) {
      setError("Nothing to approve: no color value.");
      return;
    }
    const key = `palette:${row.nombre_color}`;
    setSaving((current) => new Set([...current, key]));
    setError(null);
    try {
      await api.patch<CharacterPalette>(
        `/characters/${characterId}/palettes/${row.nombre_color}/approve`,
        {},
      );
      setPalettes((current) =>
        current.map((r) =>
          r.nombre_color === row.nombre_color
            ? { ...r, valor_hex: row.valor_hex, esta_aprobado: true }
            : r,
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to approve palette color.",
      );
    } finally {
      setSaving((current) => {
        const next = new Set(current);
        next.delete(key);
        return next;
      });
    }
  };

  if (loading) {
    return (
      <div className="page editor">
        <h1>Character editor</h1>
        <p>Loading character...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page editor">
        <h1>Character editor</h1>
        <div className="alert alert-error">{error}</div>
      </div>
    );
  }

  if (!character) {
    return (
      <div className="page editor">
        <h1>Character editor</h1>
        <p>No character data available.</p>
      </div>
    );
  }

  return (
    <div className="page editor">
      <h1>Character editor</h1>
      <p className="meta">
        Character {character.nombre} &middot; {character.id}
      </p>

      <section className="editor-attributes">
        <h2>Attributes</h2>
        {attributes.length === 0 ? (
          <p>No attributes configured.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Attribute</th>
                <th>Suggested value</th>
                <th>Uncertainty</th>
                <th>Approved value</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {attributes.map((row) => (
                <tr key={row.nombre_atributo}>
                  <td>{row.nombre_atributo}</td>
                  <td>
                    {row.valor_sugerido ?? "-"}
                    {row.confianza_sugerencia !== undefined && row.confianza_sugerencia !== null ? (
                      <span className="uncertainty">
                        &middot; {(row.confianza_sugerencia * 100).toFixed(0)}% confidence
                      </span>
                    ) : null}
                  </td>
                  <td>
                    {row.confianza_sugerencia !== undefined && row.confianza_sugerencia !== null ? (
                      <span className="uncertainty">
                        {(row.confianza_sugerencia * 100).toFixed(0)}%
                      </span>
                    ) : "-"}
                  </td>
                  <td>
                    <input
                      type="text"
                      value={row.valor_aprobado ?? ""}
                      onChange={(event) => handleAttributeChange(row, event)}
                      disabled={isSaving(`attribute:${row.nombre_atributo}`)}
                      placeholder="Enter approved value"
                    />
                  </td>
                  <td>
                    <button
                      type="button"
                      onClick={() => handleApproveAttribute(row)}
                      disabled={
                        isSaving(`attribute:${row.nombre_atributo}`) || !row.valor_sugerido
                      }
                    >
                      Approve
                    </button>
                    {row.esta_aprobado && <span className="approved-tag">Approved</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="editor-palette">
        <h2>Color palette</h2>
        {palettes.length === 0 ? (
          <p>No palette colors configured.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Color</th>
                <th>Suggested hex</th>
                <th>Approved hex</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {palettes.map((row) => {
                const colorDef = PALETTE_COLORS.find((c) => c.name === row.nombre_color);
                return (
                  <tr key={row.nombre_color}>
                    <td>
                      {colorDef ? colorDef.label : row.nombre_color}
                    </td>
                    <td>
                      {row.valor_hex ?? "-"}
                    </td>
                    <td>
                      <div className="color-input-row">
                        <input
                          type="color"
                          value={row.valor_hex ?? "#ffffff"}
                          onChange={(event) => handlePaletteChange(row, event)}
                          disabled={isSaving(`palette:${row.nombre_color}`)}
                        />
                        <input
                          type="text"
                          value={row.valor_hex ?? ""}
                          onChange={(event) => handlePaletteChange(row, event)}
                          disabled={isSaving(`palette:${row.nombre_color}`)}
                          maxLength={7}
                          placeholder="#ffffff"
                        />
                      </div>
                    </td>
                    <td>
                      <button
                        type="button"
                        onClick={() => handleApprovePalette(row)}
                        disabled={
                          isSaving(`palette:${row.nombre_color}`) || !row.valor_hex
                        }
                      >
                        Approve
                      </button>
                      {row.esta_aprobado && <span className="approved-tag">Approved</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
