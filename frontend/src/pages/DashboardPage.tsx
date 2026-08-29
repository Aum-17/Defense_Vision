import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  FolderSearch,
  Gauge,
  PlusCircle,
  Trash2,
  TriangleAlert,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/client";
import type { DashboardOverview, RecentAnalysis } from "../types";
import { Badge, Card, EmptyState, Spinner, StatCard, StatusBadge } from "../components/ui";
import { formatDate } from "../utils/format";

const SEV_COLORS = ["#ef4444", "#f59e0b", "#22c55e"];

export function DashboardPage() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [recent, setRecent] = useState<RecentAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [o, r] = await Promise.all([api.dashboardOverview(), api.recent()]);
        setOverview(o);
        setRecent(r);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function remove(id: number) {
    await api.deleteAnalysis(id);
    const [o, r] = await Promise.all([api.dashboardOverview(), api.recent()]);
    setOverview(o);
    setRecent(r);
  }

  if (loading) return <Spinner label="Loading dashboard…" />;
  if (error)
    return <EmptyState title="Unable to reach backend" body={error} />;

  const sevData = [
    { name: "High", value: overview!.high_severity },
    { name: "Medium", value: overview!.medium_severity },
    { name: "Low", value: overview!.low_severity },
  ];
  const statusData = Object.entries(overview!.analysis_status).map(([k, v]) => ({
    name: k.replace("_", " "),
    value: v,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Geospatial Analysis Overview</h1>
          <p className="text-sm text-slate-400">
            Infrastructure change detection decision-support dashboard
          </p>
        </div>
        <Link to="/new" className="btn-primary">
          <PlusCircle className="h-4 w-4" /> New Analysis
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <StatCard label="Total Analyses" value={overview!.total_analyses} icon={<FolderSearch />} />
        <StatCard label="Detected Changes" value={overview!.total_changes} icon={<Activity />} />
        <StatCard label="High Severity" value={overview!.high_severity} accent="text-red-300" icon={<AlertTriangle />} />
        <StatCard label="Medium Severity" value={overview!.medium_severity} accent="text-amber-300" icon={<TriangleAlert />} />
        <StatCard label="Low Severity" value={overview!.low_severity} accent="text-emerald-300" icon={<CheckCircle2 />} />
        <StatCard label="Avg Confidence" value={`${(overview!.average_confidence * 100).toFixed(0)}%`} icon={<Gauge />} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Severity Distribution" subtitle="Across all detections">
          {overview!.total_changes === 0 ? (
            <EmptyState title="No detections yet" />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={sevData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={2}>
                  {sevData.map((_, i) => (
                    <Cell key={i} fill={SEV_COLORS[i % SEV_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card title="Analysis Status" subtitle="Lifecycle state of analyses">
          {statusData.every((s) => s.value === 0) ? (
            <EmptyState title="No analyses yet" />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={statusData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }} />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      <Card
        title="Recent Analyses"
        actions={
          <Link to="/analyses" className="btn-ghost !py-1.5 text-xs">
            View all
          </Link>
        }
      >
        {recent.length === 0 ? (
          <EmptyState title="No analyses yet" body="Create a new analysis or load the demo." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-base-800 text-xs uppercase tracking-wide text-slate-400">
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Location</th>
                  <th className="py-2 pr-4">Date</th>
                  <th className="py-2 pr-4">Changes</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Model</th>
                  <th className="py-2 pr-4"></th>
                </tr>
              </thead>
              <tbody>
                {recent.map((r) => (
                  <tr key={r.id} className="border-b border-base-800/50 hover:bg-base-800/40">
                    <td className="py-2 pr-4">
                      <Link to={`/analyses/${r.id}`} className="font-medium text-accent-soft hover:underline">
                        {r.name}
                      </Link>
                    </td>
                    <td className="py-2 pr-4 text-slate-400">{r.area || "—"}</td>
                    <td className="py-2 pr-4 text-slate-400">{formatDate(r.created_at)}</td>
                    <td className="py-2 pr-4">
                      <Badge tone="blue">{r.detection_count}</Badge>
                    </td>
                    <td className="py-2 pr-4">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="py-2 pr-4 text-xs text-slate-400">{r.model_version || "—"}</td>
                    <td className="py-2 pr-4 text-right">
                      <button
                        onClick={() => remove(r.id)}
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
      </Card>
    </div>
  );
}
