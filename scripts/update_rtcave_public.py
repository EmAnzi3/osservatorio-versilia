#!/usr/bin/env python3
"""Aggiorna la fotografia RTCave e la sola scheda «Siti censiti in RTCave».

Da eseguire esplicitamente, mai durante una build. Produzione estrattiva e PRC
restano quelli dello snapshot v1.28: questo script tocca soltanto `rtcave`.
Tutte le verifiche si chiudono prima di scrivere qualsiasi file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

from materialize_attivita_estrattive_v128 import (
    RTCAVE_URL,
    VERSILIA_CODES,
    build_sites_metric,
)

ROOT = Path(__file__).resolve().parents[1]
SITE = 'data/site-data.json'
SNAPSHOT = 'data/source-snapshots/attivita-estrattive-v128.json'
STATE = 'data/source-monitor-state.json'
REGISTRY = 'data/source-registry.json'
REQUIRED_FIELDS = {
    'cod_comprensorio', 'cod_istat', 'codice_giacimento', 'codice_rt', 'id_caratteristica', 'id_cava',
    'id_comprensorio', 'id_comune', 'id_giacimento', 'id_stato', 'id_tipo_prestito', 'id_tipo_prima_prod',
    'id_tipologia', 'lat', 'localita', 'lon', 'nome_cava', 'nome_comprensorio', 'nome_comune', 'nome_giacimento',
    'nome_provincia', 'sigla_provincia', 'stato', 'tipo_produzione', 'tipologia',
}
# Categorie già riviste: un valore nuovo richiede una revisione esplicita.
REVIEWED = {
    'stato': {'Attiva', 'Inattiva', 'Sospesa', 'Scaduta', 'In ripristino', 'Chiusa', None},
    'tipologia': {'Cava Ordinaria', 'Opere di ripristino', 'Piano di recupero'},
    'tipo_produzione': {'ORNAMENTALE', 'INDUSTRIALE', 'COSTRUZIONE'},
}
MONTHS = ('gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre',
          'ottobre', 'novembre', 'dicembre')


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def save(path, value):
    (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def italian_date(moment: datetime) -> str:
    return f'{moment.day} {MONTHS[moment.month - 1]} {moment.year}'


def records(raw: bytes):
    payload = json.loads(raw.decode('utf-8'))
    rows = payload.get('data') or []
    if payload.get('ok') is not True or not rows:
        raise ValueError('RTCave: risposta non valida')
    if any(set(r) != REQUIRED_FIELDS for r in rows):
        raise ValueError('RTCave: schema cambiato')
    codes = [str(r.get('codice_rt') or '') for r in rows]
    ids = [r.get('id_cava') for r in rows]
    if not all(codes) or len(set(codes)) != len(rows) or len(set(ids)) != len(rows):
        raise ValueError('RTCave: identificativi mancanti o duplicati')
    selected = [r for r in rows if str(r.get('cod_istat') or '').zfill(6) in VERSILIA_CODES]
    for r in selected:
        for field, allowed in REVIEWED.items():
            if r.get(field) not in allowed:
                raise ValueError(f'RTCave: categoria non rivista {field}={r.get(field)!r}')
    return rows, selected


def update(raw: bytes, acquired_at: str):
    moment = datetime.fromisoformat(acquired_at)
    label = italian_date(moment)
    period = moment.date().isoformat()
    all_rows, selected = records(raw)
    sha = hashlib.sha256(raw).hexdigest()

    site, snapshot, state, registry = map(load, (SITE, SNAPSHOT, STATE, REGISTRY))
    old = {r['id_cava']: r for r in snapshot['rtcave']['records']}
    new = {r['id_cava']: r for r in selected}
    changes = [
        dict(id_cava=i, codice_rt=new[i]['codice_rt'], town=new[i]['nome_comune'], nome_cava=new[i]['nome_cava'],
             field=f, published=old[i].get(f), observed=new[i].get(f))
        for i in sorted(set(old) & set(new)) for f in sorted(REQUIRED_FIELDS) if old[i].get(f) != new[i].get(f)
    ]
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))

    current = site['metrics']['extractiveSites']
    rebuilt = build_sites_metric(site, snapshot['rtcave']['records'])
    rebuilt['meta']['year'] = current['meta']['year']
    if rebuilt != current:
        raise ValueError('RTCave: la scheda pubblicata non coincide con lo snapshot attuale')
    metric = build_sites_metric(site, selected)
    metric['meta']['year'] = label
    site['metrics']['extractiveSites'] = metric

    snapshot['rtcave'].update(
        sha256=sha, retrievedAt=acquired_at, regionalRecordCount=len(all_rows),
        regionalUniqueCodiceRt=len({r['codice_rt'] for r in all_rows}),
        regionalUniqueIdCava=len({r['id_cava'] for r in all_rows}),
        versiliaRecordCount=len(selected), rawFieldNames=sorted(REQUIRED_FIELDS), records=selected,
    )
    snapshot['releaseChecks'].update(expectedRtcaveRegionalRecords=len(all_rows),
                                     expectedRtcaveVersiliaRecords=len(selected))

    item = state['metrics']['extractiveSites']
    evidence = item.get('verificationEvidence') or {}
    item.update(publishedPeriod=label, observedLatestPeriod=period, periodVerifiedAt=acquired_at, status='current')
    item.pop('releaseEvidence', None)
    item['verificationEvidence'] = dict(evidence, verdict='match', referenceDate=period, contentSha256=sha,
                                        valuesMatchPublished=True)
    policy = registry['sourceProbePolicies'][RTCAVE_URL]
    policy['releaseCheck'] = (f'Confrontare i record RTCave per identificativo e contenuto con lo snapshot {label}; '
                              'non confrontare la data snapshot con un mese generico.')

    for path, value in ((SNAPSHOT, snapshot), (SITE, site), (STATE, state), (REGISTRY, registry)):
        save(path, value)
    states = Counter(r.get('stato') for r in selected)
    return dict(sha256=sha, regional=len(all_rows), versilia=len(selected), added=added, removed=removed,
                changes=changes, states=dict(states))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', type=Path, help='File cave_public.json già scaricato')
    parser.add_argument('--acquired-at', required=True, help='Data/ora ISO dell’acquisizione, con fuso')
    args = parser.parse_args()
    payload = args.json.read_bytes() if args.json else urllib.request.urlopen(RTCAVE_URL, timeout=60).read()
    print(json.dumps(update(payload, args.acquired_at), ensure_ascii=False, indent=2))
