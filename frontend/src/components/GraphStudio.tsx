"use client";

import React, { useRef, useState, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import {
  Plus,
  Trash2,
  Maximize2,
  Layers,
  ArrowRight,
  X,
  Search,
} from "lucide-react";
import { GraphData, GraphNode, GraphLink, NodeType } from "@/types";
import { useI18n } from "@/i18n";

// ForceGraph2D dynamic import to prevent SSR canvas issues
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center text-slate-500 text-xs">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-500 mr-2" />
      Loading Causal Graph Studio Canvas...
    </div>
  ),
});

interface GraphStudioProps {
  graphData: GraphData;
  onAddNode: (node: GraphNode) => Promise<void>;
  onDeleteNode: (nodeId: string) => Promise<void>;
  onAddEdge: (edge: GraphLink) => Promise<void>;
  onDeleteEdge: (source: string, target: string) => Promise<void>;
  highlightedNodeIds?: string[];
  isDedicatedTab?: boolean;
}

const NODE_COLORS: Record<NodeType, { bg: string; border: string; text: string; glow: string }> = {
  Symptom: { bg: "#f59e0b", border: "#b45309", text: "#fef3c7", glow: "rgba(245, 158, 11, 0.4)" },
  RootCause: { bg: "#f43f5e", border: "#be123c", text: "#ffe4e6", glow: "rgba(244, 63, 94, 0.4)" },
  Verification: { bg: "#0284c7", border: "#0369a1", text: "#e0f2fe", glow: "rgba(2, 132, 199, 0.4)" },
  Command: { bg: "#10b981", border: "#047857", text: "#d1fae5", glow: "rgba(16, 185, 129, 0.4)" },
};

