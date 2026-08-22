#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,sys,unicodedata
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit,urlunsplit
sys.path.insert(0,str(Path(__file__).resolve().parent))
import opportunity_radar_v024 as v024
v022=v024.v022;v021=v022.v021;base=v022.base
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONFIG=ROOT/'data'/'opportunity-sources.json';DEFAULT_BASE_RULES=ROOT/'data'/'opportunity-rules-v022.json';DEFAULT_RULES=ROOT/'data'/'opportunity-rules-v025.json';DEFAULT_PRESENTATION=ROOT/'data'/'opportunity-presentation-v024.json';DEFAULT_COVERAGE=ROOT/'data'/'opportunity-source-coverage-v025.json';DEFAULT_BACKTEST=ROOT/'data'/'opportunity-backtest-v025.json'

def fold(v:Any)->str:
 t=str(v or '').strip().lower();t=''.join(ch for ch in unicodedata.normalize('NFKD',t) if not unicodedata.combining(ch));return re.sub(r'[^a-z0-9]+',' ',t).strip()
def load_overlay(path:Path=DEFAULT_RULES):
 p=json.loads(path.read_text(encoding='utf-8'));rules,policy=v022.load_policy(path.parent/(p.get('baseRulesFile') or DEFAULT_BASE_RULES.name));m={r['id']:dict(r) for r in rules};order=[r['id'] for r in rules]
 for o in p.get('rules') or []:
  i=o.get('id');
  if not i: raise ValueError('Regola v0.2.5 senza id')
  if i not in m: order.append(i);m[i]={}
  m[i]={**m[i],**o,'_v025':True}
 return [m[i] for i in order],{**policy,**(p.get('qualityGate') or {})}
def load_json(path:Path):
 p=json.loads(path.read_text(encoding='utf-8'))
 if not isinstance(p,dict): raise ValueError(f'JSON non valido: {path}')
 return p
def normalized_url(v:Any)->str:
 t=str(v or '').strip()
 if not t:return ''
 p=urlsplit(t);path=re.sub(r'/+','/',p.path).rstrip('/') or '/';return urlunsplit((p.scheme.lower(),p.netloc.lower(),path,'',''))
def identity_key(i):
 r=str(i.get('rule_id') or '').strip()
 return f'rule:{r}' if r else f"title:{fold(i.get('title'))}|deadline:{i.get('deadline_at') or ''}"
def duplicate_key(i):
 t=fold(i.get('title'));d=str(i.get('deadline_at') or '')
 if t:return f'title:{t}|deadline:{d}'
 u=normalized_url(i.get('url'));return f'url:{u}' if u else identity_key(i)
def _completeness(i):return sum(bool(i.get(f)) for f in ('deadline_at','municipality_role','geographic_scope','project_requirements','eligibility_evidence','presentation','final_beneficiaries'))
def _priority(i,c):
 s=(c.get('sources') or {}).get(str(i.get('source_id') or '')) or {};return int(s.get('priority') or 0),_completeness(i)
def _merge_matrix(a,b):
 rank={'not_eligible':0,'review':1,'conditional':2,'eligible':3};t=a.setdefault('municipality_eligibility',{})
 for town,e in (b.get('municipality_eligibility') or {}).items():
  old=t.get(town)
  if not old or rank.get(e.get('status'),-1)>rank.get(old.get('status'),-1):t[town]=dict(e)
def deduplicate(items,cov):
 g={}
 for i in items:g.setdefault(duplicate_key(i),[]).append(i)
 out=[];groups=records=0
 for k,grp in g.items():
  ordered=sorted(grp,key=lambda x:_priority(x,cov),reverse=True);p=dict(ordered[0]);seen=[]
  for x in ordered:
   s=str(x.get('source_id') or '')
   if s and s not in seen:seen.append(s)
  p['also_seen_in']=seen;p['dedupe_key']=k
  for x in ordered[1:]:_merge_matrix(p,x)
  if len(grp)>1:groups+=1;records+=len(grp)-1
  out.append(p)
 out.sort(key=lambda x:(str(x.get('deadline_at') or '9999-99-99'),str(x.get('title') or '')))
 return out,{'inputRecords':len(items),'outputRecords':len(out),'duplicateGroups':groups,'recordsCollapsed':records}
def _archive_compact(i,today,reason='deadline_passed'):
 e=v024.archive_entry(i,today);e['archive_reason']=reason;e['identity_key']=identity_key(i);return e
