#!/usr/bin/env python3
"""Materializza v1.34.0 Economia prodotta nei renderer canonici OV."""
from __future__ import annotations
import json, runpy
from pathlib import Path
from economia_prodotta_config import CONFIG, ECONOMIA_PRODOTTA_KEYS, NEW_KEYS, SCOPES, SOURCE_LABEL, SOURCE_URL, TOWN_ORDER

ROOT=Path(__file__).resolve().parents[1]
SITE_DATA=ROOT/'data/site-data.json'; REGISTRY=ROOT/'data/source-registry.json'
SNAPSHOT=ROOT/'data/source-snapshots/economia-prodotta-frame-sbs-v134.json'


def load_snapshot():
    s=json.loads(SNAPSHOT.read_text(encoding='utf-8')); rows=[]
    for name in s.get('parts',[]):
        part=json.loads((SNAPSHOT.parent/name).read_text(encoding='utf-8'))
        cols=part['columns']; rows += [dict(zip(cols,v,strict=True)) for v in part['rows']]
    s['rows']=rows; return s


def idx(s): return {(int(r['year']),r['scope'],r['town']):r for r in s['rows']}
def itnum(v,d): return f'{v:,.{d}f}'.replace(',','X').replace('.',',').replace('X','.')
def fmt(v,u):
    if v is None:return 'n.d.'
    if u=='millionCurrency':return f'{itnum(v,1)} mln €'
    if u=='currency':return f'{itnum(v,0)} €'
    if u=='percent':return f'{itnum(v,1)}%'
    return itnum(v,1)


def value(r,key):
    if key=='businessTurnover': return r['turnoverThousandEuro']/1000
    if key=='businessValueAdded': return r['valueAddedThousandEuro']/1000
    if key=='labourProductivity': return r['valueAddedPerPersonEmployedThousandEuro']*1000
    if key=='turnoverPerPersonEmployed': return r['turnoverThousandEuro']/r['personsEmployed']*1000
    if key=='valueAddedTurnoverShare': return r['valueAddedTurnoverPercent']
    if key=='averageGrossRemunerationPerEmployee': return r['averageGrossRemunerationPerEmployeeThousandEuro']*1000
    if key=='labourCost': return None if r['labourCostThousandEuro'] is None else r['labourCostThousandEuro']/1000
    if key=='grossOperatingMargin': return None if r['labourCostThousandEuro'] is None else (r['valueAddedThousandEuro']-r['labourCostThousandEuro'])/1000
    raise KeyError(key)


def aggregate(rows,key):
    def s(field):
        vv=[r[field] for r in rows]
        return None if any(v is None for v in vv) else sum(vv)
    add=s('personsEmployed'); emp=s('employees'); va=s('valueAddedThousandEuro'); turn=s('turnoverThousandEuro'); wages=s('grossWagesThousandEuro'); cost=s('labourCostThousandEuro')
    if key=='businessTurnover':return turn/1000
    if key=='businessValueAdded':return va/1000
    if key=='labourProductivity':return va/add*1000
    if key=='turnoverPerPersonEmployed':return turn/add*1000
    if key=='valueAddedTurnoverShare':return va/turn*100
    if key=='averageGrossRemunerationPerEmployee':return wages/emp*1000
    if key=='labourCost':return None if cost is None else cost/1000
    if key=='grossOperatingMargin':return None if cost is None else (va-cost)/1000
    raise KeyError(key)


def variants(s,key):
    ii=idx(s); c=CONFIG[key]; years=c['years']; rows=[]
    for town in TOWN_ORDER:
        scopes={}
        for scope,label in SCOPES:
            vals=[]; yrs=[]
            for y in years:
                v=value(ii[(y,scope,town)],key)
                if v is not None: yrs.append(y); vals.append(round(float(v),6))
            scopes[scope]={'key':scope,'label':label,'value':vals[-1] if vals else None,'formatted':fmt(vals[-1],c['unit']) if vals else 'n.d.','series':{'years':yrs,'values':vals,'unit':c['unit']}}
        base=ii[(2023,'total',town)]; cur=scopes['total']
        rows.append({'town':town,'code':base['code'],'slug':town.lower().replace(' ','-'),'value':cur['value'],'formatted':cur['formatted'],'series':cur['series'],'normalized':None,'benchmarkValue':cur['value'],'economicScopes':scopes})
    aggs={}
    for scope,label in SCOPES:
        vals=[]; yrs=[]
        for y in years:
            selected=[ii[(y,scope,t)] for t in TOWN_ORDER]; v=aggregate(selected,key)
            if v is not None:yrs.append(y);vals.append(round(float(v),6))
        aggs[scope]={'key':scope,'label':label,'value':vals[-1] if vals else None,'formatted':fmt(vals[-1],c['unit']) if vals else 'n.d.','series':{'years':yrs,'values':vals,'unit':c['unit']}}
    return rows,aggs


