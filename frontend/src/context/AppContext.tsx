/* Contexto compartido de SUMI Studio.
 *
 * Almacena el estado global de la aplicación:
 * - projectId: proyecto activo
 * - analysisId: análisis activo
 * - jobId: job de colorización activo
 * - currentPage: página actual
 */

import { createContext, useContext, useState, useMemo, ReactNode } from "react";

type AppContextType = {
  projectId: string | null;
  setProjectId: (id: string | null) => void;
  analysisId: string | null;
  setAnalysisId: (id: string | null) => void;
  jobId: string | null;
  setJobId: (id: string | null) => void;
  currentPage: string | null;
  setCurrentPage: (id: string | null) => void;
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<string | null>(null);

  const value = useMemo(
    () => ({ projectId, setProjectId, analysisId, setAnalysisId, jobId, setJobId, currentPage, setCurrentPage }),
    [projectId, analysisId, jobId, currentPage],
  );

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

export const useApp = () => {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return ctx;
};
