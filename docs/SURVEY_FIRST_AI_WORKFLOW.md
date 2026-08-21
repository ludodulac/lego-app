# Survey-first external AI workflow

BrickHouse external analysis is now intentionally split into two semantic stages before LEGO construction.

## Stage 1 — ArchitecturalSurvey v0.1

Use `frontend/brickhouse-survey-prompt.txt` with the source photos and user facts.

The output must describe what is actually observed: boundaries, materials, nominal colors, weathering, openings and their visual composition, terrain, equipment, roof/chimney context and occlusions. It must not yet choose global depth/height or reconstruct the complete building.

Validate this JSON through `POST /api/v1/validate-survey`.

## Human/contradictory review gate

Review the survey before scene reconstruction. The key questions are semantic rather than metric:

- Are front/left/right/rear assignments correct?
- Does image-left map to the intended canonical facade offset?
- Does every opening really belong to the target building before its physical boundary?
- Are technical boxes/pipes separated from architectural openings?
- Are nominal materials separated from stains/weathering?
- Are visible frame, glazing, mullion, sill and surround details preserved?

## Stage 2 — ArchitecturalScene v0.2

Only after the survey passes review should the existing scene reconstruction prompt estimate coherent dimensions, offsets, terrain grades, platforms, stairs and other geometry.

The survey is evidence input to reconstruction; the scene is not allowed to silently contradict certain survey observations.

## Stage 3 — LEGO representation

Representation policy is separate again. Weathering and temporary objects are ignored by default while nominal materials, opening composition and important architectural details should be preserved where the LEGO vocabulary supports them.

The pipeline is therefore:

`photos → survey → review → scene → adversarial validation → LEGO representation → BOM/instructions`

The real-house photos 1 and 2 are the initial regression case for this workflow.