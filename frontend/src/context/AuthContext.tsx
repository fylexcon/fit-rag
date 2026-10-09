"use client";

import { createContext, useCallback, useContext, useMemo, useSyncExternalStore } from "react";
import { api, tokenStore } from "@/lib/api";

interface AuthContextValue {
  token: string | null;
  isAuthenticated: boolean;
  /** False during SSR and hydration, before localStorage has been read. */
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const noopSubscribe = () => () => {};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const token = useSyncExternalStore(tokenStore.subscribe, tokenStore.get, () => null);
  const ready = useSyncExternalStore(noopSubscribe, () => true, () => false);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await api.login(email, password);
    tokenStore.set(access_token);
  }, []);

  const register = useCallback(
    async (email: string, password: string) => {
      await api.register(email, password);
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(() => tokenStore.set(null), []);

  const value = useMemo(
    () => ({ token, isAuthenticated: !!token, ready, login, register, logout }),
    [token, ready, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
