"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { getWorkspaces, createWorkspace as createWsApi, type Workspace } from "@/services/workspaces";
import { useAuth } from "@/context/AuthContext";

interface WorkspaceContextType {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  setActiveWorkspace: (ws: Workspace | null) => void;
  createWorkspace: (name: string, description?: string) => Promise<Workspace>;
  refreshWorkspaces: () => Promise<void>;
  loading: boolean;
  needsOnboarding: boolean; // true when user has no workspaces
}

const WorkspaceContext = createContext<WorkspaceContextType>({
  workspaces: [],
  activeWorkspace: null,
  setActiveWorkspace: () => {},
  createWorkspace: async () => ({} as Workspace),
  refreshWorkspaces: async () => {},
  loading: true,
  needsOnboarding: false,
});

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspaceState] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);

  const refreshWorkspaces = useCallback(async () => {
    if (!user) {
      setLoading(false);
      return;
    }
    try {
      const res = await getWorkspaces();
      const wsList = res.data.workspaces || [];
      setWorkspaces(wsList);

      if (wsList.length === 0) {
        setNeedsOnboarding(true);
        setActiveWorkspaceState(null);
      } else {
        setNeedsOnboarding(false);
        // Restore active workspace from localStorage or pick first
        const savedId = localStorage.getItem("memora_active_workspace");
        const saved = wsList.find((w) => w.workspace_id === savedId);
        if (saved) {
          setActiveWorkspaceState(saved);
        } else {
          setActiveWorkspaceState(wsList[0]);
          localStorage.setItem("memora_active_workspace", wsList[0].workspace_id);
        }
      }
    } catch {
      // User may not be logged in yet
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    refreshWorkspaces();
  }, [refreshWorkspaces]);

  const setActiveWorkspace = (ws: Workspace | null) => {
    setActiveWorkspaceState(ws);
    if (ws) {
      localStorage.setItem("memora_active_workspace", ws.workspace_id);
    } else {
      localStorage.removeItem("memora_active_workspace");
    }
  };

  const createWorkspace = async (name: string, description: string = "") => {
    const res = await createWsApi(name, description);
    const ws = res.data.workspace;
    setWorkspaces((prev) => [ws, ...prev]);
    setActiveWorkspace(ws);
    setNeedsOnboarding(false);
    return ws;
  };

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        setActiveWorkspace,
        createWorkspace,
        refreshWorkspaces,
        loading,
        needsOnboarding,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export const useWorkspace = () => useContext(WorkspaceContext);
