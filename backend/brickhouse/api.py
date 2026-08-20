"""HTTP API boundary for BrickHouse engine and photo-analysis services."""
from __future__ import annotations

import os
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel
from brickhouse.bricks.export import BrickExportBundle
from brickhouse.pipeline import DEFAULT_FRONT_WIDTH_STUDS, run_m0_pipeline_model
from brickhouse.vision.compatibility import assess_m0_compatibility
from brickhouse.vision.models import PhotoAnalysisResult
from brickhouse.vision.openai_provider import PhotoInput
from brickhouse.vision.provider import VisionProviderError, analyze_with_configured_provider, vision_status

MAX_PHOTO_BYTES = 12 * 1024 * 1024
SUPPORTED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTOS = 6


class BuildRequest(BaseModel):
    building: BuildingModel
    front_width_studs: int = Field(default=DEFAULT_FRONT_WIDTH_STUDS, gt=0, le=256)


class Capabilities(BaseModel):
    engine_ready: bool = True
    photo_analysis_ready: bool
    photo_provider: str | None = None
    photo_model: str | None = None
    photo_analysis_reason: str
    max_photos: int = MAX_PHOTOS
    supported_photo_types: list[str]
    max_photo_bytes: int = MAX_PHOTO_BYTES
    engine_revision: str


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
    version="0.8.0",
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
def health() -> dict[str, str | bool | None]:
    vision = vision_status()
    return {
        "status": "ok",
        "service": "brickhouse-engine",
        "vision_enabled": vision.ready,
        "vision_provider": vision.provider,
        "vision_model": vision.model,
        "vision_reason": vision.reason,
        "engine_revision": _engine_revision(),
    }


@app.get("/api/v1/capabilities", response_model=Capabilities)
def capabilities() -> Capabilities:
    vision = vision_status()
    return Capabilities(
        photo_analysis_ready=vision.ready,
        photo_provider=vision.provider,
        photo_model=vision.model,
        photo_analysis_reason=vision.reason,
        supported_photo_types=sorted(SUPPORTED_PHOTO_TYPES),
        engine_revision=_engine_revision(),
    )


@app.post("/api/v1/build", response_model=BrickExportBundle)
def build(request: BuildRequest) -> BrickExportBundle:
    compatibility = assess_m0_compatibility(request.building)
    if not compatibility.buildable:
        raise HTTPException(status_code=422, detail=" ".join(compatibility.blockers))
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
    vision = vision_status()
    if not vision.ready:
        raise HTTPException(
            status_code=503,
            detail=f"L’analyse photo IA n’est pas activée sur ce serveur ({vision.reason}). Le moteur BrickHouse reste disponible.",
        )
    if not 1 <= len(photos) <= MAX_PHOTOS:
        raise HTTPException(status_code=422, detail=f"Envoyez entre 1 et {MAX_PHOTOS} photos.")
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
        result = analyze_with_configured_provider(
            prepared,
            user_notes=user_notes,
            known_front_width_m=known_front_width_m,
        )
        return result.model_copy(update={"m0_compatibility": assess_m0_compatibility(result.building)})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except VisionProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail="Le fournisseur de vision n’a pas pu terminer l’analyse. Réessayez dans un instant ; si le problème persiste, vérifiez la configuration serveur.",
        ) from exc
