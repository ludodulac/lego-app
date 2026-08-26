# BrickHouse photo reasoning loop

BrickHouse must not jump directly from pixels to metric geometry or LEGO. The analysis loop is deliberately staged:

1. **Observe one photo at a time.** Inventory visible objects, boundaries, openings, materials, level changes, roof edges, exterior structures, equipment, context and occlusions without completing hidden geometry.
2. **Record the questions raised by those observations.** Examples: whether two visible edges belong to the same physical object, whether an exterior stair continues behind an occlusion, which volume owns a platform, or which roof direction is actually supported.
3. **Keep hypotheses separate from facts.** A plausible answer may guide the next comparison, but it must not silently become an `ArchitecturalSurvey` fact or a metric primitive.
4. **Map only sufficiently supported facts to simple architectural primitives.** Start with volumes, planes, openings, platforms, stair runs and other conservative geometry. Unknown dimensions and hidden connections stay unknown.
5. **Repeat for every view and fuse across photos.** Reuse stable object identities, link independent evidence, refine or invalidate earlier hypotheses, and avoid duplicate objects when several views show the same physical thing.
6. **Prefer information gain over generic questioning.** Ask the user for another photo, a measurement or a semantic confirmation only when it can resolve a blocker or materially improve the downstream LEGO model.
7. **Convert only validated geometry to LEGO.** The deterministic LEGO stage chooses supported catalog pieces, BOM entries and assembly steps. Decorative fidelity such as gutters, trims and surrounds is added incrementally only when catalog-backed and geometrically justified.

`SurveyReasoningState` is the machine-readable layer for step 2/3. It wraps the factual `ArchitecturalSurvey` with unresolved `SurveyOpenQuestion` objects and candidate `SurveyHypothesis` values so reasoning can persist without contaminating observed facts.