export const GraphStudio: React.FC<GraphStudioProps> = ({
  graphData,
  onAddNode,
  onDeleteNode,
  onAddEdge,
  onDeleteEdge,
  highlightedNodeIds = [],
}) => {
  const { t } = useI18n();
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 700 });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Filters & Search
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedTypeFilter, setSelectedTypeFilter] = useState<string>("ALL");

  // Modals state
  const [showAddNodeModal, setShowAddNodeModal] = useState(false);
  const [showAddEdgeModal, setShowAddEdgeModal] = useState(false);

  // New Node Form
  const [newNodeId, setNewNodeId] = useState("");
  const [newNodeLabel, setNewNodeLabel] = useState("");
  const [newNodeType, setNewNodeType] = useState<NodeType>("Symptom");
  const [newNodeDesc, setNewNodeDesc] = useState("");

  // New Edge Form
  const [newEdgeSource, setNewEdgeSource] = useState("");
  const [newEdgeTarget, setNewEdgeTarget] = useState("");
  const [newEdgeRel, setNewEdgeRel] = useState("leads_to");

  // Resize observer to handle dynamic panel resizing
  useEffect(() => {
    if (!containerRef.current) return;
    const updateSize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };
    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Filtered nodes calculation
  const filteredGraphData = useMemo(() => {
    let nodes = graphData.nodes;
    if (selectedTypeFilter !== "ALL") {
      nodes = nodes.filter((n) => n.type === selectedTypeFilter);
    }
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      nodes = nodes.filter(
        (n) =>
          n.id.toLowerCase().includes(q) ||
          n.label.toLowerCase().includes(q) ||
          (n.description && n.description.toLowerCase().includes(q))
      );
    }
    const nodeIds = new Set(nodes.map((n) => n.id));
    const links = graphData.links.filter((l) => {
      const srcId = typeof l.source === "object" ? (l.source as any).id : l.source;
      const tgtId = typeof l.target === "object" ? (l.target as any).id : l.target;
      return nodeIds.has(srcId) && nodeIds.has(tgtId);
    });
    return { nodes, links };
  }, [graphData, selectedTypeFilter, searchTerm]);

  // Node details relations (incoming & outgoing)
  const nodeRelations = useMemo(() => {
    if (!selectedNode) return { incoming: [], outgoing: [] };
    const incoming: Array<{ node: GraphNode; rel: string }> = [];
    const outgoing: Array<{ node: GraphNode; rel: string }> = [];

    graphData.links.forEach((l) => {
      const srcId = typeof l.source === "object" ? (l.source as any).id : l.source;
      const tgtId = typeof l.target === "object" ? (l.target as any).id : l.target;

      if (srcId === selectedNode.id) {
        const targetNode = graphData.nodes.find((n) => n.id === tgtId);
        if (targetNode) outgoing.push({ node: targetNode, rel: l.relationship || "leads_to" });
      }
      if (tgtId === selectedNode.id) {
        const sourceNode = graphData.nodes.find((n) => n.id === srcId);
        if (sourceNode) incoming.push({ node: sourceNode, rel: l.relationship || "leads_to" });
      }
    });

    return { incoming, outgoing };
  }, [selectedNode, graphData]);

  const handleCreateNode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNodeId.trim() || !newNodeLabel.trim()) return;
    await onAddNode({
      id: newNodeId.trim().toLowerCase().replace(/\s+/g, "_"),
      label: newNodeLabel.trim(),
      type: newNodeType,
      description: newNodeDesc.trim(),
    });
    setNewNodeId("");
    setNewNodeLabel("");
    setNewNodeDesc("");
    setShowAddNodeModal(false);
  };

  const handleCreateEdge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEdgeSource || !newEdgeTarget || newEdgeSource === newEdgeTarget) return;
    await onAddEdge({
      source: newEdgeSource,
      target: newEdgeTarget,
      relationship: newEdgeRel.trim() || "leads_to",
    });
    setNewEdgeSource("");
    setNewEdgeTarget("");
    setShowAddEdgeModal(false);
  };

  const handleZoomFit = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400, 50);
    }
  };

  return (
    <div ref={containerRef} className="relative w-full h-full bg-slate-950 overflow-hidden flex flex-col select-none">
      {/* Studio Top Control Bar */}
      <div className="h-12 px-4 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between z-20 shrink-0 gap-3">
        {/* Left: Search & Filter */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-purple-400" />
            <span className="text-xs font-semibold text-slate-100 hidden sm:inline">
              Causal Graph Engine
            </span>
          </div>

          {/* Search Box */}
          <div className="relative w-44 sm:w-56">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={t.graph.searchPlaceholder}
              className="w-full pl-8 pr-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500 font-mono"
            />
          </div>

          {/* Category Filter Pills */}
          <div className="hidden lg:flex items-center gap-1 text-[11px]">
            {[
              { id: "ALL", label: t.common.all },
              { id: "Symptom", label: t.graph.symptom },
              { id: "RootCause", label: t.graph.rootCause },
              { id: "Verification", label: t.graph.verification },
              { id: "Command", label: t.graph.command },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setSelectedTypeFilter(f.id)}
                className={`px-2.5 py-1 rounded-md transition font-medium ${
                  selectedTypeFilter === f.id
                    ? "bg-purple-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddNodeModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium shadow-md shadow-purple-600/20 transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{t.graph.addNode}</span>
          </button>

          <button
            onClick={() => setShowAddEdgeModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 text-xs transition"
          >
            <ArrowRight className="w-3.5 h-3.5 text-emerald-400" />
            <span>{t.graph.addEdge}</span>
          </button>

          <button
            onClick={handleZoomFit}
            title={t.graph.fitView}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="relative flex-1 w-full h-full overflow-hidden">
        {dimensions.width > 0 && dimensions.height > 0 && (
          <ForceGraph2D
            ref={fgRef}
            width={dimensions.width}
            height={dimensions.height - 48}
            graphData={filteredGraphData}
            backgroundColor="#080c14"
            nodeRelSize={7}
            nodeVal={(node: any) => (node.type === "Symptom" ? 10 : 7)}
            linkDirectionalArrowLength={5}
            linkDirectionalArrowRelPos={0.88}
            linkColor={() => "rgba(100, 116, 139, 0.4)"}
            linkWidth={1.5}
            linkDirectionalParticles={2}
            linkDirectionalParticleSpeed={0.005}
            linkDirectionalParticleWidth={2}
            onNodeClick={(node: any) => setSelectedNode(node)}
            nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
              const label = node.label || node.id;
              const type = (node.type as NodeType) || "Symptom";
              const colors = NODE_COLORS[type] || NODE_COLORS.Symptom;
              const isSelected = selectedNode?.id === node.id;
              const isHighlighted = highlightedNodeIds.includes(node.id);
              const radius = isSelected ? 9 : 7;

              // Outer Glow
              if (isSelected || isHighlighted) {
                ctx.beginPath();
                ctx.arc(node.x, node.y, radius + 5, 0, 2 * Math.PI, false);
                ctx.fillStyle = isHighlighted ? "rgba(34, 211, 238, 0.4)" : colors.glow;
                ctx.fill();
              }

              // Circle Body
              ctx.beginPath();
              ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
              ctx.fillStyle = colors.bg;
              ctx.fill();
              ctx.lineWidth = 1.8;
              ctx.strokeStyle = isSelected ? "#ffffff" : colors.border;
              ctx.stroke();

              // Label Text
              if (globalScale >= 0.55 || isSelected || isHighlighted) {
                const fontSize = Math.max(10 / globalScale, 3.5);
                ctx.font = `600 ${fontSize}px -apple-system, BlinkMacSystemFont, sans-serif`;
                ctx.textAlign = "center";
                ctx.textBaseline = "top";
                ctx.fillStyle = isSelected ? "#ffffff" : "#e2e8f0";
                ctx.fillText(label, node.x, node.y + radius + 4);
              }
            }}
          />
        )}

        {/* Legend Overlay on Bottom Left */}
        <div className="absolute bottom-4 left-4 p-3 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-800 text-xs space-y-1.5 shadow-2xl pointer-events-none">
          <div className="text-slate-400 font-semibold mb-1 uppercase tracking-wider text-[10px]">
            {t.graph.legend}
          </div>
          <div className="flex items-center gap-2 text-amber-300">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-sm shadow-amber-500/50" />
            <span className="font-medium">{t.graph.symptom}</span>
          </div>
          <div className="flex items-center gap-2 text-rose-300">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50" />
            <span className="font-medium">{t.graph.rootCause}</span>
          </div>
          <div className="flex items-center gap-2 text-sky-300">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-500 shadow-sm shadow-sky-500/50" />
            <span className="font-medium">{t.graph.verification}</span>
          </div>
          <div className="flex items-center gap-2 text-emerald-300">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
            <span className="font-medium">{t.graph.command}</span>
          </div>
        </div>

        {/* Dedicated Right Side Node Inspector Panel */}
        {selectedNode && (
          <div className="absolute top-4 right-4 w-80 max-h-[85vh] overflow-y-auto p-4 rounded-xl bg-slate-900/95 backdrop-blur-md border border-slate-700 shadow-2xl text-xs space-y-3 z-30 animate-in fade-in slide-in-from-right-4">
            {/* Inspector Header */}
            <div className="flex items-start justify-between">
              <div>
                <span
                  className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider"
                  style={{
                    backgroundColor: `${NODE_COLORS[selectedNode.type]?.bg}33`,
                    color: NODE_COLORS[selectedNode.type]?.bg,
                  }}
                >
                  {selectedNode.type}
                </span>
                <h3 className="text-sm font-bold text-slate-100 mt-1 break-words">
                  {selectedNode.label}
                </h3>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Description */}
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-semibold text-slate-400">
                {t.graph.nodeDesc}
              </span>
              <p className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 leading-relaxed break-words text-[11px]">
                {selectedNode.description || "-"}
              </p>
            </div>

            {/* Node ID */}
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 p-2 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-slate-500">{t.graph.nodeId}</span>
              <span className="text-slate-200">{selectedNode.id}</span>
            </div>

            {/* Inbound Causes / Relations */}
            {nodeRelations.incoming.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[10px] uppercase font-semibold text-rose-400">
                  {t.graph.causeNodes} ({nodeRelations.incoming.length})
                </span>
                <div className="space-y-1 max-h-28 overflow-y-auto">
                  {nodeRelations.incoming.map((item, idx) => (
                    <div
                      key={idx}
                      onClick={() => setSelectedNode(item.node)}
                      className="p-1.5 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800 cursor-pointer flex items-center justify-between text-[11px] transition"
                    >
                      <span className="text-slate-200 font-medium truncate">
                        {item.node.label}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {item.rel}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Outbound Consequences / Verifications */}
            {nodeRelations.outgoing.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[10px] uppercase font-semibold text-cyan-400">
                  {t.graph.effectNodes} ({nodeRelations.outgoing.length})
                </span>
                <div className="space-y-1 max-h-28 overflow-y-auto">
                  {nodeRelations.outgoing.map((item, idx) => (
                    <div
                      key={idx}
                      onClick={() => setSelectedNode(item.node)}
                      className="p-1.5 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800 cursor-pointer flex items-center justify-between text-[11px] transition"
                    >
                      <span className="text-slate-200 font-medium truncate">
                        {item.node.label}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {item.rel}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions: Delete Node */}
            <div className="pt-2 border-t border-slate-800 flex justify-end">
              <button
                onClick={async () => {
                  await onDeleteNode(selectedNode.id);
                  setSelectedNode(null);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-950/70 hover:bg-rose-900 text-rose-300 border border-rose-800/60 transition text-xs font-medium"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>{t.graph.deleteNode}</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Add Node Modal */}
      {showAddNodeModal && (
        <div className="absolute inset-0 z-40 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="w-full max-w-sm rounded-xl bg-slate-900 border border-slate-700 p-5 shadow-2xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-xs font-semibold text-slate-100">{t.graph.modalAddNodeTitle}</h3>
              <button onClick={() => setShowAddNodeModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateNode} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 mb-1 font-medium">{t.graph.nodeId}</label>
                <input
                  type="text"
                  required
                  placeholder="symptom_bgp_route_flap"
                  value={newNodeId}
                  onChange={(e) => setNewNodeId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-purple-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">{t.graph.nodeLabelLabel}</label>
                <input
                  type="text"
                  required
                  placeholder="BGP Route Flapping"
                  value={newNodeLabel}
                  onChange={(e) => setNewNodeLabel(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">{t.graph.nodeType}</label>
                <select
                  value={newNodeType}
                  onChange={(e) => setNewNodeType(e.target.value as NodeType)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-purple-500"
                >
                  <option value="Symptom">{t.graph.symptom}</option>
                  <option value="RootCause">{t.graph.rootCause}</option>
                  <option value="Verification">{t.graph.verification}</option>
                  <option value="Command">{t.graph.command}</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">{t.graph.nodeDescLabel}</label>
                <textarea
                  rows={2}
                  placeholder="Node description..."
                  value={newNodeDesc}
                  onChange={(e) => setNewNodeDesc(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-purple-500 resize-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddNodeModal(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  {t.common.cancel}
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold shadow"
                >
                  {t.graph.addNode}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Edge Modal */}
      {showAddEdgeModal && (
        <div className="absolute inset-0 z-40 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="w-full max-w-sm rounded-xl bg-slate-900 border border-slate-700 p-5 shadow-2xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-xs font-semibold text-slate-100">{t.graph.modalAddEdgeTitle}</h3>
              <button onClick={() => setShowAddEdgeModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateEdge} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 mb-1 font-medium">{t.graph.sourceNode}</label>
                <select
                  required
                  value={newEdgeSource}
                  onChange={(e) => setNewEdgeSource(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-purple-500"
                >
                  <option value="">-- {t.graph.sourceNode} --</option>
                  {graphData.nodes.map((n) => (
                    <option key={n.id} value={n.id}>
                      [{n.type}] {n.label} ({n.id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">{t.graph.targetNode}</label>
                <select
                  required
                  value={newEdgeTarget}
                  onChange={(e) => setNewEdgeTarget(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-purple-500"
                >
                  <option value="">-- {t.graph.targetNode} --</option>
                  {graphData.nodes.map((n) => (
                    <option key={n.id} value={n.id}>
                      [{n.type}] {n.label} ({n.id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">{t.graph.relationshipType}</label>
                <input
                  type="text"
                  placeholder="leads_to, verified_by, fixed_by, executes..."
                  value={newEdgeRel}
                  onChange={(e) => setNewEdgeRel(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddEdgeModal(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  {t.common.cancel}
                </button>
                <button
                  type="submit"
                  disabled={!newEdgeSource || !newEdgeTarget}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow disabled:opacity-50"
                >
                  {t.graph.addEdge}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
