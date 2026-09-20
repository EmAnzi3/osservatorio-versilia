#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import enrichment_audit_matrix_core as audit
import materialize_a3_5_official_companions as enrichment

SITE = ROOT / "data" / "site-data.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def strip_a3(value):
    if isinstance(value, dict):
        return {k: strip_a3(v) for k, v in value.items() if not str(k).startswith("a3")}
    if isinstance(value, list):
        return [strip_a3(item) for item in value]
    return value


def test_official_companions() -> None:
    original = load(SITE)
    site = copy.deepcopy(original)
    before = strip_a3(site)

    summary = enrichment.apply_enrichment(
        site,
        load(enrichment.ISTAT_2024_PATH),
        load(enrichment.LIA_2023_PATH),
        load(enrichment.AGCOM_PATH),
        load(enrichment.RGS_ADMIN_PATH),
        load(enrichment.RGS_TRAINING_PATH),
    )
    assert summary == {"istatPairs": 8, "agcomPairs": 10, "rgsPairs": 3, "pairsAcquired": 21}, summary
    assert strip_a3(site) == before, "Il lotto 8 non deve modificare il payload pubblico preesistente"

    expected = {
        ("femaleEmploymentRate", "sesso"),
        ("femaleEmploymentRate", "eta"),
        ("femaleEmploymentRate", "categorie_specifiche"),
        ("maleEmploymentRate", "sesso"),
        ("maleEmploymentRate", "eta"),
        ("maleEmploymentRate", "categorie_specifiche"),
        ("employmentGenderGap", "sesso"),
        ("employmentGenderGap", "eta"),
        ("ftthCoverageDesi", "assoluto_normalizzato"),
        ("ftthCoverageDesi", "numeratore_denominatore"),
        ("ftthCoverageDesi", "categorie_specifiche"),
        ("ftthCoverage20m", "assoluto_normalizzato"),
        ("ftthCoverage20m", "numeratore_denominatore"),
        ("ftthCoverage20m", "categorie_specifiche"),
        ("ftthReachedHouseholds", "assoluto_normalizzato"),
        ("ftthReachedHouseholds", "categorie_specifiche"),
        ("ftthUnreachedHouseholds", "assoluto_normalizzato"),
        ("ftthUnreachedHouseholds", "categorie_specifiche"),
        ("municipalStaffTurnover", "assoluto_normalizzato"),
        ("municipalStaffTurnover", "categorie_specifiche"),
        ("municipalStaffTraining", "sesso"),
    }
    assert len(expected) == 21

    for metric_id, dimension in sorted(expected):
        evidence = audit.acquired_evidence(site["metrics"][metric_id], dimension)
        assert evidence is not None, (metric_id, dimension, evidence)
        assert evidence.startswith("rows."), (metric_id, dimension, evidence)

    # Evita acquisizioni accidentali fuori dal perimetro esplicito del lotto.
    assert audit.acquired_evidence(site["metrics"]["employmentGenderGap"], "categorie_specifiche") is None
    assert audit.acquired_evidence(site["metrics"]["ftthReachedHouseholds"], "numeratore_denominatore") is None
    assert audit.acquired_evidence(site["metrics"]["ftthUnreachedHouseholds"], "numeratore_denominatore") is None

    print(
        "A3.5 lotto 8 regression passed: 21 coppie da snapshot Istat/AGCOM/RGS già versionati "
        "(8 Istat, 10 AGCOM, 3 RGS), payload pubblico invariato."
    )


if __name__ == "__main__":
    test_official_companions()
