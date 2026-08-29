import type { ReactNode } from "react";

export function Card({
  title,
  subtitle,
  children,
  className = "",
  actions,
}: {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
}) {
  return (
    <div className={`card p-5 ${className}`}>
      {(title || actions) && (
        <div className="mb-4 flex items-center justify-between">
          <div>
            {title && <h3 className="text-sm font-semibold text-slate-100">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-6 text-slate-400">
      <span className="spinner" />
      {label && <span className="text-sm">{label}</span>}
    </div>
  );
}

export function EmptyState({ title, body }: { title: string; body?: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-base-700 py-14 text-center">
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {body && <p className="mt-1 max-w-md text-xs text-slate-500">{body}</p>}
    </div>
  );
}

export function Badge({ children, tone = "slate" }: { children: ReactNode; tone?: string }) {
  const tones: Record<string, string> = {
    slate: "bg-base-700 text-slate-200",
    blue: "bg-blue-500/15 text-blue-300",
    green: "bg-emerald-500/15 text-emerald-300",
    amber: "bg-amber-500/15 text-amber-300",
    red: "bg-red-500/15 text-red-300",
    violet: "bg-violet-500/15 text-violet-300",
  };
  return <span className={`badge ${tones[tone] || tones.slate}`}>{children}</span>;
}

export function SeverityPill({ severity }: { severity?: string | null }) {
  const tone =
    (severity || "").toUpperCase() === "HIGH"
      ? "red"
      : (severity || "").toUpperCase() === "MEDIUM"
      ? "amber"
      : "green";
  return <Badge tone={tone}>{(severity || "NONE").toUpperCase()}</Badge>;
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { tone: string; label: string }> = {
    PENDING: { tone: "slate", label: "Pending" },
    PROCESSING: { tone: "blue", label: "Processing" },
    COMPLETED: { tone: "green", label: "Completed" },
    FAILED: { tone: "red", label: "Failed" },
    NEEDS_REVIEW: { tone: "amber", label: "Needs Review" },
    CONFIRMED: { tone: "green", label: "Confirmed" },
    REJECTED: { tone: "red", label: "Rejected" },
    PENDING_REVIEW: { tone: "amber", label: "Pending Review" },
  };
  const info = map[status] || { tone: "slate", label: status };
  return <Badge tone={info.tone}>{info.label}</Badge>;
}

export function StatCard({
  label,
  value,
  icon,
  accent = "text-slate-100",
}: {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  accent?: string;
}) {
  return (
    <div className="card flex items-center gap-4 p-5">
      {icon && (
        <div className="flex h-11 w-11 items-center justify-center rounded-md bg-base-800 text-accent-soft">
          {icon}
        </div>
      )}
      <div>
        <div className={`text-2xl font-bold ${accent}`}>{value}</div>
        <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
      </div>
    </div>
  );
}
