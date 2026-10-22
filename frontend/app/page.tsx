"use client";

import { useCallback, useEffect, useState } from "react";
import { AdminDashboard } from "./admin-dashboard";
import { useAuth } from "./auth-provider";
import { EmployeeDashboard } from "./employee-dashboard";
import { apiError } from "./time-types";

type CurrentUser = {
  id: string;
  email: string;
  display_name: string;
  role: "employee" | "admin";
  active: boolean;
};

export default function Home() {
  const { authenticated, initializing, error, login, logout, apiFetch } = useAuth();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  const loadProfile = useCallback(async () => {
    setProfileError(null);
    try {
      const response = await apiFetch("/api/me");
      if (!response.ok) throw new Error(await apiError(response));
      setUser(await response.json());
    } catch (requestError) {
      setProfileError(
        requestError instanceof Error ? requestError.message : "Unable to load your profile.",
      );
    }
  }, [apiFetch]);

  useEffect(() => {
    if (authenticated) loadProfile();
    else setUser(null);
  }, [authenticated, loadProfile]);

  return (
    <main className="shell">
      <header className="brand-bar">
        <div>
          <p className="eyebrow">Technology Center Lanka</p>
          <h1>TCL WorkHub</h1>
        </div>
        {user && (
          <div className="account-actions">
            <div className="account-copy">
              <strong>{user.display_name}</strong>
              <span>{user.email}</span>
            </div>
            <span className={`role role-${user.role}`}>{user.role}</span>
            <button className="button button-secondary" onClick={logout} type="button">
              Sign out
            </button>
          </div>
        )}
      </header>

      {initializing && <section className="auth-panel"><p className="status">Checking your session...</p></section>}
      {!initializing && error && <section className="auth-panel"><p className="error">{error}</p></section>}

      {!initializing && !error && !authenticated && (
        <section className="auth-panel">
          <div className="signed-out">
            <h2>Sign in to your workspace</h2>
            <p>Use your TCL WorkHub account to manage work time and review records.</p>
            <button className="button button-primary" onClick={login} type="button">
              Sign in
            </button>
          </div>
        </section>
      )}

      {authenticated && !user && !profileError && (
        <section className="auth-panel"><p className="status">Loading your WorkHub profile...</p></section>
      )}

      {profileError && (
        <section className="auth-panel error-row">
          <p className="error">{profileError}</p>
          <button className="button button-secondary" onClick={loadProfile} type="button">Retry</button>
        </section>
      )}

      {user?.role === "employee" && <EmployeeDashboard apiFetch={apiFetch} />}
      {user?.role === "admin" && <AdminDashboard apiFetch={apiFetch} />}
    </main>
  );
}
