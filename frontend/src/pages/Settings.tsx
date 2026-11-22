/* SUMI Settings — información del entorno de ejecución. */
import { useState, useEffect } from "react";
import { API_BASE } from "../api/client";

export default function Settings() {
  const [backendUrl, setBackendUrl] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // La URL del backend se deriva de la variable de entorno VITE_API_BASE_URL
    // quitando el sufijo /api/v1 si existe
    const base = API_BASE.replace(/\/api\/v1$/, "");
    setBackendUrl(base);
    setLoading(false);
  }, [API_BASE]);

  if (loading) {
    return (
      <section className="screen is-active" id="screen-settings">
        <div className="page-head">
          <div>
            <span className="eyebrow">11 // Environment</span>
            <h1 className="h1">Studio <em>Settings</em></h1>
          </div>
        </div>
        <p style={{ color: "var(--ink-muted)" }}>Loading settings…</p>
      </section>
    );
  }

  return (
    <section className="screen is-active" id="screen-settings">
      <div className="page-head">
        <div>
          <span className="eyebrow">11 // Environment</span>
          <h1 className="h1">Studio <em>Settings</em></h1>
        </div>
      </div>
      <div className="panel-box" style={{ maxWidth: 540 }}>
        <p style={{ fontSize: "0.9rem", color: "var(--ink-muted)", marginBottom: 12 }}>
          Connected to FastAPI backend at <code>{backendUrl}</code> with local artifact storage and Celery worker queues.
        </p>
        <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 10, fontSize: "0.84rem" }}>
          <div>
            <strong>API Base URL:</strong>
            <span className="mono-label">{API_BASE}</span>
          </div>
          <div>
            <strong>Environment:</strong>
            <span className="badge badge-review">Development</span>
          </div>
          <div>
            <strong>Adapter:</strong>
            <span className="badge badge-review">SUMI U-Net CPU</span>
          </div>
        </div>
      </div>
    </section>
  );
}
