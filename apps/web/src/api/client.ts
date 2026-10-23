const API_BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    let message = `خطا در ارتباط با سرور (${response.status})`;
    try {
      const data = JSON.parse(text);
      if (data.detail) message = data.detail;
    } catch {
      if (text) message = text;
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

async function upload<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `خطا در آپلود (${response.status})`);
  }
  return response.json();
}

// Types
export interface Project {
  id: number;
  name: string;
  parcel_code: string | null;
  description: string | null;
  created_at: string;
}

export interface ProjectFile {
  id: number;
  project_id: number;
  filename: string;
  size_bytes: number;
  status: string;
  error: string | null;
  detected_crs: string | null;
  created_at: string;
}

export interface Geometry {
  type: string;
  coordinates: number[][][] | number[][][][];
  crs?: string | null;
}

export interface Analysis {
  id: number;
  project_id: number;
  status: string;
  engine_version: string;
  result: {
    tests?: unknown[];
    rules?: RuleResult[];
    error?: string;
  } | null;
  created_at: string;
}

export interface RuleResult {
  rule_id: number | null;
  rule_code: string;
  kind: string;
  status: string;
  message: string;
  threshold: number | null;
  actual: number | null;
  source_reference: string | null;
  warnings: string[];
}

export interface Rule {
  id: number;
  code: string;
  title: string;
  kind: string;
  threshold: number;
  source_reference: string | null;
  version: string;
  is_active: boolean;
  is_verified: boolean;
  description: string | null;
}

export interface Report {
  report_id: string;
  report_version: string;
  generated_at: string;
  disclaimer: string;
  project: {
    id: number;
    name: string;
    parcel_code: string | null;
    description: string | null;
    created_at: string;
  };
  analysis: {
    id: number;
    status: string;
    engine_version: string;
    created_at: string;
  };
  summary: {
    overall_status: string;
    test_count: number;
    verified_count: number;
    failed_count: number;
    needs_review_count: number;
  };
  tests: Array<{
    name: string;
    status: string;
    reason: string | null;
    area_m2: number | null;
    perimeter_m: number | null;
    crs: string | null;
    warnings: string[];
  }>;
  warnings: string[];
  review_items: string[];
  assumptions: string[];
  limitations: string[];
  rules_applied: RuleResult[];
}

export interface KnowledgeSource {
  id: number;
  title: string;
  document_type: string | null;
  document_number: string | null;
  version: string;
  filename: string | null;
  size_bytes: number | null;
  page_count: number;
  extraction_status: string;
  extraction_error: string | null;
  is_verified: boolean;
  created_at: string;
}

export interface KnowledgeSearchHit {
  chunk_id: number;
  source_id: number;
  source_title: string;
  page_number: number;
  chunk_index: number;
  snippet: string;
}

// API
export const api = {
  health: () => request<{ status: string; version: string }>("/health".replace("/api/v1", "")),

  // Projects
  createProject: (data: { name: string; parcel_code?: string; description?: string }) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify(data) }),
  listProjects: () => request<Project[]>("/projects"),
  getProject: (id: number) => request<Project>(`/projects/${id}`),

  // Files
  uploadFile: (projectId: number, file: File) =>
    upload<ProjectFile>(`/projects/${projectId}/files`, file),
  getFile: (id: number) => request<ProjectFile>(`/files/${id}`),
  processFile: (id: number) =>
    request<ProjectFile>(`/files/${id}/process`, { method: "POST" }),

  // Parcels
  validateParcel: (geometry: Geometry & { crs?: string }) =>
    request<{
      valid: boolean;
      reason: string | null;
      area_m2: number | null;
      perimeter_m: number | null;
      crs: string | null;
      warnings: string[];
    }>("/parcels/validate", { method: "POST", body: JSON.stringify(geometry) }),

  // Analyses
  createAnalysis: (data: {
    project_id: number;
    file_id?: number;
    geometry?: Geometry & { crs?: string };
  }) => request<Analysis>("/analyses", { method: "POST", body: JSON.stringify(data) }),
  getAnalysis: (id: number) => request<Analysis>(`/analyses/${id}`),
  getReport: (id: number) => request<Report>(`/analyses/${id}/report`),

  // Rules
  listRules: () => request<Rule[]>("/rules"),

  // Knowledge
  listSources: () => request<KnowledgeSource[]>("/knowledge/sources"),
  createSource: (data: {
    title: string;
    document_type?: string;
    document_number?: string;
    version?: string;
    description?: string;
  }) => request<KnowledgeSource>("/knowledge/sources", { method: "POST", body: JSON.stringify(data) }),
  uploadDocument: (sourceId: number, file: File) =>
    upload<KnowledgeSource>(`/knowledge/sources/${sourceId}/document`, file),
  searchKnowledge: (q: string) =>
    request<KnowledgeSearchHit[]>(`/knowledge/search?q=${encodeURIComponent(q)}`),
};
