/* SUMI Colorize Center — real inference via local U-Net (F08). */
import { useState, useEffect } from "react";
import { API_BASE } from "../api/client";

const stages = [
  { pct: 10, msg: "Stage: queued — job created" },
  { pct: 30, msg: "Stage: preprocessing — resolving input image" },
  { pct: 60, msg: "Stage: colorizing — U-Net inference (CPU)" },
  { pct: 90, msg: "Stage: refining — saving result artifact" },
  { pct: 100, msg: "Stage: completed — result ready" },
];

export default function Colorize() {
  const [analysisId, setAnalysisId] = useState("");
  const [running, setRunning] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [idx, setIdx] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);

  const startColorization = async () => {
    setError(null);
    setResultUrl(null);
    setJobStatus(null);
    setIdx(0);
    setRunning(true);

    try {
      const response = await fetch(
        `${API_BASE}/colorizations?analysis_id=${encodeURIComponent(analysisId)}`,
        { method: "POST" }
      );
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${response.status}`);
      }
      const data = await response.json();
      setJobId(data.job_id);
      setJobStatus(data.estado);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setRunning(false);
    }
  };

  // Poll job status while running.
  useEffect(() => {
    if (!running || !jobId) return;
    const timer = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE}/colorizations/${jobId}`);
        if (!response.ok) {
          clearInterval(timer);
          setRunning(false);
          setError(`Failed to fetch job status: HTTP ${response.status}`);
          return;
        }
        const data = await response.json();
        setJobStatus(data.estado);

        // Map estado to progress index.
        const estado = data.estado;
        let nextIdx = idx;
        if (estado === "pending") nextIdx = 1;
        else if (estado === "preprocessing") nextIdx = 2;
        else if (estado === "colorizing") nextIdx = 3;
        else if (estado === "refining") nextIdx = 4;
        else if (estado === "completed") nextIdx = 5;
        else if (estado === "failed") nextIdx = 5;

        setIdx(nextIdx);

        if (estado === "completed") {
          setResultUrl(`${API_BASE}/colorizations/${jobId}/result`);
          clearInterval(timer);
          setRunning(false);
        } else if (estado === "failed") {
          clearInterval(timer);
          setRunning(false);
          setError("Colorization job failed.");
        }
      } catch (err) {
        clearInterval(timer);
        setRunning(false);
        setError(err instanceof Error ? err.message : String(err));
      }
    }, 2000);
    return () => clearInterval(timer);
  }, [running, jobId, idx]);

  return (
    <section className="screen is-active" id="screen-colorize">
      <div className="page-head">
        <div>
          <span className="eyebrow">07 // Asynchronous Execution</span>
          <h1 className="h1">Colorization <em>Center</em></h1>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="text"
            placeholder="Analysis ID"
            value={analysisId}
            onChange={(e) => setAnalysisId(e.target.value)}
            disabled={running}
            style={{ padding: "6px 10px", fontSize: "0.85rem" }}
          />
          <button
            type="button"
            className="btn btn-vermilion"
            onClick={startColorization}
            disabled={running || !analysisId}
          >
            Start Colorization Job
          </button>
        </div>
      </div>

      {error && (
        <p style={{ color: "#c0392b", fontSize: 0.85, margin: "8px 0" }}>
          Error: {error}
        </p>
      )}

      <div className="panel-box">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div>
            <span className="eyebrow">POST /api/v1/colorizations</span>
            <strong id="jobIdLabel">
              Job: {jobId ? jobId.slice(0, 8) + "…" : "—"}
            </strong>
          </div>
          <span className={`badge ${running ? "badge-running" : "badge-approved"}`}>
            {jobStatus || (running ? "Colorizing" : "Idle")}
          </span>
        </div>

        <div className="progress-track">
          <div
            className="progress-fill"
            id="jobProgressBar"
            style={{
              width: idx > 0 ? stages[idx - 1]?.pct ?? 0 : 0,
              transition: "width 0.3s ease",
            }}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: 0.75, color: "var(--ink-muted)" }}>
          <span id="jobStageMsg">
            {idx > 0 ? stages[idx - 1]?.msg : "Stage: Waiting for execution"}
          </span>
          <span id="jobPctLabel">
            {idx > 0 ? stages[idx - 1]?.pct : 0}%
          </span>
        </div>

        {resultUrl && (
          <div style={{ marginTop: 16, textAlign: "center" }}>
            <img
              src={resultUrl}
              alt="Colorized result"
              style={{ maxWidth: "100%", height: "auto", border: "1px solid var(--border)" }}
            />
            <p style={{ marginTop: 8, fontSize: 0.8, color: "var(--ink-muted)" }}>
              Result: <a href={resultUrl} target="_blank" rel="noopener noreferrer">Open image</a>
            </p>
          </div>
        )}
      </div>

      <p style={{ fontSize: 0.8, color: "var(--ink-muted)", marginTop: 16, paddingTop: 12, borderTop: "1px solid var(--border)" }}>
        Connected to real local U-Net inference via Celery worker. Result served from backend.
      </p>
    </section>
  );
}
