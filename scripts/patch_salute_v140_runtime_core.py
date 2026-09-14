#!/usr/bin/env python3
"""Stable Salute v1.40 runtime overlay.

The v1.40 release must not depend on optional demographic enrichments. This
wrapper applies only the reviewed core runtime changes required by the 12 new
indicators and leaves sex/age/Toscana enrichments out of the production build
until their source and UI contracts are independently green.
"""
from __future__ import annotations

from patch_salute_v140_runtime import (
    patch_health_comparison_contract,
    patch_health_position_layout,
    patch_visual_grammar,
    remove_redundant_health_deep_dive,
)


def main() -> None:
    patch_health_comparison_contract()
    patch_visual_grammar()
    remove_redundant_health_deep_dive()
    patch_health_position_layout()
    print(
        "Salute v1.40 runtime core: dati, riferimenti Versilia, quote strutture "
        "e schede comunali allineati; arricchimenti demografici non bloccanti"
    )


if __name__ == "__main__":
    main()
