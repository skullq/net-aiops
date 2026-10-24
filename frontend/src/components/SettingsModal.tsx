"use client";

import React, { useState, useEffect } from "react";
import { X, Server, Sparkles, Key, Check, Info } from "lucide-react";
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
      mock_mode: false,
    },
  });

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (config) {
      setFormData(config);
    }
  }, [config, isOpen]);

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
                  <label className="block text-slate-300 mb-1 font-medium">
                    {t.settings.modelName}
                  </label>
                  <input
                    type="text"
                    value={formData.llm.model}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        llm: { ...formData.llm, model: e.target.value },
                      })
                    }
                    placeholder="gemini-2.5-flash"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                  />
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

              {/* Mock Mode Toggle */}
              <label className="relative inline-flex items-center cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={formData.device.mock_mode}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      device: { ...formData.device, mock_mode: e.target.checked },
                    })
                  }
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-600"></div>
                <span className="ml-2 text-xs font-medium text-slate-300">
                  {formData.device.mock_mode ? `${t.common.mock} ON` : `${t.common.live} SSH`}
                </span>
              </label>
            </div>

            {formData.device.mock_mode && (
              <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-800/40 text-amber-300/90 text-[11px] flex items-start gap-2">
                <Info className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" />
                <span>{t.settings.mockModeDesc}</span>
              </div>
            )}

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
