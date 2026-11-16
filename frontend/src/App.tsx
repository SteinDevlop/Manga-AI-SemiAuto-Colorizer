/** Punto de entrada de la aplicación React con enrutado. */

import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import Projects from "./pages/Projects";
import { Upload } from "./pages/Upload";
import Analysis from "./pages/Analysis";
import Masks from "./pages/Masks";
import Editor from "./pages/Editor";
import Review from "./pages/Review";
import { Colorize } from "./pages/Colorize";
import { History } from "./pages/History";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="upload" element={<Upload />} />
          <Route path="analysis/:analysisId" element={<Analysis />} />
          <Route path="editor/:characterId" element={<Editor />} />
          <Route path="masks" element={<Masks />} />
          <Route path="approve/:analysisId" element={<Review />} />
          <Route path="colorize/:analysisId" element={<Colorize />} />
          <Route path="history" element={<History />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