def harden_continuity(current,previous,today):
 active={identity_key(i) for i in current};archive={};hold=[]
 for old in previous.get('archive') or []:
  k=str(old.get('identity_key') or identity_key(old))
  if k not in active:archive[k]=dict(old)
 for old in previous.get('opportunities') or []:
  k=identity_key(old)
  if k in active:continue
  dl=base.parse_date(old.get('deadline_at')) if old.get('deadline_at') else None
  if dl and dl<today:archive[k]=_archive_compact(old,today);continue
  hold.append({'identity_key':k,'title':old.get('title'),'source_id':old.get('source_id'),'deadline_at':old.get('deadline_at'),'url':old.get('url'),'reason':'Opportunità presente nel run precedente ma non più rilevata prima della scadenza: verificare revoca, spostamento o regressione della fonte.'})
 return sorted(archive.values(),key=lambda x:(str(x.get('deadline_at') or '0000-00-00'),str(x.get('title') or '')),reverse=True),hold
def build_coverage(result,registry):
 live={s.get('sourceId'):s for s in result.get('sources') or []};rows=[]
 for sid,m in (registry.get('sources') or {}).items():
  st=live.get(sid) or {};f=st.get('freshness') or {};rows.append({'source_id':sid,'label':m.get('label') or sid,'monitoringStatus':m.get('monitoringStatus'),'role':m.get('role'),'priority':m.get('priority'),'listingDiscovery':bool(m.get('listingDiscovery')),'detailEnrichment':bool(m.get('detailEnrichment')),'pdfFallback':bool(m.get('pdfFallback')),'archiveContinuity':bool(m.get('archiveContinuity')),'historicalReplay':bool(m.get('historicalReplay')),'runtimeStatus':st.get('status','not_run'),'freshness':f.get('status','unknown'),'observedDate':f.get('observedDate'),'publicCount':st.get('publicCount',0),'reviewCount':st.get('reviewCount',0),'qualityHoldCount':st.get('qualityHoldCount',0),'replacementNeeded':bool(m.get('replacementNeeded')),'note':m.get('note')})
 active=[r for r in rows if r['monitoringStatus']=='active'];degraded=[r for r in rows if r['monitoringStatus']=='degraded'];healthy=[r for r in active if r['runtimeStatus']=='ok' and r['freshness']=='current']
 return {'rows':rows,'summary':{'configured':len(rows),'active':len(active),'healthyActive':len(healthy),'degraded':len(degraded),'planned':len(registry.get('plannedSources') or [])},'plannedSources':registry.get('plannedSources') or []}
def predict_backtest_case(case,rules):
 rule=v021.matching_rule({'source_id':case.get('source_id'),'title':case.get('title')},rules)
 if not rule:return 'review',None
 role=rule.get('municipality_role','unknown')
 if role=='none' or rule.get('actionable') is False:return 'non_operational',rule.get('id')
 if rule.get('opportunity_type')=='non_financial_award' or rule.get('lifecycle_stage')=='implementation_only':return 'non_operational',rule.get('id')
 if rule.get('requires_versilia_nexus') and not case.get('versilia_nexus',False):return 'non_operational',rule.get('id')
 if role not in {'unknown',None,'none'} and (rule.get('force_eligibility') in {'eligible','conditional'} or rule.get('actionable')):return 'operational',rule.get('id')
 return 'review',rule.get('id')
def run_backtest(path,rules):
 p=load_json(path);tp=fp=tn=fn=0;rows=[];un=[]
 for c in p.get('cases') or []:
  pred,rid=predict_backtest_case(c,rules);exp=c.get('expected');ep=exp=='operational';pp=pred=='operational'
  if ep and pp:tp+=1
  elif ep:fn+=1
  elif pp:fp+=1
  else:tn+=1
  row={'id':c.get('id'),'title':c.get('title'),'source_id':c.get('source_id'),'expected':exp,'prediction':pred,'rule_id':rid,'official_url':c.get('official_url')};rows.append(row)
  if pred=='review':un.append(row)
 precision=tp/(tp+fp) if tp+fp else 1.;recall=tp/(tp+fn) if tp+fn else 1.;f1=2*precision*recall/(precision+recall) if precision+recall else 0.;th=p.get('thresholds') or {};passed=precision>=float(th.get('precision',0)) and recall>=float(th.get('recall',0))
 return {'windowDays':p.get('windowDays'),'scope':p.get('scope'),'cases':len(p.get('cases') or []),'confusion':{'tp':tp,'fp':fp,'tn':tn,'fn':fn},'precision':round(precision,4),'recall':round(recall,4),'f1':round(f1,4),'thresholds':th,'passed':passed,'unresolved':un,'rows':rows}
def _recompute_summary(r):
 towns=list(r.get('municipalitySummary') or {});s={}
 for town in towns:
  e=c=0
  for i in r.get('opportunities') or []:
   st=((i.get('municipality_eligibility') or {}).get(town) or {}).get('status');e+=st=='eligible';c+=st=='conditional'
  s[town]={'eligible':e,'conditional':c}
 r['municipalitySummary']=s
