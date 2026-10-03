#!/usr/bin/env python3
"""Acquire the complete Istat 2021 littoral DBF without GIS dependencies."""
from __future__ import annotations
import argparse, hashlib, io, json, math, struct, zipfile
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://www.istat.it/wp-content/uploads/2026/02/Linea_litoranea_al-31-12-2021.zip'
LANDING = 'https://www.istat.it/classificazione/principali-statistiche-geografiche-sui-comuni/'
PUBLIC = ROOT / 'data/source-snapshots/territorio-ucs-v136.json'


def read_dbf(raw: bytes) -> list[dict[str, str]]:
    count, header_size, record_size = struct.unpack_from('<IHH', raw, 4)
    if len(raw) < header_size + count * record_size:
        raise RuntimeError('DBF truncated')
    fields = []
    for offset in range(32, header_size - 1, 32):
        field = raw[offset:offset + 32]
        fields.append((field[:11].split(b'\0')[0].decode('ascii'), field[16]))
    if 1 + sum(size for _, size in fields) != record_size:
        raise RuntimeError('DBF invalid record width')
    if not {'PRO_COM', 'COD_REG', 'SHAPE_Leng'} <= {key for key, _ in fields}:
        raise RuntimeError('DBF missing geography fields')
    rows = []
    for index in range(count):
        record = raw[header_size + index * record_size:header_size + (index + 1) * record_size]
        if record[0:1] != b' ':
            raise RuntimeError('DBF contains deleted/unknown records; no omissions allowed')
        row, offset = {}, 1
        for key, size in fields:
            row[key] = record[offset:offset + size].decode('utf-8').strip()
            offset += size
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument('--output', required=True)
    args = parser.parse_args()
    response = requests.get(URL, timeout=180); response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith('.dbf')]
        if len(names) != 1: raise RuntimeError('Expected exactly one DBF')
        rows = read_dbf(archive.read(names[0]))
    codes = [str(int(row['PRO_COM'])).zfill(6) for row in rows]
    if len(set(codes)) != len(codes): raise RuntimeError('Duplicate municipalities')
    lengths, regions = {}, {}
    for code, row in zip(codes, rows):
        length = float(row['SHAPE_Leng']) / 1000
        region = int(row['COD_REG'])
        if not math.isfinite(length) or length <= 0 or not 1 <= region <= 20:
            raise RuntimeError(f'Invalid coastline/region for {code}')
        lengths[code], regions[code] = length, region
    public = json.loads(PUBLIC.read_text())
    site = json.loads((ROOT / 'data/site-data.json').read_text())
    identities = {row['town']: row['code'] for row in site['metrics']['population']['rows']}
    reconciliation = {}
    for town, expected in public['coastlineKm'].items():
        code = identities[town]
        littoral = public['classifications'][town]['littoral']
        if expected is None:
            if littoral or code in lengths: raise RuntimeError(f'{town}: invalid n.a.')
            reconciliation[code] = {'notApplicable': True}
        else:
            if not littoral or code not in lengths or regions[code] != 9:
                raise RuntimeError(f'{town}: missing coastal row')
            if not math.isclose(lengths[code], float(expected), rel_tol=0, abs_tol=1e-8):
                raise RuntimeError(f'{town}: public coastline mismatch')
            reconciliation[code] = {'valueKm': lengths[code], 'publicValueKm': expected}
    if len(reconciliation) != 7: raise RuntimeError('Incomplete public reconciliation')
    regional = {region: math.fsum(lengths[c] for c in codes if regions[c] == region) for region in sorted(set(regions.values()))}
    italy = math.fsum(lengths.values())
    if not math.isclose(math.fsum(regional.values()), italy, rel_tol=0, abs_tol=1e-8):
        raise RuntimeError('Regional/national totals mismatch')
    result = {'schemaVersion': 2, 'profileId': 'istat-geografie-funzionali-2021',
        'publisher': 'Istat — Linea litoranea statistica', 'sourceUrl': LANDING, 'dataUrl': URL,
        'sourceSha256': hashlib.sha256(response.content).hexdigest(), 'status': 'ACQUIRED_CANDIDATE',
        'scope': {'municipalityRecords': len(rows), 'tuscanyRecords': sum(regions[c] == 9 for c in codes),
            'coverage': 'all records in the complete official DBF; no deleted or duplicate records'},
        'benchmarks': {'statisticalCoastlineLength': {'year': '2021', 'unit': 'km',
            'tuscany': regional[9], 'italy': italy, 'formula': 'sum of official SHAPE_Leng / 1000'}},
        'municipalReconciliation': reconciliation, 'regionalTotalsKm': regional,
        'records': [{'code': c, 'region': regions[c], 'lengthKm': lengths[c]} for c in sorted(codes)],
        'qualityGate': {'status': 'PASS', 'publicReconciliation': '4 coastal + 3 n.a. PASS',
            'regionalNationalControl': 'complete official DBF and regional sum PASS', 'errors': []},
        'blocked': {'territorialClassification': 'categorical littoral/coastal-zone/DEGURBA profile; scalar benchmark is not equivalent'}}
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'benchmarks': result['benchmarks'], 'scope': result['scope']}))

if __name__ == '__main__': main()
