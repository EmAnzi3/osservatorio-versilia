"""Acquire SISBON 2.0 public CSV and update only the remediation carrier.

Run explicitly; never during a build. Keep water/GAIA acquisition dates intact.
"""
import argparse
import base64
import csv
import gzip
import hashlib
import io
import json
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://sisbon.regione.toscana.it/api/v1/sisbon/map_public?format=csv'
CLOSED = {'200', '210', '220', '230', '280'}
ACTIVE = {'10', '40', '50', '60', '70', '120', '135', '140'}

def load(path):
    return json.loads((ROOT / path).read_text())

def save(path, value):
    (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def procedures(raw, towns):
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    required = {'codice_regionale', 'denominazione_sito', 'nome_comune', 'indirizzo', 'd_stato_proc', 'd_stato_cont'}
    if not required <= set(reader.fieldnames or []):
        raise ValueError('SISBON schema changed')
    lookup = {t['name'].casefold(): t['code'] for t in towns}
    seen = set()
    result = []
    for r in reader:
        ident = r['codice_regionale'].strip()
        if not ident or ident in seen:
            raise ValueError('SISBON missing or duplicate regional code')
        seen.add(ident)
        code = lookup.get(r['nome_comune'].strip().casefold())
        if code is None:
            continue
        state = r['d_stato_proc'].split('-', 1)[0]
        if state not in ACTIVE | CLOSED:
            raise ValueError('SISBON unreviewed municipal state')
        result.append(dict(townCode=code, id=ident, name=r['denominazione_sito'], address=r['indirizzo'],
                           contamination=r['d_stato_cont'], procedureState=r['d_stato_proc'], stateCode=state,
                           status='closed' if state in CLOSED else 'active', lat=None, lon=None))
    if not result or {r['townCode'] for r in result} != {t['code'] for t in towns}:
        raise ValueError('SISBON incomplete municipal coverage')
    return result

def update(raw, acquired):
    date.fromisoformat(acquired)
    raw_path = f'data/source-snapshots/sisbon-public-{acquired}.csv.gz.b64'
    site = load('data/site-data.json')
    records = procedures(raw, site['towns'])
    old_order = {r['id']: i for row in site['metrics']['remediationProceedings']['rows'] for i, r in enumerate(row['procedures'])}
    records.sort(key=lambda r: (r['townCode'], old_order.get(r['id'], 10**9), r['id']))
    sha = hashlib.sha256(raw).hexdigest()
    native_path = 'data/source-snapshots/ambiente-acqua-v124-data.json'
    manifest_path = 'data/source-snapshots/ambiente-acqua-v124-manifest.json'
    summary_path = 'data/source-snapshots/ambiente-acqua-bonifiche-v124.json'
    native, manifest, summary = map(load, (native_path, manifest_path, summary_path))
    counts = {t['code']: dict(active=0, closed=0, total=0) for t in site['towns']}
    for r in records:
        counts[r['townCode']][r['status']] += 1
        counts[r['townCode']]['total'] += 1
    total = {k: sum(v[k] for v in counts.values()) for k in ('active', 'closed', 'total')}
    native['sources']['sisbon'] = dict(validatedCsvSha256=sha, fetchedSha256=sha, url=URL, acquiredAt=acquired, rawSnapshot=raw_path)
    native['remediationProceedings']['procedures'] = records
    manifest['sources']['sisbon'] = dict(csvSha256=sha, url=URL, snapshot=acquired, rawSnapshot=raw_path)
    manifest['versilia']['remediationProceedings'] = total
    summary['sources']['sisbon'].update(sha256=sha, url=URL, snapshot=acquired, uniqueRegionalCodesVersilia=total['total'])
    summary['remediationProceedings'].update(countsByMunicipality=counts, versilia=total)
    metric = site['metrics']['remediationProceedings']
    metric['meta']['year'] = acquired
    metric['meta']['source'] = 'Regione Toscana — SISBON 2.0'
    metric['sourceUrl'] = URL
    for row in metric['rows']:
        n = counts[row['code']]
        row['procedures'] = [r for r in records if r['townCode'] == row['code']]
        row['value'] = row['benchmarkValue'] = n['active']
        for part in row['parts']:
            part['value'] = n[part['key']]
    metric['aggregate']['value'] = total['active']
    for part in metric['aggregate']['parts']:
        part['value'] = total[part['key']]
    metric['aggregate']['note'] = f"{total['total']} procedimenti univoci: {total['active']} attivi e {total['closed']} chiusi."
    metric['method']['coverage'] = f"7/7 · {total['total']}/{total['total']} codici regionali univoci"
    registry = load('data/source-registry.json')
    legacy = 'https://sira.arpat.toscana.it/apex/f?p=SISBON:REPORT_PER_RT::CSV:IR_REPORT_GEOSCOPIO'
    for field in ('sourceProfileByUrl', 'sourceUrlProfiles', 'sourceChangePolicies'):
        if legacy in registry.get(field, {}):
            registry[field][URL] = registry[field][legacy]
    registry['sourceProbePolicies'][URL] = dict(role='data_export', acquisition=dict(method='public_csv', path=raw_path, materializer='scripts/update_sisbon_public.py', publishedReference=acquired), releaseCheck='Compare regional IDs and procedure states in the public CSV; a proceeding is not confirmed contamination.')
    # All validation completes before any data file is written.
    (ROOT / raw_path).write_text(base64.b64encode(gzip.compress(raw, mtime=0)).decode() + '\n')
    for path, value in ((native_path, native), (manifest_path, manifest), (summary_path, summary), ('data/site-data.json', site), ('data/source-registry.json', registry)):
        save(path, value)
    return total

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', type=Path)
    parser.add_argument('--acquired-at', default=date.today().isoformat())
    args = parser.parse_args()
    raw = args.csv.read_bytes() if args.csv else urllib.request.urlopen(URL, timeout=60).read()
    print(update(raw, args.acquired_at))
