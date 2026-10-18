"use client";

import Keycloak from "keycloak-js";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

type AuthContextValue = {
  authenticated: boolean;
  initializing: boolean;
  error: string | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  apiFetch: (path: string, init?: RequestInit) => Promise<Response>;
};

const keycloak = new Keycloak({
  url: process.env.NEXT_PUBLIC_KEYCLOAK_URL ?? "http://localhost:8080",
  realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM ?? "tcl-workhub",
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID ?? "tcl-workhub-web",
});

let initialization: Promise<boolean> | undefined;

function initializeKeycloak() {
  initialization ??= keycloak.init({
    onLoad: "check-sso",
    pkceMethod: "S256",
    checkLoginIframe: false,
  });
  return initialization;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  const [authenticated, setAuthenticated] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    initializeKeycloak()
      .then((isAuthenticated) => {
        if (active) {
          setAuthenticated(isAuthenticated);
          setInitializing(false);
        }
      })
      .catch(() => {
        if (active) {
          setError("Authentication service could not be initialized.");
          setInitializing(false);
        }
      });

    const refreshTimer = window.setInterval(() => {
      if (keycloak.authenticated) {
        keycloak.updateToken(30).catch(() => {
          keycloak.clearToken();
          setAuthenticated(false);
        });
      }
    }, 20_000);

    return () => {
      active = false;
      window.clearInterval(refreshTimer);
    };
  }, []);

  const login = useCallback(async () => {
    await keycloak.login({ redirectUri: window.location.origin });
  }, []);

  const logout = useCallback(async () => {
    await keycloak.logout({ redirectUri: window.location.origin });
  }, []);

  const apiFetch = useCallback(async (path: string, init: RequestInit = {}) => {
    if (!keycloak.authenticated) {
      throw new Error("You are not signed in.");
    }

    await keycloak.updateToken(30);
    const headers = new Headers(init.headers);
    headers.set("Authorization", `Bearer ${keycloak.token}`);
    headers.set("Accept", "application/json");

    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
    return fetch(`${backendUrl}${path}`, { ...init, headers });
  }, []);

  const value = useMemo(
    () => ({ authenticated, initializing, error, login, logout, apiFetch }),
    [authenticated, initializing, error, login, logout, apiFetch],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
