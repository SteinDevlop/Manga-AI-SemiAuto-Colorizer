/* SUMI Settings — from studio.html mockup. */

export default function Settings() {
  return (
    <section className="screen is-active" id="screen-settings">
      <div className="page-head">
        <div>
          <span className="eyebrow">11 // Environment</span>
          <h1 className="h1">Studio <em>Settings</em></h1>
        </div>
      </div>
      <div className="panel-box" style={{ maxWidth: 540 }}>
        <p style={{ fontSize: 0.9, color: "var(--ink-muted)", marginBottom: 12 }}>
          Connected to FastAPI REST backend at <code>/api/v1</code> with local artifact storage and Celery worker queues.
        </p>
        <span className="badge badge-review">Mock Adapter Active</span>
      </div>
    </section>
  );
}
