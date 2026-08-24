from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def read(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


def test_guided_zones_accept_multiple_photos_without_collapsing_to_first_file() -> None:
    html = read("photo.html")
    simple = read("photo-simple.js")

    assert html.count('class="guided-photo-input" type="file" accept="image/jpeg,image/png,image/webp" multiple') == 6
    assert "slots.flatMap" in simple
    assert "const files = [...(input?.files ?? [])]" in simple
    assert "files.map((file, fileIndex)" in simple
    assert "slot_view_index: fileIndex + 1" in simple
    assert "input?.files?.[0]" not in simple


def test_multi_photo_zone_metadata_stays_generic_and_does_not_override_image_evidence() -> None:
    html = read("photo.html")
    simple = read("photo-simple.js")

    assert "Les intitulés des cases sont seulement des repères" in html
    assert "weak_capture_hints_recheck_from_images" in simple
    assert "les libellés des cases sont seulement des repères de capture" in simple.lower()
    assert "guided_base_zones" in simple
    assert "slot_view_index: item.slot_view_index" in simple
    assert "orientation_authority" in simple


def test_total_photo_limit_rejects_overflow_instead_of_silently_truncating_handoff() -> None:
    simple = read("photo-simple.js")

    assert "const records = [...selectedSlotRecords(), ...selectedExtraRecords()]" in simple
    assert "if (records.length > MAX_TOTAL_PHOTOS)" in simple
    assert "Vous en avez sélectionné ${records.length}" in simple
    assert "downloadTextFile(INSTRUCTION_FILENAME" in simple