def run(config_path,today,*,payloads=None,detail_payloads=None,rules_path=DEFAULT_RULES,presentation_path=DEFAULT_PRESENTATION,coverage_path=DEFAULT_COVERAGE,backtest_path=DEFAULT_BACKTEST,previous_path=None):
 rules,policy=load_overlay(rules_path);cov=load_json(coverage_path);old=v022.load_policy;v022.load_policy=lambda _path=DEFAULT_BASE_RULES:(rules,policy)
 try:r=v024.run(config_path,today,payloads=payloads,detail_payloads=detail_payloads,rules_path=DEFAULT_BASE_RULES,presentation_path=presentation_path,previous_path=None)
 finally:v022.load_policy=old
 rows,ds=deduplicate(list(r.get('opportunities') or []),cov);r['opportunities']=rows;prev=v024.load_previous(previous_path);archive,hold=harden_continuity(rows,prev,today);r['archive']=archive;r['continuityHold']=hold;r['sourceCoverage']=build_coverage(r,cov);r['backtest']=run_backtest(backtest_path,rules);r['deduplication']=ds;r['schemaVersion']='2.5';r['hardeningVersion']='0.2.5';r['counts']['public']=len(rows);r['counts']['archive']=len(archive);r['counts']['continuityHold']=len(hold);r['counts']['duplicatesCollapsed']=ds['recordsCollapsed'];_recompute_summary(r);return r
def render_markdown(r):
 b=r.get('backtest') or {};c=(r.get('sourceCoverage') or {}).get('summary') or {};d=r.get('deduplication') or {};lines=['# Radar Opportunità Versilia — v0.2.5','',f"Data di riferimento: **{r.get('referenceDate')}**",'',f"Opportunità correnti: **{len(r.get('opportunities') or [])}** · archivio: **{len(r.get('archive') or [])}** · continuity hold: **{len(r.get('continuityHold') or [])}**.",f"Deduplicazione: **{d.get('recordsCollapsed',0)}** record collassati in **{d.get('duplicateGroups',0)}** gruppi.",f"Fonti: **{c.get('healthyActive',0)}/{c.get('active',0)}** fonti attive sane · **{c.get('degraded',0)}** degradate · **{c.get('planned',0)}** pianificate.",'','## Backtest 90 giorni','',f"Casi: **{b.get('cases',0)}** · precision **{b.get('precision',0):.1%}** · recall **{b.get('recall',0):.1%}** · F1 **{b.get('f1',0):.1%}** · esito **{'PASS' if b.get('passed') else 'FAIL'}**.",'']
 if b.get('unresolved'):
  lines+=['### Casi ancora non risolti','']+[f"- {x.get('title')} — atteso **{x.get('expected')}**, previsione **{x.get('prediction')}**" for x in b['unresolved']]+['']
 lines+=['## Copertura fonti','']+[f"- **{x['label']}** — monitoraggio `{x['monitoringStatus']}` · runtime `{x['runtimeStatus']}` · freshness `{x['freshness']}` · PDF fallback {'sì' if x['pdfFallback'] else 'no'}" for x in (r.get('sourceCoverage') or {}).get('rows') or []]+['','## Continuità','']
 lines+=['Nessuna opportunità è scomparsa prematuramente rispetto allo stato precedente.'] if not r.get('continuityHold') else [f"- **HOLD** {x.get('title')} — scadenza {x.get('deadline_at') or 'non rilevata'}" for x in r['continuityHold']]
 lines+=['','## Output corrente','']+[f"- {x.get('title')} — {x.get('deadline_at') or 'scadenza non rilevata'}" for x in r.get('opportunities') or []];return '\n'.join(lines)+'\n'
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=DEFAULT_CONFIG);p.add_argument('--rules',type=Path,default=DEFAULT_RULES);p.add_argument('--presentation',type=Path,default=DEFAULT_PRESENTATION);p.add_argument('--coverage',type=Path,default=DEFAULT_COVERAGE);p.add_argument('--backtest',type=Path,default=DEFAULT_BACKTEST);p.add_argument('--previous',type=Path);p.add_argument('--date',type=date.fromisoformat,default=date.today());p.add_argument('--output',type=Path);p.add_argument('--report',type=Path);p.add_argument('--backtest-only',action='store_true');a=p.parse_args(argv);rules,_=load_overlay(a.rules)
 if a.backtest_only:
  r=run_backtest(a.backtest,rules);print(json.dumps(r,ensure_ascii=False,indent=2));return 0 if r['passed'] else 3
 r=run(a.config,a.date,rules_path=a.rules,presentation_path=a.presentation,coverage_path=a.coverage,backtest_path=a.backtest,previous_path=a.previous)
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 rep=render_markdown(r)
 if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(rep,encoding='utf-8')
 elif not a.output:print(rep,end='')
 if any(s.get('status')=='error' for s in r.get('sources') or []):return 1
 if r.get('continuityHold'):return 2
 if not (r.get('backtest') or {}).get('passed'):return 3
 return 0
if __name__=='__main__':raise SystemExit(main())
