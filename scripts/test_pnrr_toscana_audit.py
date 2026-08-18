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


def strict_feed():
    projects = {}
    subjects = []
    for name, code in TOWNS:
        projects[code] = [
            {
                "id_progetto": f"{code}-A",
                "cod_istat": code,
                "finanziato_pnrr": "50.000,00",
                "misura_pnrr_estesa": "M1",
                "fase_avanzamento": "5. conclusione",
            },
            {
                "id_progetto": f"{code}-B",
                "cod_istat": code,
                "finanziato_pnrr": "50000",
                "misura_pnrr_estesa": "M2",
                "fase_avanzamento": "4. esecuzione",
            },
        ]
        subjects.extend([
            {"id_progetto": f"{code}-A", "ruolo": "Soggetto attuatore", "soggetto": f"Comune di {name}"},
            {"id_progetto": f"{code}-B", "ruolo": "Soggetto Attuatore", "soggetto": f"COMUNE DI {name.upper()}"},
        ])
    return projects, subjects


def test_helpers():
    assert module.parse_number("1.234.567,89") == 1234567.89
    assert module.parse_number("€ 50.000,00") == 50000
    assert module.parse_number("SI") is None
    assert module.town_subject_match("Comune di Forte dei Marmi", "Forte dei Marmi")
    assert not module.town_subject_match("Comune di Camaiore", "Massarosa")
    assert module.is_concluded({"fase_avanzamento": "5. conclusione"})


def test_strict_match():
    projects, subjects = strict_feed()
    original_all = module.all_records
    original_load = module.load_town_projects
    try:
        module.all_records = lambda resource_id, filters=None: (
            (subjects, ["id_progetto", "ruolo", "soggetto"])
            if resource_id == module.SUBJECT_RESOURCE
            else ([], [])
        )
        module.load_town_projects = lambda code: (projects[code], code)
        result = module.audit(fixture_data())
    finally:
        module.all_records = original_all
        module.load_town_projects = original_load

    assert result["strictSubjectScopeAvailable"] is True
    assert result["verdict"] == "match"
    assert result["eligibleForAutomaticVerification"] is True
    assert len(result["perTown"]) == 7
    assert all(item["selectedProjects"] == 2 for item in result["perTown"].values())
    assert all(item["match"] is True for item in result["perTown"].values())


def test_no_role_is_not_comparable():
    projects, subjects = strict_feed()
    subjects = [{"id_progetto": row["id_progetto"], "soggetto": row["soggetto"]} for row in subjects]
    for code, rows in projects.items():
        town = next(name for name, town_code in TOWNS if town_code == code)
        for row in rows:
            row["soggetto_richiedente"] = f"Comune di {town}"

    original_all = module.all_records
    original_load = module.load_town_projects
    try:
        module.all_records = lambda resource_id, filters=None: (
            (subjects, ["id_progetto", "soggetto"])
            if resource_id == module.SUBJECT_RESOURCE
            else ([], [])
        )
        module.load_town_projects = lambda code: (projects[code], code)
        result = module.audit(fixture_data())
    finally:
        module.all_records = original_all
        module.load_town_projects = original_load

    assert result["strictSubjectScopeAvailable"] is False
    assert result["verdict"] == "not_comparable"
    assert result["eligibleForAutomaticVerification"] is False


if __name__ == "__main__":
    test_helpers()
    test_strict_match()
    test_no_role_is_not_comparable()
    print("OK: audit PNRR Regione Toscana")
