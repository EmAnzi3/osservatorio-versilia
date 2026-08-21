#!/usr/bin/env python3
"""Radar Opportunità Versilia v0.2.

La v0.2 separa le opportunità operative dalla coda interna di revisione,
calcola l'ammissibilità per ciascuno dei sette Comuni e segnala la freschezza
delle fonti. Non pubblica dati sul sito.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opportunity_radar_quality as quality

base = quality.base
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "data" / "opportunity-sources.json"

OBVIOUS_NON_MUNICIPAL = (
    r"\bmobilit[aà] esterna\b",
    r"\bfunzionario\b",
    r"\boperatori economici\b",
    r"\bpmi\b",
    r"\bstart[ -]?up\b",
    r"\bimprese?\b",
    r"\blavorator",
    r"\bdatori di lavoro\b",
    r"\bcontributi individuali\b",
    r"\btirocini\b",
    r"\bassegno formazione\b",
    r"\bborse? di mobilit[aà] professionale\b",
    r"\bapicolt",
    r"\bpesc(?:a|atori|atrici)\b",
    r"\bacquacolt",
    r"\briproduttori\b",
    r"\bproduzioni artigianali\b",
    r"\btranscan\b",
)

UNRESOLVED_MUNICIPAL_SCOPE = (
    r"\bcomuni ricadenti\b",
    r"\bcomuni classificati\b",
    r"\bcomuni montani\b",
    r"\bcomuni con popolazione\b",
    r"\bcomuni (?:fino|sotto|sopra)\b",
    r"\bfascia demografica\b",
    r"\baree interne\b",
    r"\bterritori montani\b",
    r"\bzone montane\b",
)


def clean(value: Any) -> str:
    return base.clean(value)


def norm(value: Any) -> str:
    return base.norm(value)


def municipality_profiles(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    profiles = config.get("municipalityProfiles") or {}
    result: dict[str, dict[str, Any]] = {}
    for town in config.get("municipalities") or base.TOWNS:
        result[town] = {
            "province": "Lucca",
            "toscanaDiffusa": "no",
            **(profiles.get(town) or {}),
        }
    return result


def _status_reason(status: str, reason: str) -> dict[str, str]:
    return {"status": status, "reason": reason}


def _explicit_municipalities(context: str, towns: list[str]) -> set[str]:
    found: set[str] = set()
    for town in towns:
        town_re = re.escape(norm(town))
        if re.search(rf"\bcomun(?:e|i)\b[^.;:]{{0,140}}\b{town_re}\b", context, re.I):
            found.add(town)
    return found


def _has_unresolved_scope(context: str) -> bool:
    return any(re.search(pattern, context, re.I) for pattern in UNRESOLVED_MUNICIPAL_SCOPE)


def resolve_municipalities(
    item: dict[str, Any], profiles: dict[str, dict[str, Any]], today: date
) -> dict[str, Any]:
    """Calcola lo stato per singolo Comune senza trasformare condizioni in certezze."""
    towns = list(profiles)
    base_status = item.get("eligibility", "review")
    base_reason = item.get("eligibility_reason") or "Destinatari non determinabili automaticamente."
    context = norm(
        f"{item.get('title', '')}. {item.get('beneficiary_text', '')}. {item.get('summary', '')}"
    )
    explicit = _explicit_municipalities(context, towns)
    is_toscana_diffusa = "toscana diffusa" in context
    province_lucca = "provincia di lucca" in context or "provincia lucchese" in context

    matrix: dict[str, dict[str, str]] = {}
    for town, profile in profiles.items():
        status = base_status if base_status in {"eligible", "conditional"} else "review"
        reason = base_reason

        if status in {"eligible", "conditional"} and is_toscana_diffusa:
            td = profile.get("toscanaDiffusa", "no")
            if td == "full":
                status = "eligible" if base_status == "eligible" else "conditional"
                reason = "Comune incluso integralmente nell'elenco dei territori della Toscana Diffusa."
            elif td == "partial":
                status = "conditional"
                reason = (
                    "Comune classificato TD*: l'intervento è ammissibile solo se ricade "
                    "nella porzione montana del territorio comunale."
                )
            else:
                status = "not_eligible"
                reason = "Comune non incluso nei territori della Toscana Diffusa."
        elif status in {"eligible", "conditional"} and province_lucca:
            if norm(profile.get("province")) != "lucca":
                status = "not_eligible"
                reason = "Il bando è limitato alla Provincia di Lucca."
        elif status in {"eligible", "conditional"} and explicit:
            if town not in explicit:
                status = "not_eligible"
                reason = "Il Comune non compare nel perimetro territoriale esplicitamente indicato dalla fonte."

        if (
            status == "eligible"
            and not is_toscana_diffusa
            and not explicit
            and _has_unresolved_scope(context)
        ):
            status = "conditional"
            reason = (
                "La fonte indica un ulteriore requisito territoriale o demografico: "
                "serve una verifica documentale per questo Comune."
            )

        matrix[town] = _status_reason(status, reason)

    statuses = [entry["status"] for entry in matrix.values()]
    if "eligible" in statuses:
        aggregate = "eligible"
    elif "conditional" in statuses:
        aggregate = "conditional"
    elif "review" in statuses:
        aggregate = "review"
    else:
        aggregate = "not_relevant"

    resolved = dict(item)
    resolved["eligibility"] = aggregate
    resolved["eligibility_reason"] = "Ammissibilità calcolata separatamente per ciascun Comune."
    resolved["municipality_eligibility"] = matrix
    resolved["municipalities"] = [
        town for town, entry in matrix.items() if entry["status"] in {"eligible", "conditional"}
    ]
    resolved["priority"] = base.priority(
        aggregate, resolved.get("deadline_at"), resolved.get("themes") or [], today
    )
    return resolved


def obvious_non_municipal(item: dict[str, Any]) -> bool:
    context = norm(f"{item.get('title', '')}. {item.get('beneficiary_text', '')}. {item.get('summary', '')}")
    if any(re.search(pattern, context, re.I) for pattern in base.DIRECT + base.CONDITIONAL):
        return False
    return any(re.search(pattern, context, re.I) for pattern in OBVIOUS_NON_MUNICIPAL)


def _dates_in_payload(payload: str, today: date) -> list[date]:
    values: list[date] = []
    tokens = re.findall(
        r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[./]\d{1,2}[./]\d{4}|\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\b",
        payload,
    )
    for token in tokens:
        parsed = base.parse_date(token)
        if parsed and parsed <= today:
            values.append(parsed)
    return values


def source_freshness(
    source: dict[str, Any], payload: str, items: list[dict[str, Any]], today: date
) -> dict[str, Any]:
    max_days = int(source.get("freshnessMaxDays") or 60)
    candidates = _dates_in_payload(payload, today)
    for item in items:
        for key in ("published_at", "opens_at"):
            value = item.get(key)
            if value:
                parsed = base.parse_date(value)
                if parsed and parsed <= today:
                    candidates.append(parsed)
    observed = max(candidates) if candidates else None
    if not observed:
        return {
            "status": "unknown",
            "observedDate": None,
            "ageDays": None,
            "maxAgeDays": max_days,
        }
    age = (today - observed).days
    return {
        "status": "stale" if age > max_days else "current",
        "observedDate": observed.isoformat(),
        "ageDays": age,
        "maxAgeDays": max_days,
    }


def _dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chosen: dict[tuple[str, str], dict[str, Any]] = {}
    for item in items:
        key = (item.get("source_id", ""), norm(item.get("title", "")))
        current = chosen.get(key)
        if current is None or len(item.get("summary") or "") > len(current.get("summary") or ""):
            chosen[key] = item
    return sorted(
        chosen.values(),
        key=lambda item: (item.get("deadline_at") or "9999-12-31", norm(item.get("title", ""))),
    )


def _compact_review(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "source_id": item.get("source_id"),
        "title": item.get("title"),
        "url": item.get("url"),
        "deadline_at": item.get("deadline_at"),
        "reason": item.get("eligibility_reason"),
    }


def run(
    config_path: Path,
    today: date,
    payloads: dict[str, str] | None = None,
    detail_payloads: dict[str, str] | None = None,
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    profiles = municipality_profiles(config)
    towns = list(profiles)
    payloads = payloads or {}
    detail_payloads = detail_payloads or {}

    public_items: list[dict[str, Any]] = []
    review_queue: list[dict[str, Any]] = []
    source_states: list[dict[str, Any]] = []
    discarded_total = 0
    candidate_total = 0

    def detail_loader(url: str) -> str:
        if url in detail_payloads:
            return detail_payloads[url]
        return "" if payloads else base.fetch(url)

    for raw_source in config["sources"]:
        source = {**raw_source, "_towns": towns}
        try:
            payload = payloads.get(source["id"])
            if payload is None:
                payload = base.fetch(source["url"])

            if source["type"] == "html_cards":
                candidates = quality.collect_html(source, today, payload, detail_loader)
            elif source["type"] == "jsonld_grants":
                candidates = quality.collect_grants(source, today, payload, detail_loader)
            elif source["type"] == "padigitale_json":
                candidates = base.collect_pad(source, today, payload)
            else:
                raise ValueError(f"Tipo non supportato: {source['type']}")

            candidate_total += len(candidates)
            source_public = 0
            source_review = 0
            source_discarded = 0

            for candidate in candidates:
                resolved = resolve_municipalities(candidate, profiles, today)
                if resolved["eligibility"] == "not_relevant":
                    source_discarded += 1
                    continue
                if resolved["eligibility"] == "review":
                    if obvious_non_municipal(resolved):
                        source_discarded += 1
                    else:
                        review_queue.append(_compact_review(resolved))
                        source_review += 1
                    continue
                public_items.append(resolved)
                source_public += 1

            discarded_total += source_discarded
            source_states.append(
                {
                    "sourceId": source["id"],
                    "status": "ok",
                    "candidateCount": len(candidates),
                    "publicCount": source_public,
                    "reviewCount": source_review,
                    "discardedCount": source_discarded,
                    "freshness": source_freshness(source, payload, candidates, today),
                    "error": None,
                }
            )
        except (ValueError, json.JSONDecodeError, urllib.error.URLError, TimeoutError) as exc:
            source_states.append(
                {
                    "sourceId": source["id"],
                    "status": "error",
                    "candidateCount": 0,
                    "publicCount": 0,
                    "reviewCount": 0,
                    "discardedCount": 0,
                    "freshness": {
                        "status": "unknown",
                        "observedDate": None,
                        "ageDays": None,
                        "maxAgeDays": int(source.get("freshnessMaxDays") or 60),
                    },
                    "error": str(exc),
                }
            )

    public_items = _dedupe(public_items)
    review_queue = _dedupe(review_queue)

    municipality_summary: dict[str, dict[str, int]] = {}
    for town in towns:
        eligible = 0
        conditional = 0
        for item in public_items:
            status = item["municipality_eligibility"][town]["status"]
            eligible += status == "eligible"
            conditional += status == "conditional"
        municipality_summary[town] = {"eligible": eligible, "conditional": conditional}

    counts = {
        "candidates": candidate_total,
        "public": len(public_items),
        "eligible": sum(item["eligibility"] == "eligible" for item in public_items),
        "conditional": sum(item["eligibility"] == "conditional" for item in public_items),
        "reviewInternal": len(review_queue),
        "discardedNonMunicipal": discarded_total,
        "staleSources": sum(
            state["freshness"]["status"] == "stale" for state in source_states
        ),
    }

    return {
        "schemaVersion": 2,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "referenceDate": today.isoformat(),
        "municipalities": towns,
        "counts": counts,
        "municipalitySummary": municipality_summary,
        "sources": source_states,
        "opportunities": public_items,
        "reviewQueue": review_queue,
    }


def render_markdown(result: dict[str, Any]) -> str:
    counts = result["counts"]
    lines = [
        "# Radar Opportunità Versilia — v0.2",
        "",
        f"Data di riferimento: **{result['referenceDate']}**",
        "",
        (
            f"Candidati raccolti: **{counts['candidates']}** · output operativo: **{counts['public']}** "
            f"({counts['eligible']} eligible, {counts['conditional']} conditional) · "
            f"review interna: **{counts['reviewInternal']}** · scartati: **{counts['discardedNonMunicipal']}**."
        ),
        "",
        "## Fonti e freschezza",
        "",
    ]
    for source in result["sources"]:
        freshness = source["freshness"]
        marker = "OK" if source["status"] == "ok" else "ERRORE"
        lines.append(
            f"- **{marker}** `{source['sourceId']}`: {source['publicCount']} operative, "
            f"{source['reviewCount']} review, {source['discardedCount']} scartate · "
            f"freshness **{freshness['status']}**"
            + (f" ({freshness['observedDate']}, {freshness['ageDays']} giorni)" if freshness['observedDate'] else "")
            + (f" — {source['error']}" if source['error'] else "")
        )

    lines.extend(["", "## Sintesi per Comune", ""])
    for town, values in result["municipalitySummary"].items():
        lines.append(
            f"- **{town}**: {values['eligible']} ammissibili · {values['conditional']} condizionate"
        )

    lines.extend(["", "## Opportunità operative", ""])
    for item in result["opportunities"]:
        lines.extend(
            [
                f"### {item['title']}",
                f"- Fonte: {item['source_name']}",
                f"- Stato aggregato: **{item['eligibility']}**",
                f"- Scadenza: **{item.get('deadline_at') or 'non rilevata'}**",
                f"- URL: {item['url']}",
                "- Comuni:",
            ]
        )
        for town, entry in item["municipality_eligibility"].items():
            lines.append(f"  - {town}: **{entry['status']}** — {entry['reason']}")
        lines.append("")

    lines.extend(["## Coda interna review", ""])
    if not result["reviewQueue"]:
        lines.append("Nessun elemento in review.")
    else:
        for item in result["reviewQueue"][:20]:
            lines.append(
                f"- {item['title']} — {item['source_id']} — {item.get('deadline_at') or 'scadenza non rilevata'}"
            )
        if len(result["reviewQueue"]) > 20:
            lines.append(f"- … altri {len(result['reviewQueue']) - 20} elementi")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    today = date.fromisoformat(args.date)
    result = run(args.config, today)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(render_markdown(result), encoding="utf-8")

    return 1 if any(source["status"] == "error" for source in result["sources"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
