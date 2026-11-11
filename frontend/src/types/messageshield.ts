export type NavTab = "home" | "scan" | "history" | "insights" | "settings";
export type ActiveView = NavTab | "result" | "examples";
export type ScanSubMode = "paste" | "screenshot" | "batch";
export type PreviewMode = "phone" | "fullscreen";

export type ThreatCategory =
  | "Safe / Normal"
  | "Promotional"
  | "General Spam"
  | "Financial Scam"
  | "Phishing"
  | "Fake Reward"
  | "Impersonation"
  | "OTP / Credential Theft"
  | "Needs Review";

export type RiskLevel = "Low" | "Medium" | "High" | "Critical" | "Needs Review";

export interface TokenContribution {
  token: string;
  weight: number;
  direction: "spam" | "ham";
}

export interface MLPredictionInfo {
  model_name: string;
  model_display_name: string;
  ml_classification: "Spam / Suspicious" | "Legitimate (Ham)";
  raw_spam_score: number;
  threshold_used: number;
  is_calibrated: boolean;
  calibration_note: string;
  top_contributions: TokenContribution[];
}

export interface URLInspectionItem {
  url: string;
  normalized_url: string;
  host: string;
  scheme: string;
  is_shortened: boolean;
  is_ip_address: boolean;
  has_suspicious_tld: boolean;
  is_lookalike_domain: boolean;
  lookalike_target: string | null;
  has_suspicious_params: boolean;
  risk_score: number;
  risk_level: "Low" | "Medium" | "High";
  findings: string[];
  reputation_status: string;
}

export interface URLSummary {
  count: number;
  has_suspicious_urls: boolean;
  reputation_mode: string;
  reputation_notice: string;
  items: URLInspectionItem[];
}

export interface IntentMatch {
  intent: string;
  reason: string;
  matched_phrases: string[];
}

export interface RuleIndicatorMatch {
  rule_id: string;
  label: string;
  category: string;
  severity: "medium" | "high" | "critical";
  description: string;
  matched_text: string;
}

export interface HighlightedSpan {
  start: number;
  end: number;
  text: string;
  reason: string;
  severity: "info" | "medium" | "high" | "critical";
}

export interface UnicodeSpoofItem {
  token: string;
  issue_type:
    | "zero_width"
    | "mixed_script_homoglyph"
    | "bidi_override"
    | "punycode"
    | "userinfo_trick";
  detail: string;
  canonical_form: string;
}

export interface UnicodeAuditReport {
  has_obfuscation: boolean;
  zero_width_count: number;
  homoglyph_count: number;
  bidi_control_count: number;
  spoofed_brands: string[];
  canonical_preview: string | null;
  findings: UnicodeSpoofItem[];
}

export interface UPIDissectionItem {
  raw_uri: string;
  source: "message_text" | "screenshot_qr";
  action_type: string;
  payee_vpa: string | null;
  payee_name: string | null;
  amount: string | null;
  currency: string;
  merchant_code: string | null;
  transaction_note: string | null;
  is_outgoing_transfer: boolean;
  is_personal_handle: boolean;
  lure_contradiction: boolean;
  risk_level: "Medium" | "High" | "Critical";
  truth_statement: string;
  warnings: string[];
}

export interface SenderAnalysis {
  provided: boolean;
  raw_sender: string | null;
  sender_type:
    | "none"
    | "personal_mobile"
    | "trai_dlt_header"
    | "shortcode_or_alpha"
    | "unknown";
  operator_name: string | null;
  circle_name: string | null;
  header_code: string | null;
  category_suffix: string | null;
  category_label: string | null;
  claimed_entity: string | null;
  is_suspicious_mismatch: boolean;
  verdict_summary: string;
  findings: string[];
}

export interface OfficialVerificationChannel {
  entity: string;
  official_domain: string;
  helplines: string[];
  official_headers: string[];
  verify_instruction: string;
}

export interface CampaignMatchSummary {
  has_match: boolean;
  match_count: number;
  matched_record_ids: number[];
  shared_phones: string[];
  shared_vpas: string[];
  shared_domains: string[];
  rotated_domains: string[];
  similarity_score: number;
  summary: string;
}

export interface RecoveryTriagePlan {
  applicable: boolean;
  scenario_title: string;
  urgency_banner: string;
  immediate_steps: string[];
  evidence_to_keep: string[];
  extracted_indicators: string[];
}

