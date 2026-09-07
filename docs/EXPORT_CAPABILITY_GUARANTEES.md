# Export capability guarantees

`BrickExportBundle` exposes an additive `capability_summary` for newly generated exports. This summary does not create a new source of architectural truth: Survey remains the semantic authority, Scene remains the metric/spatial authority, and the BrickModel remains a derived LEGO representation.

## What the states mean

- `render_artifact = available`: a BrickModel/export artifact exists in the validated bundle. This does **not** assert that a browser deployment has been exercised.
- `bom = contract_verified`: the BOM belongs to the same building/volume and its total part count matches the BrickModel. This does **not** validate procurement or part/color availability.
- `assembly_plan = contract_verified`: an AssemblyPlan exists and passes its structural/coverage contracts against the BrickModel. This is not a claim of global mechanical stability.
- `instruction_plan = contract_verified`: an InstructionPlan exists and its placement ordering is consistent with the AssemblyPlan.
- `bag_plan = contract_verified`: a BagPlan exists and its placement/step ordering is consistent with the AssemblyPlan.
- `not_available`: the corresponding optional derived artifact was not produced in this bundle.

`fidelity_level` is derived only from `fidelity_issues`: any blocker gives `blocked`; otherwise any warning gives `degraded`; info-only or no issues gives `clear`. It does not replace the detailed fidelity diagnostics.

## Mechanical verification is deliberately separate

`mechanical_verification` defaults to `not_claimed`, even when a BrickModel, AssemblyPlan and instructions all exist. Boldüngo currently has several real deterministic physical checks, but their coverage is not a general mechanical proof. A positive state may therefore be carried only as `verified_in_declared_scope` together with a named validator and explicit scopes supplied by the caller that actually ran that validator.

The capability summary never infers mechanical verification from artifact existence, CI success, absence of fidelity blockers, or assembly-plan coverage.

## Evidence maturity stays outside architectural truth

These concepts must remain distinct:

- **implemented**: code exists;
- **tested**: automated tests exercise a behavior;
- **verified**: a defined runtime/deployment/validator check has actually run for the relevant artifact or scope;
- **validated in real use**: a human or real-world procedure has accepted the result for its intended use.

`contract_verified` in an export means only deterministic contract consistency inside that bundle. It is not synonymous with deployed, mechanically verified, visually accepted, or validated in real use. CI/deployment/human-validation state is operational evidence and must not be written back into Survey or Scene.

## Compatibility

The field is optional in schema `0.1` so historical serialized bundles remain readable. `create_export_bundle()` always fills it for newly generated bundles. If a caller manually supplies a capability summary, bundle validation rejects artifact/fidelity states that disagree with the actual bundle contents.
