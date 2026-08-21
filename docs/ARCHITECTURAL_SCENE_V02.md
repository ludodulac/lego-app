# ArchitecturalScene v0.2 — design direction

Status: draft design for BH-069.

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

Do not break BuildingModel 0.1 or the current M0 builder. ArchitecturalScene v0.2 should sit above it:

`photos -> analysis -> ArchitecturalScene v0.2 -> compatibility/projection -> BuildingModel 0.1 -> M0`

The projection step must be explicit about information loss. Unsupported scene elements become blockers/warnings; they must never be silently converted into misleading rectangular masses.

## Proposed scene concepts

### 1. Evidence and provenance per property/object

Every scene object may carry:

- `source.kind`: observed | user_provided | inferred | generated_default
- `confidence`
- `evidence`: references such as photo index + short observation

For dimensions that mix certainty, keep provenance at property level where needed. Example: facade width can be user-provided while depth/height remain inferred.

### 2. Local ground / terrain profile

Minimum viable representation:

```json
{
  "terrain": {
    "kind": "facade_grade_profiles",
    "profiles": [
      {"facade":"right","start_elevation":0.0,"end_elevation":1.4,"source":{...}}
    ]
  }
}
```

This is intentionally simpler than a general terrain mesh. It is sufficient to express that local ground rises along a facade and to interpret low openings relative to the ground visible beneath them.

A later version may use a plane or free-form surface if repeated cases demand it.

### 3. Facade-local opening elevation

Keep architectural z coordinates in a global frame, but allow evidence/derived metadata to record local sill/threshold height above grade.

Example:

```json
{
  "opening_id":"window_right_workshop_low",
  "local_grade_clearance":0.05
}
```

This avoids moving the opening merely because the road rises.

### 4. Chimneys

Add a simple first-class chimney primitive:

```json
{
  "id":"chimney_01",
  "type":"chimney",
  "position":{"x":...,"y":...,"z":...},
  "width":...,"depth":...,"height":...,
  "source":{...}
}
```

Rectangular chimneys are enough for the current regression case. Complex caps can remain appearance/detail metadata.

### 5. Exterior platforms / terraces

Represent a terrace as a horizontal platform, not a solid building volume:

```json
{
  "id":"terrace_left",
  "type":"platform",
  "position":{"x":...,"y":...,"z":...},
  "width":...,"depth":...,"thickness":...,
  "supports":[...],
  "source":{...}
}
```

Supports may initially be simple posts. Railings can be deferred unless they materially affect the LEGO result.

### 6. Exterior stairs

Minimum viable stair description:

```json
{
  "id":"stair_left",
  "type":"stair_run",
  "start":{"x":...,"y":...,"z":...},
  "end":{"x":...,"y":...,"z":...},
  "width":...,
  "source":{...}
}
```

The scene contract should support more than one run so an L-shaped stair is not forced into one block.

### 7. Facade equipment / non-opening observations

Add semantic scene observations for items that matter to interpretation but are not wall holes:

- utility_box
- pipe
- gutter/downspout
- vent
- antenna
- temporary_object

These do not necessarily need LEGO geometry. Their primary purpose is preventing misclassification as doors/windows and preserving scene understanding.

### 8. Occlusion and building boundaries

Record which facade spans are visible/unknown and why.

Example:

```json
{
  "facade":"rear",
  "visibility":[
    {"from":0.0,"to":4.7,"state":"occluded","by":"neighbor_building"},
    {"from":4.7,"to":10.0,"state":"visible"}
  ]
}
```

Likewise, scene analysis should identify the actual end/corner of the target building before assigning openings to it.

## M0 projection rules

Projection from ArchitecturalScene v0.2 to BuildingModel 0.1 should:

1. keep only supported rectangular building volumes, openings and flat/gable roofs;
2. preserve dimensions/provenance that are representable;
3. emit blockers/warnings for terrain slope, chimneys, platforms, stairs and other unsupported geometry;
4. never create an opening in an occluded/unknown facade span;
5. never turn a terrace/stair into a solid volume to achieve buildability;
6. expose information loss to the user before construction.

## Regression expectations for the current house

The reference scene should eventually encode at least:

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

## Non-goals for v0.2

- full photogrammetric mesh reconstruction;
- arbitrary curved/free-form architecture;
- decorative brick-by-brick facade modeling;
- exact terrain mesh;
- automatic certainty from a single ambiguous photo.

## Implementation sequence

1. Define Pydantic scene contracts in a new `brickhouse.scene` package without changing BuildingModel 0.1.
2. Add validation rules for unique IDs, references, evidence ranges and facade visibility.
3. Add an explicit scene -> BuildingModel 0.1 projection with structured warnings/blockers.
4. Add regression fixtures based on the real-house observations (derived facts only; do not commit the source photos).
5. Update external-analysis prompts to target ArchitecturalScene only after the schema/projection path is stable.
6. Extend the LEGO engine incrementally: chimney first, then platform/supports/stairs, then terrain-aware placement/visualization.