export interface AnalyzeResponse {
  analysis_id: number | null;
  timestamp: string;
  message: string;
  sender_id?: string | null;
  classification: string;
  threat_category: ThreatCategory;
  category_source:
    | "ml_and_rules"
    | "rule_indicator"
    | "ml_baseline"
    | "defensive_context"
    | "insufficient_evidence";
  category_source_label: string;
  risk_level: RiskLevel;
  risk_score: number;
  summary: string;
  ml_prediction: MLPredictionInfo;
  rule_indicators: RuleIndicatorMatch[];
  benign_context_matches: string[];
  detected_intents: IntentMatch[];
  url_analysis: URLSummary;
  highlighted_spans: HighlightedSpan[];
  unicode_audit?: UnicodeAuditReport;
  upi_dissection?: UPIDissectionItem[];
  sender_analysis?: SenderAnalysis;
  official_channels?: OfficialVerificationChannel[];
  campaign_match?: CampaignMatchSummary;
  recovery_triage?: RecoveryTriagePlan;
  reasons: string[];
  recommended_actions: string[];
  official_reporting_note: string;
}

export interface OCRResponse {
  success: boolean;
  extracted_text: string;
  detected_sender?: string | null;
  qr_payloads?: string[];
  upi_previews?: UPIDissectionItem[];
  character_count: number;
  word_count: number;
  engine: string;
  message: string;
  warnings: string[];
}

export interface HistoryRecord {
  id: number;
  timestamp: string;
  message: string;
  source: string;
  classification: string;
  threat_category: ThreatCategory;
  risk_level: RiskLevel;
  risk_score: number;
  model_name: string;
  raw_spam_score: number;
  threshold_used: number;
  warning_signs: string[];
  url_indicators: URLInspectionItem[];
  detected_intents: string[];
  recommended_actions: string[];
  full_result: AnalyzeResponse | null;
}

export interface HistoryListResponse {
  total_count: number;
  flagged_count: number;
  records: HistoryRecord[];
}

export interface BatchInspectResponse {
  filename: string;
  row_count: number;
  columns: string[];
  suggested_column: string;
  preview_rows: Record<string, string>[];
}

export interface BatchRowResult {
  row_index: number;
  message: string;
  classification: string;
  threat_category: ThreatCategory;
  risk_level: RiskLevel;
  raw_spam_score: number;
  url_count: number;
  top_intent: string | null;
  summary: string;
}

export interface BatchAnalyzeResponse {
  filename: string;
  text_column: string;
  total_rows: number;
  processed_rows: number;
  skipped_empty_rows: number;
  summary_counts: Record<string, number>;
  results: BatchRowResult[];
}

export interface ThresholdCurvePoint {
  threshold: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  true_negatives: number;
  false_positives: number;
  false_negatives: number;
  true_positives: number;
}

export interface ModelMetrics {
  model_key: string;
  display_name: string;
  default_threshold: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
  confusion_matrix: {
    matrix: [[number, number], [number, number]];
    tn: number;
    fp: number;
    fn: number;
    tp: number;
    labels: string[];
  };
  threshold_curve: ThresholdCurvePoint[];
  top_features: {
    spam_indicators: { feature: string; weight: number }[];
    ham_indicators: { feature: string; weight: number }[];
  };
  vocabulary_size: number;
}

export interface ModelInsightsResponse {
  dataset: {
    name: string;
    source_url: string;
    license: string;
    raw_rows: number;
    clean_rows: number;
    duplicate_rows_removed: number;
    ham_count: number;
    spam_count: number;
    spam_ratio: number;
    train_rows: number;
    test_rows: number;
    split_strategy: string;
  };
  trained_at: string;
  selected_model: string;
  selection_rationale: string;
  calibration_note: string;
  active_model: string;
  active_threshold: number;
  models: Record<string, ModelMetrics>;
}

export interface SettingsModel {
  active_model: "logistic_regression" | "multinomial_nb";
  classification_threshold: number;
  url_reputation_mode: "local_only" | "external_configured";
  save_history_enabled: boolean;
  appearance_mode: "warm_light" | "crisp_slate";
}

export interface HealthResponse {
  status: string;
  app_name: string;
  model_loaded: boolean;
  active_model: string;
  ocr_available: boolean;
  ocr_engine: string;
  history_count: number;
}
