import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Projects } from "./pages/Projects";
import { ProjectDetail } from "./pages/ProjectDetail";
import { NewAnalysis } from "./pages/NewAnalysis";
import { AnalysisReport } from "./pages/AnalysisReport";
import { Knowledge } from "./pages/Knowledge";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:id" element={<ProjectDetail />} />
          <Route path="/analysis/new" element={<NewAnalysis />} />
          <Route path="/analysis/:id" element={<AnalysisReport />} />
          <Route path="/knowledge" element={<Knowledge />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}