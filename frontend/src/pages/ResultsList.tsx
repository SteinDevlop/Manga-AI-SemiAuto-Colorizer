/* Results & Exports — listado global de resultados y exportaciones.
 *
 * Muestra todos los trabajos de colorización con su estado, progreso y
 * enlace para descargar el resultado. Cada resultado está vinculado a un
 * análisis (y por tanto a un proyecto) a través del analysis_id.
 */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function ResultsList() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Array<{
    job_id: string;
    analysis_id: string;
    estado: string;
    progreso: number;
    mensaje: string | null;
    ruta_resultado: string | null;
    version_modelo: string | null;
    created_at: string | null;
    updated_at: string | null;
  }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.listColorizations()
      .then((data) => {
        if (!cancelled) {
          setJobs(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "No se pudieron cargar los resultados.");
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, []);

  const statusBadge = (estado: string) => {
    const conf: Record<string, string> = {
      completed: "badge badge-done",
      failed: "badge badge-failed",
      error: "badge badge-failed",
      pending: "badge badge-running",
      processing: "badge badge-running",
      colorizing: "badge badge-running",
    };
    return conf[estado] || "badge";
  };

  const download = async (jobId: string) => {
    try {
      const blob = await api.downloadColorization(jobId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = `colorized-${jobId}.png`;
      document.body.appendChild(anchor); anchor.click(); anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo descargar el resultado.");
    }
  };

  const viewResult = (jobId: string) => navigate(`/results/${jobId}`);

  if (loading) {
    return (
      <section className="screen is-active" id="screen-results">
        <div className="page-head">
          <div>
            <span className="eyebrow">Results &amp; Exports</span>
            <h1 className="h1">Resultados y exportaciones</h1>
          </div>
        </div>
        <p style={{ color: "var(--ink-muted)" }}>Cargando resultados…</p>
      </section>
    );
  }
  if (error) {
    return (
      <section className="screen is-active" id="screen-results">
        <div className="page-head">
          <div>
            <span className="eyebrow">Results &amp; Exports</span>
            <h1 className="h1">Resultados y exportaciones</h1>
          </div>
        </div>
        <p style={{ color: "#c0392b" }}>{error}</p>
      </section>
    );
  }

  return (
    <section className="screen is-active" id="screen-results">
      <div className="page-head">
        <div>
          <span className="eyebrow">Results &amp; Exports</span>
          <h1 className="h1">Resultados y exportaciones</h1>
          <p style={{ color: "var(--ink-muted)", marginTop: 6 }}>
            Listado global de trabajos de colorización de todos los proyectos.
          </p>
        </div>
      </div>

      {jobs.length === 0 && (
        <div className="panel-box" style={{ textAlign: "center", padding: "64px 24px" }}>
          <span className="eyebrow">Sin resultados aún</span>
          <h2 className="h1" style={{ marginBottom: 12 }}>
            No hay exportaciones disponibles.
          </h2>
          <p style={{ color: "var(--ink-muted)", maxWidth: 440, margin: "0 auto 24px" }}>
            Sube una página, ejecuta el análisis, apropialo y lanza la
            colorización para generar un resultado exportable.
          </p>
          <button type="button" className="btn-vermilion" onClick={() => navigate("/projects")}>
            Crear proyecto
          </button>
        </div>
      )}

      {jobs.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Job</th>
              <th>Análisis</th>
              <th>Estado</th>
              <th>Progreso</th>
              <th>Modelo</th>
              <th>Resultado</th>
              <th>Creado</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.job_id}>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>
                  {job.job_id.slice(0, 8)}…
                </td>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem", color: "var(--ink-muted)" }}>
                  {job.analysis_id ? job.analysis_id.slice(0, 8) + "…" : "—"}
                </td>
                <td>
                  <span className={statusBadge(job.estado)} style={{ fontSize: "0.8rem" }}>
                    {job.estado}
                  </span>
                </td>
                <td>{job.progreso}%</td>
                <td style={{ fontSize: "0.8rem", color: "var(--ink-muted)" }}>
                  {job.version_modelo ?? "—"}
                </td>
                <td>
                  {job.estado === "completed" && job.ruta_resultado ? (
                    <>
                      <button
                        type="button"
                        className="btn btn-vermilion btn-sm"
                        onClick={() => download(job.job_id)}
                        style={{ marginRight: 6 }}
                      >
                        Descargar
                      </button>
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        onClick={() => viewResult(job.job_id)}
                      >
                        Ver detalle
                      </button>
                    </>
                  ) : (
                    <span style={{ color: "var(--ink-muted)", fontSize: "0.85rem" }}>
                      {job.estado === "failed" ? "Fallido" : "Pendiente"}
                    </span>
                  )}
                </td>
                <td style={{ fontSize: "0.8rem", color: "var(--ink-muted)" }}>
                  {job.created_at ? new Date(job.created_at).toLocaleString() : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
