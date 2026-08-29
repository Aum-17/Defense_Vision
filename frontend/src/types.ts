export interface Analysis {
  id: number;
  name: string;
  area: string | null;
  latitude: number | null;
  longitude: number | null;
  description: string | null;
  analyst: string | null;
  analysis_date: string | null;
  model_version: string | null;
  status: string;
  error_message: string | null;
  processing_time: number | null;
  image_height: number | null;
  image_width: number | null;
  registration_quality: number | null;
  created_at: string;
  completed_at: string | null;
  has_before: boolean;
  has_after: boolean;
  detection_count: number;
}

export interface AnalysisCreate {
  name: string;
  area?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  description?: string | null;
  analyst?: string | null;
  analysis_date?: string | null;
}

export interface Detection {
  id: number;
  analysis_id: number;
  change_id: string;
  category: string | null;
  confidence: number;
  confidence_source: string;
  severity: string | null;
  area_pixels: number;
  change_percentage: number | null;
  bbox_json: string | null;
  coordinates_json: string | null;
  centroid_json: string | null;
  mean_intensity: number | null;
  status: string;
  model_version: string | null;
  evidence_json: string | null;
  created_at: string;
}

export interface DetectionStatistics {
  total: number;
  confirmed: number;
  rejected: number;
  needs_review: number;
  pending_review: number;
  high: number;
  medium: number;
  low: number;
  avg_confidence: number;
  categories: Record<string, number>;
}

export interface AnalysisStats {
  analysis_id: number;
  status: string;
  total_images: number;
  image_height: number | null;
  image_width: number | null;
  registration_quality: number | null;
  processing_time: number | null;
  detection_statistics: DetectionStatistics;
}

export interface Evidence {
  before: string;
  after: string;
  difference: string;
  mask: string;
}

export interface DashboardOverview {
  total_analyses: number;
  total_changes: number;
  high_severity: number;
  medium_severity: number;
  low_severity: number;
  average_confidence: number;
  analysis_status: Record<string, number>;
}

export interface RecentAnalysis {
  id: number;
  name: string;
  area: string | null;
  created_at: string;
  status: string;
  model_version: string | null;
  detection_count: number;
}

export interface EvaluationRow {
  method: string;
  precision: number | null;
  recall: number | null;
  f1: number | null;
  iou: number | null;
  dice: number | null;
  accuracy: number | null;
  false_positive_rate: number | null;
  false_negative_rate: number | null;
  evaluated: boolean;
  note: string;
}

export type Severity = "HIGH" | "MEDIUM" | "LOW" | string;
