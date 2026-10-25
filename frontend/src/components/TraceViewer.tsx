"use client";

import React, { useState } from "react";
import {
  Activity,
  Terminal,
  Database,
  Clock,
  ChevronDown,
  ChevronRight,
  Code2,
  Copy,
  Check,
  Layers,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import { TraceEvent } from "@/types";
import { useI18n } from "@/i18n";

interface TraceViewerProps {
  traceEvents: TraceEvent[];
  isStreaming: boolean;
  onClearTrace: () => void;
}

export const TraceViewer: React.FC<TraceViewerProps> = ({
  traceEvents,
  isStreaming,
  onClearTrace,
}) => {
  const { t } = useI18n();
  const [expandedIndices, setExpandedIndices] = useState<Record<number, boolean>>({});
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const toggleExpand = (index: number) => {
    setExpandedIndices((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 1500);
  };

  const getStepIcon = (step: string) => {
    if (step.includes("session")) {
      return <Database className="w-3.5 h-3.5 text-emerald-400" />;
    }
    if (step.includes("llm_context") || step.includes("prompt")) {
      return <Sparkles className="w-3.5 h-3.5 text-amber-300" />;
    }
    if (step.includes("graph")) {
      return <Database className="w-3.5 h-3.5 text-purple-400" />;
    }
    if (step.includes("mcp") || step.includes("command")) {
      return <Terminal className="w-3.5 h-3.5 text-cyan-400" />;
    }
    if (step.includes("remediation")) {
      return <Code2 className="w-3.5 h-3.5 text-emerald-400" />;
    }
    if (step.includes("intent") || step.includes("synthesis")) {
      return <Sparkles className="w-3.5 h-3.5 text-amber-400" />;
    }
    return <Activity className="w-3.5 h-3.5 text-blue-400" />;
  };

  const t0 = traceEvents.length > 0 ? new Date(traceEvents[0].timestamp).getTime() : 0;

  return (
    <div className="relative w-full h-full bg-slate-950 flex flex-col select-text overflow-hidden">
      {/* Panel Header */}
      <div className="h-10 px-4 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-semibold text-slate-200">
            {t.trace.title}
          </span>
          {isStreaming && (
            <span className="flex items-center gap-1 text-[10px] text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-1.5 py-0.2 rounded animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              {t.trace.liveBadge}
            </span>
          )}
        </div>

        <button
          onClick={onClearTrace}
          className="text-xs text-slate-400 hover:text-slate-200 hover:underline"
        >
          {t.trace.clear}
        </button>
      </div>

      {/* Timeline Stream Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {traceEvents.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500">
            <Clock className="w-8 h-8 text-slate-600 mb-2 opacity-60" />
            <p className="text-xs font-medium text-slate-400">
              {t.trace.emptyTitle}
            </p>
            <p className="text-[11px] text-slate-500 mt-1 max-w-xs">
              {t.trace.emptyDesc}
            </p>
          </div>
        ) : (
          <div className="relative border-l border-slate-800 ml-3 space-y-4 pb-4">
            {traceEvents.map((event, idx) => {
              const isExpanded = expandedIndices[idx] !== false; // default open
              const hasPayload =
                Boolean(event.parsed_output) ||
                Boolean(event.raw_output) ||
                Boolean(event.remediation_lines) ||
                Boolean(event.paths) ||
                Boolean(event.used_batfish_apis && event.used_batfish_apis.length > 0) ||
                Boolean(event.system_prompt) ||
                Boolean(event.dynamic_context) ||
                Boolean(event.session_id) ||
                Boolean(event.llm_messages);

              const currTime = new Date(event.timestamp).getTime();
              const prevTime = idx > 0 ? new Date(traceEvents[idx - 1].timestamp).getTime() : currTime;

              const elapsedSec =
                !isNaN(currTime) && !isNaN(t0) && currTime >= t0
                  ? ((currTime - t0) / 1000).toFixed(1)
                  : "0.0";
              const stepDurationSec =
                !isNaN(currTime) && !isNaN(prevTime) && currTime >= prevTime
                  ? ((currTime - prevTime) / 1000).toFixed(1)
                  : "0.0";

              return (
                <div key={idx} className="relative pl-6 group">
                  {/* Timeline Node Dot */}
                  <div className="absolute -left-[11px] top-1 w-5 h-5 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center shadow-md">
                    {getStepIcon(event.step)}
                  </div>

                  {/* Card Content */}
                  <div className="rounded-lg bg-slate-900/90 border border-slate-800 overflow-hidden shadow-md">
                    {/* Event Header */}
                    <div
                      onClick={() => hasPayload && toggleExpand(idx)}
                      className={`p-3 flex items-start justify-between gap-2 ${
                        hasPayload ? "cursor-pointer hover:bg-slate-850" : ""
                      }`}
                    >
                      <div className="space-y-1.5 flex-1 min-w-0">
                        {/* 1. 검증 제목 */}
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-slate-100 break-words">
                            {event.title}
                          </span>
                        </div>

                        {/* 2. 검증제목 바로 밑 한줄: 성공 배지 + 소요시간 + 타임스탬프 (명령어 제거) */}
                        <div className="flex items-center gap-2 flex-wrap text-[10px] font-mono">
                          {event.status === "success" && (
                            <span className="text-emerald-400 bg-emerald-950/70 border border-emerald-800/40 px-1.5 py-0.5 rounded font-medium">
                              {t.trace.successBadge}
                            </span>
                          )}
                          {event.status === "error" && (
                            <span className="text-rose-400 bg-rose-950/70 border border-rose-800/40 px-1.5 py-0.5 rounded font-medium">
                              {t.trace.failedBadge}
                            </span>
                          )}
                          {event.status === "in_progress" && (
                            <span className="text-cyan-400 bg-cyan-950/70 border border-cyan-800/40 px-1.5 py-0.5 rounded font-medium animate-pulse">
                              진행중
                            </span>
                          )}
                          <span className="inline-flex items-center gap-1 font-semibold text-cyan-300 bg-cyan-950/70 border border-cyan-800/50 px-1.5 py-0.5 rounded shadow-sm">
                            <Clock className="w-2.5 h-2.5 text-cyan-400" />
                            {idx === 0 ? (
                              <span>+{elapsedSec}s ({t.trace.startBadge})</span>
                            ) : (
                              <span>+{elapsedSec}s ({stepDurationSec}s {t.trace.tookTime})</span>
                            )}
                          </span>
                          <span className="text-slate-500">
                            {new Date(event.timestamp).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                              second: "2-digit",
                            })}
                          </span>
                        </div>

                        {/* 3. 설명 메시지 */}
                        {event.message && (
                          <p className="text-[11px] text-slate-300 leading-relaxed pt-0.5">
                            {event.message}
                          </p>
                        )}
                      </div>

                      {/* Header Right: Expand Chevron Arrow Only */}
                      {hasPayload && (
                        <div className="text-slate-400 pl-1 pt-0.5 shrink-0">
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-slate-400 hover:text-slate-200" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-slate-400 hover:text-slate-200" />
                          )}
                        </div>
                      )}
                    </div>

                    {/* Expandable Payload Body */}
                    {hasPayload && isExpanded && (
                      <div className="border-t border-slate-800/80 bg-slate-950/60 p-3 space-y-2.5 text-xs">
                        {/* Batfish Formal Question APIs Used */}
                        {event.used_batfish_apis && event.used_batfish_apis.length > 0 && (
                          <div className="space-y-1.5 p-2.5 rounded-lg bg-blue-950/40 border border-blue-800/50">
                            <span className="text-[10px] font-semibold uppercase text-blue-300 tracking-wider flex items-center gap-1">
                              <Code2 className="w-3.5 h-3.5 text-cyan-400" />
                              Batfish 정형 질의 실행 API (Formal Question APIs)
                            </span>
                            <div className="flex flex-wrap gap-1.5 font-mono text-[10.5px] pt-1">
                              {event.used_batfish_apis.map((api, aIdx) => (
                                <span
                                  key={aIdx}
                                  className="px-2 py-0.5 rounded bg-blue-900/60 border border-blue-700/60 text-cyan-200 shadow-sm"
                                >
                                  {api}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {/* 0. Session Troubleshooting Record */}
                        {event.session_id && (
                          <div className="space-y-1.5 p-2.5 rounded bg-emerald-950/40 border border-emerald-800/50">
                            <div className="flex items-center justify-between text-[11px] text-emerald-300 font-semibold">
                              <span className="flex items-center gap-1.5">
                                🛠️ Session ID: <code className="font-mono bg-emerald-900/60 px-1.5 py-0.5 rounded text-emerald-200">{event.session_id}</code>
                              </span>
                              <button
                                onClick={() => handleCopy(event.session_id || "", `sess_${idx}`)}
                                className="flex items-center gap-1 text-[10px] text-emerald-400 hover:text-white transition"
                              >
                                {copiedKey === `sess_${idx}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                                <span>{copiedKey === `sess_${idx}` ? t.chat.copied : t.chat.copy}</span>
                              </button>
                            </div>
                            <div className="text-[10px] font-mono text-emerald-200/90 space-y-1 pt-1">
                              <div>• JSON Data: <code className="bg-slate-900 px-1.5 py-0.5 rounded text-cyan-300">{event.json_log_path}</code></div>
                              <div>• Text Trace: <code className="bg-slate-900 px-1.5 py-0.5 rounded text-amber-300">{event.text_log_path}</code></div>
                            </div>
                          </div>
                        )}

                        {/* 1. GraphDB Traversal Path Display */}
                        {event.paths && event.paths.length > 0 && (
                          <div className="space-y-1.5">
                            <span className="text-[10px] font-semibold uppercase text-purple-400 tracking-wider flex items-center gap-1">
                              <Layers className="w-3 h-3" />
                              {t.trace.graphPaths}
                            </span>
                            <div className="space-y-1 font-mono text-[11px]">
                              {event.paths.map((p, pIdx) => (
                                <div
                                  key={pIdx}
                                  className="p-2 rounded bg-purple-950/30 border border-purple-800/40 text-purple-200 flex flex-wrap items-center gap-1.5"
                                >
                                  {p.steps.map((st, sIdx) => (
                                    <React.Fragment key={st.id}>
                                      <span className="px-1.5 py-0.5 rounded bg-purple-900/60 border border-purple-700/60 text-[10px]">
                                        {st.label}
                                      </span>
                                      {sIdx < p.steps.length - 1 && (
                                        <ArrowRight className="w-3 h-3 text-purple-400 shrink-0" />
                                      )}
                                    </React.Fragment>
                                  ))}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* 2. TextFSM Parsed JSON Tree View */}
                        {event.parsed_output && (
                          <div className="space-y-1.5">
                            <div className="flex items-center justify-between text-[10px] text-cyan-400 font-semibold uppercase tracking-wider">
                              <span className="flex items-center gap-1">
                                <Terminal className="w-3 h-3" />
                                {t.trace.parsedOutput}
                              </span>
                              <button
                                onClick={() =>
                                  handleCopy(
                                    JSON.stringify(event.parsed_output, null, 2),
                                    `parsed_${idx}`
                                  )
                                }
                                className="flex items-center gap-1 text-slate-400 hover:text-white transition"
                              >
                                {copiedKey === `parsed_${idx}` ? (
                                  <Check className="w-3 h-3 text-emerald-400" />
                                ) : (
                                  <Copy className="w-3 h-3" />
                                )}
                                <span>{copiedKey === `parsed_${idx}` ? t.chat.copied : t.chat.copy}</span>
                              </button>
                            </div>

                            <pre className="p-2.5 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-cyan-300 overflow-x-auto max-h-48 leading-relaxed">
                              {JSON.stringify(event.parsed_output, null, 2)}
                            </pre>
                          </div>
                        )}

                        {/* 3. Raw CLI Terminal Output */}
                        {event.raw_output && (
                          <div className="space-y-1.5">
                            <div className="flex items-center justify-between text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
                              <span>{t.trace.rawCliOutput}</span>
                              <button
                                onClick={() => handleCopy(event.raw_output || "", `raw_${idx}`)}
                                className="flex items-center gap-1 text-slate-400 hover:text-white transition"
                              >
                                {copiedKey === `raw_${idx}` ? (
                                  <Check className="w-3 h-3 text-emerald-400" />
                                ) : (
                                  <Copy className="w-3 h-3" />
                                )}
                                <span>{copiedKey === `raw_${idx}` ? t.chat.copied : t.chat.copy}</span>
                              </button>
                            </div>

                            <pre className="p-2.5 rounded bg-slate-950 border border-slate-800/80 text-[10px] font-mono text-slate-300 overflow-x-auto max-h-36 leading-tight whitespace-pre-wrap">
                              {event.raw_output}
                            </pre>
                          </div>
                        )}

                        {/* 4. hier-config Remediation CLI script */}
                        {event.remediation_lines && event.remediation_lines.length > 0 && (
                          <div className="space-y-1.5">
                            <div className="flex items-center justify-between text-[10px] text-emerald-400 font-semibold uppercase tracking-wider">
                              <span className="flex items-center gap-1">
                                <Code2 className="w-3 h-3" />
                                {t.trace.remediationScript}
                              </span>
                              <button
                                onClick={() =>
                                  handleCopy(
                                    event.remediation_text || event.remediation_lines?.join("\n") || "",
                                    `rem_${idx}`
                                  )
                                }
                                className="flex items-center gap-1 text-slate-400 hover:text-white transition"
                              >
                                {copiedKey === `rem_${idx}` ? (
                                  <Check className="w-3 h-3 text-emerald-400" />
                                ) : (
                                  <Copy className="w-3 h-3" />
                                )}
                                <span>{copiedKey === `rem_${idx}` ? t.chat.copied : t.chat.copy}</span>
                              </button>
                            </div>

                            <pre className="p-2.5 rounded bg-emerald-950/20 border border-emerald-800/50 text-[11px] font-mono text-emerald-300 overflow-x-auto leading-relaxed">
                              {event.remediation_text || event.remediation_lines.join("\n")}
                            </pre>
                          </div>
                        )}

                        {/* 5. LLM Prompt & Injected Dynamic Context Display */}
                        {(event.system_prompt || event.dynamic_context || event.llm_messages) && (
                          <div className="space-y-2.5 rounded-lg bg-amber-950/25 border border-amber-800/50 p-3">
                            <div className="flex items-center justify-between text-[10px] text-amber-300 font-semibold uppercase tracking-wider">
                              <span className="flex items-center gap-1.5">
                                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                                {t.trace.llmPromptPayload}
                              </span>
                              {event.llm_messages && (
                                <button
                                  onClick={() =>
                                    handleCopy(
                                      JSON.stringify(event.llm_messages, null, 2),
                                      `llm_msg_${idx}`
                                    )
                                  }
                                  className="flex items-center gap-1 text-[10px] text-amber-400/80 hover:text-amber-200 transition"
                                >
                                  {copiedKey === `llm_msg_${idx}` ? (
                                    <Check className="w-3 h-3 text-emerald-400" />
                                  ) : (
                                    <Copy className="w-3 h-3" />
                                  )}
                                  <span>{copiedKey === `llm_msg_${idx}` ? t.chat.copied : t.chat.copy}</span>
                                </button>
                              )}
                            </div>

                            {/* System Prompt View */}
                            {event.system_prompt && (
                              <div className="space-y-1">
                                <span className="text-[10px] font-semibold text-amber-400/90 block">
                                  {t.trace.systemPromptTitle}
                                </span>
                                <pre className="p-2 rounded bg-slate-950/80 border border-amber-900/40 text-[11px] font-mono text-amber-200 leading-relaxed whitespace-pre-wrap">
                                  {event.system_prompt}
                                </pre>
                              </div>
                            )}

                            {/* Dynamic Context View */}
                            {event.dynamic_context && (
                              <div className="space-y-1">
                                <div className="flex items-center justify-between text-[10px] text-amber-400/90 font-semibold">
                                  <span>{t.trace.dynamicContextTitle}</span>
                                  <button
                                    onClick={() =>
                                      handleCopy(
                                        JSON.stringify(event.dynamic_context, null, 2),
                                        `dyn_${idx}`
                                      )
                                    }
                                    className="flex items-center gap-1 text-slate-400 hover:text-white transition"
                                  >
                                    {copiedKey === `dyn_${idx}` ? (
                                      <Check className="w-3 h-3 text-emerald-400" />
                                    ) : (
                                      <Copy className="w-3 h-3" />
                                    )}
                                    <span>{copiedKey === `dyn_${idx}` ? t.chat.copied : t.chat.copy}</span>
                                  </button>
                                </div>
                                <pre className="p-2.5 rounded bg-slate-950 border border-slate-800 text-[10px] font-mono text-amber-100 overflow-x-auto max-h-52 leading-relaxed">
                                  {JSON.stringify(event.dynamic_context, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
