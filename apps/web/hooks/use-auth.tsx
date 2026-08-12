"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch, clearToken, getToken, setToken } from "@/lib/api-client";
import type { TokenResponse, User } from "@/types/auth";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (input: {
    email: string;
    password: string;
    full_name: string;
    organization_name: string;
  }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const loadUser = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const currentUser = await apiFetch<User>("/auth/me");
      setUser(currentUser);
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      const token = await apiFetch<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
        auth: false,
      });
      setToken(token.access_token);
      await loadUser();
      router.push("/dashboard");
    },
    [loadUser, router]
  );

  const register = useCallback(
    async (input: {
      email: string;
      password: string;
      full_name: string;
      organization_name: string;
    }) => {
      const token = await apiFetch<TokenResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify(input),
        auth: false,
      });
      setToken(token.access_token);
      await loadUser();
      router.push("/dashboard");
    },
    [loadUser, router]
  );

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
