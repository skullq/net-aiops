"use client";

import React, { useState, useEffect, useCallback } from "react";
import { X, Server, Sparkles, Key, Check, Info, Bug, RefreshCw, ChevronDown } from "lucide-react";
import { AppConfig } from "@/types";
import { useI18n } from "@/i18n";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: AppConfig | null;
  onSave: (newConfig: AppConfig) => Promise<void>;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  config,
  onSave,
}) => {
  const { t } = useI18n();
  const [formData, setFormData] = useState<AppConfig>({
    llm: {
      base_url: "https://generativelanguage.googleapis.com/v1beta/openai",
      api_key: "",
      model: "gemini-2.5-flash",
    },
    device: {
      host: "192.168.100.11",
      port: 22,
      username: "admin",
      password: "admin",
      enable_password: "admin",
    },
  });

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [availableModels, setAvailableModels] = useState<string[]>([
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gpt-4o",
    "gpt-4o-mini",
  ]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);

  const fetchModels = useCallback(async (apiKey?: string, baseUrl?: string) => {
    setIsLoadingModels(true);
    try {
      const res = await fetch("/api/llm/models", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          api_key: apiKey || "",
          base_url: baseUrl || "",
        }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.models && data.models.length > 0) {
          setAvailableModels(data.models);
        }
      }
    } catch (err) {
      console.warn("Failed to fetch available LLM models:", err);
    } finally {
      setIsLoadingModels(false);
    }
  }, []);

  useEffect(() => {
    if (config) {
      setFormData(config);
    }
  }, [config, isOpen]);

  useEffect(() => {
    if (isOpen) {
      fetchModels(formData.llm.api_key, formData.llm.base_url);
    }
  }, [isOpen, fetchModels]);

  // API 키 입력 시 디바운스(600ms)로 사용 가능한 모델 목록 자동 갱신
  useEffect(() => {
    if (!isOpen) return;
    const timer = setTimeout(() => {
      if (formData.llm.api_key && !formData.llm.api_key.startsWith("***")) {
        fetchModels(formData.llm.api_key, formData.llm.base_url);
      }
    }, 600);
    return () => clearTimeout(timer);
  }, [formData.llm.api_key, formData.llm.base_url, isOpen, fetchModels]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(formData);
      setSaveSuccess(true);
      setTimeout(() => {
        setSaveSuccess(false);
        onClose();
      }, 700);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-xl glass-modal rounded-xl shadow-2xl overflow-hidden border border-slate-700/60 bg-slate-900/95">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-cyan-950/70 text-cyan-400 border border-cyan-800/40">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100">
                {t.settings.modalTitle}
              </h2>
              <p className="text-xs text-slate-400">
                {t.settings.modalDesc}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          {/* Section 1: LLM Configuration */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-cyan-400">
              <Key className="w-3.5 h-3.5" />
              <span>{t.settings.llmSectionTitle}</span>
            </div>

            <div className="grid grid-cols-1 gap-3 text-xs">
              <div>
                <label className="block text-slate-300 mb-1 font-medium">
                  {t.settings.baseUrl}
                </label>
                <input
                  type="text"
                  value={formData.llm.base_url}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      llm: { ...formData.llm, base_url: e.target.value },
                    })
                  }
                  placeholder="https://generativelanguage.googleapis.com/v1beta/openai"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 mb-1 font-medium">
                    {t.settings.apiKey}
                  </label>
                  <input
                    type="password"
                    value={formData.llm.api_key}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        llm: { ...formData.llm, api_key: e.target.value },
                      })
                    }
                    placeholder="AIzaSy..."
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                  />
                  <p className="text-[10px] text-slate-500 mt-1">
                    {t.settings.apiKeyHint}
                  </p>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-slate-300 font-medium">
                      {t.settings.modelName}
                    </label>
                    <div className="flex items-center gap-1.5">
                      {availableModels.length > 0 && (
                        <span className="text-[10px] text-cyan-400 bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-800/40">
                          {availableModels.length}개 모델 검색됨
                        </span>
                      )}
                      <button
                        type="button"
                        onClick={() => fetchModels(formData.llm.api_key, formData.llm.base_url)}
                        disabled={isLoadingModels}
                        title="사용 가능한 LLM 목록 새로고침"
                        className="p-1 rounded text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition disabled:opacity-50"
                      >
                        <RefreshCw className={`w-3 h-3 ${isLoadingModels ? "animate-spin text-cyan-400" : ""}`} />
                      </button>
                    </div>
                  </div>

                  <div className="relative">
                    <input
                      type="text"
                      list="llm-model-options"
                      value={formData.llm.model}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          llm: { ...formData.llm, model: e.target.value },
                        })
                      }
                      placeholder="gemini-2.5-flash"
                      className="w-full px-3 py-2 pr-8 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                    />
                    <datalist id="llm-model-options">
                      {availableModels.map((m) => (
                        <option key={m} value={m} />
                      ))}
                    </datalist>
                    <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none text-slate-500">
                      <ChevronDown className="w-3.5 h-3.5" />
                    </div>
                  </div>

                  {/* 빠른 모델 선택 칩 */}
                  <div className="mt-1.5 flex flex-wrap gap-1 max-h-16 overflow-y-auto">
                    {availableModels.slice(0, 6).map((m) => (
                      <button
                        key={m}
                        type="button"
                        onClick={() =>
                          setFormData({
                            ...formData,
                            llm: { ...formData.llm, model: m },
                          })
                        }
                        className={`text-[10px] px-1.5 py-0.5 rounded font-mono transition border ${
                          formData.llm.model === m
                            ? "bg-cyan-950/90 text-cyan-300 border-cyan-500/60 shadow-xs"
                            : "bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200 hover:border-slate-700"
                        }`}
                      >
                        {m}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="border-t border-slate-800" />

          {/* Section 2: Cisco IOS-XE Device Configuration */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-400">
                <Server className="w-3.5 h-3.5" />
                <span>{t.settings.deviceSectionTitle}</span>
              </div>

              <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-950/70 border border-emerald-800/40 text-emerald-400 text-[11px] font-mono font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span>100% {t.common.live} SSH</span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 text-xs">
              <div className="col-span-2">
                <label className="block text-slate-300 mb-1 font-medium">
                  {t.settings.deviceHost}
                </label>
                <input
                  type="text"
                  value={formData.device.host}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      device: { ...formData.device, host: e.target.value },
                    })
                  }
                  placeholder="192.168.100.11"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">
                  {t.settings.devicePort}
                </label>
                <input
                  type="number"
                  value={formData.device.port}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      device: { ...formData.device, port: parseInt(e.target.value) || 22 },
                    })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">
                  {t.settings.deviceUser}
                </label>
                <input
                  type="text"
                  value={formData.device.username}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      device: { ...formData.device, username: e.target.value },
                    })
                  }
                  placeholder="admin"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">
                  {t.settings.devicePass}
                </label>
                <input
                  type="password"
                  value={formData.device.password || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      device: { ...formData.device, password: e.target.value },
                    })
                  }
                  placeholder="••••••••"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">
                  {t.settings.enablePass}
                </label>
                <input
                  type="password"
                  value={formData.device.enable_password || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      device: { ...formData.device, enable_password: e.target.value },
                    })
                  }
                  placeholder={t.settings.enablePassHint}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>
            </div>
          </div>

          <div className="border-t border-slate-800" />

          {/* Section 3: Debug Mode Configuration */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400">
              <Bug className="w-3.5 h-3.5" />
              <span>{t.settings.debugSectionTitle}</span>
            </div>

            <label className="flex items-start gap-3 p-3 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-amber-500/40 transition cursor-pointer select-none">
              <input
                type="checkbox"
                checked={formData.debug_mode ?? true}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    debug_mode: e.target.checked,
                  })
                }
                className="mt-1 h-4 w-4 rounded border-slate-700 bg-slate-900 text-amber-500 focus:ring-amber-500/30"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-200">
                    {t.settings.debugModeLabel}
                  </span>
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.2 rounded font-bold ${
                      formData.debug_mode ?? true
                        ? "bg-amber-950/80 text-amber-300 border border-amber-800/60"
                        : "bg-slate-800 text-slate-400 border border-slate-700"
                    }`}
                  >
                    {formData.debug_mode ?? true ? "ACTIVE (ON)" : "INACTIVE (OFF)"}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                  {t.settings.debugModeDesc}
                </p>
              </div>
            </label>
          </div>

          {/* Modal Footer */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
            >
              {t.settings.cancel}
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-600/30 transition disabled:opacity-50"
            >
              {saveSuccess ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>{t.settings.saved}</span>
                </>
              ) : (
                <span>{t.settings.saveSettings}</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
