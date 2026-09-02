# Architectural LEGO solutions

Status: first deterministic slice for BH-091 / issue #348.

## Boundary

The architectural source remains `ArchitecturalScene`. A new representation-only planning layer may inspect Scene geometry/composition and the explicitly placement-approved LEGO families, rank candidate architectural assemblies, and then let the brick engine fill surrounding wall/detail cells around the chosen representation.

This layer must never rewrite Survey or Scene measurements. A local LEGO dimensional anchor is therefore a property of the LEGO representation, not a corrected architectural measurement.

Target pipeline:

`ArchitecturalScene -> architectural importance/composition -> LEGO solution candidates -> selected local representation anchors -> surrounding wall fill -> architectural details -> fidelity checks -> BrickModel/BOM/AssemblyPlan/viewer`

The existing build path stays in place; this layer is additive.

## First supported family: windows

`backend/brickhouse/bricks/windows.py` already contains three validated frame/pane assemblies and explicit simple/paired/four-pane composition rules. `backend/brickhouse/bricks/piece_capabilities.py` already prevents raw catalogue presence from becoming automatic placement authority. BH-091 therefore starts from those existing contracts instead of creating a broad new piece library.

`backend/brickhouse/bricks/architectural_solutions.py` ranks candidate window solutions using:

- architectural width/height ratio from the higher-level geometry;
- observed leaf/pane composition when present;
- only the validated frame/pane families;
- a bounded local LEGO-grid adjustment cost.

Composition mismatch is intentionally more expensive than a small grid adjustment because recognisable opening composition carries facade identity. Aspect-ratio distortion also has a high weight. The function returns the whole ranked candidate set plus an optional recommendation; it does not mutate the opening, wall or Scene.

## Local anchor rule

A characteristic opening may become a *local LEGO anchor* only when all of these hold:

1. the architectural opening already exists in the validated source;
2. candidate parts are placement-approved for the required construction mode;
3. any departure from the current LEGO raster is explicit, small and bounded;
4. the departure changes only the LEGO representation around the opening;
5. exact or `user_provided` architectural measurements remain unchanged;
6. unsupported composition remains unsupported instead of being invented.

A later integration slice must move/fill wall cells around an accepted anchor and surface the representation loss through fidelity reporting. The present slice deliberately stops before that wall mutation so the contract and scoring can be validated independently first.

## Facade-relative optimisation

Independent per-opening optimisation is not sufficient. The next scoring slice should group openings by facade and add a relative-proportion term so repeated or hierarchical openings remain visually coherent. This comparison must use architectural ratios/proportions, not private-house constants.

## Other architectural families

The repository already has separate implementations for facade surrounds/sills, Scene glazing, roofs, chimneys, platforms/supports, stairs, terrain and wall depth. These should be promoted into architectural-solution families incrementally only when there is a real candidate choice to make and the necessary pieces/techniques are explicitly supported.

Possible later families include roof edges, gutters/downspouts, railings, deck supports, stair details, plinths and material/relief transitions. Plates, tiles, slopes, brackets and SNOT must not become generally selectable merely because they exist in a catalogue; their geometry/orientation/connection semantics must first reach the appropriate capability stage.

## Privacy

Private benchmark photos, Survey, Scene and house-specific dimensions/topology stay outside the repository. Regressions for this layer use generic synthetic openings only.
