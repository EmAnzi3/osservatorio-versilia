#!/usr/bin/env python3
"""Test di regressione del controllo mensile."""

from __future__ import annotations

import io
import json
import subprocess
import zipfile
import sys
import tempfile
from pathlib import Path

import monthly_data_check_coverage as coverage
import monthly_data_check_status as status_model
import monthly_data_check as checker
import monitor_semantic_checks as semantics

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "monthly_data_check.py"
TOWNS = [
    {"name": "Camaiore", "code": "046005"},
    {"name": "Forte dei Marmi", "code": "046013"},
    {"name": "Massarosa", "code": "046018"},
    {"name": "Pietrasanta", "code": "046024"},
    {"name": "Seravezza", "code": "046028"},
    {"name": "Stazzema", "code": "046030"},
    {"name": "Viareggio", "code": "046033"},
]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_checker(
    work: Path,
    state: dict,
    *,
    not_applicable_code: str | None = None,
) -> dict:
    data = {
        "towns": TOWNS,
        "metrics": {
            "population": {
                "meta": {
                    "key": "population",
                    "theme": "demografia",
                    "label": "Popolazione residente",
                    "unit": "number",
                    "year": "2026",
                    "source": "Istat",
                },
                "sourceUrl": "https://example.invalid/population.csv",
                "rows": [
                    {
                        "town": town["name"],
                        "code": town["code"],
                        "value": 100,
                        "series": {"years": [2025, 2026], "values": [99, 100]},
                    }
                    for town in TOWNS
                ],
                "method": {
                    "type": "Dato ufficiale",
                    "formula": "Valore pubblicato dalla fonte.",
                    "coverage": "7/7",
                },
            }
        },
    }
    if not_applicable_code is not None:
        row = next(
            item
            for item in data["metrics"]["population"]["rows"]
            if item["code"] == not_applicable_code
        )
        row.update(
            {
                "value": None,
                "formatted": "n.a.",
                "notApplicable": True,
                "applicabilityNote": "Fenomeno non applicabile a questo territorio.",
                "series": None,
            }
        )
    registry = {
        "schemaVersion": 2,
        "expectedMetricCount": 1,
        "expectedInlineMetricCount": 1,
        "expectedExternalMetricCount": 0,
        "expectedTowns": TOWNS,
        "defaults": {
            "monitorMode": "availability",
            "unreachableIsBlocker": False,
        },
        "sourceProfiles": {
            "test-annual": {
                "publisher": "Fonte di test",
                "frequency": "annual",
                "frequencyLabel": "Annuale",
                "expectedRelease": "Ogni anno",
                "acquisitionMethod": "Dataset di test",
                "licenseName": "Licenza di test",
                "licenseUrl": "https://example.invalid/license",
            }
        },
        "sourceProfileByUrl": {
            "https://example.invalid/population.csv": "test-annual",
        },
        "metricOverrides": {},
        "contentExtensions": [".csv"],
        "requestTimeoutSeconds": 2,
        "maxDownloadBytes": 1024,
    }
    data_path = work / "data.json"
    registry_path = work / "registry.json"
    state_path = work / "state.json"
    report_md = work / "report.md"
    report_json = work / "report.json"
    next_state = work / "next-state.json"
    write_json(data_path, data)
    write_json(registry_path, registry)
    write_json(state_path, state)

    subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--mode",
            "offline",
            "--data",
            str(data_path),
            "--registry",
            str(registry_path),
            "--state",
            str(state_path),
            "--report-md",
            str(report_md),
            "--report-json",
            str(report_json),
            "--next-state",
            str(next_state),
        ],
        cwd=ROOT,
        check=True,
    )
    return json.loads(report_json.read_text(encoding="utf-8"))


