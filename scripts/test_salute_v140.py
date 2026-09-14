#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATERIALIZER = ROOT / "scripts" / "materialize_salute_v140.py"
ARS_SNAPSHOT = ROOT / "data" / "source-snapshots" / "ars-salute-11-v140.json"
RSA_SNAPSHOT = ROOT / "data" / "source-snapshots" / "regione-toscana-rsa-accreditate-2025-v140.json"

EXPECTED_ARS = {
    1499: ("mortalityCancer", "2002-2011", "2013-2022", 12, "negative"),
    1327: ("mortalityCirculatory", "2002-2011", "2013-2022", 12, "negative"),
    1606: ("mortalityRespiratory", "2002-2011", "2013-2022", 12, "negative"),
    255: ("hypertensionPrevalence", "2015", "2025", 11, "negative"),
    268: ("copdPrevalence", "2015", "2025", 11, "negative"),
    269: ("ischemicHeartDiseasePrevalence", "2015", "2025", 11, "negative"),
    272: ("heartFailurePrevalence", "2015", "2025", 11, "negative"),
    273: ("priorStrokePrevalence", "2015", "2025", 11, "negative"),
    261: ("permanentRsaAssisted", "2016", "2024", 9, "neutral"),
    1425: ("specialistVisits7Psr", "2010", "2025", 16, "neutral"),
    1325: ("diagnosticImagingServices", "2010", "2025", 16, "neutral"),
}
RSA_VALUES = {
    "Camaiore": 5,
    "Forte dei Marmi": 0,
    "Massarosa": 0,
    "Pietrasanta": 2,
    "Seravezza": 2,
    "Stazzema": 0,
    "Viareggio": 4,
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_materializer():
    spec = importlib.util.spec_from_file_location("materialize_salute_v140", MATERIALIZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Impossibile caricare il materializzatore Salute v1.40")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    ars = load(ARS_SNAPSHOT)
    rsa = load(RSA_SNAPSHOT)
    assert set(map(int, ars["indicators"])) == set(EXPECTED_ARS)
    assert ars["versiliaAggregate"]["geographyCode"] == "202M"
    assert rsa["series"] == RSA_VALUES
    assert rsa["versilia"]["value"] == 13

    for iid, (key, first, last, count, _) in EXPECTED_ARS.items():
        source = ars["indicators"][str(iid)]
        periods = source["periods"]
        assert (periods[0], periods[-1], len(periods)) == (first, last, count), iid
        assert source["key"] == key
        assert source["sex"] == "totale"
        assert source["measurementField"] == "misura_standardizzata"
        assert source["coverage"] == "7/7"
        assert set(source["series"]) == set(RSA_VALUES) | {"Versilia"}
        for geography, cells in source["series"].items():
            assert len(cells) == count, (iid, geography)
            for cell in cells:
                assert cell["raw"] is not None, (iid, geography, cell["period"], "raw")
                assert cell["standardized"] is not None, (iid, geography, cell["period"], "standardized")
                assert cell["ci95Low"] is not None and cell["ci95High"] is not None, (iid, geography, cell["period"], "ci")
                assert cell["num"] is not None and cell["den"] is not None, (iid, geography, cell["period"], "num/den")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        tmp_data = tmp_root / "data"
        tmp_data.mkdir()
        site_path = tmp_data / "site-data.json"
        registry_path = tmp_data / "source-registry.json"
        shutil.copy2(ROOT / "data" / "site-data.json", site_path)
        shutil.copy2(ROOT / "data" / "source-registry.json", registry_path)
        before = load(site_path)
        before_count = len(before["metrics"])

        module = load_materializer()
        module.DATA = site_path
        module.REGISTRY = registry_path
        module.apply_overlay()

        data = load(site_path)
        registry = load(registry_path)
        assert len(data["metrics"]) == before_count + 12
        assert data["version"] == "v1.40.0"
        assert data["release_version"] == "1.40.0"
        assert registry["expectedMetricCount"] == len(data["metrics"])
        assert registry["expectedInlineMetricCount"] + registry["expectedExternalMetricCount"] == len(data["metrics"])

        salute = data["themes"]["salute"]
        theme_keys = set(salute["metrics"])
        sections = {section["key"]: set(section["metrics"]) for section in salute["sections"]}

        for iid, (key, first, last, count, polarity) in EXPECTED_ARS.items():
            assert key in data["metrics"] and key in theme_keys, key
            metric = data["metrics"][key]
            assert metric["meta"]["theme"] == "salute"
            assert metric["meta"]["polarity"] == polarity
            assert metric["meta"]["sourceMeta"]["measurement"] == "misura_standardizzata"
            assert len(metric["rows"]) == 7
            assert {row["town"] for row in metric["rows"]} == set(RSA_VALUES)
            for row in metric["rows"]:
                assert len(row["series"]["years"]) == count
                assert row["series"]["years"][0] == first
                assert row["series"]["years"][-1] == last
                assert row["value"] == row["series"]["values"][-1]
            source_versilia = ars["indicators"][str(iid)]["series"]["Versilia"]
            expected_aggregate = round(float(source_versilia[-1]["standardized"]) + 1e-12, 2)
            assert metric["aggregate"]["value"] == expected_aggregate, key
            assert metric["aggregate"]["series"]["values"][-1] == expected_aggregate, key
            assert "media" in metric["aggregate"]["note"].lower() and "non" in metric["aggregate"]["note"].lower(), key

        outcomes = {"mortalityCancer", "mortalityCirculatory", "mortalityRespiratory", "hypertensionPrevalence", "copdPrevalence", "ischemicHeartDiseasePrevalence", "heartFailurePrevalence", "priorStrokePrevalence"}
        territory = {"permanentRsaAssisted", "specialistVisits7Psr", "diagnosticImagingServices", "accreditedRsaCount"}
        assert outcomes <= sections["esiti"]
        assert territory <= sections["territorio"]

        rsa_metric = data["metrics"]["accreditedRsaCount"]
        assert rsa_metric["meta"]["polarity"] == "neutral"
        assert {row["town"]: row["value"] for row in rsa_metric["rows"]} == RSA_VALUES
        assert rsa_metric["aggregate"]["value"] == 13
        assert "posti letto" in rsa_metric["method"]["caveat"].lower()
        assert not any("rsa" in key.lower() and "bed" in key.lower() for key in data["metrics"])

    print("Salute v1.40: snapshot, 12 metriche, storici, aggregato ARS 202M, RSA 2025 e semantica neutral OK")


if __name__ == "__main__":
    main()
