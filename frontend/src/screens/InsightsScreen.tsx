import React, { useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Info,
  ShieldCheck,
  Sliders,
} from "lucide-react";
import { ConfusionMatrix } from "../components/ConfusionMatrix";
import type { ModelInsightsResponse } from "../types/messageshield";

interface InsightsScreenProps {
  insights: ModelInsightsResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

const CHECKED_PATTERNS = [
  {
    title: "QR Codes & UPI Pay Deep-Links",
    desc: "Decodes screenshot QR codes locally and warns when a cashback lure tries to initiate an outgoing payment.",
  },
  {
    title: "TRAI Sender Headers & Disguised Links",
    desc: "Checks Indian DLT sender headers, flags 10-digit mobile impersonation, and catches invisible or lookalike spoof characters.",
  },
  {
    title: "Fake KYC & Bank Block Alerts",
    desc: "Flags urgent warnings claiming your bank account, PAN, or SIM will be suspended within hours.",
  },
  {
    title: "Suspicious & Lookalike Links",
    desc: "Checks shortened URLs, raw IP links, and lookalike domains locally without ever opening them.",
  },
  {
    title: "Courier, Utility & Job Fees",
    desc: "Spots fake customs charges, electricity disconnection threats, and upfront job registration fees.",
  },
];

export const InsightsScreen: React.FC<InsightsScreenProps> = ({
  insights,
  loading,
  error,
  onRetry,
}) => {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [selectedModelKey, setSelectedModelKey] = useState<
    "logistic_regression" | "multinomial_nb"
  >("multinomial_nb");
  const [explorerThreshold, setExplorerThreshold] = useState<number>(0.5);

  const availableKeys = useMemo(
    () => (insights ? Object.keys(insights.models) : []),
    [insights]
  );

  if (loading) {
    return (
      <div className="space-y-3">
        <div className="h-24 animate-pulse rounded-lg bg-zinc-200/70" />
        <div className="h-40 animate-pulse rounded-lg bg-zinc-200/70" />
        <div className="h-28 animate-pulse rounded-lg bg-zinc-200/70" />
      </div>
    );
  }

  if (error || !insights) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center">
        <AlertCircle className="mx-auto h-6 w-6 text-red-600" />
        <p className="mt-2 text-xs font-semibold text-red-900">
          {error || "Could not load protection overview."}
        </p>
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-lg bg-zinc-900 px-4 py-1.5 text-xs font-semibold text-white"
        >
          Retry
        </button>
      </div>
    );
  }

  const effectiveKey = availableKeys.includes(selectedModelKey)
    ? selectedModelKey
    : (insights.selected_model as "logistic_regression" | "multinomial_nb");
  const activeMetrics = insights.models[effectiveKey];
  const defaultKey = (
    availableKeys.includes(insights.selected_model)
      ? insights.selected_model
      : effectiveKey
  ) as "logistic_regression" | "multinomial_nb";
  const defaultMetrics = insights.models[defaultKey];

  const ds = insights.dataset;
  const hamPct = Math.round((ds.ham_count / ds.clean_rows) * 100);
  const spamPct = 100 - hamPct;
  const normalTestedCount =
    defaultMetrics.confusion_matrix.tn + defaultMetrics.confusion_matrix.fp;

  const curve = activeMetrics.threshold_curve;
  const thresholdPoint =
    curve.reduce((prev, curr) =>
      Math.abs(curr.threshold - explorerThreshold) <
      Math.abs(prev.threshold - explorerThreshold)
        ? curr
        : prev
    ) ?? curve[0];

  const lr = insights.models["logistic_regression"];
  const nb = insights.models["multinomial_nb"];

  return (
    <div className="space-y-3" data-testid="insights-screen">
      {/* Everyday Plain-English Protection Summary */}
      <section className="rounded-lg border border-zinc-200 bg-white p-3.5">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="h-4 w-4 text-zinc-800" />
          <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
            How TextVigil Protects You
          </h2>
        </div>

        <p className="mt-1.5 text-xs leading-relaxed text-zinc-600">
          Every message is checked locally on your device using a combination of trained
          spam filtering, India-specific scam rules, and offline link inspection.
        </p>

        <div className="mt-3 grid grid-cols-3 gap-2 text-center">
          <div className="rounded-md border border-zinc-200 bg-[#FAFAF8] p-2">
            <div className="font-mono-safe text-sm font-bold text-zinc-900">
              {(defaultMetrics.accuracy * 100).toFixed(1)}%
            </div>
            <div className="mt-0.5 text-[10px] leading-tight text-zinc-500">
              Test Accuracy
            </div>
          </div>
          <div className="rounded-md border border-zinc-200 bg-[#FAFAF8] p-2">
            <div className="font-mono-safe text-sm font-bold text-zinc-900">
              {defaultMetrics.confusion_matrix.fp} / {normalTestedCount}
            </div>
            <div className="mt-0.5 text-[10px] leading-tight text-zinc-500">
              False Alarms
            </div>
          </div>
          <div className="rounded-md border border-zinc-200 bg-[#FAFAF8] p-2">
            <div className="font-mono-safe text-sm font-bold text-zinc-900">
              100%
            </div>
            <div className="mt-0.5 text-[10px] leading-tight text-zinc-500">
              On-Device
            </div>
          </div>
        </div>
      </section>

      {/* What We Check For (Consumer-Friendly Checklist) */}
      <section className="rounded-lg border border-zinc-200 bg-white p-3.5">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
          What Messages Are Checked For
        </h2>

        <div className="mt-2.5 divide-y divide-zinc-100">
          {CHECKED_PATTERNS.map((item) => (
            <div key={item.title} className="py-2 first:pt-0 last:pb-0">
              <div className="text-xs font-semibold text-zinc-900">{item.title}</div>
              <p className="mt-0.5 text-[11px] leading-snug text-zinc-600">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Honest Scope Note */}
      <section className="flex items-start gap-2 rounded-lg border border-zinc-200 bg-white p-3 text-[11px] text-zinc-600">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-zinc-500" />
        <span>
          Scam templates change often. If a message still feels suspicious, confirm directly inside
          your official bank or utility app before taking action.
        </span>
      </section>

      {/* Collapsible Technical / Developer Details (Hidden by Default) */}
      <section className="overflow-hidden rounded-lg border border-zinc-200 bg-white">
        <button
          type="button"
          onClick={() => setShowTechnicalDetails((v) => !v)}
          data-testid="insights-technical-toggle"
          aria-expanded={showTechnicalDetails}
          className="flex w-full items-center justify-between px-3.5 py-3 text-left transition hover:bg-zinc-50"
        >
          <div>
            <div className="text-xs font-semibold text-zinc-800">
              Technical Model Details
            </div>
            <div className="text-[11px] text-zinc-500">
              Evaluation metrics, threshold curve & feature weights
            </div>
          </div>
          {showTechnicalDetails ? (
            <ChevronUp className="h-4 w-4 shrink-0 text-zinc-500" />
          ) : (
            <ChevronDown className="h-4 w-4 shrink-0 text-zinc-500" />
          )}
        </button>

        {showTechnicalDetails && (
          <div className="space-y-3 border-t border-zinc-200 bg-[#FAFAF8] p-3">
            {/* Dataset Summary */}
            <div className="rounded-md border border-zinc-200 bg-white p-3">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-[11px] font-semibold uppercase tracking-wide text-zinc-800">
                  Evaluation Dataset
                </h3>
                <span className="font-mono-safe text-[10px] text-zinc-500">
                  n = {ds.clean_rows} unique
                </span>
              </div>
              <p className="mt-1 text-xs font-medium text-zinc-900">{ds.name}</p>
              <p className="mt-0.5 text-[11px] text-zinc-500">
                {ds.raw_rows} raw rows · {ds.duplicate_rows_removed} duplicates removed ·{" "}
                {ds.train_rows} train / {ds.test_rows} test
              </p>

              <div className="mt-2 space-y-1">
                <div className="flex justify-between text-[11px] font-medium text-zinc-700">
                  <span>Ham: {ds.ham_count} ({hamPct}%)</span>
                  <span>Spam: {ds.spam_count} ({spamPct}%)</span>
                </div>
                <div className="flex h-2 w-full overflow-hidden rounded-full bg-zinc-200">
                  <div className="bg-zinc-800" style={{ width: `${hamPct}%` }} />
                  <div className="bg-amber-500" style={{ width: `${spamPct}%` }} />
                </div>
              </div>
            </div>

            {/* Model Comparison */}
            <div className="rounded-md border border-zinc-200 bg-white p-3">
              <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-zinc-800">
                Classifier Comparison (Test Set)
              </h3>
              <div className="overflow-hidden rounded border border-zinc-200">
                <table className="w-full text-left text-[11px]">
                  <thead className="bg-zinc-100 text-zinc-600">
                    <tr>
                      <th className="px-2 py-1 font-semibold">Metric</th>
                      <th className="px-2 py-1 font-semibold">LogReg</th>
                      <th className="px-2 py-1 font-semibold">Naive Bayes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-100 bg-white font-mono-safe">
                    {[
                      { label: "Accuracy", key: "accuracy" as const },
                      { label: "Precision", key: "precision" as const },
                      { label: "Recall", key: "recall" as const },
                      { label: "F1-Score", key: "f1_score" as const },
                      { label: "ROC-AUC", key: "roc_auc" as const },
                    ].map((row) => (
                      <tr key={row.key}>
                        <td className="px-2 py-1 font-sans font-medium text-zinc-700">
                          {row.label}
                        </td>
                        <td className="px-2 py-1 text-zinc-900">
                          {(lr[row.key] * 100).toFixed(2)}%
                        </td>
                        <td className="px-2 py-1 text-zinc-900">
                          {(nb[row.key] * 100).toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-2 flex items-start gap-1.5 rounded border border-zinc-200 bg-zinc-50 p-2 text-[11px] text-zinc-700">
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-zinc-700" />
                <span>{insights.selection_rationale}</span>
              </div>
            </div>

            {/* Model Switcher */}
            <div className="grid grid-cols-2 rounded-md border border-zinc-200 bg-zinc-100 p-0.5">
              {(
                [
                  { id: "multinomial_nb", label: "Multinomial NB" },
                  { id: "logistic_regression", label: "Logistic Regression" },
                ] as const
              ).map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setSelectedModelKey(m.id)}
                  data-testid={`insights-model-${m.id}`}
                  className={`rounded py-1.5 text-xs font-medium transition ${
                    effectiveKey === m.id
                      ? "bg-white font-semibold text-zinc-900 shadow-2xs"
                      : "text-zinc-600 hover:text-zinc-900"
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>

            {/* Threshold Explorer */}
            <div className="rounded-md border border-zinc-200 bg-white p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Sliders className="h-3.5 w-3.5 text-zinc-700" />
                  <h3 className="text-[11px] font-semibold uppercase tracking-wide text-zinc-800">
                    Threshold Explorer
                  </h3>
                </div>
                <span className="rounded bg-zinc-900 px-2 py-0.5 font-mono-safe text-[11px] font-semibold text-white">
                  {Math.round(thresholdPoint.threshold * 100)}%
                </span>
              </div>

              <input
                type="range"
                min={0.1}
                max={0.9}
                step={0.05}
                value={explorerThreshold}
                onChange={(e) => setExplorerThreshold(parseFloat(e.target.value))}
                aria-label="Explore classification threshold"
                data-testid="insights-threshold-slider"
                className="mt-2.5 w-full accent-zinc-900"
              />

              <div className="mt-2 grid grid-cols-3 gap-1.5 text-center">
                <div className="rounded bg-zinc-50 p-1.5">
                  <div className="font-mono-safe text-xs font-bold text-zinc-900">
                    {(thresholdPoint.precision * 100).toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-zinc-500">Precision</div>
                </div>
                <div className="rounded bg-zinc-50 p-1.5">
                  <div className="font-mono-safe text-xs font-bold text-zinc-900">
                    {(thresholdPoint.recall * 100).toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-zinc-500">Recall</div>
                </div>
                <div className="rounded bg-zinc-50 p-1.5">
                  <div className="font-mono-safe text-xs font-bold text-zinc-900">
                    {(thresholdPoint.f1_score * 100).toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-zinc-500">F1-Score</div>
                </div>
              </div>

              <div className="mt-1.5 grid grid-cols-2 gap-1.5 text-center text-[11px]">
                <div className="rounded border border-amber-200 bg-amber-50/70 py-1 text-amber-900">
                  FP: <span className="font-mono-safe font-bold">{thresholdPoint.false_positives}</span>
                </div>
                <div className="rounded border border-orange-200 bg-orange-50/70 py-1 text-orange-900">
                  FN: <span className="font-mono-safe font-bold">{thresholdPoint.false_negatives}</span>
                </div>
              </div>
            </div>

            {/* Confusion Matrix */}
            <div className="rounded-md border border-zinc-200 bg-white p-3">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-[11px] font-semibold uppercase tracking-wide text-zinc-800">
                  Confusion Matrix (at 50%)
                </h3>
                <span className="text-[10px] text-zinc-500">
                  Vocab: {activeMetrics.vocabulary_size.toLocaleString()} n-grams
                </span>
              </div>
              <ConfusionMatrix
                tn={activeMetrics.confusion_matrix.tn}
                fp={activeMetrics.confusion_matrix.fp}
                fn={activeMetrics.confusion_matrix.fn}
                tp={activeMetrics.confusion_matrix.tp}
              />
            </div>

            {/* Top Influential Features */}
            <div className="rounded-md border border-zinc-200 bg-white p-3">
              <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-zinc-800">
                Top Influential Features
              </h3>
              <div className="space-y-2.5">
                <div>
                  <div className="mb-1 text-[11px] font-semibold text-orange-900">
                    Spam-Pushing Tokens
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {activeMetrics.top_features.spam_indicators.slice(0, 10).map((f) => (
                      <span
                        key={f.feature}
                        className="rounded border border-orange-200 bg-orange-50 px-1.5 py-0.5 font-mono-safe text-[10px] text-orange-900"
                      >
                        {f.feature} (+{f.weight.toFixed(2)})
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="mb-1 text-[11px] font-semibold text-emerald-900">
                    Legitimate (Ham) Tokens
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {activeMetrics.top_features.ham_indicators.slice(0, 10).map((f) => (
                      <span
                        key={f.feature}
                        className="rounded border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 font-mono-safe text-[10px] text-emerald-900"
                      >
                        {f.feature} ({f.weight.toFixed(2)})
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <p className="text-[10px] leading-snug text-zinc-500">
              {insights.calibration_note} Held-out test metrics reflect the UCI SMS dataset and
              do not measure accuracy on every regional or evolving scam template.
            </p>
          </div>
        )}
      </section>
    </div>
  );
};
