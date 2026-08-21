# BH-074 — Survey semantic validation

ArchitecturalSurvey is an evidence layer, not a geometry proposal. The following invariants are enforced before Survey→Scene fusion:

- a semantic type explicitly confirmed by the user must not be weakened by visual ambiguity; only metric geometry may remain inferred;
- opening observations can carry `semantic_role` and `confirmed_by_user` independently from visual composition;
- an opening whose ownership by the target building is not proven must remain `unproven` and must never become target geometry without new evidence;
- gable-end terminology must distinguish `gable_end`, `rake_edge` and `eave`; a front gable facade must not be described as having a horizontal front eave across the facade;
- workshop identity and glazing subtype are separate: a workshop window may use glass blocks;
- malformed/truncated JSON must fail before any scene fusion.

The real-house photos 1 and 2 are the regression reference for these rules.
