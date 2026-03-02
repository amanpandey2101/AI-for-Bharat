"use client";

import { useEffect, useState, useCallback, use } from "react";
import { useRouter } from "next/navigation";
import { useWorkspace } from "@/context/WorkspaceContext";
import { getADR, exportADRUrl, type ADR, updateADR } from "@/services/adrs";
import { toast } from "sonner";
import {
  ArrowLeft,
  Loader2,
  Calendar,
  Download,
  CheckCircle2,
  Clock,
  Ban,
  Archive,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import Link from "next/link";

export default function ADRDetailPage({
  params,
}: {
  params: Promise<{ adr_id: string }>;
}) {
  const { adr_id } = use(params);
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();
  const [adr, setAdr] = useState<ADR | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  const fetchADR = useCallback(async () => {
    if (!activeWorkspace) return;
    try {
      setLoading(true);
      const res = await getADR(activeWorkspace.workspace_id, adr_id);
      setAdr(res.data.adr);
    } catch {
      toast.error("Failed to load Architecture Decision");
      router.push("/dashboard/adrs");
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace, adr_id, router]);

  useEffect(() => {
    fetchADR();
  }, [fetchADR]);

  const handleStatusChange = async (newStatus: string) => {
    if (!activeWorkspace || !adr) return;
    try {
      setUpdating(true);
      const res = await updateADR(activeWorkspace.workspace_id, adr.adr_id, {
        status: newStatus,
      });
      setAdr(res.data.adr);
      toast.success("Status updated");
    } catch {
      toast.error("Failed to update status");
    } finally {
      setUpdating(false);
    }
  };

  if (!activeWorkspace || loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-violet-600" />
      </div>
    );
  }

  if (!adr) return null;

  return (
    <div className="w-full max-w-4xl mx-auto px-6 py-8">
 
      <Button variant="ghost" size="sm" asChild className="mb-6 -ml-3 text-muted-foreground">
        <Link href="/dashboard/adrs">
          <ArrowLeft className="w-4 h-4 mr-1.5" />
          Back to standard view
        </Link>
      </Button>

      <div className="space-y-6 mb-10 pb-6 border-b">
        <div className="flex items-start justify-between gap-6">
          <h1 className="text-3xl font-bold tracking-tight">{adr.title}</h1>
          <div className="flex items-center gap-2 shrink-0">
            <Select
              value={adr.status}
              onValueChange={handleStatusChange}
              disabled={updating}
            >
              <SelectTrigger className="w-[140px] h-9">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="proposed">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-primary" />
                    <span>Proposed</span>
                  </div>
                </SelectItem>
                <SelectItem value="accepted">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Accepted</span>
                  </div>
                </SelectItem>
                <SelectItem value="deprecated">
                  <div className="flex items-center gap-2">
                    <Archive className="w-4 h-4 text-amber-600" />
                    <span>Deprecated</span>
                  </div>
                </SelectItem>
                <SelectItem value="superseded">
                  <div className="flex items-center gap-2">
                    <Ban className="w-4 h-4 text-red-600" />
                    <span>Superseded</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>

            <Button variant="outline" size="sm" asChild>
              <a href={exportADRUrl(activeWorkspace.workspace_id, adr.adr_id)} download>
                <Download className="w-4 h-4 mr-2" />
                Export MD
              </a>
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1.5 bg-muted px-2.5 py-1 rounded-md">
            <Calendar className="w-4 h-4" />
            <span>Created {new Date(adr.created_at).toLocaleDateString()}</span>
          </div>
          <span className="font-mono text-xs opacity-70">ID: {adr.adr_id}</span>
        </div>
      </div>

    
      <div className="space-y-10">
        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            Context and Problem Statement
          </h2>
          <div className="bg-card border rounded-xl p-6 text-card-foreground leading-relaxed whitespace-pre-wrap">
            {adr.context || <span className="text-muted-foreground italic">No context documented.</span>}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            Decision Outcomes
          </h2>
          <div className="bg-primary/5 border border-primary/20 rounded-xl p-6 text-card-foreground leading-relaxed whitespace-pre-wrap">
            {adr.decision || <span className="text-muted-foreground italic">No decision documented.</span>}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            Consequences
          </h2>
          <div className="bg-card border rounded-xl p-6 text-card-foreground leading-relaxed whitespace-pre-wrap">
            {adr.consequences || <span className="text-muted-foreground italic">No consequences documented.</span>}
          </div>
        </section>
      </div>
    </div>
  );
}
