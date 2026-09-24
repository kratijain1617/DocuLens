"use client";

import { client } from "@/lib/api";
import type { User } from "@/lib/types";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

type AuthState = {
  user: User | null;
  token: string | null;
  ready: boolean;
  setSession: (token: string, user: User) => void;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem("doculens_token");
    const savedUser = localStorage.getItem("doculens_user");
    if (!savedToken || !savedUser) {
      setReady(true);
      return;
    }
    setToken(savedToken);
    try {
      setUser(JSON.parse(savedUser) as User);
    } catch {
      localStorage.removeItem("doculens_user");
    }
    client
      .me(savedToken)
      .then((fresh) => {
        setUser(fresh);
        localStorage.setItem("doculens_user", JSON.stringify(fresh));
      })
      .catch(() => {
        localStorage.removeItem("doculens_token");
        localStorage.removeItem("doculens_user");
        setToken(null);
        setUser(null);
      })
      .finally(() => setReady(true));
  }, []);

  const setSession = useCallback((nextToken: string, nextUser: User) => {
    localStorage.setItem("doculens_token", nextToken);
    localStorage.setItem("doculens_user", JSON.stringify(nextUser));
    setToken(nextToken);
    setUser(nextUser);
  }, []);

  const logout = useCallback(async () => {
    if (token) {
      try {
        await client.logout(token);
      } catch {
        /* The local session is cleared either way. */
      }
    }
    localStorage.removeItem("doculens_token");
    localStorage.removeItem("doculens_user");
    setToken(null);
    setUser(null);
  }, [token]);

  const value = useMemo<AuthState>(
    () => ({ user, token, ready, setSession, logout }),
    [logout, ready, setSession, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("AuthProvider is missing.");
  return value;
}
