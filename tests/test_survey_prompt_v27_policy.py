from pathlib import Path


def test_v27_keeps_representation_policy_fields() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    for field in ("preserve_nominal_materials","preserve_opening_composition","preserve_architectural_details","reproduce_weathering","reproduce_temporary_objects"):
        assert field in source
