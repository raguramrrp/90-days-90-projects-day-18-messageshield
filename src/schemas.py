"""Pydantic v2 API request and response schemas for TextVigil."""

from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

ThreatCategory = Literal[
    "Safe / Normal",
    "Promotional",
    "General Spam",
    "Financial Scam",
    "Phishing",
    "Fake Reward",
    "Impersonation",
    "OTP / Credential Theft",
    "Needs Review",
]

RiskLevel = Literal["Low", "Medium", "High", "Critical", "Needs Review"]


class AnalyzeRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    sender_id: Optional[str] = Field(default=None, max_length=64)
    qr_payloads: list[str] = Field(default_factory=list, max_length=10)
    source: Literal["text", "ocr", "example"] = "text"
    model_name: Optional[Literal["logistic_regression", "multinomial_nb"]] = None
    threshold: Optional[float] = Field(default=None, ge=0.05, le=0.95)
    save_to_history: bool = True


class TokenContribution(BaseModel):
    token: str
    weight: float
    direction: Literal["spam", "ham"]


class MLPredictionInfo(BaseModel):
    model_name: str
    model_display_name: str
    ml_classification: Literal["Spam / Suspicious", "Legitimate (Ham)"]
    raw_spam_score: float
    threshold_used: float
    is_calibrated: bool = False
    calibration_note: str
    top_contributions: list[TokenContribution] = Field(default_factory=list)


class URLInspectionItem(BaseModel):
    url: str
    normalized_url: str
    host: str
    scheme: str
    is_shortened: bool
    is_ip_address: bool
    has_suspicious_tld: bool
    is_lookalike_domain: bool
    lookalike_target: Optional[str] = None
    has_suspicious_params: bool
    risk_score: float
    risk_level: Literal["Low", "Medium", "High"]
    findings: list[str] = Field(default_factory=list)
    reputation_status: str


class URLSummary(BaseModel):
    count: int
    has_suspicious_urls: bool
    reputation_mode: str
    reputation_notice: str
    items: list[URLInspectionItem] = Field(default_factory=list)


class IntentMatch(BaseModel):
    intent: str
    reason: str
    matched_phrases: list[str] = Field(default_factory=list)


class RuleIndicatorMatch(BaseModel):
    rule_id: str
    label: str
    category: str
    severity: Literal["medium", "high", "critical"]
    description: str
    matched_text: str


class HighlightedSpan(BaseModel):
    start: int
    end: int
    text: str
    reason: str
    severity: Literal["info", "medium", "high", "critical"]


class UnicodeSpoofItem(BaseModel):
    token: str
    issue_type: Literal[
        "zero_width",
        "mixed_script_homoglyph",
        "bidi_override",
        "punycode",
        "userinfo_trick",
    ]
    detail: str
    canonical_form: str


class UnicodeAuditReport(BaseModel):
    has_obfuscation: bool = False
    zero_width_count: int = 0
    homoglyph_count: int = 0
    bidi_control_count: int = 0
    spoofed_brands: list[str] = Field(default_factory=list)
    canonical_preview: Optional[str] = None
    findings: list[UnicodeSpoofItem] = Field(default_factory=list)


class UPIDissectionItem(BaseModel):
    raw_uri: str
    source: Literal["message_text", "screenshot_qr"] = "message_text"
    action_type: str = "pay"
    payee_vpa: Optional[str] = None
    payee_name: Optional[str] = None
    amount: Optional[str] = None
    currency: str = "INR"
    merchant_code: Optional[str] = None
    transaction_note: Optional[str] = None
    is_outgoing_transfer: bool = True
    is_personal_handle: bool = False
    lure_contradiction: bool = False
    risk_level: Literal["Medium", "High", "Critical"] = "Medium"
    truth_statement: str
    warnings: list[str] = Field(default_factory=list)


class SenderAnalysis(BaseModel):
    provided: bool = False
    raw_sender: Optional[str] = None
    sender_type: Literal[
        "none",
        "personal_mobile",
        "trai_dlt_header",
        "shortcode_or_alpha",
        "unknown",
    ] = "none"
    operator_name: Optional[str] = None
    circle_name: Optional[str] = None
    header_code: Optional[str] = None
    category_suffix: Optional[str] = None
    category_label: Optional[str] = None
    claimed_entity: Optional[str] = None
    is_suspicious_mismatch: bool = False
    verdict_summary: str = ""
    findings: list[str] = Field(default_factory=list)


class OfficialVerificationChannel(BaseModel):
    entity: str
    official_domain: str
    helplines: list[str] = Field(default_factory=list)
    official_headers: list[str] = Field(default_factory=list)
    verify_instruction: str


