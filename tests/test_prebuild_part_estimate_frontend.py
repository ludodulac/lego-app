from pathlib import Path


HTML = Path("frontend/configurator.html")
JS = Path("frontend/configurator.js")


def test_configurator_exposes_prebuild_part_estimate() -> None:
    html = HTML.read_text(encoding="utf-8")
    source = JS.read_text(encoding="utf-8")

    assert 'id="part-estimate-summary"' in html
    assert "async function estimatePartCount(model)" in source
    assert "await estimatePartCount(model)" in source
    assert "payload?.bom?.total_parts" in source
    assert "payload?.bom?.unique_part_types" in source
    assert "Estimation déterministe" in source


def test_prebuild_estimate_uses_real_build_pipeline_without_persisting_export() -> None:
    source = JS.read_text(encoding="utf-8")
    estimate = source.split("async function estimatePartCount(model)", 1)[1].split(
        "form.addEventListener", 1
    )[0]

    assert "`${base}/api/v1/build`" in estimate
    assert "front_width_studs:studs" in estimate
    assert "brickhouse.pendingExport" not in estimate
    assert "heuristique de surface" in estimate


def test_changing_named_size_profile_recomputes_estimate() -> None:
    source = JS.read_text(encoding="utf-8")

    assert "document.querySelector('#studs').addEventListener('change'" in source
    assert "if(currentModel)estimatePartCount(currentModel)" in source


def test_estimate_errors_are_rendered_as_text_not_api_html() -> None:
    source = JS.read_text(encoding="utf-8")

    assert "function setEstimateText(message)" in source
    assert "p.textContent=message" in source
    assert "setEstimateText(`Estimation indisponible : ${error.message}`)" in source