def metric(s,key,old=None):
    c=CONFIG[key]; rows,aggs=variants(s,key); meta=dict((old or {}).get('meta',{})); existing_terms=meta.get('searchTerms') or []
    meta.update({'key':key,'theme':'economia','label':c['label'],'shortLabel':c['short'],'description':c['description'],'unit':c['unit'],'year':'2023','source':SOURCE_LABEL,'polarity':'neutral','comparisonReference':'aggregate','economicScopeSelector':True,'economicScopeLabel':'Perimetro Frame SBS','searchTerms':sorted(set(existing_terms+c['searchTerms']))})
    agg=dict((old or {}).get('aggregate',{})); agg.update({'value':aggs['total']['value'],'label':'Versilia · Totale','note':'Aggregato dei sette Comuni sullo stesso perimetro Frame SBS; rapporti e medie sono ricalcolati dai valori elementari, non dalla media semplice dei Comuni.','economicScopes':aggs})
    if old:
        by={r['town']:r for r in rows}; oldby={r.get('town'):r for r in old.get('rows',[])}
        rows=[{**oldby.get(t,{}),**by[t]} for t in TOWN_ORDER]
    return {'meta':meta,'sourceUrl':SOURCE_URL,'rows':rows,'aggregate':agg,'normalizedAggregate':None,'method':{'type':c['methodType'],'formula':c['formula'],'caveat':c['caveat'],'coverage':'7/7'}}


def patch_theme(data):
    e=data.get('themes',{}).get('economia');
    if not e:raise RuntimeError('Tema Economia non trovato')
    target=set(ECONOMIA_PRODOTTA_KEYS); sections=[]; pos=None
    for sec in e.get('sections',[]):
        if sec.get('key')=='economia-prodotta':continue
        x=dict(sec); x['metrics']=[k for k in sec.get('metrics',[]) if k not in target]; sections.append(x)
        if sec.get('key')=='produzione':pos=len(sections)
    new={'key':'economia-prodotta','label':'Economia prodotta','description':'Fatturato, valore aggiunto, produttività, retribuzioni e margini delle unità locali secondo Frame SBS Territoriale Istat.','metrics':list(ECONOMIA_PRODOTTA_KEYS)}
    sections.insert(pos if pos is not None else len(sections),new); e['sections']=sections; e['metrics']=[k for s in sections for k in s.get('metrics',[]) if k in data['metrics']]
    featured=list(e.get('featured') or []); featured=[k for k in featured if k in e['metrics']]
    if 'businessValueAdded' not in featured:featured.insert(0,'businessValueAdded')
    e['featured']=featured[:3]


def patch_registry(metrics):
    r=json.loads(REGISTRY.read_text(encoding='utf-8')); external=sum(m.get('dataStorage',{}).get('type')=='external-climate' for m in metrics.values()); r['expectedMetricCount']=len(metrics);r['expectedExternalMetricCount']=external;r['expectedInlineMetricCount']=len(metrics)-external
    p=r.setdefault('sourceProfiles',{}).setdefault('istat-business-annual',{}); p.update({'publisher':'Istat','frequency':'annual','frequencyLabel':'Annuale','expectedRelease':'Con ritardo fisiologico di circa due anni','acquisitionMethod':'Tavole comunali ufficiali Frame SBS Territoriale Istat; snapshot 2015–2023 con file, tavola, riga e impronta SHA-256 delle fonti annuali.','licenseName':'CC BY 4.0','licenseUrl':'https://www.istat.it/note-legali/'})
    r.setdefault('sourceProfileByUrl',{})[SOURCE_URL]='istat-business-annual'; o=r.setdefault('metricOverrides',{})
    for k in ECONOMIA_PRODOTTA_KEYS:o[k]={'profile':'istat-business-annual'}
    REGISTRY.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def validate(s):
    if s.get('qualityGate',{}).get('coverage')!='7/7' or s.get('qualityGate',{}).get('suppressedTargetCells')!=0:raise RuntimeError('Gate Frame SBS non valido')
    if len(s['rows'])!=189:raise RuntimeError(f"Attese 189 righe Frame SBS, trovate {len(s['rows'])}")
    ii=idx(s)
    for y in range(2015,2024):
        for scope,_ in SCOPES:
            for t in TOWN_ORDER:
                if (y,scope,t) not in ii:raise RuntimeError(f'Riga mancante: {y}/{scope}/{t}')


def main():
    if not SNAPSHOT.exists():raise RuntimeError('Manifest Economia prodotta v1.34.0 mancante')
    s=load_snapshot();validate(s)
    runpy.run_path(str(ROOT/'scripts/patch_economia_prodotta_runtime.py'),run_name='__main__')
    runpy.run_path(str(ROOT/'scripts/patch_economia_prodotta_history.py'),run_name='__main__')
    data=json.loads(SITE_DATA.read_text(encoding='utf-8')); metrics=data.setdefault('metrics',{})
    for k in ('businessValueAdded','labourProductivity'):
        if k not in metrics:raise RuntimeError(f'Indicatore esistente atteso non trovato: {k}')
        metrics[k]=metric(s,k,metrics[k])
    for k in NEW_KEYS:metrics[k]=metric(s,k)
    patch_theme(data);data['version']='v1.34.0';data['release_version']='1.34.0';data['updated']='10 settembre 2026';SITE_DATA.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');patch_registry(metrics)
    print('Economia prodotta v1.34.0 materializzata nel catalogo canonico.')

if __name__=='__main__':main()
