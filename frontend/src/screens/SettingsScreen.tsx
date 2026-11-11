import React, { useState } from "react";
import {
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  Database,
  Globe,
  Lock,
  Palette,
  Shield,
  Sliders,
  Trash2,
} from "lucide-react";
import type {
  HealthResponse,
  PreviewMode,
  SettingsModel,
} from "../types/messageshield";

interface SettingsScreenProps {
  settings: SettingsModel | null;
  health: HealthResponse | null;
  historyCount: number;
  previewMode: PreviewMode;
  onChangePreviewMode: (mode: PreviewMode) => void;
  onUpdateSettings: (patch: Partial<SettingsModel>) => Promise<void>;
  onClearHistory: () => Promise<void>;
}

export const SettingsScreen: React.FC<SettingsScreenProps> = ({
  settings,
  health,
  historyCount,
  previewMode,
  onChangePreviewMode,
  onUpdateSettings,
  onClearHistory,
}) => {
  const [confirmClear, setConfirmClear] = useState(false);
  const [savedNotice, setSavedNotice] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  if (!settings) {
    return (
      <div className="space-y-3">
        <div className="h-24 animate-pulse rounded-lg bg-zinc-200/70" />
        <div className="h-36 animate-pulse rounded-lg bg-zinc-200/70" />
      </div>
    );
  }

  const applySetting = async (patch: Partial<SettingsModel>, label: string) => {
    await onUpdateSettings(patch);
    setSavedNotice(label);
    setTimeout(() => setSavedNotice(null), 2200);
  };

  return (
    <div className="space-y-3" data-testid="settings-screen">
      {savedNotice && (
        <div className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-900">
          <CheckCircle2 className="h-3.5 w-3.5 text-zinc-700" />
          <span>{savedNotice}</span>
        </div>
      )}

      {/* Appearance & Mobile Preview */}
      <section className="rounded-lg border border-zinc-200 bg-white p-3.5">
        <div className="mb-2.5 flex items-center gap-1.5">
          <Palette className="h-3.5 w-3.5 text-zinc-700" />
          <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
            Appearance
          </h2>
        </div>

        <div className="grid grid-cols-2 gap-2">
          {(
            [
              { id: "warm_light", label: "Warm Paper" },
              { id: "crisp_slate", label: "Pure White" },
            ] as const
          ).map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => applySetting({ appearance_mode: opt.id }, "Appearance updated")}
              className={`rounded-md border px-3 py-2 text-xs font-semibold transition ${
                settings.appearance_mode === opt.id
                  ? "border-zinc-900 bg-zinc-900 text-white"
                  : "border-zinc-200 bg-zinc-50 text-zinc-700 hover:bg-zinc-100"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <div className="mt-3 hidden items-center justify-between border-t border-zinc-100 pt-2.5 md:flex">
          <span className="text-xs text-zinc-700">Desktop Frame Mode</span>
          <button
            type="button"
            onClick={() =>
              onChangePreviewMode(previewMode === "phone" ? "fullscreen" : "phone")
            }
            className="rounded-md border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-[11px] font-medium text-zinc-800 hover:bg-zinc-100"
          >
            {previewMode === "phone" ? "Switch to Full Screen" : "Switch to Phone Frame"}
          </button>
        </div>
      </section>

      {/* Link Safety */}
      <section className="space-y-2 rounded-lg border border-zinc-200 bg-white p-3.5">
        <div className="flex items-center gap-1.5">
          <Globe className="h-3.5 w-3.5 text-zinc-700" />
          <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
            Link Safety
          </h2>
        </div>

        <div className="rounded-md border border-zinc-200 bg-[#FAFAF8] p-2.5 text-xs">
          <div className="flex items-center justify-between font-semibold text-zinc-800">
            <span>Safe Offline Link Checking</span>
            <span className="text-[11px] font-medium text-emerald-800">Protected</span>
          </div>
          <p className="mt-1 text-[11px] leading-snug text-zinc-600">
            Suspicious links are checked on your device and never opened automatically.
          </p>
        </div>
      </section>

      {/* Local History */}
      <section className="space-y-2.5 rounded-lg border border-zinc-200 bg-white p-3.5">
        <div className="flex items-center gap-1.5">
          <Database className="h-3.5 w-3.5 text-zinc-700" />
          <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
            Local History
          </h2>
        </div>

        <label className="flex cursor-pointer items-center justify-between rounded-md border border-zinc-200 bg-[#FAFAF8] p-2.5">
          <div>
            <div className="text-xs font-semibold text-zinc-800">
              Save Checked Messages
            </div>
            <div className="text-[10px] text-zinc-500">
              {historyCount} saved on this device
            </div>
          </div>
          <input
            type="checkbox"
            checked={settings.save_history_enabled}
            onChange={(e) =>
              applySetting(
                { save_history_enabled: e.target.checked },
                e.target.checked ? "Local history enabled" : "Local history paused"
              )
            }
            className="h-4 w-4 accent-zinc-900"
          />
        </label>

        {!confirmClear ? (
          <button
            type="button"
            disabled={historyCount === 0}
            onClick={() => setConfirmClear(true)}
            className="flex w-full items-center justify-center gap-1.5 rounded-md border border-red-200 bg-red-50/70 py-2 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-40"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Clear Saved History ({historyCount})
          </button>
        ) : (
          <div className="flex items-center justify-between rounded-md border border-red-200 bg-red-50 p-2.5 text-xs">
            <span className="font-medium text-red-900">Confirm deletion?</span>
            <div className="flex gap-1.5">
              <button
                type="button"
                onClick={async () => {
                  await onClearHistory();
                  setConfirmClear(false);
                  setSavedNotice("Local history cleared");
                }}
                className="rounded-md bg-red-700 px-2.5 py-1 text-[11px] font-semibold text-white"
              >
                Clear
              </button>
              <button
                type="button"
                onClick={() => setConfirmClear(false)}
                className="rounded-md border border-red-200 bg-white px-2.5 py-1 text-[11px] text-zinc-700"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </section>

      {/* Privacy & About */}
      <section className="space-y-2 rounded-lg border border-zinc-200 bg-white p-3.5">
        <div className="flex items-center gap-1.5">
          <Lock className="h-3.5 w-3.5 text-zinc-700" />
          <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
            Privacy & About TextVigil
          </h2>
        </div>

        <p className="text-[11px] leading-relaxed text-zinc-600">
          TextVigil v1.0 verifies messages, screenshot text, and saved history privately
          on your device without user accounts or cloud uploads.
        </p>

        <div className="flex items-start gap-2 rounded-md border border-zinc-200 bg-[#FAFAF8] p-2.5 text-[10px] leading-snug text-zinc-600">
          <Shield className="mt-0.5 h-3.5 w-3.5 shrink-0 text-zinc-700" />
          <span>
            Official India cyber fraud reporting: dial <strong>1930</strong>, visit{" "}
            <strong>cybercrime.gov.in</strong>, or report scam SMS on{" "}
            <strong>sancharsaathi.gov.in</strong>.
          </span>
        </div>
      </section>

      {/* Collapsible Advanced Classifier Controls (Hidden by Default) */}
      <section className="overflow-hidden rounded-lg border border-zinc-200 bg-white">
        <button
          type="button"
          onClick={() => setShowAdvanced((v) => !v)}
          data-testid="settings-advanced-toggle"
          aria-expanded={showAdvanced}
          className="flex w-full items-center justify-between px-3.5 py-3 text-left transition hover:bg-zinc-50"
        >
          <span className="text-xs font-medium text-zinc-700">
            Advanced Detection Settings
          </span>
          {showAdvanced ? (
            <ChevronUp className="h-4 w-4 text-zinc-500" />
          ) : (
            <ChevronDown className="h-4 w-4 text-zinc-500" />
          )}
        </button>

        {showAdvanced && (
          <div className="space-y-3 border-t border-zinc-200 bg-[#FAFAF8] p-3.5">
            <div className="flex items-center gap-1.5">
              <Cpu className="h-3.5 w-3.5 text-zinc-700" />
              <h3 className="text-[11px] font-semibold uppercase tracking-wide text-zinc-800">
                ML Classifier & Threshold
              </h3>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {(
                [
                  { id: "multinomial_nb", label: "Multinomial NB", sub: "93.4% Test F1" },
                  { id: "logistic_regression", label: "Logistic Regression", sub: "93.0% Test F1" },
                ] as const
              ).map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => applySetting({ active_model: m.id }, `Switched to ${m.label}`)}
                  data-testid={`setting-model-${m.id}`}
                  className={`rounded-md border p-2 text-left transition ${
                    settings.active_model === m.id
                      ? "border-zinc-900 bg-zinc-900 text-white"
                      : "border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-100"
                  }`}
                >
                  <div className="text-xs font-semibold">{m.label}</div>
                  <div className="text-[10px] opacity-75">{m.sub}</div>
                </button>
              ))}
            </div>

            <div>
              <div className="flex items-center justify-between text-xs">
                <span className="inline-flex items-center gap-1 font-medium text-zinc-800">
                  <Sliders className="h-3.5 w-3.5 text-zinc-500" />
                  Classification Threshold
                </span>
                <span className="font-mono-safe font-semibold text-zinc-900">
                  {Math.round(settings.classification_threshold * 100)}%
                </span>
              </div>
              <input
                type="range"
                min={0.1}
                max={0.9}
                step={0.05}
                value={settings.classification_threshold}
                onChange={(e) =>
                  applySetting(
                    { classification_threshold: parseFloat(e.target.value) },
                    "Threshold updated"
                  )
                }
                data-testid="setting-threshold-slider"
                className="mt-2 w-full accent-zinc-900"
              />
              <p className="mt-1 text-[10px] leading-snug text-zinc-500">
                Lower values catch more borderline spam (more false alarms); higher values
                require stronger confidence before flagging.
              </p>
            </div>

            {health && (
              <div className="rounded bg-white p-2 font-mono-safe text-[10px] text-zinc-600 ring-1 ring-zinc-200">
                API: {health.status} · OCR: {health.ocr_engine}
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
};
