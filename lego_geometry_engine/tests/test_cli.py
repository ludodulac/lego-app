from pathlib import Path
import json
from lego_geometry_engine.cli import main


def test_cli_json_report(tmp_path, capsys):
    fixture = Path(__file__).parent / "fixtures" / "ldraw"
    assembly = tmp_path / "assembly.json"
    assembly.write_text(json.dumps({"parts": [
        {"instance_id": "a", "part_id": "3005", "position": [0, 0, 0]},
        {"instance_id": "b", "part_id": "3005", "position": [40, 0, 0]},
    ]}))
    assert main(["analyze", str(assembly), "--ldraw-root", str(fixture)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["valid"] is True
