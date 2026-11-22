/* SUMI Review & Approve — aprobación real conectada a la API. */
import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, API_BASE } from "../api/client";

export default function Review() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [modalOpen, setModalOpen] = useState(false);
  const [approving, setApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const approve = async () => {
    setError(null);
    setApproving(true);
    try {
      const res = await api.post<any>(`/analysis/${analysisId}/approve`, {});
      setModalOpen(false);
      navigate(`/colorize/${analysisId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed.");
    } finally {
      setApproving(false);
    }
  };

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

      {error && <p style={{ color: "#c0392b", fontSize: "0.85rem", margin: "8px 0" }}>{error}</p>}

      <div className="grid-2">
        <div className="panel-box">
          <span className="eyebrow">Configuration Summary</span>
          <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: 8, borderBottom: "1px solid var(--border)" }}>
              <span>Analysis ID</span>
              <strong>{analysisId}</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: 8, borderBottom: "1px solid var(--border)" }}>
              <span>Endpoint</span>
              <strong>{'POST /api/v1/analysis/{analysis_id}/approve'}</strong>
            </div>
          </div>
        </div>
      </div>

      <div
        className={`modal-backdrop ${modalOpen ? "is-open" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modalTitle"
      >
        <div className="modal-card">
          <span className="eyebrow">{'POST /api/v1/analysis/{analysis_id}/approve…'}</span>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1.3rem", margin: "8px 0" }}>
            Confirm Color Configuration
          </h3>
          <p style={{ fontSize: "0.86rem", color: "var(--ink-muted)", marginBottom: 18 }}>
            You are approving the analysis for colorization. Once approved, you can proceed to colorize the page.
          </p>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => setModalOpen(false)}>
              Cancel
            </button>
            <button type="button" className="btn btn-vermilion btn-sm" onClick={approve} disabled={approving}>
              {approving ? "Approving…" : "Confirm Approval"}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
