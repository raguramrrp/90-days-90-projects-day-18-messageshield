import React, { useState } from "react";
import { Clock, Lock, Search, Trash2 } from "lucide-react";
import { RiskBadge } from "../components/RiskBadge";
import type { HistoryListResponse, HistoryRecord } from "../types/messageshield";

interface HistoryScreenProps {
  history: HistoryListResponse | null;
  search: string;
  categoryFilter: string;
  onChangeSearch: (value: string) => void;
  onChangeCategory: (category: string) => void;
  onSelectRecord: (record: HistoryRecord) => void;
  onDeleteRecord: (id: number) => Promise<void>;
  onClearAll: () => Promise<void>;
  onGoToScan: () => void;
}

const FILTER_CATEGORIES = [
  "All",
  "Flagged",
  "Safe / Normal",
  "Promotional",
  "Phishing",
  "Financial Scam",
  "OTP / Credential Theft",
  "Impersonation",
  "Fake Reward",
];

export const HistoryScreen: React.FC<HistoryScreenProps> = ({
  history,
  search,
  categoryFilter,
  onChangeSearch,
  onChangeCategory,
  onSelectRecord,
  onDeleteRecord,
  onClearAll,
  onGoToScan,
}) => {
  const [confirmClear, setConfirmClear] = useState(false);

  const records = history?.records ?? [];
  const totalCount = history?.total_count ?? 0;

  return (
    <div className="space-y-3" data-testid="history-screen">
      <div className="flex items-start gap-2 rounded-lg border border-zinc-200 bg-white p-3 text-[11px] text-zinc-600">
        <Lock className="mt-0.5 h-3.5 w-3.5 shrink-0 text-zinc-500" />
        <span>
          Saved privately on this device. Messages never leave your phone or computer.
        </span>
      </div>

      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-3.5 w-3.5 text-zinc-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => onChangeSearch(e.target.value)}
            placeholder="Search saved messages or categories..."
            data-testid="history-search-input"
            className="w-full rounded-lg border border-zinc-200 bg-white py-2 pl-8 pr-3 text-xs text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none"
          />
        </div>

        {totalCount > 0 && !confirmClear && (
          <button
            type="button"
            onClick={() => setConfirmClear(true)}
            data-testid="history-clear-all-btn"
            className="shrink-0 rounded-lg border border-zinc-200 bg-white px-2.5 py-2 text-[11px] font-semibold text-red-700 hover:bg-red-50"
          >
            Clear All
          </button>
        )}
      </div>

      {confirmClear && (
        <div className="flex items-center justify-between gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs">
          <span className="font-medium text-red-900">
            Delete all {totalCount} local records?
          </span>
          <div className="flex gap-1.5">
            <button
              type="button"
              onClick={async () => {
                await onClearAll();
                setConfirmClear(false);
              }}
              data-testid="history-confirm-clear-btn"
              className="rounded-md bg-red-700 px-2.5 py-1 text-[11px] font-semibold text-white"
            >
              Delete
            </button>
            <button
              type="button"
              onClick={() => setConfirmClear(false)}
              className="rounded-md border border-red-200 bg-white px-2.5 py-1 text-[11px] font-medium text-zinc-700"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="mobile-scroll flex gap-1.5 overflow-x-auto pb-1">
        {FILTER_CATEGORIES.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => onChangeCategory(cat)}
            className={`shrink-0 rounded-md px-2.5 py-1 text-[11px] font-medium transition ${
              categoryFilter === cat
                ? "bg-zinc-900 text-white"
                : "border border-zinc-200 bg-white text-zinc-600 hover:bg-zinc-50"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {records.length === 0 ? (
        <div className="rounded-lg border border-dashed border-zinc-300 bg-white p-6 text-center">
          <Clock className="mx-auto h-6 w-6 text-zinc-400" />
          <h3 className="mt-2 text-xs font-semibold text-zinc-800">
            {totalCount === 0 ? "No local scans saved" : "No matching records"}
          </h3>
          <p className="mt-1 text-[11px] text-zinc-500">
            {totalCount === 0
              ? "Messages you inspect are saved here privately for quick reference."
              : "Try clearing your search or switching the category filter."}
          </p>
          {totalCount === 0 && (
            <button
              type="button"
              onClick={onGoToScan}
              className="mt-3 rounded-lg bg-zinc-900 px-4 py-2 text-xs font-semibold text-white"
            >
              Scan First Message
            </button>
          )}
        </div>
      ) : (
        <div className="divide-y divide-zinc-200 overflow-hidden rounded-lg border border-zinc-200 bg-white">
          {records.map((rec) => (
            <div key={rec.id} className="p-3">
              <div className="flex items-start justify-between gap-2">
                <button
                  type="button"
                  onClick={() => onSelectRecord(rec)}
                  className="min-w-0 flex-1 text-left"
                >
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-xs font-semibold text-zinc-900">
                      {rec.threat_category}
                    </span>
                    <RiskBadge risk={rec.risk_level} category={rec.threat_category} compact />
                  </div>
                  <p className="mt-1 line-clamp-2 text-xs leading-snug text-zinc-700">
                    {rec.message}
                  </p>
                  <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[10px] text-zinc-400">
                    <span>{new Date(rec.timestamp).toLocaleString()}</span>
                    {rec.url_indicators.length > 0 && (
                      <span>· {rec.url_indicators.length} URL(s)</span>
                    )}
                    {rec.warning_signs.length > 0 && (
                      <span>· {rec.warning_signs[0]}</span>
                    )}
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => onDeleteRecord(rec.id)}
                  aria-label="Delete record"
                  title="Delete record"
                  className="rounded-md p-1.5 text-zinc-400 hover:bg-red-50 hover:text-red-700"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
