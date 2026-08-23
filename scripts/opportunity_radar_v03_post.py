#!/usr/bin/env python3
"""Hardening finale v0.3: detail verificati e deduplica semantica per rule_id."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _source_config(config_path: Path) -> dict[str, dict[str, Any]]:
    cfg = _load(config_path)
    return {str(x.get("id")): x for x in cfg.get("sources") or []}


def _verified_text(radar, entry: dict[str, Any], detail_payloads: dict[str, str] | None, live: bool) -> str | None:
    url = str(entry.get("url") or "")
    if detail_payloads and url in detail_payloads:
        raw = detail_payloads[url]
    elif live:
        try:
            raw = radar.v025.v022.fetch_resilient(url, timeout=30, attempts=2)
        except Exception:
            return None
    else:
        return None
    text = radar.base.visible(raw)
    folded = radar.v025.fold(text)
    if not all(radar.v025.fold(term) in folded for term in entry.get("required_terms") or []):
        return None
    return text


def _build_verified_item(
    radar,
    entry: dict[str, Any],
    rule: dict[str, Any],
    source: dict[str, Any],
    towns: list[str],
    today: date,
    presentation_path: Path,
    policy: dict[str, Any],
    source_state: dict[str, Any] | None,
) -> dict[str, Any]:
    status = str(rule.get("force_eligibility") or "conditional")
    reason = str(rule.get("municipality_reason") or rule.get("beneficiary_evidence") or "Ammissibilità documentata dalla fonte ufficiale.")
    matrix = {town: {"status": status, "reason": reason} for town in towns}
    item = {
        "id": radar.base.sid(str(entry["source_id"]), str(entry["title"]), str(entry["url"])),
        "source_id": entry["source_id"],
        "source_name": source.get("name") or source.get("publisher") or entry["source_id"],
        "publisher": source.get("publisher") or source.get("name") or entry["source_id"],
        "title": entry["title"],
        "url": entry["url"],
        "summary": entry.get("summary") or rule.get("project_requirements") or "",
        "status": "open",
        "opens_at": None,
        "deadline_at": entry.get("deadline_at") or rule.get("deadline_override"),
        "deadline_time": entry.get("deadline_time"),
        "published_at": None,
        "beneficiary_text": rule.get("beneficiary_evidence") or "",
        "municipalities": towns[:],
        "eligibility": status,
        "eligibility_reason": reason,
        "municipality_eligibility": matrix,
        "applicant_eligibility": rule.get("applicant_eligibility_override") or status,
        "applicant_type": rule.get("applicant_type"),
        "municipality_role": rule.get("municipality_role"),
        "final_beneficiaries": rule.get("final_beneficiaries"),
        "partnership_required": bool(rule.get("partnership_required", False)),
        "project_requirements": rule.get("project_requirements"),
        "geographic_scope": rule.get("geographic_scope"),
        "geographic_eligibility": rule.get("geographic_eligibility"),
        "territorial_relevance": rule.get("territorial_relevance"),
        "actionable_for_municipality": bool(rule.get("actionable", True)),
        "decision_class": rule.get("decision_class"),
        "rule_id": rule["id"],
        "themes": ["cultura"] if str(rule.get("id", "")).startswith("mic-") else [],
        "eligibility_evidence": {
            "rule_id": rule["id"],
            "text": rule.get("beneficiary_evidence") or rule.get("project_requirements"),
            "source_url": rule.get("evidence_url") or entry.get("url"),
        },
        "verified_direct": True,
        "verified_at": today.isoformat(),
    }
    registry = radar.v025.v024.load_presentation(presentation_path)
    item = radar.v025.v024.enrich_item(item, registry)
    if entry.get("deadline_time"):
        item["deadline_time"] = entry["deadline_time"]
    gate = radar.v025.v022._quality_gate(item, source_state, policy, today)
    item["quality_gate"] = gate
    return item


def inject_verified_details(
    radar,
    result: dict[str, Any],
    config_path: Path,
    today: date,
    presentation_path: Path,
    verified_path: Path,
    *,
    detail_payloads: dict[str, str] | None = None,
    live: bool = True,
) -> None:
    payload = _load(verified_path)
    rules, policy, _ = radar.load_rules()
    by_rule = {str(rule.get("id")): rule for rule in rules}
    sources = _source_config(config_path)
    states = {str(x.get("sourceId")): x for x in result.get("sources") or []}
    towns = list(result.get("municipalities") or [])
    existing_rules = {str(x.get("rule_id")) for x in result.get("opportunities") or [] if x.get("rule_id")}

    for entry in payload.get("entries") or []:
        rule_id = str(entry.get("rule_id") or "")
        if not rule_id or rule_id in existing_rules:
            continue
        rule = by_rule.get(rule_id)
        source = sources.get(str(entry.get("source_id") or ""))
        if not rule or not source:
            continue
        if not _verified_text(radar, entry, detail_payloads, live):
            continue
        item = _build_verified_item(
            radar, entry, rule, source, towns, today, presentation_path, policy,
            states.get(str(entry.get("source_id") or "")),
        )
        if item.get("quality_gate", {}).get("status") != "pass":
            result.setdefault("qualityHold", []).append(item)
            continue
        result.setdefault("opportunities", []).append(item)
        existing_rules.add(rule_id)


def canonicalize_by_rule(radar, result: dict[str, Any], verified_path: Path) -> None:
    verified = _load(verified_path)
    canonical = {str(x.get("rule_id")): x for x in verified.get("entries") or [] if x.get("canonical")}
    items = list(result.get("opportunities") or [])
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        rule_id = str(item.get("rule_id") or "")
        deadline = str(item.get("deadline_at") or "")
        key = f"rule:{rule_id}|deadline:{deadline}" if rule_id else f"id:{item.get('id')}"
        groups.setdefault(key, []).append(item)

    output: list[dict[str, Any]] = []
    collapsed = 0
    duplicate_groups = 0
    for group in groups.values():
        if len(group) == 1:
            output.append(group[0])
            continue
        duplicate_groups += 1
        collapsed += len(group) - 1
        rule_id = str(group[0].get("rule_id") or "")
        preferred = canonical.get(rule_id)
        primary = None
        if preferred:
            primary = next((x for x in group if str(x.get("url")) == str(preferred.get("url"))), None)
        if primary is None:
            primary = max(group, key=lambda x: radar.v025._completeness(x))
        primary = dict(primary)
        seen_sources: list[str] = []
        seen_urls: list[str] = []
        for item in group:
            sid = str(item.get("source_id") or "")
            url = str(item.get("url") or "")
            if sid and sid not in seen_sources:
                seen_sources.append(sid)
            if url and url not in seen_urls:
                seen_urls.append(url)
            if item is not primary:
                radar.v025._merge_matrix(primary, item)
        if preferred:
            primary["title"] = preferred.get("title") or primary.get("title")
            primary["url"] = preferred.get("url") or primary.get("url")
        primary["also_seen_in"] = seen_sources
        primary["also_seen_urls"] = seen_urls
        output.append(primary)

    output.sort(key=lambda x: (str(x.get("deadline_at") or "9999-99-99"), str(x.get("title") or "")))
    result["opportunities"] = output
    dedupe = result.setdefault("deduplication", {})
    dedupe["recordsCollapsed"] = int(dedupe.get("recordsCollapsed") or 0) + collapsed
    dedupe["duplicateGroups"] = int(dedupe.get("duplicateGroups") or 0) + duplicate_groups
    dedupe["outputRecords"] = len(output)
    result.setdefault("counts", {})["public"] = len(output)
    result["counts"]["eligible"] = sum(x.get("eligibility") == "eligible" for x in output)
    result["counts"]["conditional"] = sum(x.get("eligibility") == "conditional" for x in output)
    result["counts"]["duplicatesCollapsed"] = dedupe["recordsCollapsed"]
    for state in result.get("sources") or []:
        sid = str(state.get("sourceId") or "")
        state["publicCount"] = sum(str(x.get("source_id") or "") == sid for x in output)
    radar.v025._recompute_summary(result)


def harden(
    radar,
    result: dict[str, Any],
    config_path: Path,
    today: date,
    presentation_path: Path,
    verified_path: Path,
    *,
    detail_payloads: dict[str, str] | None = None,
    live: bool = True,
) -> dict[str, Any]:
    inject_verified_details(
        radar, result, config_path, today, presentation_path, verified_path,
        detail_payloads=detail_payloads, live=live,
    )
    canonicalize_by_rule(radar, result, verified_path)
    radar.attach_source_visuals(result, presentation_path)
    result["engineVersion"] = "0.3.2"
    result["uiVersion"] = "0.3.2"
    return result
