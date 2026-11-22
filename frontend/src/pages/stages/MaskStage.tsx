import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../api/client";

export function MaskStage({ onComplete }: { onComplete?: () => void }) {
  const { id: projectId = "" } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [masks, setMasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [replacementFiles, setReplacementFiles] = useState<Record<string, File | null>>({});
  const [imageUrls, setImageUrls] = useState<Record<string, string>>({});
  const urlsRef = useRef<string[]>([]);

  const load = async () => {
    const project = await api.getProject(projectId);
    const analysisId = project.pages?.find(p => p.analysis_id)?.analysis_id;
    if (!analysisId) throw new Error("Primero debes ejecutar el análisis de la página.");
    const items = await api.getAnalysisMasks(analysisId);
    urlsRef.current.forEach(url => URL.revokeObjectURL(url));
    urlsRef.current = [];
    const failed: string[] = [];
    const entries = await Promise.all(items.map(async (mask: any) => {
      try { const blob = await api.downloadMask(mask.id); const url = URL.createObjectURL(blob); urlsRef.current.push(url); return [mask.id, url] as const; }
      catch (err) { failed.push(mask.id); return [mask.id, ""] as const; }
    }));
    if (failed.length) setError(prev => prev ? prev + ` | ${failed.length} máscara(s) no se pudieron descargar` : `${failed.length} máscara(s) no se pudieron descargar (verifica que el backend esté en http://localhost:8000 y que tengas sesión activa).`);
    setImageUrls(Object.fromEntries(entries));
    setMasks(items);
  };
  useEffect(() => { let cancelled = false; load().catch(err => { if (!cancelled) setError(err instanceof Error ? err.message : "No se pudieron cargar las máscaras."); }).finally(() => { if (!cancelled) setLoading(false); }); return () => { cancelled = true; urlsRef.current.forEach(url => URL.revokeObjectURL(url)); urlsRef.current = []; }; }, [projectId]);
  const markReviewed = async (appearanceId: string, maskId: string) => {
    const correction = (notes[maskId] || "Revisión manual confirmada").trim();
    if (!correction) return;
    try { await api.correctMask(appearanceId, { review_note: correction, reviewed_at: new Date().toISOString() }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "No se pudo guardar la revisión."); }
  };
  if (loading) return <p>Cargando máscaras…</p>;
  return <section className="screen is-active">
    <div className="page-head"><div><span className="eyebrow">4. Mask</span><h1 className="h1">Máscaras</h1><p style={{ color: "var(--ink-muted)" }}>Consulta las máscaras generadas y registra las correcciones o revisiones por aparición.</p></div></div>
    {error && <p role="alert" style={{ color: "#c0392b" }}>{error}</p>}
    {!masks.length && <div className="panel-box">No hay máscaras asociadas al análisis. Vuelve a ejecutar el análisis o revisa el resultado de segmentación.</div>}
    {masks.map(mask => <article className="panel-box" key={mask.id} style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}><div><h3>{mask.tipo_mascara}</h3><p style={{ color: "var(--ink-muted)", fontSize: "0.85rem" }}>Aparición: {mask.appearance_id.slice(0, 8)}… · Versión {mask.version} · SHA-256 {mask.hash_sha256.slice(0, 12)}…</p></div><span className={mask.corregido ? "badge badge-done" : "badge badge-running"}>{mask.corregido ? "Revisada" : "Pendiente de revisión"}</span></div>
      {imageUrls[mask.id] && <img src={imageUrls[mask.id]} alt={`Máscara ${mask.tipo_mascara}`} style={{ display: "block", maxWidth: "100%", maxHeight: 280, objectFit: "contain", margin: "12px 0", border: "1px solid var(--border)" }} />}
      <label style={{ display: "block", marginTop: 10 }}>Reemplazar archivo de máscara<input type="file" accept="image/png,image/jpeg,image/webp" onChange={e => setReplacementFiles(v => ({ ...v, [mask.id]: e.target.files?.[0] || null }))} style={{ display: "block", marginTop: 6 }} /></label>
      <button className="btn btn-outline btn-sm" disabled={!replacementFiles[mask.id]} style={{ marginTop: 8 }} onClick={async () => { const file = replacementFiles[mask.id]; if (!file) return; try { await api.replaceMask(mask.appearance_id, file); setReplacementFiles(v => ({ ...v, [mask.id]: null })); await load(); } catch (err) { setError(err instanceof Error ? err.message : "No se pudo reemplazar la máscara."); } }}>Reemplazar máscara</button>
      <label style={{ display: "block", marginTop: 10 }}>Nota / corrección<input value={notes[mask.id] ?? ""} onChange={e => setNotes(v => ({ ...v, [mask.id]: e.target.value }))} placeholder="Describe el ajuste o confirma la revisión" style={{ width: "100%", marginTop: 6 }} /></label>
      <button className="btn btn-vermilion btn-sm" style={{ marginTop: 10 }} onClick={() => markReviewed(mask.appearance_id, mask.id)}>{mask.corregido ? "Guardar nueva revisión" : "Guardar revisión"}</button>
      {mask.correcciones && <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.8rem", marginTop: 10 }}>{JSON.stringify(mask.correcciones, null, 2)}</pre>}
    </article>)}
    <button className="btn btn-outline" onClick={() => navigate(`/projects/${projectId}/character`)}>Volver a personajes</button>
    <button className="btn btn-vermilion" style={{ marginLeft: 8 }} onClick={() => onComplete?.()}>Guardar y continuar a aprobación →</button>
  </section>;
}
