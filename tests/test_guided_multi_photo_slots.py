from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def read(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


def test_cardinal_and_detail_groups_accept_multiple_photos_without_collapsing() -> None:
    html = read("photo.html")
    simple = read("photo-simple.js")

    assert html.count('class="guided-photo-input" type="file" accept="image/jpeg,image/png,image/webp" multiple') == 4
    assert html.count('class="detail-photo-input" type="file" accept="image/jpeg,image/png,image/webp" multiple') == 6
    assert "baseSlots.flatMap" in simple
    assert "detailSlots.flatMap" in simple
    assert ".slice(0, MAX_PHOTOS_PER_GROUP)" in simple
    assert "slot_view_index: fileIndex + 1" in simple
    assert "input?.files?.[0]" not in simple


def test_detail_metadata_never_overrides_image_evidence_with_fake_facade() -> None:
    html = read("photo.html")
    simple = read("photo-simple.js")

    assert "Un groupe de détail n’a aucune orientation de façade implicite" in html
    assert "weak_capture_hints_recheck_from_images" in simple
    assert "no_implicit_facade_orientation_use_images_and_user_note_only" in simple
    assert "targeted_detail" in simple
    assert "orientation_authority" in simple
    assert ": 'none'" in simple
    assert "targeted_detail_groups" in simple
    assert "slot_view_index: item.slot_view_index" in simple


def test_structured_capture_has_explicit_group_and_total_limits() -> None:
    simple = read("photo-simple.js")

    assert "const MAX_PHOTOS_PER_GROUP = 4" in simple
    assert "const MAX_TOTAL_PHOTOS = 40" in simple
    assert "const records = selectedPhotoRecords()" in simple
    assert "if (records.length > MAX_TOTAL_PHOTOS)" in simple
    assert "downloadTextFile(INSTRUCTION_FILENAME" in simple
