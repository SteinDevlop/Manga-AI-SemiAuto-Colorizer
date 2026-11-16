/* SUMI Projects — from studio.html mockup. */

import { useState } from "react";

const projects = [
  {
    id: "p1",
    title: "Tokyo Dusk — Ch. 09",
    desc: "Seinen rooftop sequence with 4 recurring characters.",
    pages: 8,
    updated: "2h ago",
    status: "review",
    thumb: `M0 150 L70 95 L140 130 L230 80 L320 135 L320 200 L0 200 Z`,
  },
  {
    id: "p2",
    title: "Crimson Gate — Vol. 02",
    desc: "Shrine dusk spread and action duel plates.",
    pages: 6,
    updated: "Yesterday",
    status: "done",
    thumb: `M95 45 L225 45 L225 186 L95 186 Z`,
  },
  {
    id: "p3",
    title: "Moonlit Pagoda — Ch. 03",
    desc: "Fantasy landscape with screentone preservation.",
    pages: 12,
    updated: "3 days ago",
    status: "running",
    thumb: `M160 40 Q200 10 240 40 Q200 80 160 40 Z`,
  },
];

const badgeConfig: Record<string, { className: string; text: string }> = {
  review: { className: "badge badge-review", text: "Review Required" },
  done: { className: "badge badge-done", text: "Completed" },
  running: { className: "badge badge-running", text: "Analyzing" },
};

export default function Projects() {
  const [files, setFiles] = useState<File[]>([]);
  const [feedback, setFeedback] = useState("");

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = Array.from(e.target.files ?? []);
    setFiles(fileList);
    setFeedback(
      `Uploaded ${fileList.length} page(s): ${fileList.map((f) => f.name).join(", ")} — Queued for analysis.`
    );
  };

  return (
    <section className="screen is-active" id="screen-project">
      <div className="page-head">
        <div>
          <span className="eyebrow">02 // Project Workspace</span>
          <h1 className="h1">Tokyo Dusk — Ch. <em>09</em></h1>
          <p style={{ color: "var(--ink-muted)", marginTop: 4 }}>
            8 imported pages · Last modified Nov 15, 2026
          </p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => {}}>
          + Import Pages
        </button>
      </div>

      <label className="dropzone" htmlFor="pageUploadInput" style={{ display: "block" }}>
        <span className="eyebrow">POST /api/v1/pages</span>
        <strong>Drop monochrome PNG, JPG, or TIFF manga pages here</strong>
        <p style={{ color: "var(--ink-muted)", fontSize: 0.82, marginTop: 4 }}>
          Supports multi-file selection. Max 25MB per page.
        </p>
        <input
          type="file"
          id="pageUploadInput"
          accept="image/*"
          multiple
          hidden
          onChange={handleUpload}
        />
      </label>

      {files.length > 0 && (
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 0.78,
            color: "var(--emerald)",
            marginBottom: 16,
          }}
        >
          {feedback}
        </div>
      )}

      <div className="grid-3" id="pagesGrid">
        {projects.map((p) => {
          const badge = badgeConfig[p.status];
          return (
            <article key={p.id} className="project-card" onClick={() => {}}>
              <div className="project-thumb">
                <svg viewBox="0 0 300 400" preserveAspectRatio="xMidYMid slice">
                  <rect width="300" height="400" fill="#fff" />
                  <rect x="16" y="16" width="268" height="120" fill="#efece4" stroke="#111" strokeWidth="2" />
                  <rect x="16" y="148" width="268" height="236" fill="#efece4" stroke="#111" strokeWidth="2" />
                  <path d={p.thumb} fill="#111111" stroke="#111111" strokeWidth="2" />
                </svg>
                <span className="exhibit-pill">
                  <span className="on-ink">Original Ink</span>
                  <span className="on-color">SUMI Color</span>
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong>{p.title}</strong>
                <span className={badge.className}>{badge.text}</span>
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 0.7, color: "var(--ink-muted)" }}>
                {p.pages} Pages · ch09_p{p.id}.png
              </div>
              <button type="button" className="btn btn-outline btn-sm" onClick={() => {}}>
                Open in Analysis Studio →
              </button>
            </article>
          );
        })}
      </div>
    </section>
  );
}
