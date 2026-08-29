import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PlusCircle, Trash2 } from "lucide-react";
import { api } from "../api/client";
import type { Analysis } from "../types";
import { Badge, EmptyState, Spinner, StatusBadge } from "../components/ui";
import { formatDate } from "../utils/format";

export function AnalysesPage() {
  const [rows, setRows] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    try {
      setRows(await api.listAnalyses());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function remove(id: number) {
    await api.deleteAnalysis(id);
    load();
  }

  if (loading) return <Spinner label="Loading analyses…" />;
  if (error) return <EmptyState title="Failed to load analyses" body={error} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Analyses</h1>
          <p className="text-sm text-slate-400">All geospatial change assessments</p>
        </div>
        <Link to="/new" className="btn-primary">
          <PlusCircle className="h-4 w-4" /> New Analysis
        </Link>
      </div>

      {rows.length === 0 ? (
        <EmptyState
          title="No analyses yet"
          body="Create a new analysis with imagery, or load the synthetic demo to see the pipeline in action."
        />
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-base-800 text-xs uppercase tracking-wide text-slate-400">
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Location</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Changes</th>
                <th className="px-4 py-3">Model</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <tr key={a.id} className="border-b border-base-800/40 hover:bg-base-800/40">
                  <td className="px-4 py-3">
                    <Link to={`/analyses/${a.id}`} className="font-medium text-accent-soft hover:underline">
                      {a.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-400">{a.area || "—"}</td>
                  <td className="px-4 py-3 text-slate-400">{formatDate(a.created_at)}</td>
                  <td className="px-4 py-3">
                    <Badge tone="blue">{a.detection_count}</Badge>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400">{a.model_version || "—"}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={a.status} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => remove(a.id)}
                      className="rounded p-1 text-slate-500 hover:bg-base-800 hover:text-red-300"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
