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


def ordinary_items(plan: dict) -> list[dict]:
    return [item for item in plan["scheduled"] if item["type"] == "ordinary"]


def observance_items(plan: dict) -> list[dict]:
    return [item for item in plan["scheduled"] if item["type"] == "observance"]


def main() -> int:
    observances = load(KIT / "config" / "editorial-observances-2026-2027.json")
    cadence = load(KIT / "config" / "editorial-cadence.json")
    rotation = load(KIT / "config" / "editorial-rotation.json")
    site = load(ROOT / "data" / "site-data.json")

    if cadence["ordinary_posts_per_week"] != 2:
        fail("La cadenza ordinaria deve restare di due post a settimana")
    if not cadence.get("special_posts_are_additive"):
        fail("Le ricorrenze pertinenti devono essere aggiuntive rispetto ai due slot ordinari")
    if len(rotation["slots"]) != cadence["ordinary_posts_per_week"]:
        fail("Gli slot della rotazione devono coincidere con la cadenza ordinaria")

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

    launch = run_plan("2026-08-24")
    launch_ordinary = ordinary_items(launch)
    if len(launch_ordinary) != 2:
        fail("La settimana 24–30 agosto deve avere due uscite ordinarie")
    launch_themes = [item["theme"] for item in launch_ordinary]
    if launch_themes != ["istruzione", "salute"]:
        fail(f"Avvio nuova rotazione errato dopo il post Lavoro del 21 agosto: {launch_themes}")
    if len(set(launch_themes)) != 2:
        fail("Martedì e venerdì devono usare temi diversi")

    november = run_plan("2026-11-09")
    november_ordinary = ordinary_items(november)
    november_special = observance_items(november)
    if len(november_ordinary) != 2:
        fail("La settimana 9–15 novembre deve mantenere due uscite ordinarie")
    if len(november_special) != 2:
        fail("La settimana 9–15 novembre deve aggiungere entrambe le ricorrenze anchor")
    november_ids = {item.get("id") for item in november_special}
    if november_ids != {"diabetes-2026", "road-victims-2026"}:
        fail(f"Ricorrenze anchor novembre risolte male: {november_ids}")
    if len(november["scheduled"]) != 4:
        fail("Due ricorrenze anchor devono portare il totale settimanale a quattro contenuti")
    if len({item["theme"] for item in november_ordinary}) != 2:
        fail("Anche con ricorrenze, i due post ordinari devono restare su temi diversi")
    friday_ordinary = next(item for item in november_ordinary if item["date"] == "2026-11-13")
    if not friday_ordinary.get("same_day_observance"):
        fail("La collisione tra slot ordinario e Giornata mondiale del diabete deve essere segnalata")

    september = run_plan("2026-09-07")
    if len(ordinary_items(september)) != 2 or len(september["conditional_candidates"]) != 2:
        fail("Le ricorrenze conditional del 7–8 settembre non devono entrare automaticamente nel piano")

    promoted = run_plan("2026-09-07", "literacy-2026")
    if len(ordinary_items(promoted)) != 2 or len(observance_items(promoted)) != 1:
        fail("Promuovere una conditional deve aggiungerla ai due post ordinari")
    promoted_ids = {item.get("id") for item in observance_items(promoted)}
    if promoted_ids != {"literacy-2026"}:
        fail("La conditional richiesta non è stata promossa correttamente")
    if len(promoted["scheduled"]) != 3:
        fail("Una conditional promossa deve portare il totale settimanale a tre contenuti")

    for sample in ["2026-09-07", "2026-11-09", "2027-03-22", "2027-07-05"]:
        plan = run_plan(sample)
        ordinary = ordinary_items(plan)
        if len(ordinary) != 2:
            fail(f"Numero di post ordinari errato nella settimana di {sample}")
        if len({item["theme"] for item in ordinary}) != 2:
            fail(f"Temi ordinari duplicati nella settimana di {sample}")

    print(f"Calendario social: {len(ids)} ricorrenze, rotazione {len(rotation['themes'])} temi per singola uscita, scenari esecutivi verificati")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