def main() -> None:
    multi_sources = list(
        checker.iter_metric_sources(
            {
                "sourceUrl": "https://example.org/catalog",
                "sourceUrls": {
                    "catalogo": "https://example.org/catalog",
                    "bus": "https://example.org/bus.gtfs",
                    "rail": "https://example.org/rail.gtfs",
                },
                "meta": {"benchmark": {"url": "https://example.org/benchmark.csv"}},
            }
        )
    )
    assert multi_sources == [
        ("primary", "https://example.org/catalog"),
        ("source:bus", "https://example.org/bus.gtfs"),
        ("source:rail", "https://example.org/rail.gtfs"),
        ("benchmark", "https://example.org/benchmark.csv"),
    ]

    mef_old = (
        "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php"
        "?tree=2013&t=111"
    )
    mef_new = (
        "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php"
        "?tree=2013&t=222"
    )
    mef_stable = (
        "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php"
        "?tree=2013"
    )
    assert coverage.canonical_url(mef_old) == mef_stable
    assert coverage.canonical_url(mef_new) == mef_stable
    assert coverage.canonical_url("https://example.org/data?t=222").endswith("?t=222")

    redirect_changes = coverage.compare_states(
        {
            "sources": {
                "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php": {
                    "ok": True,
                    "finalUrl": mef_old,
                }
            }
        },
        {
            "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php": {
                "ok": True,
                "finalUrl": mef_new,
            }
        },
    )
    assert not redirect_changes["redirect"]

    # Due ZIP con gli stessi membri ma timestamp differenti devono produrre lo
    # stesso hash semantico: ARS rigenera il contenitore senza cambiare il CSV.
    def zip_payload(year: int) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            info = zipfile.ZipInfo("data.csv", date_time=(year, 1, 1, 0, 0, 0))
            archive.writestr(info, "anno,valore\n2022,1.0\n")
        return buffer.getvalue()

    zip_hash_a, zip_mode_a = semantics.semantic_content_hash(zip_payload(2025))
    zip_hash_b, zip_mode_b = semantics.semantic_content_hash(zip_payload(2026))
    assert zip_mode_a == zip_mode_b == "zip-members"
    assert zip_hash_a == zip_hash_b

    volatile_url = "https://example.org/live.gtfs"
    volatile_changes = checker.compare_states(
        {"sources": {volatile_url: {"ok": True, "finalUrl": volatile_url, "contentSha256": "old", "contentHashMode": "raw"}}},
        {volatile_url: {"ok": True, "finalUrl": volatile_url, "contentSha256": "new", "contentHashMode": "raw", "contentChangePolicy": "informational", "contentChangeReason": "feed continuo"}},
    )
    assert not volatile_changes["content"]
    assert volatile_changes["informationalContent"] == [{"url": volatile_url, "reason": "feed continuo"}]

    zip_migration = checker.compare_states(
        {"sources": {volatile_url: {"ok": True, "finalUrl": volatile_url, "contentSha256": "legacy"}}},
        {volatile_url: {"ok": True, "finalUrl": volatile_url, "contentSha256": zip_hash_a, "contentHashMode": "zip-members"}},
    )
    assert not zip_migration["content"]

    fuel_metric = {
        "rows": [
            {"town": "A", "stationCount": 1, "parts": [{"label": "Benzina self", "value": 1.8}, {"label": "Gasolio self", "value": 1.7}]},
            {"town": "B", "stationCount": 0, "parts": [{"label": "Benzina self", "value": None}, {"label": "Gasolio self", "value": None}]},
        ]
    }
    fuel_live = {"referenceDate": "2026-08-28", "coverage": "1/2", "sourceUrls": {"prezzi": "https://example.org/fuel.csv"}, "towns": {"A": {"benzina": 1.8, "gasolio": 1.7, "stations": 1}, "B": {"benzina": None, "gasolio": None, "stations": 0}}}
    assert semantics.fuel_metric_matches(fuel_metric, fuel_live)
    fuel_state = {"publishedPeriod": "2026-08-28", "status": "verification_required"}
    evidence = status_model.apply_fuel_verification_result(fuel_metric, fuel_state, fuel_live, "2026-08-29T00:00:00+00:00")
    assert fuel_state["status"] == "current"
    assert evidence["verdict"] == "match"
    newer_state = {"publishedPeriod": "2026-08-27", "status": "current"}
    evidence = status_model.apply_fuel_verification_result(fuel_metric, newer_state, fuel_live, "2026-08-29T00:00:00+00:00")
    assert newer_state["status"] == "release_detected"
    assert evidence["verdict"] == "new_period"

    # L'ingresso di una URL nella nuova baseline del monitor non è un'anomalia
    # del dato. Solo contenuto o redirect cambiati di una fonte già monitorata
    # richiedono una verifica umana.
    new_source = "https://example.org/new-source"
    changed_source = "https://example.org/changed-source"
    status_changes = status_model.changed_urls(
        {
            "changes": {
                "added": [{"url": new_source}],
                "removed": [{"url": "https://example.org/old-source"}],
                "content": [{"url": changed_source}],
                "redirect": [],
            }
        }
    )
    assert coverage.canonical_url(new_source) not in status_changes
    assert coverage.canonical_url(changed_source) in status_changes

    # Un endpoint ufficiale alternativo può attestare solo la raggiungibilità
    # tecnica del servizio: identità e URL pubblica della fonte restano originali.
    original = "https://example.org/source"
    fallback = "https://example.org/source/download"
    fallback_state = coverage._as_official_fallback(
        original,
        fallback,
        {
            "ok": True,
            "status": 200,
            "finalUrl": fallback,
            "contentType": "text/html",
            "error": "",
            "probeMethod": "curl-range",
        },
    )
    assert fallback_state["url"] == original
    assert fallback_state["finalUrl"] == coverage.canonical_url(original)
    assert fallback_state["probeUrl"] == fallback
    assert fallback_state["directReachable"] is False
    assert fallback_state["probeMethod"].startswith("official-fallback:")

    # Un 403 di un portale esplicitamente noto per limitare i bot non viene
    # mascherato come fonte raggiunta né promosso a indisponibilità del dato.
    pnrr_url = "https://www.italiadomani.gov.it/content/sogei-ng/it/it/catalogo-open-data.html"
    limited_state = coverage._as_automation_limited(
        pnrr_url,
        {
            "ok": False,
            "status": 403,
            "finalUrl": pnrr_url,
            "contentType": "text/html",
            "error": "HTTP 403",
        },
    )
    assert limited_state["ok"] is True
    assert limited_state["directReachable"] is False
    assert limited_state["automationLimited"] is True
    assert limited_state["probeMethod"] == "automation-limited"
    assert limited_state["finalUrl"] == coverage.canonical_url(pnrr_url)

    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        first = run_checker(
            work / "first",
            {"schemaVersion": 1, "checkedAt": None, "sources": {}},
        )
        assert first["status"] == "baseline_required"
        assert first["summary"]["metricCount"] == 1
        assert first["summary"]["inlineMetricCount"] == 1
        assert first["summary"]["externalMetricCount"] == 0
        assert first["summary"]["townCount"] == 7
        assert not first["findings"]

        baseline = {
            "schemaVersion": 1,
            "checkedAt": "2026-08-01T00:00:00+00:00",
            "mode": "offline",
            "sources": first["sources"],
        }
        second = run_checker(work / "second", baseline)
        assert second["status"] == "no_changes"
        assert not second["changes"]["content"]
        assert not second["changes"]["removed"]

        # Un n.a. esplicito descrive un fenomeno fuori perimetro e non è un
        # valore corrente mancante. Il monitor deve però continuare a esigere
        # flag, formato, motivazione e assenza di una serie artificiale.
        not_applicable = run_checker(
            work / "not-applicable",
            baseline,
            not_applicable_code="046018",
        )
        assert not any(
            item["code"] == "value_missing" and item.get("metric") == "population"
            for item in not_applicable["findings"]
        )
        assert not not_applicable["findings"], not_applicable["findings"]

        changed = dict(baseline)
        sources = dict(baseline["sources"])
        sources["https://example.invalid/removed.csv"] = {
            "url": "https://example.invalid/removed.csv",
            "ok": True,
            "status": 200,
            "finalUrl": "https://example.invalid/removed.csv",
        }
        changed["sources"] = sources
        third = run_checker(work / "third", changed)
        assert third["status"] == "changes_detected"
        assert third["changes"]["removed"]

    print("Monthly data monitor tests passed.")


if __name__ == "__main__":
    main()
