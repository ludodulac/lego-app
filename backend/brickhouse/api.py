"""HTTP API boundary for the BrickHouse engine.

The future photo-analysis layer should produce a BuildingModel and call this API;
it must not depend on brick-engine internals.
"""
from __future__ import annotations

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel
from brickhouse.bricks.export import BrickExportBundle
from brickhouse.pipeline import DEFAULT_FRONT_WIDTH_STUDS, run_m0_pipeline_model


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


app = FastAPI(
    title="BrickHouse Engine API",
    version="0.1.0",
    description="BuildingModel → constructible BrickModel/BOM/AssemblyPlan",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "brickhouse-engine"}


@app.post("/api/v1/build", response_model=BrickExportBundle)
def build(request: BuildRequest) -> BrickExportBundle:
    try:
        return run_m0_pipeline_model(
            request.building,
            front_width_studs=request.front_width_studs,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
