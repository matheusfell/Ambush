export type User = {
  id: number;
  username: string;
  role: "admin" | "viewer" | string;
  created_at: string;
};

export type MonitorHistoryItem = {
  id: number;
  result: string;
  checked_at: string;
};

export type MonitorCard = {
  id: number;
  name: string;
  url: string;
  enabled: boolean;
  interval_seconds: number;
  tags: string[];
  current_result: "UP" | "DEGRADED" | "DOWN" | string | null;
  last_checked_at: string | null;
  next_check_at: string | null;
  last_response_time_ms: number | null;
  uptime_24h_percent: number | null;
  history: MonitorHistoryItem[];
};

export type DashboardSummary = {
  up: number;
  degraded: number;
  down: number;
  paused: number;
  unknown: number;
  monitors: MonitorCard[];
};

export type MonitorCreatePayload = {
  name: string;
  url: string;
  method?: "GET" | "HEAD" | "POST" | "PUT" | "PATCH" | "DELETE";
  interval_seconds?: number;
  timeout_seconds?: number;
  expected_status?: number[];
  expected_body_contains?: string | null;
  retries?: number;
  slow_threshold_ms?: number;
  skip_tls_verify?: boolean;
  follow_redirects?: boolean;
  enabled?: boolean;
  tags?: string[];
};

export type MonitorDetails = {
  id: number;
  name: string;
  url: string;
  method: string;
  interval_seconds: number;
  timeout_seconds: number;
  expected_status: number[];
  expected_body_contains: string | null;
  headers: Record<string, unknown> | null;
  body: string | null;
  basic_auth_user: string | null;
  has_basic_auth_pass: boolean;
  skip_tls_verify: boolean;
  follow_redirects: boolean;
  retries: number;
  slow_threshold_ms: number;
  enabled: boolean;
  tags: string[];
  notification_group_id: number | null;
  created_at: string;
  updated_at: string;
  last_result: string | null;
  last_checked_at: string | null;
  last_response_time_ms: number | null;
};

export type Incident = {
  id: number;
  monitor_id: number;
  monitor_name: string | null;
  started_at: string;
  resolved_at: string | null;
  duration_seconds: number | null;
  failure_count: number;
  last_error: string | null;
  status: string;
};

export type CheckRecord = {
  id: number;
  monitor_id: number;
  checked_at: string;
  status_code: number | null;
  response_time_ms: number | null;
  result: string;
  error_message: string | null;
  response_body_excerpt: string | null;
  attempt_count: number;
};

export type CheckListResponse = {
  items: CheckRecord[];
  total: number;
  page: number;
  page_size: number;
};

export type SmtpSettings = {
  id: number;
  delivery_method: "graph" | "smtp" | string;
  graph_tenant_id: string | null;
  graph_client_id: string | null;
  has_graph_client_secret: boolean;
  host: string;
  port: number;
  username: string | null;
  has_password: boolean;
  from_email: string;
  from_name: string;
  use_tls: boolean;
  updated_at: string;
};

export type SmtpSettingsUpdate = {
  delivery_method?: "graph" | "smtp";
  graph_tenant_id?: string | null;
  graph_client_id?: string | null;
  graph_client_secret?: string | null;
  host?: string;
  port?: number;
  username?: string | null;
  password?: string | null;
  from_email?: string;
  from_name?: string;
  use_tls?: boolean;
};

export type EmailNotificationConfig = {
  id: number;
  monitor_id: number;
  enabled: boolean;
  emails: string[];
  failure_threshold: number;
  reminder_minutes: number;
  down_subject: string;
  down_body: string;
  recovery_subject: string;
  recovery_body: string;
  updated_at: string;
};

export type EmailNotificationConfigPayload = {
  monitor_id: number;
  enabled: boolean;
  emails: string[];
  failure_threshold: number;
  reminder_minutes: number;
  down_subject: string;
  down_body: string;
  recovery_subject: string;
  recovery_body: string;
};

const TOKEN_KEY = "ambush_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(path, { ...init, headers });
  if (res.status === 401) {
    setToken(null);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = (await res.json()) as { detail?: unknown };
      if (typeof data.detail === "string") detail = data.detail;
      else if (Array.isArray(data.detail)) detail = JSON.stringify(data.detail);
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  login: (username: string, password: string) =>
    request<{ access_token: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  me: () => request<User>("/api/auth/me"),
  dashboard: () => request<DashboardSummary>("/api/dashboard/summary"),
  monitor: (id: number) => request<MonitorDetails>(`/api/monitors/${id}`),
  createMonitor: (payload: MonitorCreatePayload) =>
    request<unknown>("/api/monitors", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateMonitor: (id: number, payload: MonitorCreatePayload) =>
    request<unknown>(`/api/monitors/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteMonitor: (id: number) =>
    request<void>(`/api/monitors/${id}`, { method: "DELETE" }),
  checkNow: (id: number) =>
    request<unknown>(`/api/monitors/${id}/check`, { method: "POST" }),
  monitorChecks: (id: number, pageSize = 1, page = 1) =>
    request<CheckListResponse>(
      `/api/monitors/${id}/checks?page=${page}&page_size=${pageSize}`,
    ),
  monitorCheck: (monitorId: number, checkId: number) =>
    request<CheckRecord>(`/api/monitors/${monitorId}/checks/${checkId}`),
  toggleMonitor: (id: number) =>
    request<unknown>(`/api/monitors/${id}/toggle`, { method: "PATCH" }),
  incidents: (status?: string) => {
    const q = status ? `?status=${encodeURIComponent(status)}` : "";
    return request<Incident[]>(`/api/incidents${q}`);
  },
  smtp: () => request<SmtpSettings>("/api/settings/smtp"),
  updateSmtp: (payload: SmtpSettingsUpdate) =>
    request<SmtpSettings>("/api/settings/smtp", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  testSmtp: (toEmail: string) =>
    request<{ status: string; detail: string }>("/api/settings/smtp/test", {
      method: "POST",
      body: JSON.stringify({ to_email: toEmail }),
    }),
  emailConfigs: () =>
    request<EmailNotificationConfig[]>("/api/settings/email-configs"),
  upsertEmailConfig: (
    monitorId: number,
    payload: EmailNotificationConfigPayload,
  ) =>
    request<EmailNotificationConfig>(`/api/settings/email-configs/${monitorId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteEmailConfig: (monitorId: number) =>
    request<void>(`/api/settings/email-configs/${monitorId}`, {
      method: "DELETE",
    }),
};
