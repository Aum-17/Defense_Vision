import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AboutPage } from "./pages/AboutPage";
import { AnalysesPage } from "./pages/AnalysesPage";
import { AnalysisDetailPage } from "./pages/AnalysisDetailPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EvaluationPage } from "./pages/EvaluationPage";
import { NewAnalysisPage } from "./pages/NewAnalysisPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SettingsPage } from "./pages/SettingsPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/new" element={<NewAnalysisPage />} />
        <Route path="/analyses" element={<AnalysesPage />} />
        <Route path="/analyses/:id" element={<AnalysisDetailPage />} />
        <Route path="/evaluation" element={<EvaluationPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/about" element={<AboutPage />} />
      </Routes>
    </Layout>
  );
}
