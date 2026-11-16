/* SUMI Results & Export — from studio.html mockup. */

export default function History() {
  return (
    <section className="screen is-active" id="screen-results">
      <div className="page-head">
        <div>
          <span className="eyebrow">08 // Final Output</span>
          <h1 className="h1">Results &amp; <em>Export</em></h1>
        </div>
        <button type="button" className="btn btn-vermilion" onClick={() => {}}>
          Download Colorized Image
        </button>
      </div>

      <div className="grid-2" style={{ gridTemplateColumns: "1fr 320px" }}>
        <div className="panel-box">
          <div className="compare-stage" id="resultCompareStage" style={{ "--split": "50%" } as React.CSSProperties}>
            <div className="comp-layer comp-bw">
              <svg viewBox="0 0 600 450" preserveAspectRatio="xMidYMid slice" id="resultTemplate">
                <defs>
                  <linearGradient id="resSky" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#19284f" />
                    <stop offset="60%" stopColor="#315bea" />
                    <stop offset="100%" stopColor="#f2c94c" />
                  </linearGradient>
                </defs>
                <rect width="600" height="450" fill="url(#resSky)" />
                <path d="M0 320 L140 210 L290 280 L450 185 L600 265 L600 450 L0 450 Z" fill="#1b2440" stroke="#111" strokeWidth="2" />
                <path d="M235 450 L255 280 Q290 250 325 280 L345 450 Z" fill="#1e2d4d" stroke="#111" strokeWidth="2.4" />
                <path d="M262 285 Q195 268 145 292 Q190 310 260 304 Z" fill="#f04438" stroke="#111" strokeWidth="2" />
                <circle cx="290" cy="240" r="24" fill="#fae2d6" stroke="#111" strokeWidth="2" />
              </svg>
            </div>
            <div className="comp-layer comp-color" id="resultColorLayer" />
            <div className="comp-divider" id="resultDivider">
              <div className="comp-handle">⇄</div>
            </div>
          </div>
        </div>

        <div className="panel-box">
          <span className="eyebrow">Artifact Metadata</span>
          <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 10, fontSize: 0.84 }}>
            <div>
              <strong>Job ID:</strong>{" "}
              <span className="mono-label">job_9f2a1c</span>
            </div>
            <div>
              <strong>Dimensions:</strong> 2480 × 3508 px
            </div>
            <div>
              <strong>Project:</strong> Tokyo Dusk — Ch. 09
            </div>
            <div>
              <strong>Adapter:</strong> SUMI Mock Engine v1
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
