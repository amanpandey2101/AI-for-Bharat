"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { Plug, RefreshCw, Loader2, Zap, FolderKanban } from "lucide-react";
import { Button } from "@/components/ui/button";
import IntegrationCard from "@/components/IntegrationCard";
import ResourceSelector from "@/components/ResourceSelector";
import { useWorkspace } from "@/context/WorkspaceContext";
import {
  getIntegrations,
  disconnectPlatform,
  type Integration,
} from "@/services/integrations";

const PLATFORMS = ["github", "gitlab", "slack", "jira"] as const;

function IntegrationsContent() {
  const searchParams = useSearchParams();
  const { activeWorkspace } = useWorkspace();
  const [integrations, setIntegrations] = useState<
    Record<string, Integration | null>
  >({});
  const [loading, setLoading] = useState(true);
  const [disconnecting, setDisconnecting] = useState<string | null>(null);
  const [managingPlatform, setManagingPlatform] = useState<string | null>(null);

  const fetchIntegrations = useCallback(async () => {
    try {
      setLoading(true);
      const res = await getIntegrations();
      const map: Record<string, Integration | null> = {};
      PLATFORMS.forEach((p) => {
        map[p] =
          res.data.integrations.find(
            (i: Integration) => i.platform === p
          ) ?? null;
      });
      setIntegrations(map);
    } catch {
      toast.error("Failed to load integrations");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchIntegrations();
  }, [fetchIntegrations]);

  // Show toast when redirected back from OAuth
  useEffect(() => {
    const connected = searchParams.get("connected");
    if (connected) {
      const name = connected.charAt(0).toUpperCase() + connected.slice(1);
      toast.success(`${name} connected successfully!`, {
        description: "You can now select resources to monitor.",
      });
      window.history.replaceState({}, "", "/dashboard/integrations");
      fetchIntegrations();
    }
  }, [searchParams, fetchIntegrations]);

  const handleDisconnect = async (platform: string) => {
    try {
      setDisconnecting(platform);
      await disconnectPlatform(platform);
      toast.success(
        `${platform.charAt(0).toUpperCase() + platform.slice(1)} disconnected`
      );
      setIntegrations((prev) => ({ ...prev, [platform]: null }));
    } catch {
      toast.error("Failed to disconnect");
    } finally {
      setDisconnecting(null);
    }
  };

  const handleManage = (platform: string) => {
    setManagingPlatform(platform);
  };

  const connectedCount = Object.values(integrations).filter(
    (i) => i?.status === "active"
  ).length;

  return (
    <div className="w-full max-w-5xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500/10 to-indigo-500/10">
              <Plug className="w-6 h-6 text-violet-600" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Integrations</h1>
          </div>
          <p className="text-muted-foreground max-w-lg">
            Connect your tools so Memora can passively observe decisions across
            your workflow. No manual logging needed.
          </p>
          {activeWorkspace && (
            <div className="flex items-center gap-1.5 mt-2 text-xs text-violet-600 bg-violet-50 px-2.5 py-1 rounded-full w-fit">
              <FolderKanban className="w-3 h-3" />
              Resources will be added to <strong>{activeWorkspace.name}</strong>
            </div>
          )}
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchIntegrations}
          disabled={loading}
          className="shrink-0"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin mr-1.5" />
          ) : (
            <RefreshCw className="w-4 h-4 mr-1.5" />
          )}
          Refresh
        </Button>
      </div>

      {/* Stats bar */}
      <div className="flex items-center gap-6 mb-8 px-4 py-3 bg-muted/50 rounded-xl border">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-500" />
          <span className="text-sm font-medium">
            {connectedCount}/{PLATFORMS.length} platforms connected
          </span>
        </div>
        <div className="h-4 w-px bg-border" />
        <span className="text-sm text-muted-foreground">
          {Object.values(integrations).reduce(
            (acc, i) => acc + (i?.connected_resources || 0),
            0
          )}{" "}
          resources monitored
        </span>
      </div>

      {/* Cards grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {PLATFORMS.map((platform) => (
            <IntegrationCard
              key={platform}
              platform={platform}
              integration={integrations[platform]}
              onDisconnect={handleDisconnect}
              onManage={handleManage}
              disconnecting={disconnecting}
            />
          ))}
        </div>
      )}

      {/* Help text */}
      <div className="mt-10 text-center text-sm text-muted-foreground space-y-1">
        <p>
          Once connected, Memora automatically captures decisions from your
          workflow.
        </p>
        <p>
          Webhooks are registered automatically — no manual configuration
          required.
        </p>
      </div>

      {/* Resource Selection Dialog */}
      {managingPlatform && (
        <ResourceSelector
          platform={managingPlatform}
          onClose={() => setManagingPlatform(null)}
          onSaved={fetchIntegrations}
        />
      )}
    </div>
  );
}

export default function IntegrationsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center py-20 w-full">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <IntegrationsContent />
    </Suspense>
  );
}
