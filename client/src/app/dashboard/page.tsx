"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Brain,
  Activity,
  Plug,
  Sparkles,
  TrendingUp,
  ArrowRight,
  Loader2,
  Zap,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getDecisionStats, type DecisionStats } from "@/services/decisions";
import { getIntegrations, type Integration } from "@/services/integrations";
import { getEvents, type ActivityEvent } from "@/services/events";
import { useAuth } from "@/context/AuthContext";

function timeAgo(timestamp: string) {
  const now = new Date();
  const date = new Date(timestamp);
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function DashboardHome() {
  const router = useRouter();
  const { user } = useAuth();
  const [stats, setStats] = useState<DecisionStats | null>(null);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [recentEvents, setRecentEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [statsRes, intRes, eventsRes] = await Promise.allSettled([
        getDecisionStats(),
        getIntegrations(),
        getEvents(undefined, 5),
      ]);

      if (statsRes.status === "fulfilled") setStats(statsRes.value.data);
      if (intRes.status === "fulfilled")
        setIntegrations(intRes.value.data.integrations || []);
      if (eventsRes.status === "fulfilled")
        setRecentEvents(eventsRes.value.data.events || []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const connectedCount = integrations.filter(
    (i) => i.status === "active"
  ).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 w-full">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-5xl mx-auto px-6 py-8">
      {/* Welcome */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight mb-1">
          Welcome back{user?.name ? `, ${user.name}` : ""}
        </h1>
        <p className="text-muted-foreground">
          Here&apos;s an overview of your organizational memory.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card className="bg-gradient-to-br from-blue-500/5 to-indigo-500/5 border-blue-200/50">
          <CardContent className="py-4 px-4">
            <div className="flex items-center gap-2 mb-1">
              <Brain className="w-4 h-4 text-blue-600" />
              <span className="text-xs text-muted-foreground font-medium">
                Decisions
              </span>
            </div>
            <p className="text-2xl font-bold">
              {stats?.total_decisions || 0}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-500/5 to-orange-500/5 border-amber-200/50">
          <CardContent className="py-4 px-4">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span className="text-xs text-muted-foreground font-medium">
                Needs Review
              </span>
            </div>
            <p className="text-2xl font-bold">
              {stats?.pending_validation || 0}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-500/5 to-green-500/5 border-emerald-200/50">
          <CardContent className="py-4 px-4">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span className="text-xs text-muted-foreground font-medium">
                Confidence
              </span>
            </div>
            <p className="text-2xl font-bold">
              {stats ? `${(stats.avg_confidence * 100).toFixed(0)}%` : "—"}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-violet-500/5 to-purple-500/5 border-violet-200/50">
          <CardContent className="py-4 px-4">
            <div className="flex items-center gap-2 mb-1">
              <Plug className="w-4 h-4 text-violet-600" />
              <span className="text-xs text-muted-foreground font-medium">
                Connected
              </span>
            </div>
            <p className="text-2xl font-bold">{connectedCount}/4</p>
          </CardContent>
        </Card>
      </div>

      {/* Actions grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {/* Getting started / Quick actions */}
        {connectedCount === 0 ? (
          <Card className="md:col-span-2 border-dashed border-2 border-violet-300/50 bg-gradient-to-br from-violet-500/5 to-indigo-500/5">
            <CardContent className="py-8 text-center">
              <Sparkles className="w-10 h-10 text-violet-500 mx-auto mb-3" />
              <h3 className="font-semibold text-lg mb-2">Get started</h3>
              <p className="text-sm text-muted-foreground mb-4 max-w-md mx-auto">
                Connect your first platform so Memora can start observing
                decisions from your workflow.
              </p>
              <Button
                onClick={() => router.push("/dashboard/integrations")}
                className="cursor-pointer"
              >
                <Plug className="w-4 h-4 mr-2" />
                Connect a Platform
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Decision memory card */}
            <Card
              className="cursor-pointer hover:shadow-md transition-all group"
              onClick={() => router.push("/dashboard/decisions")}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Brain className="w-5 h-5 text-blue-600" />
                  Decision Memory
                  <ArrowRight className="w-4 h-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  {stats?.total_decisions
                    ? `${stats.total_decisions} decisions discovered. ${stats.pending_validation} awaiting your review.`
                    : "AI will start discovering decisions from your connected platforms."}
                </p>
              </CardContent>
            </Card>

            {/* Activity feed card */}
            <Card
              className="cursor-pointer hover:shadow-md transition-all group"
              onClick={() => router.push("/dashboard/activity")}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="w-5 h-5 text-emerald-600" />
                  Activity Feed
                  <ArrowRight className="w-4 h-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  {recentEvents.length > 0
                    ? `${recentEvents.length} recent events from your workflow.`
                    : "Events will appear here as webhooks fire from your platforms."}
                </p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Recent events */}
      {recentEvents.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-500" />
              Recent Events
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y">
              {recentEvents.map((event) => (
                <div
                  key={event.event_id}
                  className="px-5 py-3 flex items-center gap-3"
                >
                  <span className="text-xs font-medium uppercase px-1.5 py-0.5 rounded bg-muted">
                    {event.platform}
                  </span>
                  <span className="text-sm truncate flex-1">
                    {event.title ||
                      event.event_type.replace(/_/g, " ")}
                  </span>
                  {event.author && (
                    <span className="text-xs text-muted-foreground">
                      {event.author}
                    </span>
                  )}
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {timeAgo(event.timestamp)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Platform overview */}
      <div className="mt-8">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Connected Platforms
        </h3>
        <div className="flex flex-wrap gap-2">
          {["github", "gitlab", "slack", "jira"].map((p) => {
            const connected = integrations.some(
              (i) => i.platform === p && i.status === "active"
            );
            return (
              <span
                key={p}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  connected
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "bg-muted text-muted-foreground border border-transparent"
                }`}
              >
                {connected && (
                  <CheckCircle2 className="w-3.5 h-3.5 inline mr-1.5 -mt-0.5" />
                )}
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}