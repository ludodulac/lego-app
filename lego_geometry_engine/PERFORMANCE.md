# Geometry engine performance and correctness gates

Assembly analysis uses a conservative sweep-and-prune broad phase before invoking the exact triangle narrow phase. Each instance's broad-phase bounds are the union of its transformed mesh AABB and transformed connector tolerance envelopes. This preserves connector-only mating candidates even when the solid mesh AABBs are separated.

The broad phase only removes pairs that cannot geometrically touch, overlap, or mate by connector, so it does not change exact `SEPARATED` / `CONTACT` / `COLLISION` classification. AABB filtering is never used as the final collision decision.

The regression suite compares the optimized assembly analyzer with the original pairwise reference on a mixed stack/floating/collision assembly. It also checks touching candidates, Y/Z separation, candidate uniqueness, connector-only candidates, and a sparse 500-part line where no pair reaches narrow phase. Duplicate assembly `instance_id` values are rejected explicitly because support/component topology is keyed by instance identity.

A second optional correctness gate is available for complete official LDraw installations. Set `LDRAW_ROOT` before running `pytest lego_geometry_engine/tests/test_full_ldraw_integration.py`. These tests load the full official `60592` frame and `60601` pane dependency closures, reject false collision at correct co-location, and require a real collision after a 1-LDU penetration. Hermetic CI keeps the reduced attributed fixtures and skips this optional gate when `LDRAW_ROOT` is absent.

The public `analyze_assembly` API uses the optimized analyzer; `check_collision` remains the correctness-first narrow phase. This keeps the optimization replaceable without changing callers.
