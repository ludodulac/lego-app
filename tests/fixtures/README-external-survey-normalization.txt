Regression source: real external BrickHouse Survey output observed 2026-08-25.
The external model produced three conservative shape drifts that must not force a user rerun:
1) representation_policy as a list of known field names rather than the required object;
2) semantic_type="opening" paired with attribute_certainty.semantic_type="unproven";
3) facade_horizontal_rank / facade_vertical_rank as qualitative "low"/"high" labels.
The executable regression is tests/survey/test_external_shape_normalization.py.
No benchmark-specific geometry is encoded here.