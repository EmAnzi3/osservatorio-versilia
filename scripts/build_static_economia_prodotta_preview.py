#!/usr/bin/env python3
"""Build preview v1.34.0 inserendo Economia prodotta nel builder corrente.

La PR resta in draft: questo wrapper aggancia il materializer solo nella build di
review. L'hook permanente del builder di produzione viene fatto dopo approvazione
visiva dell'artifact, evitando di rendere merge-ready una UI non ancora approvata.

Il builder corrente di main contiene byte legacy non UTF-8 ma viene eseguito
correttamente dal workflow Pages. La patch di preview opera quindi sui byte grezzi:
conserva esattamente il contenuto baseline e inserisce soltanto una riga ASCII.
"""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "scripts" / "build_static_brand_impl.py"
ENTRY = ROOT / "scripts" / "build_static_brand.py"

NEEDLE = b'    runpy.run_path(str(ROOT / "scripts" / "materialize_fragilita_release.py"), run_name="__main__")\n'
INJECTION = NEEDLE + b'    runpy.run_path(str(ROOT / "scripts" / "materialize_economia_prodotta_release.py"), run_name="__main__")\n'
MARKER = b"materialize_economia_prodotta_release.py"


def main() -> None:
    source = IMPL.read_bytes()
    if MARKER not in source:
        if source.count(NEEDLE) != 1:
            raise RuntimeError("Hook fragilità del builder non trovato in modo univoco")
        IMPL.write_bytes(source.replace(NEEDLE, INJECTION, 1))
    runpy.run_path(str(ENTRY), run_name="__main__")


if __name__ == "__main__":
    main()
