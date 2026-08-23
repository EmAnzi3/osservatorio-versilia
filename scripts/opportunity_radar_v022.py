#!/usr/bin/env python3
"""Radar Opportunità Versilia v0.2.2.

Consolida la semantica v0.2.1 con due livelli ulteriori:
- chiusura documentale della coda di collaudo umano v0.2.1;
- quality gate che separa candidati operativi da record realmente esponibili.

Nessun dato viene pubblicato sul sito.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opportunity_radar_v021 as v021

v02 = v021.v02
base = v02.base
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "data" / "opportunity-sources.json"
DEFAULT_RULES = ROOT / "data" / "opportunity-rules-v022.json"

ACTIVE_POLICY: dict[str, Any] = {}
V022_STATS: dict[str, int] = {}


def load_policy(path: Path = DEFAULT_RULES) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    base_name = payload.get("baseRulesFile") or "opportunity-rules-v021.json"
    base_path = path.parent / base_name
    merged: dict[str, dict[str, Any]] = {rule["id"]: dict(rule) for rule in v021.load_rules(base_path)}
    order = [rule["id"] for rule in v021.load_rules(base_path)]

    for overlay in payload.get("rules") or []:
        rule_id = overlay.get("id")
        if not rule_id:
            raise ValueError("Regola v0.2.2 senza id.")
        if rule_id not in merged:
            order.append(rule_id)
            merged[rule_id] = {}
        merged[rule_id] = {**merged[rule_id], **overlay, "_v022": True}

    return [merged[rule_id] for rule_id in order], payload.get("qualityGate") or {}


def _recompute_municipality_aggregate(resolved: dict[str, Any], today: date) -> None:
    matrix = resolved.get("municipality_eligibility") or {}
    statuses = [entry.get("status") for entry in matrix.values()]
    if "eligible" in statuses:
        aggregate = "eligible"
    elif "conditional" in statuses:
        aggregate = "conditional"
    elif "review" in statuses:
        aggregate = "review"
    else:
        aggregate = "not_relevant"
    resolved["eligibility"] = aggregate
    resolved["municipalities"] = [
        town for town, entry in matrix.items() if entry.get("status") in {"eligible", "conditional"}
    ]
    resolved["priority"] = base.priority(
        aggregate, resolved.get("deadline_at"), resolved.get("themes") or [], today
    )


def resolve_municipalities(
    item: dict[str, Any], profiles: dict[str, dict[str, Any]], today: date
) -> dict[str, Any]:
    """Applica le regole documentali v0.2.2 sopra il resolver v0.2.1."""
    rule = v021.matching_rule(item)
    working = dict(item)
    original_status = item.get("eligibility", "review")

    if rule and rule.get("deadline_override"):
        working["deadline_at"] = rule["deadline_override"]

    resolved = v021.resolve_municipalities(working, profiles, today)
    rule = v021.matching_rule(working)
    if not rule:
        return resolved

    resolved["decision_class"] = rule.get("decision_class")
    resolved["exclusion_code"] = rule.get("exclusion_code")
    resolved["opportunity_type"] = rule.get("opportunity_type", "funding")
    resolved["lifecycle_stage"] = rule.get("lifecycle_stage", "application_open")
    resolved["deadline_evidence"] = rule.get("deadline_evidence")
    resolved["territorial_evidence_url"] = rule.get("territorial_evidence_url")

    if rule.get("applicant_eligibility_override"):
        resolved["applicant_eligibility"] = rule["applicant_eligibility_override"]

    overrides = rule.get("municipality_status_overrides") or {}
    if overrides:
        for town, override in overrides.items():
            if town in resolved.get("municipality_eligibility", {}):
                resolved["municipality_eligibility"][town] = {
                    "status": override["status"],
                    "reason": override["reason"],
                }
        _recompute_municipality_aggregate(resolved, today)
        V022_STATS["municipalityOverrides"] = V022_STATS.get("municipalityOverrides", 0) + 1

    if rule.get("opportunity_type") == "non_financial_award":
        resolved["eligibility"] = "not_relevant"
        resolved["actionable_for_municipality"] = False
        resolved["eligibility_reason"] = rule.get("suppress_reason") or "Opportunità non finanziaria."
        V022_STATS["typeSuppressed"] = V022_STATS.get("typeSuppressed", 0) + 1

    if rule.get("lifecycle_stage") == "implementation_only":
        resolved["eligibility"] = "not_relevant"
        resolved["actionable_for_municipality"] = False
        resolved["eligibility_reason"] = rule.get("suppress_reason") or "Fase di candidatura conclusa."
        V022_STATS["lifecycleSuppressed"] = V022_STATS.get("lifecycleSuppressed", 0) + 1

    if rule.get("_v022") and original_status == "review":
        V022_STATS["humanReviewMatched"] = V022_STATS.get("humanReviewMatched", 0) + 1
        if resolved.get("eligibility") in {"eligible", "conditional"}:
            V022_STATS["humanReviewPromoted"] = V022_STATS.get("humanReviewPromoted", 0) + 1
        elif resolved.get("eligibility") == "not_relevant":
            V022_STATS["humanReviewSuppressed"] = V022_STATS.get("humanReviewSuppressed", 0) + 1

    return resolved


def _quality_gate(
    item: dict[str, Any], source_state: dict[str, Any] | None, policy: dict[str, Any], today: date
) -> dict[str, Any]:
    reasons: list[str] = []
    missing: list[str] = []

    for field in policy.get("requiredFields") or []:
        value = item.get(field)
        if value is None or value == "" or value == {} or value == []:
            missing.append(field)

    evidence = item.get("eligibility_evidence") or {}
    if not evidence.get("source_url"):
        missing.append("eligibility_evidence.source_url")

    if item.get("municipality_role") in {None, "unknown", "none"}:
        reasons.append("municipality_role non operativo")

    if item.get("geographic_eligibility") in {None, "unknown", "not_eligible", "not_applicable"}:
        reasons.append("geografia non validata per un uso comunale")

    if item.get("territorial_relevance") in {None, "unknown", "none", "requires_versilia_nexus"}:
        reasons.append("pertinenza territoriale non sufficiente")

    if policy.get("requireActionable") and not item.get("actionable_for_municipality"):
        reasons.append("opportunità non azionabile dal Comune")

    if policy.get("requireMunicipalityMatch"):
        matrix = item.get("municipality_eligibility") or {}
        if not any(entry.get("status") in {"eligible", "conditional"} for entry in matrix.values()):
            reasons.append("nessun Comune della Versilia ammissibile o condizionale")

    if policy.get("conditionalRequiresProjectRequirements") and item.get("eligibility") == "conditional":
        if not item.get("project_requirements"):
            missing.append("project_requirements")

    deadline = base.parse_date(item.get("deadline_at")) if item.get("deadline_at") else None
    if deadline and deadline < today:
        reasons.append("scadenza per nuove domande già trascorsa")

    if policy.get("requireCurrentSource"):
        freshness = (source_state or {}).get("freshness") or {}
        if freshness.get("status") != "current":
            reasons.append(f"fonte non current: {freshness.get('status', 'unknown')}")

    indirect = set(policy.get("allowedIndirectRoles") or [])
    if item.get("applicant_eligibility") == "not_direct_applicant" and item.get("municipality_role") not in indirect:
        reasons.append("richiedente non comunale senza ruolo indiretto ammesso")

    missing = sorted(set(missing))
    reasons = sorted(set(reasons))
    return {
        "status": "pass" if not missing and not reasons else "hold",
        "missing": missing,
        "reasons": reasons,
    }


def _recompute_summaries(result: dict[str, Any]) -> None:
    towns = list(result.get("municipalitySummary") or {})
    summary: dict[str, dict[str, int]] = {}
    for town in towns:
        eligible = 0
        conditional = 0
        for item in result["opportunities"]:
            state = item["municipality_eligibility"][town]["status"]
            eligible += state == "eligible"
            conditional += state == "conditional"
        summary[town] = {"eligible": eligible, "conditional": conditional}
    result["municipalitySummary"] = summary


def run(
    config_path: Path,
    today: date,
    payloads: dict[str, str] | None = None,
    detail_payloads: dict[str, str] | None = None,
    rules_path: Path = DEFAULT_RULES,
) -> dict[str, Any]:
    global ACTIVE_POLICY, V022_STATS
    rules, ACTIVE_POLICY = load_policy(rules_path)
    V022_STATS = {
        "humanReviewMatched": 0,
        "humanReviewPromoted": 0,
        "humanReviewSuppressed": 0,
        "municipalityOverrides": 0,
        "typeSuppressed": 0,
        "lifecycleSuppressed": 0,
    }
    v021.ACTIVE_RULES = rules
    v021.RULE_STATS = {
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

    source_by_id = {source["sourceId"]: source for source in result["sources"]}
    pre_gate = list(result["opportunities"])
    passed: list[dict[str, Any]] = []
    held: list[dict[str, Any]] = []
    for item in pre_gate:
        gate = _quality_gate(item, source_by_id.get(item.get("source_id")), ACTIVE_POLICY, today)
        item["quality_gate"] = gate
        if gate["status"] == "pass":
            passed.append(item)
        else:
            held.append(item)

    result["schemaVersion"] = "2.2"
    result["opportunities"] = passed
    result["qualityHold"] = held
    result["qualityGatePolicy"] = ACTIVE_POLICY
    result["v022Stats"] = dict(V022_STATS)
    result["ruleStats"] = {**v021.RULE_STATS, **V022_STATS}

    result["counts"]["preQualityOperational"] = len(pre_gate)
    result["counts"]["public"] = len(passed)
    result["counts"]["eligible"] = sum(item["eligibility"] == "eligible" for item in passed)
    result["counts"]["conditional"] = sum(item["eligibility"] == "conditional" for item in passed)
    result["counts"]["qualityPassed"] = len(passed)
    result["counts"]["qualityHeld"] = len(held)
    result["counts"]["humanReviewMatched"] = V022_STATS["humanReviewMatched"]
    result["counts"]["humanReviewPromoted"] = V022_STATS["humanReviewPromoted"]
    result["counts"]["humanReviewSuppressed"] = V022_STATS["humanReviewSuppressed"]

    for source in result["sources"]:
        source_id = source["sourceId"]
        source["preQualityPublicCount"] = source.get("publicCount", 0)
        source["publicCount"] = sum(item.get("source_id") == source_id for item in passed)
        source["qualityHoldCount"] = sum(item.get("source_id") == source_id for item in held)

    _recompute_summaries(result)
    return result


def render_markdown(result: dict[str, Any]) -> str:
    counts = result["counts"]
    stats = result.get("v022Stats") or {}
    lines = [
        "# Radar Opportunità Versilia — v0.2.2",
        "",
        f"Data di riferimento: **{result['referenceDate']}**",
        "",
        (
            f"Candidati: **{counts['candidates']}** · candidati operativi pre-gate: "
            f"**{counts['preQualityOperational']}** · quality pass: **{counts['qualityPassed']}** "
            f"({counts['eligible']} eligible, {counts['conditional']} conditional) · "
            f"quality hold: **{counts['qualityHeld']}** · review semantica interna: "
            f"**{counts['reviewInternal']}** · scartati/non operativi: **{counts['discardedNonMunicipal']}**."
        ),
        (
            f"Collaudo umano v0.2.2: **{stats.get('humanReviewMatched', 0)}** casi riconosciuti · "
            f"**{stats.get('humanReviewPromoted', 0)}** promossi · "
            f"**{stats.get('humanReviewSuppressed', 0)}** esclusi."
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
            f"{source.get('publicCount', 0)} quality-pass, {source.get('qualityHoldCount', 0)} hold, "
            f"{source.get('reviewCount', 0)} review · freshness **{fresh.get('status', 'unknown')}**{observed}"
        )

    lines += ["", "## Opportunità quality-pass", ""]
    if not result["opportunities"]:
        lines.append("Nessuna opportunità supera il quality gate.")
    for item in result["opportunities"]:
        lines += [
            f"### {item['title']}",
            f"- Fonte: {item['source_name']}",
            f"- Stato: **{item['eligibility']}**",
            f"- Ruolo Comune: **{item.get('municipality_role', 'unknown')}**",
            f"- Richiedente: **{item.get('applicant_eligibility', 'unknown')}**",
            f"- Geografia: **{item.get('geographic_eligibility', 'unknown')}** — {item.get('geographic_scope') or 'non determinata'}",
            f"- Pertinenza: **{item.get('territorial_relevance', 'unknown')}**",
            f"- Scadenza: **{item.get('deadline_at') or 'non rilevata'}**",
            f"- Quality gate: **{item.get('quality_gate', {}).get('status', 'unknown')}**",
            f"- Regola: `{item.get('rule_id', 'nessuna')}`",
            f"- URL: {item['url']}",
        ]
        if item.get("project_requirements"):
            lines.append(f"- Condizioni chiave: {item['project_requirements']}")
        lines.append("- Comuni:")
        for town, entry in item["municipality_eligibility"].items():
            lines.append(f"  - {town}: **{entry['status']}** — {entry['reason']}")
        lines.append("")

    lines += ["## Quality hold", ""]
    if not result["qualityHold"]:
        lines.append("Nessun candidato operativo è bloccato dal quality gate.")
    else:
        for item in result["qualityHold"]:
            gate = item["quality_gate"]
            detail = "; ".join(gate["missing"] + gate["reasons"])
            lines.append(f"- {item['title']} — {detail}")

    lines += ["", "## Review semantica interna", ""]
    if not result["reviewQueue"]:
        lines.append("Nessun elemento residuo nella review del campione corrente.")
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
