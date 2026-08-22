#!/usr/bin/env python3
"""Radar Opportunità Versilia v0.4 — coverage first.

La v0.4 riusa il motore/classificatore v0.3 e aggiunge un livello separato di
copertura: nuove famiglie di discovery, casi sentinella e tre stati di ciclo di
vita (aperta, a sportello, in arrivo). Il recall del backtest v0.3 resta una
metrica del classificatore sui candidati osservati e non viene presentato come
copertura dell'universo delle opportunità.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

import run_opportunity_radar_v03 as runtime_v03

radar = runtime_v03.radar
ROOT = Path(__file__).resolve().parents[1]
BASE_CONFIG = ROOT / "data" / "opportunity-sources-v03.json"
BASE_COVERAGE = ROOT / "data" / "opportunity-source-coverage-v03.json"
DISCOVERY_V04 = ROOT / "data" / "opportunity-discovery-v04.json"
CONTRACT_V04 = ROOT / "data" / "opportunity-coverage-contract-v04.json"
VERIFIED_V04 = ROOT / "data" / "opportunity-verified-v04.json"
SENTINELS_V04 = ROOT / "data" / "opportunity-coverage-sentinels-v04.json"
DEFAULT_OUTPUT = ROOT / "reports" / "runtime" / "opportunities-v04.json"
DEFAULT_REPORT = ROOT / "reports" / "runtime" / "opportunities-v04.md"

TOWNS = ("Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio")
LIFECYCLE_LABELS = {
    "application_open": "Aperta",
    "rolling_open": "A sportello",
    "announced_upcoming": "In arrivo",
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON non valido: {path}")
    return payload


def compose_runtime_payloads() -> tuple[dict[str, Any], dict[str, Any]]:
    """Compone v0.3 + nuove fonti senza duplicare i registri canonici esistenti."""
    config = _load(BASE_CONFIG)
    coverage = _load(BASE_COVERAGE)
    extra = _load(DISCOVERY_V04)

    config = json.loads(json.dumps(config))
    coverage = json.loads(json.dumps(coverage))
    existing = {str(x.get("id")) for x in config.get("discoverySources") or []}
    for source in extra.get("discoverySources") or []:
        if str(source.get("id")) not in existing:
            config.setdefault("discoverySources", []).append(source)
            existing.add(str(source.get("id")))

    registry = coverage.setdefault("sources", {})
    for source_id, meta in (extra.get("coverageRegistry") or {}).items():
        registry[str(source_id)] = meta

    # Le famiglie MASE/MIT, Interreg e UE diretta sono ora almeno in discovery.
    # Il collector GSE strutturato resta invece un debito esplicito.
    coverage["plannedSources"] = [
        item for item in coverage.get("plannedSources") or []
        if str(item.get("id")) == "gse-structured"
    ]
    coverage["schemaVersion"] = "0.4"
    config["schemaVersion"] = 4
    return config, coverage


def _recent_seed_allowed(entry: dict[str, Any], today: date, max_days: int) -> bool:
    if not entry.get("allow_recent_evidence_fallback"):
        return False
    try:
        verified = date.fromisoformat(str(entry.get("evidence_verified_at") or ""))
    except ValueError:
        return False
    return 0 <= (today - verified).days <= max_days


def verify_entry(
    entry: dict[str, Any],
    today: date,
    *,
    detail_payloads: dict[str, str] | None = None,
    live: bool = True,
    fallback_max_days: int = 7,
) -> tuple[bool, str, str | None]:
    """Verifica la fonte primaria; fallback solo su evidenza recentissima versionata."""
    url = str(entry.get("url") or "")
    raw: str | None = None
    error: str | None = None
    if detail_payloads and url in detail_payloads:
        raw = detail_payloads[url]
    elif live:
        try:
            raw = radar.v025.v022.fetch_resilient(url, timeout=30, attempts=2)
        except Exception as exc:  # pragma: no cover - dipende dalla rete live
            error = str(exc)

    if raw is not None:
        text = radar.base.visible(raw)
        folded = radar.v025.fold(text)
        missing = [term for term in entry.get("required_terms") or [] if radar.v025.fold(term) not in folded]
        if not missing:
            return True, "live", None
        error = "termini obbligatori non trovati: " + ", ".join(missing)

    if _recent_seed_allowed(entry, today, fallback_max_days):
        return True, "cached_recent", error
    return False, "failed", error or "fonte primaria non verificabile"


def _source_visual(source_id: str) -> dict[str, Any]:
    extra = _load(DISCOVERY_V04).get("coverageRegistry") or {}
    meta = extra.get(source_id) or {}
    return {
        "source_label": meta.get("label") or source_id,
        "source_favicon": meta.get("favicon") or "",
    }


def build_seed_item(entry: dict[str, Any], today: date, verification_status: str) -> dict[str, Any]:
    stage = str(entry.get("lifecycle_stage") or "application_open")
    matrix = {
        town: dict((entry.get("municipality_status_overrides") or {}).get(town) or {
            "status": "not_eligible",
            "reason": "Nessuna ammissibilità documentata per questo Comune.",
        })
        for town in TOWNS
    }
    statuses = {str(x.get("status")) for x in matrix.values()}
    aggregate = "eligible" if "eligible" in statuses else "conditional" if "conditional" in statuses else "not_eligible"
    presentation = dict(entry.get("presentation") or {})
    visual = _source_visual(str(entry.get("source_id") or ""))
    presentation.setdefault("source_label", entry.get("source_label") or visual["source_label"])
    presentation.setdefault("source_favicon", visual["source_favicon"])
    presentation.setdefault("source_mark", str(entry.get("source_label") or entry.get("source_id") or "F")[:4].upper())
    presentation.setdefault("source_class", "other")
    presentation.setdefault("category", entry.get("category") or "generale")
    presentation.setdefault("description", entry.get("description") or entry.get("project_requirements") or "")
    presentation.setdefault("condition_label", entry.get("condition_label") or "")

    source_id = str(entry.get("source_id") or "")
    title = str(entry.get("title") or "")
    url = str(entry.get("url") or "")
    item = {
        "id": radar.base.sid(source_id, title, url),
        "coverage_id": entry.get("coverage_id"),
        "rule_id": "coverage:" + str(entry.get("coverage_id") or radar.base.sid(source_id, title, url)),
        "source_id": source_id,
        "source_name": entry.get("source_label") or entry.get("publisher") or source_id,
        "publisher": entry.get("publisher") or entry.get("source_label") or source_id,
        "title": title,
        "url": url,
        "summary": entry.get("description") or entry.get("project_requirements") or "",
        "status": "upcoming" if stage == "announced_upcoming" else "open",
        "lifecycle_stage": stage,
        "lifecycle_label": LIFECYCLE_LABELS.get(stage, stage),
        "opens_at": entry.get("opens_at"),
        "deadline_at": entry.get("deadline_at"),
        "deadline_time": entry.get("deadline_time"),
        "published_at": entry.get("published_at"),
        "municipalities": list(TOWNS),
        "eligibility": aggregate,
        "eligibility_reason": entry.get("project_requirements") or "Ammissibilità documentata dalla fonte ufficiale.",
        "municipality_eligibility": matrix,
        "applicant_eligibility": aggregate,
        "applicant_type": entry.get("applicant_type"),
        "municipality_role": entry.get("municipality_role"),
        "final_beneficiaries": entry.get("final_beneficiaries"),
        "partnership_required": str(entry.get("municipality_role")) == "partner",
        "project_requirements": entry.get("project_requirements"),
        "geographic_scope": entry.get("geographic_scope"),
        "geographic_eligibility": "eligible" if aggregate in {"eligible", "conditional"} else "not_eligible",
        "territorial_relevance": "direct",
        "actionable_for_municipality": bool(entry.get("actionable", stage != "announced_upcoming")),
        "decision_class": "coverage_verified_" + stage,
        "access_mode": "specific_requirement" if aggregate == "conditional" else "direct",
        "themes": [entry.get("category")] if entry.get("category") else [],
        "eligibility_evidence": {
            "rule_id": "coverage:" + str(entry.get("coverage_id") or ""),
            "text": entry.get("project_requirements"),
            "source_url": url,
        },
        "presentation": presentation,
        "verified_direct": True,
        "verified_at": today.isoformat(),
        "verification_status": verification_status,
    }
    return item


def _is_expired_application(entry: dict[str, Any], today: date) -> bool:
    if str(entry.get("lifecycle_stage")) != "application_open":
        return False
    deadline = entry.get("deadline_at")
    if not deadline:
        return False
    try:
        return date.fromisoformat(str(deadline)) < today
    except ValueError:
        return False


def _append_archive(result: dict[str, Any], item: dict[str, Any]) -> None:
    existing = {str(x.get("coverage_id") or x.get("id")) for x in result.get("archive") or []}
    key = str(item.get("coverage_id") or item.get("id"))
    if key in existing:
        return
    result.setdefault("archive", []).append({
        "id": item.get("id"),
        "coverage_id": item.get("coverage_id"),
        "title": item.get("title"),
        "url": item.get("url"),
        "source_id": item.get("source_id"),
        "source_label": (item.get("presentation") or {}).get("source_label"),
        "source_mark": (item.get("presentation") or {}).get("source_mark"),
        "source_class": (item.get("presentation") or {}).get("source_class"),
        "source_favicon": (item.get("presentation") or {}).get("source_favicon"),
        "deadline_at": item.get("deadline_at"),
        "deadline_time": item.get("deadline_time"),
    })


def inject_verified_v04(
    result: dict[str, Any],
    today: date,
    *,
    detail_payloads: dict[str, str] | None = None,
    live: bool = True,
) -> set[str]:
    payload = _load(VERIFIED_V04)
    max_days = int(payload.get("evidenceFallbackMaxDays") or 7)
    resolved: set[str] = set()
    existing_coverage = {str(x.get("coverage_id")) for x in result.get("opportunities") or [] if x.get("coverage_id")}
    existing_urls = {radar.v025.normalized_url(str(x.get("url") or "")) for x in result.get("opportunities") or []}

    for entry in payload.get("entries") or []:
        coverage_id = str(entry.get("coverage_id") or "")
        ok, verification_status, error = verify_entry(
            entry, today, detail_payloads=detail_payloads, live=live, fallback_max_days=max_days
        )
        if not ok:
            result.setdefault("coverageHold", []).append({
                "coverage_id": coverage_id,
                "title": entry.get("title"),
                "source_id": entry.get("source_id"),
                "url": entry.get("url"),
                "reason": error,
            })
            continue

        item = build_seed_item(entry, today, verification_status)
        resolved.add(coverage_id)
        if _is_expired_application(entry, today):
            _append_archive(result, item)
            continue
        norm_url = radar.v025.normalized_url(str(item.get("url") or ""))
        if coverage_id in existing_coverage or (norm_url and norm_url in existing_urls):
            continue
        result.setdefault("opportunities", []).append(item)
        existing_coverage.add(coverage_id)
        if norm_url:
            existing_urls.add(norm_url)

    order = {"application_open": 0, "rolling_open": 1, "announced_upcoming": 2}
    result.setdefault("opportunities", []).sort(
        key=lambda x: (
            order.get(str(x.get("lifecycle_stage") or "application_open"), 9),
            str(x.get("deadline_at") or "9999-99-99"),
            str(x.get("title") or ""),
        )
    )
    return resolved


def _active_current_sentinel(case: dict[str, Any], today: date, verified_by_id: dict[str, dict[str, Any]]) -> bool:
    if case.get("expected") != "current":
        return False
    entry = verified_by_id.get(str(case.get("coverage_id") or "")) or {}
    return not _is_expired_application(entry, today)


def build_coverage_audit(result: dict[str, Any], resolved: set[str], today: date) -> dict[str, Any]:
    contract = _load(CONTRACT_V04)
    sentinels = _load(SENTINELS_V04)
    verified = _load(VERIFIED_V04)
    verified_by_id = {str(x.get("coverage_id")): x for x in verified.get("entries") or []}
    rows = list((result.get("sourceCoverage") or {}).get("rows") or [])
    configured = {str(row.get("source_id") or "") for row in rows}

    missing_families: list[str] = []
    runtime_unhealthy: list[str] = []
    for family in contract.get("requiredFamilies") or []:
        source_ids = {str(x) for x in family.get("sourceIds") or []}
        available = source_ids & configured
        if not available:
            missing_families.append(str(family.get("id")))
            continue
        healthy = [
            row for row in rows
            if str(row.get("source_id")) in available and str(row.get("runtimeStatus")) == "ok"
        ]
        if not healthy:
            runtime_unhealthy.append(str(family.get("id")))

    missing_current: list[str] = []
    historical_unmonitored: list[str] = []
    for case in sentinels.get("cases") or []:
        expected = str(case.get("expected") or "")
        if _active_current_sentinel(case, today, verified_by_id):
            if str(case.get("coverage_id") or "") not in resolved:
                missing_current.append(str(case.get("id") or case.get("coverage_id")))
        elif expected == "historical_monitored" and str(case.get("source_id") or "") not in configured:
            historical_unmonitored.append(str(case.get("id") or case.get("source_id")))

    excluded = set(contract.get("excludedOpportunityKinds") or [])
    exclusion_ok = "procurement_where_municipality_is_contracting_authority" in excluded
    backtest = result.get("backtest") or {}
    status = "pass" if not missing_families and not missing_current and not historical_unmonitored and exclusion_ok else "fail"
    return {
        "status": status,
        "claim": "coverage_first_not_exhaustive_web_claim",
        "classifierMetricScope": "known-candidate classification only; not total web coverage",
        "classifierRecall": backtest.get("recall"),
        "requiredFamilies": len(contract.get("requiredFamilies") or []),
        "configuredSources": len(configured),
        "missingFamilies": missing_families,
        "runtimeUnhealthyFamilies": runtime_unhealthy,
        "currentSentinelsResolved": len([
            case for case in sentinels.get("cases") or []
            if _active_current_sentinel(case, today, verified_by_id)
            and str(case.get("coverage_id") or "") in resolved
        ]),
        "missingCurrentSentinels": missing_current,
        "historicalUnmonitored": historical_unmonitored,
        "procurementExclusionContract": exclusion_ok,
    }


def _recompute_v04_counts(result: dict[str, Any]) -> None:
    opportunities = list(result.get("opportunities") or [])
    stage_counts = {key: 0 for key in LIFECYCLE_LABELS}
    for item in opportunities:
        stage = str(item.get("lifecycle_stage") or "application_open")
        if stage in stage_counts:
            stage_counts[stage] += 1
    result["lifecycleSummary"] = stage_counts
    counts = result.setdefault("counts", {})
    counts["public"] = len(opportunities)
    counts["applicationOpen"] = stage_counts["application_open"]
    counts["rollingOpen"] = stage_counts["rolling_open"]
    counts["announcedUpcoming"] = stage_counts["announced_upcoming"]
    counts["coverageHold"] = len(result.get("coverageHold") or [])

    by_source: dict[str, int] = {}
    for item in opportunities:
        sid = str(item.get("source_id") or "")
        by_source[sid] = by_source.get(sid, 0) + 1
    for row in (result.get("sourceCoverage") or {}).get("rows") or []:
        sid = str(row.get("source_id") or "")
        row["publicCount"] = by_source.get(sid, int(row.get("publicCount") or 0))
        row["verifiedOutputCount"] = by_source.get(sid, 0)


def run_v04(
    today: date,
    *,
    previous_path: Path | None = None,
    payloads: dict[str, str] | None = None,
    detail_payloads: dict[str, str] | None = None,
    discovery_payloads: dict[str, str] | None = None,
) -> dict[str, Any]:
    config, coverage = compose_runtime_payloads()
    with tempfile.TemporaryDirectory(prefix="opportunity-v04-") as tmp:
        tmpdir = Path(tmp)
        config_path = tmpdir / "sources-v04.json"
        coverage_path = tmpdir / "coverage-v04.json"
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        coverage_path.write_text(json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8")
        result = radar.run(
            config_path,
            today,
            payloads=payloads,
            detail_payloads=detail_payloads,
            discovery_payloads=discovery_payloads,
            coverage_path=coverage_path,
            previous_path=previous_path,
        )

    result.setdefault("coverageHold", [])
    resolved = inject_verified_v04(result, today, detail_payloads=detail_payloads, live=payloads is None)
    result["coverageAudit"] = build_coverage_audit(result, resolved, today)
    _recompute_v04_counts(result)
    result["schemaVersion"] = "4.0"
    result["engineVersion"] = "0.4"
    result["uiVersion"] = "0.4"
    result["coverageVersion"] = "0.4"
    return result


def render_markdown(result: dict[str, Any]) -> str:
    counts = result.get("counts") or {}
    audit = result.get("coverageAudit") or {}
    backtest = result.get("backtest") or {}
    coverage = (result.get("sourceCoverage") or {}).get("summary") or {}
    lines = [
        "# Radar Opportunità Versilia — v0.4 coverage-first",
        "",
        f"Data di riferimento: **{result.get('referenceDate')}**",
        "",
        f"Opportunità correnti: **{counts.get('public', 0)}** · aperte: **{counts.get('applicationOpen', 0)}** · a sportello: **{counts.get('rollingOpen', 0)}** · in arrivo: **{counts.get('announcedUpcoming', 0)}**.",
        f"Fonti configurate: **{coverage.get('configured', 0)}** · attive: **{coverage.get('active', 0)}** · discovery: **{coverage.get('discovery', 0)}**.",
        "",
        "## Audit copertura",
        "",
        f"Esito: **{str(audit.get('status', 'unknown')).upper()}** · famiglie richieste: **{audit.get('requiredFamilies', 0)}** · sentinelle correnti risolte: **{audit.get('currentSentinelsResolved', 0)}**.",
        f"Famiglie mancanti: **{', '.join(audit.get('missingFamilies') or []) or 'nessuna'}**.",
        f"Famiglie senza endpoint sano nel run: **{', '.join(audit.get('runtimeUnhealthyFamilies') or []) or 'nessuna'}**.",
        f"Sentinelle correnti mancanti: **{', '.join(audit.get('missingCurrentSentinels') or []) or 'nessuna'}**.",
        "",
        "## Classificatore",
        "",
        f"Backtest casi osservati: precision **{backtest.get('precision', 0):.1%}** · recall **{backtest.get('recall', 0):.1%}** · F1 **{backtest.get('f1', 0):.1%}**.",
        "Il recall sopra misura la classificazione dei candidati noti e non la completezza dell'intero web.",
        "",
        "## Coverage hold",
        "",
    ]
    holds = result.get("coverageHold") or []
    if holds:
        for hold in holds:
            lines.append(f"- **{hold.get('title')}** — {hold.get('reason')}")
    else:
        lines.append("Nessuno.")
    return "\n".join(lines) + "\n"


def _classifier_backtest() -> dict[str, Any]:
    rules, _, aliases = radar.load_rules()
    original = radar.v021.matching_rule

    def alias_match(item: dict[str, Any], selected_rules=None):
        working = dict(item)
        sid = str(working.get("source_id") or "")
        if sid in aliases:
            working["source_id"] = aliases[sid]
        return original(working, selected_rules)

    radar.v021.matching_rule = alias_match
    try:
        return radar.v025.run_backtest(radar.DEFAULT_BACKTEST, rules)
    finally:
        radar.v021.matching_rule = original


def _exit_code(result: dict[str, Any]) -> int:
    if result.get("continuityHold"):
        return 2
    if not (result.get("backtest") or {}).get("passed"):
        return 3
    if (result.get("coverageAudit") or {}).get("status") != "pass":
        return 5
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--backtest-only", action="store_true")
    args = parser.parse_args()

    if args.backtest_only:
        report = _classifier_backtest()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("passed") else 3

    today = date.fromisoformat(args.date)
    result = run_v04(today, previous_path=args.previous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    args.report.write_text(render_markdown(result), encoding="utf-8")
    print(render_markdown(result))
    return _exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
