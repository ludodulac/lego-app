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
    assert "Plusieurs photos peuvent volontairement partager le même libellé de zone" in simple
    assert "le libellé ne doit jamais forcer une interprétation contraire à l’image" in simple
    assert "guided_base_zones" in simple
    assert "slot_view_index: item.slot_view_index" in simple


def test_total_photo_limit_rejects_overflow_instead_of_silently_truncating_package() -> None:
    simple = read("photo-simple.js")

    assert "const allRecords = [...selectedSlotRecords(), ...selectedExtraRecords()]" in simple
    assert "if (allRecords.length > MAX_TOTAL_PHOTOS)" in simple
    assert "Vous en avez sélectionné ${allRecords.length}" in simple
    assert "const records = allRecords" in simple
