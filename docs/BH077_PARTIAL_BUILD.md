# BH-077 — conservative partial LEGO build

BrickHouse may build the metrically resolved envelope and openings of an `ArchitecturalScene` before every architectural unknown is resolved.

The partial build is intentionally asymmetric with the strict scene build:

- known volume dimensions and known openings may become LEGO geometry;
- an unresolved roof is omitted rather than guessed;
- unresolved exterior topology (terrace/stair junctions, etc.) remains outside the partial build until its metric connection is resolved;
- omitted architecture is reported through fidelity issues;
- the resulting `BrickModel`, BOM and `AssemblyPlan` are still generated from exactly the same placements, so the viewer can reveal the trustworthy subset step by step.

The strict `brickhouse-scene-build` behavior remains the default. `--allow-partial` opts into this conservative preview path.
