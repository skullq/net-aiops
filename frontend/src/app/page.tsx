"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Header, ActiveTab } from "@/components/Header";
import { ResizableLayout } from "@/components/ResizableLayout";
import { GraphStudio } from "@/components/GraphStudio";
import { ChatPanel } from "@/components/ChatPanel";
import { TraceViewer } from "@/components/TraceViewer";
import { SettingsModal } from "@/components/SettingsModal";
import { DeviceManagerModal } from "@/components/DeviceManagerModal";
import {
  AppConfig,
  ChatMessage,
  GraphData,
  GraphLink,
  GraphNode,
  ManagedDevice,
  TraceEvent,
} from "@/types";
import { I18nProvider, useI18n } from "@/i18n";

function NetAIOpsStudio() {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState<ActiveTab>("diagnostics");

  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [backendHealthy, setBackendHealthy] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDeviceManagerOpen, setIsDeviceManagerOpen] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  // Managed Devices State (from devices.env / devices.json)
  const [devices, setDevices] = useState<ManagedDevice[]>([]);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [traceEvents, setTraceEvents] = useState<TraceEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [highlightedNodeIds, setHighlightedNodeIds] = useState<string[]>([]);

  // 1. Backend Data Fetchers
  const fetchGraphData = useCallback(async () => {
    try {
      const res = await fetch("/api/graph");
      if (res.ok) {
        const data = await res.json();
        setGraphData(data);
        setBackendHealthy(true);
      } else {
        setBackendHealthy(false);
      }
    } catch (err) {
      console.error("Failed to fetch graph data:", err);
      setBackendHealthy(false);
    }
  }, []);

  const fetchConfig = useCallback(async () => {
    try {
      const res = await fetch("/api/config");
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
      }
    } catch (err) {
      console.error("Failed to fetch config:", err);
    }
  }, []);

  const fetchDevices = useCallback(async () => {
    try {
      const res = await fetch("/api/devices");
      if (res.ok) {
        const data = await res.json();
        setDevices(data.devices || []);
      }
    } catch (err) {
      console.error("Failed to fetch devices:", err);
    }
  }, []);

  useEffect(() => {
    fetchGraphData();
    fetchConfig();
    fetchDevices();

    // Heartbeat every 15s
    const interval = setInterval(() => {
      fetch("/api/health")
        .then((res) => setBackendHealthy(res.ok))
        .catch(() => setBackendHealthy(false));
    }, 15000);

    return () => clearInterval(interval);
  }, [fetchGraphData, fetchConfig, fetchDevices]);

  // 2. Device Management Handlers
  const handleUpdateDevice = async (deviceId: string, data: Partial<ManagedDevice>) => {
    try {
      const res = await fetch(`/api/devices/${deviceId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (res.ok) {
        await fetchDevices();
        await fetchConfig();
      }
    } catch (err) {
      console.error("Error updating device:", err);
    }
  };

  const handleAddDevice = async (newDev: ManagedDevice) => {
    try {
      const res = await fetch("/api/devices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newDev),
      });
      if (res.ok) {
        await fetchDevices();
        await fetchConfig();
      }
    } catch (err) {
      console.error("Error adding device:", err);
    }
  };

  const handleDeleteDevice = async (deviceId: string) => {
    try {
      const res = await fetch(`/api/devices/${deviceId}`, { method: "DELETE" });
      if (res.ok) {
        await fetchDevices();
        await fetchConfig();
      }
    } catch (err) {
      console.error("Error deleting device:", err);
    }
  };

  // 3. Graph CRUD Handlers
  const handleAddNode = async (node: GraphNode) => {
    try {
      const res = await fetch("/api/graph/nodes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(node),
      });
      if (res.ok) {
        await fetchGraphData();
      }
    } catch (err) {
      console.error("Error adding node:", err);
    }
  };

  const handleDeleteNode = async (nodeId: string) => {
    try {
      const res = await fetch(`/api/graph/nodes/${nodeId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        await fetchGraphData();
      }
    } catch (err) {
      console.error("Error deleting node:", err);
    }
  };

  const handleAddEdge = async (edge: GraphLink) => {
    try {
      const res = await fetch("/api/graph/edges", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(edge),
      });
      if (res.ok) {
        await fetchGraphData();
      }
    } catch (err) {
      console.error("Error adding edge:", err);
    }
  };

  const handleDeleteEdge = async (source: string, target: string) => {
    try {
      const res = await fetch(`/api/graph/edges?source=${source}&target=${target}`, {
        method: "DELETE",
      });
      if (res.ok) {
        await fetchGraphData();
      }
    } catch (err) {
      console.error("Error deleting edge:", err);
    }
  };

  const handleResetGraph = async () => {
    setIsResetting(true);
    try {
      const res = await fetch("/api/graph/reset", { method: "POST" });
      if (res.ok) {
        await fetchGraphData();
      }
    } finally {
      setIsResetting(false);
    }
  };

  // 4. Settings Save Handler
  const handleSaveConfig = async (newConfig: AppConfig) => {
    try {
      const res = await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newConfig),
      });
      if (res.ok) {
        setConfig(newConfig);
      }
    } catch (err) {
      console.error("Failed to update config:", err);
    }
  };

  // 5. Chat & SSE Streaming Execution
  const handleSendMessage = async (text: string) => {
    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    const assistantMsgId = `assistant_${Date.now()}`;
    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          history: messages.slice(-4).map((m) => ({ role: m.role, content: m.content })),
          llm_config: config?.llm,
          device_config: config?.device,
        }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`SSE request failed with status ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("event:")) {
            currentEvent = trimmed.replace("event:", "").trim();
          } else if (trimmed.startsWith("data:")) {
            const dataStr = trimmed.replace("data:", "").trim();
            if (!dataStr) continue;

            try {
              const parsed = JSON.parse(dataStr);

              if (currentEvent === "trace") {
                setTraceEvents((prev) => [...prev, parsed]);
              } else if (currentEvent === "graph_path") {
                setTraceEvents((prev) => [...prev, parsed]);
                // Highlight nodes in the graph
                if (parsed.paths && parsed.paths.length > 0) {
                  const nodeIds: string[] = [];
                  parsed.paths.forEach((p: any) => {
                    p.steps?.forEach((st: any) => nodeIds.push(st.id));
                  });
                  setHighlightedNodeIds(Array.from(new Set(nodeIds)));
                } else if (parsed.start_node) {
                  setHighlightedNodeIds([parsed.start_node]);
                }
              } else if (currentEvent === "mcp_result") {
                setTraceEvents((prev) => [...prev, parsed]);
              } else if (currentEvent === "llm_token") {
                const token = parsed.token || "";
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? { ...msg, content: msg.content + token }
                      : msg
                  )
                );
              } else if (currentEvent === "complete") {
                setIsStreaming(false);
              }
            } catch (jsonErr) {
              // Ignore partial JSON chunks
            }
          }
        }
      }
    } catch (err) {
      console.error("SSE stream error:", err);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                content:
                  msg.content || t.chat.apiFailError,
              }
            : msg
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950 select-none">
      {/* 1. Header with Tab Navigation, Device Button and Settings */}
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        config={config}
        graphData={graphData}
        backendHealthy={backendHealthy}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenDeviceManager={() => setIsDeviceManagerOpen(true)}
        deviceCount={devices.length}
        onResetGraph={handleResetGraph}
        isResetting={isResetting}
      />

      {/* 2. Main Viewport switching by Active Tab */}
      <main className="flex-1 w-full h-[calc(100vh-3.5rem)] overflow-hidden relative">
        {/* Tab 1: AIOps 통합 진단 워크스페이스 (Chat + Trace Timeline) */}
        <div
          className={`w-full h-full ${
            activeTab === "diagnostics" ? "block" : "hidden"
          }`}
        >
          <ResizableLayout
            chatPanel={
              <ChatPanel
                messages={messages}
                onSendMessage={handleSendMessage}
                isStreaming={isStreaming}
                onClearChat={() => {
                  setMessages([]);
                  setHighlightedNodeIds([]);
                }}
              />
            }
            tracePanel={
              <TraceViewer
                traceEvents={traceEvents}
                isStreaming={isStreaming}
                onClearTrace={() => setTraceEvents([])}
              />
            }
          />
        </div>

        {/* Tab 2: Graph Causal Studio 전용 캔버스 뷰 */}
        <div
          className={`w-full h-full ${
            activeTab === "graph_studio" ? "block" : "hidden"
          }`}
        >
          <GraphStudio
            graphData={graphData}
            onAddNode={handleAddNode}
            onDeleteNode={handleDeleteNode}
            onAddEdge={handleAddEdge}
            onDeleteEdge={handleDeleteEdge}
            highlightedNodeIds={highlightedNodeIds}
            isDedicatedTab={true}
          />
        </div>
      </main>

      {/* 3. Settings Modal (LLM Provider) */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        config={config}
        onSave={handleSaveConfig}
      />

      {/* 4. Dedicated Cisco IOS-XE Device Manager Modal */}
      <DeviceManagerModal
        isOpen={isDeviceManagerOpen}
        onClose={() => setIsDeviceManagerOpen(false)}
        devices={devices}
        onAddDevice={handleAddDevice}
        onUpdateDevice={handleUpdateDevice}
        onDeleteDevice={handleDeleteDevice}
      />
    </div>
  );
}

export default function Home() {
  return (
    <I18nProvider>
      <NetAIOpsStudio />
    </I18nProvider>
  );
}
