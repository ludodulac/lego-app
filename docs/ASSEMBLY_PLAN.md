# AssemblyPlan v0.1

`AssemblyPlan` is the first deterministic build-order contract derived from `BrickModel`.

M0 deliberately uses a simple rule: wall placements are grouped by increasing `z_plates`, then roof placements are grouped by increasing `z_plates`. Every step stores only stable `placement_id` references; the geometry remains in `BrickModel`.

## Guarantees

- contiguous step sequence numbers starting at 1;
- stable step ids (`step-0001`, ...);
- every BrickModel placement appears exactly once;
- walls are completed before the roof starts;
- ordering inside a step is deterministic.

## Limitation

This is not yet a structural or ergonomic instruction solver. It does not prove that every individual placement is physically supported at the moment it appears, nor does it optimize step sizes for human builders. It establishes the stable contract needed for viewer playback and later instruction optimization.
