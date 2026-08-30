#!/usr/bin/env python3
"""Gate dati e contratto per Morosità ERP v1.25.0."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data/site-data.json"
REGISTRY = ROOT / "data/source-registry.json"
SNAPSHOT = ROOT / "data/source-snapshots/erp-lucca-arrears-2020-2024.json"
APP00 = ROOT / "assets/app-parts/00.txt"
APP03 = ROOT / "assets/app-parts/03.txt"
UXHC = ROOT / "assets/ux-history-core.js"
FINALIZER = ROOT / "scripts/finalize_catalog_release.py"

EXPECTED_2024 = {
    "046005": 7.37,
    "046013": 6.98,
    "046018": 3.48,
    "046024": 7.02,
    "046028": 4.41,
    "046030": 4.05,
    "046033": 10.83,
}
EXPECTED_HASHES = {
    2020: "0362d001246832bc66040c533a14b503ed9e6e3416d11a870638b56ccc3199bd",
    2021: "52d476f097066a3807099202ca508e961c6c61c5efe452a9861df538c980f757",
    2022: "831ba0712eb026ec955e45763831fe12ab6a941bc6f7940c585b888371ff872a",
    2023: "de36675ef97245b818bee99caec598f334166884e61c300c2be28c5d13902983",
    2024: "ca00f1a212d6fa29bdfa688ebc949ee5d9fb3c708342d36f07832add8b495422",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def close(a: float, b: float, tolerance: float = 0.011) -> bool:
    return abs(float(a) - float(b)) <= tolerance


def main() -> None:
    site = load(SITE)
    registry = load(REGISTRY)
    snapshot = load(SNAPSHOT)

    assert site["version"] == "v1.25.0"
    assert site["updated"] == "30 agosto 2026"
    assert len(site["metrics"]) == 166
    assert registry["expectedMetricCount"] == 166
    assert registry["expectedInlineMetricCount"] == 162
    assert registry["expectedExternalMetricCount"] == 4

    metric = site["metrics"]["erpArrears"]
    assert metric["meta"]["theme"] == "abitare"
    assert metric["meta"]["unit"] == "%"
    assert metric["meta"]["year"] == "2024"
    assert metric["meta"]["polarity"] == "neutral"
    assert metric["meta"]["comparisonReference"] == "aggregate"
    assert metric["meta"]["comparisonLabel"] == "valore Versilia"
    assert "non la media semplice" in metric["meta"]["comparisonNote"]
    assert metric["sourceUrl"] == "https://at.erplucca.it/default?path=75&t=1"
    assert metric["method"]["coverage"] == "7/7 · 2020–2024"
    assert "percentuali stampate incoerenti" in metric["method"]["caveat"]
    assert metric["history"]["years"] == [2020, 2021, 2022, 2023, 2024]

    sections = site["themes"]["abitare"]["sections"]
    erp_sections = [section for section in sections if section.get("key") == "erp-fragilita-abitativa"]
    assert len(erp_sections) == 1
    assert erp_sections[0]["metrics"] == ["erpArrears"]
    assert site["themes"]["abitare"]["metrics"].count("erpArrears") == 1
    assert [key for key in site["metrics"] if key.lower().startswith("erp")] == ["erpArrears"]

    rows = {row["code"]: row for row in metric["rows"]}
    assert set(rows) == set(EXPECTED_2024)
    for code, expected in EXPECTED_2024.items():
        row = rows[code]
        assert close(row["value"], expected), (code, row["value"], expected)
        assert row["series"]["years"] == [2020, 2021, 2022, 2023, 2024]
        assert len(row["series"]["values"]) == 5
        issued = row["accounting"]["issued"]
        arrears = row["accounting"]["arrears"]
        assert close(row["value"], arrears / issued * 100.0)

    assert close(metric["aggregate"]["value"], 8.56)
    simple_mean = sum(row["value"] for row in metric["rows"]) / len(metric["rows"])
    assert close(simple_mean, 6.31)
    assert not close(simple_mean, metric["aggregate"]["value"]), "Il benchmark ERP non deve usare la media semplice comunale"
    assert metric["aggregate"]["accounting"]["issued"] == 50285906.83
    assert metric["aggregate"]["accounting"]["arrears"] == 4304930.64
    assert close(metric["aggregate"]["accounting"]["arrears"] / metric["aggregate"]["accounting"]["issued"] * 100.0, 8.56)

    # Il dato anomalo 2023 di Massarosa deve restare quello pubblicato, non corretto o interpolato.
    massarosa = rows["046018"]
    index_2023 = massarosa["accountingSeries"]["years"].index(2023)
    assert massarosa["accountingSeries"]["issued"][index_2023] == 3164988.55
    assert massarosa["accountingSeries"]["arrears"][index_2023] == 64990.36
    assert close(massarosa["series"]["values"][index_2023], 2.05)

    # Ogni percentuale nello snapshot deve riconciliare con i due importi elementari.
    for code, source_row in snapshot["rows"].items():
        for item in source_row["values"]:
            assert abs(item["rate"] - item["arrears"] / item["issued"] * 100.0) < 0.00011, (code, item)
    for item in snapshot["aggregate"]["values"]:
        assert abs(item["rate"] - item["arrears"] / item["issued"] * 100.0) < 0.00011, item

    hashes = {item["year"]: item["sha256"] for item in snapshot["sourceDocuments"]}
    assert hashes == EXPECTED_HASHES
    assert any(item["type"] == "published_header_date_mismatch" and item["year"] == 2022 for item in snapshot["anomalies"])
    assert any(item["type"] == "published_percentage_inconsistency" and item["year"] == 2023 for item in snapshot["anomalies"])

    assert registry["metricOverrides"]["erpArrears"]["profile"] == "erp-lucca-annual-balance-sheet"
    profile = registry["sourceProfiles"]["erp-lucca-annual-balance-sheet"]
    assert profile["frequency"] == "annual"
    assert "SHA-256" in profile["acquisitionMethod"]

    app00 = APP00.read_text(encoding="utf-8")
    app03 = APP03.read_text(encoding="utf-8")
    history_core = UXHC.read_text(encoding="utf-8")
    assert "case '%'" in app00
    assert "erpArrears: ['morosità erp'" in app00
    assert "function erpArrearsDetailMarkup" in app03
    assert "Importi emessi cumulati" in app03 and "Morosità cumulata" in app03
    assert "${erpArrearsDetailMarkup(metric,row)}" in app03
    assert "erp-arrears-view" in app03
    assert "case '%'" in history_core
    assert "unit === '%' || unit === 'percent'" in history_core

    finalizer = FINALIZER.read_text(encoding="utf-8")
    assert 'VERSION = "v1.25.0"' in finalizer
    assert 'EXPECTED_METRICS = 166' in finalizer
    assert 'EXPECTED_INLINE = 162' in finalizer

    print("Morosità ERP v1.25.0: dati, formula, anomalie, UI e contratto verificati.")


if __name__ == "__main__":
    main()
