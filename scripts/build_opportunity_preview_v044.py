#!/usr/bin/env python3
"""Renderer v0.4.4: evidenzia le opportunità rilevate negli ultimi 7 giorni."""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import build_opportunity_preview_v04 as v04
import build_opportunity_preview_v043 as base

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "reports" / "runtime" / "opportunities-v04.json"
DEFAULT_DIST = ROOT / "dist"
TARGET_ROUTE = "opportunita-preview"

_ORIGINAL_LIFECYCLE_CARD = v04.lifecycle_card
_source_options = base._source_options


def _card_with_new_badge(item: dict) -> str:
    text = _ORIGINAL_LIFECYCLE_CARD(item)
    if not bool(item.get("is_new")):
        return text
    text = text.replace(
        '<article class="op-card"',
        '<article class="op-card is-new" data-new="true"',
        1,
    )
    text = text.replace(
        '<div class="op-card-heading">',
        '<div class="op-card-heading"><span class="op-new-badge" aria-label="Nuova opportunità">Nuova</span>',
        1,
    )
    return text


def build(payload_path: Path, dist: Path) -> Path:
    previous_card = v04.lifecycle_card
    previous_route = v04.TARGET_ROUTE
    v04.lifecycle_card = _card_with_new_badge
    v04.TARGET_ROUTE = TARGET_ROUTE
    try:
        target = base.build(payload_path, dist)
    finally:
        v04.lifecycle_card = previous_card
        v04.TARGET_ROUTE = previous_route

    assets = dist / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "assets" / "opportunity-preview-v044.css", assets / "opportunity-preview-v044.css")

    text = target.read_text(encoding="utf-8")
    text = text.replace("v0.4.3", "v0.4.4")
    if "opportunity-preview-v044.css" not in text:
        text = text.replace(
            "</head>",
            '  <link rel="stylesheet" href="../assets/opportunity-preview-v044.css">\n</head>',
            1,
        )
    target.write_text(text, encoding="utf-8")

    check = target.read_text(encoding="utf-8")
    if "Anteprima v0.4.4" not in check:
        raise SystemExit("Preview v0.4.4 non materializzata correttamente")
    expected_new = sum(bool(x.get("is_new")) for x in base.json.loads(payload_path.read_text(encoding="utf-8")).get("opportunities") or [])
    actual_new = len(re.findall(r'class="op-new-badge"', check))
    if actual_new != expected_new:
        raise SystemExit(f"Badge Nuova incoerenti: HTML={actual_new} payload={expected_new}")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    args = parser.parse_args()
    print(f"Preview opportunità v0.4.4 materializzata: {build(args.data, args.dist)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
