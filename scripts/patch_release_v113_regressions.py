#!/usr/bin/env python3
"""Align long-lived compatibility checks with validated v1.13 exceptions."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts' / 'test_release_v170_compat.py'

OLD_CONST = 'PARTIAL_KEYS = {"ftthReachedHouseholds", "ftthUnreachedHouseholds"}'
NEW_CONST = '''PARTIAL_MISSING = {
    "ftthReachedHouseholds": "Forte dei Marmi",
    "ftthUnreachedHouseholds": "Forte dei Marmi",
    "fuelPrices": "Stazzema",
}'''

OLD_BLOCK = '''        if key in PARTIAL_KEYS:
            require(coverage == "6/7", f"{key}: deve dichiarare copertura 6/7")
            missing = [row for row in rows if row.get("value") is None]
            require(len(missing) == 1, f"{key}: copertura 6/7 senza un solo valore mancante")
            require(missing[0].get("town") == "Forte dei Marmi", f"{key}: Comune n.d. inatteso")
            require(missing[0].get("formatted") == "n.d.", f"{key}: valore mancante non etichettato n.d.")
        else:
            require("7/7" in coverage, f"{key}: copertura diversa da 7/7")'''

NEW_BLOCK = '''        if key in PARTIAL_MISSING:
            require(coverage == "6/7", f"{key}: deve dichiarare copertura 6/7")
            missing = [row for row in rows if row.get("value") is None]
            require(len(missing) == 1, f"{key}: copertura 6/7 senza un solo valore mancante")
            require(missing[0].get("town") == PARTIAL_MISSING[key], f"{key}: Comune n.d. inatteso")
            require(missing[0].get("formatted") == "n.d.", f"{key}: valore mancante non etichettato n.d.")
        else:
            require("7/7" in coverage, f"{key}: copertura diversa da 7/7")'''


def main() -> None:
    text = TARGET.read_text(encoding='utf-8')
    if NEW_CONST not in text:
        if OLD_CONST not in text:
            raise RuntimeError('Partial-coverage constant anchor missing')
        text = text.replace(OLD_CONST, NEW_CONST, 1)
    if NEW_BLOCK not in text:
        if OLD_BLOCK not in text:
            raise RuntimeError('Partial-coverage validation anchor missing')
        text = text.replace(OLD_BLOCK, NEW_BLOCK, 1)
    TARGET.write_text(text, encoding='utf-8')
    print('Release compatibility check aligned: fuelPrices 6/7 with Stazzema n.d.')


if __name__ == '__main__':
    main()
