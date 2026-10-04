#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from semantic_model_contract import validate_semantic_model_contract


def expect_failure(payload: dict, path: Path, contract: Path, needle: str) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        validate_semantic_model_contract(path, contract)
    except AssertionError as exc:
        assert needle in str(exc), (needle, str(exc))
    else:
        raise AssertionError(f"Regressione semantica non intercettata: {needle}")


def sample_catalog() -> dict:
    return {
        "towns": [
            {"name": "Comune A", "code": "001"},
            {"name": "Comune B", "code": "002"},
        ],
        "themes": {
            "demo": {"label": "Demografia", "metrics": ["population"]}
        },
        "metrics": {
            "population": {
                "meta": {
                    "label": "Popolazione",
                    "theme": "demo",
                    "year": 2025,
                    "unit": "number",
                    "source": "Fonte ufficiale",
                    "benchmark": {
                        "year": 2025,
                        "source": "Fonte benchmark",
                        "url": "https://example.test/benchmark",
                        "tuscany": 100.0,
                        "italy": 90.0,
                    },
                },
                "sourceUrl": "https://example.test/source",
                "aggregate": {"value": 150.0},
                "rows": [
                    {"town": "Comune A", "code": "001", "value": 100, "series": {"years": [2024, 2025], "values": [98, 100]}},
                    {"town": "Comune B", "code": "002", "value": 200, "normalized": {"value": 20, "unit": "per1000"}},
                ],
            }
        },
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    contract = root / "ci" / "semantic-model-contract.json"

    with tempfile.TemporaryDirectory(prefix="a6-semantic-") as tmp:
        path = Path(tmp) / "catalog.json"
        payload = sample_catalog()
        path.write_text(json.dumps(payload), encoding="utf-8")
        report = validate_semantic_model_contract(path, contract)
        assert report["municipalities"] == 2
        assert report["themes"] == 1
        assert report["metrics"] == 1
        assert report["historicalSeries"] == 1
        assert report["benchmarkMetrics"] == 1

        bad = copy.deepcopy(payload)
        bad["metrics"]["population"]["meta"]["theme"] = "missing"
        expect_failure(bad, path, contract, "Tema semantico sconosciuto")

        bad = copy.deepcopy(payload)
        bad["metrics"]["population"]["sourceUrl"] = ""
        expect_failure(bad, path, contract, "Fonte semantica incompleta")

        bad = copy.deepcopy(payload)
        bad["metrics"]["population"]["rows"][0]["series"]["values"] = [98]
        expect_failure(bad, path, contract, "Serie years/values disallineata")

        bad = copy.deepcopy(payload)
        bad["metrics"]["population"]["rows"][0]["code"] = "002"
        expect_failure(bad, path, contract, "Town/code incoerenti")

        # Each rejection protects a concrete future query from silently using
        # the wrong municipality, period, unit, value or missing-data status.
        cases = [
            ("Nome Comune sconosciuto", lambda m: m["rows"][0].update(town="Unknown")),
            ("Codice Comune sconosciuto", lambda m: m["rows"][0].update(code="999")),
            ("Riga comunale senza identità", lambda m: m["rows"][0].update(town="", code="")),
            ("Riga comunale duplicata", lambda m: m["rows"].append(copy.deepcopy(m["rows"][0]))),
            ("Valore comunale non numerico/finito", lambda m: m["rows"][0].update(value=float("nan"))),
            ("Valore comunale non numerico/finito", lambda m: m["rows"][0].update(value=True)),
            ("Stato mancante con valore", lambda m: m["rows"][0].update(notApplicable=True)),
            ("Stati mancanti contraddittori", lambda m: m["rows"][0].update(value=None, notApplicable=True, dataUnavailable=True)),
            ("Unità semantica non esplicita", lambda m: m["meta"].pop("unit")),
            ("Periodo storico mancante", lambda m: m["rows"][0]["series"].update(years=[None, 2025])),
            ("Periodi duplicati", lambda m: m["rows"][0]["series"].update(years=[2025, "2025"])),
            ("Valore storico non numerico/finito", lambda m: m["rows"][0]["series"].update(values=[98, float("inf")])),
            ("Serie years/values disallineata", lambda m: m["rows"][0].update(componentSeries={"female": {"years": [2024, 2025], "values": [98]}})),
            ("Serie incompleta", lambda m: m["rows"][0].update(longSeries={"years": [2024, 2025]})),
            ("URL benchmark non valido", lambda m: m["meta"]["benchmark"].update(url="invalid")),
            ("Valore benchmark non finito", lambda m: m["meta"]["benchmark"].update(italy=float("inf"))),
        ]
        for needle, mutate in cases:
            bad = copy.deepcopy(payload)
            mutate(bad["metrics"]["population"])
            expect_failure(bad, path, contract, needle)

        bad = copy.deepcopy(payload)
        bad["themes"]["other"] = {"label": "Altro", "metrics": ["population"]}
        expect_failure(bad, path, contract, "Appartenenza tema non bidirezionale")

        missing = copy.deepcopy(payload)
        missing["metrics"]["population"]["rows"][0].update(value=None, notApplicable=True)
        missing["metrics"]["population"]["rows"][1].update(value=None, dataUnavailable=True)
        missing["metrics"]["population"]["meta"]["year"] = "2024/25"
        missing["metrics"]["population"]["rows"][1]["componentSeries"] = {"unavailable": {"years": [], "values": []}}
        path.write_text(json.dumps(missing), encoding="utf-8")
        for layer in ("source", "effective"):
            result = validate_semantic_model_contract(path, contract, layer=layer)
            assert result["availability"] == {"availableRows": 0, "missingRows": 1, "notApplicableRows": 1}
            assert result["emptySeries"] == 1

    canonical_path = root / "data" / "site-data.json"
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    real = validate_semantic_model_contract(canonical_path, contract, layer="source")
    assert real["municipalities"] == len(canonical["towns"]), real
    assert real["themes"] == len(canonical["themes"]), real
    assert real["metrics"] == len(canonical["metrics"]), real
    assert real["municipalities"] > 0 and real["themes"] > 0 and real["metrics"] > 0, real
    assert real["sources"] > 0, real
    print(
        "A6.1 source semantic model regression passed: "
        f"{real['municipalities']} Comuni, {real['themes']} temi, {real['metrics']} indicatori, "
        f"{real['periods']} periodi e {real['sources']} fonti derivati dal catalogo canonico."
    )


if __name__ == "__main__":
    main()
