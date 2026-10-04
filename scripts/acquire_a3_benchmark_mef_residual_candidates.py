#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from typing import Callable
import requests
import acquire_a3_benchmark_mef_candidates as base
import acquire_a3_benchmark_demography_candidates as dem

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'data/site-data.json'
LOCAL=ROOT/'data/source-snapshots/mef-income-lotto-a-2024.json'
POSAS=dem.POSAS_2026
def adult_scope(headers,rows,pred:Callable[[str],bool])->float:
    age_h=dem.pick(headers,('eta',)); total_h=dem.pick(headers,('totale',),('maschi','femmine'))
    total=0.0; matched=set()
    for row in rows:
        c=dem.code_of(row)
        if not pred(c): continue
        age=dem.age_number(row.get(age_h))
        if age is None or age==999 or age<18 or age>120: continue
        total+=dem.num(row.get(total_h)); matched.add(c)
    if total<=0 or not matched: raise RuntimeError('POSAS 18+: perimetro vuoto')
    return total
def public_reconcile(site,local):
    metric=site['metrics']['taxpayersAdultPopulationRate']; rows={r['town']:r for r in metric['rows']}; errors=[]
    if set(rows)!=set(local['towns']): errors.append('perimetro pubblico != snapshot 7/7')
    for town,d in local['towns'].items():
        adults=d.get('adultPopulation2026'); taxpayers=d.get('taxpayers'); expected=d.get('taxpayersPer100AdultResidents')
        if adults in (None,0) or taxpayers is None or expected is None: errors.append(f'{town}: componenti mancanti'); continue
        calc=float(taxpayers)/float(adults)*100
        if not math.isclose(calc,float(expected),abs_tol=1e-10): errors.append(f'{town}: snapshot formula mismatch')
        if town in rows and not math.isclose(float(rows[town]['value']),calc,abs_tol=1e-10): errors.append(f'{town}: pubblico {rows[town]["value"]} != {calc}')
    return errors
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args()
    session=requests.Session(); session.headers['User-Agent']='OsservatorioVersilia-A3-MEF-residual/1.0'
    calc_rows,calc_url,_=base.read(session,base.URL_CANDIDATES['calc']); type_rows,type_url,_=base.read(session,base.URL_CANDIDATES['type'])
    calc,_=base.totals(calc_rows); base.totals(type_rows)
    cr=next(iter(calc.values())); contrib=base.header(cr,'numero contribuenti')
    tus_tax=base.sumfield({'Toscana':calc['Toscana']},contrib); ita_tax=base.sumfield(calc,contrib)
    ph,pr,_=dem.download_rows(session,POSAS)
    tus_adults=adult_scope(ph,pr,dem.pred_tuscany); ita_adults=adult_scope(ph,pr,dem.pred_italy)
    site=json.loads(SITE.read_text(encoding='utf-8')); local=json.loads(LOCAL.read_text(encoding='utf-8')); errors=public_reconcile(site,local)
    benchmark={'year':'MEF a.i. 2024 · residenti 1.1.2026','unit':'per100','formula':'numero contribuenti MEF / residenti 18+ POSAS × 100','tuscany':tus_tax/tus_adults*100,'italy':ita_tax/ita_adults*100,'raw':{'tuscany':{'taxpayers':tus_tax,'adultPopulation2026':tus_adults},'italy':{'taxpayers':ita_tax,'adultPopulation2026':ita_adults}}}
    sanity=70<benchmark['tuscany']<110 and 70<benchmark['italy']<110
    payload={'schemaVersion':1,'publisher':'MEF — Dipartimento Finanze / Istat POSAS','profileId':'mef-irpef-annual','status':'ACQUIRED_CANDIDATE' if not errors and sanity else 'CANDIDATE_REJECTED','sources':{'mefCalc':calc_url,'mefType':type_url,'posas':POSAS},'benchmarks':{'taxpayersAdultPopulationRate':benchmark},'qualityGate':{'status':'PASS' if not errors and sanity else 'FAIL','publicReconciliation':'7/7 PASS' if not errors else 'FAIL','errors':errors,'sanity':sanity},'blocked':{'income':'contratto pubblico non riconciliato con il candidato regionale; non forzato','incomeDistribution':'mapping regionale alle quattro fasce pubbliche ancora da certificare'}}
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':payload['status'],'metrics':['taxpayersAdultPopulationRate'],'tuscany':benchmark['tuscany'],'italy':benchmark['italy'],'gate':payload['qualityGate']},ensure_ascii=False))
if __name__=='__main__': main()
