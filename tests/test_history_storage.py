"""Unit tests for local SQLite analysis history and persistent settings."""

from __future__ import annotations

from pathlib import Path

from src.core.explanation import analyze_message
from src.core.history import LocalStorage
from src.schemas import SettingsUpdateRequest


def test_local_storage_history_crud_and_settings(tmp_path: Path) -> None:
    storage = LocalStorage(db_path=tmp_path / "local.db")

    # Settings persistence
    defaults = storage.get_settings()
    assert defaults.classification_threshold == 0.50
    updated = storage.update_settings(
        SettingsUpdateRequest(
            active_model="logistic_regression",
            classification_threshold=0.65,
            save_history_enabled=True,
        )
    )
    assert updated.active_model == "logistic_regression"
    assert updated.classification_threshold == 0.65

    # History save, search, filter, delete, clear
    res_scam = analyze_message(
        "Dear customer, your SBI YONO account KYC has expired. Account will be blocked. http://sbi-kyc.xyz"
    )
    id1 = storage.save_analysis(res_scam, source="text")

    res_safe = analyze_message("Reminder: Dental appointment tomorrow at 10:30 AM.")
    storage.save_analysis(res_safe, source="text")

    all_items = storage.list_history()
    assert all_items.total_count == 2
    assert all_items.flagged_count == 1

    flagged = storage.list_history(search="YONO", category="Flagged")
    assert len(flagged.records) == 1
    assert flagged.records[0].id == id1
    assert flagged.records[0].full_result is not None

    assert storage.delete_history_item(id1) is True
    assert storage.list_history().total_count == 1

    cleared = storage.clear_history()
    assert cleared == 1
    assert storage.list_history().total_count == 0
