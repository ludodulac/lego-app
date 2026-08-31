from pathlib import Path

from brickhouse.pipeline import build_parser


def test_pipeline_cli_ldraw_root_is_optional():
    args = build_parser().parse_args(["input.json", "output.json"])
    assert args.ldraw_root is None


def test_pipeline_cli_accepts_ldraw_root_path():
    args = build_parser().parse_args(
        ["input.json", "output.json", "--ldraw-root", "vendor/ldraw"]
    )
    assert args.ldraw_root == Path("vendor/ldraw")
