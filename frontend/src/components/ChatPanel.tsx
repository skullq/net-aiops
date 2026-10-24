"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Bot,
  User,
  Sparkles,
  Copy,
  Check,
  RotateCcw,
} from "lucide-react";
import { ChatMessage } from "@/types";
import { useI18n } from "@/i18n";

interface ChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  isStreaming: boolean;
  onClearChat: () => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  onSendMessage,
  isStreaming,
  onClearChat,
}) => {
  const { t } = useI18n();
  const [inputText, setInputText] = useState("");
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isStreaming) return;
    onSendMessage(inputText.trim());
    setInputText("");
  };

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 1500);
  };

  const quickPrompts = [
    {
      title: t.chat.quick1Title,
      prompt: t.chat.quick1Prompt,
      icon: "🌐",
    },
    {
      title: t.chat.quick2Title,
      prompt: t.chat.quick2Prompt,
      icon: "⚡",
    },
    {
      title: t.chat.quick3Title,
      prompt: t.chat.quick3Prompt,
      icon: "🛠️",
    },
  ];

  return (
    <div className="relative w-full h-full bg-slate-900 flex flex-col border-r border-slate-800 select-text">
      {/* Panel Header */}
      <div className="h-10 px-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-semibold text-slate-200">
            {t.chat.title}
          </span>
        </div>
        <button
          onClick={onClearChat}
          title={t.chat.clearHistory}
          className="text-slate-400 hover:text-slate-200 p-1 rounded hover:bg-slate-800 transition"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4 max-w-md mx-auto space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-600/30 to-blue-600/30 border border-cyan-500/30 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-200 mb-1">
                {t.chat.emptyTitle}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                {t.chat.emptyDesc}
              </p>
            </div>

            {/* Quick Prompts */}
            <div className="w-full space-y-2 pt-2">
              <span className="text-[11px] font-medium text-slate-400 block text-left">
                {t.chat.quickScenarios}
              </span>
              {quickPrompts.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(item.prompt)}
                  className="w-full text-left p-2.5 rounded-lg bg-slate-950/60 hover:bg-slate-800/80 border border-slate-800 hover:border-cyan-500/40 transition group flex items-center justify-between"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{item.icon}</span>
                    <span className="text-xs font-medium text-slate-300 group-hover:text-cyan-300">
                      {item.title}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 group-hover:text-cyan-400 font-mono">
                    {t.chat.runDiagnostic}
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isUser = msg.role === "user";
            return (
              <div
                key={msg.id}
                className={`flex gap-3 text-xs ${
                  isUser ? "justify-end" : "justify-start"
                }`}
              >
                {!isUser && (
                  <div className="w-7 h-7 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800 flex items-center justify-center shrink-0 mt-0.5 shadow">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`relative max-w-[85%] rounded-xl p-3.5 shadow-md leading-relaxed ${
                    isUser
                      ? "bg-cyan-600 text-white rounded-tr-none"
                      : "bg-slate-950/90 text-slate-200 border border-slate-800 rounded-tl-none"
                  }`}
                >
                  {/* Copy Button for Assistant message */}
                  {!isUser && (
                    <button
                      onClick={() => handleCopy(msg.content, index)}
                      className="absolute top-2.5 right-2.5 text-slate-400 hover:text-white p-1 rounded bg-slate-800/60 hover:bg-slate-800 transition"
                      title={copiedIndex === index ? t.chat.copied : t.chat.copy}
                    >
                      {copiedIndex === index ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  )}

                  {/* Message Content Rendered */}
                  <div className="whitespace-pre-wrap break-words space-y-2 font-sans">
                    {msg.content}
                  </div>

                  <div className="mt-1.5 flex items-center justify-between text-[10px] opacity-60">
                    <span>
                      {new Date(msg.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>

                {isUser && (
                  <div className="w-7 h-7 rounded-lg bg-slate-800 text-slate-300 border border-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Live typing indicator */}
        {isStreaming && (
          <div className="flex gap-3 text-xs items-center text-cyan-400 animate-pulse">
            <div className="w-7 h-7 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800 flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950/80 border border-cyan-900/60 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              <span>{t.chat.streaming}</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <div className="p-3 bg-slate-950 border-t border-slate-800 shrink-0">
        <form onSubmit={handleSubmit} className="relative flex items-center gap-2">
          <textarea
            rows={1}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder={t.chat.inputPlaceholder}
            disabled={isStreaming}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition resize-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isStreaming}
            className="px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-800 text-white font-medium text-xs shadow-md shadow-cyan-600/20 transition flex items-center justify-center disabled:opacity-50 shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
