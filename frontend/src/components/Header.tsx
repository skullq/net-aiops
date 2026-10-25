"use client";

import React from "react";
import {
  RotateCcw,
  Settings,
  Server,
  Network,
  Bot,
  Layers,
  Globe,
  Bug,
  BugOff,
} from "lucide-react";
import { AppConfig, GraphData } from "@/types";
import { useI18n } from "@/i18n";

export type ActiveTab = "diagnostics" | "graph_studio";

interface HeaderProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  config: AppConfig | null;
  graphData: GraphData;
  backendHealthy: boolean;
  onOpenSettings: () => void;
  onOpenDeviceManager: () => void;
  deviceCount?: number;
  onResetGraph?: () => void;
  isResetting?: boolean;
  debugMode?: boolean;
  onToggleDebugMode?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  config,
  graphData,
  backendHealthy,
  onOpenSettings,
  onOpenDeviceManager,
  deviceCount = 0,
  onResetGraph,
  isResetting,
  debugMode = true,
  onToggleDebugMode,
}) => {
  const { language, setLanguage, t } = useI18n();

  return (
    <header className="h-14 border-b border-slate-800 bg-slate-950/90 backdrop-blur-md px-4 flex items-center justify-between select-none z-30">
      {/* Brand Logo & Name */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Network className="w-4 h-4 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-semibold tracking-wide text-slate-100">
              {t.header.title}
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 font-medium">
              v1.0
            </span>
          </div>
          <p className="text-[11px] text-slate-400 hidden sm:block">
            {t.header.subtitle}
          </p>
        </div>
      </div>

      {/* Center Tab Navigation */}
      <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-slate-800 shadow-inner">
        <button
          onClick={() => onTabChange("diagnostics")}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === "diagnostics"
              ? "bg-cyan-600 text-white shadow-md shadow-cyan-600/30 font-semibold"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          }`}
        >
          <Bot className="w-3.5 h-3.5" />
          <span>{t.header.tabDiagnostics}</span>
        </button>

        <button
          onClick={() => onTabChange("graph_studio")}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === "graph_studio"
              ? "bg-purple-600 text-white shadow-md shadow-purple-600/30 font-semibold"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>{t.header.tabGraphStudio}</span>
          <span
            className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
              activeTab === "graph_studio"
                ? "bg-purple-800/80 text-purple-200"
                : "bg-slate-800 text-slate-400"
            }`}
          >
            {graphData.nodes.length}
          </span>
        </button>
      </div>

      {/* System Status Badges, Language Selector & Actions */}
      <div className="flex items-center gap-2 text-xs">
        {/* Backend Status */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
          <div
            className={`w-2 h-2 rounded-full ${
              backendHealthy ? "bg-emerald-400 shadow-sm shadow-emerald-400/50" : "bg-rose-500 animate-ping"
            }`}
          />
          <span className="text-[11px] font-medium">
            {backendHealthy ? t.header.fastapiLive : t.header.fastapiOffline}
          </span>
        </div>

        {/* Cisco IOS-XE Device Status & Manager Trigger */}
        <button
          onClick={onOpenDeviceManager}
          title={t.header.deviceManagerTooltip}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-slate-200 hover:border-cyan-500/50 transition cursor-pointer group shadow-sm"
        >
          <Server className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-110 transition-transform" />
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-xs text-slate-200">
              {t.header.networkDevices}
            </span>
            <span className="text-[10px] font-mono text-cyan-300 px-1.5 py-0.2 rounded bg-cyan-950/80 border border-cyan-800/40">
              {deviceCount}{t.header.deviceCountUnit}
            </span>
            <span className="text-[9px] px-1.5 py-0.2 rounded font-semibold bg-emerald-950/70 text-emerald-400 border border-emerald-800/50">
              {t.header.alwaysConnected}
            </span>
          </div>
        </button>

        {/* Debug Mode Toggle Button */}
        {onToggleDebugMode && (
          <button
            onClick={onToggleDebugMode}
            title={debugMode ? t.header.debugTooltipOn : t.header.debugTooltipOff}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-semibold border transition shadow-xs ${
              debugMode
                ? "bg-amber-950/70 border-amber-500/70 text-amber-300 hover:bg-amber-900/80 shadow-amber-500/20"
                : "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
            }`}
          >
            {debugMode ? (
              <Bug className="w-3.5 h-3.5 text-amber-400" />
            ) : (
              <BugOff className="w-3.5 h-3.5 text-slate-500" />
            )}
            <span className="hidden md:inline font-mono">
              {debugMode ? t.header.debugOn : t.header.debugOff}
            </span>
          </button>
        )}

        {/* Settings Modal Trigger */}
        <button
          onClick={onOpenSettings}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium text-xs shadow-md shadow-cyan-600/20 transition"
        >
          <Settings className="w-3.5 h-3.5" />
          <span>{t.header.llmSettings}</span>
        </button>

        {/* Language Selector (KO / EN Toggle) */}
        <div className="flex items-center p-0.5 rounded-lg bg-slate-900 border border-slate-700/80 shadow-xs">
          <button
            onClick={() => setLanguage("ko")}
            title="한국어로 변경"
            className={`px-2 py-1 rounded text-[11px] font-bold transition-all ${
              language === "ko"
                ? "bg-cyan-600 text-white shadow-xs"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            KO
          </button>
          <button
            onClick={() => setLanguage("en")}
            title="Switch to English"
            className={`px-2 py-1 rounded text-[11px] font-bold transition-all ${
              language === "en"
                ? "bg-cyan-600 text-white shadow-xs"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            EN
          </button>
        </div>
      </div>
    </header>
  );
};
