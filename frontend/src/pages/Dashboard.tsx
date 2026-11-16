/* SUMI Dashboard — from studio.html mockup. */

import { useState } from "react";

const recentProjects = [
  {
    id: "p1",
    title: "Tokyo Dusk — Ch. 09",
    desc: "Seinen rooftop sequence with 4 recurring characters.",
    pages: 8,
    updated: "2h ago",
    status: "review" as const,
  },
  {
    id: "p2",
    title: "Crimson Gate — Vol. 02",
    desc: "Shrine dusk spread and action duel plates.",
    pages: 6,
    updated: "Yesterday",
    status: "done" as const,
  },
];

const summaryCells = [
  { label: "Active Projects", value: "2" },
  { label: "Imported Pages", value: "14" },
  { label: "Pending Review", value: "3", status: "vermilion" as const },
  { label: "Completed Jobs", value: "9" },
];

export default function Dashboard() {
  const [showEmpty, setShowEmpty] = useState(false);

  return (
    <section className="screen is-active" id="screen-dashboard">
      <div className="page-head">
        <div>
          <span className="eyebrow">01 // Creative Workspace</span>
          <h1 className="h1">Welcome back to <em>SUMI</em> Studio.</h1>
        </div>
        <button type="button" className="btn-vermilion" onClick={() => {}}>
          + New Project
        </button>
      </div>

      {showEmpty ? (
        <div className="panel-box" style={{ textAlign: "center", padding: "64px 24px" }}>
          <span className="eyebrow">No Projects Yet</span>
          <h2 className="h1" style={{ marginBottom: 12 }}>
            Begin your first <em>colorization</em> project.
          </h2>
          <p style={{ color: "var(--ink-muted)", maxWidth: 440, margin: "0 auto 24px" }}>
            Import monochrome manga pages, validate character identities and masks, and generate colorized plates.
          </p>
          <button type="button" className="btn-vermilion" onClick={() => {}}>
            Create your first project
          </button>
        </div>
      ) : (
        <>
          <div className="summary-strip">
            {summaryCells.map((cell) => (
              <div key={cell.label} className="summary-cell">
                <span className="eyebrow">{cell.label}</span>
                <div className="summary-val" style={{ color: cell.status === "vermilion" ? "var(--vermilion)" : undefined }}>
                  {cell.value}
                </div>
              </div>
            ))}
          </div>

          <span className="eyebrow" style={{ marginBottom: 12 }}>
            Recent Projects
          </span>
          <div className="grid-3" style={{ marginBottom: 32 }}>
            {recentProjects.map((p) => {
              const badgeConfig: Record<string, { className: string; text: string }> = {
                review: { className: "badge badge-review", text: "Review Required" },
                done: { className: "badge badge-done", text: "Completed" },
              };
              const badge = badgeConfig[p.status];
              return (
                <article
                  key={p.id}
                  className="project-card"
                  onClick={() => {}}
                >
                  <div className="project-thumb">
                    <svg viewBox="0 0 320 200" preserveAspectRatio="xMidYMid slice">
                      <rect width="320" height="200" fill="#efece4" />
                      <path d="M0 150 L70 95 L140 130 L230 80 L320 135 L320 200 L0 200 Z" fill="#111111" />
                      <circle cx="240" cy="60" r="24" fill="#f04438" />
                    </svg>
                  </div>
                  <div className="project-body">
                    <div className="project-title">{p.title}</div>
                    <p className="project-desc">{p.desc}</p>
                    <div className="project-meta">
                      <span>{p.pages} Pages · {p.updated}</span>
                      <span className={badge.className}>{badge.text}</span>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>

          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setShowEmpty(true)}
          >
            Toggle Empty State
          </button>
        </>
      )}
    </section>
  );
}
