#!/usr/bin/env python3
"""Acquire the cardinal accessibility component; never average ordinal IFC classes."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, math, re, statistics
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLOW = 'IT1,DF_COMP_FRA_IND_MUNICIPAL_02,1.0'
BASE = 'https://esploradati.istat.it/SDMXWS/rest'
DATA_URL = f'{BASE}/data/{FLOW}/A..INDEX_ACCES_ESSENT_SERVICES?startPeriod=2022&endPeriod=2022'
STRUCTURE_URL = f'{BASE}/dataflow/IT1/DF_COMP_FRA_IND_MUNICIPAL_02/1.0?references=all'
LANDING = 'https://www.istat.it/comunicato-stampa/la-fragilita-dei-comuni-italiani-anno-2022/'
METHODOLOGY = 'https://www.istat.it/wp-content/uploads/2025/12/Stat_Focus_Fragilita-dei-Comuni-italiani_Anno-2022.pdf'
TUSCANY_PREFIXES = {'045','046','047','048','049','050','051','052','053','100'}
METRIC = 'essentialServicesAccessibility'

def download(url, accept):
    request = urllib.request.Request(url, headers={'Accept':accept, 'User-Agent':'OsservatorioVersilia-A3-IFC/1.0'})
    with urllib.request.urlopen(request, timeout=300) as response:
        body = response.read(30 * 1024 * 1024 + 1)
    if len(body) > 30 * 1024 * 1024: raise RuntimeError('IFC response exceeds size limit')
    return body

def parse_records(body):
    reader = csv.DictReader(io.StringIO(body.decode('utf-8-sig')))
    required = {'FREQ','REF_AREA','DATA_TYPE','TIME_PERIOD','OBS_VALUE','UNIT_MEAS','DATA_REF_PERIOD'}
    if not required.issubset(reader.fieldnames or []): raise RuntimeError('IFC CSV schema mismatch')
    records = {}
    for row in reader:
        if (row['FREQ'], row['DATA_TYPE'], row['TIME_PERIOD'], row['UNIT_MEAS'], row['DATA_REF_PERIOD']) != ('A','INDEX_ACCES_ESSENT_SERVICES','2022','MINUT','INDEX_ACCES_ESSENT_SERVICES_REF_PERIOD'):
            raise RuntimeError('IFC unexpected series, unit or reference period')
        code = row['REF_AREA']
        if not re.fullmatch(r'\d{6}', code) or code in records: raise RuntimeError('IFC invalid or duplicate municipal code')
        value = float(row['OBS_VALUE'])
        if not math.isfinite(value) or value < 0: raise RuntimeError('IFC missing/invalid observation')
        records[code] = value
    # Official methodology: 31-12-2022 geography, excluding Misiliscemi,
    # which was created by territorial detachment rather than municipal fusion.
    if len(records) != 7903 or '081025' in records: raise RuntimeError('IFC official national scope mismatch')
    if sum(code[:3] in TUSCANY_PREFIXES for code in records) != 273: raise RuntimeError('IFC Tuscany scope mismatch')
    return records

def validate_period(structure):
    root = ET.fromstring(structure)
    ns = {'s':'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure', 'c':'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common'}
    codes = root.findall('.//s:Codelist/s:Code',ns)
    names = [n.text or '' for code in codes if code.get('id') == 'INDEX_ACCES_ESSENT_SERVICES_REF_PERIOD' for n in code.findall('c:Name',ns)]
    if not any('2019' in n and ('riferimento' in n or 'reference' in n) for n in names): raise RuntimeError('IFC effective reference year 2019 not certified')
    return names

def reconcile(records):
    local = json.loads((ROOT / 'data/source-snapshots/fragilita-comunale-v133.json').read_text())['istatByTown']
    if len(local) != 7 or len({t['code'] for t in local.values()}) != 7: raise RuntimeError('IFC public scope not 7/7')
    proof = {}
    for town, item in local.items():
        code = item['code']; expected = item['latest2022']['INDEX_ACCES_ESSENT_SERVICES']
        if code not in records or not math.isclose(records[code],float(expected),abs_tol=1e-9,rel_tol=0): raise RuntimeError(f'IFC mismatch: {town}')
        proof[code] = {'town':town, 'value':records[code]}
    return proof

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--input-csv',type=Path)
    parser.add_argument('--input-structure',type=Path)
    args = parser.parse_args()
    body = args.input_csv.read_bytes() if args.input_csv else download(DATA_URL,'application/vnd.sdmx.data+csv;version=1.0.0')
    structure = args.input_structure.read_bytes() if args.input_structure else download(STRUCTURE_URL,'application/vnd.sdmx.structure+xml;version=2.1')
    period = validate_period(structure)
    records = parse_records(body)
    proof = reconcile(records)
    benchmarks = {METRIC:{'year':'2019','unit':'minutes', 'tuscany':statistics.median(v for c,v in records.items() if c[:3] in TUSCANY_PREFIXES), 'italy':statistics.median(records.values())}}
    payload = {'schemaVersion':1, 'profileId':'istat-fragility-2022', 'publisher':'Istat — componente accessibilità IFC', 'sourceUrl':LANDING,
        'source':{'data':DATA_URL,'structure':STRUCTURE_URL,'methodology':METHODOLOGY,'csvSha256':hashlib.sha256(body).hexdigest(),'structureSha256':hashlib.sha256(structure).hexdigest()},
        'referenceYear':2019,'releaseYear':2022,'effectivePeriodMetadata':period,
        'scope':{'italyMunicipalities':7903,'tuscanyMunicipalities':273,'excludedMunicipality':{'code':'081025','name':'Misiliscemi','reason':'Escluso esplicitamente dalla geografia IFC ricostruita, nota 3 della metodologia Istat.'},
            'note':'Mediana non ponderata dei tempi comunali: 273 Comuni Toscana e 7.903 del perimetro nazionale IFC. Riferimento effettivo 2019; geografia IFC al 31 dicembre 2022, che esclude Misiliscemi. Non è il tempo medio di viaggio della popolazione.'},
        'aggregation':'median-municipalities', 'records':[[c,v] for c,v in sorted(records.items())], 'municipalReconciliation':proof,'benchmarks':benchmarks,
        'blocked':{'municipalFragility':'Decili ordinali: benchmark scalare cardinale incompatibile.', 'lowProductivityEmployment':'Ventili ordinali: benchmark scalare cardinale incompatibile.'},
        'qualityGate':{'status':'PASS','errors':[],'municipalReconciliation':'7/7 PASS','officialScope':'7903 Italy / 273 Tuscany; Misiliscemi explicitly excluded by Istat methodology'}}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    # Compact records keep the governed snapshot small without losing any municipality.
    args.output.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n')
    print(f'IFC accessibility candidate PASS: Tuscany={benchmarks[METRIC]["tuscany"]}, Italy={benchmarks[METRIC]["italy"]}; official 7903/273 scope; 7/7 reconciled. Not ACQUIRED until publication gate.')

if __name__ == '__main__': main()
