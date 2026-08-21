# ArchitecturalScene v0.2 — implementation direction

Status: first executable contract/projection slice implemented in BH-069.

## Why this exists

The first real five-photo house trial showed that prompt improvements alone are insufficient. BuildingModel 0.1 can describe a rectangular mass, facade openings and a simple roof, but it cannot honestly encode several architectural facts that materially affect reconstruction quality.

Observed failures from the regression house:

- local ground is not flat: the road rises along one side, so a low workshop window should be interpreted relative to local grade rather than one global z=0;
- the left side contains a raised terrace on posts and an exterior stair, neither of which should be replaced by a solid building volume;
- a chimney is clearly part of the building but has no representation;
- a glazed kitchen door/opening is tied to terrace level, which is not the same as global ground level;
- facade ownership must stop at the actual building boundary; poles, neighbors and perspective can otherwise make an analyzer invent openings beyond the house;
- some visible facade objects are utilities (service boxes, pipes, gutters) rather than architectural openings;
- rear geometry may be unknown because a neighboring building physically occludes it.

## Compatibility principle

Do not break BuildingModel 0.1 or the current M0 builder. ArchitecturalScene v0.2 sits above it:

`photos -> analysis -> ArchitecturalScene v0.2 -> compatibility/projection -> BuildingModel 0.1 -> M0`

The projection step is explicit about information loss. Unsupported scene elements become warnings/blockers; they are never silently converted into misleading rectangular masses.

## Implemented scene concepts

The first code slice now exists under `backend/brickhouse/scene/`.

### Evidence and per-property provenance

`Evidence` stores a photo index and factual observation. `PropertyValue` lets width/depth/height carry independent `SourceInfo`, so an exact 10 m facade width can remain user-provided while depth and height remain inferred.

### Local ground / terrain profile

`Terrain(kind="facade_grade_profiles")` contains `GradeProfile` records with facade, start/end elevation, source and evidence. This is deliberately simpler than a terrain mesh.

### Facade-local opening elevation

`SceneOpening.local_grade_clearance` records the relation between an opening and local visible grade while keeping global architectural z coordinates.

### Chimneys

`Chimney` is a first-class rectangular architectural element with position, dimensions, source and evidence.

### Exterior platforms / terraces and supports

`Platform` represents a horizontal slab separately from `SupportPost` objects. It is not projected as a fake solid building volume.

### Exterior stairs

`StairRun` records start/end 3D points and width. Multiple runs can represent an L-shaped exterior stair.

### Facade equipment / non-opening observations

`FacadeEquipment` supports utility_box, pipe, gutter, downspout, vent, antenna and temporary_object semantic observations.

### Occlusion and facade visibility

`FacadeVisibility` contains `VisibilitySpan` records (`visible`, `occluded`, `unknown`). Scene validation rejects an opening whose center lies inside a declared non-visible span. This is a conservative first guard against hallucinated rear/side openings.

## Projection to BuildingModel 0.1

`project_scene_to_building()` now:

1. preserves the supported principal rectangular volume, openings and simple roof;
2. emits structured warnings for terrain, chimneys, platforms and stairs that BuildingModel 0.1 cannot represent;
3. blocks current M0 projection when the scene contains more than one building volume or more than one roof;
4. never converts a platform/stair into a solid building volume;
5. keeps projection-loss codes in BuildingModel metadata notes for downstream visibility.

This is intentionally a compatibility projection, not a claim that M0 can build the entire scene.

## Regression expectations for the current house

The reference scene should encode at least:

- front facade width = 10.0 m exact user anchor;
- front low-left opening = window, not door;
- right low opening = workshop window with near-zero local-grade clearance;
- right-side building boundary stops before unrelated neighboring/context geometry;
- no unsupported rear openings in occluded portions;
- left raised terrace/platform on supports;
- exterior stair on left;
- terrain/road rising along right side;
- at least one chimney on the main building;
- gable roof with ridge axis front-to-rear and conservative pitch confidence;
- kitchen glazed opening aligned to terrace level rather than global flat ground.

Tests under `tests/scene/` cover occluded-opening rejection, preservation of supported geometry, warnings for unsupported scene elements and blocking of multi-volume M0 projection.

## Still to implement

- API endpoints for validating/importing ArchitecturalScene v0.2;
- a full real-house regression fixture expressed directly as ArchitecturalScene JSON;
- prompt output migration from PhotoAnalysisResult/BuildingModel to ArchitecturalScene once the API path is stable;
- LEGO engine support, incrementally: chimney first, then platform/supports/stairs, then terrain-aware visualization/placement;
- richer facade-boundary semantics beyond visibility spans when repeated cases justify them.

## Non-goals for v0.2

- full photogrammetric mesh reconstruction;
- arbitrary curved/free-form architecture;
- decorative brick-by-brick facade modeling;
- exact terrain mesh;
- automatic certainty from a single ambiguous photo.
