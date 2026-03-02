"use client";

import { useState } from "react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  FolderKanban,
  ArrowRight,
  Loader2,
  Sparkles,
  GitBranch,
  MessageSquare,
  LayoutList,
} from "lucide-react";
import { toast } from "sonner";

export function WorkspaceOnboarding() {
  const { createWorkspace } = useWorkspace();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setLoading(true);
    try {
      await createWorkspace(name.trim(), description.trim());
      toast.success(`Welcome to "${name}"! Let's connect your tools.`);
    } catch {
      toast.error("Failed to create workspace");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 via-violet-50/30 to-indigo-50/40">
      <div className="w-full max-w-lg mx-auto px-6">
        {/* Logo & welcome */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 mb-4 shadow-lg shadow-violet-200">
            <FolderKanban className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome to Memora
          </h1>
          <p className="text-muted-foreground mt-2 text-sm max-w-md mx-auto">
            Create your first workspace to start capturing decisions from your
            development workflow.
          </p>
        </div>

        {/* What is a workspace */}
        <div className="bg-white rounded-xl border shadow-sm p-6 mb-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">
            A workspace groups your project&apos;s tools together
          </h2>
          <div className="grid grid-cols-3 gap-3">
            <div className="flex flex-col items-center text-center p-3 rounded-lg bg-gray-50">
              <GitBranch className="w-5 h-5 text-gray-700 mb-1.5" />
              <span className="text-[11px] text-muted-foreground">
                GitHub / GitLab repos
              </span>
            </div>
            <div className="flex flex-col items-center text-center p-3 rounded-lg bg-gray-50">
              <MessageSquare className="w-5 h-5 text-purple-600 mb-1.5" />
              <span className="text-[11px] text-muted-foreground">
                Slack channels
              </span>
            </div>
            <div className="flex flex-col items-center text-center p-3 rounded-lg bg-gray-50">
              <LayoutList className="w-5 h-5 text-blue-600 mb-1.5" />
              <span className="text-[11px] text-muted-foreground">
                Jira projects
              </span>
            </div>
          </div>
        </div>

        {/* Create form */}
        <div className="bg-white rounded-xl border shadow-sm p-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="onboard-name" className="text-sm font-medium">
                Workspace name
              </Label>
              <Input
                id="onboard-name"
                placeholder="e.g. Memora Platform, My Startup, Backend Team..."
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                autoFocus
                className="h-11"
              />
            </div>

            <div className="space-y-2">
              <Label
                htmlFor="onboard-desc"
                className="text-sm font-medium flex items-center gap-1"
              >
                Description
                <span className="text-muted-foreground font-normal">
                  (optional)
                </span>
              </Label>
              <Textarea
                id="onboard-desc"
                placeholder="What's this workspace for?"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="resize-none"
              />
            </div>

            <Button
              onClick={handleCreate}
              disabled={!name.trim() || loading}
              className="w-full h-11 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white cursor-pointer font-medium"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4 mr-2" />
              )}
              Create Workspace
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>

        <p className="text-center text-[11px] text-muted-foreground mt-4">
          You can create more workspaces later from the sidebar.
        </p>
      </div>
    </div>
  );
}
