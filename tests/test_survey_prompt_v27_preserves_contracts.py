from pathlib import Path

PROMPT = Path(__file__).resolve().parents[1] / "frontend" / "brickhouse-survey-prompt.txt"


def test_v27_keeps_core_opening_and_exterior_contracts() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    for token in (
        'physical_object_count:1',
        'facade_horizontal_rank',
        'facade_vertical_rank',
        'attribute_certainty.semantic_type',
        'attributes.supports',
        'building_boundary',
        'connects_to',
        'front_width',
        'canonical_frame',
        'same_physical_object',
    ):
        assert token in source
