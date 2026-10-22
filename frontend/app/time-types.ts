export type ApiFetch = (path: string, init?: RequestInit) => Promise<Response>;

export type BreakType = "meal" | "rest" | "other";

export type WorkBreak = {
  id: string;
  started_at: string;
  ended_at: string | null;
  break_type: BreakType;
  notes: string | null;
  duration_seconds: number;
};

export type WorkSession = {
  id: string;
  user_id: string;
  user_display_name: string;
  started_at: string;
  ended_at: string | null;
  status: "open" | "completed" | "locked";
  source_timezone: string;
  notes: string | null;
  gross_seconds: number;
  break_seconds: number;
  worked_seconds: number;
  active_break: WorkBreak | null;
  breaks: WorkBreak[];
};

export type TimeStatus = {
  state: "checked_out" | "working" | "on_break";
  current_session: WorkSession | null;
};

export async function apiError(response: Response) {
  const body = await response.json().catch(() => null);
  return body?.detail ?? `Request failed with status ${response.status}`;
}

export function formatDuration(totalSeconds: number) {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;
  return [hours, minutes, remainder].map((value) => String(value).padStart(2, "0")).join(":");
}

export function formatDateTime(value: string | null) {
  if (!value) return "In progress";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatTime(value: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit" }).format(
    new Date(value),
  );
}
