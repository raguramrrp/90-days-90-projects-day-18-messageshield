"""FastAPI backend and static frontend host for TextVigil."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from src.config import (
    APP_NAME,
    DB_PATH,
    EVAL_PATH,
    FRONTEND_DIST_DIR,
    MODEL_PATH,
    RULES_PATH,
    SAMPLE_CSV_PATH,
)
from src.core.batch_analysis import (
    analyze_csv_bytes,
    export_batch_results_csv,
    inspect_csv_bytes,
)
from src.core.explanation import analyze_message
from src.core.history import LocalStorage
from src.core.ocr_processor import extract_text_from_screenshot, get_ocr_status
from src.ml.prediction import (
    ModelArtifactNotFoundError,
    is_model_ready,
    load_evaluation_report,
)
from src.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    BatchAnalyzeResponse,
    BatchInspectResponse,
    BatchRowResult,
    HealthResponse,
    HistoryListResponse,
    HistoryRecord,
    OCRResponse,
    SettingsModel,
    SettingsUpdateRequest,
)


def get_storage() -> LocalStorage:
    return LocalStorage(db_path=DB_PATH)


def _resolve_default_model() -> str:
    if EVAL_PATH.exists():
        try:
            report = load_evaluation_report(EVAL_PATH)
            return str(report.get("selected_model", "logistic_regression"))
        except Exception:
            pass
    return "logistic_regression"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite schema on startup; never retrain ML models here
    LocalStorage(db_path=DB_PATH)
    yield


app = FastAPI(
    title=f"{APP_NAME} API",
    description="Explainable SMS/Message Threat Detection & Personal Safety Assistant API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health(storage: LocalStorage = Depends(get_storage)) -> HealthResponse:
    ocr_ok, ocr_engine = get_ocr_status()
    default_model = _resolve_default_model()
    settings = storage.get_settings(default_model=default_model)
    history_stats = storage.list_history(limit=1)
    return HealthResponse(
        status="ok",
        app_name=APP_NAME,
        model_loaded=is_model_ready(MODEL_PATH),
        active_model=settings.active_model,
        ocr_available=ocr_ok,
        ocr_engine=ocr_engine,
        history_count=history_stats.total_count,
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze_endpoint(
    payload: AnalyzeRequest,
    storage: LocalStorage = Depends(get_storage),
) -> AnalyzeResponse:
    default_model = _resolve_default_model()
    settings = storage.get_settings(default_model=default_model)
    chosen_model = payload.model_name or settings.active_model
    chosen_threshold = (
        payload.threshold
        if payload.threshold is not None
        else settings.classification_threshold
    )

    prior_flagged = storage.list_history(category="Flagged", limit=150).records

    try:
        result = analyze_message(
            raw_message=payload.message,
            model_name=chosen_model,
            threshold=chosen_threshold,
            url_reputation_mode=settings.url_reputation_mode,
            model_path=MODEL_PATH,
            rules_path=RULES_PATH,
            sender_id=payload.sender_id,
            qr_payloads=payload.qr_payloads,
            prior_flagged_records=prior_flagged,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ModelArtifactNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if payload.save_to_history and settings.save_history_enabled:
        saved_id = storage.save_analysis(result, source=payload.source)
        result = result.model_copy(update={"analysis_id": saved_id})

    return result


@app.post("/api/ocr/extract", response_model=OCRResponse)
async def ocr_extract_endpoint(file: UploadFile = File(...)) -> OCRResponse:
    content = await file.read()
    return extract_text_from_screenshot(
        image_bytes=content,
        filename=file.filename or "screenshot.png",
    )


@app.get("/api/history", response_model=HistoryListResponse)
def list_history_endpoint(
    search: str = Query(default="", max_length=120),
    category: str = Query(default="All", max_length=60),
    limit: int = Query(default=100, ge=1, le=500),
    storage: LocalStorage = Depends(get_storage),
) -> HistoryListResponse:
    return storage.list_history(search=search, category=category, limit=limit)


@app.get("/api/history/{item_id}", response_model=HistoryRecord)
def get_history_endpoint(
    item_id: int,
    storage: LocalStorage = Depends(get_storage),
) -> HistoryRecord:
    record = storage.get_history_item(item_id)
    if record is None:
        raise HTTPException(status_code=404, detail="History record not found.")
    return record


@app.delete("/api/history/{item_id}")
def delete_history_item_endpoint(
    item_id: int,
    storage: LocalStorage = Depends(get_storage),
) -> dict[str, bool]:
    deleted = storage.delete_history_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="History record not found.")
    return {"deleted": True}


@app.delete("/api/history")
def clear_history_endpoint(
    storage: LocalStorage = Depends(get_storage),
) -> dict[str, int]:
    deleted_count = storage.clear_history()
    return {"deleted_count": deleted_count}


@app.get("/api/model/insights")
def model_insights_endpoint(storage: LocalStorage = Depends(get_storage)) -> JSONResponse:
    try:
        report = load_evaluation_report(EVAL_PATH)
    except ModelArtifactNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    default_model = str(report.get("selected_model", "logistic_regression"))
    settings = storage.get_settings(default_model=default_model)
    payload = {
        **report,
        "active_model": settings.active_model,
        "active_threshold": settings.classification_threshold,
    }
    return JSONResponse(content=payload)


@app.post("/api/batch/inspect", response_model=BatchInspectResponse)
async def batch_inspect_endpoint(file: UploadFile = File(...)) -> BatchInspectResponse:
    content = await file.read()
    try:
        return inspect_csv_bytes(content, filename=file.filename or "upload.csv")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/batch/analyze", response_model=BatchAnalyzeResponse)
async def batch_analyze_endpoint(
    file: UploadFile = File(...),
    text_column: str = Form(...),
    model_name: Optional[str] = Form(default=None),
    threshold: Optional[float] = Form(default=None),
    storage: LocalStorage = Depends(get_storage),
) -> BatchAnalyzeResponse:
    content = await file.read()
    default_model = _resolve_default_model()
    settings = storage.get_settings(default_model=default_model)
    chosen_model = model_name or settings.active_model
    chosen_threshold = threshold if threshold is not None else settings.classification_threshold

    try:
        return analyze_csv_bytes(
            raw_bytes=content,
            filename=file.filename or "upload.csv",
            text_column=text_column,
            model_name=chosen_model,
            threshold=chosen_threshold,
            url_reputation_mode=settings.url_reputation_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ModelArtifactNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/batch/export")
def batch_export_endpoint(results: list[BatchRowResult]) -> Response:
    csv_text = export_batch_results_csv(results)
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="textvigil_batch_results.csv"'
        },
    )


@app.post("/api/batch/demo", response_model=BatchAnalyzeResponse)
def batch_demo_endpoint(storage: LocalStorage = Depends(get_storage)) -> BatchAnalyzeResponse:
    if not SAMPLE_CSV_PATH.exists():
        raise HTTPException(status_code=404, detail="Bundled sample CSV is not available.")
    default_model = _resolve_default_model()
    settings = storage.get_settings(default_model=default_model)
    content = SAMPLE_CSV_PATH.read_bytes()
    return analyze_csv_bytes(
        raw_bytes=content,
        filename=SAMPLE_CSV_PATH.name,
        text_column="message",
        model_name=settings.active_model,
        threshold=settings.classification_threshold,
        url_reputation_mode=settings.url_reputation_mode,
    )


@app.get("/api/settings", response_model=SettingsModel)
def get_settings_endpoint(storage: LocalStorage = Depends(get_storage)) -> SettingsModel:
    return storage.get_settings(default_model=_resolve_default_model())


@app.put("/api/settings", response_model=SettingsModel)
def update_settings_endpoint(
    patch: SettingsUpdateRequest,
    storage: LocalStorage = Depends(get_storage),
) -> SettingsModel:
    return storage.update_settings(patch, default_model=_resolve_default_model())


# Serve built React production bundle when available
if FRONTEND_DIST_DIR.exists():
    assets_dir = FRONTEND_DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    def serve_spa_root() -> FileResponse:
        return FileResponse(str(FRONTEND_DIST_DIR / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found.")
        candidate: Path = (FRONTEND_DIST_DIR / full_path).resolve()
        if candidate.is_file() and str(candidate).startswith(str(FRONTEND_DIST_DIR.resolve())):
            return FileResponse(str(candidate))
        return FileResponse(str(FRONTEND_DIST_DIR / "index.html"))
