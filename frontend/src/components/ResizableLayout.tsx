"use client";

import React from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { GripVertical } from "lucide-react";

interface ResizableLayoutProps {
  chatPanel: React.ReactNode;
  tracePanel: React.ReactNode;
}

export const ResizableLayout: React.FC<ResizableLayoutProps> = ({
  chatPanel,
  tracePanel,
}) => {
  return (
    <div className="flex-1 w-full h-[calc(100vh-3.5rem)] overflow-hidden">
      <PanelGroup direction="horizontal" autoSaveId="net-aiops-diagnostics-layout">
        {/* Left Panel: Unified AI Chat */}
        <Panel defaultSize={52} minSize={30} maxSize={75} id="chat-panel">
          {chatPanel}
        </Panel>

        {/* Resize Handle */}
        <PanelResizeHandle className="relative w-1.5 bg-slate-900 hover:bg-cyan-500/50 active:bg-cyan-500 transition-colors flex items-center justify-center group cursor-col-resize select-none">
          <div className="absolute w-4 h-8 rounded flex items-center justify-center text-slate-600 group-hover:text-cyan-300">
            <GripVertical className="w-3 h-3" />
          </div>
        </PanelResizeHandle>

        {/* Right Panel: Real-time Trace Viewer */}
        <Panel defaultSize={48} minSize={25} maxSize={70} id="trace-panel">
          {tracePanel}
        </Panel>
      </PanelGroup>
    </div>
  );
};
