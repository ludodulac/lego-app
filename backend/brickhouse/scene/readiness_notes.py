"""Non-schema constants for architectural readiness diagnostics."""

STRICT_READINESS_INVARIANT = (
    "Strict LEGO generation requires zero backend architectural readiness blockers."
)
PARTIAL_PIPELINE_POLICY = (
    "Partial generation is explicit diagnostic behavior, never an automatic strict-build fallback."
)
