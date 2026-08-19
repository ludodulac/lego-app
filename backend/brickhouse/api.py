"""HTTP API boundary for BrickHouse engine and photo-analysis services."""
from __future__ import annotations

import os
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel
from brickhouse.bricks.export import BrickExportBundle
from brickhouse.pipeline import DEFAULT_FRONT_WIDTH_STUDS, run_m0_pipeline_model
from brickhouse.vision.models import PhotoAnalysisResult
from brickhouse.vision.openai_provider import PhotoInput, analyze_building_photos

MAX_PHOTO_BYTES = 12 * 1024 * 1024
SUPPORTED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}


class BuildRequest(BaseModel):
    building: BuildingModel
    front_width_studs: int = Field(default=DEFAULT_FRONT_WIDTH_STUDS, gt=0, le=256)


def _cors_origins() -> list[str]:
    configured = os.getenv("BRICKHOUSE_CORS_ORIGINS", "")
    if configured.strip():
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return [
        "https://ludodulac.github.io",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]


def _engine_revision() -> str:
    return os.getenv("RENDER_GIT_COMMIT", "local").strip() or "local"


app = FastAPI(
    title="BrickHouse Engine API",
    version="0.4.0",
    description="Photos or BuildingModel → architectural proposal → constructible BrickModel/BOM/AssemblyPlan",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "brickhouse-engine",
        "vision_enabled": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "engine_revision": _engine_revision(),
    }


@app.post("/api/v1/build", response_model=BrickExportBundle)
def build(request: BuildRequest) -> BrickExportBundle:
    try:
        bundle = run_m0_pipeline_model(request.building, front_width_studs=request.front_width_studs)
        bundle.metadata.engine_revision = _engine_revision()
        return bundle
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/analyze-photos", response_model=PhotoAnalysisResult)
async def analyze_photos(
    photos: list[UploadFile] = File(...),
    user_notes: str = Form(default=""),
    known_front_width_m: float | None = Form(default=None),
) -> PhotoAnalysisResult:
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise HTTPException(
            status_code=503,
            detail="L’analyse photo IA n’est pas activée sur ce serveur. Le moteur BrickHouse reste disponible gratuitement.",
        )
    if not 1 <= len(photos) <= 6:
        raise HTTPException(status_code=422, detail="Envoyez entre 1 et 6 photos.")
    if known_front_width_m is not None and known_front_width_m <= 0:
        raise HTTPException(status_code=422, detail="known_front_width_m doit être positif.")
    prepared: list[PhotoInput] = []
    for upload in photos:
        media_type = upload.content_type or ""
        if media_type not in SUPPORTED_PHOTO_TYPES:
            raise HTTPException(status_code=415, detail=f"Format non pris en charge : {media_type or upload.filename}")
        content = await upload.read(MAX_PHOTO_BYTES + 1)
        if not content:
            raise HTTPException(status_code=422, detail=f"Photo vide : {upload.filename}")
        if len(content) > MAX_PHOTO_BYTES:
            raise HTTPException(status_code=413, detail=f"Photo trop volumineuse : {upload.filename}")
        prepared.append(PhotoInput(content=content, media_type=media_type, filename=upload.filename or "photo"))
    try:
        return analyze_building_photos(
            prepared,
            user_notes=user_notes,
            known_front_width_m=known_front_width_m,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
