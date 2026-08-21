# ArchitecturalScene v0.2

Status: first executable implementation for BH-069.

## Why this exists

The first real five-photo house trial showed that prompt improvements alone are insufficient. BuildingModel 0.1 can describe a rectangular mass, facade openings and a simple roof, but it cannot honestly encode several architectural facts that materially affect reconstruction quality.

Observed failures from the regression house:

- local ground is not flat: the road rises along one side, so a low workshop window should be interpreted relative to local grade rather than one global z=0;
- the left side contains a raised terrace on posts and an exterior stair, neither of which should be replaced by a solid building volume;
- a chimney is clearly part of the building but had no representation;
- a glazed kitchen door/opening is tied to terrace level, which is not the same as global ground level;
- facade ownership must stop at the actual building boundary; poles, neighbors and perspective can otherwise make an analyzer invent openings beyond the house;
- some visible facade objects are utilities rather than architectural openings;
- rear geometry may be unknown because a neighboring building physically occludes it.

## Architecture

ArchitecturalScene v0.2 sits above the stable BuildingModel 0.1:

`photos -> external Pass A -> external Pass B -> ArchitecturalScene v0.2 -> validate/project -> BuildingModel 0.1 -> M0`

The projection step is explicit about information loss. Unsupported scene elements become structured warnings/blockers and are never silently converted into misleading rectangular masses.

## Implemented contracts

The `brickhouse.scene` package now provides:

- per-dimension `PropertyValue` provenance/evidence for volume width/depth/height;
- `Evidence` references to photo index + observation;
- `SceneVolume`, `SceneOpening`, `SceneRoof`;
- `Terrain` with facade grade profiles;
- opening `local_grade_clearance`;
- `Chimney`;
- `Platform` with `SupportPost` elements;
- multi-run exterior `StairRun`;
- semantic facade equipment: utility_box, pipe, gutter, downspout, vent, antenna, temporary_object;
- facade `VisibilitySpan` records with visible/occluded/unknown state.

Validation includes globally unique IDs, references, roof uniqueness per volume, opening containment/overlap, visibility-span containment/overlap, and rejection of any opening intersecting an occluded/unknown span.

## Terrain model

The initial terrain representation deliberately uses facade-local grade profiles rather than a general mesh:

```json
{
  "terrain": {
    "kind": "facade_grade_profiles",
    "profiles": [
      {
        "facade":"right",
        "start_elevation":0.0,
        "end_elevation":1.2,
        "source":{"kind":"observed","confidence":0.9},
        "evidence":[{"photo_index":2,"observation":"road rises along the right facade"}]
      }
    ]
  }
}
```

This preserves the key fact that local ground varies without pretending to reconstruct a survey-grade terrain mesh.

## Projection to BuildingModel 0.1

`project_scene_to_building()` keeps only representable rectangular building volumes, openings and simple roofs.

Current explicit warnings:

- terrain grade not constructible by BuildingModel 0.1;
- chimney omitted from current M0 projection;
- platform/terrace omitted;
- stair runs omitted.

Current blockers include incompatible volume/roof counts and floor counts beyond BuildingModel 0.1 limits. The projector does not silently clamp or fake scene geometry.

## API

`POST /api/v1/validate-scene` now returns:

- the validated ArchitecturalScene;
- the structured scene -> BuildingModel projection;
- M0 compatibility for the projected BuildingModel when a projection exists.

Legacy `POST /api/v1/validate-analysis` remains available during migration.

## External ChatGPT workflow

`frontend/brickhouse-ai-prompt.txt` now targets ArchitecturalScene v0.2 directly and requires an inventory-first scene-understanding pass.

`frontend/brickhouse-ai-validation-prompt.txt` performs an independent adversarial audit of the candidate scene, including building boundaries, terrain, chimney, terrace/stairs, facade equipment and visibility spans.

The photo frontend automatically detects ArchitecturalScene v0.2 imports, validates them through `/api/v1/validate-scene`, shows projection losses and still permits construction of the supported projected subset when M0 compatibility allows it.

The external JSON cleaner extracts the first complete JSON object, so accidental Markdown fences or trailing provider prose no longer cause the earlier `Unexpected non-whitespace character after JSON` failure.

## Regression fixture

`tests/fixtures/architectural_scene_real_house_v02.json` stores derived semantic facts from the first real house without committing the source photos. It includes:

- exact 10.0 m front-width anchor;
- front low-left opening classified as window;
- low right workshop window with near-zero local-grade clearance;
- rising right-side road/grade;
- right facade uncertainty near the building boundary;
- raised left terrace on supports;
- two-run exterior stair approximation;
- kitchen glazed opening tied to terrace level;
- visible chimney;
- facade utility equipment;
- rear occlusion by the neighboring attached building.

API and scene tests verify that the fixture validates, produces explicit projection losses, flows through the current M0 build subset, and rejects openings placed wholly or partly in occluded/unknown spans.

## Non-goals for v0.2

- full photogrammetric mesh reconstruction;
- arbitrary curved/free-form architecture;
- decorative brick-by-brick facade modeling;
- exact terrain mesh;
- automatic certainty from a single ambiguous photo.

## Next implementation sequence

1. Deploy/run the scene validation path and repeat the same five-photo external two-pass test against the v0.2 prompts.
2. Compare the resulting ArchitecturalScene against the semantic regression fixture.
3. Add LEGO geometry support incrementally: chimney first, then platform/supports/stairs, then terrain-aware visualization/placement.
4. Only after those pieces are stable, consider migrating the integrated vision-provider endpoint from legacy PhotoAnalysisResult to ArchitecturalScene.
