#!/usr/bin/env python3
"""Radar Opportunita Versilia v0.2.1.

Correzione semantica della v0.2: distingue ammissibilita del richiedente,
ruolo operativo del Comune e pertinenza geografico-territoriale. Le eccezioni
sono regole documentali versionate, non inferenze generative.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opportunity_radar_v02 as v02

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "data" / "opportunity-sources.json"
DEFAULT_RULES = ROOT / "data" / "opportunity-rules-v021.json"
ORIGINAL_RESOLVE = v02.resolve_municipalities
ACTIVE_RULES: list[dict[str, Any]] = []
RULE_STATS: dict[str, int] = {}


def fold(value: Any) -> str:
    text = v02.norm(value)
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch)
    )


def load_rules(path: Path = DEFAULT_RULES) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rules = payload.get("rules")
    if not isinstance(rules, list):
        raise ValueError("Il registro regole v0.2.1 non contiene una lista 'rules'.")
    return rules


def matching_rule(item: dict[str, Any], rules: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    rules = rules if rules is not None else (ACTIVE_RULES or load_rules())
    title = fold(item.get("title", ""))
    source_id = item.get("source_id")
    for rule in rules:
        if rule.get("source_id") and rule["source_id"] != source_id:
            continue
        pattern = fold(rule.get("title_pattern", ""))
        if pattern and re.search(pattern, title, re.I):
            return rule
    return None


def has_versilia_nexus(item: dict[str, Any], towns: list[str]) -> bool:
    context = fold(
        f"{item.get('title', '')}. {item.get('summary', '')}. {item.get('beneficiary_text', '')}"
    )
    if "versilia" in context:
        return True
    return any(re.search(rf"\b{re.escape(fold(town))}\b", context) for town in towns)


def _matrix_not_eligible(profiles: dict[str, dict[str, Any]], reason: str) -> dict[str, dict[str, str]]:
    return {town: {"status": "not_eligible", "reason": reason} for town in profiles}


def _annotate_rule(resolved: dict[str, Any], rule: dict[str, Any]) -> None:
    resolved["rule_id"] = rule["id"]
    resolved["applicant_type"] = rule.get("applicant_type")
    resolved["municipality_role"] = rule.get("municipality_role", "unknown")
    resolved["final_beneficiaries"] = rule.get("final_beneficiaries")
    resolved["partnership_required"] = bool(rule.get("partnership_required", False))
    resolved["project_requirements"] = rule.get("project_requirements")
    resolved["geographic_scope"] = rule.get("geographic_scope")
    resolved["geographic_eligibility"] = rule.get("geographic_eligibility", "unknown")
    resolved["territorial_relevance"] = rule.get("territorial_relevance", "unknown")
    resolved["eligibility_evidence"] = {
        "rule_id": rule["id"],
        "text": rule.get("beneficiary_evidence") or rule.get("project_requirements"),
        "source_url": rule.get("evidence_url"),
    }


def resolve_municipalities(
    item: dict[str, Any], profiles: dict[str, dict[str, Any]], today: date
) -> dict[str, Any]:
    """Risoluzione v0.2.1: applicant + ruolo + geografia + azionabilita."""
    rule = matching_rule(item)
    working = dict(item)
    original_status = item.get("eligibility", "review")

    if rule and rule.get("force_eligibility"):
        working["eligibility"] = rule["force_eligibility"]
    if rule and rule.get("beneficiary_evidence"):
        working["beneficiary_text"] = v02.clean(
            f"{working.get('beneficiary_text', '')}. {rule['beneficiary_evidence']}"
        )

    resolved = ORIGINAL_RESOLVE(working, profiles, today)
    applicant_status = resolved.get("eligibility", "review")
    resolved["applicant_eligibility"] = applicant_status

    if not rule:
        # In v0.2.1 nessun nuovo caso generico entra automaticamente nell'output operativo.
        resolved["municipality_role"] = "unknown"
        resolved["geographic_eligibility"] = "unknown"
        resolved["territorial_relevance"] = "unknown"
        resolved["actionable_for_municipality"] = False
        if resolved["eligibility"] in {"eligible", "conditional"}:
            resolved["eligibility"] = "review"
            resolved["eligibility_reason"] = (
                "Manca una regola documentale v0.2.1 su richiedente, ruolo o geografia; "
                "il caso resta nella coda interna."
            )
        return resolved

    _annotate_rule(resolved, rule)
    RULE_STATS["matched"] = RULE_STATS.get("matched", 0) + 1

    if rule.get("municipality_role") == "none":
        reason = rule.get("suppress_reason") or "Il Comune non ha un ruolo operativo previsto dal bando."
        resolved["municipality_eligibility"] = _matrix_not_eligible(profiles, reason)
        resolved["municipalities"] = []
        resolved["applicant_eligibility"] = "not_eligible"
        resolved["eligibility"] = "not_relevant"
        resolved["eligibility_reason"] = reason
        resolved["actionable_for_municipality"] = False
        RULE_STATS["role_suppressed"] = RULE_STATS.get("role_suppressed", 0) + 1
        return resolved

    if rule.get("requires_versilia_nexus"):
        nexus = has_versilia_nexus(working, list(profiles))
        resolved["versilia_nexus"] = nexus
        if not nexus:
            reason = rule.get("suppress_reason") or "Manca un nesso territoriale documentato con la Versilia."
            resolved["territorial_relevance"] = "none"
            resolved["actionable_for_municipality"] = False
            resolved["eligibility"] = "not_relevant"
            resolved["eligibility_reason"] = reason
            RULE_STATS["geography_suppressed"] = RULE_STATS.get("geography_suppressed", 0) + 1
            return resolved
        resolved["territorial_relevance"] = "conditional"
        resolved["actionable_for_municipality"] = True
    else:
        resolved["actionable_for_municipality"] = bool(rule.get("actionable", True))

    if original_status == "review" and resolved["eligibility"] in {"eligible", "conditional"}:
        RULE_STATS["promoted_from_review"] = RULE_STATS.get("promoted_from_review", 0) + 1

    return resolved


def run(
    config_path: Path,
    today: date,
    payloads: dict[str, str] | None = None,
    detail_payloads: dict[str, str] | None = None,
    rules_path: Path = DEFAULT_RULES,
) -> dict[str, Any]:
    global ACTIVE_RULES, RULE_STATS
    ACTIVE_RULES = load_rules(rules_path)
    RULE_STATS = {
        "matched": 0,
        "promoted_from_review": 0,
        "role_suppressed": 0,
        "geography_suppressed": 0,
    }

    previous = v02.resolve_municipalities
    v02.resolve_municipalities = resolve_municipalities
    try:
        result = v02.run(config_path, today, payloads=payloads, detail_payloads=detail_payloads)
    finally:
        v02.resolve_municipalities = previous

    result["schemaVersion"] = "2.1"
    result["ruleStats"] = dict(RULE_STATS)
    result["counts"]["rulePromotedFromReview"] = RULE_STATS["promoted_from_review"]
    result["counts"]["roleSuppressed"] = RULE_STATS["role_suppressed"]
    result["counts"]["geographySuppressed"] = RULE_STATS["geography_suppressed"]
    return result


def render_markdown(result: dict[str, Any]) -> str:
    counts = result["counts"]
    stats = result.get("ruleStats", {})
    lines = [
        "# Radar Opportunita Versilia — v0.2.1",
        "",
        f"Data di riferimento: **{result['referenceDate']}**",
        "",
        (
            f"Candidati: **{counts['candidates']}** · output operativo: **{counts['public']}** "
            f"({counts['eligible']} eligible, {counts['conditional']} conditional) · "
            f"review interna: **{counts['reviewInternal']}** · scartati/non operativi: "
            f"**{counts['discardedNonMunicipal']}**."
        ),
        (
            f"Regole v0.2.1: **{stats.get('matched', 0)}** match · "
            f"**{stats.get('promoted_from_review', 0)}** promossi dalla review · "
            f"**{stats.get('role_suppressed', 0)}** esclusi per ruolo · "
            f"**{stats.get('geography_suppressed', 0)}** esclusi per pertinenza geografica."
        ),
        "",
        "## Fonti e freschezza",
        "",
    ]
    for source in result["sources"]:
        fresh = source.get("freshness") or {}
        observed = f" ({fresh.get('observedDate')})" if fresh.get("observedDate") else ""
        lines.append(
            f"- **{source['status'].upper()}** `{source['sourceId']}`: "
            f"{source.get('publicCount', 0)} operative, {source.get('reviewCount', 0)} review, "
            f"{source.get('discardedCount', 0)} scartate · freshness **{fresh.get('status', 'unknown')}**{observed}"
        )
    lines += ["", "## Opportunita operative", ""]
    if not result["opportunities"]:
        lines.append("Nessuna opportunita operativa.")
    for item in result["opportunities"]:
        lines += [
            f"### {item['title']}",
            f"- Fonte: {item['source_name']}",
            f"- Stato operativo: **{item['eligibility']}**",
            f"- Ammissibilita richiedente: **{item.get('applicant_eligibility', 'unknown')}**",
            f"- Ruolo Comune: **{item.get('municipality_role', 'unknown')}**",
            f"- Pertinenza territoriale: **{item.get('territorial_relevance', 'unknown')}**",
            f"- Ambito geografico: {item.get('geographic_scope') or 'non determinato'}",
            f"- Beneficiari finali: {item.get('final_beneficiaries') or 'non determinati'}",
            f"- Scadenza: **{item.get('deadline_at') or 'non rilevata'}**",
            f"- Regola/evidenza: `{item.get('rule_id', 'nessuna')}`",
            f"- URL: {item['url']}",
        ]
        if item.get("project_requirements"):
            lines.append(f"- Requisiti chiave: {item['project_requirements']}")
        lines.append("- Comuni:")
        for town, entry in item["municipality_eligibility"].items():
            lines.append(f"  - {town}: **{entry['status']}** — {entry['reason']}")
        lines.append("")
    lines += ["## Coda interna review", ""]
    if not result["reviewQueue"]:
        lines.append("Nessun elemento in review.")
    else:
        for item in result["reviewQueue"]:
            lines.append(
                f"- {item['title']} — {item['source_id']} — {item.get('deadline_at') or 'scadenza non rilevata'}"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)

    result = run(args.config, args.date, rules_path=args.rules)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = render_markdown(result)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
    elif not args.output:
        print(report, end="")

    return 1 if any(source["status"] == "error" for source in result["sources"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
