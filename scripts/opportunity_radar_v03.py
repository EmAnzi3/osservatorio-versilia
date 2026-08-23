#!/usr/bin/env python3
"""Radar Opportunità Versilia v0.3.

Prima espansione controllata delle fonti:
- PR Toscana FESR e FSE+ entrano nel collector operativo;
- ANCI/ANCI Toscana, GSE e Ministero dell'Interno entrano come canali di discovery;
- i canali di discovery non possono pubblicare un'opportunità da soli: i casi trovati
  restano in una coda interna finché non vengono ricondotti alla fonte ufficiale e
  a una regola documentale.
- la UI riceve metadati fonte/favicons e una matrice di copertura completa.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opportunity_radar_v025 as v025

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "data" / "opportunity-sources-v03.json"
DEFAULT_RULES = ROOT / "data" / "opportunity-rules-v03.json"
DEFAULT_PRESENTATION = ROOT / "data" / "opportunity-presentation-v03.json"
DEFAULT_COVERAGE = ROOT / "data" / "opportunity-source-coverage-v03.json"
DEFAULT_BACKTEST = ROOT / "data" / "opportunity-backtest-v03.json"

base = v025.base
v021 = v025.v021


def load_rules(path: Path = DEFAULT_RULES) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    base_name = payload.get("baseRulesFile") or "opportunity-rules-v025.json"
    rules, policy = v025.load_overlay(path.parent / base_name)
    merged = {rule["id"]: dict(rule) for rule in rules}
    order = [rule["id"] for rule in rules]
    for overlay in payload.get("rules") or []:
        rule_id = overlay.get("id")
        if not rule_id:
            raise ValueError("Regola v0.3 senza id.")
        if rule_id not in merged:
            order.append(rule_id)
            merged[rule_id] = {}
        merged[rule_id] = {**merged[rule_id], **overlay, "_v03": True}
    aliases = {str(k): str(v) for k, v in (payload.get("sourceAliases") or {}).items()}
    return [merged[rule_id] for rule_id in order], {**policy, **(payload.get("qualityGate") or {})}, aliases


def _matches_any(text: str, terms: list[str]) -> bool:
    folded = v025.fold(text)
    return any(v025.fold(term) in folded for term in terms if term)


def discovery_candidates(source: dict[str, Any], payload: str, page_url: str) -> list[dict[str, Any]]:
    parser = base.Cards()
    parser.feed(payload)
    parser.close()
    include_terms = list(source.get("includeTerms") or [])
    municipal_terms = list(source.get("municipalTerms") or [])
    out: list[dict[str, Any]] = []

    for title, href, body in parser.out:
        title = base.clean(title)
        body = base.clean(body)
        if len(title) < 7:
            continue
        combined = f"{title}. {body}"
        if include_terms and not _matches_any(combined, include_terms):
            continue
        if municipal_terms and not _matches_any(combined, municipal_terms):
            continue
        out.append(
            {
                "source_id": source["id"],
                "source_label": source.get("label") or source["id"],
                "publisher": source.get("publisher") or source.get("label"),
                "territory": source.get("territory"),
                "title": title,
                "url": urljoin(page_url, href) if href else page_url,
                "summary": body[:600],
                "discovery_only": True,
                "status": "internal_review",
                "reason": (
                    "Segnalazione emersa da un canale di discovery: prima dell'output pubblico "
                    "serve la fonte ufficiale del bando e la verifica documentale di richiedente, ruolo e geografia."
                ),
            }
        )

    if not out:
        visible = base.visible(payload)
        if _matches_any(visible, include_terms) and _matches_any(visible, municipal_terms):
            title = source.get("label") or source["id"]
            out.append(
                {
                    "source_id": source["id"],
                    "source_label": source.get("label") or source["id"],
                    "publisher": source.get("publisher") or source.get("label"),
                    "territory": source.get("territory"),
                    "title": f"Aggiornamenti da {title}",
                    "url": page_url,
                    "summary": visible[:600],
                    "discovery_only": True,
                    "status": "internal_review",
                    "reason": "Pagina ufficiale monitorata: nessuna scheda strutturata è stata promossa automaticamente.",
                }
            )
    return out


def probe_discovery_sources(
    config: dict[str, Any],
    *,
    payloads: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    payloads = payloads or {}
    queue: list[dict[str, Any]] = []
    states: list[dict[str, Any]] = []

    for source in config.get("discoverySources") or []:
        urls = list(source.get("urls") or [])
        endpoint_ok = 0
        endpoint_errors: list[str] = []
        source_candidates: list[dict[str, Any]] = []
        for url in urls:
            try:
                payload = payloads[url] if url in payloads else v025.v022.fetch_resilient(
                    url,
                    timeout=int(source.get("fetchTimeoutSeconds") or 25),
                    attempts=1,
                )
                endpoint_ok += 1
                source_candidates.extend(discovery_candidates(source, payload, url))
            except Exception as exc:
                endpoint_errors.append(f"{url}: {exc}")

        unique: dict[tuple[str, str], dict[str, Any]] = {}
        for item in source_candidates:
            key = (v025.fold(item.get("title")), v025.normalized_url(item.get("url")))
            unique[key] = item
        source_candidates = list(unique.values())[:50]
        queue.extend(source_candidates)

        if endpoint_ok == len(urls) and urls:
            runtime = "ok"
        elif endpoint_ok:
            runtime = "degraded"
        else:
            runtime = "error"
        states.append(
            {
                "sourceId": source["id"],
                "status": runtime,
                "endpointCount": len(urls),
                "endpointOk": endpoint_ok,
                "candidateCount": len(source_candidates),
                "errors": endpoint_errors,
                "freshness": {"status": "discovery", "observedDate": None, "ageDays": None},
            }
        )

    queue.sort(key=lambda item: (str(item.get("source_label") or ""), str(item.get("title") or "")))
    return queue, states


def build_coverage(
    result: dict[str, Any],
    registry: dict[str, Any],
    discovery_states: list[dict[str, Any]],
) -> dict[str, Any]:
    live = {str(state.get("sourceId")): state for state in result.get("sources") or []}
    discovery = {str(state.get("sourceId")): state for state in discovery_states}
    rows: list[dict[str, Any]] = []

    for source_id, meta in (registry.get("sources") or {}).items():
        role = meta.get("role")
        state = discovery.get(source_id) if role == "discovery" else live.get(source_id)
        state = state or {}
        freshness = state.get("freshness") or {}
        runtime = state.get("status", "not_run")
        row = {
            "source_id": source_id,
            "label": meta.get("label") or source_id,
            "monitoringStatus": meta.get("monitoringStatus"),
            "role": role,
            "priority": meta.get("priority"),
            "favicon": meta.get("favicon"),
            "listingDiscovery": bool(meta.get("listingDiscovery")),
            "detailEnrichment": bool(meta.get("detailEnrichment")),
            "pdfFallback": bool(meta.get("pdfFallback")),
            "archiveContinuity": bool(meta.get("archiveContinuity")),
            "historicalReplay": bool(meta.get("historicalReplay")),
            "runtimeStatus": runtime,
            "freshness": freshness.get("status", "unknown"),
            "observedDate": freshness.get("observedDate"),
            "publicCount": state.get("publicCount", 0),
            "candidateCount": state.get("candidateCount", state.get("count", 0)),
            "reviewCount": state.get("reviewCount", 0),
            "qualityHoldCount": state.get("qualityHoldCount", 0),
            "replacementNeeded": bool(meta.get("replacementNeeded")),
            "note": meta.get("note"),
        }
        rows.append(row)

    active = [row for row in rows if row["monitoringStatus"] == "active"]
    healthy = [
        row for row in active
        if row["runtimeStatus"] == "ok"
        and (row["role"] == "discovery" or row["freshness"] in {"current", "discovery"})
    ]
    degraded = [
        row for row in rows
        if row["monitoringStatus"] == "degraded" or row["runtimeStatus"] == "degraded"
    ]
    return {
        "rows": rows,
        "summary": {
            "configured": len(rows),
            "active": len(active),
            "healthyActive": len(healthy),
            "degraded": len(degraded),
            "planned": len(registry.get("plannedSources") or []),
            "discovery": sum(row["role"] == "discovery" for row in rows),
        },
        "plannedSources": registry.get("plannedSources") or [],
    }


def attach_source_visuals(result: dict[str, Any], presentation_path: Path) -> None:
    registry = json.loads(presentation_path.read_text(encoding="utf-8"))
    source_meta = registry.get("sources") or {}
    for item in result.get("opportunities") or []:
        meta = source_meta.get(str(item.get("source_id") or "")) or {}
        item.setdefault("presentation", {})
        item["presentation"]["source_favicon"] = meta.get("favicon")
        item["presentation"]["source_label"] = meta.get("label") or item["presentation"].get("source_label")
        item["presentation"]["source_mark"] = meta.get("mark") or item["presentation"].get("source_mark")
        item["presentation"]["source_class"] = meta.get("class") or item["presentation"].get("source_class")
    for item in result.get("archive") or []:
        meta = source_meta.get(str(item.get("source_id") or "")) or {}
        item["source_favicon"] = meta.get("favicon")
        item["source_label"] = meta.get("label") or item.get("source_label")
        item["source_mark"] = meta.get("mark") or item.get("source_mark")
        item["source_class"] = meta.get("class") or item.get("source_class")


def run(
    config_path: Path,
    today: date,
    *,
    payloads: dict[str, str] | None = None,
    detail_payloads: dict[str, str] | None = None,
    discovery_payloads: dict[str, str] | None = None,
    rules_path: Path = DEFAULT_RULES,
    presentation_path: Path = DEFAULT_PRESENTATION,
    coverage_path: Path = DEFAULT_COVERAGE,
    backtest_path: Path = DEFAULT_BACKTEST,
    previous_path: Path | None = None,
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    rules, policy, aliases = load_rules(rules_path)

    original_load_overlay = v025.load_overlay
    original_match = v021.matching_rule

    def alias_match(item: dict[str, Any], selected_rules: list[dict[str, Any]] | None = None):
        working = dict(item)
        source_id = str(working.get("source_id") or "")
        if source_id in aliases:
            working["source_id"] = aliases[source_id]
        return original_match(working, selected_rules)

    v025.load_overlay = lambda _path=rules_path: (rules, policy)
    v021.matching_rule = alias_match
    try:
        result = v025.run(
            config_path,
            today,
            payloads=payloads,
            detail_payloads=detail_payloads,
            rules_path=rules_path,
            presentation_path=presentation_path,
            coverage_path=coverage_path,
            backtest_path=backtest_path,
            previous_path=previous_path,
        )
    finally:
        v025.load_overlay = original_load_overlay
        v021.matching_rule = original_match

    attach_source_visuals(result, presentation_path)
    discovery_queue, discovery_states = probe_discovery_sources(
        config, payloads=discovery_payloads
    )
    coverage_registry = json.loads(coverage_path.read_text(encoding="utf-8"))
    result["sourceCoverage"] = build_coverage(result, coverage_registry, discovery_states)
    result["discoveryQueue"] = discovery_queue
    result["discoverySources"] = discovery_states
    result["schemaVersion"] = "3.0"
    result["engineVersion"] = "0.3"
    result["uiVersion"] = "0.3"
    result["counts"]["discoveryReview"] = len(discovery_queue)
    return result


def render_markdown(result: dict[str, Any]) -> str:
    backtest = result.get("backtest") or {}
    coverage = (result.get("sourceCoverage") or {}).get("summary") or {}
    dedupe = result.get("deduplication") or {}
    lines = [
        "# Radar Opportunità Versilia — v0.3",
        "",
        f"Data di riferimento: **{result.get('referenceDate')}**",
        "",
        (
            f"Opportunità correnti: **{len(result.get('opportunities') or [])}** · "
            f"archivio: **{len(result.get('archive') or [])}** · "
            f"continuity hold: **{len(result.get('continuityHold') or [])}**."
        ),
        (
            f"Fonti attive: **{coverage.get('active', 0)}** · "
            f"sane: **{coverage.get('healthyActive', 0)}** · "
            f"canali discovery: **{coverage.get('discovery', 0)}** · "
            f"coda discovery interna: **{len(result.get('discoveryQueue') or [])}**."
        ),
        (
            f"Deduplicazione cross-source: **{dedupe.get('recordsCollapsed', 0)}** record "
            f"collassati in **{dedupe.get('duplicateGroups', 0)}** gruppi."
        ),
        "",
        "## Backtest 90 giorni",
        "",
        (
            f"Casi: **{backtest.get('cases', 0)}** · precision **{backtest.get('precision', 0):.1%}** · "
            f"recall **{backtest.get('recall', 0):.1%}** · F1 **{backtest.get('f1', 0):.1%}** · "
            f"esito **{'PASS' if backtest.get('passed') else 'FAIL'}**."
        ),
        "",
        "## Copertura fonti",
        "",
    ]
    for row in (result.get("sourceCoverage") or {}).get("rows") or []:
        lines.append(
            f"- **{row['label']}** — ruolo `{row['role']}` · runtime `{row['runtimeStatus']}` · "
            f"freshness `{row['freshness']}`"
        )
    lines += ["", "## Discovery interna", ""]
    if result.get("discoveryQueue"):
        for item in result["discoveryQueue"][:20]:
            lines.append(f"- {item.get('source_label')}: {item.get('title')}")
    else:
        lines.append("Nessuna segnalazione interna dai nuovi canali.")
    lines += ["", "## Output corrente", ""]
    for item in result.get("opportunities") or []:
        lines.append(
            f"- {item.get('title')} — {item.get('deadline_at') or 'scadenza non rilevata'} — "
            f"{(item.get('presentation') or {}).get('source_label') or item.get('source_name')}"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--presentation", type=Path, default=DEFAULT_PRESENTATION)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--backtest", type=Path, default=DEFAULT_BACKTEST)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--backtest-only", action="store_true")
    args = parser.parse_args(argv)

    if args.backtest_only:
        rules, _, aliases = load_rules(args.rules)
        original_match = v021.matching_rule

        def alias_match(item, selected_rules=None):
            working = dict(item)
            sid = str(working.get("source_id") or "")
            if sid in aliases:
                working["source_id"] = aliases[sid]
            return original_match(working, selected_rules)

        v021.matching_rule = alias_match
        try:
            report = v025.run_backtest(args.backtest, rules)
        finally:
            v021.matching_rule = original_match
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["passed"] else 3

    result = run(
        args.config,
        args.date,
        rules_path=args.rules,
        presentation_path=args.presentation,
        coverage_path=args.coverage,
        backtest_path=args.backtest,
        previous_path=args.previous,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    report = render_markdown(result)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
    elif not args.output:
        print(report, end="")

    if any(state.get("status") == "error" for state in result.get("sources") or []):
        return 1
    if result.get("continuityHold"):
        return 2
    if not (result.get("backtest") or {}).get("passed"):
        return 3
    discovery_states = result.get("discoverySources") or []
    if discovery_states and all(state.get("status") == "error" for state in discovery_states):
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
