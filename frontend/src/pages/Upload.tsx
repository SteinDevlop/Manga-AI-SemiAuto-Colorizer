/* Etapa Upload dentro de un proyecto.
 *
 * Selecciona y sube la imagen original del proyecto, genera la miniatura de
 * portada (backend), marca la etapa Upload como completada y avanza a
 * Analysis. Upload no es retornable: una vez completada no se puede volver a
 * subir para ese proyecto.
 */
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { ProjectDetail } from "../components/ProjectLayout";

const ACCEPTED_MIME_TYPES = ["image/png", "image/jpeg", "image/webp"];
const MAX_UPLOAD_BYTES = 50 * 1024 * 1024; // 50 MB

type UploadStatus = "idle" | "uploading" | "done" | "error";

export function Upload() {
  const { id: projectIdParam } = useParams<{ id: string }>();
  const projectId = projectIdParam ?? "";
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api.getProject(projectId)
      .then((p) => {
        if (!cancelled) {
          setProject(p);
          // Si Upload ya está completada, no permite volver a subir.
          if (p.stage_progress.includes("upload")) {
            setStatus("done");
          }
        }
      })
      .catch(() => {
        if (!cancelled) setUploadError("No se pudo cargar el proyecto.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [projectId]);

  useEffect(() => {
    if (preview) return () => { URL.revokeObjectURL(preview); };
    return undefined;
  }, [preview]);

  // Restablecer scroll al entrar a la ruta.
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [projectId]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError(null);
    const selected = event.target.files?.[0] ?? null;
    setFile(selected);
    if (!selected) {
      setPreview(null);
      return;
    }
    if (!ACCEPTED_MIME_TYPES.includes(selected.type)) {
      setUploadError("Tipo de archivo no permitido. Use PNG, JPEG o WebP.");
      setPreview(null);
      setFile(null);
      return;
    }
    if (selected.size > MAX_UPLOAD_BYTES) {
      setUploadError(`El archivo excede ${MAX_UPLOAD_BYTES / (1024 * 1024)} MB.`);
      setPreview(null);
      setFile(null);
      return;
    }
    setPreview(URL.createObjectURL(selected as File));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setUploadError(null);
    setProgress(0);
    if (!file) {
      setUploadError("Selecciona una imagen para subir.");
      return;
    }
    if (!ACCEPTED_MIME_TYPES.includes(file.type)) {
      setUploadError("Tipo de archivo no permitido. Use PNG, JPEG o WebP.");
      return;
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setUploadError(`El archivo excede ${MAX_UPLOAD_BYTES / (1024 * 1024)} MB.`);
      return;
    }

    setStatus("uploading");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("project_id", projectId);

    // Indicador de progreso simulado durante la subida.
    let t = 0;
    const iv = setInterval(() => {
      t = Math.min(t + 12, 90);
      setProgress(t);
    }, 100);

    try {
      await api.uploadFile(formData);
      setProgress(100);
      // Marcar Upload como completada y avanzar a Analysis (Fase 1, defecto 0.9).
      await api.transitionStage(projectId, "complete", "upload");
      setStatus("done");
      navigate(`/projects/${projectId}/analysis`);
    } catch (err) {
      setStatus("error");
      setUploadError(
        err instanceof Error ? err.message : "Error al subir la página.",
      );
    } finally {
      clearInterval(iv);
      setProgress(0);
    }
  };

  const isUploadDone = status === "done" || (project?.stage_progress.includes("upload"));

  if (loading) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "var(--ink-muted)" }}>
        Cargando proyecto…
      </div>
    );
  }

  // Upload ya completada para este proyecto.
  if (isUploadDone && !file) {
    return (
      <section className="screen is-active" id="screen-upload">
        <div className="page-head">
          <div>
            <span className="eyebrow">1. Subida</span>
            <h1 className="h1">Subida completada</h1>
            <p style={{ color: "var(--ink-muted)", marginTop: 6 }}>
              La imagen ya fue subida y la etapa Upload está cumplida.
            </p>
          </div>
          <button
            type="button"
            className="btn-vermilion"
            onClick={() => navigate(`/projects/${projectId}/analysis`)}
          >
            Ir a Análisis
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="screen is-active" id="screen-upload">
      <div className="page-head">
        <div>
          <span className="eyebrow">1. Subida</span>
          <h1 className="h1">Sube la página del manga</h1>
          <p style={{ color: "var(--ink-muted)", marginTop: 6 }}>
            Selecciona la imagen original en blanco y negro. Se generará una
            miniatura como portada del proyecto.
          </p>
        </div>
      </div>

      {uploadError && (
        <div className="alert alert-error" role="alert">
          {uploadError}
          <button
            type="button"
            onClick={() => setUploadError(null)}
            style={{ marginLeft: 10, background: "none", border: "none", color: "inherit", cursor: "pointer" }}
          >
            ×
          </button>
        </div>
      )}

      <form className="form" onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14, maxWidth: 560 }}>
        <div className="form-field">
          <label htmlFor="page-file" style={{ display: "block", fontWeight: 600, marginBottom: 6 }}>
            Imagen original
          </label>
          <input
            id="page-file"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={handleFileChange}
            disabled={status === "uploading"}
          />
          {file && (
            <p style={{ fontSize: "0.82rem", color: "var(--ink-muted)", marginTop: 4 }}>
              {file.name} · {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          )}
          {preview && (
            <div style={{ marginTop: 10, border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden", background: "var(--surface)" }}>
              <img
                src={preview}
                alt="Vista previa"
                style={{
                  width: "100%",
                  maxHeight: 360,
                  objectFit: "contain",
                  display: "block",
                  margin: "0 auto",
                  background: "var(--surface)",
                }}
              />
            </div>
          )}
        </div>

        <div className="form-field">
          <label htmlFor="project-display" style={{ display: "block", fontWeight: 600, marginBottom: 6 }}>
            Proyecto
          </label>
          <div id="project-display" style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 14px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)", fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>
            {project?.nombre ?? projectId}
          </div>
        </div>

        {status === "uploading" && (
          <div className="form-field">
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", color: "var(--ink-muted)", marginBottom: 4 }}>
              <span>Subiendo…</span>
              <span>{progress}%</span>
            </div>
            <div style={{ height: 6, background: "var(--border)", borderRadius: 3, overflow: "hidden" }}>
              <div
                style={{ width: `${progress}%`, height: "100%", background: "var(--vermilion)" }}
              />
            </div>
          </div>
        )}

        <div className="form-actions">
          <button
            type="submit"
            disabled={status === "uploading" || !file || isUploadDone}
          >
            {status === "uploading"
              ? "Subiendo…"
              : isUploadDone
              ? "Ya subida"
              : "Subir página"}
          </button>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => {
              setFile(null);
              setPreview(null);
              setUploadError(null);
              setProgress(0);
            }}
            disabled={status === "uploading" || !file}
          >
            Cambiar archivo
          </button>
        </div>
      </form>

      {status === "done" && (
        <div className="form-actions">
          <button
            type="button"
            className="btn btn-vermilion"
            onClick={() => navigate(`/projects/${projectId}/analysis`)}
          >
            Continuar a Análisis
          </button>
        </div>
      )}
    </section>
  );
}
