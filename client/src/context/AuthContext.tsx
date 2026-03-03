"use client";

import { createContext, useContext, useMemo } from "react";
import { useSession } from "next-auth/react";
import { setAccessToken } from "@/lib/axios";

type User = {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
};

type AuthContextType = {
  user: User | null;
  loading: boolean;
  accessToken: string | null;
  githubAccessToken: string | null;
};

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  accessToken: null,
  githubAccessToken: null,
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const { data: session, status } = useSession();

  const value = useMemo(() => {
    const loading = status === "loading";
    const user = session?.user
      ? {
          id: (session.user as { id?: string }).id || "",
          email: session.user.email || "",
          name: session.user.name || "",
          avatar_url: session.user.image || undefined,
        }
      : null;
    const accessToken = (session as { accessToken?: string })?.accessToken || null;
    const githubAccessToken = (session as { githubAccessToken?: string })?.githubAccessToken || null;

    // CRITICAL: Set token synchronously during render, BEFORE any child
    // useEffects fire (like WorkspaceProvider's getWorkspaces call).
    setAccessToken(accessToken);

    console.log(`[Auth] status=${status}, user=${user?.email || "none"}, token=${accessToken ? "present" : "none"}, ghToken=${githubAccessToken ? "present" : "none"}`);

    return { user, loading, accessToken, githubAccessToken };
  }, [session, status]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
