"use client";

import { useCallback, useEffect, useState } from "react";
import { apiError, ApiFetch, formatDateTime, formatDuration, WorkSession } from "./time-types";

export function AdminDashboard({ apiFetch }: { apiFetch: ApiFetch }) {
  const [sessions, setSessions] = useState<WorkSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch("/api/admin/time/sessions?limit=100");
      if (!response.ok) throw new Error(await apiError(response));
      setSessions(await response.json());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load sessions.");
    } finally {
      setLoading(false);
    }
  }, [apiFetch]);

  useEffect(() => {
    load();
  }, [load]);

  const activeCount = sessions.filter((session) => session.status === "open").length;
  const completedCount = sessions.filter((session) => session.status === "completed").length;

  return (
    <div className="workspace">
      <section className="admin-summary">
        <div>
          <p className="summary-value">{activeCount}</p>
          <p>Active sessions</p>
        </div>
        <div>
          <p className="summary-value">{completedCount}</p>
          <p>Completed sessions</p>
        </div>
        <div>
          <p className="summary-value">{sessions.length}</p>
          <p>Recent records</p>
        </div>
      </section>

      <section className="records-section">
        <div className="section-heading">
          <div>
            <p className="label">Administration</p>
            <h2>Employee time records</h2>
          </div>
          <button className="button button-secondary" disabled={loading} onClick={load} type="button">
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>
        {error && <p className="error">{error}</p>}
        {!loading && sessions.length === 0 && (
          <p className="empty-state">No employee sessions have been recorded yet.</p>
        )}
        {sessions.length > 0 && (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Employee</th>
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
                    <td className="employee-cell">{session.user_display_name}</td>
                    <td>{formatDateTime(session.started_at)}</td>
                    <td>{formatDateTime(session.ended_at)}</td>
                    <td>{formatDuration(session.break_seconds)}</td>
                    <td className="duration-cell">{formatDuration(session.worked_seconds)}</td>
                    <td><span className={`status-tag status-${session.status}`}>{session.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
