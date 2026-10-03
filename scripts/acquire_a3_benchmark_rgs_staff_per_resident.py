#!/usr/bin/env python3
"""Complete Tuscany municipal-employer stock, with two explicit PIAO zero records."""
from __future__ import annotations

import argparse
import base64
import csv
import gzip
import hashlib
import io
import json
import math
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

import audit_rgs_amministrazione_values as source

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/'data/source-snapshots/a3-rgs-staff-benchmark-2024.json'
URL='https://contoannuale.rgs.mef.gov.it/it/web/sicosito/dipendenti/abitanti-comune-acc'
STAFF_SHA='a4491d878cc59ed55c50400fcf782d7ea9228c0f00ad0366d6edb7de824a5c89'
POP_SHA='fd0c36bae14df0737b5c60a675d978507fe875cfa9381747a006de6db90a4875'
GEO_SHA='f63b4fd3c27d463c7fc070e42acf0357883a945aca5bf4a33cc38a830e3f7159'
ANAGRAFE_SHA='0b8aa75222446bf1570237cf8dc5bd0e7f4cc7615c5bd726281025e120ffadf8'
ANAGRAFE_URL='https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/datastore/dump/745861d3-e741-43ff-b68a-7cf357aab888.csv'
POP_URL='https://demo.istat.it/data/p2/P2_2024_it_Comuni.zip'
ZERO_SOURCES={
    '048025':('https://www.comune.londa.fi.it/system/files/2025-04/piao%202025-2027_londa.pdf',
              '7e4fde3069c2a341e63cafccaf8a0f6d11fda7640f84b6faa17dc854a0bf91cc'),
    '048039':('https://www.comune.san-godenzo.fi.it/sites/www.comune.san-godenzo.fi.it/files/documenti/piao_2025-2027_san_godenzo.pdf',
              '667c9c331fb78661f59ad1cd4f86784a5718b2f0b810b58a333ef562dea95460'),
}
PROVINCES={'045','046','047','048','049','050','051','052','053','100'}
CODES={'046018','046033','046005','046024','046028','046013','046030'}
STAFF_FIELDS=[
    'Numero Dipendenti Donne Tempo Pieno','Numero Dipendenti Uomini Tempo Pieno',
    'Numero Dipendenti Donne Part time Inf. 50%','Numero Dipendenti Uomini Part time Inf. 50%',
    'Numero Dipendenti Donne Part time Sup. 50%','Numero Dipendenti Uomini Part time Sup. 50%',
]


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def integer(value):
    if not isinstance(value,str) or not value.strip():
        raise RuntimeError('RGS: missing native count; zero imputation forbidden')
    result=Decimal(value.strip())
    if not result.is_finite() or result<0 or result!=result.to_integral_value():
        raise RuntimeError('RGS: native nonnegative integer count required')
    return int(result)


def public_number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise RuntimeError('RGS: finite public number required')
    return value


