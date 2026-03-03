"use client";

import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import "./home.css";
import { AppSidebar } from "@/components/app-sidebar";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { WorkspaceProvider, useWorkspace } from "@/context/WorkspaceContext";
import { WorkspaceOnboarding } from "@/components/workspace-onboarding";
import { ChatWidget } from "@/components/ChatWidget";
import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

function DashboardGate({ children }: { children: React.ReactNode }) {
  const { loading: authLoading, user } = useAuth();
  const { loading: wsLoading, needsOnboarding } = useWorkspace();
  const router = useRouter();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      console.warn("[DashboardGate] Not authenticated. Redirecting to /login");
      router.replace("/login");
    }
  }, [authLoading, user, router]);

  if (authLoading || wsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-6 h-6 animate-spin text-violet-600" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-6 h-6 animate-spin text-violet-600" />
      </div>
    );
  }

  if (needsOnboarding) {
    return <WorkspaceOnboarding />;
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex-1 w-full min-w-0 overflow-auto">
        <SidebarTrigger />
        {children}
      </main>
      <ChatWidget />
    </SidebarProvider>
  );
}

export default function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <AuthProvider>
      <WorkspaceProvider>
        <DashboardGate>{children}</DashboardGate>
      </WorkspaceProvider>
    </AuthProvider>
  );
}
