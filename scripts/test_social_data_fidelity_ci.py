#!/usr/bin/env python3
"""Adapter CI del gate di fedelta per il formato numerico compatto delle card.

Il renderer mostra nelle barre alcune unita (es. ogni 1.000) come numero
compatto, mentre l'unita e' dichiarata a livello di card. Il controllo resta
sul valore numerico canonico; cambia soltanto la stringa attesa nello SVG.
"""

from __future__ import annotations

import sys

import test_social_data_fidelity as gate


_base_fmt_value = gate.fmt_value


def rendered_value(value: float, unit: str, signed: bool = False) -> str:
    if not signed and unit in {"per1000", "per10k", "minutes"}:
        return gate.fmt_it(value, 1)
    return _base_fmt_value(value, unit, signed)


gate.fmt_value = rendered_value


if __name__ == "__main__":
    sys.exit(gate.main())
