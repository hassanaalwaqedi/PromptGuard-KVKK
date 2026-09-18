export interface HealthResponse {
  status: "healthy";
  service: string;
  version: string;
}

export interface AnalyzeResponse {
  analysis_id: string;
  entity_count: number;
  entities: DetectedEntity[];
  status: "analyzed";
  ner_available: boolean;
  ner_provider: string;
  risk: RiskSummary;
  risk_factors: RiskFactor[];
  sanitized_prompt: string;
}

export interface DetectedEntity {
  type: string;
  text: string;
  start: number;
  end: number;
  confidence: number;
  source: string;
  metadata: Record<string, string>;
  category: string;
  base_weight: number;
  risk_contribution: number;
  reason: string;
  sanitization_action: "KEEP" | "PSEUDONYMIZE" | "MASK";
}

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type PolicyDecision = "ALLOW" | "WARN" | "MASK" | "BLOCK";

export interface RiskSummary {
  score: number;
  level: RiskLevel;
  decision: PolicyDecision;
}

export interface RiskFactor {
  kind: "entity" | "sensitivity" | "combination" | "repetition";
  rule: string;
  message: string;
  bonus: number;
  entity_type?: string | null;
}

interface ApiErrorPayload {
  detail?: string | Array<{ msg?: string }>;
}

export class ApiError extends Error {
  constructor(message: string, public readonly status?: number) {
    super(message);
    this.name = "ApiError";
  }
}

export function messageFromApiError(payload: ApiErrorPayload): string {
  if (typeof payload.detail === "string") return payload.detail;
  if (Array.isArray(payload.detail)) return payload.detail[0]?.msg ?? "Invalid request.";
  return "Request failed.";
}
