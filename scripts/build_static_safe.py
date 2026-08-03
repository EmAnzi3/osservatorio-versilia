#!/usr/bin/env python3
"""Build wrapper that localizes legacy asset URLs inside the private output."""

from __future__ import annotations

import json

import build_static as build

_original_copy_source_tree = build.copy_source_tree


def copy_source_tree_with_local_assets() -> None:
    _original_copy_source_tree()
    data_path = build.DIST / "data" / "site-data.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    crest_files = {
        "Camaiore": "camaiore.svg",
        "Forte dei Marmi": "forte-dei-marmi.svg",
        "Massarosa": "massarosa.png",
        "Pietrasanta": "pietrasanta.svg",
        "Seravezza": "seravezza.png",
        "Stazzema": "stazzema.webp",
        "Viareggio": "viareggio.svg",
    }
    data["crests"] = {
        town: f"/crests/{filename}" for town, filename in crest_files.items()
    }
    data_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


build.copy_source_tree = copy_source_tree_with_local_assets

if __name__ == "__main__":
    build.main()
