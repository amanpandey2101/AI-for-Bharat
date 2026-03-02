"use client";

import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import {
  Brain,
  RefreshCw,
  Loader2,
  Filter,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Archive,
  Clock,
  ChevronRight,
  ThumbsUp,
  ThumbsDown,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getDecisions,
  getDecisionStats,
  validateDecision,
  type Decision,
  type DecisionStats,
} from "@/services/decisions";

const STATUS_CONFIG: Record<
  string,
  { label: string; icon: React.ReactNode; color: string }
> = {
  inferred: {
    label: "AI Inferred",
    icon: <Sparkles className="w-3.5 h-3.5" />,
    color: "bg-amber-50 text-amber-700 border-amber-200",
  },
  validated: {
    label: "Validated",
    icon: <CheckCircle2 className="w-3.5 h-3.5" />,
    color: "bg-emerald-50 text-emerald-700 border-emerald-200",
  },
  disputed: {
    label: "Disputed",
    icon: <XCircle className="w-3.5 h-3.5" />,
    color: "bg-red-50 text-red-700 border-red-200",
  },
  superseded: {
    label: "Superseded",
    icon: <Archive className="w-3.5 h-3.5" />,
    color: "bg-gray-50 text-gray-600 border-gray-200",
  },
  archived: {
    label: "Archived",
    icon: <Archive className="w-3.5 h-3.5" />,
    color: "bg-gray-50 text-gray-500 border-gray-200",
  },
};

const STATUS_FILTERS = [
  "all",
  "inferred",
  "validated",
  "disputed",
] as const;

function confidenceColor(score: number): string {
  if (score >= 0.8) return "text-emerald-600";
  if (score >= 0.6) return "text-amber-600";
  return "text-red-500";
}

function confidenceBar(score: number): string {
  if (score >= 0.8) return "bg-emerald-500";
  if (score >= 0.6) return "bg-amber-500";
  return "bg-red-500";
}

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

export default function DecisionsPage() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [stats, setStats] = useState<DecisionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [validatingId, setValidatingId] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [decisionsRes, statsRes] = await Promise.all([
        getDecisions(statusFilter === "all" ? undefined : statusFilter),
        getDecisionStats(),
      ]);
      setDecisions(decisionsRes.data.decisions);
      setStats(statsRes.data);
    } catch {
      toast.error("Failed to load decisions");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleValidate = async (id: string, action: "validated" | "disputed") => {
    try {
      setValidatingId(id);
      await validateDecision(id, action);
      toast.success(`Decision ${action}`);
      fetchData();
    } catch {
      toast.error("Failed to update decision");
    } finally {
      setValidatingId(null);
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500/10 to-indigo-500/10">
              <Brain className="w-6 h-6 text-blue-600" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">
              Decision Memory
            </h1>
          </div>
          <p className="text-muted-foreground max-w-lg">
            AI-inferred technical decisions extracted from your workflow.
            Validate or dispute to improve accuracy.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchData}
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

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="py-4 px-4">
              <p className="text-2xl font-bold">{stats.total_decisions}</p>
              <p className="text-xs text-muted-foreground">Total decisions</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4 px-4">
              <p className="text-2xl font-bold text-amber-600">
                {stats.pending_validation}
              </p>
              <p className="text-xs text-muted-foreground">
                Pending validation
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4 px-4">
              <p className={`text-2xl font-bold ${confidenceColor(stats.avg_confidence)}`}>
                {(stats.avg_confidence * 100).toFixed(0)}%
              </p>
              <p className="text-xs text-muted-foreground">Avg. confidence</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4 px-4">
              <p className="text-2xl font-bold">
                {Object.keys(stats.by_platform).length}
              </p>
              <p className="text-xs text-muted-foreground">Platforms active</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Status filter */}
      <div className="flex items-center gap-2 mb-6">
        <Filter className="w-4 h-4 text-muted-foreground" />
        {STATUS_FILTERS.map((s) => (
          <Button
            key={s}
            variant={statusFilter === s ? "default" : "outline"}
            size="sm"
            onClick={() => setStatusFilter(s)}
            className="capitalize cursor-pointer"
          >
            {s}
          </Button>
        ))}
      </div>

      {/* Decisions list */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : decisions.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <Brain className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
            <p className="text-muted-foreground font-medium">No decisions yet</p>
            <p className="text-sm text-muted-foreground mt-1">
              Decisions will appear here as the AI processes events from your
              connected platforms.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {decisions.map((d) => {
            const statusCfg = STATUS_CONFIG[d.status] || STATUS_CONFIG.inferred;
            return (
              <Card
                key={d.decision_id}
                className="hover:shadow-md transition-all group"
              >
                <CardContent className="py-4 px-5">
                  <div className="flex items-start gap-4">
                    {/* Confidence bar */}
                    <div className="flex flex-col items-center gap-1 pt-1 shrink-0 w-12">
                      <span
                        className={`text-sm font-bold ${confidenceColor(d.confidence)}`}
                      >
                        {(d.confidence * 100).toFixed(0)}%
                      </span>
                      <div className="w-8 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${confidenceBar(d.confidence)}`}
                          style={{ width: `${d.confidence * 100}%` }}
                        />
                      </div>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-sm truncate">
                          {d.title}
                        </h3>
                        <span
                          className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md border ${statusCfg.color}`}
                        >
                          {statusCfg.icon}
                          {statusCfg.label}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {d.description}
                      </p>

                      {/* Meta */}
                      <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                        <span className="font-medium">{d.repository}</span>
                        <span>{d.evidence_count} evidence items</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {timeAgo(d.created_at)}
                        </span>
                        {d.tags.length > 0 && (
                          <div className="flex gap-1">
                            {d.tags.slice(0, 3).map((t) => (
                              <span
                                key={t}
                                className="px-1.5 py-0.5 bg-muted rounded text-xs"
                              >
                                {t}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1 shrink-0">
                      {d.status === "inferred" && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              handleValidate(d.decision_id, "validated")
                            }
                            disabled={validatingId === d.decision_id}
                            className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 cursor-pointer"
                            title="Validate"
                          >
                            <ThumbsUp className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              handleValidate(d.decision_id, "disputed")
                            }
                            disabled={validatingId === d.decision_id}
                            className="text-red-500 hover:text-red-600 hover:bg-red-50 cursor-pointer"
                            title="Dispute"
                          >
                            <ThumbsDown className="w-4 h-4" />
                          </Button>
                        </>
                      )}
                      <ChevronRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
