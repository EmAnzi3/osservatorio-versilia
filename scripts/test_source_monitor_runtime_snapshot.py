#!/usr/bin/env python3
"""Regressioni: falsi rilasci, provenienza delle date e trust degli artifact."""
import copy
import io
import http.client
from threading import Barrier, Lock
from unittest.mock import patch
import monthly_data_check as base
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import monthly_data_check_coverage as coverage
from data_status_model import compare_periods, catalog_digest, published_period
from monthly_data_check_status import build_metric_state, run_fuel_verification
from source_monitor_runtime_snapshot import read_artifact, reconcile, trusted_run


def main():
    live = {"referenceDate": "2026-10-04", "coverage": "0/0", "sourceUrls": {"prezzi": "https://example.org/fuel.csv"}, "towns": {}}
    fuel_data = {"metrics": {"fuelPrices": {"sourceUrl": "https://example.org/fuel.csv", "rows": []}}}
    fuel_state = {"fuelPrices": {"publishedPeriod": "2026-08-28", "status": "current"}}
    with patch.dict("os.environ", {"MONITOR_CHECK_DEPTH": "deep", "MONITOR_RUN_TRIGGER": "workflow_dispatch"}), patch("monthly_data_check_status.fuel_mimit.collect", return_value=live) as collect:
        evidence, error = run_fuel_verification(fuel_data, fuel_state, {}, "2026-10-04T10:00:00Z")
        collect.assert_called_once()
        assert not error and evidence["verdict"] == "new_period", "Il deep manuale deve verificare MIMIT"
    barrier, lock = Barrier(2), Lock()
    active, peak = 0, 0

    def parallel_probe(url, registry):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        barrier.wait(timeout=5)
        with lock:
            active -= 1
        return {"ok": True, "url": url}

    urls = {f"https://example.org/{index}": {} for index in range(4)}
    with patch.object(base, "probe_source", side_effect=parallel_probe):
        result = base.probe_sources(urls, {}, "live")
    assert peak == 2 and list(result) == sorted(urls), "Limite per host e ordine deterministico"
    with patch.object(base, "open_request", side_effect=http.client.RemoteDisconnected("connection closed")):
        probe = base.probe_source("https://example.org/", {})
        assert probe["ok"] is False and "connection closed" in probe["error"]
    assert compare_periods("agosto 2026", "2026-08") == 0
    assert compare_periods("2 settembre 2026", "2026-09-02") == 0
    assert compare_periods("2025", "2026") == 1
    assert compare_periods("2026-09", "2026-08") == -1
    assert compare_periods("2 settembre 2026", "2026-09") is None
    assert compare_periods("DCRT 24/2025 · confini Istat 1 gennaio 2026", "2025") is None
    assert compare_periods("PRC vigente · variante 2025", "2026-09") is None
    assert compare_periods("2026-13", "2026-14") is None
    assert compare_periods("31 febbraio 2026", "2026-02-28") is None

    data = {"metrics": {"sample": {"meta": {"year": "agosto 2026"}, "sourceUrl": "https://example.org/"}}}
    previous = {"checkedAt": "2026-08-31T10:00:00+00:00", "metrics": {"sample": {"checkedAt": "2026-08-29T10:00:00+00:00", "observedLatestPeriod": "2026-08"}}}
    current = {"checkedAt": "2026-10-04T10:00:00+00:00", "depth": "light", "sources": {"https://example.org/": {"ok": True}}}
    item = build_metric_state(data, previous, current, {})["sample"]
    assert item["status"] == "current", "Stesso mese: nessun falso rilascio"
    assert item["checkedAt"] == current["checkedAt"]
    assert item["periodVerifiedAt"] == "2026-08-29T10:00:00+00:00"
    changed = {"changes": {"content": [{"url": "https://example.org/"}]}}
    assert build_metric_state(data, previous, current, changed)["sample"]["status"] == "verification_required"
    updated = copy.deepcopy(previous)
    updated["metrics"]["sample"].update(publishedPeriod="luglio 2026", releaseEvidence={"verdict": "new_period"})
    assert build_metric_state(data, updated, current, {})["sample"]["status"] == "current", "Una release già acquisita non resta un allarme"
    legacy = copy.deepcopy(current)
    legacy["metrics"] = {"sample": {"observedLatestPeriod": "2026-08", "status": "release_detected", "checkedAt": current["checkedAt"]}}
    fixed = reconcile(data, previous, legacy, {})
    assert fixed["metrics"]["sample"]["status"] == "current"
    assert fixed["metrics"]["sample"]["periodVerifiedAt"] == "2026-08-29T10:00:00+00:00"
    deep_previous = copy.deepcopy(previous)
    deep_previous["metrics"]["sample"].update(observedLatestPeriod="2026-09", periodVerifiedAt="2026-10-03T10:00:00+00:00")
    assert reconcile(data, deep_previous, legacy, {})["metrics"]["sample"]["observedLatestPeriod"] == "2026-09", "Light non cancella una verifica deep più recente"

    previous_source = copy.deepcopy(previous)
    previous_source["sources"] = {"https://example.org/": {"lastSuccessfulCheck": "2026-10-03", "lastSuccessfulContent": {"contentSha256": "valid"}, "releaseCatalogue": {"ok": True, "fingerprint": "valid", "markers": ["dataset_2025.csv"]}}}
    preserved = reconcile(data, previous_source, legacy, {})["sources"]["https://example.org/"]
    assert preserved["lastSuccessfulContent"]["contentSha256"] == "valid"
    assert preserved["lastSuccessfulReleaseCatalogue"]["markers"] == ["dataset_2025.csv"]
    root = Path(__file__).resolve().parents[1]
    catalog = json.loads((root / "data/site-data.json").read_text())
    registry = json.loads((root / "data/source-registry.json").read_text())
    findings, sources, _ = coverage.validate_dataset(catalog, registry)
    assert not [f for f in findings if f["level"] == "error"]
    state = {"schemaVersion": 2, "mode": "live", "depth": "light", "checkedAt": current["checkedAt"], "metrics": {key: {"publishedPeriod": published_period(metric)} for key, metric in catalog["metrics"].items()}, "sources": {url: {} for url in sources}}
    report = {"mode": "live", "depth": "light", "status": "no_changes", "findings": [], "catalogSha256": catalog_digest(catalog)}
    run = {"created_at": "2026-10-04T09:00:00Z", "updated_at": "2026-10-04T11:00:00Z", "head_branch": "main", "event": "schedule", "conclusion": "success", "path": ".github/workflows/source-monitor-light.yml"}
    assert trusted_run(run, "source-monitor-light.yml")
    for field, value in (("event", "pull_request"), ("head_branch", "other"), ("conclusion", "failure"), ("path", ".github/workflows/other.yml")):
        assert not trusted_run({**run, field: value}, "source-monitor-light.yml")

    def archive(payload, summary=report):
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w") as z:
            z.writestr("source-monitor-light-state.next.json", json.dumps(payload))
            z.writestr("source-monitor-light-2026-10-04.json", json.dumps(summary))
        return raw.getvalue()

    now = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)
    read_artifact(archive(state), run, "light", catalog, registry, now)
    invalid = []
    for key, value in (("mode", "offline"), ("depth", "deep"), ("checkedAt", "2026-10-05T10:00:00Z"), ("metrics", {}), ("sources", {})):
        invalid.append(archive({**state, key: value}))
    invalid.append(archive(state, {**report, "findings": [{"level": "error"}]}))
    invalid.append(archive(state, {**report, "catalogSha256": "old-catalog"}))
    for raw in invalid:
        try:
            read_artifact(raw, run, "light", catalog, registry, now)
        except ValueError:
            pass
        else:
            raise AssertionError("Artifact non verificato accettato")
    pages = (root / ".github/workflows/pages.yml").read_text()
    radar = (root / ".github/workflows/opportunity-radar-daily.yml").read_text()
    assert 'workflows: ["Controllo mensile dati", "Controllo frequente fonti"]' in pages
    assert "github.event.workflow_run.event == 'schedule'" in pages
    assert "github.event.workflow_run.head_branch == 'main'" in pages
    for workflow in (pages, radar):
        assert "python scripts/source_monitor_runtime_snapshot.py" in workflow
        assert "data/source-monitor-state.json" in workflow
    print("Source monitor runtime: periodi, date, provenienza e copertura PASS")


if __name__ == "__main__":
    main()