class CampaignMatchSummary(BaseModel):
    has_match: bool = False
    match_count: int = 0
    matched_record_ids: list[int] = Field(default_factory=list)
    shared_phones: list[str] = Field(default_factory=list)
    shared_vpas: list[str] = Field(default_factory=list)
    shared_domains: list[str] = Field(default_factory=list)
    rotated_domains: list[str] = Field(default_factory=list)
    similarity_score: float = 0.0
    summary: str = ""


class RecoveryTriagePlan(BaseModel):
    applicable: bool = False
    scenario_title: str = ""
    urgency_banner: str = ""
    immediate_steps: list[str] = Field(default_factory=list)
    evidence_to_keep: list[str] = Field(default_factory=list)
    extracted_indicators: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    analysis_id: Optional[int] = None
    timestamp: str
    message: str
    sender_id: Optional[str] = None
    classification: str
    threat_category: ThreatCategory
    category_source: Literal[
        "ml_and_rules",
        "rule_indicator",
        "ml_baseline",
        "defensive_context",
        "insufficient_evidence",
    ]
    category_source_label: str
    risk_level: RiskLevel
    risk_score: float
    summary: str
    ml_prediction: MLPredictionInfo
    rule_indicators: list[RuleIndicatorMatch] = Field(default_factory=list)
    benign_context_matches: list[str] = Field(default_factory=list)
    detected_intents: list[IntentMatch] = Field(default_factory=list)
    url_analysis: URLSummary
    highlighted_spans: list[HighlightedSpan] = Field(default_factory=list)
    unicode_audit: UnicodeAuditReport = Field(default_factory=UnicodeAuditReport)
    upi_dissection: list[UPIDissectionItem] = Field(default_factory=list)
    sender_analysis: SenderAnalysis = Field(default_factory=SenderAnalysis)
    official_channels: list[OfficialVerificationChannel] = Field(default_factory=list)
    campaign_match: CampaignMatchSummary = Field(default_factory=CampaignMatchSummary)
    recovery_triage: RecoveryTriagePlan = Field(default_factory=RecoveryTriagePlan)
    reasons: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    official_reporting_note: str


class OCRResponse(BaseModel):
    success: bool
    extracted_text: str
    detected_sender: Optional[str] = None
    qr_payloads: list[str] = Field(default_factory=list)
    upi_previews: list[UPIDissectionItem] = Field(default_factory=list)
    character_count: int
    word_count: int
    engine: str
    message: str
    warnings: list[str] = Field(default_factory=list)


class HistoryRecord(BaseModel):
    id: int
    timestamp: str
    message: str
    source: str
    classification: str
    threat_category: str
    risk_level: str
    risk_score: float
    model_name: str
    raw_spam_score: float
    threshold_used: float
    warning_signs: list[str] = Field(default_factory=list)
    url_indicators: list[dict[str, Any]] = Field(default_factory=list)
    detected_intents: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    full_result: Optional[dict[str, Any]] = None


class HistoryListResponse(BaseModel):
    total_count: int
    flagged_count: int
    records: list[HistoryRecord]


class BatchInspectResponse(BaseModel):
    filename: str
    row_count: int
    columns: list[str]
    suggested_column: str
    preview_rows: list[dict[str, str]]


class BatchRowResult(BaseModel):
    row_index: int
    message: str
    classification: str
    threat_category: str
    risk_level: str
    raw_spam_score: float
    url_count: int
    top_intent: Optional[str] = None
    summary: str


class BatchAnalyzeResponse(BaseModel):
    filename: str
    text_column: str
    total_rows: int
    processed_rows: int
    skipped_empty_rows: int
    summary_counts: dict[str, int]
    results: list[BatchRowResult]


class SettingsModel(BaseModel):
    active_model: Literal["logistic_regression", "multinomial_nb"] = "logistic_regression"
    classification_threshold: float = Field(default=0.50, ge=0.10, le=0.90)
    url_reputation_mode: Literal["local_only", "external_configured"] = "local_only"
    save_history_enabled: bool = True
    appearance_mode: Literal["warm_light", "crisp_slate"] = "warm_light"


class SettingsUpdateRequest(BaseModel):
    active_model: Optional[Literal["logistic_regression", "multinomial_nb"]] = None
    classification_threshold: Optional[float] = Field(default=None, ge=0.10, le=0.90)
    url_reputation_mode: Optional[Literal["local_only", "external_configured"]] = None
    save_history_enabled: Optional[bool] = None
    appearance_mode: Optional[Literal["warm_light", "crisp_slate"]] = None


class HealthResponse(BaseModel):
    status: str
    app_name: str
    model_loaded: bool
    active_model: str
    ocr_available: bool
    ocr_engine: str
    history_count: int
