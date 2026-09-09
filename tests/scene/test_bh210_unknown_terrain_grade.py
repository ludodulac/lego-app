from brickhouse.scene.models import GradeProfile


def test_grade_profile_preserves_unresolved_metric_endpoints() -> None:
    profile = GradeProfile.model_validate(
        {
            "facade": "right",
            "start_elevation": None,
            "end_elevation": None,
            "outward_extent": None,
            "source": {"kind": "observed", "confidence": 0.86},
            "evidence": [
                {
                    "photo_index": 2,
                    "observation": "Grade direction is visible but its metric amplitude is not calibrated.",
                }
            ],
        }
    )

    assert profile.start_elevation is None
    assert profile.end_elevation is None


def test_grade_profile_still_preserves_known_metric_endpoints() -> None:
    profile = GradeProfile.model_validate(
        {
            "facade": "right",
            "start_elevation": 0.15,
            "end_elevation": 1.1,
            "outward_extent": 2.0,
            "source": {"kind": "inferred", "confidence": 0.7},
            "evidence": [],
        }
    )

    assert profile.start_elevation == 0.15
    assert profile.end_elevation == 1.1
    assert profile.outward_extent == 2.0
