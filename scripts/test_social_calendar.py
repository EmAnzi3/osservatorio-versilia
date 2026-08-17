#!/usr/bin/env python3
"""Controlli strutturali e scenari noti del calendario social esecutivo."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "social-kit"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise AssertionError(message)


def run_plan(day: str, conditional_id: str | None = None) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [sys.executable, str(ROOT / "scripts" / "plan_social_week.py"), "--date", day, "--out-dir", tmp]
        if conditional_id:
            cmd.extend(["--conditional-id", conditional_id])
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        return load(Path(tmp) / "week.json")


def main() -> int:
    observances = load(KIT / "config" / "editorial-observances-2026-2027.json")
    rotation = load(KIT / "config" / "editorial-rotation.json")
    site = load(ROOT / "data" / "site-data.json")

    if observances["cadence"]["weekly_post_budget"] != 2:
        fail("Il budget editoriale deve restare di due post a settimana")

    horizon_start = date.fromisoformat(observances["horizon"]["from"])
    horizon_end = date.fromisoformat(observances["horizon"]["to"])
    sources = observances["sources"]
    ids: set[str] = set()

    for event in observances["observances"]:
        if event["id"] in ids:
            fail(f"ID ricorrenza duplicato: {event['id']}")
        ids.add(event["id"])
        if event["priority"] not in {"anchor", "conditional"}:
            fail(f"Priorità non valida: {event['id']}")
        event_date = date.fromisoformat(event["date"])
        publish_date = date.fromisoformat(event["suggested_publish_date"])
        if not (horizon_start <= event_date <= horizon_end):
            fail(f"Ricorrenza fuori orizzonte: {event['id']}")
        if not (horizon_start <= publish_date <= horizon_end):
            fail(f"Data di pubblicazione fuori orizzonte: {event['id']}")
        if event.get("source") not in sources:
            fail(f"Fonte non registrata: {event['id']}")
        if not sources[event["source"]].startswith("https://"):
            fail(f"URL fonte non HTTPS: {event['id']}")
        if event.get("theme") not in site["themes"]:
            fail(f"Tema inesistente per ricorrenza: {event['id']}")

    for theme_key in rotation["themes"]:
        theme = site["themes"].get(theme_key)
        if not theme:
            fail(f"Tema inesistente nella rotazione: {theme_key}")
        if not any(metric in site["metrics"] for metric in theme.get("featured", [])):
            fail(f"Tema senza indicatore featured utilizzabile: {theme_key}")

    november = run_plan("2026-11-09")
    if len(november["scheduled"]) != 2:
        fail("La settimana 9–15 novembre deve avere esattamente due uscite")
    november_ids = {item.get("id") for item in november["scheduled"] if item["type"] == "observance"}
    if november_ids != {"diabetes-2026", "road-victims-2026"}:
        fail(f"Collisione anchor novembre risolta male: {november_ids}")
    if any(item["type"] == "ordinary" for item in november["scheduled"]):
        fail("La doppia ricorrenza anchor di novembre deve sostituire entrambi gli slot ordinari")

    september = run_plan("2026-09-07")
    if len(september["scheduled"]) != 2 or len(september["conditional_candidates"]) != 2:
        fail("Le ricorrenze conditional del 7–8 settembre non devono entrare automaticamente nel piano")

    promoted = run_plan("2026-09-07", "literacy-2026")
    if len(promoted["scheduled"]) != 2:
        fail("Promuovere una conditional non deve superare il budget settimanale")
    promoted_ids = {item.get("id") for item in promoted["scheduled"] if item["type"] == "observance"}
    if promoted_ids != {"literacy-2026"}:
        fail("La conditional richiesta non è stata promossa correttamente")

    for sample in ["2026-09-07", "2026-11-09", "2027-03-22", "2027-07-05"]:
        plan = run_plan(sample)
        if len(plan["scheduled"]) > 2:
            fail(f"Budget superato nella settimana di {sample}")

    print(f"Calendario social: {len(ids)} ricorrenze, rotazione {len(rotation['themes'])} temi, scenari esecutivi verificati")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