def validate_snapshot(metric,snapshot):
    s=snapshot['source']
    if (snapshot.get('profileId')!='rgs-conto-annuale-annual' or snapshot.get('sourceUrl')!=URL
            or type(snapshot.get('referenceYear')) is not int or snapshot['referenceYear']!=2024
            or s.get('staffUrl')!=source.URLS['turnover'] or s.get('staffSha256')!=STAFF_SHA
            or s.get('anagrafeUrl')!=ANAGRAFE_URL or s.get('anagrafeSha256')!=ANAGRAFE_SHA
            or s.get('populationUrl')!=POP_URL or s.get('populationSha256')!=POP_SHA):
        raise RuntimeError('RGS: native source or reference period mismatch')
    staff=gzip.decompress(base64.b64decode(s['staffCsvGzipBase64'],validate=True))
    pop_zip=base64.b64decode(s['populationZipBase64'],validate=True)
    if hashlib.sha256(staff).hexdigest()!=STAFF_SHA or hashlib.sha256(pop_zip).hexdigest()!=POP_SHA:
        raise RuntimeError('RGS: full native source fingerprint mismatch')
    with ZipFile(io.BytesIO(pop_zip)) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('RGS: demographic archive CRC failure')
        text=archive.read('P2_2024_it_Comuni.csv').decode('utf-8-sig')
    lines=text.splitlines()
    if lines[0]!='"Bilancio demografico e popolazione residente al 31 dicembre 2024"':
        raise RuntimeError('RGS: demographic year mismatch')
    population={}
    for row in csv.DictReader(io.StringIO('\n'.join(lines[1:])),delimiter=';'):
        code=row['Codice comune']
        if len(code)!=6 or not code.isdigit() or code in population:
            raise RuntimeError('RGS: demographic municipal identity mismatch')
        for when in ('1° gennaio','31 dicembre'):
            prefix=f'Popolazione censita al {when} - '
            men,women,total=(integer(row[prefix+sex]) for sex in ('Maschi','Femmine','Totale'))
            if men+women!=total:
                raise RuntimeError('RGS: demographic sex components mismatch')
        population[code]=integer(row['Popolazione censita al 1° gennaio - Totale'])
    tus={code for code in population if code[:3] in PROVINCES}
    if len(population)!=7896 or len(tus)!=273 or sum(population[c] for c in tus)!=3660530:
        raise RuntimeError('RGS: complete demographic cohort mismatch')
    geographies=snapshot['geographies']
    if s.get('geographiesSha256')!=GEO_SHA or digest(geographies)!=GEO_SHA or len(geographies)!=271:
        raise RuntimeError('RGS: native employer/geography mapping mismatch')
    by_id={r['Id_Ente']:r['Codice_ISTAT_Comune'] for r in geographies}
    if len(by_id)!=271 or len(set(by_id.values()))!=271 or set(by_id.values())!=tus-set(ZERO_SOURCES):
        raise RuntimeError('RGS: municipal-employer coverage mismatch')
    counts=defaultdict(int); identities=set(); employers=set(); native=source.parse(staff)
    if len(native)!=40521:
        raise RuntimeError('RGS: complete occupation panel mismatch')
    for row in native:
        if row['Anno Rilevazione']!='2024':
            raise RuntimeError('RGS: mixed occupation years')
        if source.norm(row['Descrizione Tipo Istituzione'])!='COMUNI':
            continue
        entity=row['Codice Ente BDAP'];employers.add(entity)
        identity=tuple(row[k] for k in ('Codice Istituzione','Codice Ente BDAP','Codice Comparto',
                                      'Codice Contratto Lavoro','Codice Macrocategoria','Codice Categoria'))
        if identity in identities:
            raise RuntimeError('RGS: duplicate occupation identity')
        identities.add(identity)
        total=sum(integer(row[k]) for k in STAFF_FIELDS)
        if entity in by_id:
            counts[by_id[entity]]+=total
    if len(employers)!=7725 or not set(by_id)<=employers or set(counts)!=tus-set(ZERO_SOURCES):
        raise RuntimeError('RGS: native institution coverage mismatch')
    zero_records=snapshot['explicitZeroEmployers']
    if len(zero_records)!=2 or {r['code'] for r in zero_records}!=set(ZERO_SOURCES):
        raise RuntimeError('RGS: explicit zero-employer evidence missing')
    for row in zero_records:
        url,sha=ZERO_SOURCES[row['code']]
        pdf=base64.b64decode(row['pdfBase64'],validate=True)
        if (row['sourceUrl']!=url or row['sha256']!=sha or hashlib.sha256(pdf).hexdigest()!=sha
                or not pdf.startswith(b'%PDF') or row['referenceDate']!='2024-12-31'
                or type(row['staff']) is not int or row['staff']!=0
                or type(row['physicalPage']) is not int or row['physicalPage']!=4
                or row['statement']!='alla data del 31/12/2024 non ha nessun dipendente'):
            raise RuntimeError('RGS: explicit native zero/date evidence mismatch')
        counts[row['code']]=0
    raw={'tuscany':{'staff':sum(counts.values()),'population':sum(population[c] for c in tus),
                    'nativeEmployers':271,'explicitZeroEmployers':2,'municipalities':273},'italy':None}
    if snapshot['raw']!=raw or any(type(v) is not int for v in snapshot['raw']['tuscany'].values()):
        raise RuntimeError('RGS: regional components mismatch')
    if metric['meta'].get('year')!='2024' or metric['meta'].get('unit')!='per1000':
        raise RuntimeError('RGS: public period/unit mismatch')
    rows=metric['rows']
    if len(rows)!=7 or {r['code'] for r in rows}!=CODES:
        raise RuntimeError('RGS: public municipal perimeter mismatch')
    for row in rows:
        code=row['code'];expected=counts[code]/population[code]*1000
        if (type(row.get('staffAt31Dec')) is not int or row['staffAt31Dec']!=counts[code]
                or type(row.get('residentPopulation')) is not int or row['residentPopulation']!=population[code]
                or not math.isclose(public_number(row['value']),expected,rel_tol=0,abs_tol=1e-12)):
            raise RuntimeError('RGS: native municipal numerator/denominator mismatch')
    if set(snapshot['benchmarks'])!={'municipalEmployeesPer1000'}:
        raise RuntimeError('RGS: unsupported candidate metric')
    bench=snapshot['benchmarks']['municipalEmployeesPer1000']
    expected=raw['tuscany']['staff']/raw['tuscany']['population']*1000
    if (bench.get('year')!='2024' or bench.get('unit')!='per1000' or bench.get('italy') is not None
            or bench.get('formula')!='dipendenti comunali al 31 dicembre 2024 / residenti al 1° gennaio 2024 × 1.000'
            or not math.isclose(public_number(bench['tuscany']),expected,rel_tol=0,abs_tol=1e-12)):
        raise RuntimeError('RGS: complete regional benchmark mismatch')
    if snapshot.get('qualityGate',{}).get('status')!='PASS' or snapshot['qualityGate'].get('errors')!=[]:
        raise RuntimeError('RGS: candidate quality gate mismatch')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();snapshot=json.loads(FROZEN.read_text())
    metric=json.loads((ROOT/'data/site-data.json').read_text())['metrics']['municipalEmployeesPer1000']
    validate_snapshot(metric,snapshot)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(snapshot,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({'status':'ACQUIRED_CANDIDATE','publicReconciliation':'7/7',
                      'tuscanyCoverage':'273/273','raw':snapshot['raw'],'benchmarks':snapshot['benchmarks']}))


if __name__=='__main__':main()
