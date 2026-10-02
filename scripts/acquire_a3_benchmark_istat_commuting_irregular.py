#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import urllib.request
import csv
import io
import json
import math
import re
import zipfile
from pathlib import Path
from typing import Any


ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data/site-data.json"
FLOW="DF_BULK_PEND_LAV_2021_1"
BASE="https://esploradati.istat.it/SDMXWS/rest/data"
SOURCE_URL="https://www.istat.it/notizia/matrice-di-pendolarismo-per-lavoro/"
TUSCANY_PREFIXES={"045","046","047","048","049","050","051","052","053","100"}

def decode_blob(blob:bytes)->str:
    if blob.startswith(b"PK\x03\x04"):
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            members=[n for n in z.namelist() if n.lower().endswith((".csv",".txt"))]
            if not members: raise RuntimeError("Pendolarismo: ZIP senza CSV/TXT")
            member=max(members,key=lambda n:z.getinfo(n).file_size)
            blob=z.read(member)
    for enc in ("utf-8-sig","utf-8","cp1252","latin-1"):
        try:return blob.decode(enc)
        except UnicodeDecodeError: pass
    return blob.decode("latin-1",errors="replace")

ARCHIVE_URL="https://esploradati.istat.it/databrowser/DWL/PERMPOP/MATPEN/matrix_pendoLAVORO_2021.zip"
DEMO=ROOT/"data/source-snapshots/a3-istat-demography-benchmark-2026.json"
DIRECT={"inboundCommuters":"inbound","outboundCommuters":"outbound","commuterBalance":"balance"}
RATES={"inboundCommutersRate":"inbound","outboundCommutersRate":"outbound","commuterBalanceRate":"balance"}
P2_URL="https://demo.istat.it/data/p2/P2_2021_it_Comuni.zip"
def fetch_matrix(session=None):
    with urllib.request.urlopen(ARCHIVE_URL,timeout=180) as r: body=r.read(20*1024*1024+1)
    if len(body)>20*1024*1024:raise RuntimeError("Commuting archive oversized")
    return decode_blob(body),ARCHIVE_URL

def verify_records(records):
    if len(records)!=7904:raise RuntimeError("Commuting native coverage mismatch")
    seen=set();totals=[0,0,0]
    for code,internal,outbound,inbound in records:
        if not re.fullmatch(r"\d{6}",code) or code in seen:raise RuntimeError("Commuting duplicate/code mismatch")
        seen.add(code)
        for i,v in enumerate((internal,outbound,inbound)):
            if isinstance(v,bool) or not isinstance(v,int) or v<0:raise RuntimeError("Commuting missing/noninteger")
            totals[i]+=v
    if totals[1]!=totals[2] or sum(totals[:2])!=19565808 or sum(c[:3] in TUSCANY_PREFIXES for c in seen)!=273:raise RuntimeError("Commuting national/Tuscany reconciliation mismatch")

def population_2021(body):
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        if z.namelist()!=['P2_2021_it_Comuni.csv']:raise RuntimeError('P02 2021 archive member mismatch')
        rows=list(csv.reader(io.StringIO(z.read(z.namelist()[0]).decode('utf-8-sig')),delimiter=';'))
    if rows[0]!=['Bilancio demografico e popolazione residente al 31 dicembre 2021']:raise RuntimeError('P02 year mismatch')
    h=rows[1];inds=[h.index('Popolazione censita al 1° gennaio - '+v) for v in ('Maschi','Femmine','Totale')];records=[]
    for row in rows[2:]:
        if not row:continue
        if len(row)!=len(h) or not re.fullmatch(r'\d{1,6}',row[0]) or any(not re.fullmatch(r'\d+',row[i]) for i in inds):raise RuntimeError('P02 missing or invalid observation')
        records.append([row[0].zfill(6),*[int(row[i]) for i in inds]])
    return sorted(records)

def verify_population_2021(records,flows):
    seen=set()
    for code,men,women,total in records:
        if code in seen or not re.fullmatch(r'\d{6}',code):raise RuntimeError('P02 duplicate/code mismatch')
        seen.add(code)
        if any(isinstance(v,bool) or not isinstance(v,int) or v<0 for v in (men,women,total)) or men+women!=total:raise RuntimeError('P02 components mismatch')
    if len(records)!=7904 or seen!={r[0] for r in flows} or sum(r[3] for r in records)!=59236213 or sum(r[3] for r in records if r[0][:3] in TUSCANY_PREFIXES)!=3692865:raise RuntimeError('P02 complete national/Tuscany coverage mismatch')

