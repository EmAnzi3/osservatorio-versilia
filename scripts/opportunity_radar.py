#!/usr/bin/env python3
"""Radar Opportunità Versilia v0.1: collector sperimentale, nessuna pubblicazione."""
from __future__ import annotations
import argparse, hashlib, html, json, re, sys, urllib.error, urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONFIG=ROOT/'data'/'opportunity-sources.json'
UA='OsservatorioVersilia-OpportunityRadar/0.1 (+https://osservatorioversilia.it/)'
TOWNS=['Camaiore','Forte dei Marmi','Massarosa','Pietrasanta','Seravezza','Stazzema','Viareggio']
MONTHS={'gennaio':1,'febbraio':2,'marzo':3,'aprile':4,'maggio':5,'giugno':6,'luglio':7,'agosto':8,'settembre':9,'ottobre':10,'novembre':11,'dicembre':12}
DIRECT=(r'\benti locali\b',r'\bcomuni\b',r'\bamministrazioni pubbliche locali\b',r'\bunioni dei comuni\b')
CONDITIONAL=(r'\benti pubblici\b',r'\bsoggetti pubblici\b',r'\bamministrazioni pubbliche\b',r'\bpartnership\b.*\bsoggetti pubblici\b')
EXCLUDED=(r'\bliber[ei] professionist',r'\bimprese\b',r'\bscuole\b',r'\buniversit',r'\bstudent',r'\baziende\b')
THEMES={'ambiente':('ambiente','amianto','rifiuti','energia','clima','bonifica'),'opere-pubbliche':('opere pubbliche','edifici pubblici','infrastrutture','sism'),'digitale':('digitale','cloud','pagopa','app io','pdnd','notifiche'),'sociale':('sociale','welfare','giovani','comunità','comunita'),'cultura':('cultura','culturale','patrimonio','restauro')}
IGNORE={'filtra la ricerca','cerca nel sito','bandi in corso e in arrivo','informazioni e contatti','contatti','informazioni','allegati','documenti','come partecipare','navigazione'}

def clean(s:Any)->str:return re.sub(r'\s+',' ',html.unescape(str(s or ''))).strip()
def norm(s:Any)->str:return clean(s).casefold().replace('’',"'")
def sid(source,title,url):return 'opp-'+hashlib.sha256(f'{source}|{norm(title)}|{url}'.encode()).hexdigest()[:14]
def fp(*parts):return hashlib.sha256('|'.join(clean(x) for x in parts).encode()).hexdigest()
def now():return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

