#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from data_status_model import ALLOWED_RELEASE_BASES, build_public_status, derive_status  # noqa: E402


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    data = load(ROOT / "data" / "site-data.json")
    registry = load(ROOT / "data" / "source-registry.json")
    state = load(ROOT / "data" / "source-monitor-state.json")
    public = build_public_status(data, registry, state)
    expected_count = int(registry["expectedMetricCount"])
    expected_inline = int(registry["expectedInlineMetricCount"])
    expected_external = int(registry["expectedExternalMetricCount"])
    special_routes = {
        key: metric
        for key, metric in data["metrics"].items()
        if isinstance(metric, dict)
        and isinstance(metric.get("dataStorage"), dict)
        and metric["dataStorage"].get("type") == "special-route"
    }
    expected_special = len(special_routes)

    assert expected_inline + expected_external + expected_special == expected_count
    assert public["metricCount"] == expected_count
    assert sum(public["counts"].values()) == expected_count
    assert set(public["counts"]) == {
        "current", "source_checked", "source_access_limited", "release_detected",
        "update_expected", "source_unavailable", "verification_required",
    }

    # Una fonte raggiungibile, senza annualità osservata, NON equivale a dato aggiornato.
    assert derive_status("2024", {"ok": True}, {}) == "source_checked"
    assert derive_status("2024", {"ok": False}, {}) == "source_unavailable"
    assert derive_status("2024", {"ok": True, "automationLimited": True}, {}) == "source_access_limited"
    assert derive_status("2024", {"ok": True}, {"observedLatestPeriod": "2024"}) == "current"
    assert derive_status("2024", {"ok": True}, {"observedLatestPeriod": "2025"}) == "release_detected"

    # La data globale dell'esecuzione non deve essere attribuita a una metrica
    # che ha una sonda di fonte ma non un controllo operativo registrato.
    sample_key = next(iter(data["metrics"]))
    sample_metric = data["metrics"][sample_key]
    sample_status = build_public_status(
        {"version": "test", "metrics": {sample_key: sample_metric}, "themes": data["themes"]},
        registry,
        {
            "schemaVersion": 2,
            "checkedAt": "2026-08-18T12:10:09+00:00",
            "sources": {sample_metric["sourceUrl"]: {"ok": True}},
            "metrics": {},
        },
    )["metrics"][0]
    assert sample_status["status"] == "source_checked"
    assert sample_status["lastChecked"] == "", "La data generale non è una prova per-metrica"

    for metric in public["metrics"]:
        release = metric.get("nextExpectedRelease")
        if release:
            assert release["basis"] in ALLOWED_RELEASE_BASES
            assert release.get("value")
        if metric["status"] == "current":
            assert metric["observedLatestPeriod"] == metric["publishedPeriod"]
        if metric["status"] == "source_access_limited":
            assert metric["sourceAutomationLimited"] is True
            assert metric["sourceReachable"] is False

    climate = [
        metric for metric in public["metrics"]
        if data["metrics"][metric["key"]].get("dataStorage", {}).get("type") == "external-climate"
    ]
    assert len(climate) == expected_external
    assert all(metric["isExternalClimate"] is True for metric in climate)
    assert all(
        metric["isExternalClimate"] is False
        for metric in public["metrics"]
        if metric not in climate
    )
    assert all(metric["publishedPeriod"] == "2025" for metric in climate)
    assert all("2026" not in metric["publishedPeriod"] for metric in climate)

    dist = ROOT / "dist"
    if dist.exists():
        status_path = dist / "data" / "data-status.json"
        page_path = dist / "stato-dati" / "index.html"
        assert status_path.is_file()
        assert page_path.is_file()
        materialized = load(status_path)
        assert materialized["metricCount"] == expected_count
        page = page_path.read_text(encoding="utf-8")
        assert "Stato dei dati" in page
        assert "rilevazione → validazione → pubblicazione" in page
        assert "Prossimo aggiornamento atteso" not in page
        assert page.count('href="../confronta/meteo-clima/"') == expected_external
        for metric in special_routes.values():
            detail_route = str(metric.get("meta", {}).get("detailRoute") or "").lstrip("/")
            assert detail_route, "Route dedicata mancante per una metrica special-route"
            assert page.count(f'href="../{detail_route}"') == 1
        assert f"Dettaglio dei {expected_count} indicatori" in page
        project = (dist / "progetto" / "index.html").read_text(encoding="utf-8")
        assert "data-status-project-link" in project
        indicators = list((dist / "indicatori").glob("*/index.html"))
        assert len(indicators) == expected_inline
        for path in indicators:
            text = path.read_text(encoding="utf-8")
            assert 'data-data-status-row="period"' in text, path
            assert 'data-data-status-row="state"' in text, path
            assert "Ultimo controllo Osservatorio" in text, path
            assert "Prossimo aggiornamento atteso" not in text, path
            assert "assets/data-status.css" in text, path

    print(
        f"Data status tests passed: {expected_count} indicators "
        f"({expected_inline} inline + {expected_external} external + {expected_special} special-route), "
        "static metadata, climate full years only."
    )


if __name__ == "__main__":
    main()
