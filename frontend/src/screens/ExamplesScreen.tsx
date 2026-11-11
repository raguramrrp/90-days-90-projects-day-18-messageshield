import React, { useState } from "react";
import { ArrowLeft, BookOpen, Send } from "lucide-react";
import { DEMO_EXAMPLES } from "../data/examples";
import { RiskBadge } from "../components/RiskBadge";

interface ExamplesScreenProps {
  onSendToScanner: (message: string, senderId?: string) => void;
  onBack: () => void;
}

export const ExamplesScreen: React.FC<ExamplesScreenProps> = ({
  onSendToScanner,
  onBack,
}) => {
  const [filter, setFilter] = useState<"all" | "scam" | "safe">("all");

  const scamCount = DEMO_EXAMPLES.filter(
    (ex) => ex.expectedCategory !== "Safe / Normal" && ex.expectedCategory !== "Promotional"
  ).length;
  const safeCount = DEMO_EXAMPLES.length - scamCount;

  const items = DEMO_EXAMPLES.filter((ex) => {
    if (filter === "scam") {
      return ex.expectedCategory !== "Safe / Normal" && ex.expectedCategory !== "Promotional";
    }
    if (filter === "safe") {
      return ex.expectedCategory === "Safe / Normal" || ex.expectedCategory === "Promotional";
    }
    return true;
  });

  return (
    <div className="space-y-3" data-testid="examples-screen">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-1 rounded-md border border-zinc-200 bg-white px-2.5 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-50"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back
        </button>
        <span className="text-[11px] text-zinc-500">Demonstration Examples</span>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white p-3 text-xs text-zinc-700">
        <div className="flex items-center gap-1.5 font-semibold text-zinc-900">
          <BookOpen className="h-3.5 w-3.5 text-zinc-700" />
          <span>Demo Message Library</span>
        </div>
        <p className="mt-1 text-[11px] leading-relaxed text-zinc-600">
          Realistic messages covering TRAI DLT alerts, UPI deep-link baits, lookalike links,
          and common Indian scam scripts.
        </p>
      </div>

      <div className="flex gap-1.5">
        {(
          [
            { id: "all", label: `All (${DEMO_EXAMPLES.length})` },
            { id: "scam", label: `Suspicious (${scamCount})` },
            { id: "safe", label: `Safe & Promo (${safeCount})` },
          ] as const
        ).map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setFilter(tab.id)}
            className={`rounded-md px-2.5 py-1 text-[11px] font-medium ${
              filter === tab.id
                ? "bg-zinc-900 text-white"
                : "border border-zinc-200 bg-white text-zinc-600 hover:bg-zinc-50"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="space-y-2.5">
        {items.map((ex) => (
          <article
            key={ex.id}
            className="rounded-lg border border-zinc-200 bg-white p-3.5"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="rounded bg-zinc-100 px-1.5 py-0.5 font-mono-safe text-[10px] font-medium text-zinc-600">
                    {ex.senderTag}
                  </span>
                  <span className="text-[10px] text-zinc-400">DEMO</span>
                </div>
                <h3 className="mt-1 text-xs font-semibold text-zinc-900">
                  {ex.title}
                </h3>
              </div>
              <RiskBadge
                risk={ex.expectedRisk}
                category={ex.expectedCategory}
                compact
              />
            </div>

            <div className="mt-2 rounded-md border border-zinc-100 bg-[#FAFAF8] p-2.5 text-xs leading-relaxed text-zinc-800">
              {ex.message}
            </div>

            <p className="mt-2 text-[11px] leading-snug text-zinc-600">
              <span className="font-semibold text-zinc-800">Expected ({ex.expectedCategory}):</span>{" "}
              {ex.explanation}
            </p>

            <button
              type="button"
              onClick={() => onSendToScanner(ex.message, ex.senderTag)}
              data-testid={`example-send-${ex.id}`}
              className="mt-2.5 flex w-full items-center justify-center gap-1.5 rounded-md border border-zinc-300 bg-zinc-50 py-1.5 text-xs font-semibold text-zinc-900 hover:bg-zinc-100"
            >
              <Send className="h-3.5 w-3.5" />
              Send to Scanner
            </button>
          </article>
        ))}
      </div>
    </div>
  );
};
