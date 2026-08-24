#!/usr/bin/env python3
"""Genera il pacchetto Social Kit a partire dal piano settimanale eseguibile.

Il planner resta la fonte canonica di date/temi/indicatori. Questo adattatore
trasforma ogni uscita pianificata in un carosello di quattro tavole 1080×1350,
riusando il renderer editoriale approvato. Se una ricorrenza non ha ancora una
metrica riconoscibile, il pacchetto viene prodotto come parziale e la voce viene
segnalata esplicitamente invece di inventare un dato.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import generate_social_kit as renderer


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "social-kit"
DIST = KIT / "dist"
DEFAULT_PLAN = DIST / "editorial-plan" / "week.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def safe_id(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-").replace("--", "-")


def questions_for(theme: str, bank: dict[str, Any]) -> list[str]:
    configured = bank.get("themes", {}).get(theme, {})
    fallback = bank["fallback"]
    return [
        configured.get("data") or fallback["data"],
        configured.get("context") or fallback["context"],
    ]


def series_years(metric: dict[str, Any]) -> list[int]:
    rows = metric.get("rows") or []
    if not rows or not all(row.get("series") for row in rows):
        return []
    years = [int(value) for value in rows[0]["series"].get("years", [])]
    if not years:
        return []
    for row in rows:
        row_years = [int(value) for value in row["series"].get("years", [])]
        if row_years != years or len(row["series"].get("values", [])) != len(years):
            return []
    return years


def temporal_spec(metric: dict[str, Any]) -> dict[str, Any]:
    years = series_years(metric)
    if not years:
        return {}
    current = int(metric.get("meta", {}).get("year", years[-1]))
    usable = [year for year in years if year <= current]
    if not usable:
        return {}
    target = current - 10
    base = next((year for year in usable if year >= target), usable[0])
    return {
        "history_from": base,
        "comparison": {"type": "base_year", "year": base},
    }


def metric_for_item(item: dict[str, Any], site: dict[str, Any]) -> tuple[str | None, str | None]:
    if item["type"] == "ordinary":
        key = item.get("metric")
        if key in site["metrics"]:
            return key, None
        return None, f"Indicatore ordinario inesistente nel dataset: {key}"

    candidates: list[str] = []
    for field in ("generator_ready_metrics", "matching_metrics", "preferred_indicators"):
        for key in item.get(field, []) or []:
            if key in site["metrics"] and key not in candidates:
                candidates.append(key)
    if candidates:
        return candidates[0], None
    return None, "La ricorrenza non ha ancora una metrica esatta riconosciuta nel dataset corrente."


def post_from_item(
    item: dict[str, Any],
    site: dict[str, Any],
    questions: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    metric_key, reason = metric_for_item(item, site)
    if not metric_key:
        return None, {
            "date": item["date"],
            "id": item.get("id") or safe_id(item.get("title", "uscita")),
            "title": item.get("title", "Uscita pianificata"),
            "theme": item.get("theme"),
            "reason": reason,
        }

    metric = site["metrics"][metric_key]
    metric_theme = metric.get("meta", {}).get("theme")
    if metric_theme != item.get("theme"):
        return None, {
            "date": item["date"],
            "id": item.get("id") or safe_id(item.get("title", "uscita")),
            "title": item.get("title", "Uscita pianificata"),
            "theme": item.get("theme"),
            "reason": f"Tema della metrica {metric_key} ({metric_theme}) non coerente con il piano ({item.get('theme')}).",
        }

    kind = "ricorrenza" if item["type"] == "observance" else "ordinario"
    post_id = f"{item['date']}-{kind}-{item['theme']}-{metric_key}"
    post: dict[str, Any] = {
        "id": safe_id(post_id),
        "date": item["date"],
        "status": "draft",
        "priority": item.get("priority", "ordinary"),
        "theme": item["theme"],
        "dataset": "site",
        "metric": metric_key,
        "questions": questions_for(item["theme"], questions),
    }
    post.update(temporal_spec(metric))
    if item["type"] == "observance":
        limitation = (item.get("limitations") or "").strip()
        angle = (item.get("angle") or "").strip()
        if limitation:
            post["context_note"] = limitation
        elif angle:
            post["context_note"] = angle
        post["observance"] = {
            "id": item.get("id"),
            "name": item.get("title"),
            "source_url": item.get("source_url"),
        }
    return post, None


def package_readme(plan: dict[str, Any], manifests: list[dict[str, Any]], manual: list[dict[str, Any]]) -> str:
    lines = [
        f"# Social Kit · settimana {plan['week']['from']}",
        "",
        f"Periodo: **{plan['week']['from']} – {plan['week']['to']}**.",
        f"Uscite pianificate: **{len(plan['scheduled'])}/{plan['weekly_budget']}**. Caroselli generati: **{len(manifests)}**.",
        "",
        "## Come usare il pacchetto",
        "",
        "Per ogni uscita apri la cartella con la data: in `cards/` trovi i quattro PNG 1080×1350 nell'ordine 01→04; in `testi/` trovi i copy per Facebook, Instagram, LinkedIn e X; in `alt/` i testi alternativi; `provenienza.json` documenta dati, fonte e versione.",
        "",
    ]
    if manifests:
        lines.extend(["## Materiale pronto", ""])
        for item in manifests:
            lines.append(f"- **{item['date']}** · `{item['post_id']}` · 4 PNG + copy + ALT + provenienza")
        lines.append("")
    if manual:
        lines.extend(["## Attenzione: intervento editoriale necessario", ""])
        for item in manual:
            lines.append(f"- **{item['date']} · {item['title']}**: {item['reason']}")
        lines.extend(["", "Queste voci non sono state sostituite con indicatori simili: il sistema evita associazioni metodologicamente deboli.", ""])
    lines.extend([
        "## Stato",
        "",
        "Pacchetto di revisione: controllare i PNG prima della pubblicazione. Il workflow non pubblica automaticamente sui social.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", default=str(DEFAULT_PLAN), help="week.json prodotto da plan_social_week.py")
    args = parser.parse_args()

    plan_path = Path(args.plan)
    plan = load(plan_path)
    site = load(ROOT / "data" / "site-data.json")
    questions = load(KIT / "config" / "question-bank.json")
    design = load(KIT / "config" / "design-system.json")
    themes = load(KIT / "config" / "themes.json")

    if plan.get("version") != "social-week-v3":
        raise ValueError(f"Versione piano non supportata: {plan.get('version')}")
    if len(plan.get("scheduled", [])) > int(plan["weekly_budget"]):
        raise ValueError("Il piano supera il budget settimanale")

    posts: list[dict[str, Any]] = []
    manual: list[dict[str, Any]] = []
    for item in plan["scheduled"]:
        post, unresolved = post_from_item(item, site, questions)
        if post:
            posts.append(post)
        if unresolved:
            manual.append(unresolved)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    manifests = [renderer.generate_post(post, design, themes, DIST / post["id"]) for post in posts]
    renderer.write(DIST / "index.html", renderer.gallery(manifests))
    renderer.write(DIST / "week.json", json.dumps(plan, ensure_ascii=False, indent=2) + "\n")

    root_manifest = {
        "status": "partial" if manual else "ready-for-review",
        "method": "weekly-four-slide-carousels",
        "design_system": design["version"],
        "week": plan["week"],
        "weekly_budget": plan["weekly_budget"],
        "scheduled_count": len(plan["scheduled"]),
        "posts": len(manifests),
        "slides": len(manifests) * 4,
        "manual_required": manual,
        "items": manifests,
        "weekly_counts": dict(Counter(date.fromisoformat(post["date"]).isocalendar()[:2] for post in posts)),
    }
    # Le tuple ISO week non sono chiavi JSON portabili: esponiamo anche una forma leggibile.
    root_manifest["weekly_counts"] = {
        f"{year}-W{week:02d}": count
        for (year, week), count in Counter(date.fromisoformat(post["date"]).isocalendar()[:2] for post in posts).items()
    }
    renderer.write(DIST / "manifest.json", json.dumps(root_manifest, ensure_ascii=False, indent=2) + "\n")
    renderer.write(DIST / "README.md", package_readme(plan, manifests, manual))

    print(
        f"Social Kit settimana {plan['week']['from']}: {len(manifests)} caroselli, "
        f"{len(manifests) * 4} PNG, {len(manual)} voci da gestire manualmente"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
