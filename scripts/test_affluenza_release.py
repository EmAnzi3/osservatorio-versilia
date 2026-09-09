#!/usr/bin/env python3
"""Contratto sorgente/runtime per Affluenza al voto v1.32.0."""
from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = tuple(ROOT / "data" / "affluenza" / f"archive-v2-{index:02d}.b64" for index in range(4))


def main() -> None:
    page = ROOT / "confronta" / "comunita" / "affluenza" / "index.html"
    css = ROOT / "assets" / "affluenza-v3.css"
    runtime = ROOT / "assets" / "affluenza-v3.js"
    hotfix = ROOT / "assets" / "affluenza-hotfix.js"
    for path in (page, css, runtime, hotfix, *CHUNKS):
        assert path.is_file() and path.stat().st_size > 0, path

    html = page.read_text(encoding="utf-8")
    assert "Affluenza al voto" in html and "turnout-app" in html
    assert "affluenza-v3.css" in html and "affluenza-hotfix.js" in html and "affluenza-v3.js" in html
    assert html.index("affluenza-hotfix.js") < html.index("affluenza-v3.js")

    patch = hotfix.read_text(encoding="utf-8")
    assert "data/affluenza/archive-00.b64" in patch
    for index in range(4):
        assert f"archive-v2-{index:02d}.b64" in patch

    encoded = "".join(chunk.read_text(encoding="utf-8").strip() for chunk in CHUNKS)
    payload = json.loads(gzip.decompress(base64.b64decode(encoded, validate=True)).decode("utf-8"))

    assert len(payload.get("towns", [])) == 7
    families = payload.get("families", {})
    expected = {"politiche_camera", "europee", "regionali_toscana", "referendum"}
    assert set(families) == expected
    assert sum(len(families[key].get("events", [])) for key in expected) == 71
    communal = payload.get("communal", [])
    assert len(communal) == 7
    assert sum(len(entry.get("history", [])) for entry in communal) == 53
    assert len(payload.get("provinceReferendumContext", [])) == 53

    viareggio = next(entry for entry in communal if entry.get("town") == "Viareggio")["latest"]
    assert viareggio["electors"] == 52432 and viareggio["voters"] == 28841
    assert round(viareggio["turnout"], 2) == 55.01

    print("Affluenza runtime contract: OK · 71 consultazioni · 53 Comunali · 53 contesti provinciali")


if __name__ == "__main__":
    main()