def validate_snapshot(metric,snapshot,population=None):
    mid=metric['meta']['key']
    unit='per1000' if mid in RATES else 'number' if mid=='inboundCommuters' else 'people'
    if mid not in DIRECT|RATES or metric['meta']['year']!='2021' or metric['meta']['unit']!=unit:raise RuntimeError("Commuting reference mismatch")
    if snapshot['qualityGate']['status']!='PASS' or snapshot['sourceUrl']!=SOURCE_URL or snapshot['resolvedDataUrl']!=ARCHIVE_URL or snapshot['matrixRows']!=523949:raise RuntimeError("Commuting source/gate mismatch")
    records=snapshot['records'];verify_records(records);by={r[0]:r for r in records}
    p21=snapshot['population2021'];verify_population_2021(p21['records'],records)
    if p21['sourceUrl']!=P2_URL or p21['year']!='2021':raise RuntimeError('P02 provenance mismatch')
    pop21={r[0]:r[3] for r in p21['records']}
    demo_bytes=DEMO.read_bytes();demo=json.loads(demo_bytes)['benchmarks']['population']
    if snapshot['population']['sha256']!=hashlib.sha256(demo_bytes).hexdigest() or snapshot['population']['year']!='2026':raise RuntimeError("Commuting population provenance mismatch")
    for target,field in (DIRECT|RATES).items():
        b=snapshot['benchmarks'][target]
        expected_unit='per1000' if target in RATES else 'number' if target=='inboundCommuters' else 'people'
        if b.get('unit')!=expected_unit:raise RuntimeError('Commuting benchmark unit mismatch')
        for scope in ('tuscany','italy'):
            rs=[r for r in records if scope=='italy' or r[0][:3] in TUSCANY_PREFIXES]
            v=sum(r[3]-r[2] if field=='balance' else r[3 if field=='inbound' else 2] for r in rs)
            if target in RATES:
                den=sum(r[3] for r in p21['records'] if scope=='italy' or r[0][:3] in TUSCANY_PREFIXES) if target=='commuterBalanceRate' else demo[scope]
                v=v/den*1000
            if isinstance(b[scope],bool) or not math.isclose(b[scope],v,rel_tol=0,abs_tol=1e-9) or b['year']!='2021':raise RuntimeError("Commuting aggregate mismatch")
    rows=metric['rows']
    if len(rows)!=7 or len({r['code'] for r in rows})!=7:raise RuntimeError("Commuting public scope mismatch")
    for row in rows:
        r=by[row['code']];field=(DIRECT|RATES)[mid]
        value=r[3]-r[2] if field=='balance' else r[3 if field=='inbound' else 2]
        if mid in RATES:
            if mid=='commuterBalanceRate':
                value=value/pop21[row['code']]*1000
            else:
                if population is None or population['meta']['year']!='2026':raise RuntimeError("Commuting public denominator mismatch")
                ps=[p['value'] for p in population['rows'] if p['code']==row['code']]
                if len(ps)!=1 or isinstance(ps[0],bool) or ps[0]<=0:raise RuntimeError("Commuting public population missing")
                value=value/ps[0]*1000
        if isinstance(row['value'],bool) or not math.isclose(row['value'],value,rel_tol=0,abs_tol=1e-9):raise RuntimeError("Commuting public reconciliation mismatch")

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input-zip',type=Path);ap.add_argument('--input-population-2021',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    if args.input_zip: body=args.input_zip.read_bytes()
    else:
        with urllib.request.urlopen(ARCHIVE_URL,timeout=180) as r:body=r.read(20*1024*1024+1)
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        if z.namelist()!=['matrix_pendoLAVORO_2021.txt']:raise RuntimeError('Commuting archive member mismatch')
    reader=csv.DictReader(io.StringIO(decode_blob(body)),delimiter='\t')
    if reader.fieldnames!=['Prov_res','Procom_res','Prov_lav','Procom_lav','Pendolari']:raise RuntimeError('Commuting header mismatch')
    towns={};seen=set();flows=0;destinations=set()
    for row in reader:
        o,d=row['Procom_res'],row['Procom_lav'];v=row['Pendolari']
        if not re.fullmatch(r'\d{6}',o) or not re.fullmatch(r'\d{6}',d) or row['Prov_res']!=o[:3] or row['Prov_lav']!=d[:3] or not re.fullmatch(r'\d+',v) or (o,d) in seen:raise RuntimeError('Commuting invalid/duplicate flow')
        v=int(v);seen.add((o,d));flows+=1;destinations.add(d)
        towns.setdefault(o,[0,0,0]);towns.setdefault(d,[0,0,0])
        if o==d:towns[o][0]+=v
        else:towns[o][1]+=v;towns[d][2]+=v
    if flows!=523949 or len(destinations)!=7903:raise RuntimeError('Commuting flow/destination coverage mismatch')
    records=[[code,*v] for code,v in sorted(towns.items())];verify_records(records)
    if args.input_population_2021:p21body=args.input_population_2021.read_bytes()
    else:
        with urllib.request.urlopen(P2_URL,timeout=180) as r:p21body=r.read(8*1024*1024+1)
    p21records=population_2021(p21body);verify_population_2021(p21records,records)
    site=json.loads(SITE.read_text());demo_bytes=DEMO.read_bytes();demo=json.loads(demo_bytes)['benchmarks']['population'];benchmarks={}
    for mid,field in (DIRECT|RATES).items():
        values={}
        for scope in ('tuscany','italy'):
            rs=[r for r in records if scope=='italy' or r[0][:3] in TUSCANY_PREFIXES]
            v=sum(r[3]-r[2] if field=='balance' else r[3 if field=='inbound' else 2] for r in rs)
            den=sum(r[3] for r in p21records if scope=='italy' or r[0][:3] in TUSCANY_PREFIXES) if mid=='commuterBalanceRate' else demo[scope]
            values[scope]=v/den*1000 if mid in RATES else v
        benchmarks[mid]={'year':'2021','unit':site['metrics'][mid]['meta']['unit'],**values}
    snapshot={'schemaVersion':1,'profileId':'istat-commuting-irregular','publisher':'Istat — Matrice di pendolarismo per lavoro 2021','sourceUrl':SOURCE_URL,'resolvedDataUrl':ARCHIVE_URL,'archiveSha256':hashlib.sha256(body).hexdigest(),'records':records,'matrixRows':flows,'benchmarks':benchmarks,'population':{'year':'2026','sha256':hashlib.sha256(demo_bytes).hexdigest()},'qualityGate':{'status':'PASS','errors':[],'public7of7':list(benchmarks)},'scope':{'note':'Somma dei flussi tra Comuni distinti della matrice ufficiale Istat 2021, 523.949 coppie uniche, 7.904 origini e 7.903 destinazioni, 273 Comuni toscani. In Toscana entrate e uscite comprendono anche flussi tra Comuni toscani: si conserva la definizione comunale. Il saldo nazionale zero deriva dalla conservazione dei flussi osservati. I tassi in entrata e uscita usano la popolazione pubblica al 1° gennaio 2026, dichiarata anche per gli aggregati.'},'blocked':{'commuterBalanceRate':'Denominatore comunale diverso dalla popolazione pubblica 2026: richiede fotografia demografica esatta.','outsideMunicipality':'Quote censuarie pubbliche non riconciliate con la sottopopolazione della matrice per lavoro.','selfContainment':'Quote censuarie pubbliche non riconciliate con la sottopopolazione della matrice per lavoro.'}}
    snapshot['population2021']={'year':'2021','sourceUrl':P2_URL,'archiveSha256':hashlib.sha256(p21body).hexdigest(),'records':p21records}
    snapshot['blocked'].pop('commuterBalanceRate')
    snapshot['scope']['note']+=' Il tasso di saldo usa invece la popolazione censita al 1° gennaio 2021, riconciliata 7/7 e nel pannello nazionale completo di 7.904 Comuni, con maschi + femmine = totale in ogni riga.'
    for mid in benchmarks:validate_snapshot(site['metrics'][mid],snapshot,site['metrics']['population'])
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(snapshot,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({'candidateCount':len(benchmarks),'benchmarks':benchmarks,'blocked':snapshot['blocked']}))
if __name__=='__main__':main()
