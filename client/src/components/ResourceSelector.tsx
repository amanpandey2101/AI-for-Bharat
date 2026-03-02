"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useWorkspace } from "@/context/WorkspaceContext";
import { addResource } from "@/services/workspaces";
import {
  Check,
  Loader2,
  Search,
  X,
  Lock,
  Globe,
  GitBranch,
  Hash,
  Briefcase,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  getGitHubRepos,
  selectGitHubRepos,
  getGitLabRepos,
  selectGitLabRepos,
  getSlackChannels,
  selectSlackChannels,
  getJiraProjects,
  selectJiraProjects,
  type Repo,
  type SlackChannel,
  type JiraProject,
} from "@/services/integrations";
import { toast } from "sonner";

type ResourceItem = {
  id: string;
  name: string;
  description?: string;
  isPrivate?: boolean;
  extra?: string;
};

interface ResourceSelectorProps {
  platform: string;
  onClose: () => void;
  onSaved: () => void;
}

export default function ResourceSelector({
  platform,
  onClose,
  onSaved,
}: ResourceSelectorProps) {
  const { activeWorkspace, refreshWorkspaces } = useWorkspace();
  const [resources, setResources] = useState<ResourceItem[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const fetchResources = async () => {
      try {
        setLoading(true);
        let items: ResourceItem[] = [];

        if (platform === "github") {
          const res = await getGitHubRepos();
          items = res.data.repos.map((r: Repo) => ({
            id: r.full_name,
            name: r.name,
            description: r.full_name,
            isPrivate: r.private,
            extra: r.owner,
          }));
        } else if (platform === "gitlab") {
          const res = await getGitLabRepos();
          items = res.data.repos.map((r: Repo) => ({
            id: String(r.id),
            name: r.name,
            description: r.full_name || r.name,
            isPrivate: r.private,
          }));
        } else if (platform === "slack") {
          const res = await getSlackChannels();
          items = res.data.channels.map((c: SlackChannel) => ({
            id: c.id,
            name: c.name,
            isPrivate: c.is_private,
            extra: `${c.num_members} members`,
          }));
        } else if (platform === "jira") {
          const res = await getJiraProjects();
          items = res.data.projects.map((p: JiraProject) => ({
            id: p.key,
            name: p.name,
            description: p.key,
          }));
        }

        setResources(items);
      } catch {
        toast.error(`Failed to load ${platform} resources`);
      } finally {
        setLoading(false);
      }
    };

    fetchResources();
  }, [platform]);

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const selectAll = () => {
    if (selected.size === filteredResources.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filteredResources.map((r) => r.id)));
    }
  };

  const handleSave = async () => {
    if (selected.size === 0) {
      toast.warning("Please select at least one resource");
      return;
    }

    try {
      setSaving(true);
      const ids = Array.from(selected);
      const names = ids.map(
        (id) => resources.find((r) => r.id === id)?.name || id
      );

      // 1. Save to integrations backend
      if (platform === "github") {
        await selectGitHubRepos(ids, names);
      } else if (platform === "gitlab") {
        await selectGitLabRepos(ids, names);
      } else if (platform === "slack") {
        await selectSlackChannels(ids, names);
      } else if (platform === "jira") {
        await selectJiraProjects(ids, names);
      }

      // 2. Also add resources to the active workspace
      if (activeWorkspace) {
        const resourceType =
          platform === "slack" ? "channel" :
          platform === "jira" ? "project" : "repository";

        await Promise.all(
          ids.map((id, i) =>
            addResource(
              activeWorkspace.workspace_id,
              platform,
              id,
              names[i],
              resourceType
            )
          )
        );
        refreshWorkspaces();
      }

      toast.success(
        `${selected.size} ${getResourceLabel(platform)} connected!`,
        {
          description: activeWorkspace
            ? `Added to workspace "${activeWorkspace.name}". Events will start flowing.`
            : "Webhooks registered. Events will start flowing.",
        }
      );
      onSaved();
      onClose();
    } catch {
      toast.error("Failed to save selection");
    } finally {
      setSaving(false);
    }
  };

  const getResourceLabel = (p: string) => {
    switch (p) {
      case "github":
      case "gitlab":
        return "repositories";
      case "slack":
        return "channels";
      case "jira":
        return "projects";
      default:
        return "resources";
    }
  };

  const getIcon = (p: string) => {
    switch (p) {
      case "github":
      case "gitlab":
        return <GitBranch className="w-4 h-4" />;
      case "slack":
        return <Hash className="w-4 h-4" />;
      case "jira":
        return <Briefcase className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const filteredResources = resources.filter(
    (r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      r.description?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <Card className="w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl border">
        {/* Header */}
        <CardHeader className="pb-3 border-b shrink-0">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              {getIcon(platform)}
              Select {getResourceLabel(platform)} to monitor
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="cursor-pointer"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          {/* Search */}
          <div className="relative mt-3">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder={`Search ${getResourceLabel(platform)}...`}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
        </CardHeader>

        {/* Resource list */}
        <CardContent className="flex-1 overflow-y-auto p-0">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-sm text-muted-foreground">
                Loading {getResourceLabel(platform)}...
              </span>
            </div>
          ) : filteredResources.length === 0 ? (
            <div className="flex items-center justify-center py-16 text-muted-foreground text-sm">
              No {getResourceLabel(platform)} found.
            </div>
          ) : (
            <div className="divide-y">
              {/* Select all */}
              <button
                onClick={selectAll}
                className="w-full px-4 py-2.5 flex items-center justify-between text-sm text-muted-foreground hover:bg-muted/50 transition-colors cursor-pointer"
              >
                <span>
                  {selected.size === filteredResources.length
                    ? "Deselect all"
                    : `Select all (${filteredResources.length})`}
                </span>
                <span className="text-xs font-medium text-foreground">
                  {selected.size} selected
                </span>
              </button>

              {filteredResources.map((item) => {
                const isSelected = selected.has(item.id);
                return (
                  <button
                    key={item.id}
                    onClick={() => toggleSelect(item.id)}
                    className={`w-full px-4 py-3 flex items-center gap-3 text-left transition-colors cursor-pointer ${
                      isSelected
                        ? "bg-primary/5 border-l-2 border-l-primary"
                        : "hover:bg-muted/50 border-l-2 border-l-transparent"
                    }`}
                  >
                    {/* Checkbox */}
                    <div
                      className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors shrink-0 ${
                        isSelected
                          ? "bg-primary border-primary text-primary-foreground"
                          : "border-muted-foreground/30"
                      }`}
                    >
                      {isSelected && <Check className="w-3 h-3" />}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm truncate">
                          {item.name}
                        </span>
                        {item.isPrivate !== undefined && (
                          <span className="shrink-0">
                            {item.isPrivate ? (
                              <Lock className="w-3 h-3 text-amber-500" />
                            ) : (
                              <Globe className="w-3 h-3 text-muted-foreground" />
                            )}
                          </span>
                        )}
                      </div>
                      {item.description && (
                        <span className="text-xs text-muted-foreground truncate block">
                          {item.description}
                        </span>
                      )}
                    </div>

                    {/* Extra info */}
                    {item.extra && (
                      <span className="text-xs text-muted-foreground shrink-0">
                        {item.extra}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </CardContent>

        {/* Footer */}
        <div className="border-t p-4 flex items-center justify-between shrink-0">
          <span className="text-sm text-muted-foreground">
            {selected.size} {getResourceLabel(platform)} selected
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              className="cursor-pointer"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={saving || selected.size === 0}
              className="cursor-pointer"
            >
              {saving ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
                  Connecting...
                </>
              ) : (
                `Connect ${selected.size} ${getResourceLabel(platform)}`
              )}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
