"""Shared prompt helpers for bounded architectural landmark proposals."""
from __future__ import annotations

from brickhouse.survey import ArchitecturalSurvey


LANDMARK_INSTRUCTIONS = """
In addition to the semantic architectural proposal, populate landmark_proposals with only a small set of high-value physical architectural points that are genuinely visible in at least two supplied views. Aim for 8-15 cross-view candidates when the photographs support them; never invent points merely to reach a count.

Landmark rules:
- physical_landmark_id names one exact physical point, not a feature class. Good examples are one specified window corner, a wall/landing intersection, one volume corner, one railing endpoint, or one clearly identifiable tread/landing corner.
- Assign the same physical_landmark_id across views only when physical identity is defensible from the building geometry and surrounding context. Visual resemblance alone is insufficient.
- Give each occurrence its original-photo coordinate as x/width and y/height in [0,1]. Do not perspective-rectify these coordinates.
- Use status AMBIGUOUS or REJECTED and state why whenever identity or point localization is doubtful. Those proposals are evidence for rejection, not usable geometry.
- Confidence must cover both visibility and localization, and should fall when vegetation, crop boundaries, shadows, repeated windows/steps, blur or occlusion make the exact point uncertain.
- The provider proposes identity and approximate localization only. Downstream deterministic validation decides whether a proposal becomes an ArchitecturalLandmarkTrack.
- provider must identify the active provider name given in the user prompt.
""".strip()


def survey_landmark_context(survey: ArchitecturalSurvey | None) -> str:
    """Return a compact immutable Survey index for optional landmark provenance binding."""
    if survey is None:
        return (
            "No accepted ArchitecturalSurvey was supplied to this analysis. Leave survey_observation_id null; "
            "survey_object_hint may describe the physical object without inventing an ID."
        )
    rows = []
    for observation in survey.observations:
        photos = ",".join(str(item.photo_index) for item in observation.evidence)
        rows.append(
            f"- {observation.id} | kind={observation.kind.value} | accepted_evidence_photos=[{photos}] | {observation.statement}"
        )
    return (
        "Accepted ArchitecturalSurvey is read-only. Bind survey_observation_id only when the physical object is defensibly "
        "the same observation. If it is visible in a new photo absent from accepted_evidence_photos, keep that exact Survey ID "
        "and let downstream validation represent the extra photo as a new evidence candidate; never pretend the accepted Survey "
        "already contains that evidence.\n" + "\n".join(rows)
    )
