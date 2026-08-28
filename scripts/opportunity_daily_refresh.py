#!/usr/bin/env python3
"""Esegue il refresh giornaliero del Radar e prepara lo snapshot pubblicabile.

La scansione è live, ma non salta i gate: continuità, backtest, copertura,
verifiche dirette e completezza regionale devono essere verdi. Le fonti di puro
discovery non possono pubblicare da sole; eventuali candidati restano nella
coda interna del report.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from opportunity_continuity import reconcile_final_continuity as _reconcile_final_continuity
import opportunity_regione_toscana_guard as regione_guard
import run_opportunity_radar_v044 as radar

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "data" / "opportunity-release.json"
DEFAULT_DAILY = ROOT / "data" / "opportunity-daily-public.json"
DEFAULT_REPORT = ROOT / "reports" / "runtime" / "opportunity-daily-summary.md"
DEFAULT_CONTINUITY_DIAGNOSTIC = ROOT / "reports" / "runtime" / "opportunity-continuity-hold.json"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON non valido: {path}")
    return payload


def _identity(item: dict[str, Any]) -> str:
    coverage_id = str(item.get("coverage_id") or "").strip()
    if coverage_id:
        return "coverage:" + coverage_id
    url = radar.radar.v025.normalized_url(str(item.get("url") or ""))
    if url:
        return "url:" + url
    return "id:" + str(item.get("id") or "")


def _previous_snapshot(daily: Path, baseline: Path) -> tuple[Path, dict[str, Any]]:
    if daily.exists():
        return daily, _load(daily)
    if not baseline.exists():
        raise RuntimeError(
            "Baseline Radar assente: eseguire prima scripts/materialize_opportunity_release_snapshot.py"
        )
    return baseline, _load(baseline)


def _write_continuity_diagnostic(
    result: dict[str, Any],
    path: Path = DEFAULT_CONTINUITY_DIAGNOSTIC,
) -> Path | None:
    holds = list(result.get("continuityHold") or [])
    if not holds:
        return None

    fields = (
        "identity_key",
        "coverage_id",
        "rule_id",
        "title",
        "source_id",
        "deadline_at",
        "url",
        "reason",
    )
    diagnostic_holds = [
        {field: hold.get(field) for field in fields if hold.get(field) not in {None, ""}}
        for hold in holds
    ]
    payload = {
        "referenceDate": result.get("referenceDate"),
        "count": len(diagnostic_holds),
        "holds": diagnostic_holds,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"CONTINUITY HOLD: {len(diagnostic_holds)} opportunità irrisolte")
    for index, hold in enumerate(diagnostic_holds, start=1):
        print(f"CONTINUITY HOLD #{index}")
        print(f"  Titolo: {hold.get('title') or 'n.d.'}")
        print(f"  Fonte: {hold.get('source_id') or 'n.d.'}")
        print(f"  Scadenza: {hold.get('deadline_at') or 'n.d.'}")
        print(f"  Identità: {hold.get('identity_key') or hold.get('coverage_id') or hold.get('rule_id') or 'n.d.'}")
        print(f"  URL: {hold.get('url') or 'n.d.'}")
        print(f"  Motivo: {hold.get('reason') or 'n.d.'}")
    print(f"Diagnostica continuità salvata in: {path}")
    return path


def _assert_publishable(result: dict[str, Any]) -> None:
    problems: list[str] = []
    if result.get("continuityHold"):
        _write_continuity_diagnostic(result)
        problems.append(f"continuityHold={len(result.get('continuityHold') or [])}")
    if result.get("coverageHold"):
        problems.append(f"coverageHold={len(result.get('coverageHold') or [])}")
    backtest = result.get("backtest") or {}
    if not backtest.get("passed", False):
        problems.append("backtest=fail")
    audit = result.get("coverageAudit") or {}
    if audit.get("status") != "pass":
        problems.append("coverageAudit=fail")
    regional = result.get("regionalCompleteness") or {}
    if regional.get("status") == "fail":
        problems.append("regionalCompleteness=fail")
    if not result.get("opportunities"):
        problems.append("opportunities=0")
    if problems:
        raise RuntimeError("Snapshot giornaliero non pubblicabile: " + ", ".join(problems))


def _annotate_first_seen(
    result: dict[str, Any],
    previous: dict[str, Any],
    today: date,
) -> list[dict[str, Any]]:
    previous_by_key = {
        _identity(item): item
        for item in previous.get("opportunities") or []
        if _identity(item) not in {"id:", "url:", "coverage:"}
    }
    new_items: list[dict[str, Any]] = []

    for item in result.get("opportunities") or []:
        key = _identity(item)
        old = previous_by_key.get(key)
        if old is not None:
            old_first = str(old.get("first_seen_at") or "").strip()
            if old_first:
                item["first_seen_at"] = old_first
                _, item["is_new"] = radar._new_state(old_first, today)
            else:
                # Le opportunità della baseline precedente all'introduzione del
                # first-seen non devono diventare artificialmente "nuove".
                item.pop("first_seen_at", None)
                item["is_new"] = False
            continue

        first = str(item.get("first_seen_at") or today.isoformat())
        item["first_seen_at"], item["is_new"] = radar._new_state(first, today)
        item["is_new"] = True
        new_items.append(item)

    result["newOpportunityWindowDays"] = radar.NEW_WINDOW_DAYS
    result.setdefault("counts", {})["new"] = sum(
        bool(item.get("is_new")) for item in result.get("opportunities") or []
    )
    return new_items


def _prepare_public(result: dict[str, Any], today: date) -> dict[str, Any]:
    result["referenceDate"] = today.isoformat()
    result["releaseVersion"] = "0.4.4"
    result["engineVersion"] = "0.4.4"
    result["coverageVersion"] = "0.4.4"
    result["uiVersion"] = "0.4.4"
    result["dailyHardeningVersion"] = "0.4.4-h2"
    return result


def _render_report(result: dict[str, Any], new_items: list[dict[str, Any]]) -> str:
    counts = result.get("counts") or {}
    queue = result.get("discoveryQueue") or []
    regional = result.get("regionalCompleteness") or {}
    continuity = result.get("continuityReconciliation") or {}
    new_titles = [str(item.get("title") or "") for item in new_items]
    lines = [
        "# Radar Opportunità · refresh giornaliero",
        "",
        f"Data: **{result.get('referenceDate')}**",
        "",
        f"Opportunità correnti: **{counts.get('public', len(result.get('opportunities') or []))}** · evidenziate come nuove: **{counts.get('new', 0)}**.",
        f"Nuove identità rilevate in questo run: **{len(new_items)}** · candidati discovery non pubblicati automaticamente: **{len(queue)}**.",
        (
            "Riconciliazione continuità: "
            f"**{continuity.get('reconciled', 0)}** hold risolti a fine pipeline · "
            f"**{continuity.get('remaining', len(result.get('continuityHold') or []))}** ancora irrisolti."
        ),
        (
            "Safety net Regione Toscana: "
            f"**{str(regional.get('status', 'unknown')).upper()}** · "
            f"{regional.get('municipalCandidates', 0)} candidati comunali recenti controllati · "
            f"{regional.get('safetyNetAdded', 0)} aggiunti alla discovery · "
            f"{len(regional.get('overdue') or [])} oltre la finestra di revisione."
        ),
        "",
        "## Nuove opportunità pubblicabili",
        "",
    ]
    if new_titles:
        lines.extend(f"- {title}" for title in new_titles)
    else:
        lines.append("Nessuna nuova identità pubblicabile oggi.")

    unresolved = regional.get("unresolved") or []
    lines.extend(["", "## Regione Toscana · candidati da qualificare", ""])
    if unresolved:
        for item in unresolved:
            lines.append(
                f"- {item.get('title')} — pubblicato {item.get('published_at') or 'data non rilevata'} · "
                f"stato `{item.get('account_state') or 'unknown'}`"
            )
    else:
        lines.append("Nessun candidato regionale con ruolo comunale esplicito resta da qualificare.")

    lines.extend([
        "",
        "## Gate",
        "",
        f"- continuità: **{'PASS' if not result.get('continuityHold') else 'FAIL'}**",
        f"- backtest: **{'PASS' if (result.get('backtest') or {}).get('passed') else 'FAIL'}**",
        f"- copertura: **{str((result.get('coverageAudit') or {}).get('status', 'unknown')).upper()}**",
        f"- completezza Regione Toscana: **{str(regional.get('status', 'unknown')).upper()}**",
        f"- verifiche dirette in hold: **{len(result.get('coverageHold') or [])}**",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--daily", type=Path, default=DEFAULT_DAILY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    today = date.fromisoformat(args.date)
    previous_path, previous = _previous_snapshot(args.daily, args.baseline)
    result = radar.run_v04(today, previous_path=previous_path)
    result = _reconcile_final_continuity(result)
    result = regione_guard.apply(result, today)
    _assert_publishable(result)
    new_items = _annotate_first_seen(result, previous, today)
    result = _prepare_public(result, today)

    if result.get("referenceDate") != today.isoformat():
        raise RuntimeError("Snapshot giornaliero con referenceDate non coerente con il run corrente.")

    args.daily.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.daily.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(_render_report(result, new_items), encoding="utf-8")

    print(
        f"Radar giornaliero OK: {len(result.get('opportunities') or [])} correnti · "
        f"{len(new_items)} nuove identità · {(result.get('counts') or {}).get('new', 0)} con badge Nuova · "
        f"continuità riconciliata {(result.get('continuityReconciliation') or {}).get('reconciled', 0)} · "
        f"Regione Toscana {str((result.get('regionalCompleteness') or {}).get('status', 'unknown')).upper()}."
    )
    for item in new_items:
        print("NEW:", item.get("title"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
