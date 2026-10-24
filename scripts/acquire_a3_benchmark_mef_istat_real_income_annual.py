#!/usr/bin/env python3
"""Acquire a complete taxable-income panel and apply the governed NIC contract."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, math, re, zipfile
from pathlib import Path
from audit_taxable_income_history_mef import URL, decode
from acquire_a3_benchmark_istat_fragility_2022 import download

ROOT = Path(__file__).resolve().parents[1]
METRIC = 'incomeVsInflation'
NIC = ROOT / 'data/source-snapshots/nic-italia-2016-2024.json'
COUNTS = {2016: (7979,276), 2024: (7897,273)}
AMOUNT = 'Reddito imponibile - Ammontare in euro'
FREQUENCY = 'Reddito imponibile - Frequenza'

def integer(value):
    text = str(value).strip()
    if not re.fullmatch(r'\d+(?:\.\d{3})*', text):
        raise RuntimeError(f'MEF missing or non-integer component: {value!r}')
    return int(text.replace('.',''))

def parse_archive(body, year):
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith('.csv')]
        expected = f'Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_{year}.csv'
        if names != [expected]: raise RuntimeError('MEF archive member/year mismatch')
        raw = archive.read(expected)
    reader = csv.DictReader(io.StringIO(decode(raw)),delimiter=';')
    required = {'Anno di imposta','Codice Istat Comune','Codice Istat Regione',AMOUNT,FREQUENCY}
    if not required.issubset(reader.fieldnames or []): raise RuntimeError('MEF schema/unit mismatch')
    records=[]; seen=set()
    for row in reader:
        if row['Anno di imposta'].strip() != str(year): raise RuntimeError('MEF actual tax-year mismatch')
        code=row['Codice Istat Comune'].strip(); region=row['Codice Istat Regione'].strip()
        if code in seen or (code!='0' and not re.fullmatch(r'\d{6}',code)):
            raise RuntimeError('MEF duplicate or invalid municipality')
        if region!='0' and not re.fullmatch(r'\d{2}',region): raise RuntimeError('MEF invalid region')
        if (code=='0') != (region=='0'): raise RuntimeError('MEF unlocated record mismatch')
        amount=integer(row[AMOUNT]); frequency=integer(row[FREQUENCY])
        if frequency<=0 or amount<=0: raise RuntimeError('MEF nonpositive taxable-income pair')
        seen.add(code); records.append([code,region,amount,frequency])
    verify_records(records,year)
    return sorted(records), {'archiveMember':expected,'csvSha256':hashlib.sha256(raw).hexdigest(),
        'archiveSha256':hashlib.sha256(body).hexdigest(),'url':URL.format(year=year),
        'actualTaxYear':year,'amountHeader':AMOUNT,'frequencyHeader':FREQUENCY}

def verify_records(records,year):
    if not isinstance(records,list) or len(records)!=COUNTS[year][0]: raise RuntimeError('MEF incomplete panel')
    seen=set(); regions=set(); tuscany=0
    for row in records:
        if not isinstance(row,list) or len(row)!=4: raise RuntimeError('MEF invalid record shape')
        code,region,amount,frequency=row
        if not isinstance(code,str) or code in seen or (code!='0' and not re.fullmatch(r'\d{6}',code)): raise RuntimeError('MEF invalid/duplicate code')
        if not isinstance(region,str) or (region!='0' and not re.fullmatch(r'\d{2}',region)): raise RuntimeError('MEF invalid region')
        if (code=='0') != (region=='0'): raise RuntimeError('MEF unlocated record mismatch')
        for value in (amount,frequency):
            if isinstance(value,bool) or not isinstance(value,int) or value<=0: raise RuntimeError('MEF missing/nonpositive component')
        seen.add(code); regions.add(region); tuscany += region=='09'
    expected_regions={f'{x:02}' for x in range(1,21)}|{'0'}
    if regions!=expected_regions or '0' not in seen or tuscany!=COUNTS[year][1]: raise RuntimeError('MEF geographic scope mismatch')

def totals(records,scope):
    rows=[r for r in records if scope=='italy' or r[1]=='09']
    return {'amountEuro':sum(r[2] for r in rows),'frequency':sum(r[3] for r in rows),'records':len(rows)}

def real_growth(base,current,price_factor):
    return ((current['amountEuro']/current['frequency'])/(base['amountEuro']/base['frequency'])/price_factor-1)*100

def validate_snapshot(metric,snapshot):
    if snapshot.get('qualityGate')!={'status':'PASS','errors':[],'publicReconciliation':'7/7 PASS'}: raise RuntimeError('Real-income gate not PASS')
    if metric['meta'].get('year')!='2024' or metric['meta'].get('unit')!='percent': raise RuntimeError('Real-income public year/unit mismatch')
    nic_bytes=NIC.read_bytes(); nic=json.loads(nic_bytes)
    if snapshot['nic']['sha256']!=hashlib.sha256(nic_bytes).hexdigest() or snapshot['nic']['years']!=[2016,2024]: raise RuntimeError('Real-income NIC provenance mismatch')
    factor=nic['comparisonIndex'][nic['years'].index(2024)]/nic['comparisonIndex'][nic['years'].index(2016)]
    if snapshot['nic']['priceFactor']!=factor: raise RuntimeError('Real-income price-factor mismatch')
    records={}
    for year in (2016,2024):
        rs=snapshot['records'][str(year)]; verify_records(rs,year); records[year]={r[0]:r for r in rs}
        source=snapshot['sources'][str(year)]
        if source['actualTaxYear']!=year or source['url']!=URL.format(year=year) or source['amountHeader']!=AMOUNT or source['frequencyHeader']!=FREQUENCY:
            raise RuntimeError('Real-income source schema/year mismatch')
        for scope in ('tuscany','italy'):
            if totals(rs,scope)!=snapshot['raw'][scope][str(year)]: raise RuntimeError('Real-income totals/component mismatch')
    benchmark=snapshot['benchmarks'][METRIC]
    if benchmark.get('year')!='2024' or benchmark.get('unit')!='percent': raise RuntimeError('Real-income benchmark year/unit mismatch')
    for scope in ('tuscany','italy'):
        expected=real_growth(snapshot['raw'][scope]['2016'],snapshot['raw'][scope]['2024'],factor)
        value=benchmark[scope]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not math.isclose(value,expected,rel_tol=0,abs_tol=1e-10): raise RuntimeError('Real-income aggregate mismatch')
    rows=metric['rows']; codes={r['code'] for r in rows}
    if len(rows)!=7 or len(codes)!=7 or set(snapshot['municipalReconciliation'])!=codes: raise RuntimeError('Real-income public scope not 7/7')
    for row in rows:
        code=row['code']; proof=snapshot['municipalReconciliation'][code]; averages=[]
        for year in (2016,2024):
            record=records[year][code]
            if record[1]!='09' or proof[str(year)]!={'amountEuro':record[2],'frequency':record[3],'averageEuro':round(record[2]/record[3],2)}:
                raise RuntimeError('Real-income municipal components mismatch')
            averages.append(round(record[2]/record[3],2))
        nominal=(averages[1]/averages[0]-1)*100; expected=(averages[1]/averages[0]/factor-1)*100
        series=row['nominalSeries']; nominal_public=series['values'][series['years'].index(2024)]
        if not math.isclose(nominal,nominal_public,rel_tol=0,abs_tol=.000051) or not math.isclose(expected,row['value'],rel_tol=0,abs_tol=.000051) or not math.isclose(expected,proof['value'],rel_tol=0,abs_tol=1e-10):
            raise RuntimeError('Real-income public endpoint reconciliation mismatch')

def main():
    p=argparse.ArgumentParser();p.add_argument('--input-2016',type=Path);p.add_argument('--input-2024',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    site=json.loads((ROOT/'data/site-data.json').read_text());metric=site['metrics'][METRIC]
    records={};sources={}
    for year in (2016,2024):
        path=getattr(args,f'input_{year}'); body=path.read_bytes() if path else download(URL.format(year=year),'application/zip')
        records[str(year)],sources[str(year)]=parse_archive(body,year)
    nic_bytes=NIC.read_bytes();nic=json.loads(nic_bytes);factor=nic['comparisonIndex'][-1]/nic['comparisonIndex'][0]
    raw={scope:{year:totals(rs,scope) for year,rs in records.items()} for scope in ('tuscany','italy')}
    proof={}
    for row in metric['rows']:
        code=row['code']; local={}
        for year,rs in records.items():
            r=next(r for r in rs if r[0]==code);local[year]={'amountEuro':r[2],'frequency':r[3],'averageEuro':round(r[2]/r[3],2)}
        local['value']=(local['2024']['averageEuro']/local['2016']['averageEuro']/factor-1)*100;proof[code]=local
    benchmark={'year':'2024','unit':'percent',**{scope:real_growth(v['2016'],v['2024'],factor) for scope,v in raw.items()}}
    payload={'schemaVersion':1,'profileId':'mef-istat-real-income-annual','publisher':'MEF — Dipartimento Finanze / Istat NIC',
        'sourceUrl':'https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php','sources':sources,'records':records,'raw':raw,
        'nic':{'sha256':hashlib.sha256(nic_bytes).hexdigest(),'years':[2016,2024],'priceFactor':factor,'sourceSnapshot':str(NIC.relative_to(ROOT))},
        'municipalReconciliation':proof,'benchmarks':{METRIC:benchmark},
        'scope':{'note':'Variazione reale 2016–2024 del reddito imponibile medio per dichiarante. Per Toscana e Italia: somma degli importi / somma delle frequenze su tutte le righe dei rispettivi archivi comunali MEF, poi stesso NIC nazionale del pubblico. Italia include la riga esplicita Mancante/errata (Non indicato nel 2016); nessuna cella mancante riempita. Non è una media dei redditi medi comunali. Le medie comunali sono arrotondate al centesimo, come nel contratto pubblico; gli aggregati regionali/nazionali mantengono i rapporti esatti.'},
        'qualityGate':{'status':'PASS','errors':[],'publicReconciliation':'7/7 PASS'}}
    validate_snapshot(metric,payload)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n')
    print(f'Real-income candidate PASS: Tuscany {benchmark["tuscany"]}; Italy {benchmark["italy"]}; complete panels and 7/7. Not ACQUIRED before publication gate.')

if __name__=='__main__':main()
