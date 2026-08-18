#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("pnrr_toscana_audit.py")
spec = importlib.util.spec_from_file_location("pnrr_toscana_audit", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)

TOWNS = [
    ("Camaiore", "046005"),
    ("Forte dei Marmi", "046013"),
    ("Massarosa", "046018"),
    ("Pietrasanta", "046024"),
    ("Seravezza", "046028"),
    ("Stazzema", "046030"),
    ("Viareggio", "046033"),
]


def fixture_data():
    def rows(value):
        return [{"town": name, "code": code, "value": value} for name, code in TOWNS]

    return {
        "towns": [{"name": name, "code": code} for name, code in TOWNS],
        "metrics": {
            "population": {"rows": rows(1000)},
            "pnrrFunding": {"rows": rows(100)},
            "pnrrConcluded": {"rows": rows(50)},
        },
    }


def fixture_records():
    records = []
    for name, code in TOWNS:
        for suffix, phase in (("A", "5. conclusione"), ("B", "4. esecuzione")):
            records.append({
                "id_progetto": f"{code}-{suffix}",
                "cup": f"CUP-{code}-{suffix}",
                "area": "PNRR",
                "misura_pnrr_estesa": "M1",
                "soggetto_attuatore": f"Comune di {name}",
                "cf_soggetto_attuatore": f"CF-{code}",
                "importo_finanziato_pnrr": "50.000,00",
                "fase_avanzamento_da_regis": phase,
                "fase_avanzamento_da_monitoraggio_progetti": phase,
                "fase_regis": phase,
                "data_fine_effettiva_chiusura_intervento": "2026-01-31" if suffix == "A" else "",
                "data_elaborazione": "2026-08-11",
            })
    return records


def test_helpers():
    assert module.parse_number("1.234.567,89") == 1234567.89
    assert module.parse_number("€ 50.000,00") == 50000
    assert module.parse_number("NULL") is None
    assert module.town_subject_match("Comune di Forte dei Marmi", "Forte dei Marmi")
    assert not module.town_subject_match("Comune di Camaiore", "Massarosa")
    assert module.concluded_from({"fase_avanzamento_da_regis": "5. conclusione"}, "fase_avanzamento_da_regis")


def test_exact_match():
    result = module.audit_records(fixture_data(), fixture_records())
    assert result["verdict"] == "match"
    assert result["eligibleForAutomaticVerification"] is True
    assert result["fundingMatch7of7"] is True
    assert "fase_avanzamento_da_regis" in result["conclusionDefinitionMatches"]
    assert len(result["perTown"]) == 7
    assert all(item["selectedProjects"] == 2 for item in result["perTown"].values())


def test_dedupe_project():
    records = fixture_records()
    records.append(dict(records[0]))
    result = module.audit_records(fixture_data(), records)
    assert result["verdict"] == "match"
    assert result["perTown"]["046005"]["selectedProjects"] == 2


def test_new_snapshot_is_not_auto_published():
    records = fixture_records()
    records[0]["importo_finanziato_pnrr"] = "75.000,00"
    result = module.audit_records(fixture_data(), records)
    assert result["verdict"] == "different_current_snapshot"
    assert result["eligibleForAutomaticVerification"] is False
    assert result["fundingMatch7of7"] is False


if __name__ == "__main__":
    test_helpers()
    test_exact_match()
    test_dedupe_project()
    test_new_snapshot_is_not_auto_published()
    print("OK: audit PNRR Regione Toscana")
