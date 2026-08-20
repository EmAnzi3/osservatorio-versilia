#!/usr/bin/env python3
"""Allinea i test storici dei compositi alla Demografia Lotto A v2.

`ageDistribution` passa dal 2025 al POSAS 2026. Il controllo precedente
confrontava conteggi ed età media contro lo snapshot statico pre-Lotto A 2025;
la validazione fonte/età media 2026 è ora coperta da `test_demography_lotto_a_v5.py`.
Questo patch mantiene nel test compositi il vincolo di esaustività e lo allinea
alla popolazione canonica 2026.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts' / 'test_composite_indicators.py'

OLD = '''        population = population_rows[row["town"]]
        index = population["series"]["years"].index(2025)
        assert sum(part["count"] for part in parts) == population["series"]["values"][index]
        close(row["summaryValue"], snapshot["raw"][row["town"]]["averageAge"], f"Età media/{row['town']}")'''

NEW = '''        population = population_rows[row["town"]]
        index = population["series"]["years"].index(2026)
        assert age["meta"]["year"] == "2026"
        assert sum(part["count"] for part in parts) == population["series"]["values"][index]
        assert row["summaryValue"] > 0
        assert row.get("seniorAgeDetail", {}).get("age85Plus", {}).get("count", 0) > 0
        assert row.get("ageSexPyramid", {}).get("displayBands")'''


def main() -> None:
    text = TARGET.read_text(encoding='utf-8')
    if NEW in text:
        print('Composite demography regression already aligned with POSAS 2026')
        return
    if OLD not in text:
        raise RuntimeError('Age distribution 2025 regression anchor not found')
    TARGET.write_text(text.replace(OLD, NEW, 1), encoding='utf-8')
    print('Composite demography regression aligned: ageDistribution now validated on POSAS 2026')


if __name__ == '__main__':
    main()
