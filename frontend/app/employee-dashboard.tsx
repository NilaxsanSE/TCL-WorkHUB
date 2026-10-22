"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  apiError,
  ApiFetch,
  BreakType,
  formatDateTime,
  formatDuration,
  formatTime,
  TimeStatus,
  WorkSession,
} from "./time-types";

type Props = { apiFetch: ApiFetch };

export function EmployeeDashboard({ apiFetch }: Props) {
  const [timeStatus, setTimeStatus] = useState<TimeStatus | null>(null);
  const [sessions, setSessions] = useState<WorkSession[]>([]);
  const [breakType, setBreakType] = useState<BreakType>("rest");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [snapshotAt, setSnapshotAt] = useState(Date.now());
  const [clock, setClock] = useState(Date.now());

  const load = useCallback(async () => {
    const [statusResponse, sessionsResponse] = await Promise.all([
      apiFetch("/api/time/status"),
      apiFetch("/api/time/sessions?limit=30"),
    ]);
    if (!statusResponse.ok) throw new Error(await apiError(statusResponse));
    if (!sessionsResponse.ok) throw new Error(await apiError(sessionsResponse));
    setTimeStatus(await statusResponse.json());
    setSessions(await sessionsResponse.json());
    setSnapshotAt(Date.now());
  }, [apiFetch]);

  useEffect(() => {
    load().catch((requestError) => setError(messageFor(requestError)));
  }, [load]);

  useEffect(() => {
    const timer = window.setInterval(() => setClock(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const liveWorkedSeconds = useMemo(() => {
    const current = timeStatus?.current_session;
    if (!current) return 0;
    const runningSeconds =
      timeStatus.state === "working" ? Math.floor((clock - snapshotAt) / 1000) : 0;
    return current.worked_seconds + runningSeconds;
  }, [clock, snapshotAt, timeStatus]);

  async function perform(path: string, body?: object) {
    setBusy(true);
    setError(null);
    try {
      const response = await apiFetch(path, {
        method: "POST",
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!response.ok) throw new Error(await apiError(response));
      setNotes("");
      await load();
    } catch (requestError) {
      setError(messageFor(requestError));
    } finally {
      setBusy(false);
    }
  }

  if (!timeStatus) return <p className="status">Loading your time records...</p>;

  const current = timeStatus.current_session;
  return (
    <div className="workspace">
      <section className="time-console" aria-live="polite">
        <div className="console-heading">
          <div>
            <p className="label">Today</p>
            <h2>{statusLabel(timeStatus.state)}</h2>
          </div>
          <span className={`state state-${timeStatus.state}`}>
            {timeStatus.state.replace("_", " ")}
          </span>
        </div>

        <div className="timer" aria-label="Worked time">
          {formatDuration(liveWorkedSeconds)}
        </div>
        <p className="timer-caption">
          {current ? `Checked in ${formatDateTime(current.started_at)}` : "No active work session"}
        </p>

        {timeStatus.state === "checked_out" && (
          <div className="action-area">
            <label className="field">
              <span>Work note</span>
              <textarea
                maxLength={2000}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Optional note for this session"
                rows={3}
                value={notes}
              />
            </label>
            <button
              className="button button-primary button-large"
              disabled={busy}
              onClick={() =>
                perform("/api/time/check-in", {
                  source_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                  notes: notes || null,
                })
              }
              type="button"
            >
              {busy ? "Checking in..." : "Check in"}
            </button>
          </div>
        )}

        {timeStatus.state === "working" && (
          <div className="action-grid">
            <div className="action-group">
              <label className="field compact-field">
                <span>Break type</span>
                <select
                  onChange={(event) => setBreakType(event.target.value as BreakType)}
                  value={breakType}
                >
                  <option value="rest">Rest</option>
                  <option value="meal">Meal</option>
                  <option value="other">Other</option>
                </select>
              </label>
              <button
                className="button button-secondary"
                disabled={busy}
                onClick={() => perform("/api/time/breaks/start", { break_type: breakType })}
                type="button"
              >
                Start break
              </button>
            </div>
            <button
              className="button button-danger"
              disabled={busy}
              onClick={() => perform("/api/time/check-out", { notes: notes || null })}
              type="button"
            >
              Check out
            </button>
          </div>
        )}

        {timeStatus.state === "on_break" && (
          <div className="action-area">
            <p className="break-notice">
              {current?.active_break?.break_type} break started at{" "}
              {formatTime(current?.active_break?.started_at ?? null)}
            </p>
            <button
              className="button button-primary button-large"
              disabled={busy}
              onClick={() => perform("/api/time/breaks/end")}
              type="button"
            >
              {busy ? "Ending break..." : "End break"}
            </button>
          </div>
        )}

        {error && <p className="error">{error}</p>}
      </section>

      <section className="records-section">
        <div className="section-heading">
          <div>
            <p className="label">Recent activity</p>
            <h2>Your sessions</h2>
          </div>
          <button className="button button-secondary" onClick={() => load()} type="button">
            Refresh
          </button>
        </div>
        <SessionTable sessions={sessions} />
      </section>
    </div>
  );
}

function SessionTable({ sessions }: { sessions: WorkSession[] }) {
  if (sessions.length === 0) return <p className="empty-state">No work sessions recorded yet.</p>;
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Check in</th>
            <th>Check out</th>
            <th>Breaks</th>
            <th>Worked</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {sessions.map((session) => (
            <tr key={session.id}>
              <td>{new Intl.DateTimeFormat().format(new Date(session.started_at))}</td>
              <td>{formatTime(session.started_at)}</td>
              <td>{formatTime(session.ended_at)}</td>
              <td>{formatDuration(session.break_seconds)}</td>
              <td className="duration-cell">{formatDuration(session.worked_seconds)}</td>
              <td><span className={`status-tag status-${session.status}`}>{session.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function statusLabel(state: TimeStatus["state"]) {
  if (state === "working") return "Work session in progress";
  if (state === "on_break") return "Break in progress";
  return "Ready to begin";
}

function messageFor(value: unknown) {
  return value instanceof Error ? value.message : "An unexpected error occurred.";
}
