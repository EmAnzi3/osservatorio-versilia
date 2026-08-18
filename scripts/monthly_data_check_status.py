#!/usr/bin/env python3
"""Estende il controllo mensile esistente con uno stato operativo per indicatore.

Non modifica valori pubblicati. Il wrapper usa il monitor esistente, quindi aggiunge
metadata senza introdurre un secondo sistema di polling.
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
from data_status_model import canonical_url, published_period  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON non valido: {path}")
    return value


def changed_urls(report: dict[str, Any]) -> set[str]:
    """Restituisce solo cambiamenti di una fonte già monitorata.

    Una URL appena aggiunta alla baseline non è di per sé un'anomalia: se il
    controllo live la raggiunge, lo stato corretto è `source_checked`. Le fonti
    rimosse non appartengono invece alla sorgente corrente dell'indicatore e non
    devono contaminare il suo stato. Restano significativi contenuto e redirect.
    """
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

        if probe is None:
            item["status"] = "verification_required"
        elif not probe.get("ok"):
            item["status"] = "source_unavailable"
        elif source_key in changed:
            # Un cambiamento tecnico di una fonte già monitorata non equivale a
            # un nuovo dato. Se un periodo più recente era già stato verificato,
            # lo manteniamo; altrimenti richiediamo una verifica umana.
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


def append_report_section(report_md: Path, state: dict[str, Any]) -> None:
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
        "release_detected": "Nuovo rilascio da verificare",
        "update_expected": "Aggiornamento atteso",
        "source_unavailable": "Fonte temporaneamente non verificabile",
        "verification_required": "Verifica necessaria",
    }
    for key in labels:
        lines.append(f"| {labels[key]} | {counts.get(key, 0)} |")
    with report_md.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--data", type=Path, default=Path("data/site-data.json"))
    parser.add_argument("--state", type=Path, default=Path("data/source-monitor-state.json"))
    parser.add_argument("--report-md", type=Path, required=True)
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--next-state", type=Path, required=True)
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
    next_state["metrics"] = build_metric_state(data, previous, next_state, report)
    args.next_state.write_text(
        json.dumps(next_state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    append_report_section(args.report_md, next_state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
