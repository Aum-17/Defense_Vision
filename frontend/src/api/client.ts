import type {
  Analysis,
  AnalysisCreate,
  AnalysisStats,
  DashboardOverview,
  Detection,
  EvaluationRow,
  RecentAnalysis,
} from "../types";

const BASE = "";

async function handle<T>(p: Promise<Response> | Response): Promise<T> {
  const res = await p;
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || res.statusText;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  async health() {
    return handle<{ status: string }>(await fetch(`${BASE}/api/health`));
  },

  // Analyses
  async createAnalysis(payload: AnalysisCreate): Promise<Analysis> {
    return handle(
      await fetch(`${BASE}/api/analyses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload, analysis_date: payload.analysis_date || null }),
      })
    );
  },
  listAnalyses(): Promise<Analysis[]> {
    return handle(fetch(`${BASE}/api/analyses`));
  },
  getAnalysis(id: number): Promise<Analysis> {
    return handle(fetch(`${BASE}/api/analyses/${id}`));
  },
  async uploadImage(id: number, type: "before" | "after", file: File): Promise<Analysis> {
    const fd = new FormData();
    fd.append("file", file);
    return handle(
      await fetch(`${BASE}/api/analyses/${id}/upload?type=${type}`, { method: "POST", body: fd })
    );
  },
  async process(id: number): Promise<Analysis> {
    return handle(await fetch(`${BASE}/api/analyses/${id}/process`, { method: "POST" }));
  },
  async deleteAnalysis(id: number): Promise<void> {
    await fetch(`${BASE}/api/analyses/${id}`, { method: "DELETE" });
  },
  stats(id: number): Promise<AnalysisStats> {
    return handle(fetch(`${BASE}/api/analyses/${id}/statistics`));
  },
  detections(id: number): Promise<Detection[]> {
    return handle(fetch(`${BASE}/api/analyses/${id}/detections`));
  },
  reportGenerated(id: number): Promise<{ filename: string; url: string; generated_at: string }> {
    return handle(
      fetch(`${BASE}/api/analyses/${id}/report`, { method: "POST" })
    );
  },

  // Detections / review
  getDetection(id: number): Promise<Detection> {
    return handle(fetch(`${BASE}/api/detections/${id}`));
  },
  async review(id: number, decision: string, comment: string, analyst: string) {
    return handle(
      await fetch(`${BASE}/api/detections/${id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision, comment, analyst }),
      })
    );
  },

  // Dashboard
  dashboardOverview(): Promise<DashboardOverview> {
    return handle(fetch(`${BASE}/api/dashboard/overview`));
  },
  recent(): Promise<RecentAnalysis[]> {
    return handle(fetch(`${BASE}/api/dashboard/recent`));
  },

  // Evaluation / demo
  evaluationCompare(): Promise<EvaluationRow[]> {
    return handle(fetch(`${BASE}/api/evaluation/compare`));
  },
  async loadDemo(): Promise<Analysis> {
    return handle(await fetch(`${BASE}/api/demo/load`, { method: "POST" }));
  },

  // Image/mask URLs
  imageUrl(id: number, type: "before" | "after"): string {
    return `${BASE}/api/analyses/${id}/image/${type}`;
  },
  maskUrl(id: number): string {
    return `${BASE}/api/analyses/${id}/mask`;
  },
  reportUrl(id: number): string {
    return `${BASE}/api/analyses/${id}/report`;
  },
};
