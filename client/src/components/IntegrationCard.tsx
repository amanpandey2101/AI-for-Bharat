"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Check,
  ExternalLink,
  Loader2,
  Trash2,
  AlertCircle,
} from "lucide-react";
import type { Integration } from "@/services/integrations";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

// ── Platform metadata ───────────────────────────────────────────────────────

type PlatformConfig = {
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  bgGradient: string;
  connectLabel: string;
  resourceLabel: string;
};

const PLATFORM_CONFIG: Record<string, PlatformConfig> = {
  github: {
    name: "GitHub",
    description: "Track PRs, code reviews, commits & issues",
    icon: (
      <svg viewBox="0 0 24 24" className="w-7 h-7" fill="currentColor">
        <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
      </svg>
    ),
    color: "text-gray-900",
    bgGradient: "from-gray-900/5 to-gray-900/10",
    connectLabel: "Connect GitHub",
    resourceLabel: "repositories",
  },
  gitlab: {
    name: "GitLab",
    description: "Track merge requests, notes & pushes",
    icon: (
      <svg viewBox="0 0 24 24" className="w-7 h-7" fill="currentColor">
        <path d="M23.955 13.587l-1.342-4.135-2.664-8.189a.455.455 0 00-.867 0L16.418 9.45H7.582L4.918 1.263a.455.455 0 00-.867 0L1.387 9.452.045 13.587a.924.924 0 00.331 1.023L12 23.054l11.624-8.443a.92.92 0 00.331-1.024" />
      </svg>
    ),
    color: "text-orange-600",
    bgGradient: "from-orange-500/5 to-orange-600/10",
    connectLabel: "Connect GitLab",
    resourceLabel: "projects",
  },
  slack: {
    name: "Slack",
    description: "Monitor decision discussions & threads",
    icon: (
      <svg viewBox="0 0 24 24" className="w-7 h-7" fill="currentColor">
        <path d="M5.042 15.165a2.528 2.528 0 01-2.52 2.523A2.528 2.528 0 010 15.165a2.527 2.527 0 012.522-2.52h2.52v2.52zm1.271 0a2.527 2.527 0 012.521-2.52 2.527 2.527 0 012.521 2.52v6.313A2.528 2.528 0 018.834 24a2.528 2.528 0 01-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 01-2.521-2.52A2.528 2.528 0 018.834 0a2.528 2.528 0 012.521 2.522v2.52H8.834zm0 1.271a2.528 2.528 0 012.521 2.521 2.528 2.528 0 01-2.521 2.521H2.522A2.528 2.528 0 010 8.834a2.528 2.528 0 012.522-2.521h6.312zm10.122 2.521a2.528 2.528 0 012.522-2.521A2.528 2.528 0 0124 8.834a2.528 2.528 0 01-2.522 2.521h-2.522V8.834zm-1.268 0a2.528 2.528 0 01-2.523 2.521 2.527 2.527 0 01-2.52-2.521V2.522A2.527 2.527 0 0115.165 0a2.528 2.528 0 012.523 2.522v6.312zm-2.523 10.122a2.528 2.528 0 012.523 2.522A2.528 2.528 0 0115.165 24a2.527 2.527 0 01-2.52-2.522v-2.522h2.52zm0-1.268a2.527 2.527 0 01-2.52-2.523 2.527 2.527 0 012.52-2.52h6.313A2.528 2.528 0 0124 15.165a2.528 2.528 0 01-2.522 2.523h-6.313z" />
      </svg>
    ),
    color: "text-purple-600",
    bgGradient: "from-purple-500/5 to-purple-600/10",
    connectLabel: "Add to Slack",
    resourceLabel: "channels",
  },
  jira: {
    name: "Jira",
    description: "Track issues, comments & sprint changes",
    icon: (
      <svg viewBox="0 0 24 24" className="w-7 h-7" fill="currentColor">
        <path d="M11.571 11.513H0a5.218 5.218 0 005.232 5.215h2.13v2.057A5.215 5.215 0 0012.575 24V12.518a1.005 1.005 0 00-1.005-1.005zm5.723-5.756H5.736a5.215 5.215 0 005.215 5.214h2.129v2.058a5.218 5.218 0 005.215 5.214V6.758a1.001 1.001 0 00-1.001-1.001zM23.013 0H11.455a5.215 5.215 0 005.215 5.215h2.129v2.057A5.215 5.215 0 0024.013 12.5V1.005A1.005 1.005 0 0023.013 0z" />
      </svg>
    ),
    color: "text-blue-600",
    bgGradient: "from-blue-500/5 to-blue-600/10",
    connectLabel: "Connect Jira",
    resourceLabel: "projects",
  },
};

