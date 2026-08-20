#!/usr/bin/env python3
"""Align long-lived compatibility checks with validated v1.13 changes."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPAT = ROOT / 'scripts' / 'test_release_v170_compat.py'
HISTORY = ROOT / 'scripts' / 'test_history_v180.py'

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
            if key == "fuelPrices":
                require(missing[0].get("stationCount") == 0, "fuelPrices: Stazzema non deve avere impianti attivi")
                parts = missing[0].get("parts") or []
                require(len(parts) == 2 and all(part.get("value") is None for part in parts),
                        "fuelPrices: benzina e gasolio di Stazzema devono restare null/n.d., mai zero")
            else:
                require(missing[0].get("formatted") == "n.d.", f"{key}: valore mancante non etichettato n.d.")
        else:
            require("7/7" in coverage, f"{key}: copertura diversa da 7/7")'''

OLD_HISTORY_VERSION = 'require(DATA["version"] == "v1.12.0", "Versione dati v1.12.0 non applicata")'
NEW_HISTORY_VERSION = 'require(DATA["version"] == "v1.13.0", "Versione dati v1.13.0 non applicata")'
OLD_HISTORY_DATE = 'require(DATA["updated"] == "15 agosto 2026", "Data di aggiornamento v1.12.0 inattesa")'
NEW_HISTORY_DATE = 'require(DATA["updated"] == "16 agosto 2026", "Data di aggiornamento v1.13.0 inattesa")'
HISTORY_VERSION_RE = re.compile(
    r'require\(DATA\["version"\] == "v(\d+)\.(\d+)\.(\d+)", '
    r'"Versione dati v\d+\.\d+\.\d+ non applicata"\)'
)


def patch_compat() -> None:
    text = COMPAT.read_text(encoding='utf-8')
    if NEW_CONST not in text:
        if OLD_CONST not in text:
            raise RuntimeError('Partial-coverage constant anchor missing')
        text = text.replace(OLD_CONST, NEW_CONST, 1)
    if NEW_BLOCK not in text:
        if OLD_BLOCK not in text:
            raise RuntimeError('Partial-coverage validation anchor missing')
        text = text.replace(OLD_BLOCK, NEW_BLOCK, 1)
    COMPAT.write_text(text, encoding='utf-8')


def patch_history() -> None:
    text = HISTORY.read_text(encoding='utf-8')
    match = HISTORY_VERSION_RE.search(text)
    if not match:
        raise RuntimeError('History version anchor missing')
    version = tuple(int(part) for part in match.groups())
    if version < (1, 13, 0):
        if OLD_HISTORY_VERSION not in text:
            raise RuntimeError('History version anchor missing')
        text = text.replace(OLD_HISTORY_VERSION, NEW_HISTORY_VERSION, 1)
        version = (1, 13, 0)
    if version == (1, 13, 0) and NEW_HISTORY_VERSION not in text:
        raise RuntimeError('History v1.13 version assertion is inconsistent')
    if version == (1, 13, 0) and NEW_HISTORY_DATE not in text:
        if OLD_HISTORY_DATE not in text:
            raise RuntimeError('History update-date anchor missing')
        text = text.replace(OLD_HISTORY_DATE, NEW_HISTORY_DATE, 1)
    HISTORY.write_text(text, encoding='utf-8')


def main() -> None:
    patch_compat()
    patch_history()
    print('Release compatibility checks aligned with v1.13 metadata and validated fuel 6/7 coverage')


if __name__ == '__main__':
    main()
