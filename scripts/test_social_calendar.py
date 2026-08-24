#!/usr/bin/env python3
"""Controlli strutturali e scenari noti del calendario social esecutivo."""

from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "social-kit"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise AssertionError(message)


def load_planner():
    path = ROOT / "scripts" / "plan_social_week.py"
    spec = importlib.util.spec_from_file_location("plan_social_week", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Impossibile caricare plan_social_week.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PLANNER = load_planner()


def run_plan(day: str, conditional_id: str | None = None) -> dict:
    return PLANNER.make_plan(date.fromisoformat(day), conditional_id)


def ordinary_items(plan: dict) -> list[dict]:
    return [item for item in plan["scheduled"] if item["type"] == "ordinary"]


def observance_items(plan: dict) -> list[dict]:
    return [item for item in plan["scheduled"] if item["type"] == "observance"]


def assert_budget(plan: dict, label: str) -> None:
    if len(plan["scheduled"]) > plan["weekly_budget"]:
        fail(f"Budget settimanale superato in {label}: {len(plan['scheduled'])}/{plan['weekly_budget']}")


def main() -> int:
    observances = load(KIT / "config" / "editorial-observances-2026-2027.json")
    cadence = load(KIT / "config" / "editorial-cadence.json")
    rotation = load(KIT / "config" / "editorial-rotation.json")
    site = load(ROOT / "data" / "site-data.json")

    if cadence["weekly_post_budget"] != 2:
        fail("Il budget editoriale deve essere di due post a settimana")
    if cadence["ordinary_posts_per_week"] != 2:
        fail("La capacità ordinaria deve restare di due slot a settimana")
    if cadence.get("special_posts_are_additive"):
        fail("Le ricorrenze non devono essere additive rispetto ai due slot")
    if len(rotation["slots"]) != cadence["ordinary_posts_per_week"]:
        fail("Gli slot della rotazione devono coincidere con la capacità ordinaria")
    if "2026-12-25" not in cadence.get("blackout_dates", []):
        fail("Il blackout di Natale 2026 deve essere registrato")
    if "2027-01-01" not in cadence.get("blackout_dates", []):
        fail("Il blackout di Capodanno 2027 deve essere registrato")

    obs_cadence = observances.get("cadence", {})
    if obs_cadence.get("weekly_post_budget") != cadence["weekly_post_budget"]:
        fail("Il budget nel file ricorrenze deve essere allineato alla cadenza canonica")

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

    required_2026 = {
        "literacy-2026",
        "cleanup-2026",
        "tourism-2026",
        "older-persons-2026",
        "habitat-2026",
        "disaster-risk-2026",
        "diabetes-2026",
        "road-victims-2026",
        "children-2026",
        "sustainable-transport-2026",
        "disability-2026",
        "migrants-2026",
    }
    if not required_2026.issubset(ids):
        fail(f"Ricorrenze operative 2026 mancanti: {sorted(required_2026 - ids)}")

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
        fail(f"Avvio rotazione errato dopo il post Lavoro del 21 agosto: {launch_themes}")
    assert_budget(launch, "24–30 agosto")

    september = run_plan("2026-09-07")
    september_special = observance_items(september)
    september_ordinary = ordinary_items(september)
    if {item["id"] for item in september_special} != {"literacy-2026"}:
        fail("L'8 settembre deve essere presidiato automaticamente dall'alfabetizzazione")
    if len(september_ordinary) != 1 or september_ordinary[0]["theme"] != "ambiente":
        fail("L'alfabetizzazione deve sostituire lo slot di martedì e lasciare Ambiente il venerdì")
    if {item["id"] for item in september["conditional_candidates"]} != {"clean-air-2026"}:
        fail("Aria pulita deve restare conditional e non entrare automaticamente")
    assert_budget(september, "7–13 settembre")

    cleanup = run_plan("2026-09-14")
    if {item["id"] for item in observance_items(cleanup)} != {"cleanup-2026"}:
        fail("World Cleanup Day deve entrare automaticamente nel piano")
    if [item["theme"] for item in ordinary_items(cleanup)] != ["bilanci"]:
        fail("World Cleanup Day deve sostituire lo slot ordinario più vicino, lasciando Bilanci")
    assert_budget(cleanup, "14–20 settembre")

    tourism = run_plan("2026-09-21")
    if {item["id"] for item in observance_items(tourism)} != {"tourism-2026"}:
        fail("La Giornata mondiale del turismo deve occupare il secondo slot della settimana")
    if [item["theme"] for item in ordinary_items(tourism)] != ["demografia"]:
        fail("Il turismo deve sostituire lo slot Economia del venerdì")
    assert_budget(tourism, "21–27 settembre")

    november = run_plan("2026-11-09")
    november_special = observance_items(november)
    if len(ordinary_items(november)) != 0:
        fail("La settimana 9–15 novembre non deve contenere post ordinari")
    november_ids = {item["id"] for item in november_special}
    if november_ids != {"diabetes-2026", "road-victims-2026"}:
        fail(f"Ricorrenze novembre risolte male: {november_ids}")
    if len(november["scheduled"]) != 2:
        fail("Diabete e vittime della strada devono saturare il budget a due contenuti")
    assert_budget(november, "9–15 novembre")

    children = run_plan("2026-11-16")
    if {item["id"] for item in observance_items(children)} != {"children-2026"}:
        fail("La Giornata mondiale dell'infanzia deve entrare automaticamente")
    if len(ordinary_items(children)) != 1:
        fail("La settimana dell'infanzia deve mantenere un solo post ordinario")
    assert_budget(children, "16–22 novembre")

    transport = run_plan("2026-11-23")
    if {item["id"] for item in observance_items(transport)} != {"sustainable-transport-2026"}:
        fail("Il World Sustainable Transport Day deve entrare automaticamente")
    if len(ordinary_items(transport)) != 1:
        fail("La settimana del trasporto sostenibile deve mantenere un solo post ordinario")
    assert_budget(transport, "23–29 novembre")

    christmas = run_plan("2026-12-21")
    if len(christmas["scheduled"]) != 1 or len(ordinary_items(christmas)) != 1:
        fail("La settimana di Natale deve avere una sola uscita ordinaria")
    if not christmas["blackout_slots"] or christmas["blackout_slots"][0]["slot_date"] != "2026-12-25":
        fail("Il planner deve esporre il blackout del 25 dicembre")
    assert_budget(christmas, "21–27 dicembre")

    new_year = run_plan("2026-12-28")
    if len(new_year["scheduled"]) != 1 or len(ordinary_items(new_year)) != 1:
        fail("La settimana di Capodanno deve avere una sola uscita ordinaria")
    assert_budget(new_year, "28 dicembre–3 gennaio")

    mountain = run_plan("2026-12-07", "mountain-2026")
    if {item["id"] for item in observance_items(mountain)} != {"mountain-2026"}:
        fail("La Giornata della montagna deve poter essere promossa esplicitamente")
    if len(mountain["scheduled"]) != 2:
        fail("Una conditional promossa deve sostituire uno slot, non aggiungersi ai due ordinari")
    assert_budget(mountain, "7–13 dicembre conditional")

    for sample in [
        "2026-09-07", "2026-09-14", "2026-09-21", "2026-10-12",
        "2026-11-09", "2026-11-23", "2026-12-21", "2027-03-22", "2027-07-05",
    ]:
        plan = run_plan(sample)
        assert_budget(plan, sample)
        ordinary = ordinary_items(plan)
        if len({item["theme"] for item in ordinary}) != len(ordinary):
            fail(f"Temi ordinari duplicati nella settimana di {sample}")

    print(
        f"Calendario social: {len(ids)} ricorrenze, budget {cadence['weekly_post_budget']} post/settimana, "
        f"rotazione {len(rotation['themes'])} temi e scenari esecutivi verificati"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
