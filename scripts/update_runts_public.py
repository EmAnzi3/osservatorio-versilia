"""Publish a validated current RUNTS count snapshot with dated Istat denominators.

The normalized snapshot records source hash and counts, without personal records.
No reconstruction of historical legal seats or comparison with legacy rates.
"""
import argparse
import copy
import json
import math
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://servizi.lavoro.gov.it/runts/it-it/Lista-enti'
SNAPSHOT = 'data/source-snapshots/runts-public-2026-10-11.json'


def apply(data, snapshot, snapshot_path=SNAPSHOT):
    reference = date.fromisoformat(snapshot['referenceDate'])
    if reference > date.today() or snapshot.get('sourceUrl') != SOURCE:
        raise ValueError('RUNTS source/reference invalid')
    if not re.fullmatch('[0-9a-f]{64}', snapshot.get('sourceSha256', '')):
        raise ValueError('RUNTS source hash missing')
    if snapshot.get('sourcePublicationDate') != reference.isoformat():
        raise ValueError('RUNTS publication date mismatch')
    towns = {t['code']: t['name'] for t in data['towns']}
    records = snapshot['rows']
    if len(records) != len(towns) or {r['code']: r['town'] for r in records} != towns:
        raise ValueError('RUNTS municipal identity/coverage mismatch')
    pop = data['metrics']['population']
    population = {r['code']: r['value'] for r in pop['rows']}
    rows = {r['code']: r for r in records}
    for r in records:
        if type(r['count']) is not int or r['count'] < 0:
            raise ValueError('RUNTS count invalid')
        if type(r['population']) is not int or r['population'] <= 0 or r['population'] != population[r['code']]:
            raise ValueError('RUNTS population mismatch')
        if r['populationReference'] != str(pop['meta']['year']) + '-01-01':
            raise ValueError('RUNTS population reference mismatch')
        if not math.isclose(r['per1000'], r['count'] / r['population'] * 1000, abs_tol=1e-12):
            raise ValueError('RUNTS rate mismatch')
    count = sum(r['count'] for r in records)
    denominator = sum(r['population'] for r in records)
    if snapshot['versilia'] != {'count': count, 'population': denominator}:
        raise ValueError('RUNTS aggregate mismatch')
    months = ('gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre')
    reference_label = f'{reference.day} {months[reference.month-1]} {reference.year}'
    population_label = f'1° gennaio {pop["meta"]["year"]}'
    population_reference = records[0]['populationReference']
    result = copy.deepcopy(data)
    metric = result['metrics']['thirdSector']
    metric['meta'].update(year=reference.isoformat(), description=f'Enti con sede legale nel Comune iscritti al RUNTS alla data {reference_label}, ogni 1.000 residenti al {population_label}.')
    metric['sourceUrl'] = SOURCE
    for row in metric['rows']:
        r = rows[row['code']]
        row.update(value=r['per1000'], benchmarkValue=r['per1000'],
                   formatted=f"{r['per1000']:.2f}".replace('.', ',') + ' ogni 1.000',
                   registeredEntities=r['count'], residentPopulation=r['population'],
                   populationReference=r['populationReference'], series=None)
    metric['aggregate'] = dict(value=count / denominator * 1000, label='Densità Versilia',
        note=f'{count} enti con sede legale nei sette Comuni; {denominator:,} residenti al {population_label}.'.replace(',', '.'))
    metric['method'] = dict(type='Elaborazione Osservatorio su RUNTS e Istat',
        formula=f'enti RUNTS con sede legale nel Comune / residenti Istat al {population_label} × 1.000',
        caveat=f'Fotografia del registro alla data {reference_label}. Conteggio per codice fiscale univoco e sede legale, in tutte le sezioni. La sede non misura attività o servizi effettivamente svolti nel territorio. Popolazione al {population_label}; nessuna variazione calcolata rispetto ai tassi 2025 non riconciliati.',
        coverage='7/7', sourceSnapshot=snapshot_path, referenceDate=reference.isoformat(), populationReference=population_reference)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site-data', type=Path, default=ROOT/'data/site-data.json')
    parser.add_argument('--snapshot', type=Path, default=ROOT/SNAPSHOT)
    args = parser.parse_args()
    snapshot_path = args.snapshot.resolve().relative_to(ROOT).as_posix()
    data = apply(json.loads(args.site_data.read_text()), json.loads(args.snapshot.read_text()), snapshot_path)
    args.site_data.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
