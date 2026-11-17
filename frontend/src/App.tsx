/** Punto de entrada de la aplicación React con enrutado.
 *
 * Solo rutas globales (Workspace + System). El pipeline de cada proyecto
 * (Upload → Analysis → Character → Mask → Approve → Colorize → Export) vive
 * dentro de la ruta anidada /projects/:id, implementada en la Fase 5.
 */
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import Projects from "./pages/Projects";
import Results from "./pages/Results";
import Jobs from "./pages/Jobs";
import Models from "./pages/Models";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="projects/:id" element={<Projects />} />
          <Route path="results" element={<Results />} />
          <Route path="jobs" element={<Jobs />} />
          <Route path="models" element={<Models />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
