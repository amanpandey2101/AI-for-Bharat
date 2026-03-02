"use client";

import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import {
  Activity,
  RefreshCw,
  Loader2,
  GitPullRequest,
  MessageSquare,
  GitCommit,
  AlertCircle,
  CheckCircle2,
  Clock,
  Filter,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getEvents, type ActivityEvent } from "@/services/events";

const PLATFORM_COLORS: Record<string, string> = {
  github: "bg-gray-900 text-white",
  gitlab: "bg-orange-500 text-white",
  slack: "bg-purple-600 text-white",
  jira: "bg-blue-600 text-white",
};

const EVENT_ICONS: Record<string, React.ReactNode> = {
  pr_created: <GitPullRequest className="w-4 h-4" />,
  pr_merged: <GitPullRequest className="w-4 h-4" />,
  review_submitted: <CheckCircle2 className="w-4 h-4" />,
  push: <GitCommit className="w-4 h-4" />,
  comment: <MessageSquare className="w-4 h-4" />,
  issue_created: <AlertCircle className="w-4 h-4" />,
  issue_updated: <AlertCircle className="w-4 h-4" />,
  message: <MessageSquare className="w-4 h-4" />,
};

const PLATFORMS = ["all", "github", "gitlab", "slack", "jira"] as const;

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

function formatEventType(type: string): string {
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ActivityPage() {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [platform, setPlatform] = useState<string>("all");

  const fetchEvents = useCallback(async () => {
    try {
      setLoading(true);
      const res = await getEvents(
        platform === "all" ? undefined : platform
      );
      setEvents(res.data.events || []);
    } catch {
      toast.error("Failed to load activity");
    } finally {
      setLoading(false);
    }
  }, [platform]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  return (
    <div className="w-full max-w-5xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500/10 to-teal-500/10">
              <Activity className="w-6 h-6 text-emerald-600" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">
              Activity Feed
            </h1>
          </div>
          <p className="text-muted-foreground max-w-lg">
            Real-time stream of events from all connected platforms. These events
            are processed by the AI to discover decisions.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchEvents}
          disabled={loading}
          className="shrink-0 cursor-pointer"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin mr-1.5" />
          ) : (
            <RefreshCw className="w-4 h-4 mr-1.5" />
          )}
          Refresh
        </Button>
      </div>

      {/* Platform filter */}
      <div className="flex items-center gap-2 mb-6">
        <Filter className="w-4 h-4 text-muted-foreground" />
        {PLATFORMS.map((p) => (
          <Button
            key={p}
            variant={platform === p ? "default" : "outline"}
            size="sm"
            onClick={() => setPlatform(p)}
            className="capitalize cursor-pointer"
          >
            {p}
          </Button>
        ))}
      </div>

      {/* Events */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : events.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <Activity className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
            <p className="text-muted-foreground font-medium">
              No events yet
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              Events will appear here once your connected platforms start
              sending webhooks.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {events.map((event) => (
            <Card
              key={event.event_id}
              className="hover:shadow-md transition-shadow"
            >
              <CardContent className="py-4 px-5">
                <div className="flex items-start gap-4">
                  {/* Platform badge */}
                  <div
                    className={`px-2 py-1 rounded-md text-xs font-medium uppercase shrink-0 ${
                      PLATFORM_COLORS[event.platform] || "bg-gray-200"
                    }`}
                  >
                    {event.platform}
                  </div>

                  {/* Event icon */}
                  <div className="mt-0.5 text-muted-foreground shrink-0">
                    {EVENT_ICONS[event.event_type] || (
                      <Activity className="w-4 h-4" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm truncate">
                        {event.title || formatEventType(event.event_type)}
                      </span>
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded ${
                          event.status === "processed"
                            ? "bg-emerald-50 text-emerald-600"
                            : event.status === "failed"
                            ? "bg-red-50 text-red-600"
                            : "bg-amber-50 text-amber-600"
                        }`}
                      >
                        {event.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                      <span className="px-1.5 py-0.5 bg-muted/80 rounded text-xs">
                        {formatEventType(event.event_type)}
                      </span>
                      {event.author && (
                        <span className="font-medium">{event.author}</span>
                      )}
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {timeAgo(event.timestamp)}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
