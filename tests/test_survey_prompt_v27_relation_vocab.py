from pathlib import Path


def test_v27_keeps_relation_vocabulary() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    for value in ("connects_to","adjacent_to","aligned_with","supports","part_of","same_physical_object"):
        assert value in source
