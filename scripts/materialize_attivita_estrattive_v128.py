#!/usr/bin/env python3
"""Materializza Attività estrattive v1.28.0 da RTCave pubblico + PRC Regione Toscana."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import urllib.request
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'data/site-data.json'
REGISTRY = ROOT / 'data/source-registry.json'
STATE = ROOT / 'data/source-monitor-state.json'
SNAP = ROOT / 'data/source-snapshots/attivita-estrattive-v128.json'
FINAL = ROOT / 'scripts/finalize_catalog_release.py'
README = ROOT / 'README.md'
APP00 = ROOT / 'assets/app-parts/00.txt'
APP03 = ROOT / 'assets/app-parts/03.txt'
APP05 = ROOT / 'assets/app-parts/05.txt'
SERVICE_WORKER = ROOT / 'service-worker.js'
BUILD_SAFE = ROOT / 'scripts/build_static_safe.py'
BUILD_BRAND = ROOT / 'scripts/build_static_brand.py'
EXPORT = ROOT / 'assets/export-v161.js'
UX = ROOT / 'assets/ux-history.js'

RTCAVE_URL = 'https://cave.regione.toscana.it/api/v1/cave_public'
RTCAVE_PAGE = 'https://cave.regione.toscana.it/'
PRC_URL = 'https://www.regione.toscana.it/piano-regionale-cave'
PRC_MONITOR_URL = 'https://www.regione.toscana.it/it/-/monitoraggio-del-piano-regionale-cave'
KEYS = ('extractiveSites', 'extractiveProduction', 'extractivePlanning')
VERSILIA_CODES = ('046005','046013','046018','046024','046028','046030','046033')
OLD_TOKEN = '20260901-v127-demanio-marittimo'
NEW_TOKEN = '20260902-v128-attivita-estrattive'

PRODUCTION = {
    '046028': {
        'town': 'Seravezza',
        'years': [2019,2020,2021,2022,2023,2024,2025],
        'values': [31151,46093,52048,57199,53518,53194,55801],
        'components': [
            {'year':2019,'bacinoSeravezza':31151}, {'year':2020,'bacinoSeravezza':46093},
            {'year':2021,'bacinoSeravezza':52048}, {'year':2022,'bacinoSeravezza':57199},
            {'year':2023,'bacinoSeravezza':53518}, {'year':2024,'bacinoSeravezza':53194},
            {'year':2025,'bacinoSeravezza':55801},
        ],
        'materials2025': [{'label':'Marmi per uso ornamentale','value':55801,'unit':'cubicMetres'}],
        'ops2019_2038': 1680487,
    },
    '046030': {
        'town': 'Stazzema',
        'years': [2019,2020,2021,2022,2023,2024,2025],
        'values': [19894,13619,17804,31658,25328,38372,23651],
        'components': [
            {'year':2019,'bacinoStazzema':12680,'cardosoApuane':7214,'total':19894},
            {'year':2020,'bacinoStazzema':8547,'cardosoApuane':5072,'total':13619},
            {'year':2021,'bacinoStazzema':11840,'cardosoApuane':5964,'total':17804},
            {'year':2022,'bacinoStazzema':25350,'cardosoApuane':6308,'total':31658},
            {'year':2023,'bacinoStazzema':17552,'cardosoApuane':7776,'total':25328},
            {'year':2024,'bacinoStazzema':33875,'cardosoApuane':4497,'total':38372},
            {'year':2025,'bacinoStazzema':21479,'cardosoApuane':2172,'total':23651},
        ],
        'materials2025': [
            {'label':'Marmi per uso ornamentale','value':21479,'unit':'cubicMetres'},
            {'label':'Metarenarie e quarziti per uso ornamentale','value':2172,'unit':'cubicMetres'},
        ],
        'ops2019_2038': 1504871,
    },
}

PRC = {
    '046005': {'town':'Camaiore','municipalKm2':84.69,'g':(0,0.0,0.0),'gp':(0,0.0,0.0),'acc':(0,0.0,0.0),'mos':2,'pmos':3,'sed':25},
    '046013': {'town':'Forte dei Marmi','municipalKm2':9.14,'g':(0,0.0,0.0),'gp':(0,0.0,0.0),'acc':(0,0.0,0.0),'mos':0,'pmos':0,'sed':0},
    '046018': {'town':'Massarosa','municipalKm2':68.56,'g':(0,0.0,0.0),'gp':(0,0.0,0.0),'acc':(0,0.0,0.0),'mos':0,'pmos':0,'sed':53},
    '046024': {'town':'Pietrasanta','municipalKm2':41.99,'g':(0,0.0,0.0),'gp':(1,11.390,0.271),'acc':(0,0.0,0.0),'mos':0,'pmos':0,'sed':22},
    '046028': {'town':'Seravezza','municipalKm2':39.36,'g':(2,37.976,0.965),'gp':(0,0.0,0.0),'acc':(7,156.322,3.971),'mos':1,'pmos':7,'sed':105},
    '046030': {'town':'Stazzema','municipalKm2':80.70,'g':(1,19.021,0.236),'gp':(0,0.0,0.0),'acc':(12,400.173,4.959),'mos':4,'pmos':0,'sed':151},
    '046033': {'town':'Viareggio','municipalKm2':32.42,'g':(0,0.0,0.0),'gp':(0,0.0,0.0),'acc':(0,0.0,0.0),'mos':0,'pmos':0,'sed':0},
}
PRC_AGG = {'g':(3,56.997,0.160),'gp':(1,11.390,0.032),'acc':(19,556.495,1.559)}


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def replace(path: Path, old: str, new: str, *, once: bool = False, optional: bool = False):
    text = path.read_text(encoding='utf-8')
    if new in text and old not in text:
        return
    if old not in text:
        if optional:
            return
        raise RuntimeError(f'Token non trovato in {path}: {old[:100]}')
    path.write_text(text.replace(old, new, 1 if once else -1), encoding='utf-8')


def fetch_rtcave():
    req = urllib.request.Request(RTCAVE_URL, headers={'User-Agent':'OsservatorioVersilia/1.28 (+https://osservatorioversilia.it)'})
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()
        status = getattr(response, 'status', 200)
        final_url = response.geturl()
        content_type = response.headers.get('Content-Type','')
    payload = json.loads(raw.decode('utf-8'))
    rows = payload.get('data') or []
    if payload.get('ok') is not True or len(rows) != 666:
        raise RuntimeError(f'RTCave: universo inatteso ok={payload.get("ok")} records={len(rows)}')
    codes = [str(r.get('codice_rt') or '') for r in rows]
    ids = [r.get('id_cava') for r in rows]
    if len(set(codes)) != 666 or len(set(ids)) != 666:
        raise RuntimeError('RTCave: identificativi non univoci')
    selected = [r for r in rows if str(r.get('cod_istat') or '').zfill(6) in VERSILIA_CODES]
    if len(selected) != 90:
        raise RuntimeError(f'RTCave: attesi 90 record Versilia, trovati {len(selected)}')
    expected_town = {'046005':0,'046013':0,'046018':1,'046024':2,'046028':44,'046030':43,'046033':0}
    got = Counter(str(r.get('cod_istat') or '').zfill(6) for r in selected)
    if {k:got.get(k,0) for k in expected_town} != expected_town:
        raise RuntimeError(f'RTCave: distribuzione comunale inattesa {got}')
    expected_states = {'Attiva':15,'Inattiva':2,'Sospesa':5,'Scaduta':3,'Ripristino':0,'Chiusa':64,None:1}
    states = Counter(r.get('stato') for r in selected)
    if {k:states.get(k,0) for k in expected_states} != expected_states:
        raise RuntimeError(f'RTCave: distribuzione stati inattesa {states}')
    return raw, rows, selected, {'status':status,'finalUrl':final_url,'contentType':content_type}


def slug_map(site):
    out = {}
    for metric in site.get('metrics',{}).values():
        for row in metric.get('rows',[]):
            if row.get('code') and row.get('slug'):
                out.setdefault(row['code'], row['slug'])
    for t in site['towns']:
        out.setdefault(t['code'], t['name'].lower().replace(' ','-'))
    return out


def count_value(rows, predicate):
    return sum(1 for r in rows if predicate(r))


def rtcave_parts(rows):
    specs = [
        ('total','Siti RTCave totali','Tutti',lambda r: True),
        ('state_active','Siti attivi','Stato · Attivi',lambda r:r.get('stato')=='Attiva'),
        ('state_inactive','Siti inattivi','Stato · Inattivi',lambda r:r.get('stato')=='Inattiva'),
        ('state_suspended','Siti sospesi','Stato · Sospesi',lambda r:r.get('stato')=='Sospesa'),
        ('state_expired','Siti scaduti','Stato · Scaduti',lambda r:r.get('stato')=='Scaduta'),
        ('state_restoration','Siti in ripristino','Stato · Ripristino',lambda r:r.get('stato')=='Ripristino'),
        ('state_closed','Siti chiusi','Stato · Chiusi',lambda r:r.get('stato')=='Chiusa'),
        ('state_nd','Stato non disponibile','Stato · n.d.',lambda r:r.get('stato') in (None,'')),
        ('type_ordinary','Cava ordinaria','Tipologia · Cava ordinaria',lambda r:r.get('tipologia')=='Cava Ordinaria'),
        ('type_restoreworks','Opere di ripristino','Tipologia · Opere di ripristino',lambda r:r.get('tipologia')=='Opere di ripristino'),
        ('type_recovery','Piano di recupero','Tipologia · Piano di recupero',lambda r:r.get('tipologia')=='Piano di recupero'),
        ('prod_ornamental','Classe produttiva ornamentale','Produzione · Ornamentale',lambda r:r.get('tipo_produzione')=='ORNAMENTALE'),
        ('prod_industrial','Classe produttiva industriale','Produzione · Industriale',lambda r:r.get('tipo_produzione')=='INDUSTRIALE'),
        ('prod_construction','Classe produttiva costruzione','Produzione · Costruzione',lambda r:r.get('tipo_produzione')=='COSTRUZIONE'),
    ]
    return [{'key':k,'label':label,'selectorLabel':sel,'unit':'number','value':count_value(rows,pred)} for k,label,sel,pred in specs]


def breakdown(rows, field):
    c=Counter(('n.d.' if r.get(field) in (None,'') else str(r.get(field))) for r in rows)
    return [{'label':k,'count':v} for k,v in sorted(c.items(), key=lambda kv:(-kv[1],kv[0]))]


def build_sites_metric(site, selected):
    slugs=slug_map(site); by_code={code:[] for code in VERSILIA_CODES}
    for r in selected: by_code[str(r.get('cod_istat')).zfill(6)].append(r)
    rows=[]
    town_by_code={t['code']:t for t in site['towns']}
    for code in [t['code'] for t in site['towns']]:
        rr=sorted(by_code.get(code,[]), key=lambda r:(str(r.get('nome_cava') or ''),str(r.get('codice_rt') or '')))
        parts=rtcave_parts(rr)
        detail={
            'recordCount':len(rr),
            'statusBreakdown':breakdown(rr,'stato'),
            'typeBreakdown':breakdown(rr,'tipologia'),
            'productionBreakdown':breakdown(rr,'tipo_produzione'),
            'comprensorioBreakdown':breakdown(rr,'nome_comprensorio'),
            'giacimentoBreakdown':breakdown(rr,'nome_giacimento'),
            'records':rr,
        }
        rows.append({'town':town_by_code[code]['name'],'code':code,'slug':slugs[code],'value':len(rr),'formatted':str(len(rr)),'series':None,'normalized':None,'benchmarkValue':len(rr),'parts':parts,'extractiveDetail':detail})
    agg_parts=rtcave_parts(selected)
    return {
        'meta':{
            'key':'extractiveSites','theme':'ambiente','label':'Siti censiti in RTCave','shortLabel':'Siti RTCave',
            'description':'Siti presenti nella banca dati pubblica RTCave alla data dello snapshot. La card mantiene separati stato, tipologia e classe produttiva e conserva l’anagrafica pubblica di ciascun record.',
            'unit':'number','year':'2 settembre 2026','source':'Regione Toscana — RTCave','polarity':'neutral','detailGroup':'extractive',
            'searchTerms':['cave','cava','rtcave','attività estrattive','marmo','lapideo','siti estrattivi','cave attive','cave chiuse'],
            'sourceMeta':{'snapshot':'data/source-snapshots/attivita-estrattive-v128.json','note':'Snapshot dell’endpoint pubblico anonimo RTCave. I valori null restano n.d.; Chiusa, Inattiva e SED non sono sinonimi.'},
            'compositeType':'securityMeasures','selectorLabel':'Lettura','comparisonReference':'aggregate','comparisonDifference':'shareOfAggregate','comparisonLabel':'Versilia','comparisonOverline':'Peso sulla Versilia','comparisonNote':'Quota del numero di record RTCave del Comune sul totale dei sette Comuni per la lettura selezionata.'
        },
        'sourceUrl':RTCAVE_URL,
        'sourceUrls':{'rtcave':RTCAVE_URL,'publicMap':RTCAVE_PAGE},
        'rows':rows,
        'aggregate':{'value':len(selected),'label':'Versilia · siti RTCave','parts':agg_parts,'note':'Conteggio di record distinti per codice_rt nei sette Comuni; non equivale necessariamente al numero di cave fisiche indipendenti.'},
        'normalizedAggregate':None,
        'method':{
            'type':'Snapshot dell’endpoint pubblico Regione Toscana RTCave',
            'formula':'COUNT(DISTINCT codice_rt) per Comune. Selector di stato, tipologia e classe produttiva applicati ai valori originali del JSON; null mantenuti come n.d.',
            'caveat':'codice_rt identifica univocamente il record RTCave, non necessariamente una cava fisica indipendente da record contigui o articolati. Chiusa non viene reinterpretata come dismessa; Ornamentale è una macro-classe produttiva RTCave, non una litologia.',
            'coverage':'7/7',
            'snapshot':'data/source-snapshots/attivita-estrattive-v128.json'
        }
    }


def build_production_metric(site):
    slugs=slug_map(site); town_by_code={t['code']:t for t in site['towns']}; rows=[]
    aggregate_years=list(next(iter(PRODUCTION.values()))['years'])
    aggregate_values=[sum(PRODUCTION[code]['values'][i] for code in PRODUCTION) for i in range(len(aggregate_years))]
    for code in [t['code'] for t in site['towns']]:
        info=PRODUCTION.get(code)
        if info:
            val=info['values'][-1]
            rows.append({'town':town_by_code[code]['name'],'code':code,'slug':slugs[code],'value':val,'formatted':f'{val:,}'.replace(',','.'),'series':{'years':info['years'],'values':info['values']},'normalized':None,'benchmarkValue':None,'productionDetail':info})
        else:
            rows.append({'town':town_by_code[code]['name'],'code':code,'slug':slugs[code],'value':None,'formatted':'n.d.','series':None,'normalized':None,'benchmarkValue':None,'dataUnavailable':True,'availabilityNote':'Produzione comunale non ricostruibile in modo omogeneo dal monitoraggio PRC; nessuno zero viene inferito.'})
    return {
        'meta':{
            'key':'extractiveProduction','theme':'ambiente','label':'Produzione estrattiva','shortLabel':'Produzione estrattiva',
            'description':'Volume effettivamente estratto comunicato con gli Obblighi Informativi e pubblicato dal monitoraggio PRC. La serie è mostrata solo dove il raccordo comprensorio→Comune è certo.',
            'unit':'cubicMetres','year':'2025','source':'Regione Toscana — Monitoraggio Piano Regionale Cave','polarity':'neutral','detailGroup':'extractive',
            'searchTerms':['produzione cave','volume estratto','marmo estratto','materiale estratto','prc','obblighi informativi'],
            'sourceMeta':{'snapshot':'data/source-snapshots/attivita-estrattive-v128.json','note':'Serie 2019–2025 verificata per Seravezza e Stazzema. L’aggregato è la somma aritmetica dei soli valori comunali pubblicati (copertura 2/7); gli altri cinque Comuni restano n.d.'},
            'comparisonReference':'aggregate','comparisonDifference':'shareOfAggregate','comparisonLabel':'somma pubblicata','comparisonOverline':'Peso sulla produzione rilevata','comparisonNote':'Quota del Comune sulla somma dei valori comunali effettivamente pubblicati. Copertura 2/7: i cinque Comuni senza dato restano n.d. e non vengono trattati come zero.'
        },
        'sourceUrl':PRC_MONITOR_URL,
        'rows':rows,
        'aggregate':{'value':aggregate_values[-1],'label':'Versilia · somma valori comunali disponibili (2/7)','series':{'years':aggregate_years,'values':aggregate_values},'coverage':'2/7','note':'Somma aritmetica dei valori pubblicati per Seravezza e Stazzema. I cinque Comuni senza dato restano n.d.: 79.452 m³ non implica produzione zero negli altri territori.'},
        'normalizedAggregate':None,
        'method':{
            'type':'Dati ufficiali Regione Toscana — Obblighi Informativi / monitoraggio PRC',
            'formula':'Seravezza: comprensorio 8. Stazzema: somma dei comprensori 9 Bacino di Stazzema + 92 Cardoso delle Apuane, entrambi attribuiti dal PRC al Comune. Aggregato visualizzato: somma aritmetica dei soli Comuni con dato pubblicato (2/7). I componenti elementari sono conservati nello snapshot.',
            'caveat':'I valori sono produzione effettivamente estratta, non volume autorizzato né obiettivo di produzione sostenibile. Per gli altri cinque Comuni il dato resta n.d.; la presenza/assenza in RTCave non viene trasformata in produzione zero.',
            'coverage':'2/7',
            'snapshot':'data/source-snapshots/attivita-estrattive-v128.json'
        }
    }


def prc_parts(info):
    return [
        {'key':'g_ha','label':'Superficie Giacimenti PRC','selectorLabel':'Giacimenti · superficie','unit':'hectares','value':info['g'][1]},
        {'key':'g_pct','label':'Quota comunale Giacimenti PRC','selectorLabel':'Giacimenti · % territorio','unit':'%','value':info['g'][2]},
        {'key':'g_n','label':'Numero Giacimenti PRC','selectorLabel':'Giacimenti · numero','unit':'number','value':info['g'][0]},
        {'key':'gp_ha','label':'Superficie Giacimenti Potenziali','selectorLabel':'Giacimenti potenziali · superficie','unit':'hectares','value':info['gp'][1]},
        {'key':'gp_pct','label':'Quota comunale Giacimenti Potenziali','selectorLabel':'Giacimenti potenziali · % territorio','unit':'%','value':info['gp'][2]},
        {'key':'gp_n','label':'Numero Giacimenti Potenziali','selectorLabel':'Giacimenti potenziali · numero','unit':'number','value':info['gp'][0]},
        {'key':'acc_ha','label':'Superficie Aree Contigue di Cava','selectorLabel':'ACC · superficie','unit':'hectares','value':info['acc'][1]},
        {'key':'acc_pct','label':'Quota comunale Aree Contigue di Cava','selectorLabel':'ACC · % territorio','unit':'%','value':info['acc'][2]},
        {'key':'acc_n','label':'Numero Aree Contigue di Cava','selectorLabel':'ACC · numero','unit':'number','value':info['acc'][0]},
    ]


def build_prc_metric(site):
    slugs=slug_map(site); town_by_code={t['code']:t for t in site['towns']}; rows=[]
    for code in [t['code'] for t in site['towns']]:
        d=PRC[code]; parts=prc_parts(d)
        rows.append({'town':town_by_code[code]['name'],'code':code,'slug':slugs[code],'value':d['g'][1],'formatted':f"{d['g'][1]:.2f} ha".replace('.',','),'series':None,'normalized':None,'benchmarkValue':d['g'][1],'parts':parts,'prcDetail':d})
    agg_info={'g':PRC_AGG['g'],'gp':PRC_AGG['gp'],'acc':PRC_AGG['acc']}
    agg_parts=prc_parts(agg_info)
    return {
        'meta':{
            'key':'extractivePlanning','theme':'ambiente','label':'Quadro estrattivo PRC','shortLabel':'Quadro estrattivo PRC',
            'description':'Superficie del territorio comunale ricadente nelle geometrie ufficiali del Piano Regionale Cave. Giacimenti, Giacimenti Potenziali e Aree Contigue di Cava restano categorie separate.',
            'unit':'hectares','year':'PRC vigente · variante 2025','source':'Regione Toscana — Piano Regionale Cave / GeoScopio','polarity':'neutral','detailGroup':'extractive',
            'searchTerms':['giacimenti','giacimenti potenziali','aree contigue di cava','acc','piano regionale cave','prc','marmo','cave'],
            'sourceMeta':{'snapshot':'data/source-snapshots/attivita-estrattive-v128.json','note':'Geometrie PRC EPSG:3003 intersecate con Ambiti Amministrativi Regione Toscana. MOS, pMOS e SED sono conservati nel dettaglio.'},
            'compositeType':'securityMeasures','selectorLabel':'Lettura','comparisonReference':'aggregate','comparisonDifference':'shareOfAggregate','comparisonLabel':'Versilia','comparisonOverline':'Peso sulla Versilia','comparisonNote':'Per superfici e numeri il peso è calcolato sul totale della stessa categoria PRC. Per la % di territorio si confrontano direttamente quota comunale e quota territoriale Versilia, senza dividere una percentuale per l’altra.'
        },
        'sourceUrl':PRC_URL,
        'rows':rows,
        'aggregate':{'value':PRC_AGG['g'][1],'label':'Versilia · quadro PRC','parts':agg_parts,'note':'Aggregati geometrici separati per G, GP e ACC; non vengono sommati in un’unica superficie di cava.'},
        'normalizedAggregate':None,
        'method':{
            'type':'Elaborazione GIS su dati ufficiali Regione Toscana',
            'formula':'Numero: attribuzione comunale ufficiale del PRC. Superficie: union per categoria e intersection con confini comunali ufficiali in EPSG:3003; quota = area intersecata / area comunale.',
            'caveat':'Le geometrie descrivono il quadro pianificatorio PRC, non la superficie effettivamente escavata o autorizzata. G, GP e ACC non sono sommabili come se fossero la stessa categoria. SED è una ricognizione non esaustiva.',
            'coverage':'7/7',
            'snapshot':'data/source-snapshots/attivita-estrattive-v128.json'
        }
    }


def apply_site(site, rtcave_selected):
    new_metrics={
        'extractiveSites':build_sites_metric(site, rtcave_selected),
        'extractiveProduction':build_production_metric(site),
        'extractivePlanning':build_prc_metric(site),
    }
    out=OrderedDict(); inserted=False
    for key,metric in site['metrics'].items():
        if key in KEYS: continue
        out[key]=metric
        if key=='organicAgriculturalAreaShare':
            for k in KEYS: out[k]=new_metrics[k]
            inserted=True
    if not inserted:
        raise RuntimeError('Punto di inserimento dopo agricoltura non trovato')
    site['metrics']=out
    theme=site['themes']['ambiente']
    theme['sections']=[s for s in theme['sections'] if s.get('key')!='attivita-estrattive']
    idx=next((i+1 for i,s in enumerate(theme['sections']) if s.get('key')=='agricoltura'), len(theme['sections']))
    theme['sections'].insert(idx,{
        'key':'attivita-estrattive','label':'Attività estrattive','description':'Siti RTCave, produzione effettivamente estratta e quadro pianificatorio del Piano Regionale Cave, mantenendo distinti stato operativo, produzione e categorie territoriali.',
        'metrics':list(KEYS),
    })
    theme['metrics']=[k for sec in theme['sections'] for k in sec['metrics']]
    theme['description']='Ambiente, clima, costa, acqua, bonifiche, agricoltura, attività estrattive, rifiuti e rischi del territorio.'
    site['version']='v1.28.0'; site['updated']='2 settembre 2026'


def apply_registry(reg):
    reg['expectedMetricCount']=180; reg['expectedInlineMetricCount']=176; reg['expectedExternalMetricCount']=4
    profiles=reg.setdefault('sourceProfiles',{})
    profiles['regione-toscana-rtcave-continuous']={
        'publisher':'Regione Toscana — RTCave','frequency':'continuous','frequencyLabel':'Continuo / snapshot','expectedRelease':'La banca dati pubblica è aggiornata nel corso dell’anno; l’Osservatorio conserva snapshot versionati.','acquisitionMethod':'GET endpoint pubblico anonimo /api/v1/cave_public; validazione ID e categorie originali; nessuna trascrizione dai contatori UI.','licenseName':'Dato pubblico Regione Toscana; riuso documentato nello snapshot','licenseUrl':RTCAVE_PAGE,
    }
    profiles['regione-toscana-prc-annual']={
        'publisher':'Regione Toscana — Piano Regionale Cave','frequency':'annual','frequencyLabel':'Annuale / variante di piano','expectedRelease':'Monitoraggio annuale PRC e aggiornamenti/varianti del piano.','acquisitionMethod':'Monitoraggio PRC per produzione; geometrie ufficiali GeoScopio/PRC + Ambiti Amministrativi per superfici.','licenseName':'CC BY per i dataset geografici regionali','licenseUrl':PRC_URL,
    }
    for u,p in [(RTCAVE_URL,'regione-toscana-rtcave-continuous'),(PRC_URL,'regione-toscana-prc-annual'),(PRC_MONITOR_URL,'regione-toscana-prc-annual')]:
        reg.setdefault('sourceProfileByUrl',{})[u]=p; reg.setdefault('sourceUrlProfiles',{})[u]=p
    reg.setdefault('metricOverrides',{})['extractiveSites']={'profile':'regione-toscana-rtcave-continuous'}
    reg.setdefault('metricOverrides',{})['extractiveProduction']={'profile':'regione-toscana-prc-annual'}
    reg.setdefault('metricOverrides',{})['extractivePlanning']={'profile':'regione-toscana-prc-annual'}


def apply_state(state, rtcave_meta, rtcave_sha):
    src=state.setdefault('sources',{}).setdefault(RTCAVE_URL,{})
    src.update({'url':RTCAVE_URL,'ok':True,'status':rtcave_meta['status'],'finalUrl':rtcave_meta['finalUrl'],'contentType':rtcave_meta['contentType'],'contentLength':None,'etag':'','lastModified':'','contentSha256':rtcave_sha,'hashTruncated':False,'error':'','metrics':['extractiveSites'],'roles':['primary'],'profileIds':['regione-toscana-rtcave-continuous'],'frequencies':['continuous']})
    for u,metrics in [(PRC_URL,['extractivePlanning']),(PRC_MONITOR_URL,['extractiveProduction'])]:
        state.setdefault('sources',{}).setdefault(u,{'url':u,'ok':True,'status':200,'finalUrl':u,'contentType':'text/html','contentLength':None,'etag':'','lastModified':'','contentSha256':'','hashTruncated':False,'error':'','metrics':metrics,'roles':['primary'],'profileIds':['regione-toscana-prc-annual'],'frequencies':['annual']})
    for k in KEYS:
        state.setdefault('metrics',{})[k]={'publishedPeriod':'2026-09' if k!='extractiveProduction' else '2025','checkedAt':'2026-09-02T10:49:00+00:00','observedLatestPeriod':'2026-09' if k!='extractiveProduction' else '2025','status':'current'}


def build_snapshot(raw, all_rows, selected, rtcave_meta):
    return {
        'snapshotId':'attivita-estrattive-v128','retrievedAt':'2026-09-02T10:49:00+00:00','sourceUrls':{'rtcave':RTCAVE_URL,'prc':PRC_URL,'prcMonitor':PRC_MONITOR_URL},
        'rtcave':{
            'sha256':hashlib.sha256(raw).hexdigest(),'regionalRecordCount':len(all_rows),'regionalUniqueCodiceRt':len({r.get('codice_rt') for r in all_rows}),'regionalUniqueIdCava':len({r.get('id_cava') for r in all_rows}),
            'versiliaRecordCount':len(selected),'rawFieldNames':sorted(selected[0].keys()) if selected else [],'records':selected,
            'note':'Record pubblici conservati senza rinominare o scartare i campi dell’endpoint. I contatori sono ricalcolati dai valori originali, senza il fallback UI che assegna valori sconosciuti all’ultima categoria.'
        },
        'production':PRODUCTION,
        'prc':{'towns':PRC,'aggregate':PRC_AGG,'crs':'EPSG:3003','surfaceMethod':'Union per categoria + intersection sui confini comunali ufficiali; conteggi per attribuzione comunale PRC.','sedNote':'I SED sono una ricognizione PRC non esaustiva e sono usati solo come dettaglio.'},
        'releaseChecks':{'expectedMetrics':180,'expectedInline':176,'expectedExternal':4,'expectedRtcaveRegionalRecords':666,'expectedRtcaveVersiliaRecords':90}
    }


def patch_ui():
    # unità m³
    t=APP00.read_text(encoding='utf-8')
    if "case 'cubicMetres'" not in t:
        marker="      case 'hectares': return `${number2.format(v)} ha`;"
        if marker not in t: raise RuntimeError('formatValue hectares non trovato')
        t=t.replace(marker, marker+"\n      case 'cubicMetres': return `${number0.format(v)} m³`;",1)
    syn_marker="    maritimeConcessionFeesDue: ['canoni demaniali', 'canone dovuto', 'demanio marittimo', 'sid', 'balneari'],"
    if 'extractiveSites:' not in t:
        if syn_marker not in t: raise RuntimeError('Sinonimi demanio non trovati')
        t=t.replace(syn_marker,syn_marker+"\n    extractiveSites: ['cave', 'cava', 'rtcave', 'attività estrattive', 'marmo', 'lapideo', 'siti estrattivi'],\n    extractiveProduction: ['produzione cave', 'volume estratto', 'marmo estratto', 'materiale estratto', 'prc'],\n    extractivePlanning: ['giacimenti', 'giacimenti potenziali', 'aree contigue di cava', 'acc', 'piano regionale cave', 'prc'],",1)
    APP00.write_text(t,encoding='utf-8')

    t=APP03.read_text(encoding='utf-8')
    if 'function extractiveDetailMarkup' not in t:
        marker="  function coastCompareDetailMarkup(metric) {\n    return coastDetailMarkup(metric, metric.rows, 'Dettaglio dei quattro Comuni costieri');\n  }"
        if marker not in t: raise RuntimeError('Marker coastCompareDetailMarkup non trovato')
        fn=r'''  function extractiveDetailMarkup(metric, rows, title) {
    if (metric?.meta?.detailGroup !== 'extractive') return '';
    const key=metric.meta.key;
    const list=(rows||[]);
    if (key === 'extractiveSites') {
      if (list.length === 1) {
        const row=list[0], d=row.extractiveDetail || {}, records=d.records || [];
        const summary=`<div class="composite-town-detail"><div><span>Totale RTCave</span><b>${html(number0.format(d.recordCount||0))}</b><small>record distinti per codice_rt</small></div><div><span>Stati</span><b>${html((d.statusBreakdown||[]).map(x=>`${x.label} ${x.count}`).join(' · ') || 'nessun sito')}</b><small>valori originali RTCave</small></div><div><span>Tipologie</span><b>${html((d.typeBreakdown||[]).map(x=>`${x.label} ${x.count}`).join(' · ') || 'nessun sito')}</b><small>classificazione RTCave</small></div><div><span>Produzione</span><b>${html((d.productionBreakdown||[]).map(x=>`${x.label} ${x.count}`).join(' · ') || 'nessun sito')}</b><small>macro-classe produttiva</small></div></div>`;
        const table=records.length ? `<div class="indicator-table-scroll"><table class="indicator-values-table"><thead><tr><th>Codice RT</th><th>Cava</th><th>Località</th><th>Stato</th><th>Tipologia</th><th>Produzione</th><th>Comprensorio</th><th>Giacimento</th><th>Coordinate</th></tr></thead><tbody>${records.map(r=>`<tr><td>${html(r.codice_rt||'n.d.')}</td><th>${html(r.nome_cava||'n.d.')}</th><td>${html(r.localita||'n.d.')}</td><td>${html(r.stato||'n.d.')}</td><td>${html(r.tipologia||'n.d.')}</td><td>${html(r.tipo_produzione||'n.d.')}</td><td>${html(r.nome_comprensorio||'n.d.')}</td><td>${html(r.nome_giacimento||'n.d.')}</td><td>${html(`${r.lat??'n.d.'}, ${r.lon??'n.d.'}`)}</td></tr>`).join('')}</tbody></table></div>` : '<p class="aggregate-note">Nessun record RTCave nello snapshot.</p>';
        return `<details class="detail-disclosure extractive-detail" open><summary><span>${html(title)}</span><small>Anagrafica pubblica RTCave</small></summary>${summary}${table}<p class="aggregate-note">Chiusa, Inattiva e SED non sono sinonimi. La classe produttiva RTCave non viene reinterpretata come litologia.</p></details>`;
      }
      return `<details class="detail-disclosure extractive-detail" open><summary><span>${html(title)}</span><small>Stato, tipologia e classe produttiva</small></summary><div class="indicator-table-scroll"><table class="indicator-values-table"><thead><tr><th>Comune</th><th>Totale</th><th>Attivi</th><th>Inattivi</th><th>Sospesi</th><th>Scaduti</th><th>Chiusi</th><th>n.d.</th></tr></thead><tbody>${list.map(row=>{const p=Object.fromEntries((row.parts||[]).map(x=>[x.key,x.value]));return `<tr><th>${html(row.town)}</th><td>${html(number0.format(p.total||0))}</td><td>${html(number0.format(p.state_active||0))}</td><td>${html(number0.format(p.state_inactive||0))}</td><td>${html(number0.format(p.state_suspended||0))}</td><td>${html(number0.format(p.state_expired||0))}</td><td>${html(number0.format(p.state_closed||0))}</td><td>${html(number0.format(p.state_nd||0))}</td></tr>`}).join('')}</tbody></table></div><p class="aggregate-note">I dettagli comunali conservano tutti i campi pubblici dell’endpoint, compresi comprensorio, giacimento, coordinate e ID tecnici nello snapshot.</p></details>`;
    }
    if (key === 'extractiveProduction') {
      const applicable=list.filter(r=>r.productionDetail);
      if (!applicable.length) return `<aside class="benchmark-unavailable"><span class="overline">Disponibilità del dato</span><h3>Produzione comunale n.d.</h3><p>Il monitoraggio PRC non consente un raccordo comunale omogeneo per questo Comune; nessuno zero viene inferito.</p></aside>`;
      const years=applicable[0].productionDetail.years||[];
      return `<details class="detail-disclosure extractive-detail" open><summary><span>${html(title)}</span><small>Volumi effettivamente estratti · m³</small></summary><div class="indicator-table-scroll"><table class="indicator-values-table"><thead><tr><th>Comune</th>${years.map(y=>`<th>${html(String(y))}</th>`).join('')}</tr></thead><tbody>${applicable.map(r=>`<tr><th>${html(r.town)}</th>${r.productionDetail.values.map(v=>`<td>${html(number0.format(v))}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="aggregate-note">Per Stazzema la serie conserva separatamente Bacino di Stazzema e Cardoso delle Apuane; l’OPS 2019–2038 resta un benchmark pianificatorio, non un volume autorizzato.</p></details>`;
    }
    if (key === 'extractivePlanning') {
      return `<details class="detail-disclosure extractive-detail" open><summary><span>${html(title)}</span><small>G, GP, ACC e patrimonio storico PRC</small></summary><div class="indicator-table-scroll"><table class="indicator-values-table"><thead><tr><th>Comune</th><th>G n.</th><th>G ha</th><th>G %</th><th>GP n.</th><th>GP ha</th><th>GP %</th><th>ACC n.</th><th>ACC ha</th><th>ACC %</th><th>MOS</th><th>pMOS</th><th>SED censiti</th></tr></thead><tbody>${list.map(row=>{const d=row.prcDetail||{};return `<tr><th>${html(row.town)}</th><td>${html(number0.format(d.g?.[0]||0))}</td><td>${html(number2.format(d.g?.[1]||0))}</td><td>${html(number3.format(d.g?.[2]||0))}%</td><td>${html(number0.format(d.gp?.[0]||0))}</td><td>${html(number2.format(d.gp?.[1]||0))}</td><td>${html(number3.format(d.gp?.[2]||0))}%</td><td>${html(number0.format(d.acc?.[0]||0))}</td><td>${html(number2.format(d.acc?.[1]||0))}</td><td>${html(number3.format(d.acc?.[2]||0))}%</td><td>${html(number0.format(d.mos||0))}</td><td>${html(number0.format(d.pmos||0))}</td><td>${html(number0.format(d.sed||0))}</td></tr>`}).join('')}</tbody></table></div><p class="aggregate-note">Giacimenti, Giacimenti Potenziali e ACC restano categorie distinte. I SED sono siti dismessi censiti dal PRC in una ricognizione non esaustiva.</p></details>`;
    }
    return '';
  }

  function extractiveCompareDetailMarkup(metric) {
    return extractiveDetailMarkup(metric, metric.rows, 'Dettaglio attività estrattive');
  }

  function extractiveTownDetailMarkup(metric,row) {
    return extractiveDetailMarkup(metric,[row],`Dettaglio · ${row.town}`);
  }

'''
        t=t.replace(marker,fn+marker,1)
    compare_marker="    if (metric.meta.detailGroup === 'coast') bars.insertAdjacentHTML('beforeend', coastCompareDetailMarkup(metric));"
    if "detailGroup === 'extractive'" not in t:
        if compare_marker not in t: raise RuntimeError('Marker compare coast non trovato')
        t=t.replace(compare_marker,compare_marker+"\n    if (metric.meta.detailGroup === 'extractive') bars.insertAdjacentHTML('beforeend', extractiveCompareDetailMarkup(metric));",1)
    town_marker='      ${coastTownDetailMarkup(metric,row)}'
    if '${extractiveTownDetailMarkup(metric,row)}' not in t:
        if town_marker not in t: raise RuntimeError('Marker town coast non trovato')
        t=t.replace(town_marker,town_marker+'\n      ${extractiveTownDetailMarkup(metric,row)}',1)
    APP03.write_text(t,encoding='utf-8')

    t=APP05.read_text(encoding='utf-8')
    marker="['ISPRA','https://www.isprambiente.gov.it/'],"
    if 'Regione Toscana — RTCave' not in t:
        if marker not in t: raise RuntimeError('Elenco fonti APP05 non trovato')
        t=t.replace(marker,marker+"['Regione Toscana — RTCave','https://cave.regione.toscana.it/'],['Regione Toscana — Piano Regionale Cave','https://www.regione.toscana.it/piano-regionale-cave'],",1)
    APP05.write_text(t,encoding='utf-8')


def patch_release():
    # Finalizer
    for a,b in [
        ('catalogo pubblico v1.27.0','catalogo pubblico v1.28.0'),
        ('VERSION = "v1.27.0"','VERSION = "v1.28.0"'),
        ('UPDATED = "1 settembre 2026"','UPDATED = "2 settembre 2026"'),
        ('EXPECTED_METRICS = 177','EXPECTED_METRICS = 180'),
        ('EXPECTED_INLINE = 173','EXPECTED_INLINE = 176'),
    ]: replace(FINAL,a,b)
    # README
    for a,b in [
        ('Versione dati corrente: **v1.27.0** — 1 settembre 2026.','Versione dati corrente: **v1.28.0** — 2 settembre 2026.'),
        ('177 indicatori nel catalogo canonico: 173 con valori incorporati','180 indicatori nel catalogo canonico: 176 con valori incorporati'),
        ('`indicatori/`: 173 pagine canoniche','`indicatori/`: 176 pagine canoniche'),
        ('catalogo canonico dei 177 indicatori, con dati incorporati per 173','catalogo canonico dei 180 indicatori, con dati incorporati per 176'),
        ('metadati dei 177 indicatori','metadati dei 180 indicatori'),
        ('valida tutti i 177 indicatori canonici, la ripartizione fra 173 valori incorporati','valida tutti i 180 indicatori canonici, la ripartizione fra 176 valori incorporati'),
        ('ciascuno dei 173 indicatori incorporati','ciascuno dei 176 indicatori incorporati'),
    ]: replace(README,a,b)
    # cache/revision tokens
    for p in [ROOT/'assets/app.js',EXPORT,UX,BUILD_SAFE,BUILD_BRAND]:
        replace(p,OLD_TOKEN,NEW_TOKEN,optional=True)
    replace(SERVICE_WORKER,'ov-pwa-'+OLD_TOKEN,'ov-pwa-'+NEW_TOKEN,optional=True)
    replace(BUILD_BRAND,'PWA_JS_REVISION = "catalog-v127"','PWA_JS_REVISION = "catalog-v128"',optional=True)
    # release history where present
    hist_marker="      ['2026.09.01-v1.27.0','1 settembre 2026','177 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunte Concessioni demaniali marittime e Canoni demaniali dovuti dallo snapshot MIT/SID agosto 2026, con selector Totale / Turistico-ricreative e copertura 4 Comuni costieri + 3 n.a. Superficie, metri e quota di litorale restano rinviati per incompletezza geometrica.'],"
    hist_new=hist_marker+"\n      ['2026.09.02-v1.28.0','2 settembre 2026','180 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunte Attività estrattive: Siti censiti in RTCave con dettaglio pubblico completo, Produzione estrattiva 2019–2025 dove il raccordo comunale è verificato e Quadro estrattivo PRC con G/GP/ACC separati e clipping sui confini regionali.'],"
    replace(BUILD_BRAND,hist_marker,hist_new,once=True,optional=True)


def rebuild_app():
    # app.js è concatenazione degli app-parts; evita di lasciare il sorgente principale indietro.
    parts=sorted((ROOT/'assets/app-parts').glob('*.txt'))
    if not parts: raise RuntimeError('assets/app-parts non trovato')
    app=''.join(p.read_text(encoding='utf-8') for p in parts)
    (ROOT/'assets/app.js').write_text(app,encoding='utf-8')


def validate(site, selected):
    if site.get('version')!='v1.28.0' or len(site.get('metrics',{}))!=180: raise RuntimeError('Catalogo v1.28 non riconciliato')
    for k in KEYS:
        if k not in site['metrics']: raise RuntimeError(f'Metrica mancante {k}')
    s=site['metrics']['extractiveSites'];
    if s['aggregate']['value']!=90 or next(p for p in s['aggregate']['parts'] if p['key']=='state_active')['value']!=15: raise RuntimeError('RTCave aggregato incoerente')
    if len(s['rows'])!=7 or sum(len(r['extractiveDetail']['records']) for r in s['rows'])!=90: raise RuntimeError('RTCave dettaglio castrato')
    st=next(r for r in s['rows'] if r['code']=='046030')
    if len(st['extractiveDetail']['records'])!=43: raise RuntimeError('Stazzema RTCave incompleta')
    prod=site['metrics']['extractiveProduction'];
    if next(r for r in prod['rows'] if r['code']=='046028')['value']!=55801: raise RuntimeError('Produzione Seravezza incoerente')
    if next(r for r in prod['rows'] if r['code']=='046030')['value']!=23651: raise RuntimeError('Produzione Stazzema incoerente')
    prc=site['metrics']['extractivePlanning'];
    ser=next(r for r in prc['rows'] if r['code']=='046028')['prcDetail']; sta=next(r for r in prc['rows'] if r['code']=='046030')['prcDetail']
    if ser['g'][0]!=2 or ser['acc'][0]!=7 or sta['g'][0]!=1 or sta['acc'][0]!=12: raise RuntimeError('PRC conteggi incoerenti')


def main():
    site=load(SITE); registry=load(REGISTRY); state=load(STATE)
    raw, all_rows, selected, rtcave_meta=fetch_rtcave()
    apply_site(site,selected); apply_registry(registry); apply_state(state,rtcave_meta,hashlib.sha256(raw).hexdigest())
    snapshot=build_snapshot(raw,all_rows,selected,rtcave_meta)
    save(SITE,site); save(REGISTRY,registry); save(STATE,state); save(SNAP,snapshot)
    patch_ui(); patch_release(); rebuild_app()
    subprocess.run([sys.executable,str(ROOT/'scripts/patch_attivita_estrattive_v128_release.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(FINAL)],cwd=ROOT,check=True)
    validate(load(SITE),selected)
    print('Attività estrattive v1.28.0 materializzate: 3 card, 90 record RTCave completi, produzione 2019–2025, PRC G/GP/ACC.')

if __name__=='__main__':
    main()
