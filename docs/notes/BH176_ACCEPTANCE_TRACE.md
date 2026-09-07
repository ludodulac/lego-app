# BH-176 acceptance trace

Issue #546 acceptance is mapped as follows:

- production plan before infill: `brickhouse.pipeline._prepare_opening_shell` + plan-before-infill behavioral test;
- semantic preservation: plan reservation stores `architectural_type` and never mutates BuildingModel/Scene;
- unsupported representation diagnostics: `_opening_representation_issues`;
- provenance: `_restore_opening_provenance` keeps `opening_id` on final BrickModel parts;
- no Scene overwrite: `augment_brick_model_with_planned_scene_glazing` excludes planned door/UNKNOWN glazing from the legacy cell path;
- no fake clear glazing: end-to-end tests assert validated frame/pane IDs and reject BRICK_1X1 for planned clear-glazed openings;
- glass blocks: explicitly separated as a dedicated legacy material path pending a later motif slice.
