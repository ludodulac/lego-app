from brickhouse.scene.platform_structure import PlatformStructureObservation


def test_observed_deck_structure_can_stay_non_metric() -> None:
    post = PlatformStructureObservation.model_validate(
        {
            "id": "timber-deck-posts",
            "platform_id": "timber_deck",
            "kind": "vertical_post",
            "statement": "Vertical timber support posts are directly visible below the deck; exact count and coordinates remain unresolved.",
            "count": None,
            "source": {"kind": "observed", "confidence": 0.98},
            "evidence": [{"photo_index": 3, "observation": "At least one vertical post is visibly supporting the raised deck."}],
        }
    )
    assert post.count is None
    assert not hasattr(post, "position")


def test_diagonal_bracing_is_a_first_class_observed_component() -> None:
    brace = PlatformStructureObservation.model_validate(
        {
            "id": "timber-deck-bracing",
            "platform_id": "timber_deck",
            "kind": "diagonal_brace",
            "statement": "Diagonal timber bracing is directly visible below the deck; exact member count and endpoints remain unresolved.",
            "source": {"kind": "observed", "confidence": 0.96},
            "evidence": [{"photo_index": 3, "observation": "Diagonal brace members are visible beneath the deck edge."}],
        }
    )
    assert brace.kind.value == "diagonal_brace"
    assert brace.count is None
