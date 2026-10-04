#!/usr/bin/env python3
"""Importa soltanto stato diagnostico da run live fidati; mai valori del catalogo."""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from monthly_data_check_status import build_metric_state
from data_status_model import canonical_url, catalog_digest, published_period
import monthly_data_check_coverage as coverage

WORKFLOWS = {
    "monthly-data-refresh.yml": "deep",
    "source-monitor-light.yml": "light",
}


def timestamp(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Data senza timezone")
    return parsed


def trusted_run(run, workflow):
    return (
        run.get("head_branch") == "main"
        and run.get("event") in {"schedule", "workflow_dispatch"}
        and run.get("conclusion") == "success"
        and str(run.get("path") or "").split("@", 1)[0] == f".github/workflows/{workflow}"
    )


def read_artifact(raw, run, depth, data, registry, now):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        state_name = "source-monitor-light-state.next.json" if depth == "light" else "source-monitor-state.next.json"
        report_names = [name for name in names if name.endswith(".json") and name.startswith("source-monitor-light-" if depth == "light" else "data-check-") and not name.endswith("state.next.json")]
        if state_name not in names or len(report_names) != 1:
            raise ValueError("Artifact senza report/stato univoci")
        if any(archive.getinfo(name).file_size > 10_000_000 for name in (state_name, report_names[0])):
            raise ValueError("Artifact troppo grande")
        state = json.loads(archive.read(state_name))
        report = json.loads(archive.read(report_names[0]))
    checked = timestamp(state.get("checkedAt"))
    if checked > now or checked < timestamp(run["created_at"]) or checked > timestamp(run["updated_at"]):
        raise ValueError("Data del controllo incoerente con il run")
    if state.get("mode") != "live" or state.get("depth") != depth or state.get("schemaVersion") != 2:
        raise ValueError("Stato offline o profondità/schema non validi")
    if report.get("mode") != "live" or report.get("depth") != depth or report.get("status") not in {"no_changes", "changes_detected", "baseline_required"}:
        raise ValueError("Report non pubblicabile")
    if any(item.get("level") == "error" for item in report.get("findings", [])):
        raise ValueError("Errori strutturali nel report")
    if set(state.get("metrics", {})) != set(data["metrics"]):
        raise ValueError("Il run non copre il catalogo pubblico attuale")
    if any(state["metrics"][key].get("publishedPeriod") != published_period(metric) for key, metric in data["metrics"].items()):
        raise ValueError("I periodi del run non corrispondono al catalogo pubblicato")
    # Derivato dal catalogo effettivo, non da un conteggio fissato a mano.
    findings, source_map, _ = coverage.validate_dataset(data, registry)
    if any(item.get("level") == "error" for item in findings):
        raise ValueError("Catalogo non valido")
    expected = {canonical_url(url) for url in source_map}
    actual = {canonical_url(url) for url in state.get("sources", {})}
    if actual != expected:
        raise ValueError("Le fonti del run non coincidono con il catalogo")
    if report.get("catalogSha256") != catalog_digest(data):
        raise ValueError("Il report non certifica la versione attuale dei dati pubblicati")
    return state, report


def reconcile(data, previous, current, report):
    """Ricalcola gli stati legacy e conserva la provenienza della verifica periodo."""
    observation = json.loads(json.dumps(current))
    for key, item in observation["metrics"].items():
        old = previous.get("metrics", {}).get(key, {})
        old_verified = old.get("periodVerifiedAt") or ""
        new_verified = item.get("periodVerifiedAt") or ""
        if old_verified and (not new_verified or timestamp(old_verified) > timestamp(new_verified)):
            observation["metrics"][key] = item = json.loads(json.dumps(old))
        if not item.get("periodVerifiedAt"):
            item["periodVerifiedAt"] = str(old.get("periodVerifiedAt") or (old.get("checkedAt") if old.get("observedLatestPeriod") == item.get("observedLatestPeriod") else "") or "")
        if not item.get("observedLatestPeriod") and old.get("verificationEvidence"):
            observation["metrics"][key] = old
    # Il report deep contiene prove semantiche fresche soltanto per questi casi.
    if current.get("depth") == "deep":
        for report_key, keys in (("fuelMimitVerification", ("fuelPrices",)), ("pnrrToscanaVerification", ("pnrrFunding", "pnrrConcluded"))):
            if isinstance(report.get(report_key), dict):
                for key in keys:
                    if key in observation["metrics"]:
                        observation["metrics"][key]["periodVerifiedAt"] = current["checkedAt"]
    result = json.loads(json.dumps(current))
    result["metrics"] = build_metric_state(data, observation, result, report)
    if current.get("depth") == "deep":
        for report_key, keys in (("fuelMimitVerification", ("fuelPrices",)), ("pnrrToscanaVerification", ("pnrrFunding", "pnrrConcluded"))):
            if isinstance(report.get(report_key), dict):
                for key in keys:
                    if key in result["metrics"]:
                        result["metrics"][key] = observation["metrics"][key]
    result["lastDeepCheck"] = current["checkedAt"] if current.get("depth") == "deep" else previous.get("lastDeepCheck", "")
    return result


def gh_json(endpoint):
    return json.loads(subprocess.check_output(["gh", "api", endpoint], timeout=60))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.data.read_text())
    registry = json.loads(args.registry.read_text())
    selected = json.loads(args.state.read_text())
    candidates = []
    now = datetime.now(timezone.utc)
    for workflow, depth in WORKFLOWS.items():
        runs = gh_json(f"repos/{args.repo}/actions/workflows/{workflow}/runs?branch=main&status=success&per_page=10")
        for run in runs.get("workflow_runs", []):
            if not trusted_run(run, workflow):
                continue
            if timestamp(run["updated_at"]) <= timestamp(selected["checkedAt"]):
                continue
            artifacts = gh_json(f"repos/{args.repo}/actions/runs/{run['id']}/artifacts")
            prefix = "source-monitor-light-" if depth == "light" else "data-check-"
            matches = [a for a in artifacts.get("artifacts", []) if a["name"].startswith(prefix) and not a.get("expired")]
            if len(matches) != 1:
                continue
            try:
                raw = subprocess.check_output(["gh", "api", f"repos/{args.repo}/actions/artifacts/{matches[0]['id']}/zip"], timeout=60)
                state, report = read_artifact(raw, run, depth, data, registry, now)
            except (ValueError, KeyError, zipfile.BadZipFile) as exc:
                print(f"Run {run['id']} escluso: {exc}")
                continue
            candidates.append((state, report, run["id"]))
            break
    for state, report, run_id in sorted(candidates, key=lambda item: timestamp(item[0]["checkedAt"])):
        if timestamp(state["checkedAt"]) <= timestamp(selected["checkedAt"]):
            continue
        selected = reconcile(data, selected, state, report)
        selected["runtimeRunId"] = run_id
        print(f"Stato diagnostico selezionato: run {run_id}, {state['depth']}, {state['checkedAt']}")
    args.output.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n")
    print(f"Ultimo controllo pubblico: {selected['checkedAt']}; ultimo deep: {selected.get('lastDeepCheck', 'non registrato')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
