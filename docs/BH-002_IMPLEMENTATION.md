# BH-002 — BuildingModel Python implementation contract

## Goal

Implement the first executable contract for `BuildingModel v0.1` from `docs/BUILDING_MODEL.md` and `docs/schemas/building-model.schema.json`.

The implementation must validate the existing JSON example and reject invalid models deterministically.

## Technical choice

Use **Python 3.12+** and **Pydantic v2**.

Why Pydantic:
- explicit typed contracts;
- nested validation;
- JSON serialization/deserialization;
- readable validation errors;
- future FastAPI compatibility.

Do not add FastAPI yet.

## Files to create

```text
backend/
  brickhouse/
    __init__.py
    building/
      __init__.py
      models.py
      validation.py

tests/
  building/
    test_building_model.py

pyproject.toml
```

Do not create additional application layers, APIs, database code, frontend code, or AI integrations in this ticket.

## Pydantic models

### SourceKind

Enum values:
- `observed`
- `user_provided`
- `inferred`
- `generated_default`

### SourceInfo

Fields:
- `kind: SourceKind`
- `confidence: float` constrained to `[0.0, 1.0]`

### Position3D

Fields:
- `x: float`
- `y: float`
- `z: float`

### VolumeShape

For v0.1 only:
- `rectangular_prism`

### Volume

Fields:
- `id: str`
- `shape: VolumeShape`
- `position: Position3D`
- `width: float > 0`
- `depth: float > 0`
- `height: float > 0`
- `floors: int >= 1 and <= 3`
- `source: SourceInfo`

### Facade

Enum:
- `front`
- `rear`
- `left`
- `right`

### OpeningType

Enum:
- `window`
- `door`
- `garage_door`

### Opening

Fields:
- `id: str`
- `type: OpeningType`
- `volume_id: str`
- `facade: Facade`
- `offset_horizontal: float >= 0`
- `offset_vertical: float >= 0`
- `width: float > 0`
- `height: float > 0`
- `source: SourceInfo`

### RoofType

Enum:
- `flat`
- `gable`

### RidgeDirection

Enum:
- `width`
- `depth`

### Roof

Fields:
- `id: str`
- `volume_id: str`
- `type: RoofType`
- `overhang: float >= 0`
- `ridge_direction: RidgeDirection | None = None`
- `pitch_degrees: float | None = None`
- `source: SourceInfo`

Rules:
- if `type == gable`, `ridge_direction` and `pitch_degrees` are required;
- if `type == flat`, both must be `None`;
- gable pitch must be `> 0` and `< 90`.

### AppearanceSection

Fields:
- `color: str`

### Appearance

Fields:
- `walls: AppearanceSection | None = None`
- `roof: AppearanceSection | None = None`
- `frames: AppearanceSection | None = None`

### Metadata

Fields:
- `created_from: Literal["synthetic", "photo_analysis", "user_edit"]`
- `notes: str | None = None`

### BuildingModel

Fields:
- `schema_version: Literal["0.1"]`
- `id: str`
- `name: str`
- `building_type: str`
- `units: Literal["m"]`
- `volumes: list[Volume]` with at least one item
- `openings: list[Opening] = []`
- `roofs: list[Roof] = []`
- `appearance: Appearance`
- `metadata: Metadata`

## Cross-object validation

Implement these rules at `BuildingModel` level.

### Stable IDs

All IDs within each object collection must be unique.

Additionally, use a single global namespace for object IDs across `volumes`, `openings`, and `roofs`. An ID cannot be reused by two different objects.

### References

Every `Opening.volume_id` must reference an existing `Volume.id`.

Every `Roof.volume_id` must reference an existing `Volume.id`.

At most one roof may reference a given volume in v0.1.

### Opening containment

An opening must fit completely inside its target facade.

Facade horizontal span:
- `front` / `rear` => volume `width`
- `left` / `right` => volume `depth`

Validation:
- `offset_horizontal + width <= facade_span`
- `offset_vertical + height <= volume.height`

Use a small tolerance constant `EPSILON = 1e-9` for floating-point comparisons.

### Opening overlap

Two openings on the same `volume_id` and same `facade` must not overlap in 2D facade coordinates.

Touching edges are allowed.

### Roof validation

Roof-specific field rules described above must be enforced.

## Public API

`backend/brickhouse/building/models.py` should export all model and enum types.

`backend/brickhouse/building/validation.py` should provide:

```python
def load_building_model(path: str | Path) -> BuildingModel:
    """Load UTF-8 JSON from disk and validate it as BuildingModel."""
```

Do not duplicate Pydantic validation logic in this helper.

## Error behaviour

Invalid data should raise Pydantic `ValidationError` (or preserve it when loading from file).

Do not silently correct invalid data.

Do not clamp dimensions, confidence, offsets, pitch, or floors.

## pyproject.toml

Create a minimal Python project configuration with:
- Python `>=3.12`;
- dependency on Pydantic v2;
- pytest as a development/test dependency;
- pytest configured to discover tests under `tests/`;
- package import path configured cleanly for `backend/brickhouse`.

Keep tooling minimal. Do not add linting/formatting frameworks unless needed for the ticket.

## Required tests

At minimum implement the following tests.

1. Existing `docs/examples/building-model-simple-house.json` loads successfully.
2. Round-trip serialization preserves the model semantically.
3. Confidence `< 0` is rejected.
4. Confidence `> 1` is rejected.
5. Zero or negative volume dimensions are rejected.
6. `floors = 0` is rejected.
7. `floors = 4` is rejected in v0.1.
8. Opening referencing an unknown volume is rejected.
9. Roof referencing an unknown volume is rejected.
10. Opening extending past the facade horizontally is rejected.
11. Opening extending above the volume is rejected.
12. Two overlapping openings on the same facade are rejected.
13. Two openings touching only at their edges are accepted.
14. Duplicate IDs are rejected.
15. Two roofs on the same volume are rejected.
16. Gable roof without ridge direction is rejected.
17. Gable roof without pitch is rejected.
18. Gable pitch `<= 0` is rejected.
19. Gable pitch `>= 90` is rejected.
20. Flat roof carrying gable-only fields is rejected.
21. Unsupported `schema_version` is rejected.
22. Units other than `m` are rejected.

## Acceptance criteria

BH-002 implementation is complete when:

- all required Python files exist;
- the current example JSON validates;
- all required tests pass;
- `pytest` exits successfully from repository root;
- no unrelated architecture or feature is introduced;
- no existing catalog/data files are modified;
- the implementation matches `docs/BUILDING_MODEL.md` and this contract.

## Explicit non-goals

Do not implement:
- `BuildingGeometry`;
- brick placement;
- piece catalog logic;
- Three.js;
- Supabase;
- FastAPI endpoints;
- image analysis;
- OpenAI or Claude APIs;
- supplier logic;
- pricing;
- assembly instructions.
