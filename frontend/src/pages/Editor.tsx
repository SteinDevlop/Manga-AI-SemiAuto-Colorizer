/* SUMI Character & Color Editor — from studio.html mockup. */

const attributes = [
  { name: "Skin", value: "#FAE2D6", confidence: 96, status: "ok" },
  { name: "Hair", value: "#1B1C24", confidence: 94, status: "ok" },
  { name: "Eyes", value: "#315BEA", confidence: 71, status: "uncertain" },
  { name: "Clothing", value: "#1E2D4D", confidence: 100, status: "override" },
  { name: "Accessories", value: "#F04438", confidence: 92, status: "ok" },
];

export default function Editor() {
  return (
    <section className="screen is-active" id="screen-characters">
      <div className="page-head">
        <div>
          <span className="eyebrow">04 // Character & Palette Configuration</span>
          <h1 className="h1">Renji (ID-01) — <em>Color</em> Memory</h1>
        </div>
        <button type="button" className="btn btn-primary btn-sm" onClick={() => {}}>
          Next: Mask Editor →
        </button>
      </div>

      <div className="grid-2" style={{ gridTemplateColumns: "300px 1fr" }}>
        <div className="panel-box">
          <span className="eyebrow">Character Reference</span>
          <div
            style={{
              aspectRatio: 1 / 1,
              border: "1px solid var(--ink)",
              background: "var(--paper-2)",
              margin: "12px 0",
              display: "grid",
              placeItems: "center",
            }}
          >
            <svg viewBox="0 0 160 160" width="120" height="120">
              <circle cx="80" cy="64" r="34" fill="#fae2d6" stroke="#111" strokeWidth="2" />
              <path d="M46 64 Q50 26 84 28 Q116 30 112 68 Q94 48 64 52 Z" fill="#111" />
              <path d="M36 160 L50 104 L110 104 L124 160 Z" fill="#1e2d4d" stroke="#111" strokeWidth="2" />
            </svg>
          </div>
          <div style={{ fontSize: 0.82, color: "var(--ink-muted)" }}>
            Appears on <strong>6 pages</strong> · Scene-specific wardrobe overrides enabled.
          </div>
        </div>

        <div className="panel-box">
          <div className="pane-title">
            <span>Attributes (PATCH /api/v1/characters/id-01/attributes)</span>
          </div>

          {attributes.map((attr) => (
            <div key={attr.name} className="attr-row">
              <strong>{attr.name}</strong>
              <input
                type="color"
                className="swatch-input"
                value={attr.value}
                data-attr={attr.name.toLowerCase()}
              />
              <span className={`mono-label ${attr.status === "uncertain" ? "color-uncertain" : ""}`}>
                {attr.status === "uncertain"
                  ? `${attr.confidence}% Uncertain`
                  : attr.status === "override"
                    ? "Scene Override"
                    : `${attr.confidence}% Confidence`}
              </span>
              <input type="text" className="hex-input" value={attr.value} data-hex={attr.name.toLowerCase()} />
              <button type="button" className="btn btn-outline btn-sm" data-restore={attr.name.toLowerCase()} data-default={attr.value}>
                Restore
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
