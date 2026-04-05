"use client";

import { useEffect, useState, useRef } from "react";
import ForceGraph2D from "react-force-graph-2d";
import * as d3 from "d3-force";
import api from "@/lib/axios";
import { Brain, Loader2, X } from "lucide-react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { Button } from "@/components/ui/button";

const NODE_COLORS: Record<string, string> = {
  decision_validated: "#10b981", // emerald-500
  decision_inferred: "#f59e0b",  // amber-500
  decision_disputed: "#ef4444",  // red-500
  author: "#3b82f6",            // blue-500
  repository: "#8b5cf6",        // violet-500
};

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
}

export default function KnowledgeGraphPage() {
  const { activeWorkspace } = useWorkspace();
  const [data, setData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fgRef = useRef<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      // For Demo: if no workspace selected, or even if it is, we fetch the recent decisions to build a graph
      try {
        setLoading(true);
        const res = await api.get("/decisions/graph/data");
        setData(res.data);
        
        // --- Tune Physics (WOW Factor Tuning) ---
        if (fgRef.current) {
          const fg = fgRef.current;
          // 1. Stronger repulsion to keep clusters airy
          fg.d3Force('charge').strength(-400); 
          // 2. Longer links to separate hub repositories from decisions
          fg.d3Force('link').distance(80);
          // 3. Collision force to strictly prevent overlapping nodes
          fg.d3Force('collide', d3.forceCollide(25));
          // 4. Centering
          fg.d3Force('center').strength(0.1);
        }
      } catch (err) {
        console.error("Failed to fetch graph data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [activeWorkspace]);

  const handleNodeClick = (node: object) => {
    const graphNode = node as GraphNode;
    if (graphNode.type === "decision") {
       setSelectedNode(graphNode);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[80vh]">
        <Loader2 className="w-10 h-10 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground animate-pulse text-sm font-medium">Mapping architectural memory...</p>
      </div>
    );
  }

  return (
    <div className="relative w-full h-[calc(100vh-100px)] bg-white rounded-3xl overflow-hidden border border-gray-100 shadow-sm">
       {/* Graph Container */}
       <div className="absolute inset-0 cursor-crosshair">
          <ForceGraph2D
            ref={fgRef}
            graphData={data}
            nodeLabel={(node: object) => {
               const n = node as GraphNode;
               return `${n.type.toUpperCase()}: ${n.name}`;
            }}
            nodeColor={(node: object) => {
               const n = node as GraphNode;
               if (n.type === "decision") return NODE_COLORS[`decision_${n.status}`] || NODE_COLORS.decision_inferred;
               return NODE_COLORS[n.type];
            }}
            nodeRelSize={6}
            nodeCanvasObject={(node: object, ctx: CanvasRenderingContext2D, globalScale: number) => {
               const n = node as GraphNode;
               const label = n.name;
               const fontSize = 12/globalScale;
               ctx.font = `${fontSize}px Inter, sans-serif`;
               ctx.textAlign = 'center';
               ctx.textBaseline = 'middle';
               
               // Draw Node Circle
               ctx.fillStyle = n.type === "decision" 
                  ? (NODE_COLORS[`decision_${n.status}`] || NODE_COLORS.decision_inferred)
                  : NODE_COLORS[n.type];
                  
               if (n.x !== undefined && n.y !== undefined) {
                  ctx.beginPath(); 
                  ctx.arc(n.x, n.y, n.val / 2, 0, 2 * Math.PI, false); 
                  ctx.fill();

                  // Add visual glow for decisions
                  if (n.type === "decision") {
                     ctx.strokeStyle = ctx.fillStyle;
                     ctx.globalAlpha = 0.2;
                     ctx.lineWidth = 4/globalScale;
                     ctx.stroke();
                     ctx.globalAlpha = 1.0;
                  }

                  // Label - Only show when zoomed in for clarity
                  if (globalScale > 2.2) {
                     ctx.fillStyle = '#64748b';
                     ctx.fillText(label, n.x, n.y + (n.val / 2) + 6/globalScale);
                  }
               }
            }}
            linkDirectionalArrowLength={3}
            linkDirectionalArrowRelPos={1}
            linkColor={() => '#e2e8f0'}
            linkWidth={1.5}
            onNodeClick={handleNodeClick}
            backgroundColor="#ffffff"
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.3}
          />
       </div>

       {/* Toolbar / Legend Overlay */}
       <div className="absolute top-6 left-6 flex flex-col gap-2">
           <div className="p-4 bg-white/90 backdrop-blur-md rounded-2xl border shadow-sm flex flex-col gap-3">
              <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Knowledge Map</h4>
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
                   <Button variant="ghost" size="icon" className="rounded-full hover:bg-gray-100" onClick={() => setSelectedNode(null)}>
                      <X className="w-4 h-4" />
                   </Button>
                </div>
                
                <h3 className="text-xl font-bold text-gray-900 mb-3 leading-tight">{selectedNode.name}</h3>
                
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-gray-100 text-gray-500 mb-6 border border-gray-200/50">
                   {selectedNode.status}
                </div>

                <div className="space-y-6">
                   <div>
                      <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">Rationale Summary</p>
                      <p className="text-sm text-gray-600 leading-relaxed">
                         {selectedNode.description}
                      </p>
                   </div>

                   <div className="pt-6 border-t border-gray-100">
                      <div className="flex justify-between items-end mb-3">
                         <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Inference Confidence</p>
                         <span className="text-sm font-bold text-emerald-600">{(selectedNode.confidence ?? 0) * 100}%</span>
                      </div>
                      <div className="w-full h-2 bg-gray-50 rounded-full overflow-hidden border border-gray-100">
                         <div className="h-full bg-emerald-500" style={{ width: `${(selectedNode.confidence ?? 0) * 100}%` }} />
                      </div>
                   </div>

                   {(selectedNode.tags?.length ?? 0) > 0 && (
                      <div className="pt-6 border-t border-gray-100">
                        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">Tags & Classification</p>
                        <div className="flex flex-wrap gap-2">
                           {selectedNode.tags?.map((t: string) => (
                              <span key={t} className="px-3 py-1 bg-violet-50 text-violet-600 rounded-lg text-[10px] font-bold border border-violet-100/50">
                                 {t}
                              </span>
                           ))}
                        </div>
                      </div>
                   )}
                   
                   <div className="pt-10">
                      <Button className="w-full bg-gray-900 text-white rounded-2xl h-12 font-semibold shadow-lg hover:bg-black transition-all">
                         View Evidence Chain
                      </Button>
                   </div>
                </div>
             </div>
          </div>
       )}
    </div>
  );
}
