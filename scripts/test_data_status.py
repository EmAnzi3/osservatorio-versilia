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

    assert public["metricCount"] == 127
    assert sum(public["counts"].values()) == 127
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
    assert len(climate) == 4
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
        assert materialized["metricCount"] == 127
        page = page_path.read_text(encoding="utf-8")
        assert "Stato dei dati" in page
        assert "rilevazione → validazione → pubblicazione" in page
        assert "Prossimo aggiornamento atteso" not in page
        assert page.count('href="../confronta/meteo-clima/"') == 4
        project = (dist / "progetto" / "index.html").read_text(encoding="utf-8")
        assert "data-status-project-link" in project
        indicators = list((dist / "indicatori").glob("*/index.html"))
        assert len(indicators) == 123
        for path in indicators:
            text = path.read_text(encoding="utf-8")
            assert 'data-data-status-row="period"' in text, path
            assert 'data-data-status-row="state"' in text, path
            assert "Ultimo controllo Osservatorio" in text, path
            assert "Prossimo aggiornamento atteso" not in text, path
            assert "assets/data-status.css" in text, path

    print("Data status tests passed: 127 indicators, static metadata, climate full years only.")


if __name__ == "__main__":
    main()
