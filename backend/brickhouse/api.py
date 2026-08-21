"""HTTP API boundary for BrickHouse engine and photo-analysis services."""
from __future__ import annotations
import os
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel
from brickhouse.bricks.export import BrickExportBundle
from brickhouse.pipeline import DEFAULT_FRONT_WIDTH_STUDS, run_m0_pipeline_model
from brickhouse.scene import (
    ArchitecturalScene,
    ProjectionResult,
    SceneSurveyIssue,
    validate_scene_against_survey,
    project_scene_to_building,
)
from brickhouse.survey import ArchitecturalSurvey, SurveyValidationIssue, validate_survey_extension, validate_survey_semantics
from brickhouse.vision.compatibility import M0Compatibility, assess_m0_compatibility
from brickhouse.vision.models import PhotoAnalysisResult
from brickhouse.vision.openai_provider import PhotoInput
from brickhouse.vision.provider import VisionProviderError, analyze_with_configured_provider, vision_status

MAX_PHOTO_BYTES = 12 * 1024 * 1024
SUPPORTED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTOS = 6


class BuildRequest(BaseModel):
    building: BuildingModel
    front_width_studs: int = Field(default=DEFAULT_FRONT_WIDTH_STUDS, gt=0, le=256)


class SurveyValidationIssueModel(BaseModel):
    code: str
    observation_id: str | None = None
    message: str
    severity: str


class SurveyValidationResponse(BaseModel):
    survey: ArchitecturalSurvey
    issues: list[SurveyValidationIssueModel] = Field(default_factory=list)
    valid_for_scene_fusion: bool


class SurveyExtensionValidationRequest(BaseModel):
    base: ArchitecturalSurvey
    candidate: ArchitecturalSurvey


class SceneValidationResponse(BaseModel):
    scene: ArchitecturalScene
    projection: ProjectionResult
    m0_compatibility: M0Compatibility | None = None


class SceneSurveyValidationRequest(BaseModel):
    survey: ArchitecturalSurvey
    scene: ArchitecturalScene


class SceneSurveyIssueModel(BaseModel):
    code: str
    severity: str
    message: str
    object_id: str | None = None


class SceneSurveyValidationResponse(BaseModel):
    scene: ArchitecturalScene
    issues: list[SceneSurveyIssueModel] = Field(default_factory=list)
    valid_for_projection: bool
    projection: ProjectionResult | None = None
    m0_compatibility: M0Compatibility | None = None


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
    return ["https://ludodulac.github.io", "http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:8000"]


def _engine_revision() -> str:
    return os.getenv("RENDER_GIT_COMMIT", "local").strip() or "local"


def _vision_error_detail(code: str) -> str:
    messages = {
        "gemini_request_rejected": "Gemini a refusé la requête d’analyse (HTTP 400). La configuration du schéma ou de la requête doit être corrigée côté BrickHouse.",
        "gemini_auth_or_access": "Gemini refuse l’accès (HTTP 401/403). Vérifiez la clé GEMINI_API_KEY et les autorisations du projet Google AI Studio.",
        "gemini_model_unavailable": "Le modèle Gemini configuré n’est pas accessible à cette clé (HTTP 404).",
        "gemini_quota_or_rate_limit": "La limite ou le quota Gemini a été atteint (HTTP 429). Attendez un peu ou vérifiez les limites du niveau gratuit dans Google AI Studio.",
        "gemini_upstream_unavailable": "Gemini est momentanément indisponible (erreur 5xx). Réessayez plus tard.",
        "gemini_http_error": "Gemini a renvoyé une erreur HTTP non prévue. Le code détaillé est conservé côté serveur.",
    }
    return messages.get(code, "Le fournisseur de vision n’a pas pu terminer l’analyse. Le diagnostic serveur ne contient aucune clé ni contenu privé.")


