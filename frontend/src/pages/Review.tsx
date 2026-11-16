/* SUMI Review & Approve — from studio.html mockup. */

import { useState } from "react";

export default function Review() {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <section className="screen is-active" id="screen-review">
      <div className="page-head">
        <div>
          <span className="eyebrow">06 // Mandatory Human Validation</span>
          <h1 className="h1">Review &amp; <em>Approval</em></h1>
        </div>
        <button type="button" className="btn btn-vermilion" onClick={() => setModalOpen(true)}>
          Approve Color Configuration
        </button>
      </div>

      <div className="grid-2">
        <div className="panel-box">
          <span className="eyebrow">Configuration Summary</span>
          <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: 8, borderBottom: "1px solid var(--border)" }}>
              <span>Detected Panels</span>
              <strong>3</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: 8, borderBottom: "1px solid var(--border)" }}>
              <span>Character Identities</span>
              <strong>2</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: 8, borderBottom: "1px solid var(--border)" }}>
              <span>Mask Artifacts</span>
              <strong>Verified</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>Approval Authority</span>
              <strong>Backend (/api/v1/analysis/p01/approve)</strong>
            </div>
          </div>
        </div>

        <div className="panel-box" style={{ borderColor: "var(--saffron)" }}>
          <span className="eyebrow" style={{ color: "#7a5c00" }}>
            Unresolved Warnings (1)
          </span>
          <p style={{ fontSize: 0.9, margin: "10px 0 16px" }}>
            <strong>Akira (ID-02)</strong> eye attribute has 68% confidence in Panel 03. You can still approve, or inspect in the Character Editor.
          </p>
          <button type="button" className="btn btn-outline btn-sm" onClick={() => {}}>
            Jump to Character Editor →
          </button>
        </div>
      </div>

      {/* Approval Confirmation Modal */}
      <div
        className={`modal-backdrop ${modalOpen ? "is-open" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modalTitle"
      >
        <div className="modal-card">
          <span className="eyebrow">POST /api/v1/analysis/p01/approve</span>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 1.3, margin: "8px 0" }}>
            Confirm Color Configuration
          </h3>
          <p style={{ fontSize: 0.86, color: "var(--ink-muted)", marginBottom: 18 }}>
            You are approving 3 panels, 2 character identities, and mask overlays for Page 01. One low-confidence eye attribute warning remains.
          </p>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => setModalOpen(false)}>
              Cancel
            </button>
            <button type="button" className="btn btn-vermilion btn-sm" onClick={() => setModalOpen(false)}>
              Confirm Approval
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
