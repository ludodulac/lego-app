# ArchitecturalSurvey v0.1

BrickHouse now separates **what a photo shows** from **what the building is** and from **how LEGO should represent it**.

## Pipeline

1. Photos + user facts
2. ArchitecturalSurvey v0.1 — per-photo evidence and semantic observations
3. Survey fusion / architectural interpretation
4. ArchitecturalScene v0.2 — coherent building/site geometry
5. LEGO representation policy
6. BrickModel / BOM / instructions

The important invariant is that later simplification must never rewrite earlier understanding.

## Why this layer exists

The real-house regression exposed three classes of failure that cannot be fixed by more metric prompting alone:

- left/right mirroring after a correct visual interpretation;
- treating a facade as a set of generic holes rather than windows/doors with composition, materials and surrounds;
- either ignoring weathering/terrain clues entirely or risking reproducing them literally in the final model.

ArchitecturalSurvey captures these clues before geometry is committed.

## Canonical frame

The canonical front facade defines the building frame once:

- `x`: left to right while standing outside and looking straight at the front facade;
- `y`: front to rear;
- `z`: bottom to top.

Each photo states whether image-left maps to low or high facade offset. This mapping is evidence and must survive downstream transformations. A renderer is not allowed to reverse facade-local offsets silently.

## Observation vs interpretation vs representation

An observation can state that a rendered wall has moisture staining. This can help infer local grade, exposure and material continuity. It does **not** imply the LEGO model should reproduce the stain.

`SurfaceAppearance` therefore separates:

- `base_material`;
- `nominal_color`;
- `finish`;
- observed `weathering`;
- `reproduce_weathering_in_lego`.

The default policy is to preserve nominal architecture and ignore weathering/temporary objects in LEGO unless a future user explicitly asks otherwise.

## Openings are visual components

`OpeningVisualDescription` records evidence such as:

- frame color/material;
- leaf count;
- mullion count;
- glazing character;
- sill;
- surround material/color.

This is intentionally independent from metric opening geometry. A user may confirm that an object is a window without having measured its width, height or offsets.

## Certainty

Every survey observation is one of:

- `certain` — directly visible or explicitly confirmed;
- `plausible` — supported but not uniquely determined;
- `unproven` — candidate interpretation that must not become geometry without new evidence.

## Initial regression fixture

`tests/fixtures/architectural_survey_real_house_photos_1_2.json` encodes only the first two real-house photos. It intentionally includes:

- rendered/off-white nominal facade material;
- weathering understood but excluded from LEGO reproduction;
- front window composition and mineral surrounds;
- low-left front window and glazed lower-right access;
- front gable/roof context and chimney;
- strongly rising road on the right;
- one proven upper-right window;
- near-grade workshop window;
- downspout/pipes/technical equipment;
- strict right-side building boundary.

The remaining photos are deliberately not encoded yet. The survey is meant to grow evidence-first, not to backfill facts from the previous reconstructed scene.
