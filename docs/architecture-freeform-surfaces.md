# BrickHouse — roadmap for non-orthogonal and freeform architecture

BrickHouse must not permanently equate a building with four vertical facades plus a roof. The current M0 rectangular pipeline is a deliberately conservative implementation stage, not the architectural ontology.

## Invariant

Observed architectural geometry is source truth. LEGO availability and current schema limitations may reduce fidelity in the final build, but they must never rewrite the observed building into a more convenient shape without an explicit fidelity issue.

## Three geometry capability levels

### Level A — rectilinear / current M0

- rectangular volumes;
- vertical cardinal facades;
- rectangular openings;
- flat or gable roofs in the active brick backend;
- Scene-aware terrain, platforms and stair runs.

This remains the regression baseline and should stay deterministic.

### Level B — arbitrary planar architecture

Examples include leaning walls, trapezoidal facades, non-90-degree footprints, faceted roofs and cantilevered planar masses.

Required engine capabilities:

- arbitrary planar polygons rather than four-corner wall assumptions;
- local surface coordinate systems for openings;
- triangulation/partitioning that preserves silhouette and opening topology;
- LEGO approximation with wedges, slopes, SNOT and rotated subassemblies;
- explicit approximation error instead of silent orthogonalization.

### Level C — curved / freeform envelopes

Examples include cylindrical/ovoid towers, doubly-curved shells, concave facades and repeated curved balcony pods.

Required engine capabilities:

- triangulated or parametric architectural surfaces;
- repeated-module recognition where useful;
- surface sampling at an error tolerance linked to LEGO scale;
- curved slopes, wedges, hinges and rotated subassemblies;
- silhouette- and curvature-aware optimization;
- fidelity reporting when a surface cannot be approximated adequately.

## New generic surface layer

`brickhouse.geometry.surfaces` introduces a supplier-independent `ArchitecturalSurfaceModel` with:

- `planar_polygon`;
- `triangulated_mesh`;
- `curved_patch`;
- semantic roles such as wall, roof, glazing and envelope.

The current `BuildingGeometry` can be lifted losslessly into this layer through `surface_model_from_building_geometry()`. This adapter is intentional: existing deterministic M0 behavior remains stable while future reconstruction can target generic surfaces directly.

The next stages should migrate consumers gradually rather than replacing the working rectangular pipeline in one step.

## LEGO piece strategy

`data/processed/piece_types_master.csv` is richer than the hardcoded M0 catalog and already contains standard bricks, plates, tiles, many slope angles, inverted slopes, windows, doors and other part families. Presence in that dataset does **not** mean a part is already geometrically modeled or safe for automatic use.

A piece should pass through capability stages:

1. known in source dataset;
2. canonical BrickHouse identity established;
3. dimensions and connection semantics validated;
4. orientation/footprint behavior modeled;
5. approved for deterministic placement;
6. optionally approved for special techniques (SNOT, hinge, rotated subassembly).

The optimizer must never use a merely-known part as if its connection geometry were validated.

## Single-view vs multi-view

A single photograph can support visible silhouette, repetitions and some topology, but usually cannot establish hidden depth or the back side of a freeform envelope. BrickHouse should preserve that uncertainty.

Multi-view correspondence remains the primary path to metric reconstruction. More exotic geometry increases the importance of overlap between views rather than reducing it.

## Fidelity contract

Every future freeform implementation should keep these outcomes separate:

- observed and represented;
- observed and approximated;
- observed but unsupported;
- occluded/unknown;
- deliberately ignored context.

No unsupported curved or inclined geometry may silently become a rectangular wall merely because the LEGO backend is rectilinear.
