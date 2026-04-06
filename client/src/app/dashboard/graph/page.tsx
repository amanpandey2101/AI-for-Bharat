"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { forceCollide } from "d3-force";
import api from "@/lib/axios";
import { Brain, Loader2, X, CheckCircle2 } from "lucide-react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { Button } from "@/components/ui/button";

// Dynamic import to avoid SSR issues and ensure clean mount
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const NODE_COLORS: Record<string, string> = {
  decision_validated: "#10b981", 
  decision_inferred: "#f59e0b", 
  decision_disputed: "#ef4444",  
  author: "#3b82f6",            
  repository: "#8b5cf6",      
};

interface EvidenceItem {
  source_type: string;
  content: string;
  author: string;
  timestamp: string;
  url?: string;
}

interface GraphNode {
  id: string;
  name: string;
  type: "decision" | "author" | "repository";
  status?: string;
  val: number;
  description?: string;
  tags?: string[];
  confidence?: number;
  x?: number;
  y?: number;
  color?: string;
  createdAt?: string;
  evidence?: {
    intent: EvidenceItem[];
    execution: EvidenceItem[];
    authority: EvidenceItem[];
  };
  participants?: string[];
  repository?: string;
  platform?: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type GraphData = { nodes: any[]; links: any[] };

/**
 * Pre-scatter nodes with random positions so the D3 simulation
 * never starts from all-nodes-at-(0,0). This is the root cause
 * of the "ball of nodes" clumping on client-side navigation.
 */
function scatterNodes(graphData: GraphData): GraphData {
  const spread = 300;
  return {
    ...graphData,
    nodes: graphData.nodes.map((node) => ({
      ...node,
      x: (Math.random() - 0.5) * spread,
      y: (Math.random() - 0.5) * spread,
    })),
    links: [...graphData.links],
  };
}

export default function KnowledgeGraphPage() {
  const { activeWorkspace } = useWorkspace();
  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [showEvidence, setShowEvidence] = useState(false);
  // A monotonic counter used as the React key for ForceGraph2D.
  // Changing this forces a full unmount+remount, giving us a fresh simulation.
  const [graphGeneration, setGraphGeneration] = useState(0);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fgRef = useRef<any>(null);

  useEffect(() => {
    let cancelled = false;
    const fetchGraph = async () => {
      setLoading(true);
      try {
        const workspaceId = activeWorkspace?.workspace_id;
        const res = await api.get("/decisions/graph/data", {
          params: { workspace_id: workspaceId },
        });
        if (cancelled) return;
        // Pre-scatter nodes so they never start stacked at origin
        const scattered = scatterNodes(res.data);
        setData(scattered);
        // Bump the generation to force ForceGraph2D to fully remount
        setGraphGeneration((g) => g + 1);
      } catch (err) {
        console.error("Failed to load graph:", err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchGraph();
    return () => { cancelled = true; };
  }, [activeWorkspace]);

  // Apply forces after graph mounts with new data
  useEffect(() => {
    if (!data || loading) return;

    const timer = setTimeout(() => {
      const fg = fgRef.current;
      if (!fg) return;

      // Moderate repulsion — enough to spread but not magnetic
      fg.d3Force("charge")?.strength(-250);
      // Reasonable link distance
      fg.d3Force("link")?.distance(80);
      // Prevent node overlap based on node size
      fg.d3Force("collide", forceCollide(18));
      // Remove center force entirely — this was the "magnet" pulling everything together
      fg.d3Force("center", null);

      fg.d3ReheatSimulation();
    }, 100);

    return () => clearTimeout(timer);
  }, [data, loading, graphGeneration]);

  const handleEngineStop = useCallback(() => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(600, 120);
    }
  }, []);

  const handleNodeClick = useCallback((node: object) => {
    const graphNode = node as GraphNode;
    if (graphNode.type === "decision") {
      setSelectedNode(graphNode);
      setShowEvidence(false);
    }
  }, []);

  /** Memoized canvas renderer — prevents re-draws on tab/window focus changes */
  const nodeCanvasObject = useCallback(
    (node: object, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const n = node as GraphNode;
      const label = n.name;
      const fontSize = 12 / globalScale;
      ctx.font = `${fontSize}px Inter, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      ctx.fillStyle =
        n.type === "decision"
          ? NODE_COLORS[`decision_${n.status}`] || NODE_COLORS.decision_inferred
          : NODE_COLORS[n.type];

      if (n.x !== undefined && n.y !== undefined) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.val / 2, 0, 2 * Math.PI, false);
        ctx.fill();

        if (n.type === "decision") {
          ctx.strokeStyle = ctx.fillStyle;
          ctx.globalAlpha = 0.2;
          ctx.lineWidth = 4 / globalScale;
          ctx.stroke();
          ctx.globalAlpha = 1.0;
        }

        if (globalScale > 2.2) {
          ctx.fillStyle = "#64748b";
          ctx.fillText(label, n.x, n.y + n.val / 2 + 6 / globalScale);
        }
      }
    },
    []
  );

  // Memoize static props so ForceGraph2D doesn't get unnecessary re-renders
  const linkColor = useCallback(() => "#e2e8f0", []);
  const nodeLabel = useCallback((node: object) => {
    const n = node as GraphNode;
    return `${n.type.toUpperCase()}: ${n.name}`;
  }, []);
  const nodeColor = useCallback((node: object) => {
    const n = node as GraphNode;
    if (n.type === "decision") return NODE_COLORS[`decision_${n.status}`] || NODE_COLORS.decision_inferred;
    return NODE_COLORS[n.type];
  }, []);

  if (loading || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-[80vh]">
        <Loader2 className="w-10 h-10 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground animate-pulse text-sm font-medium">
          Mapping architectural memory...
        </p>
      </div>
    );
  }

  return (
    <div className="relative w-full h-[calc(100vh-100px)] bg-white rounded-3xl overflow-hidden border border-gray-100 shadow-sm">
      {/* Graph Container */}
      <div className="absolute inset-0 cursor-crosshair">
        <ForceGraph2D
          key={graphGeneration}
          ref={fgRef}
          graphData={data}
          nodeLabel={nodeLabel}
          nodeColor={nodeColor}
          nodeRelSize={4}
          nodeCanvasObject={nodeCanvasObject}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          linkColor={linkColor}
          linkWidth={1}
          onNodeClick={handleNodeClick}
          backgroundColor="#ffffff"
          d3AlphaDecay={0.04}
          d3VelocityDecay={0.4}
          cooldownTime={2000}
          warmupTicks={30}
          onEngineStop={handleEngineStop}
        />
      </div>

      {/* Toolbar / Legend Overlay */}
      <div className="absolute top-6 left-6 flex flex-col gap-2">
        <div className="p-4 bg-white/90 backdrop-blur-md rounded-2xl border shadow-sm flex flex-col gap-3">
          <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">
            Knowledge Map
          </h4>
          <div className="flex items-center gap-3 text-xs font-semibold text-gray-700">
            <div className="w-3 h-3 rounded-full bg-violet-500 shadow-[0_0_8px_rgba(139,92,246,0.5)]" />
            Repositories
          </div>
          <div className="flex items-center gap-3 text-xs font-semibold text-gray-700">
            <div className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
            Contributors
          </div>
          <div className="flex items-center gap-3 text-xs font-semibold text-gray-700">
            <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
            Validated Decisions
          </div>
          <div className="flex items-center gap-3 text-xs font-semibold text-gray-700">
            <div className="w-3 h-3 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]" />
            Inferred Context
          </div>
          <div className="flex items-center gap-3 text-xs font-semibold text-gray-700">
            <div className="w-3 h-3 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]" />
            Disputed Decisions
          </div>
        </div>
      </div>

      {/* Side Panel for Node Details */}
      {selectedNode && (
        <div className="absolute top-6 bottom-6 right-6 w-80 bg-white rounded-3xl border border-gray-100 shadow-[0_20px_50px_rgba(0,0,0,0.1)] overflow-y-auto animate-in slide-in-from-right-4 duration-500 z-50">
          <div className="p-8">
            <div className="flex justify-between items-start mb-8">
              <div className="p-3 rounded-2xl bg-blue-50/50">
                <Brain className="w-6 h-6 text-blue-600" />
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="rounded-full hover:bg-gray-100 cursor-pointer"
                onClick={() => {
                  setSelectedNode(null);
                  setShowEvidence(false);
                }}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            {showEvidence ? (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <button
                  onClick={() => setShowEvidence(false)}
                  className="text-xs font-bold text-blue-600 mb-6 flex items-center gap-1 hover:underline cursor-pointer"
                >
                  ← Back to Rationale
                </button>

                <h3 className="text-xl font-bold text-gray-900 mb-6 leading-tight">
                  Evidence Chain
                </h3>

                <div className="space-y-4">
                  {/* Dynamic Evidence: Intent */}
                  {(selectedNode.evidence?.intent ?? []).map((e, i) => (
                    <div key={`intent-${i}`} className="p-4 rounded-2xl bg-gray-50 border border-gray-100">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-2 h-2 rounded-full bg-blue-500" />
                        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                          {e.source_type.replace(/_/g, " ")}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 mb-2">
                        &ldquo;{e.content}&rdquo;
                      </p>
                      <div className="text-[10px] text-gray-400">
                        {e.author} • {new Date(e.timestamp).toLocaleDateString()}
                      </div>
                    </div>
                  ))}

                  {/* Dynamic Evidence: Execution */}
                  {(selectedNode.evidence?.execution ?? []).map((e, i) => (
                    <div key={`exec-${i}`} className="p-4 rounded-2xl bg-gray-50 border border-gray-100">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-2 h-2 rounded-full bg-gray-900" />
                        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                          {e.source_type.replace(/_/g, " ")}
                        </span>
                      </div>
                      <p className="text-xs font-medium text-gray-700 mb-1">
                        {e.content}
                      </p>
                      <p className="text-[10px] text-gray-500">
                        {e.author} • {new Date(e.timestamp).toLocaleDateString()}
                      </p>
                    </div>
                  ))}

                  {/* Fallback if no evidence */}
                  {(selectedNode.evidence?.intent?.length === 0 && selectedNode.evidence?.execution?.length === 0) && (
                    <div className="p-4 rounded-2xl bg-amber-50/50 border border-amber-100">
                      <p className="text-xs text-amber-700">No direct evidence artifacts captured yet. This decision was inferred from contextual patterns.</p>
                    </div>
                  )}

                  {/* Consensus Badge */}
                  <div className="p-4 rounded-2xl bg-emerald-50/50 border border-emerald-100 mt-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-widest">
                        Confidence Score
                      </span>
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    </div>
                    <p className="text-[11px] text-emerald-800 font-medium">
                      {((selectedNode.confidence ?? 0) * 100).toFixed(0)}% confidence based on {(selectedNode.evidence?.intent?.length ?? 0) + (selectedNode.evidence?.execution?.length ?? 0)} evidence artifacts.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <>
                <h3 className="text-xl font-bold text-gray-900 mb-3 leading-tight">
                  {selectedNode.name}
                </h3>

                <div className="flex items-center gap-3 mb-6">
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-gray-100 text-gray-500 border border-gray-200/50">
                    {selectedNode.status}
                  </div>
                  {selectedNode.createdAt && (
                    <span className="text-[10px] font-medium text-gray-400">
                      Captured {new Date(selectedNode.createdAt).toLocaleDateString()}
                    </span>
                  )}
                </div>

                <div className="space-y-6">
                  <div>
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">
                      Rationale Summary
                    </p>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      {selectedNode.description}
                    </p>
                  </div>

                  <div className="pt-6 border-t border-gray-100">
                    <div className="flex justify-between items-end mb-3">
                      <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                        Inference Confidence
                      </p>
                      <span className="text-sm font-bold text-emerald-600">
                        {(selectedNode.confidence ?? 0) * 100}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-gray-50 rounded-full overflow-hidden border border-gray-100">
                      <div
                        className="h-full bg-emerald-500"
                        style={{ width: `${(selectedNode.confidence ?? 0) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>

                {(selectedNode.tags?.length ?? 0) > 0 && (
                  <div className="pt-6 border-t border-gray-100">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">
                      Tags & Classification
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {selectedNode.tags?.map((t: string) => (
                        <span
                          key={t}
                          className="px-3 py-1 bg-violet-50 text-violet-600 rounded-lg text-[10px] font-bold border border-violet-100/50"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="pt-10">
                  <Button
                    className="w-full bg-gray-900 text-white rounded-2xl h-12 font-semibold shadow-lg hover:bg-black transition-all cursor-pointer"
                    onClick={() => setShowEvidence(true)}
                  >
                    View Evidence Chain
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

