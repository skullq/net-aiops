"use client";

import React, { useState } from "react";
import {
  X,
  Server,
  Plus,
  Trash2,
  Edit2,
  Check,
  Info,
} from "lucide-react";
import { ManagedDevice } from "@/types";
import { useI18n } from "@/i18n";

interface DeviceManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  devices: ManagedDevice[];
  onAddDevice: (device: ManagedDevice) => Promise<void>;
  onUpdateDevice: (deviceId: string, data: Partial<ManagedDevice>) => Promise<void>;
  onDeleteDevice: (deviceId: string) => Promise<void>;
}

export const DeviceManagerModal: React.FC<DeviceManagerModalProps> = ({
  isOpen,
  onClose,
  devices,
  onAddDevice,
  onUpdateDevice,
  onDeleteDevice,
}) => {
  const { t } = useI18n();
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingDeviceId, setEditingDeviceId] = useState<string | null>(null);

  // New device form state
  const [newDevice, setNewDevice] = useState<Partial<ManagedDevice>>({
    name: "",
    host: "",
    port: 22,
    username: "",
    password: "",
    enable_password: "",
    description: "",
  });

  // Edit device form state
  const [editForm, setEditForm] = useState<Partial<ManagedDevice>>({});

  if (!isOpen) return null;

  const startEdit = (dev: ManagedDevice) => {
    setEditingDeviceId(dev.id);
    setEditForm({
      name: dev.name,
      host: dev.host,
      port: dev.port || 22,
      username: dev.username || "",
      password: dev.password || "",
      enable_password: dev.enable_password || "",
      description: dev.description || "",
    });
  };

  const handleEditSubmit = async (e: React.FormEvent, deviceId: string) => {
    e.preventDefault();
    await onUpdateDevice(deviceId, editForm);
    setEditingDeviceId(null);
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDevice.name || !newDevice.host) return;

    const id = newDevice.name.trim().toLowerCase().replace(/\s+/g, "_");
    await onAddDevice({
      id,
      name: newDevice.name.trim(),
      host: newDevice.host.trim(),
      port: newDevice.port ? Number(newDevice.port) : 22,
      username: newDevice.username?.trim() || "admin",
      password: newDevice.password || "admin",
      enable_password: newDevice.enable_password || "admin",
      description: newDevice.description?.trim() || "",
    });

    setNewDevice({
      name: "",
      host: "",
      port: 22,
      username: "",
      password: "",
      enable_password: "",
      description: "",
    });
    setShowAddForm(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150 select-none">
      <div className="w-full max-w-lg rounded-xl shadow-2xl overflow-hidden border border-slate-700 bg-slate-900 flex flex-col max-h-[82vh]">
        {/* Compact Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-950 shrink-0">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-100">
              {t.deviceManager.modalTitle} ({devices.length}{t.deviceManager.registeredCount})
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Compact Body */}
        <div className="p-4 space-y-3 overflow-y-auto flex-1 text-xs">
          {/* Default priority guide note */}
          <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-300 flex items-start gap-2">
            <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-cyan-400" />
            <span>{t.deviceManager.guideBanner}</span>
          </div>

          {/* Add Device Button / Toggle */}
          <div className="flex justify-between items-center pt-0.5">
            <span className="text-[11px] font-medium text-slate-400">
              {t.deviceManager.inventoryTitle}
            </span>
            <button
              onClick={() => {
                setShowAddForm(!showAddForm);
                setEditingDeviceId(null);
              }}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-[11px] font-medium transition shadow-sm"
            >
              <Plus className="w-3 h-3" />
              <span>{showAddForm ? t.deviceManager.closeForm : t.deviceManager.addDevice}</span>
            </button>
          </div>

          {/* Add Device Form */}
          {showAddForm && (
            <form
              onSubmit={handleAddSubmit}
              className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2.5 animate-in fade-in zoom-in-98 text-xs"
            >
              <div className="font-semibold text-slate-200 text-xs pb-1 border-b border-slate-800">
                {t.deviceManager.newDeviceTitle}
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-400 mb-0.5 text-[11px]">
                    {t.deviceManager.deviceName}
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="r6"
                    value={newDevice.name || ""}
                    onChange={(e) => setNewDevice({ ...newDevice, name: e.target.value })}
                    className="w-full px-2.5 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-0.5 text-[11px]">
                    {t.deviceManager.deviceHost}
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="192.168.100.16"
                    value={newDevice.host || ""}
                    onChange={(e) => setNewDevice({ ...newDevice, host: e.target.value })}
                    className="w-full px-2.5 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-0.5 text-[11px]">
                    {t.deviceManager.username} ({t.deviceManager.usernameHint})
                  </label>
                  <input
                    type="text"
                    placeholder="admin"
                    value={newDevice.username || ""}
                    onChange={(e) => setNewDevice({ ...newDevice, username: e.target.value })}
                    className="w-full px-2.5 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-0.5 text-[11px]">
                    {t.deviceManager.password} ({t.deviceManager.passwordHint})
                  </label>
                  <input
                    type="password"
                    placeholder="admin"
                    value={newDevice.password || ""}
                    onChange={(e) => setNewDevice({ ...newDevice, password: e.target.value })}
                    className="w-full px-2.5 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-1">
                <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                  <span>100% {t.common.live} SSH</span>
                </span>

                <div className="flex gap-1.5">
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
                    className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    {t.deviceManager.cancel}
                  </button>
                  <button
                    type="submit"
                    className="px-3 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium"
                  >
                    {t.deviceManager.register}
                  </button>
                </div>
              </div>
            </form>
          )}

          {/* Device Cards List */}
          <div className="space-y-2">
            {devices.map((device) => {
              const isEditing = editingDeviceId === device.id;

              if (isEditing) {
                return (
                  <form
                    key={device.id}
                    onSubmit={(e) => handleEditSubmit(e, device.id)}
                    className="p-3 rounded-lg bg-slate-950 border border-cyan-600/60 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between border-b border-slate-800 pb-1">
                      <span className="font-semibold text-cyan-400">
                        {t.deviceManager.editDeviceTitle} ({device.name})
                      </span>
                      <button
                        type="button"
                        onClick={() => setEditingDeviceId(null)}
                        className="text-slate-400 hover:text-white"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[11px]">
                      <div>
                        <label className="block text-slate-400 mb-0.5">
                          {t.deviceManager.deviceName}
                        </label>
                        <input
                          type="text"
                          required
                          value={editForm.name || ""}
                          onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                          className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-100 font-mono"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-400 mb-0.5">
                          {t.deviceManager.deviceHost}
                        </label>
                        <input
                          type="text"
                          required
                          value={editForm.host || ""}
                          onChange={(e) => setEditForm({ ...editForm, host: e.target.value })}
                          className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-100 font-mono"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-400 mb-0.5">
                          {t.deviceManager.username}
                        </label>
                        <input
                          type="text"
                          value={editForm.username || ""}
                          onChange={(e) => setEditForm({ ...editForm, username: e.target.value })}
                          className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-100 font-mono"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-400 mb-0.5">
                          {t.deviceManager.password}
                        </label>
                        <input
                          type="password"
                          value={editForm.password || ""}
                          onChange={(e) => setEditForm({ ...editForm, password: e.target.value })}
                          className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-100 font-mono"
                        />
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                        <span>100% {t.common.live} SSH</span>
                      </span>

                      <div className="flex gap-1.5">
                        <button
                          type="button"
                          onClick={() => setEditingDeviceId(null)}
                          className="px-2.5 py-1 rounded bg-slate-800 text-slate-300"
                        >
                          {t.deviceManager.cancel}
                        </button>
                        <button
                          type="submit"
                          className="px-3 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium flex items-center gap-1"
                        >
                          <Check className="w-3 h-3" />
                          <span>{t.deviceManager.save}</span>
                        </button>
                      </div>
                    </div>
                  </form>
                );
              }

              return (
                <div
                  key={device.id}
                  className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 transition flex items-center justify-between gap-2"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-100 text-xs">
                        {device.name}
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">
                        {device.host}:{device.port || 22}
                      </span>
                      <span className="text-[9px] px-1.5 py-0.2 rounded font-mono font-medium bg-emerald-950/70 text-emerald-400 border border-emerald-800/40">
                        {t.deviceManager.liveBadge}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono">
                      {t.deviceManager.userLabel}: {device.username || "admin"}
                      {device.description && ` • ${device.description}`}
                    </div>
                  </div>

                  {/* Actions: Edit & Delete */}
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      onClick={() => startEdit(device)}
                      title={t.deviceManager.editTooltip}
                      className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => onDeleteDevice(device.id)}
                      title={t.deviceManager.deleteTooltip}
                      className="p-1 rounded bg-slate-800 hover:bg-rose-950 text-slate-400 hover:text-rose-400 transition"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Compact Footer */}
        <div className="px-4 py-2.5 border-t border-slate-800 bg-slate-950 flex justify-end">
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition"
          >
            {t.deviceManager.close}
          </button>
        </div>
      </div>
    </div>
  );
};
