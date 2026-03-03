"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { getMe } from "@/services/auth";

type User = {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
};

type AuthContextType = {
  user: User | null;
  loading: boolean;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  refreshUser: async () => {},
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    console.log("[Auth] 🔍 Checking session via /auth/me...");
    try {
      const data = await getMe();
      console.log("[Auth] ✅ Session valid. User:", data.data);
      setUser(data.data);
    } catch (err) {
      console.warn("[Auth] ⚠️ Session check failed (not logged in or cookie blocked):", err);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <AuthContext.Provider value={{ user, loading, refreshUser: checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
