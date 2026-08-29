#!/usr/bin/env python3
"""Estende il controllo mensile esistente con uno stato operativo per indicatore.

Non modifica valori pubblicati. Il wrapper usa il monitor esistente e può aggiungere
verifiche machine-readable ufficiali quando la pagina primaria non è interrogabile.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import monthly_data_check_coverage as coverage  # noqa: E402
import monitor_semantic_checks as semantics  # noqa: E402
import pnrr_toscana_audit  # noqa: E402
import update_fuel_prices_mimit as fuel_mimit  # noqa: E402
from data_status_model import canonical_url, published_period  # noqa: E402

PNRR_METRICS = ("pnrrFunding", "pnrrConcluded")
FUEL_METRIC = "fuelPrices"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON non valido: {path}")
    return value


def changed_urls(report: dict[str, Any]) -> set[str]:
    """Restituisce solo cambiamenti di una fonte già monitorata."""
    changes = report.get("changes") if isinstance(report.get("changes"), dict) else {}
    urls: set[str] = set()
    for key in ("content", "redirect"):
        items = changes.get(key) if isinstance(changes.get(key), list) else []
        for item in items:
            if isinstance(item, dict) and item.get("url"):
                urls.add(canonical_url(str(item["url"])))
    return urls


def build_metric_state(
    data: dict[str, Any],
    previous: dict[str, Any],
    next_state: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    previous_metrics = previous.get("metrics") if isinstance(previous.get("metrics"), dict) else {}
    probes = next_state.get("sources") if isinstance(next_state.get("sources"), dict) else {}
    changed = changed_urls(report)
    checked_at = str(next_state.get("checkedAt") or "")
    result: dict[str, dict[str, Any]] = {}

    for key, metric in data.get("metrics", {}).items():
        if not isinstance(metric, dict):
            continue
        old = previous_metrics.get(key)
        old = old if isinstance(old, dict) else {}
        source_url = str(metric.get("sourceUrl") or "")
        source_key = canonical_url(source_url)
        probe = probes.get(source_url)
        if not isinstance(probe, dict):
            probe = next(
                (
                    item
                    for url, item in probes.items()
                    if isinstance(item, dict) and canonical_url(str(url)) == source_key
                ),
                None,
            )

        item: dict[str, Any] = {
            "publishedPeriod": published_period(metric),
            "checkedAt": checked_at if probe is not None else str(old.get("checkedAt") or ""),
            "observedLatestPeriod": str(old.get("observedLatestPeriod") or ""),
            "status": str(old.get("status") or ""),
        }
        if isinstance(old.get("nextExpectedRelease"), dict):
            item["nextExpectedRelease"] = old["nextExpectedRelease"]
        if old.get("releaseEvidence"):
            item["releaseEvidence"] = old["releaseEvidence"]
        if old.get("verificationEvidence"):
            item["verificationEvidence"] = old["verificationEvidence"]

        if probe is None:
            item["status"] = "verification_required"
        elif probe.get("automationLimited"):
            item["status"] = "source_access_limited"
        elif not probe.get("ok"):
            item["status"] = "source_unavailable"
        elif source_key in changed:
            if item["observedLatestPeriod"] and item["observedLatestPeriod"] != item["publishedPeriod"]:
                item["status"] = "release_detected"
            else:
                item["status"] = "verification_required"
        elif item["observedLatestPeriod"]:
            item["status"] = (
                "current"
                if item["observedLatestPeriod"] == item["publishedPeriod"]
                else "release_detected"
            )
        else:
            item["status"] = "source_checked"
        result[key] = item
    return result


def apply_fuel_verification_result(
    metric: dict[str, Any],
    item: dict[str, Any],
    live: dict[str, Any],
    checked_at: str,
) -> dict[str, Any]:
    published = str(item.get("publishedPeriod") or "")
    observed = str(live.get("referenceDate") or "")
    values_match = semantics.fuel_metric_matches(metric, live)
    evidence = {
        "provider": "Ministero delle Imprese e del Made in Italy",
        "url": str(live.get("sourceUrls", {}).get("prezzi") or fuel_mimit.audit.PRICES),
        "referenceDate": observed,
        "coverage": str(live.get("coverage") or ""),
        "valuesMatchPublished": values_match,
        "towns": live.get("towns", {}),
    }
    item["checkedAt"] = checked_at or str(item.get("checkedAt") or "")
    item["observedLatestPeriod"] = observed
    item["verificationEvidence"] = evidence
    if observed and published and observed > published:
        item["status"] = "release_detected"
        evidence["verdict"] = "new_period"
        item["releaseEvidence"] = evidence
    elif observed == published and values_match:
        item["status"] = "current"
        evidence["verdict"] = "match"
        item.pop("releaseEvidence", None)
    elif observed == published:
        item["status"] = "verification_required"
        evidence["verdict"] = "same_period_values_differ"
        item["releaseEvidence"] = evidence
    else:
        item["status"] = "verification_required"
        evidence["verdict"] = "period_not_comparable"
        item["releaseEvidence"] = evidence
    return evidence


def run_fuel_verification(
    data: dict[str, Any],
    metrics: dict[str, dict[str, Any]],
    report: dict[str, Any],
    checked_at: str,
) -> tuple[dict[str, Any] | None, str]:
    metric = data.get("metrics", {}).get(FUEL_METRIC)
    item = metrics.get(FUEL_METRIC)
    if not isinstance(metric, dict) or not isinstance(item, dict):
        return None, ""
    source_key = canonical_url(str(metric.get("sourceUrl") or ""))
    needs_semantic_check = source_key in changed_urls(report) or str(item.get("status") or "") in {
        "verification_required",
        "release_detected",
    }
    if not needs_semantic_check:
        return None, ""
    try:
        live = fuel_mimit.collect()
    except Exception as exc:
        item["status"] = "verification_required"
        return None, f"{type(exc).__name__}: {exc}"
    return apply_fuel_verification_result(metric, item, live, checked_at), ""


def append_fuel_report_section(
    report_md: Path,
    result: dict[str, Any] | None,
    error: str = "",
) -> None:
    if result is None and not error:
        return
    lines = ["", "### Verifica carburanti MIMIT", ""]
    if result is not None:
        lines.extend(
            [
                f"- Fotografia: `{result.get('referenceDate') or 'n.d.'}`",
                f"- Copertura: `{result.get('coverage') or 'n.d.'}`",
                f"- Esito semantico: `{result.get('verdict') or 'n.d.'}`",
                f"- Valori pubblicati coincidenti: `{'sì' if result.get('valuesMatchPublished') else 'no'}`",
                "- Il cambio quotidiano del CSV non viene più interpretato da solo come anomalia: il periodo e i valori vengono verificati semanticamente.",
            ]
        )
    else:
        lines.append(f"Controllo semantico non completato: `{error}`. Nessun valore viene modificato automaticamente.")
    with report_md.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def verification_evidence(audit_result: dict[str, Any], metric_key: str) -> dict[str, Any]:
    metric_verdicts = audit_result.get("metricVerdicts")
    metric_verdicts = metric_verdicts if isinstance(metric_verdicts, dict) else {}
    dates = list(audit_result.get("dataElaborationDates") or [])
    return {
        "provider": "Regione Toscana — Open Data PNRR",
        "url": str(audit_result.get("resource") or pnrr_toscana_audit.MAIN_CSV_URL),
        "datasetUrl": str(audit_result.get("dataset") or pnrr_toscana_audit.DATASET_URL),
        "dataElaborationDates": dates,
        "dataElaborationDate": dates[-1] if dates else "",
        "match7of7": str(metric_verdicts.get(metric_key) or audit_result.get("verdict") or "") == "match",
        "metric": metric_key,
        "verdict": str(metric_verdicts.get(metric_key) or audit_result.get("verdict") or ""),
        "recordsScanned": int(audit_result.get("recordsScanned") or 0),
        "selectedProjects": int(audit_result.get("selectedProjects") or 0),
    }


def apply_pnrr_verification_result(
    metrics: dict[str, dict[str, Any]],
    audit_result: dict[str, Any],
    checked_at: str,
) -> None:
    """Applica separatamente l'esito dei due indicatori PNRR.

    - match 7/7: il periodo pubblicato è certificato dalla fonte machine-readable;
    - fotografia diversa: solo l'indicatore coinvolto diventa release_detected;
    - perimetro non confrontabile: resta necessaria la verifica manuale.
    """
    metric_verdicts = audit_result.get("metricVerdicts")
    metric_verdicts = metric_verdicts if isinstance(metric_verdicts, dict) else {}

    for key in PNRR_METRICS:
        item = metrics.get(key)
        if not isinstance(item, dict):
            continue
        evidence = verification_evidence(audit_result, key)
        verdict = str(metric_verdicts.get(key) or audit_result.get("verdict") or "")
        item["checkedAt"] = checked_at or str(item.get("checkedAt") or "")
        item["verificationEvidence"] = evidence
        if verdict == "match":
            item["observedLatestPeriod"] = str(item.get("publishedPeriod") or "")
            item["status"] = "current"
            item.pop("releaseEvidence", None)
        elif verdict == "different_current_snapshot":
            item["status"] = "release_detected"
            item["releaseEvidence"] = evidence
        else:
            item["status"] = "verification_required"


def run_pnrr_verification(
    data: dict[str, Any],
    metrics: dict[str, dict[str, Any]],
    checked_at: str,
) -> tuple[dict[str, Any] | None, str]:
    try:
        result = pnrr_toscana_audit.audit(data)
    except Exception as exc:  # la fonte primaria resta comunque governata dal monitor esistente
        return None, f"{type(exc).__name__}: {exc}"
    apply_pnrr_verification_result(metrics, result, checked_at)
    return result, ""


def append_report_section(
    report_md: Path,
    state: dict[str, Any],
    pnrr_result: dict[str, Any] | None = None,
    pnrr_error: str = "",
) -> None:
    metrics = state.get("metrics") if isinstance(state.get("metrics"), dict) else {}
    counts: dict[str, int] = {}
    for item in metrics.values():
        if isinstance(item, dict):
            status = str(item.get("status") or "verification_required")
            counts[status] = counts.get(status, 0) + 1
    lines = [
        "",
        "### Stato operativo degli indicatori",
        "",
        "Il controllo distingue la raggiungibilità della fonte dalla verifica dell'ultimo periodo disponibile.",
        "Una fonte raggiungibile non viene automaticamente dichiarata come dato aggiornato.",
        "",
        "| Stato | Indicatori |",
        "|---|---:|",
    ]
    labels = {
        "current": "Ultimo dato disponibile verificato",
        "source_checked": "Fonte controllata; periodo non confermabile automaticamente",
        "source_access_limited": "Controllo automatico limitato dal portale",
        "release_detected": "Nuovo rilascio da verificare",
        "update_expected": "Aggiornamento atteso",
        "source_unavailable": "Fonte temporaneamente non verificabile",
        "verification_required": "Verifica necessaria",
    }
    for key in labels:
        lines.append(f"| {labels[key]} | {counts.get(key, 0)} |")

    detail_states = {
        "source_access_limited",
        "release_detected",
        "update_expected",
        "source_unavailable",
        "verification_required",
    }
    details = [
        (metric_key, item)
        for metric_key, item in sorted(metrics.items())
        if isinstance(item, dict) and str(item.get("status") or "verification_required") in detail_states
    ]
    if details:
        lines.extend(
            [
                "",
                "#### Dettaglio indicatori da verificare",
                "",
                "| Indicatore | Stato | Periodo pubblicato | Ultimo periodo osservato |",
                "|---|---|---|---|",
            ]
        )
        for metric_key, item in details:
            status = str(item.get("status") or "verification_required")
            published = str(item.get("publishedPeriod") or "n.d.")
            observed = str(item.get("observedLatestPeriod") or "n.d.")
            lines.append(f"| `{metric_key}` | {labels.get(status, status)} | {published} | {observed} |")

    if pnrr_result is not None:
        metric_verdicts = pnrr_result.get("metricVerdicts")
        metric_verdicts = metric_verdicts if isinstance(metric_verdicts, dict) else {}
        lines.extend(
            [
                "",
                "### Verifica PNRR Regione Toscana",
                "",
                f"- Fotografia: `{', '.join(pnrr_result.get('dataElaborationDates') or []) or 'n.d.'}`",
                f"- Progetti dei sette Comuni come soggetti attuatori: {pnrr_result.get('selectedProjects', 0)}",
                f"- Risorse PNRR per residente: `{metric_verdicts.get('pnrrFunding', '')}`",
                f"- Progetti PNRR conclusi: `{metric_verdicts.get('pnrrConcluded', '')}`",
                "- Una differenza genera solo `release_detected` sull'indicatore coinvolto: nessun valore viene pubblicato automaticamente.",
            ]
        )
    elif pnrr_error:
        lines.extend(
            [
                "",
                "### Verifica PNRR Regione Toscana",
                "",
                f"Controllo machine-readable non completato: `{pnrr_error}`. Resta valido lo stato prudenziale della fonte primaria.",
            ]
        )

    with report_md.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--data", type=Path, default=Path("data/site-data.json"))
    parser.add_argument("--state", type=Path, default=Path("data/source-monitor-state.json"))
    parser.add_argument("--report-md", type=Path, required=True)
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--next-state", type=Path, required=True)
    parser.add_argument("--mode", choices=("live", "offline"), default="live")
    known, _ = parser.parse_known_args(argv)
    return known


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    forwarded = list(sys.argv[1:] if argv is None else argv)
    code = coverage.main(forwarded)
    if code:
        return code

    data = load(args.data)
    previous = load(args.state)
    next_state = load(args.next_state)
    report = load(args.report_json)
    next_state["schemaVersion"] = 2
    metrics = build_metric_state(data, previous, next_state, report)

    fuel_result = None
    fuel_error = ""
    pnrr_result = None
    pnrr_error = ""
    if args.mode == "live":
        fuel_result, fuel_error = run_fuel_verification(
            data,
            metrics,
            report,
            str(next_state.get("checkedAt") or ""),
        )
        if fuel_result is not None:
            report["fuelMimitVerification"] = fuel_result
        elif fuel_error:
            report["fuelMimitVerificationError"] = fuel_error
        pnrr_result, pnrr_error = run_pnrr_verification(
            data,
            metrics,
            str(next_state.get("checkedAt") or ""),
        )
        if pnrr_result is not None:
            report["pnrrToscanaVerification"] = pnrr_result
        elif pnrr_error:
            report["pnrrToscanaVerificationError"] = pnrr_error
        args.report_json.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    next_state["metrics"] = metrics
    args.next_state.write_text(
        json.dumps(next_state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    append_report_section(args.report_md, next_state, pnrr_result, pnrr_error)
    append_fuel_report_section(args.report_md, fuel_result, fuel_error)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())