from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .assembly import analyze_assembly
from .core import instance_from_dict
from .library import LDrawLibrary


def main(argv=None):
    parser = argparse.ArgumentParser(prog="lego-geometry")
    sub = parser.add_subparsers(dest="cmd", required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("assembly")
    analyze.add_argument("--ldraw-root", default=os.getenv("LDRAW_ROOT"))
    ns = parser.parse_args(argv)
    if not ns.ldraw_root:
        parser.error("--ldraw-root or LDRAW_ROOT is required")
    payload = json.loads(Path(ns.assembly).read_text(encoding="utf-8"))
    raw_parts = payload["parts"] if isinstance(payload, dict) else payload
    library = LDrawLibrary(ns.ldraw_root)
    report = analyze_assembly([instance_from_dict(item, library) for item in raw_parts])
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
