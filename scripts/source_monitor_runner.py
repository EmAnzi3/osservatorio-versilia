#!/usr/bin/env python3
"""Orchestra il Source Monitor con profondità leggera o profonda."""
from __future__ import annotations

import argparse
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import monthly_data_check as base
import monthly_data_check_status as status
import source_monitor_strategy as strategy

DEPTH_LABELS = {
    "light": "light — raggiungibilità, redirect e struttura; senza hash o verifiche semantiche profonde",
    "deep": "deep — controllo completo con hash e verifiche semantiche disponibili",
}

SCHEMA_FINDING_CODES = {
    "registry_schema",
    "source_profile_shape",
    "source_profile_fields",
    "metric_shape",
    "meta_missing",
    "meta_key",
    "meta_field",
    "method_missing",
    "method_field",
    "rows_missing",
    "row_shape",
    "series_shape",
    "series_arrays",
    "series_length",
    "external_storage_field",
    "external_storage_path",
}


def parse_args(argv: list[str] | None = None) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--depth", choices=("light", "deep"), default="deep")
    known, forwarded = parser.parse_known_args(argv)
    return known, forwarded


def _skip_fuel(*_args, **_kwargs):
    return None, ""


def _skip_pnrr(*_args, **_kwargs):
    return None, ""


@contextmanager
def monitor_depth(depth: str) -> Iterator[None]:
    """Applica solo per il processo corrente le differenze tra light e deep."""
    original_should_hash = base.should_hash
    original_fuel = status.run_fuel_verification
    original_pnrr = status.run_pnrr_verification
    previous_depth = os.environ.get("MONITOR_CHECK_DEPTH")

    os.environ["MONITOR_CHECK_DEPTH"] = depth
    try:
        if depth == "light":
            base.should_hash = lambda *_args, **_kwargs: False
            status.run_fuel_verification = _skip_fuel
            status.run_pnrr_verification = _skip_pnrr
        yield
    finally:
        base.should_hash = original_should_hash
        status.run_fuel_verification = original_fuel
        status.run_pnrr_verification = original_pnrr
        if previous_depth is None:
            os.environ.pop("MONITOR_CHECK_DEPTH", None)
        else:
            os.environ["MONITOR_CHECK_DEPTH"] = previous_depth


