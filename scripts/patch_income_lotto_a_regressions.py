#!/usr/bin/env python3
"""Allinea i test di regressione esistenti alle tranche Redditi e Demografia Lotto A.

- Redditi: la sezione v1.15 include fonti, peso pensioni e contribuenti/maggiorenni.
- Demografia v2: `ageDistribution` usa il POSAS 2026 invece dello snapshot
  statico pre-Lotto A 2025; la validazione puntuale della fonte 2026 resta nel
  test dedicato `test_demography_lotto_a_v5.py`.

Il patch è idempotente e modifica soltanto aspettative storiche esatte.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts' / 'test_composite_indicators.py'

OLD_BASE = '''    assert data["themes"]["economia"]["sections"][0]["metrics"] == [
        "income", "incomeDistribution", "incomeVsInflation",
    ]'''

OLD_V1 = '''    assert data["themes"]["economia"]["sections"][0]["metrics"] == [
        "income", "incomeDistribution", "pensionIncomeShare", "incomeVsInflation",
    ]'''

NEW_INCOME = '''    assert data["themes"]["economia"]["sections"][0]["metrics"] == [
        "income", "incomeDistribution", "incomeSourceProfile", "pensionIncomeShare",
        "taxpayersAdultPopulationRate", "incomeVsInflation",
    ]'''

OLD_AGE = '''        population = population_rows[row["town"]]
        index = population["series"]["years"].index(2025)
        assert sum(part["count"] for part in parts) == population["series"]["values"][index]
        close(row["summaryValue"], snapshot["raw"][row["town"]]["averageAge"], f"Età media/{row['town']}")'''

NEW_AGE = '''        population = population_rows[row["town"]]
        index = population["series"]["years"].index(2026)
        assert age["meta"]["year"] == "2026"
        assert sum(part["count"] for part in parts) == population["series"]["values"][index]
        assert row["summaryValue"] > 0
        assert row.get("seniorAgeDetail", {}).get("age85Plus", {}).get("count", 0) > 0
        assert row.get("ageSexPyramid", {}).get("displayBands")'''


def main() -> None:
    text = TARGET.read_text(encoding='utf-8')

    if NEW_INCOME not in text:
        if OLD_V1 in text:
            text = text.replace(OLD_V1, NEW_INCOME, 1)
        elif OLD_BASE in text:
            text = text.replace(OLD_BASE, NEW_INCOME, 1)
        else:
            raise RuntimeError('Composite economy/redditi expectation anchor not found')

    if NEW_AGE not in text:
        if OLD_AGE not in text:
            raise RuntimeError('Age distribution 2025 regression anchor not found')
        text = text.replace(OLD_AGE, NEW_AGE, 1)

    TARGET.write_text(text, encoding='utf-8')
    print('Composite regression aligned: Redditi completi + ageDistribution POSAS 2026')


if __name__ == '__main__':
    main()
