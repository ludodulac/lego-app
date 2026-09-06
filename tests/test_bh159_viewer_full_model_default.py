from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "frontend" / "viewer.js"


def test_viewer_opens_completed_model_before_instruction_steps() -> None:
    source = VIEWER.read_text(encoding="utf-8")
    configure = source.split("function configureAssembly", 1)[1].split("function showAssemblyStep", 1)[0]
    assert "showFullModel();" in configure
    assert "showAssemblyStep(0);" not in configure
    assert "assemblyRange.value='0'" in configure
    assert "assemblyPrev.disabled=true" in configure


def test_instruction_controls_still_enter_and_leave_step_mode() -> None:
    source = VIEWER.read_text(encoding="utf-8")
    assert "assemblyRange.addEventListener('input',()=>showAssemblyStep" in source
    assert "assemblyNext.addEventListener('click',()=>showAssemblyStep((currentAssemblyStep??-1)+1))" in source
    assert "assemblyFull.addEventListener('click',showFullModel)" in source
    assert "assemblyTitle.textContent='Modèle complet'" in source
