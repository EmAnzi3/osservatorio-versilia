#!/usr/bin/env python3
"""Gate dati, metodo e integrazione della release Mobilità TPL v1.19.0."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import materialize_mobilita_tpl_v119 as materializer
from finalize_catalog_release import (
    EXPECTED_EXTERNAL,
    EXPECTED_INLINE,
    EXPECTED_METRICS,
    UPDATED,
    VERSION,
)
from monthly_data_check import iter_metric_sources


ROOT = Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "data" / "source-registry.json").read_text(encoding="utf-8"))
SNAP = json.loads(
    (ROOT / "data" / "source-snapshots" / "mobilita-tpl-2026-08-26.json").read_text(encoding="utf-8")
)
TRIPS = "scheduledTplTripsPer1000"
ACCESS = "activeTplAccessPoints"
SPAN = "tplServiceSpan"
KEYS = [TRIPS, ACCESS, SPAN]
EXPECTED = {
    "Camaiore": (330, 298, 32, 151, 19, "05:50:00", "29:51:10", 24.02),
    "Forte dei Marmi": (110, 110, 0, 31, 6, "06:28:56", "29:24:04", 22.92),
    "Massarosa": (106, 86, 20, 131, 6, "05:52:00", "21:34:34", 15.71),
    "Pietrasanta": (236, 182, 54, 107, 12, "05:23:00", "29:41:00", 24.30),
    "Seravezza": (119, 65, 54, 102, 9, "05:19:00", "23:12:00", 17.88),
    "Stazzema": (26, 26, 0, 80, 1, "06:10:32", "20:07:02", 13.94),
    "Viareggio": (659, 549, 110, 254, 21, "05:30:00", "30:04:00", 24.57),
}
EXPECTED_HASHES = {
    "Istat confini 2026": "b011a590656c3a3ebc297fba80726a376aa843b6f164641cf6a4a990021a81d6",
    "GTFS Autolinee Toscane": "799ece1cdfc517044fcd4cf6ff9366effceeab9fa15c8ee5cf9fd7f20b5ed3de",
    "GTFS Trenitalia": "a262c5bdfccd98a5c7e7ae08eea8eecb3189222f34c1015f5d4608faf3efc152",
}


def close(left: float, right: float, tolerance: float = 1e-10) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)


def seconds(value: str) -> int:
    hours, minutes, secs = (int(part) for part in value.split(":"))
    return hours * 3600 + minutes * 60 + secs


def main() -> None:
    # Il lotto TPL resta v1.19, ma il gate deve seguire il contratto globale
    # della release corrente invece di congelare i conteggi della v1.20.
    assert SITE["version"] == VERSION
    assert SITE["updated"] == UPDATED
    assert len(SITE["metrics"]) == REGISTRY["expectedMetricCount"] == EXPECTED_METRICS
    assert REGISTRY["expectedInlineMetricCount"] == EXPECTED_INLINE
    assert REGISTRY["expectedExternalMetricCount"] == EXPECTED_EXTERNAL

    assert SNAP["snapshotVersion"] == "2026-08-26-v3"
    assert SNAP["status"] == "release-verified-7of7"
    assert SNAP["referenceDate"] == "2026-08-26"
    assert SNAP["scope"]["coverage"] == "7/7"
    assert SNAP["derivation"]["metricKeys"] == KEYS
    assert set(SNAP["raw"]) == set(EXPECTED)
    for source, digest in EXPECTED_HASHES.items():
        assert SNAP["sources"][source]["sha256"] == digest

    trip_rows = {row["town"]: row for row in SITE["metrics"][TRIPS]["rows"]}
    access_rows = {row["town"]: row for row in SITE["metrics"][ACCESS]["rows"]}
    span_rows = {row["town"]: row for row in SITE["metrics"][SPAN]["rows"]}

    for town, expected in EXPECTED.items():
        trips, bus, rail, points, routes, first, last, span = expected
        raw = SNAP["raw"][town]
        assert (raw["trips"], raw["busTrips"], raw["railTrips"]) == (trips, bus, rail)
        assert raw["activeAccessPoints"] == points
        assert raw["routes"] == routes
        assert (raw["first"], raw["last"]) == (first, last)
        assert close(round((seconds(last) - seconds(first)) / 3600, 2), span)
        assert close(raw["serviceSpanHours"], span)
        assert close(raw["tripsPer1000"], trips / raw["population"] * 1000)
        assert close(raw["accessPointsPer1000"], points / raw["population"] * 1000)

        assert trip_rows[town]["value"] == trips
        assert close(trip_rows[town]["normalized"]["value"], raw["tripsPer1000"])
        assert access_rows[town]["value"] == points
        assert close(access_rows[town]["normalized"]["value"], raw["accessPointsPer1000"])
        assert close(span_rows[town]["value"], span)

        code = trip_rows[town]["code"]
        detail = SITE["details"][code]["mobility"]["tpl"]
        assert (detail["trips"], detail["busTrips"], detail["railTrips"]) == (trips, bus, rail)
        assert detail["activeAccessPoints"] == points
        assert detail["routes"] == routes
        assert close(detail["serviceSpanHours"], span)
        assert detail["firstDeparture"] == raw["firstDisplay"]
        assert detail["lastDeparture"] == raw["lastDisplay"]

    population = sum(item["population"] for item in SNAP["raw"].values())
    trip_total = sum(item[0] for item in EXPECTED.values())
    point_total = sum(item[3] for item in EXPECTED.values())
    span_total = sum(item[7] for item in EXPECTED.values())
    trips = SITE["metrics"][TRIPS]
    access = SITE["metrics"][ACCESS]
    span = SITE["metrics"][SPAN]

    assert trip_total == 1586 and point_total == 856
    assert close(trips["aggregate"]["value"], trip_total / 7)
    assert trips["aggregate"]["value"] != trips["aggregate"]["totalValue"] == trip_total
    assert close(trips["normalizedAggregate"]["value"], trip_total / population * 1000)
    assert close(access["aggregate"]["value"], point_total / 7)
    assert access["aggregate"]["value"] != access["aggregate"]["totalValue"] == point_total
    assert close(access["normalizedAggregate"]["value"], point_total / population * 1000)
    assert close(span["aggregate"]["value"], span_total / 7)
    assert span["aggregate"]["value"] != span["aggregate"]["totalValue"]
    assert all(metric["aggregate"]["label"] == "Media dei 7 Comuni" for metric in (trips, access, span))
    assert trips["normalizedAggregate"]["label"] == "Media ponderata dei 7 Comuni"
    assert access["normalizedAggregate"]["label"] == "Media ponderata dei 7 Comuni"
    viareggio_delta = (access_rows["Viareggio"]["value"] / access["aggregate"]["value"] - 1) * 100
    assert close(viareggio_delta, 107.71028037383177)

    expected_urls = set(materializer.SOURCE_URLS.values())
    profile_id = "regione-toscana-gtfs-scheduled"
    for key in KEYS:
        metric = SITE["metrics"][key]
        assert metric["meta"]["detailGroup"] == "tpl"
        assert metric["method"]["coverage"] == "7/7"
        assert metric["method"]["snapshot"] == materializer.SNAPSHOT_REF
        assert len(metric["rows"]) == 7
        assert set(metric["sourceUrls"].values()) == expected_urls
        monitored = {url for _, url in iter_metric_sources(metric)}
        assert monitored == expected_urls
        assert materializer.BUS_URL in monitored and materializer.RAIL_URL in monitored
        assert REGISTRY["metricOverrides"][key]["profile"] == profile_id
    for url in expected_urls:
        assert REGISTRY["sourceProfileByUrl"][url] == profile_id
        assert REGISTRY["sourceUrlProfiles"][url] == profile_id
    assert "senza stime" in REGISTRY["sourceProfiles"][profile_id]["acquisitionMethod"]

    assert "(feed, stop_id)" in SNAP["rules"]["accessPoint"]
    assert "secondi GTFS" in SNAP["rules"]["serviceSpan"]
    assert "0 è ammesso solo" in SNAP["rules"]["zero"]
    assert "n.d." in SNAP["rules"]["missing"]
    assert "non è usato come benchmark" in SNAP["derivation"]["aggregateTrips"]
    assert "solo descrittivo" in SNAP["derivation"]["aggregateAccessPoints"]

    theme = SITE["themes"]["mobilita"]
    sections = [section for section in theme["sections"] if section["key"] == "trasporto-pubblico"]
    assert len(sections) == 1 and sections[0]["metrics"] == KEYS
    assert all(theme["metrics"].count(key) == 1 for key in KEYS)
    assert [key for section in theme["sections"] for key in section["metrics"]] == theme["metrics"]

    app = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((ROOT / "assets" / "app-parts").glob("*.txt"))
    )
    for token in (
        "case 'hours':",
        "function tplCompareDetailMarkup(data)",
        'class="tpl-service-cell"',
        'class="aggregate-note tpl-detail-note"',
        'class="deep-facts-grid tpl-town-service-grid"',
        '<span>Bus</span>',
        '<span>Ferrovia</span>',
        '<span>Finestra di servizio</span>',
        "const definitionControls = '';",
        'class="compare-chart-toolbar scale-toolbar"',
        "deepDiveMarkup(data, town, themeKey, metricKey)",
        "if (!isFlow) return '';",
    ):
        assert token in app, token
    assert "Flussi e parco veicolare" not in app
    assert "Mobility TPL v1.19" not in (ROOT / "assets" / "fidelity.css").read_text(encoding="utf-8")
    tpl_css = (ROOT / "assets" / "chart-surfaces.css").read_text(encoding="utf-8")
    visual_grammar = (ROOT / "assets" / "visual-grammar.js").read_text(encoding="utf-8")
    assert "Mobilità TPL v1.19 — regole locali" in tpl_css
    assert "#compare-bars .tpl-chart-toolbar" in tpl_css
    assert "hoverLabel.className = 'bar-hover-label'" in visual_grammar
    assert "track.append(hoverLabel)" in visual_grammar
    assert ".tpl-service-range" in tpl_css and ".tpl-service-span" in tpl_css
    assert ".tpl-compare-detail > .tpl-detail-note" in tpl_css
    assert ".tpl-town-detail > .tpl-detail-note" in tpl_css
    assert ".tpl-town-deep-dive .tpl-town-service-grid" in tpl_css
    source_page = (ROOT / "confronta" / "mobilita" / "index.html").read_text(encoding="utf-8")
    assert "Mobilità e infrastrutture · Confronto dei comuni della Versilia" in source_page
    assert "incidenti stradali e contesto provinciale della criminalità" not in source_page

    # Il materializzatore deve convergere: una seconda applicazione non cambia il risultato.
    candidate_site = copy.deepcopy(SITE)
    candidate_registry = copy.deepcopy(REGISTRY)
    materializer.apply_site(candidate_site, SNAP)
    materializer.apply_registry(candidate_registry)
    once = json.dumps((candidate_site, candidate_registry), ensure_ascii=False, sort_keys=True)
    materializer.apply_site(candidate_site, SNAP)
    materializer.apply_registry(candidate_registry)
    twice = json.dumps((candidate_site, candidate_registry), ensure_ascii=False, sort_keys=True)
    assert once == twice

    print(
        "Mobilità TPL v1.19.0 verificata: fonti effettive monitorate, dati 7/7, "
        "benchmark medi e materializzazione idempotente."
    )


if __name__ == "__main__":
    main()
