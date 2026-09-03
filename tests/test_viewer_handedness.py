from pathlib import Path


VIEWER = Path("frontend/viewer.js")
DOC = Path("docs/VIEWER.md")


def test_viewer_preserves_canonical_front_facade_left_to_right_handedness() -> None:
    js = VIEWER.read_text(encoding="utf-8")

    # BrickHouse model y is front->rear while Three.js world y is vertical.
    # The display-only z reflection maps (x, y, z) -> (x, z, -y)
    # without changing model x, so low front-facade x remains viewer-left.
    assert "modelGroup.scale.z=-1" in js
    assert "front:new THREE.Vector3(0,0,1)" in js
    assert "model x = left→right on the front facade" in js
    assert "Mapping model (x,y,z) -> world (x,z,-y)" in js


def test_viewer_handedness_is_documented_as_display_only() -> None:
    doc = DOC.read_text(encoding="utf-8")

    assert "engine Y maps to **negative** Three.js Z" in doc
    assert "presentation-only" in doc
    assert "must never rewrite BrickModel placements" in doc


def test_viewer_frames_rendered_geometry_not_architectural_dimensions() -> None:
    js = VIEWER.read_text(encoding="utf-8")

    assert "new THREE.Box3().setFromObject(modelGroup)" in js
    assert "function frameModel(){frameCanonicalView('perspective');}" in js
