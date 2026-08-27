from pathlib import Path


def test_manual_instruction_import_updates_guidance_bundle_without_overwriting_on_invalid_json():
    source = Path("frontend/instruction-guidance.js").read_text(encoding="utf-8")

    assert "fileInput?.addEventListener('change',syncManualBundle,true)" in source
    assert "localStorage.setItem('brickhouse.currentExport',JSON.stringify(bundle))" in source
    assert "if(!bundle?.assembly_plan?.steps?.length||!bundle?.brick_model?.parts?.length)return" in source
    assert "catch{" in source
    assert "queueMicrotask(enhance)" in source
