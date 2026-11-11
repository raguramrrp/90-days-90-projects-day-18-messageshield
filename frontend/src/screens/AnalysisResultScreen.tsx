import React, { useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  BadgeAlert,
  Building2,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ClipboardCopy,
  ExternalLink,
  Flag,
  HeartHandshake,
  Layers,
  Link2,
  PhoneCall,
  QrCode,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import { HighlightedMessage } from "../components/HighlightedMessage";
import { getRiskColors, RiskBadge } from "../components/RiskBadge";
import type { AnalyzeResponse } from "../types/messageshield";
import {
  buildGovernmentComplaint,
  buildSafeFamilyWarning,
  copyTextSyncWithAsyncFallback,
  copyTextToClipboard,
  GOV_PORTALS,
} from "../utils/govReport";

interface AnalysisResultScreenProps {
  result: AnalyzeResponse;
  onBack: () => void;
  onScanAnother: () => void;
  onOpenHistory: () => void;
}

function formatPlainReason(raw: string): { label?: string; text: string } {
  const match = raw.match(/^\[([^\]]+)\]\s*(.+)$/);
  if (!match) {
    return { text: raw };
  }
  const tag = match[1]
    .replace(/^Rule:\s*/i, "")
    .replace(/^URL:\s*/i, "Link ")
    .replace(/^Intent:\s*/i, "");
  return { label: tag, text: match[2] };
}

