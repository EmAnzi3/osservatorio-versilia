#!/usr/bin/env python3
"""Allinea i test di regressione esistenti alla tranche Redditi Lotto A completa.

La sezione Redditi della v1.15 contiene, oltre ai tre indicatori preesistenti,
un composito per fonte, il peso pensioni e il rapporto contribuenti/maggiorenni.
Il patch è idempotente e modifica soltanto l'aspettativa storica esatta.
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

NEW = '''    assert data["themes"]["economia"]["sections"][0]["metrics"] == [
        "income", "incomeDistribution", "incomeSourceProfile", "pensionIncomeShare",
        "taxpayersAdultPopulationRate", "incomeVsInflation",
    ]'''


def main() -> None:
    text = TARGET.read_text(encoding='utf-8')
    if NEW in text:
        print('Composite regression already aligned with complete v1.15 income tranche')
        return
    if OLD_V1 in text:
        text = text.replace(OLD_V1, NEW, 1)
    elif OLD_BASE in text:
        text = text.replace(OLD_BASE, NEW, 1)
    else:
        raise RuntimeError('Composite economy/redditi expectation anchor not found')
    TARGET.write_text(text, encoding='utf-8')
    print('Composite regression aligned: income sources, pension share and taxpayers/adults enabled')


if __name__ == '__main__':
    main()
