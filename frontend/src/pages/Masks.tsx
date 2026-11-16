/* SUMI Mask Editor — from studio.html mockup. */

import { useState } from "react";

export default function Masks() {
  const [maskVisible, setMaskVisible] = useState(true);

  return (
    <section className="screen is-active" id="screen-masks">
      <div className="page-head">
        <div>
          <span className="eyebrow">05 // Segmentation & Mask Review</span>
          <h1 className="h1">Mask <em>Editor</em> — Page 01</h1>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setMaskVisible((v) => !v)}
          >
            {maskVisible ? "Hide Mask Overlay" : "Show Mask Overlay"}
          </button>
          <button type="button" className="btn btn-primary btn-sm" onClick={() => {}}>
            Next: Review & Approve →
          </button>
        </div>
      </div>

      <div className="grid-2" style={{ gridTemplateColumns: "1fr 320px" }}>
        <div className="viewer-canvas">
          <div className="viewer-art-wrap">
            <svg viewBox="0 0 360 480">
              <rect width="360" height="480" fill="#faf9f6" />
              <rect x="18" y="18" width="324" height="200" fill="#e8e5dc" stroke="#111" strokeWidth="2" />
              <path d="M90 218 L120 110 Q140 90 170 90 Q200 90 215 115 L235 218 Z" fill="#111" />
              <circle cx="155" cy="72" r="24" fill="#d8d4ca" stroke="#111" strokeWidth="2" />
            </svg>
            <svg
              className={`mask-overlay ${maskVisible ? "" : "is-hidden"}`}
              id="maskOverlaySvg"
              viewBox="0 0 360 480"
            >
              <path d="M90 218 L120 110 Q140 90 170 90 Q200 90 215 115 L235 218 Z" fill="#315bea" />
              <circle cx="155" cy="72" r="24" fill="#f04438" />
            </svg>
          </div>
        </div>

        <div className="panel-box">
          <span className="eyebrow">Active Mask Layers</span>
          <div className="char-row is-selected" style={{ marginTop: 12 }}>
            <span>Renji — Coat Region</span>
            <span className="dot" style={{ background: "var(--electric)" }} />
          </div>
          <div className="char-row">
            <span>Renji — Face & Hair</span>
            <span className="dot" style={{ background: "var(--vermilion)" }} />
          </div>
          <p style={{ fontSize: 0.82, color: "var(--ink-muted)", margin: "16px 0" }}>
            Verify segmentation boundaries before locking configuration. You may upload a corrected PNG mask artifact if needed.
          </p>
          <label className="btn btn-outline btn-sm" style={{ width: "100%", justifyContent: "center", cursor: "pointer" }}>
            Replace Mask Artifact
            <input type="file" accept="image/png" hidden />
          </label>
        </div>
      </div>
    </section>
  );
}