export const AnalysisResultScreen: React.FC<AnalysisResultScreenProps> = ({
  result,
  onBack,
  onScanAnother,
  onOpenHistory,
}) => {
  const bannerStyle = getRiskColors(result.risk_level, result.threat_category);
  const scorePct = Math.round(result.ml_prediction.raw_spam_score * 100);
  const thrPct = Math.round(result.ml_prediction.threshold_used * 100);

  const [govStatus, setGovStatus] = useState<{
    message: string;
    portalUrl?: string;
    portalLabel?: string;
  } | null>(null);
  const [familyStatus, setFamilyStatus] = useState<string | null>(null);
  const [recoveryCopyStatus, setRecoveryCopyStatus] = useState<string | null>(null);
  const [showComplaintDraft, setShowComplaintDraft] = useState(false);
  const [showFamilyDraft, setShowFamilyDraft] = useState(false);
  const [showRecoveryTriage, setShowRecoveryTriage] = useState(false);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  const complaintText = useMemo(() => buildGovernmentComplaint(result), [result]);
  const postIncidentComplaintText = useMemo(
    () => buildGovernmentComplaint(result, { postIncident: true }),
    [result]
  );
  const familyWarningText = useMemo(() => buildSafeFamilyWarning(result), [result]);

  const showGovReporting = result.threat_category !== "Safe / Normal";
  const mlSignalReasons = useMemo(
    () => result.reasons.filter((r) => r.startsWith("[ML Model]")),
    [result.reasons]
  );
  const plainReasons = useMemo(() => {
    const visible = result.reasons
      .filter((r) => !r.startsWith("[ML Model]"))
      .map(formatPlainReason);
    if (visible.length > 0) {
      return visible;
    }
    if (result.threat_category === "Safe / Normal") {
      return [{ text: "No suspicious scam patterns or risky links stood out in this message." }];
    }
    return [{ text: "Language patterns match common unsolicited or high-risk messages." }];
  }, [result.reasons, result.threat_category]);

  const handleReportToPortal = (
    portal: (typeof GOV_PORTALS)[keyof typeof GOV_PORTALS]
  ) => {
    const copied = copyTextSyncWithAsyncFallback(complaintText);
    window.open(portal.url, "_blank", "noopener,noreferrer");
    setGovStatus({
      message: copied
        ? `Message and complaint copied to clipboard. Opening ${portal.shortLabel} in a new tab — paste your complaint there.`
        : `Opening ${portal.shortLabel}. Use "View draft" below if your browser restricted clipboard access.`,
      portalUrl: portal.url,
      portalLabel: portal.shortLabel,
    });
    if (!copied) {
      setShowComplaintDraft(true);
    }
  };

  const handleCopyComplaintOnly = async () => {
    const ok = await copyTextToClipboard(complaintText);
    setGovStatus({
      message: ok
        ? "Message and complaint copied to clipboard."
        : "Automatic copy blocked—select and copy the complaint draft below.",
    });
    if (!ok) {
      setShowComplaintDraft(true);
    }
  };

  const handleCopyFamilyWarning = async () => {
    const ok = await copyTextToClipboard(familyWarningText);
    setFamilyStatus(
      ok
        ? "Safe defanged warning copied (links disabled as hxxp:// and [.]) so family members cannot tap by mistake."
        : "Select and copy the neutralized family warning below."
    );
    if (!ok) {
      setShowFamilyDraft(true);
    }
  };

  const handleCopyPostIncidentReport = async () => {
    const ok = await copyTextToClipboard(postIncidentComplaintText);
    setRecoveryCopyStatus(
      ok
        ? "1930 Emergency Report copied with extracted indicators and UTR placeholder."
        : "Clipboard unavailable — use View draft in Report to Government Portal above."
    );
  };

  const upiItems = result.upi_dissection ?? [];
  const unicodeAudit = result.unicode_audit;
  const senderAnalysis = result.sender_analysis;
  const officialChannels = result.official_channels ?? [];
  const campaignMatch = result.campaign_match;
  const recoveryTriage = result.recovery_triage;

  return (
    <div className="space-y-3" data-testid="analysis-result-screen">
      {/* Sub-navigation */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-1 rounded-md border border-zinc-200 bg-white px-2.5 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-50"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back
        </button>
        <span className="text-[11px] text-zinc-500">Threat Report</span>
      </div>

      {/* 1. Verdict Summary */}
      <section
        className={`rounded-lg border p-3.5 ${bannerStyle.bg} ${bannerStyle.border} ${bannerStyle.accentBorder}`}
      >
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
              {result.classification}
            </div>
            <h2
              data-testid="result-threat-category"
              className={`mt-0.5 text-lg font-bold tracking-tight ${bannerStyle.text}`}
            >
              {result.threat_category}
            </h2>
          </div>
          <RiskBadge risk={result.risk_level} category={result.threat_category} />
        </div>

        <p className="mt-2 text-xs leading-relaxed text-zinc-800">{result.summary}</p>
      </section>

      {/* 2A. Conditional: QR / upi://pay Payment Truth Card */}
      {upiItems.length > 0 && (
        <section
          data-testid="upi-dissection-card"
          className="rounded-lg border border-red-200 border-l-4 border-l-red-600 bg-white p-3.5"
        >
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5">
              <QrCode className="h-4 w-4 text-red-700" />
              <h3 className="text-xs font-semibold uppercase tracking-wide text-red-900">
                UPI / QR Payment Forensics
              </h3>
            </div>
            <span className="rounded bg-red-50 px-1.5 py-0.5 text-[10px] font-semibold text-red-700">
              Outgoing Debit
            </span>
          </div>

          <div className="mt-2 space-y-2">
            {upiItems.map((u, idx) => (
              <div key={idx} className="rounded-md border border-red-100 bg-red-50/40 p-2.5 text-xs">
                <p className="font-semibold leading-relaxed text-red-950">
                  {u.truth_statement}
                </p>
                <div className="mt-2 grid grid-cols-2 gap-1.5 text-[11px] text-zinc-700">
                  <div>
                    <span className="text-zinc-500">Payee UPI ID:</span>{" "}
                    <span className="font-mono-safe font-semibold text-zinc-900">
                      {u.payee_vpa || "Hidden"}
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-500">Amount:</span>{" "}
                    <span className="font-mono-safe font-semibold text-zinc-900">
                      {u.amount ? `${u.currency} ${u.amount}` : "Open-ended"}
                    </span>
                  </div>
                  {u.payee_name && (
                    <div className="col-span-2">
                      <span className="text-zinc-500">Payee Label:</span>{" "}
                      <span className="font-medium text-zinc-900">{u.payee_name}</span>
                    </div>
                  )}
                </div>
                {u.warnings.length > 0 && (
                  <ul className="mt-1.5 space-y-0.5 text-[11px] text-red-900">
                    {u.warnings.map((w, wIdx) => (
                      <li key={wIdx}>• {w}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 2B. Conditional: Unicode Lookalike / Hidden Character Spoof Card */}
      {unicodeAudit && unicodeAudit.has_obfuscation && (
        <section
          data-testid="unicode-audit-card"
          className="rounded-lg border border-amber-200 border-l-4 border-l-amber-600 bg-white p-3.5"
        >
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5">
              <Sparkles className="h-4 w-4 text-amber-700" />
              <h3 className="text-xs font-semibold uppercase tracking-wide text-amber-900">
                Disguised Text / Lookalike Spoof
              </h3>
            </div>
            {unicodeAudit.spoofed_brands.length > 0 && (
              <span className="rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-800">
                Spoofs {unicodeAudit.spoofed_brands.join(", ")}
              </span>
            )}
          </div>

          <ul className="mt-2 space-y-1 text-[11px] leading-relaxed text-zinc-800">
            {unicodeAudit.findings.map((f, i) => (
              <li key={i}>• {f.detail}</li>
            ))}
          </ul>

          {unicodeAudit.canonical_preview && (
            <div className="mt-2 rounded border border-zinc-200 bg-[#FAFAF8] p-2 text-[10px] text-zinc-700">
              <span className="font-semibold text-zinc-900">Revealed plain text:</span>{" "}
              <span className="font-mono-safe break-all">{unicodeAudit.canonical_preview}</span>
            </div>
          )}
        </section>
      )}

      {/* 2C. Conditional: TRAI DLT Sender-Header Analysis Card */}
      {senderAnalysis && senderAnalysis.provided && (
        <section
          data-testid="sender-analysis-card"
          className={`rounded-lg border bg-white p-3.5 ${
            senderAnalysis.is_suspicious_mismatch
              ? "border-red-200 border-l-4 border-l-red-500"
              : "border-zinc-200"
          }`}
        >
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5">
              <Building2 className="h-3.5 w-3.5 text-zinc-700" />
              <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
                Sender ID Check ({senderAnalysis.raw_sender})
              </h3>
            </div>
            <span
              className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                senderAnalysis.is_suspicious_mismatch
                  ? "bg-red-50 text-red-700"
                  : "bg-emerald-50 text-emerald-700"
              }`}
            >
              {senderAnalysis.is_suspicious_mismatch ? "Mismatch" : "Decoded"}
            </span>
          </div>

          <p className="mt-1.5 text-xs font-medium text-zinc-900">
            {senderAnalysis.verdict_summary}
          </p>

          {(senderAnalysis.operator_name || senderAnalysis.category_label) && (
            <div className="mt-2 flex flex-wrap gap-1.5 text-[10px]">
              {senderAnalysis.operator_name && (
                <span className="rounded border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-zinc-700">
                  Carrier: {senderAnalysis.operator_name}
                </span>
              )}
              {senderAnalysis.circle_name && (
                <span className="rounded border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-zinc-700">
                  Circle: {senderAnalysis.circle_name}
                </span>
              )}
              {senderAnalysis.category_label && (
                <span className="rounded border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-zinc-700">
                  {senderAnalysis.category_label}
                </span>
              )}
            </div>
          )}

          {senderAnalysis.findings.length > 0 && (
            <ul className="mt-1.5 space-y-0.5 text-[11px] text-zinc-600">
              {senderAnalysis.findings.map((f, idx) => (
                <li key={idx}>• {f}</li>
              ))}
            </ul>
          )}
        </section>
      )}

      {/* 2D. Conditional: Cross-Message Campaign / Rotated Domain Match */}
      {campaignMatch && campaignMatch.has_match && (
        <section
          data-testid="campaign-match-card"
          className="rounded-lg border border-orange-200 border-l-4 border-l-orange-500 bg-white p-3.5"
        >
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-orange-700" />
              <h3 className="text-xs font-semibold uppercase tracking-wide text-orange-950">
                Recurring Scam Campaign Match
              </h3>
            </div>
            <span className="rounded bg-orange-50 px-1.5 py-0.5 text-[10px] font-semibold text-orange-800">
              {campaignMatch.match_count} Prior Match{campaignMatch.match_count > 1 ? "es" : ""}
            </span>
          </div>

          <p className="mt-1.5 text-xs leading-relaxed text-zinc-800">
            {campaignMatch.summary}
          </p>

          {(campaignMatch.rotated_domains.length > 0 ||
            campaignMatch.shared_phones.length > 0 ||
            campaignMatch.shared_vpas.length > 0) && (
            <div className="mt-2 flex flex-wrap gap-1.5 text-[10px]">
              {campaignMatch.rotated_domains.map((dom) => (
                <span
                  key={dom}
                  className="font-mono-safe rounded border border-orange-200 bg-orange-50 px-2 py-0.5 text-orange-900"
                >
                  Rotated from {dom}
                </span>
              ))}
              {campaignMatch.shared_phones.map((ph) => (
                <span
                  key={ph}
                  className="font-mono-safe rounded border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-zinc-800"
                >
                  Shared phone: {ph}
                </span>
              ))}
              {campaignMatch.shared_vpas.map((vpa) => (
                <span
                  key={vpa}
                  className="font-mono-safe rounded border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-zinc-800"
                >
                  Shared UPI: {vpa}
                </span>
              ))}
            </div>
          )}
        </section>
      )}

      {/* 3. Report to Government Portal & Safe Family Warning (for non-Safe messages) */}
      {showGovReporting && (
        <section
          data-testid="gov-report-section"
          className="rounded-lg border border-zinc-200 bg-white p-3.5"
        >
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5">
              <Flag className="h-3.5 w-3.5 text-zinc-800" />
              <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
                Report or Warn Family
              </h3>
            </div>
            <button
              type="button"
              onClick={() => setShowComplaintDraft((s) => !s)}
              data-testid="gov-report-preview-toggle"
              className="text-[11px] font-medium text-zinc-600 underline decoration-zinc-300 underline-offset-2 hover:text-zinc-900"
            >
              {showComplaintDraft ? "Hide draft" : "View draft"}
            </button>
          </div>

          <p className="mt-1.5 text-[11px] leading-relaxed text-zinc-600">
            Copies the classified message and pre-filled complaint to your clipboard,
            then redirects you to the official Government of India portal.
          </p>

          <div className="mt-2.5 space-y-1.5">
            <button
              type="button"
              onClick={() => handleReportToPortal(GOV_PORTALS.sancharSaathi)}
              data-testid="gov-report-sanchar-btn"
              className="flex w-full items-center justify-between rounded-md bg-zinc-900 px-3 py-2 text-left text-xs font-semibold text-white transition hover:bg-zinc-800"
            >
              <span>Copy & Report SMS on Sanchar Saathi</span>
              <ExternalLink className="h-3.5 w-3.5 shrink-0" />
            </button>

            <div className="grid grid-cols-2 gap-1.5">
              <button
                type="button"
                onClick={() => handleReportToPortal(GOV_PORTALS.cyberCrime)}
                data-testid="gov-report-cybercrime-btn"
                className="flex items-center justify-center gap-1 rounded-md border border-zinc-200 bg-zinc-50 px-2.5 py-1.5 text-[11px] font-medium text-zinc-800 hover:bg-zinc-100"
              >
                <span>cybercrime.gov.in</span>
                <ExternalLink className="h-3 w-3 shrink-0" />
              </button>

              <button
                type="button"
                onClick={handleCopyComplaintOnly}
                data-testid="gov-report-copy-btn"
                className="flex items-center justify-center gap-1 rounded-md border border-zinc-200 bg-white px-2.5 py-1.5 text-[11px] font-medium text-zinc-700 hover:bg-zinc-50"
              >
                <ClipboardCopy className="h-3 w-3 shrink-0" />
                <span>Copy Complaint</span>
              </button>
            </div>

            <button
              type="button"
              onClick={handleCopyFamilyWarning}
              data-testid="copy-family-warning-btn"
              className="flex w-full items-center justify-center gap-1.5 rounded-md border border-zinc-300 bg-[#FAFAF8] px-3 py-2 text-[11px] font-semibold text-zinc-800 transition hover:bg-zinc-100"
            >
              <HeartHandshake className="h-3.5 w-3.5 text-zinc-700" />
              <span>Copy Safe Family Warning (Links Disabled)</span>
            </button>
          </div>

          {govStatus && (
            <div
              data-testid="gov-report-status"
              className="mt-2.5 rounded-md border border-emerald-200 bg-emerald-50 p-2.5 text-[11px] text-emerald-900"
            >
              <div className="flex items-start gap-1.5">
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-700" />
                <div className="space-y-1">
                  <p>{govStatus.message}</p>
                  {govStatus.portalUrl && (
                    <a
                      href={govStatus.portalUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 font-semibold underline"
                    >
                      Open {govStatus.portalLabel}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          )}

          {familyStatus && (
            <div
              data-testid="family-warning-status"
              className="mt-2 rounded-md border border-zinc-200 bg-zinc-50 p-2.5 text-[11px] text-zinc-800"
            >
              <p>{familyStatus}</p>
            </div>
          )}

          {showFamilyDraft && (
            <textarea
              readOnly
              rows={5}
              value={familyWarningText}
              className="font-mono-safe mt-2 w-full rounded-md border border-zinc-200 bg-[#FAFAF8] p-2 text-[10px] leading-relaxed text-zinc-800 focus:outline-none"
            />
          )}

          {showComplaintDraft && (
            <textarea
              readOnly
              rows={7}
              data-testid="gov-report-preview-text"
              value={complaintText}
              className="font-mono-safe mt-2.5 w-full rounded-md border border-zinc-200 bg-[#FAFAF8] p-2 text-[10px] leading-relaxed text-zinc-800 focus:outline-none"
            />
          )}
        </section>
      )}

      {/* 4. Conditional: "Already Tapped or Paid?" Golden-Hour Recovery Triage */}
      {recoveryTriage && recoveryTriage.applicable && (
        <section className="overflow-hidden rounded-lg border border-zinc-200 bg-white">
          <button
            type="button"
            onClick={() => setShowRecoveryTriage((v) => !v)}
            data-testid="recovery-triage-toggle"
            aria-expanded={showRecoveryTriage}
            className="flex w-full items-center justify-between px-3.5 py-2.5 text-left transition hover:bg-zinc-50"
          >
            <div className="flex items-center gap-2">
              <BadgeAlert className="h-4 w-4 text-red-700" />
              <span className="text-xs font-semibold text-zinc-900">
                Already tapped a link, shared OTP, or paid?
              </span>
            </div>
            {showRecoveryTriage ? (
              <ChevronUp className="h-4 w-4 text-zinc-500" />
            ) : (
              <ChevronDown className="h-4 w-4 text-zinc-500" />
            )}
          </button>

          {showRecoveryTriage && (
            <div
              data-testid="recovery-triage-panel"
              className="space-y-2.5 border-t border-zinc-200 bg-[#FAFAF8] p-3.5 text-xs"
            >
              <div>
                <div className="text-xs font-bold text-red-900">
                  {recoveryTriage.scenario_title}
                </div>
                <p className="mt-0.5 text-[11px] leading-relaxed text-zinc-700">
                  {recoveryTriage.urgency_banner}
                </p>
              </div>

              <ol className="space-y-1.5 text-[11px] leading-relaxed text-zinc-800">
                {recoveryTriage.immediate_steps.map((step, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-[10px] font-semibold text-white">
                      {i + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>

              {recoveryTriage.extracted_indicators.length > 0 && (
                <div className="rounded border border-zinc-200 bg-white p-2 text-[10px]">
                  <div className="font-semibold text-zinc-800">
                    Evidence Extracted for Bank / 1930 Police Desk:
                  </div>
                  <ul className="font-mono-safe mt-1 space-y-0.5 text-zinc-700">
                    {recoveryTriage.extracted_indicators.map((ind, idx) => (
                      <li key={idx}>• {ind}</li>
                    ))}
                  </ul>
                </div>
              )}

              <button
                type="button"
                onClick={handleCopyPostIncidentReport}
                data-testid="copy-post-incident-btn"
                className="flex w-full items-center justify-center gap-1.5 rounded-md bg-red-700 px-3 py-2 text-[11px] font-semibold text-white transition hover:bg-red-800"
              >
                <ClipboardCopy className="h-3.5 w-3.5" />
                <span>Copy 1930 Emergency Fraud Report (with UTR slot)</span>
              </button>

              {recoveryCopyStatus && (
                <p className="text-[11px] font-medium text-emerald-800">
                  {recoveryCopyStatus}
                </p>
              )}
            </div>
          )}
        </section>
      )}

      {/* 5. Conditional: Verify Safely Without Links Card */}
      {officialChannels.length > 0 && (
        <section
          data-testid="official-verify-card"
          className="rounded-lg border border-zinc-200 bg-white p-3.5"
        >
          <div className="mb-2 flex items-center gap-1.5">
            <PhoneCall className="h-3.5 w-3.5 text-emerald-700" />
            <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
              Verify Safely Without Links
            </h3>
          </div>
          <div className="space-y-2">
            {officialChannels.map((ch, idx) => (
              <div
                key={idx}
                className="rounded-md border border-emerald-200 bg-emerald-50/40 p-2.5 text-[11px]"
              >
                <div className="flex flex-wrap items-center justify-between gap-1">
                  <span className="font-semibold text-zinc-900">{ch.entity}</span>
                  <span className="font-mono-safe text-[10px] font-medium text-emerald-900">
                    {ch.official_domain}
                  </span>
                </div>
                <p className="mt-1 leading-relaxed text-zinc-700">
                  {ch.verify_instruction}
                </p>
                {ch.helplines.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {ch.helplines.map((num) => (
                      <span
                        key={num}
                        className="font-mono-safe rounded border border-emerald-200 bg-white px-2 py-0.5 text-[10px] font-semibold text-emerald-900"
                      >
                        Helpline: {num}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 6. Message Highlights (Links disabled) */}
      <section className="rounded-lg border border-zinc-200 bg-white p-3.5">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-700">
            Message Highlights
          </h3>
          <span className="text-[10px] text-zinc-400">Links disabled</span>
        </div>

        <div className="rounded-md border border-zinc-100 bg-[#FAFAF8] p-2.5">
          <HighlightedMessage
            message={result.message}
            spans={result.highlighted_spans}
          />
        </div>

        {result.highlighted_spans.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {result.highlighted_spans.map((span, idx) => (
              <span
                key={`${span.start}-${idx}`}
                className="rounded border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-[10px] text-zinc-700"
              >
                <span className="font-semibold text-zinc-900">"{span.text}"</span>:{" "}
                {span.reason}
              </span>
            ))}
          </div>
        )}
      </section>

      {/* 7. What This Message Tries To Do */}
      <section className="rounded-lg border border-zinc-200 bg-white p-3.5">
        <div className="mb-2 flex items-center gap-1.5">
          <Target className="h-3.5 w-3.5 text-zinc-700" />
          <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-700">
            Detected Scam Intent
          </h3>
        </div>

        {result.detected_intents.length === 0 ? (
          <p className="text-xs text-zinc-500">
            No manipulative scam intent patterns detected.
          </p>
        ) : (
          <div className="space-y-2">
            {result.detected_intents.map((item) => (
              <div
                key={item.intent}
                className="rounded-md border border-orange-200 bg-orange-50/50 p-2.5"
              >
                <div className="text-xs font-semibold text-zinc-900">{item.intent}</div>
                <p className="mt-0.5 text-[11px] text-zinc-700">{item.reason}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 8. Link Check */}
      <section className="rounded-lg border border-zinc-200 bg-white p-3.5">
        <div className="mb-2 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Link2 className="h-3.5 w-3.5 text-zinc-700" />
            <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-700">
              Links Found ({result.url_analysis.count})
            </h3>
          </div>
          {result.url_analysis.has_suspicious_urls && (
            <span className="rounded bg-red-50 px-1.5 py-0.5 text-[10px] font-semibold text-red-700">
              Warning
            </span>
          )}
        </div>

        {result.url_analysis.items.length === 0 ? (
          <p className="text-xs text-zinc-500">No links found in this message.</p>
        ) : (
          <div className="space-y-2">
            {result.url_analysis.items.map((u, idx) => (
              <div
                key={`${u.url}-${idx}`}
                className="rounded-md border border-zinc-200 bg-[#FAFAF8] p-2.5"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="font-mono-safe break-all text-[11px] font-semibold text-zinc-900">
                      {u.url}
                    </div>
                    <div className="mt-0.5 text-[10px] text-zinc-500">
                      Site: <span className="font-mono-safe">{u.host}</span>
                    </div>
                  </div>
                  <RiskBadge risk={u.risk_level} compact />
                </div>

                <ul className="mt-1.5 space-y-0.5 text-[11px] text-zinc-700">
                  {u.findings.map((f, i) => (
                    <li key={i}>• {f}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 9. Why It Was Flagged */}
      <section className="rounded-lg border border-zinc-200 bg-white p-3.5">
        <div className="mb-2 flex items-center gap-1.5">
          <AlertTriangle className="h-3.5 w-3.5 text-zinc-700" />
          <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-700">
            Why It Was Checked As {result.risk_level} Risk
          </h3>
        </div>
        <ul className="space-y-1.5 text-xs leading-relaxed text-zinc-700">
          {plainReasons.map((reason, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-zinc-400" />
              <span>
                {reason.label && (
                  <span className="font-semibold text-zinc-900">{reason.label}: </span>
                )}
                {reason.text}
              </span>
            </li>
          ))}
        </ul>
      </section>

      {/* 10. What To Do Next */}
      <section className="rounded-lg border border-zinc-200 border-l-4 border-l-zinc-800 bg-white p-3.5">
        <div className="mb-2 flex items-center gap-1.5">
          {result.risk_level === "Low" ? (
            <ShieldCheck className="h-4 w-4 text-zinc-800" />
          ) : (
            <ShieldAlert className="h-4 w-4 text-zinc-800" />
          )}
          <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
            What To Do Next
          </h3>
        </div>
        <ul className="space-y-1.5 text-xs leading-relaxed text-zinc-700">
          {result.recommended_actions.map((action, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-zinc-700" />
              <span>{action}</span>
            </li>
          ))}
        </ul>
        <p className="mt-2.5 border-t border-zinc-200 pt-2 text-[10px] leading-relaxed text-zinc-500">
          {result.official_reporting_note}
        </p>
      </section>

      {/* 11. Collapsible Technical Signal Details (Hidden by Default for Regular Users) */}
      <section className="overflow-hidden rounded-lg border border-zinc-200 bg-white">
        <button
          type="button"
          onClick={() => setShowTechnicalDetails((v) => !v)}
          data-testid="result-technical-toggle"
          aria-expanded={showTechnicalDetails}
          className="flex w-full items-center justify-between px-3.5 py-2.5 text-left transition hover:bg-zinc-50"
        >
          <span className="text-xs font-medium text-zinc-700">
            Technical Signal Details
          </span>
          {showTechnicalDetails ? (
            <ChevronUp className="h-4 w-4 text-zinc-500" />
          ) : (
            <ChevronDown className="h-4 w-4 text-zinc-500" />
          )}
        </button>

        {showTechnicalDetails && (
          <div className="space-y-2.5 border-t border-zinc-200 bg-[#FAFAF8] p-3 text-[11px] text-zinc-700">
            <div>
              <span className="font-semibold text-zinc-900">Source:</span>{" "}
              {result.category_source_label}
            </div>
            <div>
              <span className="font-semibold text-zinc-900">Classifier:</span>{" "}
              {result.ml_prediction.model_display_name} ({result.ml_prediction.ml_classification})
            </div>

            <div className="space-y-1">
              <div className="flex justify-between font-mono-safe text-[11px] text-zinc-700">
                <span>Raw Spam Score: {scorePct}%</span>
                <span>Threshold: {thrPct}%</span>
              </div>
              <div className="relative h-2 w-full overflow-hidden rounded-full bg-zinc-200">
                <div
                  className={`h-full rounded-full ${
                    scorePct >= thrPct ? "bg-red-600" : "bg-zinc-700"
                  }`}
                  style={{ width: `${Math.max(4, scorePct)}%` }}
                />
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-zinc-900"
                  style={{ left: `${thrPct}%` }}
                />
              </div>
            </div>

            {mlSignalReasons.map((mlReason, idx) => (
              <p key={idx} className="text-[10px] leading-snug text-zinc-600">
                {mlReason}
              </p>
            ))}

            <p className="text-[10px] leading-snug text-zinc-500">
              {result.ml_prediction.calibration_note}
            </p>

            {result.ml_prediction.top_contributions.length > 0 && (
              <div>
                <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
                  Top Token Contributions
                </div>
                <div className="flex flex-wrap gap-1">
                  {result.ml_prediction.top_contributions.map((tok, i) => (
                    <span
                      key={`${tok.token}-${i}`}
                      className={`rounded border px-1.5 py-0.5 font-mono-safe text-[10px] ${
                        tok.direction === "spam"
                          ? "border-orange-200 bg-orange-50 text-orange-900"
                          : "border-emerald-200 bg-emerald-50 text-emerald-900"
                      }`}
                    >
                      {tok.token} ({tok.weight > 0 ? "+" : ""}
                      {tok.weight.toFixed(2)})
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Footer Actions */}
      <div className="grid grid-cols-2 gap-2 pt-1">
        <button
          type="button"
          onClick={onScanAnother}
          className="rounded-lg bg-zinc-900 px-3 py-2.5 text-xs font-semibold text-white hover:bg-zinc-800"
        >
          Scan Another
        </button>
        <button
          type="button"
          onClick={onOpenHistory}
          className="rounded-lg border border-zinc-200 bg-white px-3 py-2.5 text-xs font-semibold text-zinc-800 hover:bg-zinc-50"
        >
          View History
        </button>
      </div>
    </div>
  );
};
