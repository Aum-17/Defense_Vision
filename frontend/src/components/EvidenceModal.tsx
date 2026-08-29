import { useState } from "react";
import { Check, MessageSquare, X, XCircle, RefreshCcw, FileSearch } from "lucide-react";
import type { Detection, Evidence } from "../types";
import { Badge, SeverityPill, StatusBadge } from "./ui";
import { formatArea, formatPct } from "../utils/format";

function parseEvidence(d: Detection): Evidence {
  try {
    return JSON.parse(d.evidence_json || "{}");
  } catch {
    return { before: "", after: "", difference: "", mask: "" };
  }
}

export function EvidenceModal({
  det,
  onClose,
  onReview,
}: {
  det: Detection;
  onClose: () => void;
  onReview: (decision: string, comment: string) => void;
}) {
  const ev = parseEvidence(det);
  const [decision, setDecision] = useState("");
  const [comment, setComment] = useState("");

  const grid = [
    { label: "Before", url: ev.before },
    { label: "After", url: ev.after },
    { label: "Difference", url: ev.difference },
    { label: "Change Mask", url: ev.mask },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-lg border border-base-700 bg-base-900 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-white">{det.change_id}</h3>
              <StatusBadge status={det.status} />
              <SeverityPill severity={det.severity} />
            </div>
            <p className="mt-1 text-sm text-slate-300">{det.category}</p>
          </div>
          <button onClick={onClose} className="rounded p-1 text-slate-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mb-4 flex flex-wrap gap-4 text-sm">
          <div>
            <span className="text-xs text-slate-500">Confidence</span>
            <div className="font-semibold text-white">{formatPct(det.confidence)}</div>
          </div>
          <div>
            <span className="text-xs text-slate-500">Source</span>
            <div className="font-semibold text-white capitalize">{det.confidence_source}</div>
          </div>
          <div>
            <span className="text-xs text-slate-500">Change Area</span>
            <div className="font-semibold text-white">{formatArea(det.area_pixels)}</div>
          </div>
          <div>
            <span className="text-xs text-slate-500">% of scene</span>
            <div className="font-semibold text-white">
              {det.change_percentage !== null ? `${det.change_percentage.toFixed(2)}%` : "—"}
            </div>
          </div>
          <div>
            <span className="text-xs text-slate-500">Model</span>
            <div className="font-semibold text-white text-xs">{det.model_version || "—"}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {grid.map((g) => (
            <figure key={g.label} className="rounded-md border border-base-800 bg-base-950 p-2">
              <figcaption className="mb-1 text-xs font-medium text-slate-400">{g.label}</figcaption>
              {g.url ? (
                <img src={g.url} alt={g.label} className="h-28 w-full rounded object-cover" loading="lazy" />
              ) : (
                <div className="flex h-28 items-center justify-center rounded bg-base-800 text-xs text-slate-500">
                  n/a
                </div>
              )}
            </figure>
          ))}
        </div>

        <div className="mt-5 rounded-md border border-base-800 bg-base-950 p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-200">
            <FileSearch className="h-4 w-4 text-accent" /> Analyst Review
          </div>
          <div>
            <p className="mb-2 text-xs text-slate-400">
              This is a <Badge tone="amber">potential</Badge> finding. Confirm only after visual
              verification against the evidence above.
            </p>
            <div className="mb-3 flex flex-wrap gap-2">
              <button
                onClick={() => setDecision("CONFIRMED")}
                className={`btn ${decision === "CONFIRMED" ? "bg-emerald-600 text-white" : "btn-outline"}`}
              >
                <Check className="h-4 w-4" /> Confirm
              </button>
              <button
                onClick={() => setDecision("REJECTED")}
                className={`btn ${decision === "REJECTED" ? "bg-red-600 text-white" : "btn-outline"}`}
              >
                <XCircle className="h-4 w-4" /> Reject
              </button>
              <button
                onClick={() => setDecision("NEEDS_REVIEW")}
                className={`btn ${decision === "NEEDS_REVIEW" ? "bg-amber-600 text-white" : "btn-outline"}`}
              >
                <RefreshCcw className="h-4 w-4" /> Needs Review
              </button>
            </div>
            <div className="mb-3 flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-slate-500" />
              <input
                className="input"
                placeholder="Optional analyst comment…"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />
            </div>
            <button
              className="btn-primary ml-auto block"
              disabled={!decision}
              onClick={() => onReview(decision, comment)}
            >
              Save Review
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
