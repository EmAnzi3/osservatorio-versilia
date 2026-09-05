#!/usr/bin/env python3
"""Entry point per materializzare l'Atlante Economia nel workspace di release."""
from pathlib import Path

PARTS = Path(__file__).resolve().parent / "economy-atlas-materializer-src"
source = "".join(path.read_text(encoding="utf-8") for path in sorted(PARTS.glob("[0-9][0-9].pyfrag")))
if not source:
    raise RuntimeError("Sorgenti materializzatore Atlante mancanti")
exec(compile(source, str(Path(__file__).resolve()), "exec"), globals(), globals())