def _option_path(args: list[str], name: str, default: Path | None = None) -> Path | None:
    prefix = name + "="
    for index, value in enumerate(args):
        if value.startswith(prefix):
            return Path(value[len(prefix):])
        if value == name and index + 1 < len(args):
            return Path(args[index + 1])
    return default


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def _write_json_depth(path: Path | None, depth: str) -> None:
    if path is None or not path.is_file():
        return
    payload = _load_json(path)
    payload["depth"] = depth
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _annotate_markdown(path: Path | None, depth: str) -> None:
    if path is None or not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if "**Profondità:**" in text:
        return
    lines = text.splitlines()
    insert_at = next(
        (index + 1 for index, line in enumerate(lines) if line.startswith("**Modalità:**")),
        min(4, len(lines)),
    )
    lines.insert(insert_at, f"**Profondità:** `{depth}` — {DEPTH_LABELS[depth]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def annotate_outputs(forwarded: list[str], depth: str) -> None:
    report_json = _option_path(forwarded, "--report-json")
    next_state = _option_path(forwarded, "--next-state")
    report_md = _option_path(forwarded, "--report-md")
    _write_json_depth(report_json, depth)
    _write_json_depth(next_state, depth)
    _annotate_markdown(report_md, depth)

    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as handle:
            handle.write(f"depth={depth}\n")


def build_strategy_artifact(forwarded: list[str]) -> dict[str, Any]:
    data_path = _option_path(forwarded, "--data", Path("data/site-data.json"))
    registry_path = _option_path(forwarded, "--registry", Path("data/source-registry.json"))
    previous_state = _option_path(forwarded, "--state", Path("data/source-monitor-state.json"))
    next_state = _option_path(forwarded, "--next-state")
    report_json = _option_path(forwarded, "--report-json")
    if not all((data_path, registry_path, previous_state, next_state, report_json)):
        raise RuntimeError("Argomenti insufficienti per derivare la strategia Source Monitor")
    output = report_json.parent / "source-monitor-strategy.json"
    return strategy.write_strategy(
        data_path,
        registry_path,
        next_state,
        previous_state,
        output,
    )


def _change_urls(report: dict[str, Any]) -> set[str]:
    changes = report.get("changes")
    if not isinstance(changes, dict):
        return set()
    urls: set[str] = set()
    for items in changes.values():
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and item.get("url"):
                try:
                    urls.add(base.canonical_url(str(item["url"])))
                except Exception:
                    urls.add(str(item["url"]))
    return urls


def _is_schema_finding(item: dict[str, Any]) -> bool:
    code = str(item.get("code") or "")
    return (
        code in SCHEMA_FINDING_CODES
        or "schema" in code
        or code.endswith("_shape")
        or code.endswith("_field")
    )


def build_operational_summary(
    report: dict[str, Any],
    next_state: dict[str, Any],
    strategy_payload: dict[str, Any],
) -> dict[str, int]:
    strategy_summary = strategy_payload.get("summary")
    strategy_summary = strategy_summary if isinstance(strategy_summary, dict) else {}
    source_strategies = strategy_payload.get("sources")
    source_strategies = source_strategies if isinstance(source_strategies, dict) else {}

    metrics = next_state.get("metrics")
    metrics = metrics if isinstance(metrics, dict) else {}
    status_counts: dict[str, int] = {}
    for item in metrics.values():
        if isinstance(item, dict):
            state = str(item.get("status") or "verification_required")
            status_counts[state] = status_counts.get(state, 0) + 1

    report_sources = report.get("sources")
    report_sources = report_sources if isinstance(report_sources, dict) else {}
    unreachable = sum(
        1 for item in report_sources.values()
        if isinstance(item, dict) and not item.get("ok")
    )
    findings = report.get("findings")
    findings = findings if isinstance(findings, list) else []
    schema_changes = sum(
        1 for item in findings
        if isinstance(item, dict) and _is_schema_finding(item)
    )

    signaled = _change_urls(report)
    current_urls: set[str] = set()
    for raw_url in source_strategies:
        try:
            current_urls.add(base.canonical_url(str(raw_url)))
        except Exception:
            current_urls.add(str(raw_url))
    unchanged = len(current_urls - signaled)

    return {
        "coveredMetrics": int(strategy_summary.get("metricsWithStrategy") or 0),
        "publicMetrics": int(strategy_summary.get("publicMetricCount") or 0),
        "sources": int(strategy_summary.get("sourceCount") or 0),
        "sourcesWithKnownSuccessfulCheck": int(
            strategy_summary.get("sourcesWithKnownSuccessfulCheck") or 0
        ),
        "updatesExpected": status_counts.get("update_expected", 0),
        "newReleases": status_counts.get("release_detected", 0),
        "verificationRequired": status_counts.get("verification_required", 0),
        "unreachableSources": unreachable,
        "schemaOrStructureChanges": schema_changes,
        "unchangedSources": unchanged,
    }


def _render_operational_summary(summary: dict[str, int]) -> str:
    return "\n".join(
        [
            "### Riepilogo operativo A2",
            "",
            "| Voce | Esito |",
            "|---|---:|",
            f"| Indicatori con strategia / pubblicati | {summary['coveredMetrics']}/{summary['publicMetrics']} |",
            f"| Fonti con strategia | {summary['sources']} |",
            f"| Fonti con ultimo successo noto | {summary['sourcesWithKnownSuccessfulCheck']}/{summary['sources']} |",
            f"| Aggiornamenti attesi/disponibili | {summary['updatesExpected']} |",
            f"| Nuove release da verificare | {summary['newReleases']} |",
            f"| Fonti irraggiungibili | {summary['unreachableSources']} |",
            f"| Cambi di schema/struttura rilevati | {summary['schemaOrStructureChanges']} |",
            f"| Fonti senza segnali di variazione | {summary['unchangedSources']} |",
            f"| Indicatori che richiedono verifica | {summary['verificationRequired']} |",
            "",
        ]
    )


def append_operational_summary(forwarded: list[str], strategy_payload: dict[str, Any]) -> dict[str, int]:
    report_json_path = _option_path(forwarded, "--report-json")
    report_md_path = _option_path(forwarded, "--report-md")
    next_state_path = _option_path(forwarded, "--next-state")
    if not all((report_json_path, report_md_path, next_state_path)):
        raise RuntimeError("Output monitor incompleti per il riepilogo A2")

    report = _load_json(report_json_path)
    next_state = _load_json(next_state_path)
    summary = build_operational_summary(report, next_state, strategy_payload)
    report["operationalSummary"] = summary
    report_json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    markdown = report_md_path.read_text(encoding="utf-8")
    section = _render_operational_summary(summary)
    marker_positions = [
        pos for marker in ("\n### Modifiche", "\n### Segnali", "\n### Regola")
        if (pos := markdown.find(marker)) >= 0
    ]
    if marker_positions:
        pos = min(marker_positions)
        markdown = markdown[:pos] + "\n\n" + section + markdown[pos:]
    else:
        markdown = markdown.rstrip() + "\n\n" + section
    report_md_path.write_text(markdown.rstrip() + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    args, forwarded = parse_args(argv)
    with monitor_depth(args.depth):
        code = status.main(forwarded)
    if code == 0:
        annotate_outputs(forwarded, args.depth)
        payload = build_strategy_artifact(forwarded)
        strategy_summary = payload["summary"]
        operational = append_operational_summary(forwarded, payload)
        print(
            "Source monitor strategy: "
            f"{strategy_summary['metricsWithStrategy']}/{strategy_summary['publicMetricCount']} indicatori · "
            f"{strategy_summary['sourceCount']} fonti · "
            f"{strategy_summary['sourcesWithKnownSuccessfulCheck']} con ultimo successo noto"
        )
        print(
            "Source monitor report: "
            f"release={operational['newReleases']} · "
            f"unreachable={operational['unreachableSources']} · "
            f"schema={operational['schemaOrStructureChanges']} · "
            f"unchanged={operational['unchangedSources']}"
        )
    print(f"Source monitor depth: {args.depth}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
