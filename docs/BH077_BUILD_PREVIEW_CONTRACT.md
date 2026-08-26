# BH-077 — Progressive LEGO build preview contract

The first user-visible LEGO milestone must not wait for every architectural unknown to be solved.

## Product rule

A partial `ArchitecturalScene` may produce a partial LEGO build when the emitted bricks are supported by resolved scene geometry. Unknown roof direction, hidden junctions, uncertain rail geometry, or unmeasured details stay absent/unresolved; they are never filled merely to make the preview look complete.

## One source, three synchronized outputs

The preview consumes the same `BrickModel` and `AssemblyPlan` used for BOM/instructions. It must never independently invent preview-only bricks.

For assembly step `N`, the visible set is exactly the union of `placement_ids` in steps `1..N`. Therefore:

- step 0 = no bricks;
- step 1 = exactly the first instruction's placements;
- final step = every BrickModel placement exactly once;
- going backward removes only placements introduced after the selected step;
- the highlighted/new set is exactly the selected step's `placement_ids`.

This gives us the first notice primitive now: the same deterministic sequence can drive an interactive build and later a rendered instruction page.

## Precision before completeness

The UI should explicitly distinguish:

1. **built/known** — emitted LEGO parts;
2. **current step** — parts being added now;
3. **unresolved** — architectural regions withheld because the evidence is insufficient.

A withheld region is a successful conservative result, not a generation failure.

## Next implementation slice

Expose a small serializable `BuildPreviewState` derived only from `BrickModel + AssemblyPlan + selected step`, then connect the existing viewer to it. Tests must assert exact placement-set equality at step 0, intermediate steps, and the final step.
