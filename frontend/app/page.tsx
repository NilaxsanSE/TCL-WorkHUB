"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "./auth-provider";

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
  const [apiMessage, setApiMessage] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const loadProfile = useCallback(async () => {
    setApiError(null);
    try {
      const response = await apiFetch("/api/me");
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      setUser(await response.json());
    } catch (requestError) {
      setApiError(errorMessage(requestError));
    }
  }, [apiFetch]);

  useEffect(() => {
    if (authenticated) {
      loadProfile();
    } else {
      setUser(null);
    }
  }, [authenticated, loadProfile]);

  async function verifyRoleAccess() {
    if (!user) return;
    setApiMessage(null);
    setApiError(null);

    try {
      const response = await apiFetch(`/api/${user.role}`);
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const result: { message: string } = await response.json();
      setApiMessage(result.message);
    } catch (requestError) {
      setApiError(errorMessage(requestError));
    }
  }

  return (
    <main className="shell">
      <header className="brand-bar">
        <div>
          <p className="eyebrow">Technology Center Lanka</p>
          <h1>TCL WorkHub</h1>
        </div>
        {authenticated && (
          <button className="button button-secondary" onClick={logout} type="button">
            Sign out
          </button>
        )}
      </header>

      <section className="auth-panel" aria-live="polite">
        {initializing && <p className="status">Checking your session...</p>}
        {!initializing && error && <p className="error">{error}</p>}

        {!initializing && !error && !authenticated && (
          <div className="signed-out">
            <h2>Sign in to your workspace</h2>
            <p>Use your TCL WorkHub account to access your own work records.</p>
            <button className="button button-primary" onClick={login} type="button">
              Sign in
            </button>
          </div>
        )}

        {!initializing && authenticated && !user && !apiError && (
          <p className="status">Loading your WorkHub profile...</p>
        )}

        {authenticated && user && (
          <div className="profile">
            <div className="profile-heading">
              <div>
                <p className="label">Signed in as</p>
                <h2>{user.display_name}</h2>
                <p>{user.email}</p>
              </div>
              <span className={`role role-${user.role}`}>{user.role}</span>
            </div>

            <div className="access-row">
              <p>Your Keycloak identity is linked to a local WorkHub profile.</p>
              <button className="button button-primary" onClick={verifyRoleAccess} type="button">
                Verify {user.role} access
              </button>
            </div>
          </div>
        )}

        {apiMessage && <p className="success">{apiMessage}</p>}
        {apiError && (
          <div className="error-row">
            <p className="error">{apiError}</p>
            {authenticated && !user && (
              <button className="button button-secondary" onClick={loadProfile} type="button">
                Retry
              </button>
            )}
          </div>
        )}
      </section>
    </main>
  );
}

async function readApiError(response: Response) {
  const body = await response.json().catch(() => null);
  return body?.detail ?? `Request failed with status ${response.status}`;
}

function errorMessage(value: unknown) {
  return value instanceof Error ? value.message : "An unexpected error occurred.";
}
