"use client";

import { createContext, useCallback, useContext, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";

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
const CURRENT_USER_KEY = ["auth", "me"];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [hasToken, setHasToken] = useState(() => Boolean(getToken()));
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: user, isLoading } = useQuery({
    queryKey: CURRENT_USER_KEY,
    queryFn: async () => {
      try {
        return await apiFetch<User>("/auth/me");
      } catch {
        clearToken();
        setHasToken(false);
        return null;
      }
    },
    enabled: hasToken,
    initialData: hasToken ? undefined : null,
    staleTime: 5 * 60_000,
  });

  const login = useCallback(
    async (email: string, password: string) => {
      const token = await apiFetch<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
        auth: false,
      });
      setToken(token.access_token);
      setHasToken(true);
      await queryClient.invalidateQueries({ queryKey: CURRENT_USER_KEY });
      router.push("/dashboard");
    },
    [queryClient, router]
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
      setHasToken(true);
      await queryClient.invalidateQueries({ queryKey: CURRENT_USER_KEY });
      router.push("/dashboard");
    },
    [queryClient, router]
  );

  const logout = useCallback(() => {
    clearToken();
    setHasToken(false);
    queryClient.setQueryData(CURRENT_USER_KEY, null);
    router.push("/login");
  }, [queryClient, router]);

  return (
    <AuthContext.Provider value={{ user: user ?? null, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
