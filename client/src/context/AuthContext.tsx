"use client";

import { createContext, useContext, useMemo } from "react";
import { useSession } from "next-auth/react";

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
};

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  accessToken: null,
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

    console.log(`[Auth] status=${status}, user=${user?.email || "none"}, token=${accessToken ? "present" : "none"}`);

    return { user, loading, accessToken };
  }, [session, status]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
