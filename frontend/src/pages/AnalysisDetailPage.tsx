import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  FileText,
  Gauge,
  Loader2,
  Trash2,
} from "lucide-react";
import { api } from "../api/client";
import type { Analysis, AnalysisStats, Detection } from "../types";
import { Badge, Card, EmptyState, SeverityPill, Spinner, StatCard, StatusBadge } from "../components/ui";
import { ImageViewer } from "../components/ImageViewer";
import { ChangeMap } from "../components/ChangeMap";
import { EvidenceModal } from "../components/EvidenceModal";
import { formatArea, formatDate, formatPct } from "../utils/format";

export function AnalysisDetailPage() {
  const { id } = useParams();
  const analysisId = Number(id);
  const navigate = useNavigate();

  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [stats, setStats] = useState<AnalysisStats | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [selected, setSelected] = useState<Detection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reportInfo, setReportInfo] = useState<string>("");
  const [reporting, setReporting] = useState(false);
  const [showMap, setShowMap] = useState(true);

  const load = useCallback(async () => {
    try {
      const a = await api.getAnalysis(analysisId);
      setAnalysis(a);
      const s = await api.stats(analysisId);
      setStats(s);
      const d = await api.detections(analysisId);
      setDetections(d);

      if (a.status === "PROCESSING" || a.status === "PENDING") {
        setTimeout(load, 1500);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [analysisId]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, [load]);

  async function handleReview(decision: string, comment: string) {
    if (!selected) return;
    await api.review(selected.id, decision, comment, analysis?.analyst || "analyst");
    setSelected(null);
    load();
  }

  async function generateReport() {
    setReporting(true);
    try {
      const info = await api.reportGenerated(analysisId);
      setReportInfo(info.filename);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setReporting(false);
    }
  }

  async function remove() {
    await api.deleteAnalysis(analysisId);
    navigate("/analyses");
  }

  if (loading && !analysis) return <Spinner label="Loading analysis…" />;
  if (error && !analysis) return <EmptyState title="Failed to load analysis" body={error} />;
  if (!analysis) return null;

  const st = stats?.detection_statistics;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-white">{analysis.name}</h1>
            <StatusBadge status={analysis.status} />
          </div>
          <p className="mt-1 text-sm text-slate-400">
            {analysis.area || "No area"} · {formatDate(analysis.created_at)}
          </p>
        </div>
        <div className="flex gap-2">
          {analysis.status === "COMPLETED" && (
            <a className="btn-primary" href={api.reportUrl(analysisId)} target="_blank" rel="noreferrer">
              <Download className="h-4 w-4" /> Open Report
            </a>
          )}
          <button className="btn-outline" onClick={remove}>
            <Trash2 className="h-4 w-4" /> Delete
          </button>
        </div>
      </div>

      {analysis.status === "PROCESSING" && (
        <Card className="border-blue-800 bg-blue-500/5">
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-accent" />
            <div>
              <p className="text-sm font-medium text-slate-200">Processing imagery</p>
              <p className="text-xs text-slate-400">
                Preprocessing → registration → change detection → region extraction. This page
                refreshes automatically.
              </p>
            </div>
          </div>
        </Card>
      )}

      {analysis.status === "FAILED" && (
        <Card className="border-red-800 bg-red-500/5">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-red-300" />
            <p className="text-sm text-red-200">{analysis.error_message || "Processing failed."}</p>
          </div>
        </Card>
      )}

      <Card title="Overview">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-6">
          <Info label="Model" value={analysis.model_version || "—"} />
          <Info label="Process Time" value={analysis.processing_time ? `${analysis.processing_time.toFixed(2)}s` : "—"} />
          <Info label="Image Size" value={analysis.image_width && analysis.image_height ? `${analysis.image_width}×${analysis.image_height}` : "—"} />
          <Info label="Registration" value={analysis.registration_quality !== null ? `${(analysis.registration_quality * 100).toFixed(0)}%` : "—"} />
          <Info label="Analyst" value={analysis.analyst || "—"} />
          <Info label="Coordinates" value={analysis.latitude !== null && analysis.longitude !== null ? "Provided" : "None"} />
        </div>
      </Card>

      {analysis.has_before && analysis.has_after ? (
        <Card title="Before / After Viewer" subtitle="Scroll to zoom · drag to pan · use tabs to switch modes">
          <ImageViewer
            beforeUrl={api.imageUrl(analysisId, "before")}
            afterUrl={api.imageUrl(analysisId, "after")}
            maskUrl={analysis.status === "COMPLETED" ? api.maskUrl(analysisId) : null}
            detections={detections}
            imageWidth={analysis.image_width}
            imageHeight={analysis.image_height}
          />
        </Card>
      ) : (
        <EmptyState
          title="Imagery not uploaded"
          body="Upload before and after images to enable the comparison viewer."
        />
      )}

      {st && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard label="Total Changes" value={st.total} />
          <StatCard label="High Severity" value={st.high} accent="text-red-300" icon={<AlertTriangle />} />
          <StatCard label="Medium Severity" value={st.medium} accent="text-amber-300" icon={<Gauge />} />
          <StatCard label="Avg Confidence" value={formatPct(st.avg_confidence)} icon={<CheckCircle2 />} />
        </div>
      )}

      {analysis.status === "COMPLETED" && (
        <Card
          title="Change List"
          subtitle={`${st?.confirmed || 0} confirmed · ${st?.rejected || 0} rejected · ${st?.needs_review || 0} needs review`}
        >
          {detections.length === 0 ? (
            <EmptyState title="No significant changes detected" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-base-800 text-xs uppercase tracking-wide text-slate-400">
                    <th className="py-2 pr-4">ID</th>
                    <th className="py-2 pr-4">Category</th>
                    <th className="py-2 pr-4">Severity</th>
                    <th className="py-2 pr-4">Confidence</th>
                    <th className="py-2 pr-4">Area</th>
                    <th className="py-2 pr-4">Status</th>
                    <th className="py-2 pr-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {detections.map((d) => (
                    <tr
                      key={d.id}
                      className="cursor-pointer border-b border-base-800/40 hover:bg-base-800/40"
                      onClick={() => setSelected(d)}
                    >
                      <td className="py-2 pr-4 font-mono text-xs text-slate-300">{d.change_id}</td>
                      <td className="py-2 pr-4 text-slate-200">{d.category}</td>
                      <td className="py-2 pr-4"><SeverityPill severity={d.severity} /></td>
                      <td className="py-2 pr-4 text-slate-300">{formatPct(d.confidence)}</td>
                      <td className="py-2 pr-4 text-slate-400">{formatArea(d.area_pixels)}</td>
                      <td className="py-2 pr-4"><StatusBadge status={d.status} /></td>
                      <td className="py-2 pr-4 text-right">
                        <Badge tone="blue">View evidence</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {analysis.status === "COMPLETED" && detections.length > 0 && (
        <Card
          title="Geospatial View"
          actions={
            <button className="btn-ghost !py-1 text-xs" onClick={() => setShowMap((v) => !v)}>
              {showMap ? "Hide" : "Show"}
            </button>
          }
        >
          {showMap && (
            <ChangeMap
              detections={detections}
              latitude={analysis.latitude}
              longitude={analysis.longitude}
              imageWidth={analysis.image_width}
              imageHeight={analysis.image_height}
            />
          )}
        </Card>
      )}

      <Card title="Assessment Report">
        <p className="mb-3 text-sm text-slate-400">
          Generate a professional PDF containing analysis information, executive summary,
          methodology, per-detection visual evidence, and limitations.
        </p>
        <div className="flex items-center gap-3">
          <button className="btn-primary" onClick={generateReport} disabled={reporting || analysis.status !== "COMPLETED"}>
            {reporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
            Generate Assessment Report
          </button>
          {reportInfo && <span className="text-xs text-emerald-300">Report generated: {reportInfo}</span>}
        </div>
        {analysis.status !== "COMPLETED" && (
          <p className="mt-2 text-xs text-slate-500">Reports can only be generated for completed analyses.</p>
        )}
      </Card>

      {selected && (
        <EvidenceModal det={selected} onClose={() => setSelected(null)} onReview={handleReview} />
      )}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-sm font-medium text-slate-200">{value}</div>
    </div>
  );
}
