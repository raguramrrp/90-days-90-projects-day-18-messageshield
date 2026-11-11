import React, { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  ClipboardPaste,
  Download,
  FileSpreadsheet,
  ImageUp,
  Loader2,
  QrCode,
  ScanSearch,
  Trash2,
  UploadCloud,
} from "lucide-react";
import { api } from "../api/client";
import { DEMO_EXAMPLES } from "../data/examples";
import { RiskBadge } from "../components/RiskBadge";
import type {
  AnalyzeResponse,
  BatchAnalyzeResponse,
  BatchInspectResponse,
  OCRResponse,
  ScanSubMode,
  SettingsModel,
} from "../types/messageshield";

interface ScannerScreenProps {
  mode: ScanSubMode;
  onChangeMode: (mode: ScanSubMode) => void;
  draftText: string;
  onChangeDraftText: (text: string) => void;
  draftSenderId: string;
  onChangeDraftSenderId: (sender: string) => void;
  autoPasteTrigger: number;
  settings: SettingsModel | null;
  onAnalysisComplete: (result: AnalyzeResponse) => void;
  onOpenExamples: () => void;
}

const MAX_CHARS = 2000;

export const ScannerScreen: React.FC<ScannerScreenProps> = ({
  mode,
  onChangeMode,
  draftText,
  onChangeDraftText,
  draftSenderId,
  onChangeDraftSenderId,
  autoPasteTrigger,
  settings: _settings,
  onAnalysisComplete,
  onOpenExamples,
}) => {
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Screenshot OCR + QR state
  const [ocrImagePreview, setOcrImagePreview] = useState<string | null>(null);
  const [ocrFileName, setOcrFileName] = useState<string>("");
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrResult, setOcrResult] = useState<OCRResponse | null>(null);
  const [ocrConfirmedText, setOcrConfirmedText] = useState("");
  const [ocrSenderId, setOcrSenderId] = useState("");
  const imageInputRef = useRef<HTMLInputElement | null>(null);

  // Batch CSV state
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvInspect, setCsvInspect] = useState<BatchInspectResponse | null>(null);
  const [selectedColumn, setSelectedColumn] = useState("");
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchResults, setBatchResults] = useState<BatchAnalyzeResponse | null>(null);
  const [batchFilter, setBatchFilter] = useState<"all" | "suspicious" | "safe">("all");
  const csvInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (autoPasteTrigger > 0 && mode === "paste") {
      handlePasteFromClipboard();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoPasteTrigger]);

  useEffect(() => {
    return () => {
      if (ocrImagePreview) URL.revokeObjectURL(ocrImagePreview);
    };
  }, [ocrImagePreview]);

  const handlePasteFromClipboard = async () => {
    setErrorMsg(null);
    setInfoMsg(null);
    if (!navigator.clipboard?.readText) {
      setInfoMsg("Clipboard read is unavailable in this browser. Paste manually into the box.");
      return;
    }
    try {
      const text = await navigator.clipboard.readText();
      if (!text.trim()) {
        setInfoMsg("Clipboard is empty. Copy an SMS message first or load a sample.");
        return;
      }
      onChangeDraftText(text.slice(0, MAX_CHARS));
      setInfoMsg("Pasted message from clipboard.");
    } catch {
      setInfoMsg("Browser blocked clipboard access. Tap the box and press Ctrl+V / Paste.");
    }
  };

  const handleAnalyzeText = async (
    textToAnalyze: string,
    source: "text" | "ocr" | "example",
    options: { senderId?: string; qrPayloads?: string[] } = {}
  ) => {
    setErrorMsg(null);
    setInfoMsg(null);
    const trimmed = textToAnalyze.trim();
    if (!trimmed) {
      setErrorMsg("Enter or paste a message before running analysis.");
      return;
    }
    if (trimmed.length > MAX_CHARS) {
      setErrorMsg(`Message exceeds ${MAX_CHARS} character limit.`);
      return;
    }
    setIsAnalyzing(true);
    try {
      const res = await api.analyzeMessage({
        message: trimmed,
        sender_id: options.senderId?.trim() || undefined,
        qr_payloads: options.qrPayloads?.length ? options.qrPayloads : undefined,
        source,
      });
      onAnalysisComplete(res);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleScreenshotSelected = async (file: File | undefined) => {
    if (!file) return;
    setErrorMsg(null);
    setInfoMsg(null);
    setOcrResult(null);
    setOcrConfirmedText("");
    setOcrSenderId("");
    setOcrFileName(file.name);

    if (ocrImagePreview) URL.revokeObjectURL(ocrImagePreview);
    setOcrImagePreview(URL.createObjectURL(file));

    setOcrLoading(true);
    try {
      const res = await api.extractScreenshotText(file);
      setOcrResult(res);
      if (res.success) {
        setOcrConfirmedText(res.extracted_text);
        setOcrSenderId(res.detected_sender ?? "");
      } else {
        setErrorMsg(res.message);
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Screenshot inspection failed.");
    } finally {
      setOcrLoading(false);
    }
  };

  const handleCsvSelected = async (file: File | undefined) => {
    if (!file) return;
    setErrorMsg(null);
    setInfoMsg(null);
    setBatchResults(null);
    setCsvFile(file);
    setBatchLoading(true);
    try {
      const inspected = await api.inspectBatchCsv(file);
      setCsvInspect(inspected);
      setSelectedColumn(inspected.suggested_column);
    } catch (err) {
      setCsvInspect(null);
      setErrorMsg(err instanceof Error ? err.message : "Could not inspect CSV file.");
    } finally {
      setBatchLoading(false);
    }
  };

  const handleRunBatch = async () => {
    if (!csvFile || !selectedColumn) return;
    setErrorMsg(null);
    setBatchLoading(true);
    try {
      const res = await api.analyzeBatchCsv(csvFile, selectedColumn);
      setBatchResults(res);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Batch analysis failed.");
    } finally {
      setBatchLoading(false);
    }
  };

  const handleRunDemoBatch = async () => {
    setErrorMsg(null);
    setInfoMsg(null);
    setCsvFile(null);
    setCsvInspect(null);
    setBatchLoading(true);
    try {
      const res = await api.runBundledDemoBatch();
      setBatchResults(res);
      setInfoMsg(`Loaded bundled demonstration CSV (${res.processed_rows} illustrative SMS rows).`);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Could not load demo CSV.");
    } finally {
      setBatchLoading(false);
    }
  };

  const handleExportBatch = async () => {
    if (!batchResults) return;
    try {
      const blob = await api.exportBatchCsv(batchResults.results);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "textvigil_batch_results.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "CSV export failed.");
    }
  };

  const filteredBatchRows = (batchResults?.results ?? []).filter((r) => {
    if (batchFilter === "suspicious") {
      return r.threat_category !== "Safe / Normal" && r.threat_category !== "Promotional";
    }
    if (batchFilter === "safe") {
      return r.threat_category === "Safe / Normal" || r.threat_category === "Promotional";
    }
    return true;
  });

  const findExample = (id: string) => DEMO_EXAMPLES.find((e) => e.id === id) ?? DEMO_EXAMPLES[0];
  const quickExamples = [
    { label: "Fake KYC", item: findExample("fake-kyc") },
    { label: "Campaign #2", item: findExample("campaign-rotated-kyc") },
    { label: "UPI Bait", item: findExample("upi-qr-link") },
    { label: "Lookalike", item: findExample("cyrillic-lookalike-sbi") },
    { label: "Bank Alert", item: findExample("legit-bank-txn") },
  ];

  return (
    <div className="space-y-3.5">
      {/* Flat Mode Switcher */}
      <div className="grid grid-cols-3 rounded-lg border border-zinc-200 bg-zinc-100 p-0.5">
        {(
          [
            { id: "paste", label: "Paste SMS" },
            { id: "screenshot", label: "Screenshot" },
            { id: "batch", label: "Batch CSV" },
          ] as { id: ScanSubMode; label: string }[]
        ).map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => {
              onChangeMode(tab.id);
              setErrorMsg(null);
              setInfoMsg(null);
            }}
            data-testid={`scan-mode-${tab.id}`}
            className={`rounded-md py-1.5 text-xs font-medium transition ${
              mode === tab.id
                ? "bg-white font-semibold text-zinc-900 shadow-2xs"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {errorMsg && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
          <span>{errorMsg}</span>
        </div>
      )}
      {infoMsg && (
        <div className="flex items-start gap-2 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-xs text-zinc-800">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-zinc-700" />
          <span>{infoMsg}</span>
        </div>
      )}

      {/* MODE A: PASTE SMS */}
      {mode === "paste" && (
        <div className="space-y-3">
          <div className="rounded-lg border border-zinc-200 bg-white p-3.5">
            <div className="mb-2 flex items-center justify-between">
              <label
                htmlFor="sms-message-input"
                className="text-xs font-semibold text-zinc-800"
              >
                Message Text
              </label>
              <span
                className={`font-mono-safe text-[11px] ${
                  draftText.length > MAX_CHARS ? "font-semibold text-red-600" : "text-zinc-400"
                }`}
              >
                {draftText.length} / {MAX_CHARS}
              </span>
            </div>

            <textarea
              id="sms-message-input"
              data-testid="sms-textarea"
              value={draftText}
              onChange={(e) => {
                onChangeDraftText(e.target.value);
                if (errorMsg) setErrorMsg(null);
              }}
              rows={5}
              maxLength={MAX_CHARS + 50}
              placeholder="Paste an SMS, UPI link (upi://pay...), KYC alert, or message..."
              className="w-full resize-none rounded-md border border-zinc-200 bg-[#FAFAF8] p-2.5 text-[13px] leading-relaxed text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:bg-white focus:outline-none"
            />

            <div className="mt-2.5">
              <label
                htmlFor="sms-sender-input"
                className="block text-[11px] font-medium text-zinc-600"
              >
                Sender Header / Number <span className="text-zinc-400">(optional · checks TRAI ID)</span>
              </label>
              <input
                id="sms-sender-input"
                type="text"
                data-testid="sender-id-input"
                value={draftSenderId}
                onChange={(e) => onChangeDraftSenderId(e.target.value)}
                maxLength={64}
                placeholder="e.g. AD-DMOBNK-T or +91 00000 00001"
                className="font-mono-safe mt-1 w-full rounded-md border border-zinc-200 bg-[#FAFAF8] px-2.5 py-1.5 text-xs text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:bg-white focus:outline-none"
              />
            </div>

            <div className="mt-2.5 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={handlePasteFromClipboard}
                  className="inline-flex items-center gap-1 rounded-md border border-zinc-200 bg-zinc-50 px-2.5 py-1.5 text-[11px] font-medium text-zinc-700 hover:bg-zinc-100"
                >
                  <ClipboardPaste className="h-3.5 w-3.5" />
                  Paste
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onChangeDraftText("");
                    onChangeDraftSenderId("");
                    setErrorMsg(null);
                    setInfoMsg(null);
                  }}
                  disabled={!draftText && !draftSenderId}
                  data-testid="clear-sms-button"
                  className="inline-flex items-center gap-1 rounded-md border border-zinc-200 bg-zinc-50 px-2.5 py-1.5 text-[11px] font-medium text-zinc-700 hover:bg-zinc-100 disabled:opacity-40"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Clear
                </button>
              </div>

              <button
                type="button"
                onClick={onOpenExamples}
                className="inline-flex items-center gap-1 text-[11px] font-medium text-zinc-700 underline decoration-zinc-300 underline-offset-2 hover:text-zinc-900"
              >
                <BookOpen className="h-3.5 w-3.5" />
                Examples
              </button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] text-zinc-500">Samples:</span>
            {quickExamples.map((ex) => (
              <button
                key={ex.label}
                type="button"
                onClick={() => {
                  onChangeDraftText(ex.item.message);
                  onChangeDraftSenderId(ex.item.senderTag);
                  setInfoMsg(`Loaded example (${ex.item.title}).`);
                  setErrorMsg(null);
                }}
                className="rounded-md border border-zinc-200 bg-white px-2.5 py-1 text-[11px] font-medium text-zinc-700 hover:bg-zinc-50"
              >
                {ex.label}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={() =>
              handleAnalyzeText(draftText, "text", { senderId: draftSenderId })
            }
            disabled={isAnalyzing}
            data-testid="analyse-message-btn"
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-zinc-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-zinc-800 disabled:opacity-60"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Checking Message...
              </>
            ) : (
              <>
                <ScanSearch className="h-4 w-4" />
                Analyse Message
              </>
            )}
          </button>

          <p className="text-center text-[11px] text-zinc-500">
            Messages are verified privately on your device.
          </p>
        </div>
      )}

      {/* MODE B: SCREENSHOT OCR & QR INSPECTION */}
      {mode === "screenshot" && (
        <div className="space-y-3">
          <div className="rounded-lg border border-zinc-200 bg-white p-3.5">
            <input
              ref={imageInputRef}
              type="file"
              accept=".png,.jpg,.jpeg,.webp,.bmp,.tiff,.tif,image/*"
              className="hidden"
              data-testid="ocr-file-input"
              onChange={(e) => handleScreenshotSelected(e.target.files?.[0])}
            />

            <button
              type="button"
              onClick={() => imageInputRef.current?.click()}
              className="flex w-full flex-col items-center justify-center gap-2 rounded-md border border-dashed border-zinc-300 bg-[#FAFAF8] px-4 py-5 text-center transition hover:border-zinc-500 hover:bg-zinc-50"
            >
              <ImageUp className="h-5 w-5 text-zinc-700" />
              <div>
                <p className="text-xs font-semibold text-zinc-800">
                  {ocrFileName ? `Selected: ${ocrFileName}` : "Upload SMS or Payment QR Screenshot"}
                </p>
                <p className="mt-0.5 text-[11px] text-zinc-500">
                  Reads text + inspects QR payment codes locally (PNG, JPG, WEBP)
                </p>
              </div>
            </button>

            {ocrImagePreview && (
              <div className="mt-3 overflow-hidden rounded-md border border-zinc-200 bg-zinc-50 p-2">
                <img
                  src={ocrImagePreview}
                  alt="Uploaded message screenshot preview"
                  className="mx-auto max-h-44 rounded object-contain"
                />
              </div>
            )}

            {ocrLoading && (
              <div className="mt-3 flex items-center justify-center gap-2 rounded-md bg-zinc-100 p-2.5 text-xs font-medium text-zinc-700">
                <Loader2 className="h-4 w-4 animate-spin text-zinc-700" />
                Inspecting text and QR codes from screenshot...
              </div>
            )}
          </div>

          {ocrResult && ocrResult.success && (
            <div className="space-y-2.5 rounded-lg border border-zinc-200 bg-white p-3.5">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-semibold text-zinc-900">
                  Confirm Extracted Details
                </span>
                <span className="font-mono-safe text-[10px] text-zinc-500">
                  {ocrResult.word_count} words
                  {(ocrResult.qr_payloads?.length ?? 0) > 0
                    ? ` · ${ocrResult.qr_payloads?.length} QR`
                    : ""}
                </span>
              </div>

              {(ocrResult.qr_payloads?.length ?? 0) > 0 && (
                <div
                  data-testid="ocr-qr-preview"
                  className="rounded-md border border-amber-200 bg-amber-50 p-2.5 text-[11px] text-amber-950"
                >
                  <div className="flex items-center gap-1.5 font-semibold">
                    <QrCode className="h-3.5 w-3.5 shrink-0 text-amber-700" />
                    <span>QR Code Decoded Inside Screenshot</span>
                  </div>
                  {(ocrResult.upi_previews ?? []).map((upi, idx) => (
                    <p key={idx} className="mt-1 leading-relaxed text-amber-900">
                      {upi.truth_statement}
                    </p>
                  ))}
                  {(!ocrResult.upi_previews || ocrResult.upi_previews.length === 0) &&
                    ocrResult.qr_payloads?.map((payload, idx) => (
                      <p key={idx} className="font-mono-safe mt-1 break-all text-amber-900">
                        Payload: {payload}
                      </p>
                    ))}
                </div>
              )}

              <div>
                <label className="block text-[11px] font-medium text-zinc-600">
                  Sender Header / Number{" "}
                  <span className="text-zinc-400">(auto-detected when visible)</span>
                </label>
                <input
                  type="text"
                  data-testid="ocr-sender-input"
                  value={ocrSenderId}
                  onChange={(e) => setOcrSenderId(e.target.value)}
                  placeholder="Optional sender ID (e.g. VK-DMOKYC)"
                  className="font-mono-safe mt-1 w-full rounded-md border border-zinc-200 bg-[#FAFAF8] px-2.5 py-1.5 text-xs text-zinc-900 focus:border-zinc-500 focus:bg-white focus:outline-none"
                />
              </div>

              <textarea
                data-testid="ocr-editable-textarea"
                value={ocrConfirmedText}
                onChange={(e) => setOcrConfirmedText(e.target.value)}
                rows={4}
                className="w-full resize-none rounded-md border border-zinc-200 bg-[#FAFAF8] p-2.5 text-[13px] leading-relaxed text-zinc-900 focus:border-zinc-500 focus:bg-white focus:outline-none"
              />

              <button
                type="button"
                onClick={() =>
                  handleAnalyzeText(ocrConfirmedText, "ocr", {
                    senderId: ocrSenderId,
                    qrPayloads: ocrResult.qr_payloads ?? [],
                  })
                }
                disabled={isAnalyzing || !ocrConfirmedText.trim()}
                data-testid="ocr-confirm-analyze-btn"
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-zinc-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-zinc-800 disabled:opacity-50"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Analysing Screenshot...
                  </>
                ) : (
                  <>
                    <ScanSearch className="h-4 w-4" />
                    Confirm & Analyse Extracted Text
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* MODE C: BATCH CSV */}
      {mode === "batch" && (
        <div className="space-y-3">
          <div className="rounded-lg border border-zinc-200 bg-white p-3.5">
            <input
              ref={csvInputRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              data-testid="csv-file-input"
              onChange={(e) => handleCsvSelected(e.target.files?.[0])}
            />

            <button
              type="button"
              onClick={() => csvInputRef.current?.click()}
              className="flex w-full flex-col items-center justify-center gap-2 rounded-md border border-dashed border-zinc-300 bg-[#FAFAF8] px-4 py-4 text-center transition hover:border-zinc-500 hover:bg-zinc-50"
            >
              <UploadCloud className="h-5 w-5 text-zinc-700" />
              <div>
                <div className="text-xs font-semibold text-zinc-800">
                  {csvFile ? csvFile.name : "Upload CSV of Messages"}
                </div>
                <div className="text-[11px] text-zinc-500">
                  Max 5 MB · up to 1,000 rows
                </div>
              </div>
            </button>

            <button
              type="button"
              onClick={handleRunDemoBatch}
              data-testid="batch-demo-btn"
              className="mt-2.5 flex w-full items-center justify-center gap-1.5 rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs font-medium text-zinc-800 hover:bg-zinc-100"
            >
              <FileSpreadsheet className="h-4 w-4 text-zinc-700" />
              Run Bundled Demo CSV (15 Messages)
            </button>
          </div>

          {csvInspect && (
            <div className="space-y-2.5 rounded-lg border border-zinc-200 bg-white p-3.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-zinc-800">Select Text Column</span>
                <span className="text-zinc-500">{csvInspect.row_count} rows detected</span>
              </div>

              <select
                value={selectedColumn}
                onChange={(e) => setSelectedColumn(e.target.value)}
                className="w-full rounded-md border border-zinc-200 bg-[#FAFAF8] px-3 py-2 text-xs font-medium text-zinc-800 focus:border-zinc-500 focus:outline-none"
              >
                {csvInspect.columns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>

              <button
                type="button"
                onClick={handleRunBatch}
                disabled={batchLoading || !selectedColumn}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-zinc-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-zinc-800 disabled:opacity-50"
              >
                {batchLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Scanning Batch...
                  </>
                ) : (
                  <>Run Batch Classification</>
                )}
              </button>
            </div>
          )}

          {batchLoading && !csvInspect && (
            <div className="flex items-center justify-center gap-2 rounded-lg border border-zinc-200 bg-white p-4 text-xs text-zinc-700">
              <Loader2 className="h-4 w-4 animate-spin text-zinc-700" />
              Processing batch messages...
            </div>
          )}

          {batchResults && (
            <div className="space-y-2.5 rounded-lg border border-zinc-200 bg-white p-3.5">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-semibold text-zinc-900">
                    Batch Summary ({batchResults.processed_rows} rows)
                  </h3>
                  <p className="text-[11px] text-zinc-500">
                    Column: <span className="font-mono-safe">{batchResults.text_column}</span>
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleExportBatch}
                  data-testid="batch-export-btn"
                  className="inline-flex items-center gap-1 rounded-md border border-zinc-200 bg-zinc-50 px-2.5 py-1.5 text-[11px] font-medium text-zinc-800 hover:bg-zinc-100"
                >
                  <Download className="h-3.5 w-3.5" />
                  Export CSV
                </button>
              </div>

              <div className="grid grid-cols-3 gap-1.5 text-center">
                <div className="rounded-md border border-red-200 bg-red-50/70 p-2">
                  <div className="font-mono-safe text-sm font-bold text-red-800">
                    {batchResults.summary_counts["Suspicious / Flagged"] ?? 0}
                  </div>
                  <div className="text-[10px] text-red-700">Flagged</div>
                </div>
                <div className="rounded-md border border-amber-200 bg-amber-50/70 p-2">
                  <div className="font-mono-safe text-sm font-bold text-amber-800">
                    {(batchResults.summary_counts["Promotional"] ?? 0) +
                      (batchResults.summary_counts["Needs Review"] ?? 0)}
                  </div>
                  <div className="text-[10px] text-amber-700">Promo / Review</div>
                </div>
                <div className="rounded-md border border-emerald-200 bg-emerald-50/70 p-2">
                  <div className="font-mono-safe text-sm font-bold text-emerald-800">
                    {batchResults.summary_counts["Safe / Normal"] ?? 0}
                  </div>
                  <div className="text-[10px] text-emerald-700">Safe</div>
                </div>
              </div>

              <div className="flex gap-1.5">
                {(
                  [
                    { id: "all", label: "All" },
                    { id: "suspicious", label: "Suspicious Only" },
                    { id: "safe", label: "Safe / Promo" },
                  ] as const
                ).map((f) => (
                  <button
                    key={f.id}
                    type="button"
                    onClick={() => setBatchFilter(f.id)}
                    className={`rounded-md px-2.5 py-1 text-[11px] font-medium ${
                      batchFilter === f.id
                        ? "bg-zinc-900 text-white"
                        : "border border-zinc-200 bg-white text-zinc-600 hover:bg-zinc-50"
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>

              <div className="divide-y divide-zinc-100 rounded-md border border-zinc-200">
                {filteredBatchRows.map((row) => (
                  <div key={row.row_index} className="p-2.5">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[11px] font-semibold text-zinc-800">
                        #{row.row_index} · {row.threat_category}
                      </span>
                      <RiskBadge risk={row.risk_level} category={row.threat_category} compact />
                    </div>
                    <p className="mt-1 line-clamp-2 text-[11px] text-zinc-600">
                      {row.message}
                    </p>
                    <div className="mt-1 flex items-center justify-between text-[10px] text-zinc-500">
                      <span>Score: {Math.round(row.raw_spam_score * 100)}%</span>
                      <span>
                        {row.top_intent || (row.url_count > 0 ? `${row.url_count} URL` : "No threat intent")}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
