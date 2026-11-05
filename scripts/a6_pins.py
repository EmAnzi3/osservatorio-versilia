"""Registro unico delle impronte congelate degli adattatori A6.

Gli adattatori non contengono più impronte SHA-256 scritte nel codice: ogni
impronta è un `Pin`, il cui valore viene letto da `ci/a6-source-pins.json`.

- In modalità normale un `Pin` si comporta esattamente come la stringa
  registrata: un file cambiato senza un aggiornamento verificato continua a
  essere rifiutato dall'adattatore, con lo stesso codice di errore di prima.
- In modalità ri-registrazione (`A6_REPIN=1`, usata solo da
  `scripts/a6_repin.py` dopo un aggiornamento dati verificato) ogni confronto
  con un `Pin` registra il valore osservato e risulta uguale; lo script mostra
  poi quali impronte sono cambiate e consente solo quelle dichiarate.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "ci" / "a6-source-pins.json"

_PINS: dict[str, str] | None = None
RECORDED: dict[str, str] = {}


def pins() -> dict[str, str]:
    global _PINS
    if _PINS is None:
        _PINS = json.loads(REGISTRY.read_text(encoding="utf-8"))["pins"]
    return _PINS


def repinning() -> bool:
    return os.environ.get("A6_REPIN") == "1"


class Pin(str):
    """Impronta registrata; confrontabile come una stringa."""

    name: str

    def __new__(cls, name: str) -> "Pin":
        registry = pins()
        if name not in registry:
            raise KeyError(f"impronta A6 non registrata: {name}")
        pin = super().__new__(cls, registry[name])
        pin.name = name
        return pin

    def __eq__(self, other: Any) -> bool:  # type: ignore[override]
        if repinning() and isinstance(other, str) and not isinstance(other, Pin):
            RECORDED[self.name] = str(other)
            return True
        return str.__eq__(self, other)

    def __ne__(self, other: Any) -> bool:  # type: ignore[override]
        return not self.__eq__(other)

    __hash__ = str.__hash__
