#!/usr/bin/env python3
"""Preserve complete ACI 2024 archives for native municipal reconciliation.

Capital-city tables are not a municipal census. Retrieval never certifies a
benchmark; immutable ZIP bytes remain in the acquisition artifact.
"""
from __future__ import annotations
import argparse, base64, csv, hashlib, io, json, math, zipfile
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'data/site-data.json'
LANDING = 'https://aci.gov.it/attivita-e-progetti/studi-e-ricerche/autoritratto/'
ARCHIVES = (
    'https://aci.gov.it//app/uploads/2025/06/Autoritratto-2024-Parco-Veicolare.zip',
    'https://aci.gov.it/app/uploads/2025/11/Autoritratto-2024-OD.zip',
)


def public_contract(site, metric_id, unit, formula_tokens):
    metric = site['metrics'][metric_id]
    meta, rows = metric['meta'], metric['rows']
    if (meta.get('unit') != unit or str(meta.get('year')) != '2024'
            or len(rows) != 7 or len({r.get('code') for r in rows}) != 7
            or any(not isinstance(r.get('code'), str) or len(r['code']) != 6
                   or not r['code'].isdigit() or isinstance(r.get('value'), bool)
                   or not isinstance(r.get('value'), (int, float))
                   or not math.isfinite(r['value']) for r in rows)):
        raise RuntimeError(f'{metric_id}: municipal public period/unit/value contract mismatch')
    source = str(meta.get('source', '')).casefold()
    formula = str(metric.get('method', {}).get('formula', '')).casefold()
    if ('aci' not in source or 'istat' not in source
            or not all(token.casefold() in formula for token in formula_tokens)):
        raise RuntimeError(f'{metric_id}: public source/formula mismatch')
    return rows


def csv_inventory(raw):
    for encoding in ('utf-8-sig', 'cp1252'):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError('CSV encoding not recognized')
    dialect = csv.Sniffer().sniff(text[:65536], delimiters=';,\t')
    reader = csv.reader(io.StringIO(text, newline=''), dialect)
    header = next(reader)
    return {'encoding': encoding, 'delimiter': dialect.delimiter,
            'headers': header, 'dataRows': sum(1 for _ in reader)}


def acquire_archive(session, url):
    evidence = {'requestedUrl': url}
    try:
        response = session.get(url, timeout=(30, 240))
        evidence.update({'resolvedUrl': response.url, 'httpStatus': response.status_code,
                         'bytes': len(response.content),
                         'contentType': response.headers.get('Content-Type')})
        response.raise_for_status()
        raw = response.content
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            corrupt = archive.testzip()
            if corrupt is not None:
                raise ValueError(f'ZIP member failed CRC: {corrupt}')
            members, names = [], set()
            for member in archive.infolist():
                if member.is_dir():
                    continue
                if member.filename in names:
                    raise ValueError(f'Duplicate ZIP member: {member.filename}')
                names.add(member.filename)
                content = archive.read(member)
                item = {'name': member.filename, 'bytes': len(content),
                        'sha256': hashlib.sha256(content).hexdigest()}
                if member.filename.lower().endswith('.csv'):
                    try:
                        item['csv'] = csv_inventory(content)
                    except (ValueError, csv.Error, StopIteration) as exc:
                        item['schemaInspectionError'] = str(exc)
                members.append(item)
            if not members:
                raise ValueError('Empty native archive')
        evidence.update({'status': 'NATIVE_ARCHIVE_RETRIEVED', 'crc': 'PASS',
                         'sha256': hashlib.sha256(raw).hexdigest(),
                         'zipBase64': base64.b64encode(raw).decode('ascii'),
                         'members': members})
    except (requests.RequestException, ValueError, zipfile.BadZipFile,
            RuntimeError, NotImplementedError) as exc:
        evidence.update({'status': 'NATIVE_ARCHIVE_ACCESS_OR_INTEGRITY_BLOCKED',
                         'error': f'{type(exc).__name__}: {exc}'})
    return evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    site = json.loads(SITE.read_text(encoding='utf-8'))
    motor = public_contract(site, 'motorization', 'per1000',
                            ('autovetture', 'popolazione', '1.000'))
    polluting = public_contract(site, 'pollutingCars', 'percent',
                                ('euro 0', 'autovetture totali', '100'))
    if {r['code'] for r in motor} != {r['code'] for r in polluting}:
        raise RuntimeError('ACI: public municipal scopes differ')
    session = requests.Session()
    session.headers['User-Agent'] = 'OsservatorioVersilia-A3-ACI-benchmark/1.0'
    archives = [acquire_archive(session, url) for url in ARCHIVES]
    retrieved = sum(a['status'] == 'NATIVE_ARCHIVE_RETRIEVED' for a in archives)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # The bulk wrapper embeds this result again. Preserve each ZIP only once;
    # profile*.json uploads sidecars, while .raw.json excludes summary entries.
    for index, archive in enumerate(archives):
        if 'zipBase64' not in archive:
            continue
        native = {'sourceUrl': archive['resolvedUrl'], 'sha256': archive['sha256'],
                  'zipBase64': archive.pop('zipBase64')}
        artifact = args.output.with_name(f'{args.output.stem}.{index}.native.raw.json')
        artifact.write_text(json.dumps(native, separators=(',', ':'))+'\n', encoding='utf-8')
        archive['nativeArtifact'] = artifact.name
    payload = {
        'schemaVersion': 1, 'profileId': 'aci-istat-annual',
        'publisher': 'ACI / Istat — parco veicolare', 'referenceYear': 2024,
        'sourceUrl': LANDING, 'status': 'CANDIDATE_REJECTED', 'benchmarks': {},
        'archives': archives,
        'publicRows': {'motorization': motor, 'pollutingCars': polluting},
        'qualityGate': {'status': 'FAIL', 'nativeArchivesRetrieved': retrieved,
                        'publicReconciliation': 'NOT_CERTIFIED',
                        'errors': ['Complete native municipal panel and coeval denominators '
                                   'must reconcile 7/7 before regional/national publication.']},
        'blocked': {metric: {'reason': 'Native panel retrieved; schema and 7/7 reconciliation pending'
                            if retrieved else 'Native archives inaccessible or invalid; no data inferred'}
                    for metric in ('motorization', 'pollutingCars')},
        'rule': 'Capital-city Istat workbook is not a full municipal panel. '
                'ZIP retrieval is evidence, not acquisition certification; missing values are not zero.',
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':'))+'\n',
                           encoding='utf-8')
    print(json.dumps({'status': payload['status'], 'nativeArchivesRetrieved': retrieved,
                      'candidateCount': 0, 'publicReconciliation': 'NOT_CERTIFIED'}))


if __name__ == '__main__':
    main()
