/** Pantalla de historial: lista de trabajos de colorización con estados y descarga. */

import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ColorizationJob } from "../types";

export function History() {
  const [jobs, setJobs] = useState<ColorizationJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<ColorizationJob[]>("/colorizations")
      .then((data) => setJobs(data))
      .catch(() => setError("No se pudo cargar el historial."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Cargando historial...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="page history">
      <h1>Historial de trabajos</h1>
      {jobs.length === 0 ? (
        <p>No hay trabajos registrados.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Trabajo</th>
              <th>Análisis</th>
              <th>Estado</th>
              <th>Progreso</th>
              <th>Resultado</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id}>
                <td>{job.id.slice(0, 8)}</td>
                <td>{job.analysis_id.slice(0, 8)}</td>
                <td>{job.estado}</td>
                <td>{job.progreso}%</td>
                <td>
                  {job.ruta_resultado ? (
                    <a href={job.ruta_resultado} download>
                      Descargar
                    </a>
                  ) : (
                    <span>-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