class Cards(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.out=[];self.h=None;self.href=None;self.hp=[];self.bp=[];self.inh=False
 def flush(self):
  if self.h:self.out.append((self.h,self.href,clean(' '.join(self.bp))))
  self.bp=[]
 def handle_starttag(self,t,a):
  t=t.lower()
  if t in {'h2','h3','h4'}:self.flush();self.inh=True;self.hp=[];self.href=None
  if self.inh and t=='a':self.href=dict(a).get('href')
 def handle_endtag(self,t):
  if self.inh and t.lower() in {'h2','h3','h4'}:self.h=clean(' '.join(self.hp));self.inh=False
 def handle_data(self,d):(self.hp if self.inh else self.bp if self.h else []).append(d)
 def close(self):super().close();self.flush()

class JsonLd(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=False);self.out=[];self.on=False;self.buf=[]
 def handle_starttag(self,t,a):
  if t.lower()=='script' and {k.lower():(v or '') for k,v in a}.get('type','').lower()=='application/ld+json':self.on=True;self.buf=[]
 def handle_data(self,d):
  if self.on:self.buf.append(d)
 def handle_endtag(self,t):
  if t.lower()=='script' and self.on:self.out.append(''.join(self.buf));self.on=False;self.buf=[]

class Visible(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.out=[];self.skip=0
 def handle_starttag(self,t,a):
  if t.lower() in {'script','style','noscript','svg'}:self.skip+=1
 def handle_endtag(self,t):
  if t.lower() in {'script','style','noscript','svg'} and self.skip:self.skip-=1
 def handle_data(self,d):
  if not self.skip:self.out.append(d)

def visible(payload):p=Visible();p.feed(payload);p.close();return clean(' '.join(p.out))
def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/json;q=0.9,*/*;q=0.8'})
 with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode(r.headers.get_content_charset() or 'utf-8','replace')

def parse_date(s):
 s=clean(s).strip(' .,')
 for f in ('%d.%m.%Y','%d/%m/%Y','%Y-%m-%d'):
  try:return datetime.strptime(s,f).date()
  except ValueError:pass
 m=re.fullmatch(r'(\d{1,2})\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})',s)
 if not m or m.group(2).casefold() not in MONTHS:return None
 try:return date(int(m.group(3)),MONTHS[m.group(2).casefold()],int(m.group(1)))
 except ValueError:return None

def dates(text):
 text=clean(text);op=dl=pub=None
 m=re.search(r'Pubblicato il\s+(\d{1,2}[./]\d{1,2}[./]\d{4})',text,re.I)
 if m and (d:=parse_date(m.group(1))):pub=d.isoformat()
 m=re.search(r'Scadenza(?:\s+presentazione\s+domande)?\s+(\d{1,2}[./]\d{1,2}[./]\d{4})',text,re.I)
 if m and (d:=parse_date(m.group(1))):dl=d.isoformat()
 for pat in (r'\bdal\s+(\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\s+al\s+(\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})',r'\bdal\s+(\d{1,2}[./]\d{1,2}[./]\d{4})\s+al\s+(\d{1,2}[./]\d{1,2}[./]\d{4})'):
  m=re.search(pat,text,re.I)
  if m:
   a,b=parse_date(m.group(1)),parse_date(m.group(2));op=a.isoformat() if a else op;dl=b.isoformat() if b else dl;break
 return op,dl,pub

def amount(s,millions=False):
 s=clean(s).replace('€','').replace(' ','')
 if not re.search(r'\d',s):return None
 if ',' in s:s=s.replace('.','').replace(',','.')
 elif s.count('.')>1 or (s.count('.')==1 and len(s.rsplit('.',1)[1])==3):s=s.replace('.','')
 try:v=float(s)
 except ValueError:return None
 return v*1_000_000 if millions else v

def money(text):
 text=clean(text)
 a=re.search(r'(?:risorse|dotazione|budget)[^€\d]{0,40}(?:€\s*)?([0-9][0-9.\s]*(?:,[0-9]+)?)\s*(milion[ei])?',text,re.I)
 b=re.search(r'(?:importo massimo|max(?:imum)?)[^€\d]{0,40}(?:€\s*)?([0-9][0-9.\s]*(?:,[0-9]+)?)',text,re.I)
 return (amount(a.group(1),bool(a.group(2))) if a else None,amount(b.group(1)) if b else None)

def themes(text):
 t=norm(text);return [k for k,vals in THEMES.items() if any(v in t for v in vals)]
def eligibility(text,towns):
 t=norm(text);direct=any(re.search(p,t,re.I) for p in DIRECT);cond=any(re.search(p,t,re.I) for p in CONDITIONAL);exc=any(re.search(p,t,re.I) for p in EXCLUDED)
 if direct:return 'eligible',towns[:],'Il testo della fonte indica esplicitamente Comuni o enti locali tra i destinatari.'
 if cond:return 'conditional',towns[:],'La fonte ammette soggetti pubblici, ma sono presenti condizioni da verificare sul bando completo.'
 if exc:return 'not_relevant',[],'I destinatari espliciti non sono amministrazioni comunali.'
 return 'review',[],'Il testo disponibile non consente di confermare i destinatari comunali.'
def priority(e,dl,ths,today):
 if e=='not_relevant':return 'low'
 days=(date.fromisoformat(dl)-today).days if dl and re.fullmatch(r'\d{4}-\d{2}-\d{2}',dl) else None
 if e=='eligible' and (days is None or days>=10) and ths:return 'high'
 return 'medium' if e in {'eligible','conditional'} else 'low'

def opportunity(source,title,url,summary,today,full='',opens=None,deadline=None,published=None,total=None,maximum=None):
 full=clean(full or f'{title}. {summary}');e,towns,reason=eligibility(full,source['_towns']);ths=themes(full)
 return {'id':sid(source['id'],title,url),'source_id':source['id'],'source_name':source['name'],'publisher':source['publisher'],'title':clean(title),'url':url,'summary':clean(summary)[:700],'status':'open','opens_at':opens,'deadline_at':deadline,'published_at':published,'beneficiary_text':full[:900],'municipalities':towns,'eligibility':e,'eligibility_reason':reason,'themes':ths,'funding_total_eur':total,'max_contribution_eur':maximum,'cofunding_text':None,'priority':priority(e,deadline,ths,today),'detected_at':now(),'fingerprint':fp(source['id'],title,summary,deadline,e)}

def collect_html(source,today,payload):
 p=Cards();p.feed(payload);p.close();out=[]
 for title,href,body in p.out:
  if len(title)<8 or norm(title) in IGNORE:continue
  full=f'{title}. {body}';e,_,_=eligibility(full,source['_towns'])
  if e=='not_relevant':continue
  op,dl,pub=dates(full)
  if dl and date.fromisoformat(dl)<today:continue
  total,maximum=money(full);out.append(opportunity(source,title,urljoin(source['url'],href) if href else source['url'],body,today,full,op,dl,pub,total,maximum))
 return out

def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def grants(payload):
 p=JsonLd();p.feed(payload);p.close();out=[]
 for block in p.out:
  try:x=json.loads(block)
  except json.JSONDecodeError:continue
  for n in walk(x):
   typ=n.get('@type');types=typ if isinstance(typ,list) else [typ]
   if any(norm(v)=='grant' for v in types if v):out.append(n)
 return out

def collect_grants(source,today,payload,detail_loader:Callable[[str],str]|None=None):
 out=[];seen=set()
 for n in grants(payload):
  title=clean(n.get('name'));url=clean(n.get('url') or n.get('@id') or source['url']).split('#',1)[0]
  if not title or url in seen:continue
  seen.add(url);summary=clean(n.get('description'));pub=clean(n.get('datePublished')) or None;dl=clean(n.get('expires')) or None
  pd=parse_date(pub) if pub else None;dd=parse_date(dl) if dl else None;pub=pd.isoformat() if pd else pub;dl=dd.isoformat() if dd else dl
  if dd and dd<today:continue
  detail=''
  if source.get('detailEnrichment') and detail_loader:
   try:detail=visible(detail_loader(url))
   except (urllib.error.URLError,TimeoutError,ValueError):pass
  full=clean(f'{title}. {summary}. {detail}');e,_,_=eligibility(full,source['_towns'])
  if e=='not_relevant':continue
  total,maximum=money(full);out.append(opportunity(source,title,url,summary,today,full,pub,dl,pub,total,maximum))
 return out

def collect_pad(source,today,payload):
 raw=json.loads(payload)
 if not isinstance(raw,list):raise ValueError('Il dataset PA digitale non è una lista JSON.')
 out=[]
 for x in raw:
  if not isinstance(x,dict) or 'comuni' not in norm(x.get('soggetti_destinatari')):continue
  end=clean(x.get('data_fine_bando')) or None
  if norm(x.get('stato')) in {'terminato','chiuso'} or (end and re.fullmatch(r'\d{4}-\d{2}-\d{2}',end) and date.fromisoformat(end)<today):continue
  title=clean(x.get('titolo'))
  if not title:continue
  measure=clean(x.get('misura'));total=x.get('totale_importo_stanziato');total=float(total) if isinstance(total,(int,float)) else None
  item=opportunity(source,title,'https://www.padigitale2026.gov.it/enti/comuni',measure,today,f'{title}. {measure}. Comuni',clean(x.get('data_inizio_bando')) or None,end,None,total,None)
  item['eligibility']='eligible';item['municipalities']=source['_towns'][:];item['eligibility_reason']='Il dataset PA digitale 2026 indica i Comuni tra i soggetti destinatari.';item['themes']=item['themes'] or ['digitale'];item['priority']=priority('eligible',end,item['themes'],today);out.append(item)
 return out

def run(config_path:Path,today:date,payloads:dict[str,str]|None=None,detail_payloads:dict[str,str]|None=None):
 cfg=json.loads(config_path.read_text(encoding='utf-8'));towns=list(cfg.get('municipalities') or TOWNS);payloads=payloads or {};detail_payloads=detail_payloads or {};all_items=[];states=[]
 def detail(url):
  if url in detail_payloads:return detail_payloads[url]
  return '' if payloads else fetch(url)
 for raw in cfg['sources']:
  s={**raw,'_towns':towns}
  try:
   body=payloads.get(s['id']);body=fetch(s['url']) if body is None else body
   items=collect_html(s,today,body) if s['type']=='html_cards' else collect_grants(s,today,body,detail) if s['type']=='jsonld_grants' else collect_pad(s,today,body) if s['type']=='padigitale_json' else (_ for _ in ()).throw(ValueError(f"Tipo non supportato: {s['type']}"))
   all_items+=items;states.append({'sourceId':s['id'],'status':'ok','count':len(items),'error':None})
  except (ValueError,json.JSONDecodeError,urllib.error.URLError,TimeoutError) as exc:states.append({'sourceId':s['id'],'status':'error','count':0,'error':str(exc)})
 chosen={}
 for x in all_items:
  k=(x['source_id'],norm(x['title']));chosen[k]=x if k not in chosen or len(x['summary'])>len(chosen[k]['summary']) else chosen[k]
 items=sorted(chosen.values(),key=lambda x:(x['deadline_at'] or '9999-12-31',norm(x['title'])))
 counts={'total':len(items),'eligible':sum(x['eligibility']=='eligible' for x in items),'conditional':sum(x['eligibility']=='conditional' for x in items),'review':sum(x['eligibility']=='review' for x in items),'highPriority':sum(x['priority']=='high' for x in items)}
 return {'schemaVersion':1,'generatedAt':now(),'referenceDate':today.isoformat(),'municipalities':towns,'counts':counts,'sources':states,'opportunities':items}

def report(r):
 c=r['counts'];lines=['# Radar Opportunità Versilia — prototipo','',f"Data di riferimento: **{r['referenceDate']}**",'',f"Opportunità trattenute: **{c['total']}** · ammissibili: **{c['eligible']}** · condizionate: **{c['conditional']}** · da verificare: **{c['review']}**.",'','## Fonti','']
 for s in r['sources']:lines.append(f"- **{'OK' if s['status']=='ok' else 'ERRORE'}** `{s['sourceId']}`: {s['count']} opportunità"+(f" — {s['error']}" if s['error'] else ''))
 lines+=['','## Opportunità','']
 for x in r['opportunities']:lines += [f"### {x['title']}",f"- Fonte: {x['source_name']}",f"- Ammissibilità: **{x['eligibility']}** — {x['eligibility_reason']}",f"- Priorità provvisoria: **{x['priority']}**",f"- Scadenza: **{x['deadline_at'] or 'non rilevata'}**",f"- Temi: {', '.join(x['themes']) if x['themes'] else 'da classificare'}",f"- URL: {x['url']}",'']
 if not r['opportunities']:lines.append('Nessuna opportunità pertinente rilevata.')
 return '\n'.join(lines).rstrip()+'\n'

def main():
 p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=DEFAULT_CONFIG);p.add_argument('--date',default=date.today().isoformat());p.add_argument('--output',type=Path);p.add_argument('--report',type=Path);a=p.parse_args();r=run(a.config,date.fromisoformat(a.date));txt=json.dumps(r,ensure_ascii=False,indent=2)+'\n'
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(txt,encoding='utf-8')
 else:sys.stdout.write(txt)
 if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(report(r),encoding='utf-8')
 return 1 if any(s['status']=='error' for s in r['sources']) else 0
if __name__=='__main__':raise SystemExit(main())
