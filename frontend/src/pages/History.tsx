/* SUMI Results & Export — lista real de jobs de colorización conectada a la API. */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api, API_BASE } from "../api/client";

export default function History() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Array<{
    job_id: string;
    analysis_id: string;
    estado: string;
    progreso: number;
    mensaje: string | null;
    ruta_resultado: string | null;
    version_modelo: string | null;
    created_at: string | null;
    updated_at: string | null;
  }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listColorizations()
      .then((data) => {
        setJobs(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load jobs.");
        setLoading(false);
      });
  }, []);

  const viewResult = (jobId: string, resultUrl: string | null) => {
    if (resultUrl) {
      navigate(`/results/${jobId}`);
    } else {
      setError("No result available for this job yet.");
    }
  };

  const statusBadge = (estado: string) => {
    switch (estado) {
      case "completed":
        return <span className="badge badge-done">Completed</span>;
      case "failed":
        return <span className="badge badge-failed">Failed</span>;
      case "pending":
      case "preprocessing":
      case "colorizing":
      case "refining":
        return <span className="badge badge-running">{estado}</span>;
      default:
        return <span>{estado}</span>;
    }
  };

  if (loading) {
    return (
      <section className="screen is-active" id="screen-results">
        <div className="page-head">
          <div>
            <span className="eyebrow">08 // Final Output</span>
            <h1 className="h1">Results &amp; <em>Export</em></h1>
          </div>
        </div>
        <p style={{ color: "var(--ink-muted)" }}>Loading jobs…</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="screen is-active" id="screen-results">
        <div className="page-head">
          <div>
            <span className="eyebrow">08 // Final Output</span>
            <h1 className="h1">Results &amp; <em>Export</em></h1>
          </div>
        </div>
        <p style={{ color: "#c0392b" }}>{error}</p>
      </section>
    );
  }

  return (
    <section className="screen is-active" id="screen-results">
      <div className="page-head">
        <div>
          <span className="eyebrow">08 // Final Output</span>
          <h1 className="h1">Results &amp; <em>Export</em></h1>
        </div>
      </div>

      {jobs.length === 0 && (
        <div className="panel-box" style={{ textAlign: "center", padding: "64px 24px" }}>
          <span className="eyebrow">No Results Yet</span>
          <h2 className="h1" style={{ marginBottom: 12 }}>No colorization jobs found.</h2>
          <p style={{ color: "var(--ink-muted)", maxWidth: 440, margin: "0 auto 24px" }}>
            Upload a manga page, run analysis, approve it, and start colorization to see results here.
          </p>
          <button type="button" className="btn btn-vermilion" onClick={() => navigate("/upload")}>
            Upload a Page
          </button>
        </div>
      )}

      {jobs.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Job ID</th>
              <th>Status</th>
              <th>Progress</th>
              <th>Model</th>
              <th>Result</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.job_id}>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>
                  {job.job_id.slice(0, 8)}…
                </td>
                <td>{statusBadge(job.estado)}</td>
                <td>{job.progreso}%</td>
                <td>{job.version_modelo ?? "—"}</td>
                <td>
                  {job.estado === "completed" && job.ruta_resultado ? (
                    <button
                      type="button"
                      className="btn btn-vermilion btn-sm"
                      onClick={() => viewResult(job.job_id, job.ruta_resultado)}
                    >
                      View Result
                    </button>
                  ) : (
                    <span style={{ color: "var(--ink-muted)", fontSize: "0.85rem" }}>
                      {job.estado === "failed" ? "Failed" : "Pending"}
                    </span>
                  )}
                </td>
                <td style={{ fontSize: "0.85rem", color: "var(--ink-muted)" }}>
                  {job.created_at ? new Date(job.created_at).toLocaleString() : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
