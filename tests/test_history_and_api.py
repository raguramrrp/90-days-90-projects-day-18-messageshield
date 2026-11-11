"""Tests for SQLite local history/settings and FastAPI integration endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.config import BASE_DIR, SAMPLE_CSV_PATH
from src.core.history import LocalStorage
from src.main import app, get_storage


def _make_test_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "test_messageshield.db"
    storage = LocalStorage(db_path=db_path)
    app.dependency_overrides[get_storage] = lambda: storage
    return TestClient(app)


def test_health_and_settings_endpoints(tmp_path: Path) -> None:
    client = _make_test_client(tmp_path)
    try:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["app_name"] == "TextVigil"
        assert body["model_loaded"] is True
        assert body["ocr_available"] is True

        upd = client.put(
            "/api/settings",
            json={"active_model": "logistic_regression", "classification_threshold": 0.60},
        )
        assert upd.status_code == 200
        assert upd.json()["active_model"] == "logistic_regression"
        assert upd.json()["classification_threshold"] == 0.60
    finally:
        app.dependency_overrides.clear()


def test_analyze_saves_history_and_supports_search_filter_delete(tmp_path: Path) -> None:
    client = _make_test_client(tmp_path)
    try:
        r1 = client.post(
            "/api/analyze",
            json={
                "message": "URGENT: Your SampleBank account KYC expired. Account will be blocked. Update at http://samplebank-kyc.xyz",
                "source": "text",
            },
        )
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["analysis_id"] is not None
        assert d1["threat_category"] == "Phishing"

        r2 = client.post(
            "/api/analyze",
            json={
                "message": "Your dental consultation at Sample Care Clinic is confirmed for 5 PM tomorrow.",
                "source": "text",
            },
        )
        assert r2.status_code == 200

        hist = client.get("/api/history").json()
        assert hist["total_count"] == 2
        assert hist["flagged_count"] == 1

        filtered = client.get("/api/history", params={"search": "SampleBank", "category": "Flagged"}).json()
        assert len(filtered["records"]) == 1

        del_one = client.delete(f"/api/history/{d1['analysis_id']}")
        assert del_one.status_code == 200
        assert client.get("/api/history").json()["total_count"] == 1

        cleared = client.delete("/api/history")
        assert cleared.status_code == 200
        assert client.get("/api/history").json()["total_count"] == 0
    finally:
        app.dependency_overrides.clear()


def test_insights_ocr_and_batch_endpoints(tmp_path: Path) -> None:
    client = _make_test_client(tmp_path)
    try:
        insights = client.get("/api/model/insights")
        assert insights.status_code == 200
        ins_data = insights.json()
        assert "logistic_regression" in ins_data["models"]
        assert "multinomial_nb" in ins_data["models"]

        scam_img = BASE_DIR / "data" / "sample_screenshots" / "sample_kyc_scam.png"
        with scam_img.open("rb") as fh:
            ocr_resp = client.post(
                "/api/ocr/extract",
                files={"file": (scam_img.name, fh, "image/png")},
            )
        assert ocr_resp.status_code == 200
        assert ocr_resp.json()["success"] is True

        # Ensure invalid analyze input returns 400/422 cleanly
        bad_analyze = client.post("/api/analyze", json={"message": "   "})
        assert bad_analyze.status_code == 400

        # Batch inspect + analyze + demo
        with SAMPLE_CSV_PATH.open("rb") as fh:
            inspect_resp = client.post(
                "/api/batch/inspect",
                files={"file": (SAMPLE_CSV_PATH.name, fh, "text/csv")},
            )
        assert inspect_resp.status_code == 200
        assert inspect_resp.json()["suggested_column"] == "message"

        demo_resp = client.post("/api/batch/demo")
        assert demo_resp.status_code == 200
        assert demo_resp.json()["processed_rows"] == 15
    finally:
        app.dependency_overrides.clear()
