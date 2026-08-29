import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Download, FileText, Loader2 } from "lucide-react";
import { api } from "../api/client";
import type { Analysis } from "../types";
import { Card, EmptyState, Spinner } from "../components/ui";
import { formatDate } from "../utils/format";

export function ReportsPage() {
  const [rows, setRows] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setRows((await api.listAnalyses()).filter((a) => a.status === "COMPLETED"));
      } catch {
        /* handled by empty state */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function download(id: number) {
    setBusyId(id);
    setError("");
    try {
      await api.reportGenerated(id);
      window.open(api.reportUrl(id), "_blank", "noopener,noreferrer");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusyId(null);
    }
  }

  if (loading) return <Spinner label="Loading reports…" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Assessment Reports</h1>
        <p className="text-sm text-slate-400">Download generated PDF reports for completed analyses</p>
      </div>

      {error && <p className="text-sm text-red-300">{error}</p>}

      {rows.length === 0 ? (
        <EmptyState
          title="No completed analyses yet"
          body="Complete an analysis, then generate its report on the analysis detail page."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {rows.map((a) => (
            <Card key={a.id} title={a.name}>
              <div className="mb-3 space-y-1 text-sm text-slate-400">
                <p>{a.area || "No area"}</p>
                <p className="text-xs text-slate-500">{formatDate(a.created_at)}</p>
                <p className="text-xs text-slate-500">{a.detection_count} changes</p>
                <p className="text-xs text-slate-500">Model: {a.model_version || "unknown"}</p>
              </div>
              <div className="flex gap-2">
                <button
                  className="btn-primary flex-1"
                  disabled={busyId === a.id}
                  onClick={() => download(a.id)}
                >
                  {busyId === a.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4" />
                  )}
                  Download PDF
                </button>
                <Link to={`/analyses/${a.id}`} className="btn-outline">
                  <FileText className="h-4 w-4" />
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
