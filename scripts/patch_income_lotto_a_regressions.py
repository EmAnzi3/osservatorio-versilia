#!/usr/bin/env python3
"""Allinea le regressioni esistenti alle tranche Redditi e Demografia Lotto A.

- Redditi: la sezione include fonti, peso pensioni e contribuenti/maggiorenni.
- Demografia v2: `ageDistribution` usa il POSAS 2026 e otto fasce esaustive,
  con 80–84 e 85+ come componenti normali della distribuzione.

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

OLD_AGE_COUNT = '''        assert len(parts) == 7
        close(sum(part["value"] for part in parts), 100.0, f"Età/{row['town']} somma")'''
NEW_AGE_COUNT = '''        assert len(parts) == 8
        assert [part["label"] for part in parts][-2:] == ["80–84 anni", "85 anni e oltre"]
        close(sum(part["value"] for part in parts), 100.0, f"Età/{row['town']} somma")'''

OLD_AGE = '''        population = population_rows[row["town"]]
        index = population["series"]["years"].index(2025)
        assert sum(part["count"] for part in parts) == population["series"]["values"][index]
        close(row["summaryValue"], snapshot["raw"][row["town"]]["averageAge"], f"Età media/{row['town']}")'''

NEW_AGE = '''        population = population_rows[row["town"]]
        index = population["series"]["years"].index(2026)
        assert age["meta"]["year"] == "2026"
        assert sum(part["count"] for part in parts) == population["series"]["values"][index]
        assert row["summaryValue"] > 0
        assert "seniorAgeDetail" not in row and "age85PlusDetail" not in row
        assert row.get("ageSexPyramid", {}).get("displayBands")'''

OLD_BROWSER = '''        tooltip_checks(page, base, "demografia", "ageDistribution", 7, 7)'''
NEW_BROWSER = '''        tooltip_checks(page, base, "demografia", "ageDistribution", 7, 8)'''


def main() -> None:
    text = TARGET.read_text(encoding='utf-8')

    if NEW_INCOME not in text:
        if OLD_V1 in text:
            text = text.replace(OLD_V1, NEW_INCOME, 1)
        elif OLD_BASE in text:
            text = text.replace(OLD_BASE, NEW_INCOME, 1)
        else:
            raise RuntimeError('Composite economy/redditi expectation anchor not found')

    if NEW_AGE_COUNT not in text:
        if OLD_AGE_COUNT not in text:
            raise RuntimeError('Age distribution 7-band expectation anchor not found')
        text = text.replace(OLD_AGE_COUNT, NEW_AGE_COUNT, 1)

    if NEW_AGE not in text:
        if OLD_AGE not in text:
            raise RuntimeError('Age distribution 2025 regression anchor not found')
        text = text.replace(OLD_AGE, NEW_AGE, 1)

    if NEW_BROWSER not in text:
        if OLD_BROWSER not in text:
            raise RuntimeError('Age distribution browser part-count anchor not found')
        text = text.replace(OLD_BROWSER, NEW_BROWSER, 1)

    TARGET.write_text(text, encoding='utf-8')
    print('Composite regression aligned: Redditi completi + ageDistribution POSAS 2026 a 8 fasce non sovrapposte.')


if __name__ == '__main__':
    main()
