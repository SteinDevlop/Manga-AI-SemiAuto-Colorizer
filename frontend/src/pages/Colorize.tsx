/** Pantalla de colorización y progreso: iniciar trabajo, ver avance y descargar resultado. */

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Analysis, ColorizationJob } from "../types";

type ColorizeView = {
  analysis: Analysis | null;
  job: ColorizationJob | null;
  loading: boolean;
  starting: boolean;
  error: string | null;
  approved: boolean;
};

const initialView: ColorizeView = {
  analysis: null,
  job: null,
  loading: true,
  starting: false,
  error: null,
  approved: false,
};

const POLL_INTERVAL_MS = 2000;

export function Colorize(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const [view, setView] = useState<ColorizeView>(initialView);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (timer.current) {
      clearInterval(timer.current);
      timer.current = null;
    }
  }, []);

  const loadAnalysis = useCallback(async () => {
    if (!id) return;
    setView((v) => ({ ...v, loading: true, error: null }));
    try {
      const analysis = await api.get<Analysis>(`/analyses/${id}`);
      setView((v) => ({ ...v, analysis, loading: false, approved: analysis.estado === "APPROVED" }));
    } catch (err) {
      setView((v) => ({
        ...v,
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load analysis",
        approved: false,
      }));
    }
  }, [id]);

  const startColorization = async () => {
    if (!id || !view.approved || view.job) return;
    setView((v) => ({ ...v, starting: true, error: null }));
    stopPolling();
    try {
      const job = await api.post<ColorizationJob>("/colorizations", { analysis_id: id });
      setView((v) => ({ ...v, starting: false, job }));
      pollJob(job.id);
    } catch (err) {
      setView((v) => ({
        ...v,
        starting: false,
        error: err instanceof Error ? err.message : "Failed to start colorization",
      }));
    }
  };

  const pollJob = useCallback((jobId: string) => {
    stopPolling();
    const fetchJob = async () => {
      try {
        const job = await api.get<ColorizationJob>(`/colorizations/${jobId}`);
        setView((v) => ({ ...v, job }));
        const done = job.estado === "COMPLETED" || job.estado === "FAILED" || job.estado === "CANCELLED";
        if (!done) {
          timer.current = setInterval(fetchJob, POLL_INTERVAL_MS);
        }
      } catch {
        // Keep polling; endpoint may not be ready yet.
        timer.current = setInterval(fetchJob, POLL_INTERVAL_MS);
      }
    };
    timer.current = setInterval(fetchJob, POLL_INTERVAL_MS);
    fetchJob();
  }, [stopPolling]);

  useEffect(() => {
    loadAnalysis();
    return () => stopPolling();
  }, [loadAnalysis, stopPolling]);

  useEffect(() => {
    stopPolling();
  }, [stopPolling]);

  if (view.loading) {
    return <div className="page colorize" style={{ padding: 2 }}>Loading...</div>;
  }

  if (view.error) {
    return <div className="page colorize" style={{ padding: 2 }}>{view.error}</div>;
  }

  const analysis = view.analysis;
  const job = view.job;

  if (!analysis) {
    return <div className="page colorize" style={{ padding: 2 }}>Analysis not found.</div>;
  }

  const stageLabel = (stage: string): string => {
    switch (stage) {
      case "pending": return "pending";
      case "preprocessing": return "preprocessing";
      case "colorizing": return "colorizing";
      case "refining": return "refining";
      case "completed": return "completed";
      case "failed": return "failed";
      case "cancelled": return "cancelled";
      default: return stage;
    }
  };

  return (
    <div className="page colorize" style={{ padding: 2, maxWidth: 900 }}>
      <h1>Colorize page</h1>
      <p>Analysis {analysis.id} — status: {analysis.estado}</p>

      {!view.approved && (
        <p>Analysis is not approved. Colorization is blocked until approval.</p>
      )}

      {view.approved && !job && (
        <button
          onClick={startColorization}
          disabled={view.starting}
          style={{
            padding: "0.6rem 1.2rem",
            fontSize: 1,
            cursor: view.starting ? "default" : "pointer",
            opacity: view.starting ? 0.5 : 1,
          }}
        >
          {view.starting ? "Starting..." : "Start colorization"}
        </button>
      )}

      {job && (
        <>
          <section style={{ marginTop: 1.5 }}>
            <h2>Job</h2>
            <p>Id: {job.id}</p>
            <p>Status: {job.estado}</p>
            <p>{job.mensaje ?? ""}</p>
          </section>

          <section style={{ marginTop: 1.5 }}>
            <h2>Progress</h2>
            <p>{stageLabel(job.estado)}</p>
            <div
              style={{
                width: "100%",
                height: 12,
                backgroundColor: "#334155",
                borderRadius: 6,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${Math.max(0, Math.min(100, job.progreso))}%`,
                  height: "100%",
                  backgroundColor: "#38bdf8",
                  transition: "width 0.3s ease",
                }}
              />
            </div>
          </section>

          {job.estado === "completed" && job.ruta_resultado && (
            <section style={{ marginTop: 1.5 }}>
              <h2>Result</h2>
              <img
                src={job.ruta_resultado}
                alt="Colorized result"
                style={{ maxWidth: "100%", border: "1px solid #334155", borderRadius: 6, marginTop: 0.5 }}
              />
              <br />
              <a
                href={job.ruta_resultado}
                download
                style={{
                  padding: "0.6rem 1.2rem",
                  fontSize: 1,
                  color: "#38bdf8",
                  textDecoration: "none",
                }}
              >
                Download result
              </a>
            </section>
          )}

          {(job.estado === "failed" || job.estado === "cancelled") && (
            <p style={{ marginTop: 1 }}>{job.estado === "failed" ? "Colorization failed." : "Colorization cancelled."}</p>
          )}
        </>
      )}
    </div>
  );
}
