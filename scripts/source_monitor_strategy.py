#!/usr/bin/env python3
"""Deriva la strategia operativa del Source Monitor dal catalogo pubblico.

Non introduce un nuovo manifest canonico: unisce catalogo/registry materializzati
con lo stato del run corrente e, quando disponibile, con la baseline precedente.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import monthly_data_check_coverage as coverage
import monitor_semantic_checks as semantics
from source_policy import resolve_metric_policy

SEMANTIC_METRICS = {
    "fuelPrices": "mimit-fuel",
    "pnrrFunding": "pnrr-toscana",
    "pnrrConcluded": "pnrr-toscana",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def _unique(values) -> list[str]:
    return sorted({str(value).strip() for value in values if str(value).strip()})


def _normalized_sources(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = state.get("sources")
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for raw_url, item in raw.items():
        if not isinstance(item, dict):
            continue
        try:
            url = coverage.canonical_url(str(raw_url))
        except Exception:
            url = str(raw_url)
        result[url] = item
    return result


def _fallback_success(previous: dict[str, Any], item: dict[str, Any] | None) -> str:
    if not isinstance(item, dict):
        return ""
    explicit = str(item.get("lastSuccessfulCheck") or "").strip()
    if explicit:
        return explicit
    if previous.get("mode") == "live" and item.get("ok"):
        return str(previous.get("checkedAt") or "").strip()
    return ""


def last_check_state(
    url: str,
    current: dict[str, Any],
    previous: dict[str, Any],
) -> dict[str, Any]:
    current_sources = _normalized_sources(current)
    previous_sources = _normalized_sources(previous)
    item = current_sources.get(url)
    old = previous_sources.get(url)
    current_mode = str(current.get("mode") or "")
    checked_at = str(current.get("checkedAt") or "").strip()
    last_success = _fallback_success(previous, old)

    if isinstance(item, dict):
        if current_mode == "live" and item.get("ok"):
            last_success = checked_at
        if current_mode == "offline":
            result = "offline_validation"
        elif item.get("automationLimited"):
            result = "automation_limited"
        elif item.get("ok"):
            result = "reachable"
        else:
            result = "unreachable"
        return {
            "lastAttemptAt": checked_at,
            "lastSuccessfulCheck": last_success,
            "lastResult": result,
            "probeMethod": str(item.get("probeMethod") or ""),
            "httpStatus": item.get("status"),
        }

    return {
        "lastAttemptAt": "",
        "lastSuccessfulCheck": last_success,
        "lastResult": "not_checked",
        "probeMethod": "",
        "httpStatus": None,
    }


def _change_policy(url: str, registry: dict[str, Any]) -> dict[str, str]:
    direct = semantics.source_change_policy(url, registry)
    if direct:
        return direct
    raw = registry.get("sourceChangePolicies")
    if not isinstance(raw, dict):
        return {}
    for candidate, item in raw.items():
        if not isinstance(item, dict):
            continue
        try:
            if coverage.canonical_url(str(candidate)) != url:
                continue
        except Exception:
            continue
        return {
            "contentChange": str(item.get("contentChange") or "").strip(),
            "redirectChange": str(item.get("redirectChange") or "").strip(),
            "reason": str(item.get("reason") or "").strip(),
        }
    return {}


def build_strategy_from_source_map(
    data: dict[str, Any],
    registry: dict[str, Any],
    current_state: dict[str, Any],
    previous_state: dict[str, Any],
    source_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo pubblico privo di metrics")

    strategies: dict[str, dict[str, Any]] = {}
    covered_metrics: set[str] = set()

    for raw_url, source in sorted(source_map.items()):
        url = coverage.canonical_url(str(raw_url))
        metric_ids = sorted({str(value) for value in source.get("metrics", []) if str(value)})
        policies = [
            resolve_metric_policy(metric_id, metrics[metric_id], registry)
            for metric_id in metric_ids
            if metric_id in metrics and isinstance(metrics[metric_id], dict)
        ]
        frequencies = _unique(policy.get("frequency") for policy in policies)
        frequency_labels = _unique(policy.get("frequencyLabel") for policy in policies)
        expected_release = _unique(policy.get("expectedRelease") for policy in policies)
        monitor_modes = _unique(policy.get("monitorMode") or "availability" for policy in policies)
        profile_ids = _unique(
            [*source.get("profileIds", []), *(policy.get("profileId") for policy in policies)]
        )
        semantic_checks = _unique(
            SEMANTIC_METRICS[metric_id]
            for metric_id in metric_ids
            if metric_id in SEMANTIC_METRICS
        )
        change_policy = _change_policy(url, registry)
        detection = ["availability", "redirect", "content-hash-when-supported"]
        detection.extend(f"semantic:{item}" for item in semantic_checks)

        if not frequencies or not expected_release or not monitor_modes:
            raise RuntimeError(f"Strategia fonte incompleta: {url}")

        covered_metrics.update(metric_ids)
        strategies[url] = {
            "url": url,
            "metrics": metric_ids,
            "roles": _unique(source.get("roles", [])),
            "profileIds": profile_ids,
            "frequency": frequencies,
            "frequencyLabels": frequency_labels,
            "expectedRelease": expected_release,
            "monitorModes": monitor_modes,
            "changeDetection": _unique(detection),
            "changePolicy": {
                "content": change_policy.get("contentChange") or "substantial",
                "redirect": change_policy.get("redirectChange") or "substantial",
                "reason": change_policy.get("reason") or "",
            },
            "lastCheck": last_check_state(url, current_state, previous_state),
        }

    public_ids = set(metrics)
    missing_metrics = sorted(public_ids - covered_metrics)
    if missing_metrics:
        raise RuntimeError(
            "Indicatori pubblici senza strategia fonte: " + ", ".join(missing_metrics[:20])
        )

    known_success = sum(
        1
        for item in strategies.values()
        if item["lastCheck"].get("lastSuccessfulCheck")
    )
    return {
        "schemaVersion": 1,
        "generatedFrom": {
            "catalogVersion": str(data.get("version") or ""),
            "catalogUpdated": str(data.get("updated") or ""),
            "monitorCheckedAt": str(current_state.get("checkedAt") or ""),
            "monitorMode": str(current_state.get("mode") or ""),
            "monitorDepth": str(current_state.get("depth") or ""),
        },
        "summary": {
            "publicMetricCount": len(public_ids),
            "metricsWithStrategy": len(covered_metrics),
            "metricsWithoutStrategy": len(missing_metrics),
            "sourceCount": len(strategies),
            "sourcesWithKnownSuccessfulCheck": known_success,
            "sourcesWithoutKnownSuccessfulCheck": len(strategies) - known_success,
        },
        "sources": strategies,
    }


def build_strategy(
    data: dict[str, Any],
    registry: dict[str, Any],
    current_state: dict[str, Any],
    previous_state: dict[str, Any],
) -> dict[str, Any]:
    findings, source_map, _summary = coverage.validate_dataset(data, registry)
    errors = [item for item in findings if item.get("level") == "error"]
    if errors:
        first = errors[0]
        raise RuntimeError(
            f"Catalogo non valido per strategia monitor: {first.get('code')} — {first.get('message')}"
        )
    return build_strategy_from_source_map(data, registry, current_state, previous_state, source_map)


def write_strategy(
    data_path: Path,
    registry_path: Path,
    state_path: Path,
    previous_state_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    payload = build_strategy(
        load(data_path),
        load(registry_path),
        load(state_path),
        load(previous_state_path),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--previous-state", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = write_strategy(
        args.data,
        args.registry,
        args.state,
        args.previous_state,
        args.output,
    )
    summary = payload["summary"]
    print(
        "Strategia Source Monitor derivata: "
        f"{summary['metricsWithStrategy']}/{summary['publicMetricCount']} indicatori · "
        f"{summary['sourceCount']} fonti · "
        f"{summary['sourcesWithKnownSuccessfulCheck']} con ultimo successo noto."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
