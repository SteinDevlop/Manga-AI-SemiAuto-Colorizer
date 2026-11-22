/* SUMI Result View — muestra el resultado de colorización de un job específico. */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function Results() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    api.getColorization(jobId)
      .then((data) => {
        setJob(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load job.");
        setLoading(false);
      });
  }, [jobId]);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;
    if (job?.estado === "completed" && jobId) {
      api.downloadColorization(jobId).then(blob => {
        if (!active) return;
        objectUrl = URL.createObjectURL(blob);
        setResultUrl(objectUrl);
      }).catch(err => { if (active) setError(err instanceof Error ? err.message : "No se pudo cargar la imagen."); });
    }
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [job?.estado, jobId]);

  const goBack = () => navigate("/results");

  if (loading) {
    return (
      <section className="screen is-active" id="screen-result-view">
        <div className="page-head">
          <div>
            <span className="eyebrow">08 // Final Output</span>
            <h1 className="h1">Result <em>View</em></h1>
          </div>
        </div>
        <p style={{ color: "var(--ink-muted)" }}>Loading result…</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="screen is-active" id="screen-result-view">
        <div className="page-head">
          <div>
            <span className="eyebrow">08 // Final Output</span>
            <h1 className="h1">Result <em>View</em></h1>
          </div>
        </div>
        <p style={{ color: "#c0392b" }}>{error}</p>
        <button type="button" className="btn btn-vermilion" onClick={goBack}>
          Back to Results
        </button>
      </section>
    );
  }

  const completed = job.estado === "completed";
  const failed = job.estado === "failed";
  const processing = !completed && !failed;

  return (
    <section className="screen is-active" id="screen-result-view">
      <div className="page-head">
        <div>
          <span className="eyebrow">08 // Final Output</span>
          <h1 className="h1">Result <em>View</em></h1>
        </div>
        <button type="button" className="btn btn-outline btn-sm" onClick={goBack}>
          ← Back to Results
        </button>
      </div>

      <div className="panel-box">
        <span className="eyebrow">Job Details</span>
        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 10, fontSize: "0.84rem" }}>
          <div>
            <strong>Job ID:</strong>
            <span className="mono-label">{job.job_id.slice(0, 8)}…</span>
          </div>
          <div>
            <strong>Status:</strong>
            {completed ? (
              <span className="badge badge-done">Completed</span>
            ) : failed ? (
              <span className="badge badge-failed">{job.estado}</span>
            ) : (
              <span className="badge badge-running">{job.estado}</span>
            )}
          </div>
          <div>
            <strong>Progress:</strong> {job.progreso}%
          </div>
          <div>
            <strong>Model:</strong> {job.version_modelo ?? "—"}
          </div>
          <div>
            <strong>Message:</strong> {job.mensaje ?? "—"}
          </div>
          <div>
            <strong>Created:</strong> {job.created_at ?? "—"}
          </div>
        </div>
      </div>

      {completed && resultUrl ? (
        <div className="panel-box" style={{ marginTop: 24 }}>
          <span className="eyebrow">Colorized Result</span>
          <div style={{ marginTop: 16, textAlign: "center" }}>
            <img
              src={resultUrl}
              alt="Colorized result"
              style={{ maxWidth: "100%", height: "auto", border: "1px solid var(--border)" }}
            />
            <p style={{ marginTop: 8, fontSize: "0.8rem", color: "var(--ink-muted)" }}>
              Result:{" "}
              <button type="button" className="btn btn-outline btn-sm" onClick={() => { if (resultUrl) window.open(resultUrl, "_blank", "noopener,noreferrer"); }}>
                Open image in new tab
              </button>
            </p>
          </div>
        </div>
      ) : null}

      {processing ? (
        <div className="panel-box" style={{ marginTop: 24, textAlign: "center" }}>
          <span className="eyebrow">Processing</span>
          <p>Colorization is still in progress. Refresh to check status.</p>
        </div>
      ) : null}

      {failed ? (
        <div className="panel-box" style={{ marginTop: 24, textAlign: "center" }}>
          <span className="eyebrow">Failed</span>
          <p style={{ color: "#c0392b" }}>{job.mensaje ?? "Colorization failed."}</p>
        </div>
      ) : null}
    </section>
  );
}
