from brickhouse.building.models import OpeningType
from brickhouse.bricks.opening_representation_plan import LEGORepresentationPlan, OpeningRepresentationReservation
from brickhouse.pipeline import _opening_representation_issues


def test_known_window_without_motif_is_blocker_but_unproven_plain_unknown_is_warning():
    plan = LEGORepresentationPlan(
        building_id="severity",
        volume_id="main",
        openings=[
            OpeningRepresentationReservation(
                opening_id="window",
                facade="front",
                architectural_type=OpeningType.WINDOW,
                status="unsupported",
                representation_role="window",
                reason="unsupported topology",
            ),
            OpeningRepresentationReservation(
                opening_id="unknown",
                facade="front",
                architectural_type=OpeningType.UNKNOWN,
                status="unsupported",
                reason="no structured glazing evidence",
            ),
        ],
    )

    issues = _opening_representation_issues(plan, [])
    by_id = {issue.object_id: issue for issue in issues}

    assert by_id["window"].severity == "blocker"
    assert by_id["unknown"].severity == "warning"
