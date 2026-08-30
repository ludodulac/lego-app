import json
import subprocess
from pathlib import Path

from brickhouse.survey import ArchitecturalSurvey

ROOT = Path(__file__).resolve().parents[1]
NORMALIZER = ROOT / "frontend" / "survey-neutral-normalize.js"


def run_normalizer(value: dict) -> dict:
    script = f"""
import {{ normalizeNeutralSurvey }} from {json.dumps(NORMALIZER.as_uri())};
const input = JSON.parse(process.argv[1]);
process.stdout.write(JSON.stringify(normalizeNeutralSurvey(input)));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script, json.dumps(value)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def second_neutral_chat_shape() -> dict:
    return {
        "schema_version": "0.1",
        "name": "neutral-survey",
        "canonical_frame": {
            "front": "front",
            "view": "front_view_left_to_right",
            "y_direction": "front_to_rear",
            "z_direction": "bottom_to_top",
        },
        "photos": [
            {
                "photo_index": 1,
                "capture_role": "facade_view",
                "facade": "front",
                "description": "Front facade is visible.",
                "source": {"kind": "observed", "confidence": 1.0},
                "image_left_maps_to_facade_offset": "low",
                "user_note": None,
            }
        ],
        "known_measurements": [],
        "observations": [
            {
                "id": "front-opening-1",
                "kind": "opening",
                "facade": "front",
                "certainty": "certain",
                "statement": "One physical opening is visible.",
                "evidence": [{"photo_index": 1, "observation": "Visible opening."}],
                "attributes": {
                    "physical_object_count": 1,
                    "semantic_type": "opening",
                    "attribute_certainty": {
                        "physical_object_count": "certain",
                        "semantic_type": "certain",
                    },
                },
                "appearance": None,
                "opening_visual": None,
            }
        ],
        "relations": [],
        "representation_policy": {
            "preserve_nominal_materials": True,
            "preserve_opening_composition": True,
            "preserve_architectural_details": True,
            "reproduce_weathering": False,
            "reproduce_temporary_objects": False,
        },
        "notes": None,
    }


def test_second_neutral_chat_shape_normalizes_to_canonical_backend_contract() -> None:
    result = run_normalizer(second_neutral_chat_shape())
    assert result["issue"] is None
    assert result["changed"] is True

    normalized = result["value"]
    assert normalized["id"] == "survey-neutral-survey-v01"
    assert normalized["canonical_frame"] == {
        "front_facade": "front",
        "x_direction": "front_view_left_to_right",
        "y_direction": "front_to_rear",
        "z_direction": "bottom_to_top",
    }
    observation = normalized["observations"][0]
    assert "attribute_certainty" not in observation["attributes"]
    assert observation["attribute_certainty"] == {"physical_object_count": "certain"}
    assert "semantic_type" not in observation["attributes"]

    survey = ArchitecturalSurvey.model_validate(normalized)
    assert survey.id == "survey-neutral-survey-v01"
    assert survey.observations[0].certainty_for_attribute("physical_object_count").value == "certain"


def test_conflicting_attribute_certainty_is_rejected_not_guessed() -> None:
    raw = second_neutral_chat_shape()
    raw["observations"][0]["attribute_certainty"] = {"physical_object_count": "plausible"}
    result = run_normalizer(raw)
    assert result["changed"] is False
    assert "contradictoires" in result["issue"]


def test_non_survey_payload_is_not_rewritten() -> None:
    payload = {"schema_version": "0.2", "scene": {}}
    result = run_normalizer(payload)
    assert result == {"value": payload, "changed": False, "issue": None}


def test_normalizer_is_loaded_before_primary_survey_importer() -> None:
    legacy_importer = (ROOT / "frontend" / "external-bundle-import.js").read_text(encoding="utf-8")
    photo_page = (ROOT / "frontend" / "photo.html").read_text(encoding="utf-8")
    assert "import './survey-neutral-normalize.js';" in legacy_importer
    assert photo_page.index("external-bundle-import.js") < photo_page.index("survey-import.js")
