/* SUMI Colorize Center — from studio.html mockup. */

import { useState } from "react";

const stages = [
  { pct: 20, msg: "Stage: queued — Celery GPU worker assigned" },
  { pct: 45, msg: "Stage: segmenting — Loading verified mask artifacts" },
  { pct: 75, msg: "Stage: conditioning — Applying character palettes (mock)" },
  { pct: 100, msg: "Stage: completed — Artifact saved to local storage" },
];

export default function Colorize() {
  const [running, setRunning] = useState(false);
  const [idx, setIdx] = useState(0);

  return (
    <section className="screen is-active" id="screen-colorize">
      <div className="page-head">
        <div>
          <span className="eyebrow">07 // Asynchronous Execution</span>
          <h1 className="h1">Colorization <em>Center</em></h1>
        </div>
        <button
          type="button"
          className="btn btn-vermilion"
          onClick={() => {
            setRunning(true);
            setIdx(0);
          }}
          disabled={running}
        >
          Start Colorization Job
        </button>
      </div>

      <div className="panel-box">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div>
            <span className="eyebrow">POST /api/v1/colorizations</span>
            <strong id="jobIdLabel">Job: Ready to queue (Page 01 — Approved)</strong>
          </div>
          <span className={`badge ${running ? "badge-running" : "badge-approved"}`}>
            {running ? "Colorizing" : "Approved"}
          </span>
        </div>

        <div className="progress-track">
          <div className="progress-fill" id="jobProgressBar" style={{ width: idx > 0 ? stages[idx - 1]?.pct ?? 0 : 0 + "%" }} />
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: 0.75, color: "var(--ink-muted)" }}>
          <span id="jobStageMsg">Stage: Waiting for execution</span>
          <span id="jobPctLabel">0%</span>
        </div>

        <p style={{ fontSize: 0.8, color: "var(--ink-muted)", marginTop: 16, paddingTop: 12, borderTop: "1px solid var(--border)" }}>
          Note: Connected to mock AI adapter for workflow verification. Real generative inference workers will replace mock stages without changing API contracts.
        </p>
      </div>
    </section>
  );
}
