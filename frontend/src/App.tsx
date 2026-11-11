import React, { useCallback, useEffect, useRef, useState } from "react";
import textvigilLogo from "./assets/textvigil-logo.png";
import { api } from "./api/client";
import { BottomNav } from "./components/BottomNav";
import { PhoneFrameShell } from "./components/PhoneFrameShell";
import { AnalysisResultScreen } from "./screens/AnalysisResultScreen";
import { ExamplesScreen } from "./screens/ExamplesScreen";
import { HistoryScreen } from "./screens/HistoryScreen";
import { HomeScreen } from "./screens/HomeScreen";
import { InsightsScreen } from "./screens/InsightsScreen";
import { ScannerScreen } from "./screens/ScannerScreen";
import { SettingsScreen } from "./screens/SettingsScreen";
import type {
  ActiveView,
  AnalyzeResponse,
  HealthResponse,
  HistoryListResponse,
  HistoryRecord,
  ModelInsightsResponse,
  NavTab,
  PreviewMode,
  ScanSubMode,
  SettingsModel,
} from "./types/messageshield";

const VIEW_TITLES: Record<ActiveView, string> = {
  home: "TextVigil",
  scan: "Message Scanner",
  result: "Threat Report",
  history: "History",
  insights: "Insights",
  examples: "Sample Messages",
  settings: "Settings",
};

function historyRecordToAnalyzeResponse(rec: HistoryRecord): AnalyzeResponse {
  if (rec.full_result) {
    return rec.full_result;
  }
  return {
    analysis_id: rec.id,
    timestamp: rec.timestamp,
    message: rec.message,
    classification: rec.classification,
    threat_category: rec.threat_category,
    category_source: "ml_baseline",
    category_source_label: "Saved Local Analysis",
    risk_level: rec.risk_level,
    risk_score: rec.risk_score,
    summary: `${rec.threat_category} (${rec.risk_level} risk).`,
    ml_prediction: {
      model_name: rec.model_name,
      model_display_name: rec.model_name,
      ml_classification:
        rec.raw_spam_score >= rec.threshold_used
          ? "Spam / Suspicious"
          : "Legitimate (Ham)",
      raw_spam_score: rec.raw_spam_score,
      threshold_used: rec.threshold_used,
      is_calibrated: false,
      calibration_note:
        "Uncalibrated classifier score; not a real-world fraud probability.",
      top_contributions: [],
    },
    rule_indicators: [],
    benign_context_matches: [],
    detected_intents: rec.detected_intents.map((i) => ({
      intent: i,
      reason: "Saved from previous analysis.",
      matched_phrases: [],
    })),
    url_analysis: {
      count: rec.url_indicators.length,
      has_suspicious_urls: rec.url_indicators.some((u) => u.risk_level !== "Low"),
      reputation_mode: "local_only",
      reputation_notice: "Structural URL inspection only.",
      items: rec.url_indicators,
    },
    highlighted_spans: [],
    reasons: rec.warning_signs,
    recommended_actions: rec.recommended_actions,
    official_reporting_note:
      "For suspected cyber fraud in India, call 1930 or report at cybercrime.gov.in.",
  };
}