// ── Component ─────────────────────────────────────────────────────────────────

interface IntegrationCardProps {
  platform: string;
  integration: Integration | null;
  onDisconnect: (platform: string) => void;
  onManage: (platform: string) => void;
  disconnecting: string | null;
}

export default function IntegrationCard({
  platform,
  integration,
  onDisconnect,
  onManage,
  disconnecting,
}: IntegrationCardProps) {
  const config = PLATFORM_CONFIG[platform];
  if (!config) return null;

  const isConnected = integration?.status === "active";
  const isDisconnecting = disconnecting === platform;

  return (
    <Card className="group relative overflow-hidden border border-border/50 hover:border-border hover:shadow-lg transition-all duration-300 cursor-default">
      {/* Gradient accent bar */}
      <div
        className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${config.bgGradient} ${
          isConnected ? "opacity-100" : "opacity-0 group-hover:opacity-60"
        } transition-opacity`}
      />

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`p-2.5 rounded-xl bg-gradient-to-br ${config.bgGradient} ${config.color}`}
            >
              {config.icon}
            </div>
            <div>
              <CardTitle className="text-lg font-semibold">
                {config.name}
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-0.5">
                {config.description}
              </p>
            </div>
          </div>

          {isConnected && (
            <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
              <Check className="w-3 h-3" />
              Connected
            </span>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {isConnected ? (
          <div className="space-y-4">
            {/* Connected info */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              {integration.platform_username && (
                <span className="font-medium text-foreground">
                  @{integration.platform_username}
                </span>
              )}
              {integration.connected_resources > 0 && (
                <span>
                  ·{" "}
                  <span className="font-medium text-foreground">
                    {integration.connected_resources}
                  </span>{" "}
                  {config.resourceLabel} monitored
                </span>
              )}
            </div>

            {/* Connected resources */}
            {integration.resources.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {integration.resources.slice(0, 5).map((r) => (
                  <span
                    key={r.id}
                    className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md ${
                      r.webhook_active
                        ? "bg-emerald-50 text-emerald-700"
                        : "bg-amber-50 text-amber-700"
                    }`}
                  >
                    {r.webhook_active ? (
                      <Check className="w-3 h-3" />
                    ) : (
                      <AlertCircle className="w-3 h-3" />
                    )}
                    {r.name}
                  </span>
                ))}
                {integration.resources.length > 5 && (
                  <span className="text-xs text-muted-foreground px-2 py-1">
                    +{integration.resources.length - 5} more
                  </span>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 pt-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onManage(platform)}
                className="flex-1 cursor-pointer"
              >
                <ExternalLink className="w-3.5 h-3.5 mr-1.5" />
                Manage {config.resourceLabel}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDisconnect(platform)}
                disabled={isDisconnecting}
                className="text-destructive hover:text-destructive hover:bg-destructive/10 cursor-pointer"
              >
                {isDisconnecting ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Trash2 className="w-3.5 h-3.5" />
                )}
              </Button>
            </div>
          </div>
        ) : (
          <a
            href={`${API_BASE}/integrations/${platform}/connect`}
            className=""
          >
            <Button className="w-full mt-1 cursor-pointer" type="button">
              {config.connectLabel}
            </Button>
          </a>
        )}
      </CardContent>
    </Card>
  );
}
