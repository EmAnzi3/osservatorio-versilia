#!/usr/bin/env python3
"""Correzione POSAS: esclude la riga aggregata Età=999.

Gli archivi Istat POSAS provinciali includono, oltre alle età singole, una riga
999 che rappresenta il totale comunale. Questa riga non è una classe di età e
non deve entrare nelle somme 0–14 / 15–64 / 65+ né nel dettaglio età×sesso.
"""
from __future__ import annotations

import materialize_demography_lotto_a as base
import materialize_demography_lotto_a_v3  # applica già le compatibilità P02
import patch_demography_lotto_a_review as review


def age_bands(records: list[dict[str, str]]) -> dict:
    counts = {'0-14': 0, '15-64': 0, '65+': 0, '80+': 0}
    total = 0
    by_age_sex = []
    total_row_value = None
    for r in records:
        age = base.age_number(r['Età'])
        men = int(base.num(r['Totale maschi']))
        women = int(base.num(r['Totale femmine']))
        value = int(base.num(r['Totale']))
        if men + women != value:
            raise RuntimeError(f'Totale età incoerente: {r}')
        if age == 999:
            if total_row_value is not None:
                raise RuntimeError('Più di una riga POSAS Età=999')
            total_row_value = value
            continue
        if age < 0 or age > 120:
            raise RuntimeError(f'Età POSAS inattesa: {age}')
        total += value
        if age <= 14:
            counts['0-14'] += value
        elif age <= 64:
            counts['15-64'] += value
        else:
            counts['65+'] += value
        if age >= 80:
            counts['80+'] += value
        by_age_sex.append({'age': age, 'men': men, 'women': women, 'total': value})
    if total_row_value is None:
        raise RuntimeError('Riga totale POSAS Età=999 assente')
    if total != total_row_value:
        raise RuntimeError(f'Somma età {total} diversa dal totale POSAS {total_row_value}')
    if sum(counts[k] for k in ('0-14', '15-64', '65+')) != total:
        raise RuntimeError('Classi di età non esaustive')
    return {'total': total, 'counts': counts, 'ageSex': by_age_sex}


base.age_bands = age_bands

if __name__ == '__main__':
    base.main()
    review.main()
