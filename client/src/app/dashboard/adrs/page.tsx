"use client";

import { useEffect, useState, useCallback } from "react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { getADRs, createADR, deleteADR, draftADR, type ADR } from "@/services/adrs";
import { toast } from "sonner";
import {
  BookOpen,
  Plus,
  Loader2,
  Calendar,
  ChevronRight,
  MoreVertical,
  Trash2,
  Wand2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import Link from "next/link";

export default function ADRsPage() {
  const { activeWorkspace } = useWorkspace();
  const [adrs, setAdrs] = useState<ADR[]>([]);
  const [loading, setLoading] = useState(true);

  // Create Flow
  const [createOpen, setCreateOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [title, setTitle] = useState("");
  const [context, setContext] = useState("");
  const [decision, setDecision] = useState("");
  const [consequences, setConsequences] = useState("");
  const [draftTopic, setDraftTopic] = useState("");
  const [drafting, setDrafting] = useState(false);
  const [showAutoDraft, setShowAutoDraft] = useState(false);

  const fetchADRs = useCallback(async () => {
    if (!activeWorkspace) return;
    try {
      setLoading(true);
      const res = await getADRs(activeWorkspace.workspace_id);
      setAdrs(res.data.adrs);
    } catch {
      toast.error("Failed to load Architecture Decisions");
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace]);

  useEffect(() => {
    fetchADRs();
  }, [fetchADRs]);

  const handleAutoDraft = async () => {
    if (!activeWorkspace || !draftTopic.trim()) return;
    try {
      setDrafting(true);
      const res = await draftADR(activeWorkspace.workspace_id, draftTopic.trim());
      const data = res.data;
      setTitle(data.title || "");
      setContext(data.context || "");
      setDecision(data.decision || "");
      setConsequences(data.consequences || "");
      toast.success("ADR drafted by AI");
      setShowAutoDraft(false);
    } catch {
      toast.error("Failed to auto-draft ADR");
    } finally {
      setDrafting(false);
    }
  };


  const handleCreate = async () => {
    if (!activeWorkspace || !title.trim() || !decision.trim()) return;

    try {
      setSaving(true);
      const res = await createADR(activeWorkspace.workspace_id, {
        title: title.trim(),
        context: context.trim(),
        decision: decision.trim(),
        consequences: consequences.trim(),
        status: "accepted", // Defaulting to accepted for simplicity
      });
      setAdrs([res.data.adr, ...adrs]);
      toast.success("ADR created successfully");
      setCreateOpen(false);
      setTitle("");
      setContext("");
      setDecision("");
      setConsequences("");
      setDraftTopic("");
      setShowAutoDraft(false);
    } catch {
      toast.error("Failed to create ADR");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (adrId: string) => {
    if (!activeWorkspace) return;
    try {
      await deleteADR(activeWorkspace.workspace_id, adrId);
      setAdrs((prev) => prev.filter((a) => a.adr_id !== adrId));
      toast.success("ADR deleted");
    } catch {
      toast.error("Failed to delete ADR");
    }
  };

  const statusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "accepted":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "proposed":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "deprecated":
      case "superseded":
        return "bg-red-50 text-red-700 border-red-200";
      default:
        return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  if (!activeWorkspace) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 text-muted-foreground">
        Please select a workspace to view architecture decisions.
      </div>
    );
  }

  return (
    <div className="w-full max-w-5xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500/10 to-indigo-500/10">
              <BookOpen className="w-6 h-6 text-violet-600" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">
              Architecture Decisions
            </h1>
          </div>
          <p className="text-muted-foreground max-w-lg">
            Maintain a formal log of architectural decisions (ADRs). Document why
            choices were made so future teams understand the context.
          </p>
        </div>

        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Decision
        </Button>
      </div>

      {/* List */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : adrs.length === 0 ? (
        <div className="text-center py-20 border rounded-xl bg-muted/20 border-dashed">
          <BookOpen className="w-10 h-10 text-muted-foreground mx-auto mb-3 opacity-20" />
          <h3 className="text-sm font-medium text-foreground">No decisions yet</h3>
          <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto mb-4">
            Start documenting your workspace&apos;s architectural choices to keep your
            team aligned.
          </p>
          <Button variant="outline" onClick={() => setCreateOpen(true)}>
            Create your first ADR
          </Button>
        </div>
      ) : (
        <div className="grid gap-3">
          {adrs.map((adr) => (
            <div
              key={adr.adr_id}
              className="flex items-center justify-between p-4 rounded-xl border bg-card hover:shadow-md transition-shadow group"
            >
              <div className="flex-1 min-w-0 pr-4">
                <div className="flex items-center gap-3 mb-1">
                  <span
                    className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${statusColor(
                      adr.status
                    )}`}
                  >
                    {adr.status}
                  </span>
                  <Link
                    href={`/dashboard/adrs/${adr.adr_id}`}
                    className="font-semibold text-base truncate hover:underline hover:text-violet-600 transition-colors"
                  >
                    {adr.title}
                  </Link>
                </div>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" />
                    {new Date(adr.created_at).toLocaleDateString()}
                  </span>
                  <span className="truncate max-w-[400px]">
                    {adr.context || "No context provided"}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Button variant="ghost" size="sm" asChild>
                  <Link href={`/dashboard/adrs/${adr.adr_id}`}>
                    View
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Link>
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      onClick={() => handleDelete(adr.adr_id)}
                      className="text-red-600 focus:text-red-600 cursor-pointer"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete ADR
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader className="flex flex-row items-center justify-between pr-8">
            <DialogTitle>Document Architecture Decision</DialogTitle>
            <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowAutoDraft(!showAutoDraft)} 
                className="text-violet-600 hover:text-violet-700 hover:bg-violet-50"
            >
               <Wand2 className="w-4 h-4 mr-2" />
               Auto-Draft with AI
            </Button>
          </DialogHeader>
          <div className="space-y-4 py-4 max-h-[70vh] overflow-y-auto px-1">
            {showAutoDraft && (
               <div className="bg-violet-50 border border-violet-100 p-4 rounded-xl space-y-3 mb-4">
                 <Label className="text-violet-800">What is the decision about?</Label>
                 <div className="flex gap-2">
                   <Input 
                      placeholder="e.g. Switching to DynamoDB for scale"
                      value={draftTopic}
                      onChange={(e) => setDraftTopic(e.target.value)}
                      className="bg-white"
                      disabled={drafting}
                   />
                   <Button onClick={handleAutoDraft} disabled={drafting || !draftTopic.trim()}>
                     {drafting ? <Loader2 className="w-4 h-4 animate-spin shrink-0" /> : <Wand2 className="w-4 h-4 mr-2 shrink-0" />}
                     Draft
                   </Button>
                 </div>
               </div>
            )}
            <div className="space-y-2">
              <Label>Title</Label>
              <Input
                placeholder="e.g. Use React Server Components for performance"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Context</Label>
              <Textarea
                placeholder="What is the problem or force that makes this decision necessary?"
                value={context}
                onChange={(e) => setContext(e.target.value)}
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label>Decision</Label>
              <Textarea
                placeholder="What exactly are we doing?"
                value={decision}
                onChange={(e) => setDecision(e.target.value)}
                rows={4}
              />
              <div className="space-y-2">
              <Label>Consequences</Label>
              <Textarea
                placeholder="What are the positive and negative consequences?"
                value={consequences}
                onChange={(e) => setConsequences(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCreateOpen(false)}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!title.trim() || !decision.trim() || saving}
            >
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Save Decision
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
