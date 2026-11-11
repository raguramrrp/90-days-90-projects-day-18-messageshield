"""Local SQLite persistence for private analysis history and application settings."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.config import DB_PATH
from src.schemas import (
    AnalyzeResponse,
    HistoryListResponse,
    HistoryRecord,
    SettingsModel,
    SettingsUpdateRequest,
)


class LocalStorage:
    """Privacy-first SQLite repository stored entirely on the local device."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    message TEXT NOT NULL,
                    source TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    threat_category TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    model_name TEXT NOT NULL,
                    raw_spam_score REAL NOT NULL,
                    threshold_used REAL NOT NULL,
                    warning_signs_json TEXT NOT NULL,
                    url_indicators_json TEXT NOT NULL,
                    detected_intents_json TEXT NOT NULL,
                    recommended_actions_json TEXT NOT NULL,
                    full_result_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def get_settings(self, default_model: str = "logistic_regression") -> SettingsModel:
        defaults = SettingsModel(active_model=default_model)  # type: ignore[arg-type]
        with self._connect() as conn:
            rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        data = defaults.model_dump()
        for row in rows:
            key = row["key"]
            if key in data:
                try:
                    data[key] = json.loads(row["value"])
                except json.JSONDecodeError:
                    data[key] = row["value"]
        return SettingsModel(**data)

    def update_settings(
        self,
        patch: SettingsUpdateRequest,
        default_model: str = "logistic_regression",
    ) -> SettingsModel:
        current = self.get_settings(default_model=default_model).model_dump()
        updates = patch.model_dump(exclude_none=True)
        current.update(updates)
        validated = SettingsModel(**current)

        with self._connect() as conn:
            for key, value in validated.model_dump().items():
                conn.execute(
                    """
                    INSERT INTO app_settings (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (key, json.dumps(value)),
                )
            conn.commit()
        return validated

    def save_analysis(self, result: AnalyzeResponse, source: str = "text") -> int:
        warning_signs = [r.label for r in result.rule_indicators]
        if result.url_analysis.has_suspicious_urls:
            warning_signs.append("Suspicious URL pattern")
        url_indicators = [u.model_dump() for u in result.url_analysis.items]
        intents = [i.intent for i in result.detected_intents]

        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO analysis_history (
                    timestamp, message, source, classification, threat_category,
                    risk_level, risk_score, model_name, raw_spam_score, threshold_used,
                    warning_signs_json, url_indicators_json, detected_intents_json,
                    recommended_actions_json, full_result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.timestamp,
                    result.message,
                    source,
                    result.classification,
                    result.threat_category,
                    result.risk_level,
                    result.risk_score,
                    result.ml_prediction.model_name,
                    result.ml_prediction.raw_spam_score,
                    result.ml_prediction.threshold_used,
                    json.dumps(warning_signs),
                    json.dumps(url_indicators),
                    json.dumps(intents),
                    json.dumps(result.recommended_actions),
                    result.model_dump_json(),
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def _row_to_record(self, row: sqlite3.Row, include_full: bool = False) -> HistoryRecord:
        full_result: dict[str, Any] | None = None
        if include_full:
            try:
                full_result = json.loads(row["full_result_json"])
            except json.JSONDecodeError:
                full_result = None
        return HistoryRecord(
            id=int(row["id"]),
            timestamp=row["timestamp"],
            message=row["message"],
            source=row["source"],
            classification=row["classification"],
            threat_category=row["threat_category"],
            risk_level=row["risk_level"],
            risk_score=float(row["risk_score"]),
            model_name=row["model_name"],
            raw_spam_score=float(row["raw_spam_score"]),
            threshold_used=float(row["threshold_used"]),
            warning_signs=json.loads(row["warning_signs_json"]),
            url_indicators=json.loads(row["url_indicators_json"]),
            detected_intents=json.loads(row["detected_intents_json"]),
            recommended_actions=json.loads(row["recommended_actions_json"]),
            full_result=full_result,
        )

    def list_history(
        self,
        search: str = "",
        category: str = "All",
        limit: int = 100,
    ) -> HistoryListResponse:
        clauses: list[str] = []
        params: list[Any] = []

        if search.strip():
            like_q = f"%{search.strip()}%"
            clauses.append("(message LIKE ? OR threat_category LIKE ? OR detected_intents_json LIKE ?)")
            params.extend([like_q, like_q, like_q])

        if category and category != "All":
            if category == "Flagged":
                clauses.append("threat_category NOT IN ('Safe / Normal', 'Promotional')")
            else:
                clauses.append("threat_category = ?")
                params.append(category)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"SELECT * FROM analysis_history {where_sql} ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            counts = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_count,
                    SUM(CASE WHEN threat_category NOT IN ('Safe / Normal', 'Promotional') THEN 1 ELSE 0 END) AS flagged_count
                FROM analysis_history
                """
            ).fetchone()

        return HistoryListResponse(
            total_count=int(counts["total_count"] or 0),
            flagged_count=int(counts["flagged_count"] or 0),
            records=[self._row_to_record(r, include_full=True) for r in rows],
        )

    def get_history_item(self, item_id: int) -> HistoryRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM analysis_history WHERE id = ?",
                (item_id,),
            ).fetchone()
        return self._row_to_record(row, include_full=True) if row else None

    def delete_history_item(self, item_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM analysis_history WHERE id = ?", (item_id,))
            conn.commit()
            return cur.rowcount > 0

    def clear_history(self) -> int:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM analysis_history")
            conn.commit()
            return cur.rowcount
