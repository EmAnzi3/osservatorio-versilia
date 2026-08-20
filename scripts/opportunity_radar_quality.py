#!/usr/bin/env python3
"""Filtro di qualità live per il prototipo Radar Opportunità Versilia.

Aggiunge arricchimento mirato delle sezioni Destinatari/Beneficiari evitando che
header, footer e testi estranei contaminino la classificazione.
"""
from __future__ import annotations
import re, sys
from datetime import date
from pathlib import Path
from typing import Callable

sys.path.insert(0,str(Path(__file__).resolve().parent))
import opportunity_radar as base
ORIG_GRANTS=base.collect_grants

AUDIENCE_KEYS=('destinatari / beneficiari','destinatari/beneficiari','destinatari','beneficiari','chi può partecipare','chi puo partecipare','soggetti beneficiari')
CLEAR_NON_MUNICIPAL=(r'\bpmi\b',r'\bstart[ -]?up\b',r'\bimprese\b',r'\bagenzie formative\b',r'\blavorator',r'\blavoratric',r'\bdatori di lavoro\b',r'\bpersone fisiche\b',r'\boperatori economici\b',r'\bprofessionist',r'\bstudent',r'\buniversit',r'\bscuole\b',r'\bagricoltor',r'\bpescator',r'\bapicoltor')

def audience_section(payload:str)->str:
    heads=list(re.finditer(r'<h[1-6][^>]*>(.*?)</h[1-6]\s*>',payload,re.I|re.S))
    for idx,m in enumerate(heads):
        h=base.norm(base.visible(m.group(1)))
        if not any(key in h for key in AUDIENCE_KEYS) or 'destinatari dei progetti' in h:continue
        candidates=[x.start() for x in heads[idx+1:]]
        for marker in re.finditer(r'<(?:footer|nav|/main)\b',payload[m.end():],re.I):candidates.append(m.end()+marker.start())
        stop=min(candidates) if candidates else len(payload)
        return base.visible(payload[m.end():stop])
    return ''

def clearly_non_municipal(text:str)->bool:
    t=base.norm(text)
    if any(re.search(p,t,re.I) for p in base.DIRECT):return False
    return any(re.search(p,t,re.I) for p in CLEAR_NON_MUNICIPAL)

def collect_html(source:dict,today:date,payload:str,loader:Callable[[str],str]|None=None):
    loader=loader or base.fetch
    p=base.Cards();p.feed(payload);p.close();out=[]
    for title,href,body in p.out:
        if len(title)<8 or base.norm(title) in base.IGNORE or not href:continue
        listing=f'{title}. {body}'
        prelim,_,_=base.eligibility(listing,source['_towns'])
        if prelim=='not_relevant' or (prelim=='review' and clearly_non_municipal(title)):continue
        url=base.urljoin(source['url'],href)
        detail='';audience=''
        if source.get('detailEnrichment'):
            try:
                detail=loader(url);audience=audience_section(detail)
            except Exception:
                detail=audience=''
        classify=f'{title}. {audience}' if audience else listing
        status,towns,reason=base.eligibility(classify,source['_towns'])
        if status=='review' and clearly_non_municipal(audience or title):status='not_relevant';towns=[];reason='I destinatari rilevati non sono amministrazioni comunali.'
        if status=='not_relevant':continue
        op,dl,pub=base.dates(listing)
        if detail and (not dl or not pub):
            dop,ddl,dpub=base.dates(base.visible(detail));op=op or dop;dl=dl or ddl;pub=pub or dpub
        if dl and date.fromisoformat(dl)<today:continue
        total,maximum=base.money(base.clean(f'{body}. {audience}'))
        item=base.opportunity(source,title,url,body,today,classify,op,dl,pub,total,maximum)
        item['eligibility']=status;item['municipalities']=towns;item['eligibility_reason']=reason;item['priority']=base.priority(status,dl,item['themes'],today)
        out.append(item)
    return out

def collect_grants(source:dict,today:date,payload:str,loader:Callable[[str],str]|None=None):
    loader=loader or base.fetch
    def focused(url:str)->str:
        raw=loader(url);section=audience_section(raw)
        return f'<h2>Destinatari</h2><p>{section}</p>' if section else '<p></p>'
    return ORIG_GRANTS(source,today,payload,focused)

base.collect_html=lambda source,today,payload: collect_html(source,today,payload,base.fetch)
base.collect_grants=lambda source,today,payload,detail_loader=None: collect_grants(source,today,payload,base.fetch)

if __name__=='__main__':raise SystemExit(base.main())
