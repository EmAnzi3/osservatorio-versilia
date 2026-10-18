#!/usr/bin/env python3
"""Costruisce il piano social esecutivo di una settimana.

Il planner applica un budget editoriale massimo di due uscite settimanali.
Le ricorrenze ``anchor`` occupano uno dei due posti e sostituiscono lo slot
ordinario più vicino; le ``conditional`` entrano solo dopo promozione esplicita.
Gli slot sostituiti o in blackout non vengono recuperati automaticamente.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "social-kit"
DEFAULT_OUT = KIT / "dist" / "editorial-plan"
HISTORY_PATH = KIT / "config" / "publication-history.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def monday_of(value: date) -> date:
    return value - timedelta(days=value.weekday())


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def fmt_date(value: date) -> str:
    months = [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
    ]
    return f"{value.day} {months[value.month - 1]} {value.year}"


def publication_history(history: dict[str, Any] | None = None) -> dict[str, Any]:
    history = load(HISTORY_PATH) if history is None else history
    if history.get("version") != "social-publications-v1":
        raise ValueError("Versione del registro pubblicazioni non riconosciuta")
    ids: set[str] = set()
    site = load(ROOT / "data" / "site-data.json")
    for entry in history["publications"]:
        if entry["id"] in ids or not entry.get("evidence", "").strip() or not entry.get("metrics"):
            raise ValueError("Pubblicazione senza ID univoco, prova o indicatori")
        ids.add(entry["id"])
        if any(key not in site["metrics"] for key in entry["metrics"]):
            raise ValueError(f"Indicatore sconosciuto nel registro: {entry['id']}")
        confirmed = parse_date(entry["confirmed_on"])
        published = parse_date(entry["published_on"]) if entry.get("published_on") else None
        if published and (published.year != int(entry["year"]) or published > confirmed):
            raise ValueError(f"Date non coerenti nel registro: {entry['id']}")
        if int(entry["year"]) > confirmed.year:
            raise ValueError(f"Anno futuro nel registro: {entry['id']}")
    return history


def used_metrics(day: date, history: dict[str, Any]) -> set[str]:
    return {
        key for entry in history["publications"]
        if int(entry["year"]) == day.year
        and parse_date(entry.get("published_on") or entry["confirmed_on"]) <= day
        for key in entry["metrics"]
    }


def check_plan_history(plan: dict[str, Any]) -> None:
    """Controlla anche piani salvati prima di un aggiornamento del registro."""
    history = publication_history()
    for item in plan["scheduled"]:
        keys = [item["metric"]] if item["type"] == "ordinary" else [
            key for field in ("preferred_indicators", "matching_metrics", "generator_ready_metrics")
            for key in item.get(field, [])
        ]
        duplicates = set(keys) & used_metrics(parse_date(item["date"]), history)
        if duplicates:
            raise ValueError(f"Piano non aggiornato: indicatori già pubblicati nell'anno: {sorted(duplicates)}")


def ordinary_for_slot(start: date, slot_index: int, rotation: dict[str, Any], site: dict[str, Any], history: dict[str, Any] | None = None) -> dict[str, Any]:
    rotation_start = monday_of(parse_date(rotation["start_week"]))
    week_index = (start - rotation_start).days // 7
    themes = rotation["themes"]
    start_theme_index = int(rotation.get("start_theme_index", 0))
    slots_per_week = len(rotation["slots"])
    theme_index = (start_theme_index + week_index * slots_per_week + slot_index) % len(themes)
    theme_key = themes[theme_index]
    theme = site["themes"].get(theme_key)
    if not theme:
        raise ValueError(f"Tema della rotazione inesistente: {theme_key}")
    featured = theme.get("featured") or []
    slot_date = start + timedelta(days=int(rotation["slots"][slot_index]["weekday"]))
    used = used_metrics(slot_date, history or publication_history())
    metric_key = next((key for key in featured if key in site["metrics"] and key not in used), None)
    if not metric_key:
        raise ValueError(f"Nessun indicatore featured inedito per {theme_key} nel {slot_date.year}: serve una scelta editoriale, nessun doppione automatico")
    metric = site["metrics"][metric_key]
    return {
        "theme": theme_key,
        "theme_label": theme.get("label", theme_key),
        "metric": metric_key,
        "metric_label": metric.get("meta", {}).get("shortLabel") or metric.get("meta", {}).get("label") or metric_key,
        "excluded_published_metrics": [key for key in featured if key in used],
    }


def event_source(event: dict[str, Any], observances: dict[str, Any]) -> str:
    return observances.get("sources", {}).get(event.get("source", ""), "")


def matching_metrics(event: dict[str, Any], site: dict[str, Any]) -> list[str]:
    return [key for key in event.get("preferred_indicators", []) if key in site["metrics"]]


def replacement_slots(
    start: date,
    special: list[dict[str, Any]],
    slots: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    if len(special) > len(slots):
        raise ValueError(
            f"Le ricorrenze selezionate ({len(special)}) superano il budget/numero di slot settimanali ({len(slots)}). "
            "Serve una decisione editoriale esplicita."
        )

    available = set(range(len(slots)))
    reserved: dict[int, dict[str, Any]] = {}
    for event in special:
        publish = parse_date(event["suggested_publish_date"])
        slot_index = min(
            available,
            key=lambda idx: (
                abs((start + timedelta(days=int(slots[idx]["weekday"])) - publish).days),
                idx,
            ),
        )
        reserved[slot_index] = event
        available.remove(slot_index)
    return reserved


def make_plan(requested: date, conditional_id: str | None = None) -> dict[str, Any]:
    observances = load(KIT / "config" / "editorial-observances-2026-2027.json")
    cadence = load(KIT / "config" / "editorial-cadence.json")
    rotation = load(KIT / "config" / "editorial-rotation.json")
    site = load(ROOT / "data" / "site-data.json")
    ready = load(KIT / "config" / "social-ready.json").get("approved_metrics", {})
    history = publication_history()

    start = monday_of(requested)
    end = start + timedelta(days=6)
    weekly_budget = int(cadence["weekly_post_budget"])
    ordinary_capacity = int(cadence["ordinary_posts_per_week"])
    slots = rotation["slots"]
    if weekly_budget != ordinary_capacity or len(slots) != ordinary_capacity:
        raise ValueError("weekly_post_budget, ordinary_posts_per_week e numero di slot devono coincidere")

    events: list[dict[str, Any]] = []
    for raw in observances["observances"]:
        publish_date = parse_date(raw["suggested_publish_date"])
        if start <= publish_date <= end:
            item = dict(raw)
            used = used_metrics(publish_date, history)
            item["excluded_published_metrics"] = [key for key in raw.get("preferred_indicators", []) if key in used]
            item["preferred_indicators"] = [key for key in raw.get("preferred_indicators", []) if key not in used]
            item["source_url"] = event_source(raw, observances)
            item["matching_metrics"] = matching_metrics(item, site)
            item["generator_ready_metrics"] = [key for key in item["matching_metrics"] if key in ready]
            events.append(item)

    anchors = [item for item in events if item["priority"] == "anchor"]
    conditionals = [item for item in events if item["priority"] == "conditional"]

    promoted: list[dict[str, Any]] = []
    if conditional_id:
        selected = next((item for item in conditionals if item["id"] == conditional_id), None)
        if not selected:
            available = ", ".join(item["id"] for item in conditionals) or "nessuna"
            raise ValueError(f"Conditional non disponibile nella settimana: {conditional_id}. Disponibili: {available}")
        promoted.append(selected)

    special = sorted(
        anchors + promoted,
        key=lambda item: (item["suggested_publish_date"], 0 if item["priority"] == "anchor" else 1, item["id"]),
    )
    if len(special) > weekly_budget:
        raise ValueError(
            f"Le ricorrenze selezionate ({len(special)}) superano il budget settimanale di {weekly_budget}. "
            "Ridurre le ricorrenze prima di produrre il piano."
        )

    reserved = replacement_slots(start, special, slots)
    blackout_dates = set(cadence.get("blackout_dates", []))
    scheduled: list[dict[str, Any]] = []
    rotation_status: list[dict[str, Any]] = []
    replaced_slots: list[dict[str, Any]] = []
    blackout_slots: list[dict[str, Any]] = []

    for slot_index, slot in enumerate(slots):
        ordinary = ordinary_for_slot(start, slot_index, rotation, site, history)
        slot_date = start + timedelta(days=int(slot["weekday"]))
        iso = slot_date.isoformat()
        status = {
            "date": iso,
            "slot_label": slot["label"],
            **ordinary,
        }

        if slot_index in reserved:
            event = reserved[slot_index]
            status["status"] = "replaced_by_observance"
            status["observance_id"] = event["id"]
            replaced_slots.append({
                "slot_date": iso,
                "slot_label": slot["label"],
                "ordinary_theme": ordinary["theme"],
                "ordinary_metric": ordinary["metric"],
                "observance_id": event["id"],
                "observance_date": event["suggested_publish_date"],
            })
        elif iso in blackout_dates:
            status["status"] = "blackout"
            blackout_slots.append({
                "slot_date": iso,
                "slot_label": slot["label"],
                "ordinary_theme": ordinary["theme"],
                "ordinary_metric": ordinary["metric"],
            })
        else:
            status["status"] = "scheduled"
            scheduled.append({
                "date": iso,
                "type": "ordinary",
                "slot": slot["kind"],
                "slot_label": slot["label"],
                "title": f"{ordinary['theme_label']} · {ordinary['metric_label']}",
                "theme": ordinary["theme"],
                "metric": ordinary["metric"],
                "metric_label": ordinary["metric_label"],
                "generator_ready": ordinary["metric"] in ready,
                "excluded_published_metrics": ordinary["excluded_published_metrics"],
            })
        rotation_status.append(status)

    for event in special:
        scheduled.append({
            "date": event["suggested_publish_date"],
            "type": "observance",
            "priority": event["priority"],
            "id": event["id"],
            "title": event["name"],
            "theme": event["theme"],
            "angle": event.get("angle", ""),
            "limitations": event.get("limitations", ""),
            "official_theme": event.get("official_theme_2026", ""),
            "preferred_indicators": event.get("preferred_indicators", []),
            "matching_metrics": event["matching_metrics"],
            "generator_ready_metrics": event["generator_ready_metrics"],
            "source_url": event["source_url"],
            "excluded_published_metrics": event["excluded_published_metrics"],
        })

    ordinary_themes = [item["theme"] for item in scheduled if item["type"] == "ordinary"]
    if len(set(ordinary_themes)) != len(ordinary_themes):
        raise ValueError("Gli slot ordinari rimasti nella settimana devono usare temi diversi")

    if len(scheduled) > weekly_budget:
        raise ValueError(f"Budget settimanale superato: {len(scheduled)}/{weekly_budget}")

    scheduled.sort(key=lambda item: (item["date"], 0 if item["type"] == "observance" else 1))

    promoted_ids = {item["id"] for item in promoted}
    return {
        "version": "social-week-v3",
        "generated_for": requested.isoformat(),
        "week": {"from": start.isoformat(), "to": end.isoformat()},
        "weekly_budget": weekly_budget,
        "planned_count": len(scheduled),
        "publication_tracking": {
            "path": "social-kit/config/publication-history.json",
            "years": {str(year): history.get("coverage", {}).get(str(year), {"status": "partial", "note": "Anno non ancora ricostruito"}) for year in {start.year, end.year}},
        },
        "ordinary_count": len(ordinary_themes),
        "special_count": len(special),
        "scheduled": scheduled,
        "replaced_slots": replaced_slots,
        "blackout_slots": blackout_slots,
        "conditional_candidates": [
            {
                "id": item["id"],
                "date": item["suggested_publish_date"],
                "name": item["name"],
                "theme": item["theme"],
                "angle": item.get("angle", ""),
                "limitations": item.get("limitations", ""),
                "preferred_indicators": item.get("preferred_indicators", []),
                "matching_metrics": item["matching_metrics"],
                "source_url": item["source_url"],
                "decision": "promuovere esplicitamente solo se il collegamento ai dati è realmente pertinente",
            }
            for item in conditionals
            if item["id"] not in promoted_ids
        ],
        "ordinary_rotation": rotation_status,
        "rules": {
            "anchor": cadence["anchor_rule"],
            "conditional": cadence["conditional_rule"],
            "slot_replacement": cadence["slot_replacement_rule"],
            "special_collision": cadence["special_collision_rule"],
            "blackout": cadence["blackout_rule"],
            "verification": cadence["verification_rule"],
        },
    }


def markdown(plan: dict[str, Any]) -> str:
    start = parse_date(plan["week"]["from"])
    end = parse_date(plan["week"]["to"])
    out = [
        f"# Piano social · settimana {plan['week']['from']}",
        "",
        f"Periodo: **{fmt_date(start)} – {fmt_date(end)}**  ",
        f"Uscite pianificate: **{plan['planned_count']}/{plan['weekly_budget']}**. "
        f"Ordinarie: **{plan['ordinary_count']}**. Ricorrenze: **{plan['special_count']}**.",
        "",
        "## Uscite pianificate",
        "",
    ]
    for year, coverage in plan.get("publication_tracking", {}).get("years", {}).items():
        if coverage["status"] != "complete":
            out.extend([f"**Registro pubblicazioni {year} parziale:** vengono esclusi i post confermati; l'assenza dal registro non certifica che un argomento sia inedito.", ""])

    for item in plan["scheduled"]:
        when = fmt_date(parse_date(item["date"]))
        if item.get("excluded_published_metrics"):
            out.extend([f"Già pubblicati nell'anno, esclusi dalla selezione: {', '.join(item['excluded_published_metrics'])}.", ""])
        if item["type"] == "ordinary":
            readiness = "generatore automatico disponibile" if item["generator_ready"] else "carosello da preparare/revisionare manualmente"
            out.extend([
                f"### {when} · ordinario — {item['slot_label']}",
                f"- Tema: **{item['theme']}**",
                f"- Indicatore: `{item['metric']}` — {item['metric_label']}",
                f"- Produzione: {readiness}",
                "",
            ])
        else:
            out.extend([
                f"### {when} · ricorrenza {item['priority']}",
                f"- **{item['title']}**",
                f"- Tema: **{item['theme']}**",
                f"- Angolo: {item['angle']}",
                f"- Indicatori suggeriti: {', '.join(item['preferred_indicators']) or 'da definire'}",
                f"- Metriche riconosciute nel dataset: {', '.join(item['matching_metrics']) or 'nessuna corrispondenza automatica; verifica manuale'}",
                f"- Limite: {item['limitations'] or 'nessun limite aggiuntivo registrato'}",
            ])
            if item.get("official_theme"):
                out.append(f"- Tema ufficiale registrato: {item['official_theme']}")
            out.extend([
                f"- Fonte ricorrenza: {item['source_url']}",
                "",
            ])

    if plan["replaced_slots"]:
        out.extend(["## Slot ordinari sostituiti", ""])
        for item in plan["replaced_slots"]:
            out.append(
                f"- {fmt_date(parse_date(item['slot_date']))} ({item['slot_label']}): "
                f"**{item['ordinary_theme']}** / `{item['ordinary_metric']}` cede il posto a `{item['observance_id']}`."
            )
        out.append("")

    if plan["blackout_slots"]:
        out.extend(["## Blackout editoriali", ""])
        for item in plan["blackout_slots"]:
            out.append(
                f"- {fmt_date(parse_date(item['slot_date']))}: nessun post ordinario; "
                f"lo slot **{item['ordinary_theme']}** non viene recuperato automaticamente."
            )
        out.append("")

    out.extend(["## Ricorrenze conditional da decidere", ""])
    if plan["conditional_candidates"]:
        for item in plan["conditional_candidates"]:
            out.extend([
                f"- **{fmt_date(parse_date(item['date']))} — {item['name']}** (`{item['id']}`): {item['angle']}",
                f"  - Limite: {item['limitations'] or 'nessun limite aggiuntivo registrato'}",
                f"  - Fonte: {item['source_url']}",
            ])
    else:
        out.append("Nessuna ricorrenza conditional in questa settimana.")

    out.extend([
        "",
        "## Checklist esecutiva",
        "",
        "- [ ] Verificare che il totale non superi due uscite settimanali.",
        "- [ ] Ricontrollare data, denominazione, eventuale tema annuale e fonte ufficiale delle ricorrenze.",
        "- [ ] Verificare che i numeri coincidano con il dataset corrente.",
        "- [ ] Confermare nel registro ogni pubblicazione effettiva, con indicatori di tutte le card e prova; un kit generato non è un post pubblicato.",
        "- [ ] Preparare/rigenerare ogni carosello con il colore canonico del relativo tema.",
        "- [ ] Controllare che nessun testo esca dai box.",
        "- [ ] Preparare copy Facebook, Instagram, LinkedIn e X, ALT e link alla pagina più specifica.",
        "- [ ] Verificare che il testo non introduca causalità o granularità non supportate.",
        "- [ ] Pubblicare soltanto i contenuti presenti nella sezione «Uscite pianificate».",
        "",
        "Il workflow prepara il piano e apre/aggiorna l'issue settimanale: **non pubblica automaticamente sui social**.",
        "",
    ])
    return "\n".join(out)


def write_github_output(path: Path, plan: dict[str, Any], markdown_path: Path, json_path: Path) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"week_start={plan['week']['from']}\n")
        handle.write(f"week_end={plan['week']['to']}\n")
        handle.write(f"issue_title=Piano social · settimana {plan['week']['from']}\n")
        handle.write(f"markdown_path={markdown_path.as_posix()}\n")
        handle.write(f"json_path={json_path.as_posix()}\n")
        handle.write(f"scheduled_count={len(plan['scheduled'])}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=date.today().isoformat(), help="Una data della settimana da pianificare, YYYY-MM-DD")
    parser.add_argument("--conditional-id", default=None, help="Promuove esplicitamente una ricorrenza conditional della settimana")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT), help="Directory per week.json e week.md")
    parser.add_argument("--github-output", default=None, help="Percorso GITHUB_OUTPUT opzionale")
    parser.add_argument("--record-published", help="ID del post effettivamente pubblicato da registrare")
    parser.add_argument("--published-metric", action="append", default=[], help="Indicatore pubblicato; ripetibile per tutte le card")
    parser.add_argument("--publication-year", type=int, help="Anno della pubblicazione confermata")
    parser.add_argument("--published-on", help="Data effettiva YYYY-MM-DD, omettere se sconosciuta")
    parser.add_argument("--evidence", help="Permalink del post o conferma esplicita del proprietario")
    parser.add_argument("--provenance", help="Provenienza del kit pubblicato: registra gli indicatori di tutte le card")
    args = parser.parse_args()

    if args.record_published:
        if not args.publication_year or not args.evidence or not args.evidence.strip():
            parser.error("Registrazione: servono --publication-year e --evidence")
        metrics = list(args.published_metric)
        if args.provenance:
            provenance = load(Path(args.provenance))
            metrics.extend((provenance.get("slide_metrics") or {}).values())
            if provenance.get("metric"):
                metrics.append(provenance["metric"])
        history = publication_history()
        entry = {
            "id": args.record_published, "year": args.publication_year,
            "published_on": args.published_on, "confirmed_on": date.today().isoformat(),
            "metrics": sorted(set(metrics)), "evidence": args.evidence.strip(),
        }
        history["publications"].append(entry)
        publication_history(history)
        HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Pubblicazione registrata: {entry['id']} · {', '.join(entry['metrics'])}")
        return 0

    plan = make_plan(parse_date(args.date), args.conditional_id)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "week.json"
    markdown_path = out_dir / "week.md"
    json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown(plan), encoding="utf-8")

    if args.github_output:
        write_github_output(Path(args.github_output), plan, markdown_path, json_path)

    print(markdown(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
