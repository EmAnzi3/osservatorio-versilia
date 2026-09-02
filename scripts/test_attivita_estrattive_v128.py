#!/usr/bin/env python3
"""Regression test del lotto Attività estrattive v1.28.0."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data/site-data.json"
REGISTRY = ROOT / "data/source-registry.json"
STATE = ROOT / "data/source-monitor-state.json"
SNAPSHOT = ROOT / "data/source-snapshots/attivita-estrattive-v128.json"

EXPECTED_TOWNS = {
    "046005": ("Camaiore", 0),
    "046013": ("Forte dei Marmi", 0),
    "046018": ("Massarosa", 1),
    "046024": ("Pietrasanta", 2),
    "046028": ("Seravezza", 44),
    "046030": ("Stazzema", 43),
    "046033": ("Viareggio", 0),
}
EXPECTED_STATE = {
    "Attiva": 15,
    "Inattiva": 2,
    "Sospesa": 5,
    "Scaduta": 3,
    "Ripristino": 0,
    "Chiusa": 64,
    "n.d.": 1,
}
RAW_FIELDS = {
    "cod_comprensorio", "cod_istat", "codice_giacimento", "codice_rt",
    "id_caratteristica", "id_cava", "id_comprensorio", "id_comune",
    "id_giacimento", "id_stato", "id_tipo_prestito", "id_tipo_prima_prod",
    "id_tipologia", "lat", "localita", "lon", "nome_cava",
    "nome_comprensorio", "nome_comune", "nome_giacimento", "nome_provincia",
    "sigla_provincia", "stato", "tipo_produzione", "tipologia",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parts(row):
    return {item["key"]: item["value"] for item in row.get("parts", [])}


def main() -> None:
    site = load(SITE)
    registry = load(REGISTRY)
    state = load(STATE)
    snapshot = load(SNAPSHOT)

    assert site["version"] == "v1.28.0"
    assert site["updated"] == "2 settembre 2026"
    assert len(site["metrics"]) == 180
    assert registry["expectedMetricCount"] == 180
    assert registry["expectedInlineMetricCount"] == 176
    assert registry["expectedExternalMetricCount"] == 4

    section = next(s for s in site["themes"]["ambiente"]["sections"] if s["key"] == "attivita-estrattive")
    assert section["metrics"] == ["extractiveSites", "extractiveProduction", "extractivePlanning"]

    sites = site["metrics"]["extractiveSites"]
    assert sites["aggregate"]["value"] == 90
    aggregate_parts = parts(sites["aggregate"])
    assert aggregate_parts["state_active"] == 15
    assert aggregate_parts["state_inactive"] == 2
    assert aggregate_parts["state_suspended"] == 5
    assert aggregate_parts["state_expired"] == 3
    assert aggregate_parts["state_restoration"] == 0
    assert aggregate_parts["state_closed"] == 64
    assert aggregate_parts["state_nd"] == 1
    assert aggregate_parts["type_ordinary"] == 82
    assert aggregate_parts["type_restoreworks"] == 2
    assert aggregate_parts["type_recovery"] == 6
    assert aggregate_parts["prod_ornamental"] == 88
    assert aggregate_parts["prod_industrial"] == 1
    assert aggregate_parts["prod_construction"] == 1

    rows = {r["code"]: r for r in sites["rows"]}
    assert set(rows) == set(EXPECTED_TOWNS)
    records = []
    for code, (town, count) in EXPECTED_TOWNS.items():
        row = rows[code]
        assert row["town"] == town and row["value"] == count
        town_records = row["extractiveDetail"]["records"]
        assert len(town_records) == count
        records.extend(town_records)
    assert len(records) == 90
    assert len({r["codice_rt"] for r in records}) == 90
    assert len({r["id_cava"] for r in records}) == 90
    assert all(set(r) == RAW_FIELDS for r in records), "Il dettaglio RTCave non deve perdere campi pubblici"

    states = Counter("n.d." if r["stato"] in (None, "") else r["stato"] for r in records)
    assert {key: states.get(key, 0) for key in EXPECTED_STATE} == EXPECTED_STATE
    assert Counter(r["tipologia"] for r in records) == Counter({"Cava Ordinaria": 82, "Piano di recupero": 6, "Opere di ripristino": 2})
    assert Counter(r["tipo_produzione"] for r in records) == Counter({"ORNAMENTALE": 88, "INDUSTRIALE": 1, "COSTRUZIONE": 1})

    massarosa = rows["046018"]["extractiveDetail"]["records"]
    assert len(massarosa) == 1
    assert massarosa[0]["codice_rt"] == "09046018002"
    assert massarosa[0]["nome_cava"] == "SULLA PIEVE"
    assert massarosa[0]["stato"] == "Inattiva"
    assert massarosa[0]["tipo_produzione"] == "INDUSTRIALE"
    assert massarosa[0]["nome_comprensorio"] == "Fuori Comprensorio"

    stazzema_records = rows["046030"]["extractiveDetail"]["records"]
    assert len(stazzema_records) == 43
    assert sum(r["stato"] is None for r in stazzema_records) == 1
    assert any(r["nome_cava"] == "TOMBACCIO" and r["stato"] is None for r in stazzema_records)

    production = site["metrics"]["extractiveProduction"]
    assert production["aggregate"]["value"] == 79452
    assert production["aggregate"]["label"] == "Versilia · somma valori comunali disponibili (2/7)"
    assert production["aggregate"]["series"] == {"years": [2019, 2020, 2021, 2022, 2023, 2024, 2025], "values": [51045, 59712, 69852, 88857, 78846, 91566, 79452]}
    assert production["aggregate"]["coverage"] == "2/7"
    assert "non implica produzione zero" in production["aggregate"]["note"]
    prod_rows = {r["code"]: r for r in production["rows"]}
    assert prod_rows["046028"]["series"] == {"years": [2019, 2020, 2021, 2022, 2023, 2024, 2025], "values": [31151, 46093, 52048, 57199, 53518, 53194, 55801]}
    assert prod_rows["046030"]["series"]["values"] == [19894, 13619, 17804, 31658, 25328, 38372, 23651]
    assert prod_rows["046028"]["value"] == 55801
    assert prod_rows["046030"]["value"] == 23651
    assert prod_rows["046030"]["productionDetail"]["components"][-1] == {"year": 2025, "bacinoStazzema": 21479, "cardosoApuane": 2172, "total": 23651}
    assert prod_rows["046028"]["productionDetail"]["ops2019_2038"] == 1680487
    assert prod_rows["046030"]["productionDetail"]["ops2019_2038"] == 1504871
    assert sum(r["value"] is None for r in production["rows"]) == 5

    planning = site["metrics"]["extractivePlanning"]
    plan_rows = {r["code"]: r["prcDetail"] for r in planning["rows"]}
    assert plan_rows["046024"]["gp"] == [1, 11.39, 0.271]
    assert plan_rows["046028"]["g"] == [2, 37.976, 0.965]
    assert plan_rows["046028"]["acc"] == [7, 156.322, 3.971]
    assert plan_rows["046030"]["g"] == [1, 19.021, 0.236]
    assert plan_rows["046030"]["acc"] == [12, 400.173, 4.959]
    assert plan_rows["046005"]["mos"] == 2 and plan_rows["046005"]["pmos"] == 3 and plan_rows["046005"]["sed"] == 25
    assert plan_rows["046018"]["sed"] == 53
    assert plan_rows["046028"]["sed"] == 105
    assert plan_rows["046030"]["sed"] == 151
    plan_agg = parts(planning["aggregate"])
    assert plan_agg["g_n"] == 3 and plan_agg["g_ha"] == 56.997 and plan_agg["g_pct"] == 0.160
    assert plan_agg["gp_n"] == 1 and plan_agg["gp_ha"] == 11.390 and plan_agg["gp_pct"] == 0.032
    assert plan_agg["acc_n"] == 19 and plan_agg["acc_ha"] == 556.495 and plan_agg["acc_pct"] == 1.559
    assert next(p for p in planning["aggregate"]["parts"] if p["key"] == "g_pct")["unit"] == "%"

    assert snapshot["rtcave"]["regionalRecordCount"] == 666
    assert snapshot["rtcave"]["regionalUniqueCodiceRt"] == 666
    assert snapshot["rtcave"]["regionalUniqueIdCava"] == 666
    assert snapshot["rtcave"]["versiliaRecordCount"] == 90
    assert set(snapshot["rtcave"]["rawFieldNames"]) == RAW_FIELDS
    assert len(snapshot["rtcave"]["records"]) == 90
    assert snapshot["prc"]["crs"] == "EPSG:3003"
    assert "non esaustiva" in snapshot["prc"]["sedNote"]

    assert state["metrics"]["extractiveSites"]["status"] == "current"
    assert state["metrics"]["extractiveProduction"]["observedLatestPeriod"] == "2025"
    assert registry["metricOverrides"]["extractiveSites"]["profile"] == "regione-toscana-rtcave-continuous"

    app0 = (ROOT / "assets/app-parts/00.txt").read_text(encoding="utf-8")
    app3 = (ROOT / "assets/app-parts/03.txt").read_text(encoding="utf-8")
    loader = (ROOT / "assets/app.js").read_text(encoding="utf-8")
    history = (ROOT / "assets/ux-history.js").read_text(encoding="utf-8")
    materializer = (ROOT / "scripts/materialize_attivita_estrattive_v128.py").read_text(encoding="utf-8")
    release_patch = (ROOT / "scripts/patch_attivita_estrattive_v128_release.py").read_text(encoding="utf-8")
    assert "case 'cubicMetres'" in app0
    assert "extractiveSites:" in app0 and "extractivePlanning:" in app0
    assert "function extractiveDetailMarkup" in app3
    assert "extractiveTownDetailMarkup(metric,row)" in app3
    assert "detailGroup === 'extractive'" in app3
    assert "const extractiveProductionHistory = metricKey === 'extractiveProduction' && historical;" in app3
    assert "extractiveProductionHistory ? seriesChart(row.series" in app3
    compare_history = history.split("function enhanceCompare(data)", 1)[1].split("function forceItalianGrouping", 1)[0]
    town_history = history.split("function enhanceTown(data)", 1)[1].split("function enhance(data)", 1)[0]
    assert "if (selected.key === 'extractiveProduction') return;" not in compare_history
    assert "if (selected.key === 'extractiveProduction') {" in compare_history
    assert "if (selected.key === 'extractiveProduction') return;" in town_history
    assert "const loader = document.currentScript;" in loader
    assert "const VERSION='20260902-v128-attivita-estrattive';" in loader
    assert "def rebuild_app" not in materializer
    assert "def rebuild_app" not in release_patch

    print("Attività estrattive v1.28 verificate: 3 card, 90/90 record RTCave completi, produzione e PRC riconciliati.")


if __name__ == "__main__":
    main()
