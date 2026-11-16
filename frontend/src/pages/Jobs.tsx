/* SUMI Job History — from studio.html mockup. */

export default function Jobs() {
  return (
    <section className="screen is-active" id="screen-jobs">
      <div className="page-head">
        <div>
          <span className="eyebrow">09 // Asynchronous Queue</span>
          <h1 className="h1">Colorization <em>Job History</em></h1>
        </div>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Job ID</th>
            <th>Project</th>
            <th>Page</th>
            <th>Status</th>
            <th>Progress</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ fontFamily: "var(--font-mono)" }}>job_9f2a1c</td>
            <td>Tokyo Dusk — Ch. 09</td>
            <td>Page 01</td>
            <td>
              <span className="badge badge-done">Completed</span>
            </td>
            <td>100%</td>
            <td>Today, 22:40</td>
          </tr>
          <tr>
            <td style={{ fontFamily: "var(--font-mono)" }}>job_7b104e</td>
            <td>Crimson Gate — Vol. 02</td>
            <td>Page 04</td>
            <td>
              <span className="badge badge-failed">Failed</span>
            </td>
            <td>42%</td>
            <td>Yesterday</td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}
