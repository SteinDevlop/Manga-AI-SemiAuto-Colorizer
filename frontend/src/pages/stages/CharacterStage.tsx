import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../api/client";

async function buildAppearancePreview(blob: Blob, panel?: { x: number; y: number; ancho: number; alto: number }): Promise<string> {
  if (!panel || typeof createImageBitmap === "undefined") return URL.createObjectURL(blob);
  try {
    const bitmap = await createImageBitmap(blob);
    const x = Math.max(0, Math.min(bitmap.width - 1, Math.round(panel.x)));
    const y = Math.max(0, Math.min(bitmap.height - 1, Math.round(panel.y)));
    const width = Math.max(1, Math.min(bitmap.width - x, Math.round(panel.ancho)));
    const height = Math.max(1, Math.min(bitmap.height - y, Math.round(panel.alto)));
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("Canvas no disponible");
    context.drawImage(bitmap, x, y, width, height, 0, 0, width, height);
    bitmap.close();
    const cropped = await new Promise<Blob>((resolve, reject) =>
      canvas.toBlob(value => value ? resolve(value) : reject(new Error("No se pudo generar la vista previa")), "image/png")
    );
    return URL.createObjectURL(cropped);
  } catch {
    return URL.createObjectURL(blob);
  }
}

export function CharacterStage({ onComplete }: { onComplete?: () => void }) {
  const { id: projectId = "" } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [characters, setCharacters] = useState<any[]>([]);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [newNames, setNewNames] = useState<Record<string, string>>({});
  const [newPaletteNames, setNewPaletteNames] = useState<Record<string, string>>({});
  const [newReferences, setNewReferences] = useState<Record<string, string>>({});
  const [identitySelections, setIdentitySelections] = useState<Record<string, string>>({});
  const [pageImages, setPageImages] = useState<Record<string, string>>({});
  const pageImageUrlsRef = useRef<string[]>([]);

  useEffect(() => {
    let cancelled = false;
    api.getProject(projectId).then(async project => {
      const currentAnalysisId = project.pages?.find(p => p.analysis_id)?.analysis_id;
      if (!currentAnalysisId) throw new Error("Primero debes ejecutar el análisis de la página.");
      const [data, analysisData] = await Promise.all([
        api.getAnalysisCharacters(currentAnalysisId),
        api.getAnalysis(currentAnalysisId),
      ]);
      const panelById = new Map<string, any>((analysisData.panels ?? []).map((panel: any) => [panel.id, panel]));
      const pageIds: string[] = Array.from(new Set<string>(
        data.flatMap((character: any) => (character.appearances ?? []).map((a: any) => String(a.page_id)))
      ));
      const pageBlobs = new Map<string, Blob>();
      await Promise.all(pageIds.map(async pageId => {
        try { pageBlobs.set(pageId, await api.downloadPage(pageId)); } catch { /* Preview opcional */ }
      }));
      const appearanceEntries = data.flatMap((character: any) => (character.appearances ?? []).map((appearance: any) => ({ appearance, panel: panelById.get(appearance.panel_id) })));
      const previews = await Promise.all(appearanceEntries.map(async ({ appearance, panel }: any) => {
        const blob = pageBlobs.get(appearance.page_id);
        if (!blob) return [appearance.id, ""] as const;
        try { return [appearance.id, await buildAppearancePreview(blob, panel)] as const; }
        catch { return [appearance.id, ""] as const; }
      }));
      if (!cancelled) {
        pageImageUrlsRef.current.forEach(url => URL.revokeObjectURL(url));
        pageImageUrlsRef.current = previews.map(([, url]) => url).filter(Boolean);
        setAnalysisId(currentAnalysisId);
        setCharacters(data);
        setPageImages(Object.fromEntries(previews));
      } else {
        previews.forEach(([, url]) => { if (url) URL.revokeObjectURL(url); });
      }
    }).catch(err => { if (!cancelled) setError(err instanceof Error ? err.message : "No se pudieron cargar los personajes."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => {
      cancelled = true;
      pageImageUrlsRef.current.forEach(url => URL.revokeObjectURL(url));
      pageImageUrlsRef.current = [];
    };
  }, [projectId]);

  const reload = async () => {
    const project = await api.getProject(projectId);
    const currentAnalysisId = project.pages?.find(p => p.analysis_id)?.analysis_id;
    if (currentAnalysisId) { setAnalysisId(currentAnalysisId); setCharacters(await api.getAnalysisCharacters(currentAnalysisId)); }
  };
  const saveAttribute = async (characterId: string, name: string, current: string) => {
    const value = drafts[`${characterId}:${name}`] ?? current;
    try { await api.updateCharacterAttribute(characterId, name, value); await reload(); }
    catch (err) { setError(err instanceof Error ? err.message : "No se pudo guardar el atributo."); }
  };
  const approve = async (characterId: string, name: string) => {
    try { await api.approveCharacterAttribute(characterId, name); await reload(); }
    catch (err) { setError(err instanceof Error ? err.message : "No se pudo aprobar el atributo."); }
  };

  if (loading) return <p>Cargando personajes…</p>;
  return <section className="screen is-active">
    <div className="page-head"><div><span className="eyebrow">3. Character</span><h1 className="h1">Personajes</h1><p style={{ color: "var(--ink-muted)" }}>Revisa las identidades detectadas y define atributos cromáticos. Las sugerencias no son colores oficiales hasta que las apruebes.</p></div></div>
    {error && <p role="alert" style={{ color: "#c0392b" }}>{error}</p>}
    {analysisId && <div style={{ marginBottom: 16 }}><button className="btn btn-outline" disabled={characters.length <= 1} onClick={async () => { try { await api.groupAnalysisIdentities(analysisId); await reload(); } catch (err) { setError(err instanceof Error ? err.message : "No se pudieron agrupar las identidades."); } }}>Agrupar identidades detectadas</button><p style={{ color: "var(--ink-muted)", fontSize: "0.8rem", marginTop: 6 }}>El matcher actual es de prueba y agrupa las apariciones en una identidad sugerida; revisa el resultado antes de continuar.</p></div>}
    {!characters.length && !error && <div className="panel-box">El análisis no detectó personajes para esta página.</div>}
    {characters.map(character => <article className="panel-box" key={character.id} style={{ marginBottom: 16 }}>
      <h2>{character.nombre}</h2><p style={{ color: "var(--ink-muted)" }}>{character.descripcion || "Sin descripción"} · {character.appearances.length} aparición(es)</p>
      {character.appearances.map((appearance: any) => <div key={appearance.id} style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", margin: "6px 0" }}><span style={{ fontSize: "0.82rem" }}>Aparición {appearance.id.slice(0, 8)}…</span>
        {pageImages[appearance.id] && <img src={pageImages[appearance.id]} alt={`Referencia visual de ${character.nombre}`} loading="lazy" style={{ width: 112, height: 150, objectFit: "contain", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />}
        <select aria-label={`Identidad para ${appearance.id}`} value={identitySelections[appearance.id] || character.id} onChange={e => setIdentitySelections(v => ({ ...v, [appearance.id]: e.target.value }))}>{characters.map(option => <option key={option.id} value={option.id}>{option.nombre}</option>)}</select><button className="btn btn-outline btn-sm" disabled={(identitySelections[appearance.id] || character.id) === character.id} onClick={async () => { try { await api.reviewIdentity(appearance.id, identitySelections[appearance.id]); await reload(); } catch (err) { setError(err instanceof Error ? err.message : "No se pudo corregir la identidad."); } }}>Cambiar identidad</button></div>)}
      <div style={{ display: "flex", gap: 8, margin: "10px 0 16px" }}><input aria-label={`Referencia estable ${character.nombre}`} placeholder="Referencia estable (ruta o identificador)" value={newReferences[character.id] || ""} onChange={e => setNewReferences(v => ({ ...v, [character.id]: e.target.value }))} /><button className="btn btn-outline btn-sm" onClick={async () => { const ref = (newReferences[character.id] || "").trim(); if (!ref) return; try { await api.addCharacterReference(character.id, ref); setNewReferences(v => ({ ...v, [character.id]: "" })); } catch (err) { setError(err instanceof Error ? err.message : "No se pudo guardar la referencia."); } }}>Guardar referencia</button></div>
      <h3>Atributos</h3>
      {character.attributes.map((attribute: any) => <div key={attribute.id} style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginBottom: 8 }}>
        <strong style={{ minWidth: 110 }}>{attribute.nombre_atributo}</strong>
        <input aria-label={`Valor ${attribute.nombre_atributo}`} value={drafts[`${character.id}:${attribute.nombre_atributo}`] ?? attribute.valor_sugerido ?? ""} onChange={e => setDrafts(v => ({ ...v, [`${character.id}:${attribute.nombre_atributo}`]: e.target.value }))} />
        <button className="btn btn-outline btn-sm" onClick={() => saveAttribute(character.id, attribute.nombre_atributo, attribute.valor_sugerido || "")}>Guardar</button>
        <button className="btn btn-vermilion btn-sm" disabled={!attribute.valor_sugerido} onClick={() => approve(character.id, attribute.nombre_atributo)}>{attribute.esta_aprobado ? "Aprobado" : "Aprobar"}</button>
      </div>)}
      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <input aria-label={`Nuevo atributo ${character.nombre}`} placeholder="Nuevo atributo (ej. cabello)" value={newNames[character.id] || ""} onChange={e => setNewNames(v => ({ ...v, [character.id]: e.target.value }))} />
        <button className="btn btn-outline btn-sm" onClick={async () => { const name = (newNames[character.id] || "").trim(); if (!name) return; try { await api.updateCharacterAttribute(character.id, name, "Por definir"); setNewNames(v => ({ ...v, [character.id]: "" })); await reload(); } catch (err) { setError(err instanceof Error ? err.message : "No se pudo crear el atributo."); } }}>Agregar</button>
      </div>
      {character.palettes.length > 0 && <><h3 style={{ marginTop: 18 }}>Paleta</h3><div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>{character.palettes.map((palette: any) => <div key={palette.id} style={{ display: "flex", gap: 6, alignItems: "center" }}><label>{palette.nombre_color}<input aria-label={`Color ${palette.nombre_color}`} type="color" value={palette.valor_hex || "#808080"} onChange={async e => { try { await api.updateCharacterPalette(character.id, palette.nombre_color, e.target.value); await reload(); } catch (err) { setError(err instanceof Error ? err.message : "No se pudo actualizar la paleta."); } }} /></label><button className="btn btn-outline btn-sm" disabled={!palette.valor_hex} onClick={async () => { try { await api.approveCharacterPalette(character.id, palette.nombre_color); await reload(); } catch (err) { setError(err instanceof Error ? err.message : "No se pudo aprobar el color."); } }}>{palette.esta_aprobado ? "Aprobado" : "Aprobar color"}</button></div>)}</div></>}
      <div style={{ display: "flex", gap: 8, marginTop: 12 }}><input aria-label={`Nueva entrada de paleta ${character.nombre}`} placeholder="Nuevo color (ej. cabello)" value={newPaletteNames[character.id] || ""} onChange={e => setNewPaletteNames(v => ({ ...v, [character.id]: e.target.value }))} /><button className="btn btn-outline btn-sm" onClick={async () => { const name = (newPaletteNames[character.id] || "").trim(); if (!name) return; try { await api.updateCharacterPalette(character.id, name, "#808080"); setNewPaletteNames(v => ({ ...v, [character.id]: "" })); await reload(); } catch (err) { setError(err instanceof Error ? err.message : "No se pudo crear el color."); } }}>Agregar color</button></div>
    </article>)}
    <button className="btn btn-outline" onClick={() => navigate(`/projects/${projectId}/analysis`)}>Volver a análisis</button>
    <button className="btn btn-vermilion" style={{ marginLeft: 8 }} onClick={() => onComplete?.()}>Guardar y continuar a máscaras →</button>
  </section>;
}