app = FastAPI(title="BrickHouse Engine API", version="0.14.0", description="Photos, ArchitecturalSurvey, ArchitecturalScene, external AI analysis or BuildingModel → architectural proposal → constructible BrickModel/BOM/AssemblyPlan")
app.add_middleware(CORSMiddleware, allow_origins=_cors_origins(), allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.get("/health")
def health() -> dict[str, str | bool | None]:
    vision = vision_status()
    return {"status": "ok", "service": "brickhouse-engine", "vision_enabled": vision.ready, "vision_provider": vision.provider, "vision_model": vision.model, "vision_reason": vision.reason, "engine_revision": _engine_revision()}


@app.get("/api/v1/capabilities", response_model=Capabilities)
def capabilities() -> Capabilities:
    vision = vision_status()
    return Capabilities(photo_analysis_ready=vision.ready, photo_provider=vision.provider, photo_model=vision.model, photo_analysis_reason=vision.reason, supported_photo_types=sorted(SUPPORTED_PHOTO_TYPES), engine_revision=_engine_revision())


@app.post("/api/v1/validate-survey", response_model=SurveyValidationResponse)
def validate_architectural_survey(survey: ArchitecturalSurvey) -> SurveyValidationResponse:
    """Validate evidence-first ArchitecturalSurvey v0.1 before scene fusion."""
    raw_issues: list[SurveyValidationIssue] = validate_survey_semantics(survey)
    issues = [SurveyValidationIssueModel(code=i.code, observation_id=i.observation_id, message=i.message, severity=i.severity) for i in raw_issues]
    return SurveyValidationResponse(survey=survey, issues=issues, valid_for_scene_fusion=not any(i.severity == "error" for i in raw_issues))


@app.post("/api/v1/validate-survey-extension", response_model=SurveyValidationResponse)
def validate_architectural_survey_extension(request: SurveyExtensionValidationRequest) -> SurveyValidationResponse:
    """Validate that a Survey extension preserves all previously validated facts."""
    raw_issues: list[SurveyValidationIssue] = validate_survey_extension(request.base, request.candidate)
    issues = [SurveyValidationIssueModel(code=i.code, observation_id=i.observation_id, message=i.message, severity=i.severity) for i in raw_issues]
    return SurveyValidationResponse(
        survey=request.candidate,
        issues=issues,
        valid_for_scene_fusion=not any(i.severity == "error" for i in raw_issues),
    )


@app.post("/api/v1/validate-analysis", response_model=PhotoAnalysisResult)
def validate_external_analysis(result: PhotoAnalysisResult) -> PhotoAnalysisResult:
    """Validate provider-independent BrickHouse JSON and recompute M0 compatibility."""
    return result.model_copy(update={"m0_compatibility": assess_m0_compatibility(result.building)})


@app.post("/api/v1/validate-scene", response_model=SceneValidationResponse)
def validate_architectural_scene(scene: ArchitecturalScene) -> SceneValidationResponse:
    """Validate ArchitecturalScene v0.2 and report its explicit BuildingModel 0.1 projection."""
    projection = project_scene_to_building(scene)
    compatibility = assess_m0_compatibility(projection.building) if projection.building is not None else None
    return SceneValidationResponse(scene=scene, projection=projection, m0_compatibility=compatibility)


@app.post("/api/v1/validate-scene-against-survey", response_model=SceneSurveyValidationResponse)
def validate_architectural_scene_against_survey(request: SceneSurveyValidationRequest) -> SceneSurveyValidationResponse:
    """Validate a reconstructed scene against the Survey that constrained its semantics."""
    raw_issues: list[SceneSurveyIssue] = validate_scene_against_survey(request.survey, request.scene)
    issues = [SceneSurveyIssueModel(code=i.code, severity=i.severity.value, message=i.message, object_id=i.object_id) for i in raw_issues]
    valid = not any(i.severity.value == "error" for i in raw_issues)
    if not valid:
        return SceneSurveyValidationResponse(scene=request.scene, issues=issues, valid_for_projection=False)
    projection = project_scene_to_building(request.scene)
    compatibility = assess_m0_compatibility(projection.building) if projection.building is not None else None
    return SceneSurveyValidationResponse(scene=request.scene, issues=issues, valid_for_projection=True, projection=projection, m0_compatibility=compatibility)


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
async def analyze_photos(photos: list[UploadFile] = File(...), user_notes: str = Form(default=""), known_front_width_m: float | None = Form(default=None)) -> PhotoAnalysisResult:
    vision = vision_status()
    if not vision.ready:
        raise HTTPException(status_code=503, detail=f"L’analyse photo IA n’est pas activée sur ce serveur ({vision.reason}). Le moteur BrickHouse reste disponible.")
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
        result = analyze_with_configured_provider(prepared, user_notes=user_notes, known_front_width_m=known_front_width_m)
        return result.model_copy(update={"m0_compatibility": assess_m0_compatibility(result.building)})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except VisionProviderError as exc:
        raise HTTPException(status_code=502, detail=_vision_error_detail(exc.code)) from exc
