#!/usr/bin/env python3
"""Materializza la correzione degli export CSV e PDF della v1.6.1."""
from __future__ import annotations

import base64
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAYLOADS = {
    'assets/app-parts/02.txt': (
        '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'
        'sDyYtJmjLxbg0bvZx+dP+dDg/zDr74g='
    ),
    'assets/ux-history.js': (
        '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'
    ),
    'assets/ux-experiment.css': (
        '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'
    ),
}


def materialize() -> None:
    for relative, chunks in PAYLOADS.items():
        target = ROOT / relative
        content = zlib.decompress(base64.b64decode("".join(chunks)))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    parts = sorted((ROOT / "assets" / "app-parts").glob("*.txt"))
    if not parts:
        raise SystemExit("Moduli dell’applicazione non trovati")
    bundle = "".join(path.read_text(encoding="utf-8") for path in parts)
    (ROOT / "assets" / "app-bundle.js").write_text(bundle, encoding="utf-8")

    workflow = ROOT / ".github" / "workflows" / "pages.yml"
    text = workflow.read_text(encoding="utf-8")
    text = text.replace(
        "python -m pip install playwright\n",
        "python -m pip install playwright pypdf\n",
        1,
    )
    marker = "      - name: Configure Pages\n"
    step = (
        "      - name: Run export checks\n"
        "        run: python scripts/test_exports_v161.py\n\n"
    )
    if "Run export checks" not in text:
        if marker not in text:
            raise SystemExit("Punto di inserimento dei test export non trovato")
        text = text.replace(marker, step + marker, 1)
    workflow.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    materialize()
    print("Export CSV e PDF v1.6.1 materializzati.")
