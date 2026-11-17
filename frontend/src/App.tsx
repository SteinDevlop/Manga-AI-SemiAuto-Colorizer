/** Punto de entrada de la aplicación React con enrutado.
 *
 * Rutas globales (Workspace + System) bajo Layout, más las rutas anidadas de
 * proyecto (/projects/:id redirige a la etapa actual;
 * /projects/:id/:stage renderiza el contenedor de proyecto con stepper
 * interno). El pipeline de cada proyecto vive dentro de estas rutas.
 */
import { BrowserRouter, Routes, Route, useParams, useNavigate, useState } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProjectLayout } from "./components/ProjectLayout";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import Projects from "./pages/Projects";
import Results from "./pages/Results";
import Jobs from "./pages/Jobs";
import Models from "./pages/Models";
import Settings from "./pages/Settings";
import { api } from "./api/client";

function ProjectIndex() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [redirected, setRedirected] = useState<boolean>(false);

  useEffect(() => {
    if (redirected) return;
    let cancelled = false;
    api.getProject(id)
      .then((p) => {
        if (!cancelled) {
          navigate(`/projects/${id}/${p.current_stage}`, { replace: true });
          setRedirected(true);
        }
      })
      .catch(() => {
        if (!cancelled) navigate(`/projects/${id}/upload`, { replace: true });
      });
    return () => { cancelled = true; };
  }, [id, redirected, navigate]);

  if (redirected) return null;
  return <div style={{ padding: 40, textAlign: "center", color: "var(--ink-muted)" }}>Cargando proyecto…</div>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="projects/:id" element={<ProjectIndex />} />
          <Route path="projects/:id/:stage" element={<ProjectLayout />} />
          <Route path="results" element={<Results />} />
          <Route path="jobs" element={<Jobs />} />
          <Route path="models" element={<Models />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
