#!/usr/bin/env python3
"""Contratto sorgente per Affluenza al voto v1.32.0."""
from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    page = ROOT / "confronta" / "comunita" / "affluenza" / "index.html"
    css = ROOT / "assets" / "affluenza-v3.css"
    js = ROOT / "assets" / "affluenza-v3.js"
    chunk = ROOT / "data" / "affluenza" / "archive-00.b64"
    for path in (page, css, js, chunk):
        assert path.is_file() and path.stat().st_size > 0, path

    html = page.read_text(encoding="utf-8")
    assert "Affluenza al voto" in html
    assert "turnout-app" in html
    assert "affluenza-v3.css" in html and "affluenza-v3.js" in html
    assert "Radar affluenza" not in html

    runtime = js.read_text(encoding="utf-8")
    assert "Serie storiche comunali" in runtime
    assert "canonicalPoint" in runtime
    assert "chart-tooltip" in runtime
    assert "archive-00.b64" in runtime
    assert "Radar affluenza" not in runtime

    raw = base64.b64decode(chunk.read_text(encoding="utf-8").strip())
    payload = json.loads(gzip.decompress(raw).decode("utf-8"))
    assert len(payload.get("towns", [])) == 7
    assert {"politiche_camera", "europee", "regionali_toscana", "referendum"}.issubset(payload.get("families", {}))
    assert len(payload.get("communal", [])) == 7
    assert payload.get("provinceContext"), "Contesto provinciale referendum assente"
    print("Affluenza source contract: OK")


if __name__ == "__main__":
    main()
