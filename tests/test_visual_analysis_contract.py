import pytest
from pydantic import ValidationError

from brickhouse.visual_analysis import IndependentVisualAnalysis


def _payload() -> dict:
    return {
        "schema_version": "independent-visual-analysis-0.1",
        "photo_analyses": [
            {
                "photo_index": 1,
                "observations": [
                    {
                        "id": "deck-post",
                        "category": "support",
                        "status": "observed",
                        "statement": "A vertical timber post is directly visible below the deck.",
                        "confidence": 0.99,
                        "evidence": [{"photo_index": 1, "observation": "Visible post below deck."}],
                    }
                ],
            },
            {"photo_index": 2, "observations": []},
        ],
        "consolidated_objects": [
            {
                "id": "timber-deck-support-system",
                "category": "support",
                "status": "observed",
                "statement": "The deck has visible vertical support posts; exact count and coordinates remain unknown.",
                "confidence": 0.98,
                "photo_indices": [1],
                "components": {"vertical_posts": "observed", "exact_coordinates": "unknown"},
            }
        ],
        "spatial_relations": [],
        "contradictions": [],
        "unresolved_questions": [
            {"id": "support-count", "question": "How many support posts are present?", "photo_indices": [1]}
        ],
        "comparison_to_current": {},
    }


def test_contract_preserves_observed_feature_without_inventing_metric_geometry() -> None:
    analysis = IndependentVisualAnalysis.model_validate(_payload())
    support = analysis.consolidated_objects[0]
    assert support.components["vertical_posts"] == "observed"
    assert support.components["exact_coordinates"] == "unknown"


def test_cold_photo_phase_cannot_cite_a_different_photo() -> None:
    payload = _payload()
    payload["photo_analyses"][0]["observations"][0]["evidence"][0]["photo_index"] = 2
    with pytest.raises(ValidationError, match="cold per-photo observations"):
        IndependentVisualAnalysis.model_validate(payload)


def test_consolidation_cannot_reference_an_unknown_photo() -> None:
    payload = _payload()
    payload["consolidated_objects"][0]["photo_indices"] = [99]
    with pytest.raises(ValidationError, match="unknown photo"):
        IndependentVisualAnalysis.model_validate(payload)
