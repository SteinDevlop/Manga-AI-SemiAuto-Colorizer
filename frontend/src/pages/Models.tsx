/* SUMI Model Registry — from studio.html mockup. */

export default function Models() {
  return (
    <section className="screen is-active" id="screen-models">
      <div className="page-head">
        <div>
          <span className="eyebrow">10 // Advanced ML Administration</span>
          <h1 className="h1">Model <em>Registry</em></h1>
        </div>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Model Name</th>
            <th>Version</th>
            <th>Capabilities</th>
            <th>Availability</th>
            <th>Registered</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>sumi-adapter-mock</td>
            <td style={{ fontFamily: "var(--font-mono)" }}>1.0.0</td>
            <td>Pipeline Verification, Palette Conditioning</td>
            <td>
              <span className="badge badge-approved">Available</span>
            </td>
            <td>2026-11-01</td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}
