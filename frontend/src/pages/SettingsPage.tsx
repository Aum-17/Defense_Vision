import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Database, FolderOpen, Loader2, PlayCircle } from "lucide-react";
import { api } from "../api/client";
import { Card } from "../components/ui";

export function SettingsPage() {
  const navigate = useNavigate();
  const [demoBusy, setDemoBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function loadDemo() {
    setDemoBusy(true);
    setMsg("");
    try {
      const a = await api.loadDemo();
      setMsg(`Demo analysis #${a.id} created. Opening…`);
      setTimeout(() => navigate(`/analyses/${a.id}`), 800);
    } catch (e) {
      setMsg(`Failed: ${(e as Error).message}`);
    } finally {
      setDemoBusy(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Settings</h1>
        <p className="text-sm text-slate-400">Configuration, demo mode and environment</p>
      </div>

      <Card title="Demo Mode" subtitle="Run the platform without an external dataset">
        <p className="mb-3 text-sm text-slate-400">
          Generates synthetic public demonstration imagery with obvious infrastructure-like
          changes and runs the full pipeline. The data is clearly labelled{" "}
          <span className="text-amber-300">PUBLIC / SYNTHETIC DEMONSTRATION DATA</span> and is not
          real imagery.
        </p>
        <button className="btn-primary" onClick={loadDemo} disabled={demoBusy}>
          {demoBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-4 w-4" />}
          Load Demo Analysis
        </button>
        {msg && <p className="mt-2 text-xs text-slate-300">{msg}</p>}
      </Card>

      <Card title="Data Directories" subtitle="Where artefacts are stored (see docker-compose volume)">
        <ul className="space-y-1 text-sm text-slate-300">
          <li className="flex items-center gap-2"><Database className="h-4 w-4 text-accent" /> PostgreSQL + PostGIS (SQLite fallback)</li>
          <li className="flex items-center gap-2"><FolderOpen className="h-4 w-4 text-accent" /> data/raw · data/processed · data/demo · data/annotations · data/output · data/uploads</li>
        </ul>
      </Card>

      <Card title="Security & Privacy">
        <ul className="space-y-1 text-sm text-slate-300">
          <li>• Uploads validated (type, size, integrity, path-traversal safe)</li>
          <li>• Config via environment variables — no hardcoded credentials</li>
          <li>• No classified or sensitive data required</li>
        </ul>
      </Card>
    </div>
  );
}
