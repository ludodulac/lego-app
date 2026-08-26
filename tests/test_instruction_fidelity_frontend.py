import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _summarize(bundle: dict) -> dict | None:
    payload = json.dumps(bundle, ensure_ascii=False)
    script = f"""
import {{ instructionFidelitySummary }} from './frontend/instruction-fidelity.js';
const bundle = {payload};
process.stdout.write(JSON.stringify(instructionFidelitySummary(bundle)));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_partial_notice_names_every_omitted_architectural_object() -> None:
    summary = _summarize(
        {
            "fidelity_issues": [
                {
                    "code": "partial_scene_object_omitted",
                    "severity": "warning",
                    "object_id": "roof_main",
                    "message": "roof_main n’est pas encore construit : toiture non résolue.",
                },
                {
                    "code": "partial_scene_object_omitted",
                    "severity": "warning",
                    "object_id": "exterior_stair",
                    "message": "exterior_stair n’est pas encore construit : raccord métrique non résolu.",
                },
            ]
        }
    )

    assert summary is not None
    assert summary["partial"] is True
    assert "provisoire" in summary["title"].lower()
    assert [item["object_id"] for item in summary["omitted"]] == [
        "roof_main",
        "exterior_stair",
    ]


def test_complete_notice_has_no_partial_banner() -> None:
    assert _summarize({"fidelity_issues": []}) is None
