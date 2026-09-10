#!/usr/bin/env python3
"""Build preview v1.34.0 inserendo Economia prodotta nel builder corrente.

La PR resta in draft: questo wrapper aggancia il materializer solo nella build di
review. L'hook permanente del builder di produzione viene fatto dopo approvazione
visiva dell'artifact, evitando di rendere merge-ready una UI non ancora approvata.
"""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "scripts" / "build_static_brand_impl.py"
ENTRY = ROOT / "scripts" / "build_static_brand.py"

NEEDLE = '    runpy.run_path(str(ROOT / "scripts" / "materialize_fragilita_release.py"), run_name="__main__")\n'
INJECTION = NEEDLE + '    runpy.run_path(str(ROOT / "scripts" / "materialize_economia_prodotta_release.py"), run_name="__main__")\n'


def main() -> None:
    source = IMPL.read_text(encoding="utf-8")
    if 'materialize_economia_prodotta_release.py' not in source:
        if source.count(NEEDLE) != 1:
            raise RuntimeError("Hook fragilità del builder non trovato in modo univoco")
        IMPL.write_text(source.replace(NEEDLE, INJECTION, 1), encoding="utf-8")
    runpy.run_path(str(ENTRY), run_name="__main__")


if __name__ == "__main__":
    main()
