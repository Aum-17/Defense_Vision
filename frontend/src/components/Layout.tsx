import { NavLink } from "react-router-dom";
import {
  Crosshair,
  FileText,
  FolderSearch,
  Globe2,
  LayoutDashboard,
  LineChart,
  PlusCircle,
  Settings,
  Shield,
} from "lucide-react";
import type { ReactNode } from "react";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/new", label: "New Analysis", icon: PlusCircle },
  { to: "/analyses", label: "Analyses", icon: FolderSearch },
  { to: "/analyses", label: "Change Detection", icon: Crosshair },
  { to: "/analyses", label: "Geospatial View", icon: Globe2 },
  { to: "/evaluation", label: "Model Evaluation", icon: LineChart },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-full min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-20 flex w-60 flex-col border-r border-base-800 bg-base-900">
        <div className="flex items-center gap-2 px-5 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-accent">
            <Shield className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="text-base font-bold tracking-wide text-white">DEFENCEVISION</div>
            <div className="text-[10px] uppercase tracking-widest text-slate-500">
              Research Prototype
            </div>
          </div>
        </div>

        <nav className="mt-2 flex-1 space-y-1 px-3">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={label}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-accent/15 text-accent-soft"
                    : "text-slate-400 hover:bg-base-800 hover:text-slate-200"
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-base-800 px-4 py-4">
          <div className="rounded-md bg-base-950 p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
              AI assists the analyst
            </p>
            <p className="mt-1 text-[11px] leading-snug text-slate-400">
              Findings require human verification. No autonomous targeting or personnel
              analysis.
            </p>
          </div>
        </div>
      </aside>

      <main className="ml-60 flex-1 px-8 py-6">{children}</main>
    </div>
  );
}
