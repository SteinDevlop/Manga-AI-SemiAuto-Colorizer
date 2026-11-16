/* SUMI Analysis Studio — from studio.html mockup. */

import { useState } from "react";

const characters = [
  { id: "ren", name: "Renji (ID-01)", appearances: 2, confidence: 96, color: "var(--emerald)" },
  { id: "akira", name: "Akira (ID-02)", appearances: 1, confidence: 68, color: "var(--saffron)" },
];

const panels = [
  { id: "p1", label: "Panel 01", confidence: 98, character: "Renji", x: 5, y: 4, w: 90, h: 41, selected: true },
  { id: "p2", label: "Panel 02", confidence: 91, character: "—", x: 5, y: 48, w: 43, h: 48, selected: false },
  { id: "p3", label: "Panel 03", confidence: 68, character: "Akira?", x: 52, y: 48, w: 43, h: 48, selected: false, uncertain: true },
];

export default function Analysis() {
  const [zoom, setZoom] = useState(1);
  const [selectedPanel, setSelectedPanel] = useState("p1");

  const selectedPanelData = panels.find((p) => p.id === selectedPanel);

  return (
    <section className="screen is-active" id="screen-analysis">
      <div className="page-head">
        <div>
          <span className="eyebrow">03 // Computer Vision Inspection</span>
          <h1 className="h1">Analysis <em>Studio</em> — Page 01</h1>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button type="button" className="btn btn-outline btn-sm" onClick={() => setZoom((z) => Math.max(0.75, z - 0.15))}>
            Zoom −
          </button>
          <button type="button" className="btn btn-outline btn-sm" onClick={() => setZoom((z) => Math.min(1.5, z + 0.15))}>
            Zoom +
          </button>
          <button type="button" className="btn btn-primary btn-sm" onClick={() => {}}>
            Configure Characters →
          </button>
        </div>
      </div>

      <div className="studio-3col">
        {/* Left: Characters & Identity Groups */}
        <div className="studio-pane">
          <div className="pane-title">
            <span>Detected Identities</span>
            <span>{characters.length}</span>
          </div>
          {characters.map((c) => (
            <div
              key={c.id}
              className={`char-row ${c.id === "ren" ? "is-selected" : ""}`}
              onClick={() => setSelectedPanel(c.id === "ren" ? "p1" : "p3")}
            >
              <div>
                <strong style={{ fontSize: 0.84 }}>{c.name}</strong>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 0.68, color: "var(--ink-muted)" }}>
                  {c.appearances} appearances · {c.confidence}%
                </div>
              </div>
              <span className="dot" style={{ background: c.color }} />
            </div>
          ))}
          <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 8 }}>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => {}}>
              Merge Selected Identities
            </button>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => {}}>
              Separate Appearance
            </button>
          </div>
        </div>

        {/* Center: Manga Page Viewer with Bounding Overlays */}
        <div className="viewer-canvas" style={{ transform: `scale(${zoom})`, transformOrigin: "top left" }}>
          <div className="viewer-art-wrap" id="analysisArtWrap">
            <svg viewBox="0 0 360 480">
              <rect width="360" height="480" fill="#faf9f6" />
              <rect x="18" y="18" width="324" height="200" fill="#e8e5dc" stroke="#111" strokeWidth="2" />
              <path d="M90 218 L120 110 Q140 90 170 90 Q200 90 215 115 L235 218 Z" fill="#111" />
              <circle cx="155" cy="72" r="24" fill="#d8d4ca" stroke="#111" strokeWidth="2" />
              <rect x="18" y="232" width="156" height="230" fill="#f3f1ec" stroke="#111" strokeWidth="2" />
              <rect x="186" y="232" width="156" height="230" fill="#e8e5dc" stroke="#111" strokeWidth="2" />
              <circle cx="264" cy="315" r="26" fill="#d8d4ca" stroke="#111" strokeWidth="2" />
            </svg>

            {panels.map((panel) => (
              <div
                key={panel.id}
                className={`bbox ${panel.selected ? "is-selected" : ""} ${panel.uncertain ? "border-color-saffron" : ""}`}
                style={{
                  top: `${panel.y}%`,
                  left: `${panel.x}%`,
                  width: `${panel.w}%`,
                  height: `${panel.h}%`,
                  borderColor: panel.uncertain ? "var(--saffron)" : undefined,
                }}
                data-panel={panel.label}
                onClick={() => setSelectedPanel(panel.id)}
              >
                <span className="bbox-label">{panel.label} · {panel.character}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Selection Inspector */}
        <div className="studio-pane">
          <div className="pane-title">
            <span>Selection Inspector</span>
            <span>{selectedPanelData?.confidence ?? 0}%</span>
          </div>
          <p style={{ fontWeight: 600, marginBottom: 6 }}>{selectedPanelData?.label ?? "Panel 01"}</p>
          <p style={{ fontSize: 0.82, color: "var(--ink-muted)", marginBottom: 16 }}>
            Bounding region verified. Character ID-01 (Renji) matched against chapter memory.
          </p>
          <div style={{ borderTop: "1px solid var(--border)", paddingTop: 12, fontFamily: "var(--font-mono)", fontSize: 0.72, color: "var(--ink-muted)" }}>
            ENDPOINT: GET /api/v1/analysis/p01
          </div>
        </div>
      </div>
    </section>
  );
}
