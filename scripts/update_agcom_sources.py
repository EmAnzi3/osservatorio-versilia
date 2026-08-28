#!/usr/bin/env python3
"""Sostituisce i riferimenti AGCOM dismessi con le fonti ufficiali attuali.

L'operazione è intenzionalmente idempotente: aggiorna i riferimenti di
navigazione verso maps.agcom.it e registra l'endpoint ArcGIS machine-readable
usato dall'audit primario, senza modificare i valori degli indicatori.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
MONITOR = ROOT / "data" / "source-monitor-state.json"
SNAPSHOTS = ROOT / "data" / "source-snapshots"

LEGACY_URLS = {
    "https://geo.agcom.it/reportistica/ai/ai_251231_260210_comuni.html",
    "https://geo.agcom.it/reportistica/ai/index.html",
}
PUBLIC_MAP_URL = "https://maps.agcom.it/"
MACHINE_DATA_URL = (
    "https://geo.agcom.it/arcgis/sharing/rest/content/items/"
    "25830559c5784c1eb5eb1cf748889f4c/data"
)
PROFILE = "agcom-quarterly"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_legacy(value: Any) -> tuple[Any, int]:
    if isinstance(value, str):
        return (PUBLIC_MAP_URL, 1) if value in LEGACY_URLS else (value, 0)
    if isinstance(value, list):
        changed = 0
        result = []
        for item in value:
            replaced, count = replace_legacy(item)
            result.append(replaced)
            changed += count
        return result, changed
    if isinstance(value, dict):
        changed = 0
        result = {}
        for key, item in value.items():
            new_key = PUBLIC_MAP_URL if key in LEGACY_URLS else key
            if new_key != key:
                changed += 1
            replaced, count = replace_legacy(item)
            result[new_key] = replaced
            changed += count
        return result, changed
    return value, 0


def update_json_file(path: Path) -> int:
    value = load(path)
    replaced, changed = replace_legacy(value)
    if changed:
        save(path, replaced)
    return changed


def update_registry() -> int:
    registry = load(REGISTRY)
    changed = 0
    mapping = registry.setdefault("sourceProfileByUrl", {})
    for url in LEGACY_URLS:
        if url in mapping:
            mapping.pop(url, None)
            changed += 1
    if mapping.get(PUBLIC_MAP_URL) != PROFILE:
        mapping[PUBLIC_MAP_URL] = PROFILE
        changed += 1
    if mapping.get(MACHINE_DATA_URL) != PROFILE:
        mapping[MACHINE_DATA_URL] = PROFILE
        changed += 1
    if changed:
        save(REGISTRY, registry)
    return changed


def update_monitor_state() -> int:
    if not MONITOR.exists():
        return 0
    state = load(MONITOR)
    sources = state.get("sources") if isinstance(state.get("sources"), dict) else {}
    changed = 0
    for url in LEGACY_URLS:
        if url in sources:
            sources.pop(url, None)
            changed += 1
    if changed:
        state["sources"] = sources
        save(MONITOR, state)
    return changed


def main() -> int:
    changes: dict[str, int] = {}
    changes[str(DATA.relative_to(ROOT))] = update_json_file(DATA)
    changes[str(REGISTRY.relative_to(ROOT))] = update_registry()
    changes[str(MONITOR.relative_to(ROOT))] = update_monitor_state()

    if SNAPSHOTS.exists():
        for path in sorted(SNAPSHOTS.glob("*.json")):
            count = update_json_file(path)
            if count:
                changes[str(path.relative_to(ROOT))] = count

    changed = {path: count for path, count in changes.items() if count}
    print(json.dumps({
        "status": "updated" if changed else "already_current",
        "publicMapUrl": PUBLIC_MAP_URL,
        "machineDataUrl": MACHINE_DATA_URL,
        "changes": changed,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())