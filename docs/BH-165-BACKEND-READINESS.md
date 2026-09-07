# BH-165 — backend architectural readiness

Strict Scene → LEGO generation must use one backend readiness decision.

`ArchitecturalReadinessReport` aggregates projection blockers, genuinely required inputs and M0 compatibility blockers. It also carries the BH-164 spatial report as diagnostic evidence. Unknown spatial geometry is **not** automatically a blocker: it blocks only when a downstream operation actually requires that metric.

The report is downstream/internal. It does not add fields to ArchitecturalSurvey or ArchitecturalScene and does not change their JSON/PDF contracts.

`evaluate_strict_scene_readiness(scene)` is the shared boundary intended for both Scene validation and strict build. The explicit partial pipeline remains a developer/diagnostic capability and must not become an automatic UI fallback.

CI should assert ready/unready behavior, determinism, non-mutation and validate/build agreement rather than exact source strings.
