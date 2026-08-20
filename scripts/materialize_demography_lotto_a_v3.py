#!/usr/bin/env python3
"""Disambiguazione finale delle intestazioni P02 storiche.

Nel P02 2019 il 31 dicembre compare per popolazione totale, residenti in
famiglia e residenti in convivenza. Per il denominatore demografico usiamo
esclusivamente la popolazione totale generale.
"""
from __future__ import annotations

import materialize_demography_lotto_a as base
import materialize_demography_lotto_a_v2 as compat

_original_field = compat.field


def field(rec: dict[str, str], *tokens: str, exclude: tuple[str, ...] = ()) -> str:
    lowered = {str(token).lower() for token in tokens}
    if 'popolazione' in lowered and 'dicembre' in lowered:
        exclude = tuple(dict.fromkeys((*exclude, 'famiglia', 'convivenza')))
    return _original_field(rec, *tokens, exclude=exclude)


compat.field = field
base.read_csv_from_zip = compat.read_csv_from_zip
base.p2_snapshot = compat.p2_snapshot

if __name__ == '__main__':
    base.main()