export const App: React.FC = () => {
  const [previewMode, setPreviewMode] = useState<PreviewMode>("phone");
  const [activeView, setActiveView] = useState<ActiveView>("home");
  const [activeTab, setActiveTab] = useState<NavTab>("home");
  const [previousView, setPreviousView] = useState<ActiveView>("home");

  const [scanMode, setScanMode] = useState<ScanSubMode>("paste");
  const [draftText, setDraftText] = useState("");
  const [draftSenderId, setDraftSenderId] = useState("");
  const [autoPasteTrigger, setAutoPasteTrigger] = useState(0);
  const [currentResult, setCurrentResult] = useState<AnalyzeResponse | null>(null);

  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [settings, setSettings] = useState<SettingsModel | null>(null);
  const [history, setHistory] = useState<HistoryListResponse | null>(null);
  const [historySearch, setHistorySearch] = useState("");
  const [historyCategory, setHistoryCategory] = useState("All");
  const [insights, setInsights] = useState<ModelInsightsResponse | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsError, setInsightsError] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement | null>(null);

  const scrollTop = () => {
    scrollRef.current?.scrollTo({ top: 0, behavior: "instant" });
  };

  const refreshHistory = useCallback(async (search = "", category = "All") => {
    try {
      const data = await api.getHistory(search, category);
      setHistory(data);
    } catch {
      // Handled gracefully in UI
    }
  }, []);

  const loadInsights = useCallback(async () => {
    setInsightsLoading(true);
    setInsightsError(null);
    try {
      const data = await api.getModelInsights();
      setInsights(data);
    } catch (err) {
      setInsightsError(err instanceof Error ? err.message : "Failed to load insights.");
    } finally {
      setInsightsLoading(false);
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const [h, s] = await Promise.all([api.getHealth(), api.getSettings()]);
        setHealth(h);
        setSettings(s);
      } catch {
        // Offline/error handled cleanly in views
      }
      await refreshHistory("", "All");
    })();
  }, [refreshHistory]);

  useEffect(() => {
    const timer = setTimeout(() => {
      refreshHistory(historySearch, historyCategory);
    }, 150);
    return () => clearTimeout(timer);
  }, [historySearch, historyCategory, refreshHistory]);

  useEffect(() => {
    if (activeView === "insights" && !insights && !insightsLoading) {
      loadInsights();
    }
  }, [activeView, insights, insightsLoading, loadInsights]);

  const navigateToTab = (tab: NavTab) => {
    setPreviousView(activeView);
    setActiveTab(tab);
    setActiveView(tab);
    scrollTop();
  };

  const handleStartScan = (mode: ScanSubMode, autoPaste = false) => {
    setPreviousView(activeView);
    setScanMode(mode);
    setActiveTab("scan");
    setActiveView("scan");
    if (autoPaste) {
      setAutoPasteTrigger((c) => c + 1);
    }
    scrollTop();
  };

  const handleAnalysisComplete = (res: AnalyzeResponse) => {
    setPreviousView("scan");
    setCurrentResult(res);
    setActiveView("result");
    refreshHistory(historySearch, historyCategory);
    scrollTop();
  };

  const handleOpenHistoryRecord = (record: HistoryRecord) => {
    setPreviousView(activeView);
    setCurrentResult(historyRecordToAnalyzeResponse(record));
    setActiveView("result");
    scrollTop();
  };

  const handleOpenExamples = () => {
    setPreviousView(activeView);
    setActiveView("examples");
    scrollTop();
  };

  const handleSendExampleToScanner = (msg: string, sender?: string) => {
    setDraftText(msg);
    setDraftSenderId(sender ?? "");
    setScanMode("paste");
    setActiveTab("scan");
    setActiveView("scan");
    scrollTop();
  };

  const handleDeleteRecord = async (id: number) => {
    await api.deleteHistoryItem(id);
    await refreshHistory(historySearch, historyCategory);
  };

  const handleClearAllHistory = async () => {
    await api.clearHistory();
    await refreshHistory(historySearch, historyCategory);
  };

  const handleUpdateSettings = async (patch: Partial<SettingsModel>) => {
    const updated = await api.updateSettings(patch);
    setSettings(updated);
    if (insights) {
      setInsights({
        ...insights,
        active_model: updated.active_model,
        active_threshold: updated.classification_threshold,
      });
    }
  };

  const handleResetViewport = () => {
    setPreviewMode("phone");
    scrollTop();
  };

  const header = (
    <header className="flex h-12 shrink-0 items-center gap-2.5 border-b border-zinc-200 bg-white px-4">
      <img
        src={textvigilLogo}
        alt="TextVigil logo"
        className="h-7 w-7 shrink-0 rounded-md"
      />
      <span className="text-[15px] font-semibold tracking-tight text-zinc-900">
        {VIEW_TITLES[activeView]}
      </span>
    </header>
  );

  const bottomNav = <BottomNav activeTab={activeTab} onSelectTab={navigateToTab} />;

  return (
    <PhoneFrameShell
      previewMode={previewMode}
      onChangePreviewMode={setPreviewMode}
      onResetViewport={handleResetViewport}
      scrollContainerRef={scrollRef}
      header={header}
      bottomNav={bottomNav}
      appearanceMode={settings?.appearance_mode ?? "warm_light"}
    >
      {activeView === "home" && (
        <HomeScreen
          history={history}
          onStartScan={handleStartScan}
          onOpenExamples={handleOpenExamples}
          onOpenHistoryRecord={handleOpenHistoryRecord}
          onNavigateTab={navigateToTab}
        />
      )}

      {activeView === "scan" && (
        <ScannerScreen
          mode={scanMode}
          onChangeMode={setScanMode}
          draftText={draftText}
          onChangeDraftText={setDraftText}
          draftSenderId={draftSenderId}
          onChangeDraftSenderId={setDraftSenderId}
          autoPasteTrigger={autoPasteTrigger}
          settings={settings}
          onAnalysisComplete={handleAnalysisComplete}
          onOpenExamples={handleOpenExamples}
        />
      )}

      {activeView === "result" && currentResult && (
        <AnalysisResultScreen
          result={currentResult}
          onBack={() => {
            setActiveView(previousView === "result" ? "home" : previousView);
            scrollTop();
          }}
          onScanAnother={() => handleStartScan("paste")}
          onOpenHistory={() => navigateToTab("history")}
        />
      )}

      {activeView === "history" && (
        <HistoryScreen
          history={history}
          search={historySearch}
          categoryFilter={historyCategory}
          onChangeSearch={setHistorySearch}
          onChangeCategory={setHistoryCategory}
          onSelectRecord={handleOpenHistoryRecord}
          onDeleteRecord={handleDeleteRecord}
          onClearAll={handleClearAllHistory}
          onGoToScan={() => handleStartScan("paste")}
        />
      )}

      {activeView === "insights" && (
        <InsightsScreen
          insights={insights}
          loading={insightsLoading}
          error={insightsError}
          onRetry={loadInsights}
        />
      )}

      {activeView === "examples" && (
        <ExamplesScreen
          onSendToScanner={handleSendExampleToScanner}
          onBack={() => {
            setActiveView(previousView === "examples" ? "home" : previousView);
            scrollTop();
          }}
        />
      )}

      {activeView === "settings" && (
        <SettingsScreen
          settings={settings}
          health={health}
          historyCount={history?.total_count ?? 0}
          previewMode={previewMode}
          onChangePreviewMode={setPreviewMode}
          onUpdateSettings={handleUpdateSettings}
          onClearHistory={handleClearAllHistory}
        />
      )}
    </PhoneFrameShell>
  );
};

export default App;
