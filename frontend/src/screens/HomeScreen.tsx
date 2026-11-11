import React, { useState } from "react";
import {
  BookOpen,
  ChevronRight,
  ClipboardPaste,
  FileSpreadsheet,
  ImageUp,
  ScanSearch,
} from "lucide-react";
import textvigilLogo from "../assets/textvigil-logo.png";
import { DEMO_EXAMPLES, SAFETY_TIPS } from "../data/examples";
import { RiskBadge } from "../components/RiskBadge";
import type {
  HistoryListResponse,
  HistoryRecord,
  NavTab,
  ScanSubMode,
} from "../types/messageshield";

interface HomeScreenProps {
  history: HistoryListResponse | null;
  onStartScan: (mode: ScanSubMode, autoPaste?: boolean) => void;
  onOpenExamples: () => void;
  onOpenHistoryRecord: (record: HistoryRecord) => void;
  onNavigateTab: (tab: NavTab) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  history,
  onStartScan,
  onOpenExamples,
  onOpenHistoryRecord,
  onNavigateTab,
}) => {
  const [tipIndex, setTipIndex] = useState(0);
  const currentTip = SAFETY_TIPS[tipIndex];
  const recentItems = history?.records.slice(0, 3) ?? [];

  return (
    <div className="space-y-4">
      {/* Simple, Direct Editorial Welcome & Primary Action */}
      <section className="rounded-lg border border-zinc-200 bg-white p-4">
        <div className="flex items-center gap-3">
          <img
            src={textvigilLogo}
            alt="TextVigil app emblem"
            className="h-10 w-10 shrink-0 rounded-lg"
          />
          <div>
            <h1 className="text-base font-bold tracking-tight text-zinc-900">
              TextVigil
            </h1>
            <p className="text-xs text-zinc-500">
              Personal SMS & Link Verification
            </p>
          </div>
        </div>

        <p className="mt-3 text-[13px] leading-relaxed text-zinc-700">
          Check suspicious SMS alerts, UPI payment traps, courier fees, and links before
          you tap or reply.
        </p>

        <button
          type="button"
          onClick={() => onStartScan("paste")}
          data-testid="home-scan-cta"
          className="mt-3.5 flex w-full items-center justify-center gap-2 rounded-lg bg-zinc-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-zinc-800 active:scale-[0.99]"
        >
          <ScanSearch className="h-4 w-4" />
          Scan Message
        </button>
      </section>

      {/* Clean Mobile List-Style Quick Actions */}
      <section className="divide-y divide-zinc-200 overflow-hidden rounded-lg border border-zinc-200 bg-white">
        <button
          type="button"
          onClick={() => onStartScan("paste", true)}
          data-testid="home-paste-action"
          className="flex w-full items-center justify-between gap-3 px-3.5 py-3 text-left transition hover:bg-zinc-50"
        >
          <div className="flex items-center gap-3">
            <ClipboardPaste className="h-4 w-4 shrink-0 text-zinc-700" />
            <div>
              <div className="text-xs font-semibold text-zinc-900">Paste Message</div>
              <div className="text-[11px] text-zinc-500">
                Inspect copied SMS or WhatsApp text
              </div>
            </div>
          </div>
          <ChevronRight className="h-4 w-4 shrink-0 text-zinc-400" />
        </button>

        <button
          type="button"
          onClick={() => onStartScan("screenshot")}
          data-testid="home-screenshot-action"
          className="flex w-full items-center justify-between gap-3 px-3.5 py-3 text-left transition hover:bg-zinc-50"
        >
          <div className="flex items-center gap-3">
            <ImageUp className="h-4 w-4 shrink-0 text-zinc-700" />
            <div>
              <div className="text-xs font-semibold text-zinc-900">Scan Screenshot</div>
              <div className="text-[11px] text-zinc-500">
                Read SMS text or inspect QR screenshots
              </div>
            </div>
          </div>
          <ChevronRight className="h-4 w-4 shrink-0 text-zinc-400" />
        </button>

        <button
          type="button"
          onClick={onOpenExamples}
          data-testid="home-examples-action"
          className="flex w-full items-center justify-between gap-3 px-3.5 py-2.5 text-left transition hover:bg-zinc-50"
        >
          <div className="flex items-center gap-3">
            <BookOpen className="h-4 w-4 shrink-0 text-zinc-700" />
            <div>
              <div className="text-xs font-semibold text-zinc-900">Sample Library</div>
              <div className="text-[11px] text-zinc-500">
                {DEMO_EXAMPLES.length} realistic safe & scam examples
              </div>
            </div>
          </div>
          <ChevronRight className="h-4 w-4 shrink-0 text-zinc-400" />
        </button>

        <button
          type="button"
          onClick={() => onStartScan("batch")}
          data-testid="home-batch-action"
          className="flex w-full items-center justify-between gap-3 px-3.5 py-2.5 text-left transition hover:bg-zinc-50"
        >
          <div className="flex items-center gap-3">
            <FileSpreadsheet className="h-4 w-4 shrink-0 text-zinc-700" />
            <div>
              <div className="text-xs font-semibold text-zinc-900">Batch CSV Scan</div>
              <div className="text-[11px] text-zinc-500">
                Check multiple exported messages together
              </div>
            </div>
          </div>
          <ChevronRight className="h-4 w-4 shrink-0 text-zinc-400" />
        </button>
      </section>

      {/* Recent Checks */}
      <section className="rounded-lg border border-zinc-200 bg-white p-3.5">
        <div className="flex items-center justify-between gap-2">
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-700">
              Recent Checks
            </h2>
            {history && history.total_count > 0 && (
              <p className="text-[11px] text-zinc-500">
                {history.total_count} saved locally · {history.flagged_count} flagged
              </p>
            )}
          </div>
          {history && history.total_count > 0 && (
            <button
              type="button"
              onClick={() => onNavigateTab("history")}
              className="text-xs font-medium text-zinc-700 underline decoration-zinc-300 underline-offset-2 hover:text-zinc-900"
            >
              View all
            </button>
          )}
        </div>

        {recentItems.length === 0 ? (
          <p className="mt-2 text-xs text-zinc-500">
            No messages scanned yet. Your recent local checks will appear here.
          </p>
        ) : (
          <div className="mt-2.5 divide-y divide-zinc-100 border-t border-zinc-100">
            {recentItems.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => onOpenHistoryRecord(item)}
                className="flex w-full items-start justify-between gap-2 py-2.5 text-left transition hover:bg-zinc-50"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span className="truncate text-xs font-semibold text-zinc-900">
                      {item.threat_category}
                    </span>
                    <RiskBadge risk={item.risk_level} category={item.threat_category} compact />
                  </div>
                  <p className="mt-1 line-clamp-2 text-[11px] leading-snug text-zinc-600">
                    {item.message}
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </section>

      {/* Concise Safety Note */}
      <section className="rounded-lg border border-zinc-200 border-l-4 border-l-amber-600 bg-white p-3.5">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-semibold text-zinc-900">
            Safety Tip: {currentTip.title}
          </span>
          <button
            type="button"
            onClick={() => setTipIndex((i) => (i + 1) % SAFETY_TIPS.length)}
            className="text-[11px] font-medium text-zinc-600 underline decoration-zinc-300 underline-offset-2 hover:text-zinc-900"
          >
            Next tip
          </button>
        </div>
        <p className="mt-1 text-xs leading-relaxed text-zinc-600">
          {currentTip.body}
        </p>
      </section>
    </div>
  );
};
