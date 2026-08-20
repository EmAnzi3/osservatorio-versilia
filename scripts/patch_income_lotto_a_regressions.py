#!/usr/bin/env python3
"""Allinea i test di regressione esistenti alla tranche Redditi Lotto A.

La sezione Redditi di Economia è deliberatamente estesa con
`pensionIncomeShare` subito dopo `incomeDistribution`; il test compositi della
release precedente conserva invece un elenco esatto pre-v1.15. Questo patch è
idempotente e modifica soltanto quella aspettativa storica.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts' / 'test_composite_indicators.py'

OLD = '''    assert data["themes"]["economia"]["sections"][0]["metrics"] == [
        "income", "incomeDistribution", "incomeVsInflation",
    ]'''

NEW = '''    assert data["themes"]["economia"]["sections"][0]["metrics"] == [
        "income", "incomeDistribution", "pensionIncomeShare", "incomeVsInflation",
    ]'''


def main() -> None:
    text = TARGET.read_text(encoding='utf-8')
    if NEW in text:
        print('Composite regression already aligned with v1.15 income tranche')
        return
    if OLD not in text:
        raise RuntimeError('Composite economy/redditi expectation anchor not found')
    TARGET.write_text(text.replace(OLD, NEW, 1), encoding='utf-8')
    print('Composite regression aligned: pensionIncomeShare inserted after incomeDistribution')


if __name__ == '__main__':
    main()
