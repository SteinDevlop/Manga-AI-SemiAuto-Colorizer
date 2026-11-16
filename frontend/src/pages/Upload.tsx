/** Page upload screen: select an image and a project, then upload the page. */

import { useState, useEffect } from "react";
import { api } from "../api/client";
import type { Project } from "../types";

const ACCEPTED_MIME_TYPES = ["image/png", "image/jpeg", "image/webp"];

export function Upload() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [projectId, setProjectId] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.get<Project[]>("/projects")
      .then((data) => {
        if (!cancelled) {
          setProjects(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to load projects.");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (preview) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [preview]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setValidationError(null);
    setUploadError(null);
    const selected = event.target.files?.[0] ?? null;
    setFile(selected);
    if (selected) {
      if (!ACCEPTED_MIME_TYPES.includes(selected.type)) {
        setValidationError("Unsupported file type. Use PNG, JPEG, or WebP.");
        setPreview(null);
        return;
      }
      const url = URL.createObjectURL(selected);
      setPreview(url);
    } else {
      setPreview(null);
    }
  };

  const handleProjectChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setProjectId(event.target.value);
    setUploadError(null);
  };

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>,
  ): Promise<void> => {
    event.preventDefault();
    setUploadError(null);
    setValidationError(null);
    if (!file) {
      setValidationError("Select an image file to upload.");
      return;
    }
    if (!ACCEPTED_MIME_TYPES.includes(file.type)) {
      setValidationError("Unsupported file type. Use PNG, JPEG, or WebP.");
      return;
    }
    if (!projectId) {
      setValidationError("Select a project.");
      return;
    }
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("project_id", projectId);
    try {
      await api.post("/pages", formData);
      setFile(null);
      setProjectId("");
      if (preview) {
        URL.revokeObjectURL(preview);
        setPreview(null);
      }
    } catch (err) {
      setUploadError(
        err instanceof Error ? err.message : "Failed to upload page.",
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page upload">
      <h1>Upload page</h1>
      {error && <div className="alert alert-error">{error}</div>}
      {loading ? (
        <p>Loading projects...</p>
      ) : (
        <form className="form" onSubmit={handleSubmit}>
          <div className="form-field">
            <label htmlFor="page-file">Image</label>
            <input
              id="page-file"
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={handleFileChange}
              disabled={uploading}
            />
            {validationError && <div className="alert alert-error">{validationError}</div>}
            {preview && (
              <div className="preview">
                <img src={preview} alt="Selected image preview" />
              </div>
            )}
          </div>
          <div className="form-field">
            <label htmlFor="project-select">Project</label>
            <select
              id="project-select"
              value={projectId}
              onChange={handleProjectChange}
              disabled={uploading}
            >
              <option value="">Select a project</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.nombre}
                </option>
              ))}
            </select>
          </div>
          {uploadError && <div className="alert alert-error">{uploadError}</div>}
          <div className="form-actions">
            <button
              type="submit"
              disabled={uploading || !file || !projectId}
            >
              {uploading ? "Uploading..." : "Upload page"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
