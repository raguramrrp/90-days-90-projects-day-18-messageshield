import type { AnalyzeResponse } from "../types/messageshield";

export const GOV_PORTALS = {
  sancharSaathi: {
    id: "sanchar_saathi",
    name: "Sanchar Saathi (Chakshu)",
    shortLabel: "Sanchar Saathi",
    url: "https://www.sancharsaathi.gov.in",
    purpose: "Report suspected fraud SMS, calls, or WhatsApp messages (DoT India).",
  },
  cyberCrime: {
    id: "cyber_crime",
    name: "National Cyber Crime Portal",
    shortLabel: "cybercrime.gov.in",
    url: "https://www.cybercrime.gov.in",
    purpose: "File cybercrime or financial fraud complaints (MHA India · Helpline 1930).",
  },
} as const;

export function defangText(input: string): string {
  if (!input) return "";
  return (
    input
      .replace(/https:\/\//gi, "hxxps://")
      .replace(/http:\/\//gi, "hxxp://")
      .replace(/upi:\/\//gi, "upi[:]//")
      // Neutralize dots inside hostnames, IP octets, and bare domains without altering trailing sentence periods
      .replace(/([a-z0-9-])\.([a-z0-9-])/gi, "$1[.]$2")
      .replace(/([a-z0-9-])\.([a-z0-9-])/gi, "$1[.]$2")
      .replace(/@/g, "[at]")
  );
}

export function buildSafeFamilyWarning(result: AnalyzeResponse): string {
  const firstReason =
    result.upi_dissection?.[0]?.truth_statement ||
    result.reasons.find((r) => !r.startsWith("[ML Model]"))?.replace(/^\[[^\]]+\]\s*/, "") ||
    result.summary;

  const mainUrlOrPayee =
    result.upi_dissection?.[0]?.payee_vpa
      ? `Payee UPI ID blocked: ${defangText(result.upi_dissection[0].payee_vpa)}`
      : result.url_analysis.items[0]
      ? `Suspicious link blocked (do not open): ${defangText(result.url_analysis.items[0].url)}`
      : result.sender_id
      ? `Sender ID seen: ${result.sender_id}`
      : "";

  const safeAlternative =
    result.official_channels?.[0]
      ? `Check safely via: ${result.official_channels[0].entity} (${result.official_channels[0].helplines[0] ?? result.official_channels[0].official_domain})`
      : "Delete this message and check only inside the official app or helpline.";

  const lines = [
    `WARNING: SUSPECTED ${result.threat_category.toUpperCase()} (${result.risk_level} Risk)`,
    "Do NOT tap any link, scan QR, enter UPI PIN, or share OTP.",
    `Why: ${defangText(firstReason)}`,
  ];
  if (mainUrlOrPayee) {
    lines.push(mainUrlOrPayee);
  }
  lines.push(safeAlternative);
  lines.push("Report fraud calls/SMS at sancharsaathi.gov.in or dial 1930.");
  return lines.join("\n");
}

export function buildGovernmentComplaint(
  result: AnalyzeResponse,
  options: { postIncident?: boolean } = {}
): string {
  const intentsText =
    result.detected_intents.length > 0
      ? result.detected_intents.map((i) => i.intent).join(", ")
      : "Suspicious communication indicators";

  const urlsText =
    result.url_analysis.items.length > 0
      ? result.url_analysis.items
          .map((u) => `- ${u.url} (${u.findings[0] ?? u.risk_level})`)
          .join("\n")
      : "- None extracted";

  const upiText =
    result.upi_dissection && result.upi_dissection.length > 0
      ? result.upi_dissection
          .map(
            (u) =>
              `- Payee VPA: ${u.payee_vpa ?? "unknown"} | Amount: ${u.amount ?? "open"} ${u.currency} | ${u.truth_statement}`
          )
          .join("\n")
      : null;

  const evidenceLines =
    result.reasons.length > 0
      ? result.reasons
          .filter((r) => !r.startsWith("[ML Model]"))
          .slice(0, 5)
          .map((r) => `- ${r}`)
          .join("\n")
      : `- ${result.summary}`;

  const sections = [
    options.postIncident
      ? "URGENT CYBER / FINANCIAL FRAUD COMPLAINT (HELPLINE 1930 / CYBERCRIME.GOV.IN)"
      : "SUSPECTED FRAUD COMMUNICATION COMPLAINT",
    `Category: ${result.threat_category} (${result.risk_level} Risk)`,
    `Classification: ${result.classification}`,
    `Sender Header / Number: ${result.sender_id || "Not provided"}`,
    `Suspected Intent: ${intentsText}`,
    `Checked At: ${new Date(result.timestamp).toLocaleString()}`,
    "",
  ];

  if (options.postIncident) {
    sections.push(
      "Post-Incident Financial Details (Complete Before Submitting on cybercrime.gov.in):",
      "- 12-Digit UPI UTR / Bank Transaction Ref ID: [ENTER YOUR UTR NUMBER HERE]",
      "- Debited Bank / Wallet & Last 4 Digits: [ENTER BANK NAME / ACCOUNT LAST 4 DIGITS]",
      "- Transaction Date & Time: [ENTER DATE & TIME OF DEBIT]",
      ""
    );
  }

  sections.push(
    "Complaint Description:",
    options.postIncident
      ? `I am reporting an active ${result.threat_category.toLowerCase()} incident involving ${intentsText.toLowerCase()}. Please freeze the beneficiary account/VPA/domain linked below and block the sender.`
      : `I received this suspected ${result.threat_category.toLowerCase()} message attempting ${intentsText.toLowerCase()}. Please investigate the sender header/number and block associated malicious links or resources.`,
    "",
    "Observed Warning Signs:",
    evidenceLines || `- ${result.summary}`,
    "",
    "Extracted Links:",
    urlsText
  );

  if (upiText) {
    sections.push("", "Extracted UPI / QR Payee Details:", upiText);
  }

  sections.push("", "Exact Message Received:", result.message);
  return sections.join("\n");
}

function syncExecCopy(text: string): boolean {
  try {
    const active = document.activeElement as HTMLElement | null;
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.top = "0";
    ta.style.left = "-9999px";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.focus({ preventScroll: true });
    ta.select();
    ta.setSelectionRange(0, text.length);
    const copied = document.execCommand("copy");
    document.body.removeChild(ta);
    active?.focus?.({ preventScroll: true });
    return copied;
  } catch {
    return false;
  }
}

export function copyTextSyncWithAsyncFallback(text: string): boolean {
  const synced = syncExecCopy(text);
  try {
    if (navigator.clipboard?.writeText && window.isSecureContext) {
      void navigator.clipboard.writeText(text).catch(() => undefined);
      return true;
    }
  } catch {
    // Synchronous copy already attempted
  }
  return synced;
}

export async function copyTextToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Fall back to execCommand below
  }

  return syncExecCopy(text);
}
