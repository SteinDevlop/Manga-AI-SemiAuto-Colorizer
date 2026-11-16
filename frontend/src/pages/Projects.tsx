/** Project list screen: lists projects and lets the user create new ones. */

import { useState, useEffect } from "react";
import { api } from "../api/client";
import type { Project } from "../types";

export function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

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

  const handleNameChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setName(event.target.value);
    setCreateError(null);
  };

  const handleDescriptionChange = (
    event: React.ChangeEvent<HTMLTextAreaElement>,
  ) => {
    setDescription(event.target.value);
    setCreateError(null);
  };

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>,
  ): Promise<void> => {
    event.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      const created = await api.post<Project>("/projects", {
        nombre: name,
        descripcion: description || undefined,
      });
      setProjects((current) => [created, ...current]);
      setName("");
      setDescription("");
      setFormOpen(false);
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "Failed to create project.",
      );
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="page projects">
      <h1>Projects</h1>
      {error && <div className="alert alert-error">{error}</div>}
      {loading ? (
        <p>Loading projects...</p>
      ) : (
        <>
          <button type="button" onClick={() => setFormOpen(true)} disabled={creating}>
            New project
          </button>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Created at</th>
              </tr>
            </thead>
            <tbody>
              {projects.length === 0 ? (
                <tr>
                  <td colSpan={3}>No projects yet.</td>
                </tr>
              ) : (
                projects.map((project) => (
                  <tr key={project.id}>
                    <td>{project.nombre}</td>
                    <td>{project.descripcion ?? "-"}</td>
                    <td>{project.created_at}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          {formOpen && (
            <form className="form" onSubmit={handleSubmit}>
              <div className="form-field">
                <label htmlFor="project-name">Name</label>
                <input
                  id="project-name"
                  type="text"
                  value={name}
                  onChange={handleNameChange}
                  disabled={creating}
                  maxLength={200}
                />
              </div>
              <div className="form-field">
                <label htmlFor="project-description">Description</label>
                <textarea
                  id="project-description"
                  value={description}
                  onChange={handleDescriptionChange}
                  disabled={creating}
                  maxLength={1000}
                />
              </div>
              {createError && <div className="alert alert-error">{createError}</div>}
              <div className="form-actions">
                <button type="submit" disabled={creating}>
                  {creating ? "Creating..." : "Create project"}
                </button>
                <button type="button" onClick={() => setFormOpen(false)}>
                  Cancel
                </button>
              </div>
            </form>
          )}
        </>
      )}
    </div>
  );
}
