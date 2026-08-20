#!/usr/bin/env python3
"""Validazione minima dell'artifact MEF Redditi Lotto A."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'audit-artifacts' / 'mef-income-lotto-a.json'
EXPECTED = {'Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta', 'Seravezza', 'Stazzema', 'Viareggio'}


def main() -> None:
    data = json.loads(PATH.read_text(encoding='utf-8'))
    assert data['source']['reference'] == '2025 a.i. 2024'
    assert data['source']['published'] == '2026-04-23'
    assert data['checks']['coverage'] == '7/7', data['checks']
    assert set(data['towns']) == EXPECTED
    assert data['parsing']['headerCount'] >= 10
    assert data['checks']['hasTaxpayerColumn'], data['classifiedColumns']['taxpayers']
    assert data['checks']['hasPensionColumns'], data['classifiedColumns']['pension']
    assert data['checks']['hasTotalIncomeColumns'], data['classifiedColumns']['totalIncome']
    assert data['checks']['hasIncomeBands'], data['classifiedColumns']['incomeBands']
    # L'ammontare pensioni è indispensabile per il candidato "peso redditi da pensione".
    assert data['checks']['hasPensionAmountColumn'], data['classifiedColumns']['pension']
    print('Probe MEF Redditi Lotto A OK: schema leggibile, copertura 7/7, pensioni e fasce presenti.')


if __name__ == '__main__':
    main()
