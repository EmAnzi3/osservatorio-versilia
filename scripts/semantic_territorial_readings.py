#!/usr/bin/env python3
"""A6.5 reviewable pilot readings, generated only from deterministic query results."""
import argparse
import copy
import json
from pathlib import Path

from semantic_query_engine import QueryEngine, ROOT

PILOTS = {
    'ageing_care': {
        'title':'Invecchiamento e assistenza domiciliare',
        'question':'Quale peso hanno gli 85+ e quale assistenza domiciliare è registrata?',
        'hypothesis':'Verificare se localizzazione, accessibilità e organizzazione dei servizi rispondano alla domanda effettiva: quote demografiche e assistenza erogata non misurano da sole il bisogno insoddisfatto.',
        'proposal':'Valutare una ricognizione territoriale della domanda e dei tempi di accesso, prima di dimensionare o riallocare servizi.',
        'target':'Residenti anziani con bisogni verificati; gli 85+ sono un gruppo demografico osservato, non un elenco di persone bisognose.',
        'outcomes':['Tempi di attesa e percorrenza per il servizio, con definizione e periodo stabili','Copertura dei bisogni accertati, distinta dal tasso standardizzato ARS'],
        'missing':['Domanda insoddisfatta e intensità del bisogno','Accessibilità subcomunale, capacità e tempi dei servizi','Allineamento temporale dei dati demografici e assistenziali'],
    },
    'work_childcare': {
        'title':'Lavoro femminile e servizi per l’infanzia',
        'question':'Come si affiancano occupazione femminile e offerta educativa potenziale?',
        'hypothesis':'Verificare domanda, orari, costi e uso intercomunale: il dato disponibile non dimostra che l’offerta locale causi il tasso di occupazione femminile.',
        'proposal':'Valutare orari e accordi intercomunali solo dopo avere osservato domanda, iscritti e accessibilità effettiva.',
        'target':'Famiglie con bambini e necessità di conciliazione accertate; il catalogo non identifica le lavoratrici con figli.',
        'outcomes':['Accessi e tempi di attesa per famiglie richiedenti, con perimetro dichiarato','Compatibilità degli orari con la domanda osservata; occupazione come contesto da monitorare'],
        'missing':['Iscrizioni, domanda e liste d’attesa','Costi, orari, accessi e mobilità fra Comuni','Occupazione dei genitori e periodi omogenei'],
    },
    'tourism_services': {
        'title':'Turismo e organizzazione dei servizi',
        'question':'Quanto movimento registrato si osserva e come cambia rispetto al 2023?',
        'hypothesis':'Verificare se flussi effettivi e picchi coincidano con pressioni su mobilità, rifiuti o servizi: notti annue non equivalgono a persone presenti ogni giorno.',
        'proposal':'Valutare la modulazione stagionale dei servizi dopo aver misurato picchi, carichi e domanda effettiva.',
        'target':'Residenti e utilizzatori dei servizi nei periodi e luoghi di pressione verificata; escursionisti e locazioni non sono coperti da queste presenze.',
        'outcomes':['Carichi e tempi dei servizi nei periodi di picco, con base di confronto','Distribuzione temporale e territoriale dei flussi effettivamente rilevati'],
        'missing':['Escursionismo, locazioni escluse e picchi giornalieri','Carichi reali dei servizi, costi marginali e mobilità','Serie di capacità dei servizi confrontabile con i flussi'],
    },
}


def query(operation, metric, dimension='total', **fields):
    selection={'metric':metric,'dimension':dimension}
    for key in ('towns','periods'):
        if key in fields:selection[key]=fields.pop(key)
    return dict(operation=operation,selectors=[selection],**fields)


def build_readings(engine):
    """No ranking, universal score, modelled effect or automated policy recommendation."""
    catalog=engine.catalog
    comparisons={}
    selections=[('ageDistribution','age:85+'),('elderlyHomeCare','sex:total'),
        ('femaleEmploymentRate','total'),('earlyChildhoodPotentialCapacityRate','total'),
        ('tourismPresences','total'),('tourismIntensity','total')]
    for metric,dimension in selections:
        comparisons[(metric,dimension)]=engine.query(query('compare',metric,dimension))
    blocked={}
    for pilot,pair in [('ageing_care',selections[:2]),('work_childcare',selections[2:4])]:
        blocked[pilot]=engine.query({'operation':'correlation','selectors':[{'metric':m,'dimension':d} for m,d in pair],
            'method':'spearman','axis':'municipalities','purpose':PILOTS[pilot]['question']+'; verificare allineamento, senza inferenza causale'})
    readings=[]
    for town in sorted(catalog['towns'],key=lambda t:t['name']):
        code=str(town['code'])
        for pilot,settings in PILOTS.items():
            pairs=selections[:2] if pilot=='ageing_care' else selections[2:4] if pilot=='work_childcare' else selections[4:]
            observed=[];failures=[]
            for m,d in pairs:
                result=comparisons[(m,d)]
                matches=[o for o in result['observations'] if o['geography']==code]
                if result['status']!='computed' or len(matches)!=1:
                    failures.extend(result['reasons'] or ['observation_not_available'])
                else:
                    observed.append({'level':'observation','label':catalog['metrics'][m]['meta']['label'],
                        'observation':matches[0],'warnings':result['warnings']})
            if pilot=='ageing_care':
                calculations=[engine.query(query('benchmark_gap','ageDistribution','age:85+',towns=[code],benchmark='tuscany')),
                    engine.query(query('benchmark_gap','elderlyHomeCare','sex:total',towns=[code],benchmark='versilia'))]
            elif pilot=='work_childcare':
                calculations=[engine.query(query('benchmark_gap','femaleEmploymentRate',towns=[code],benchmark='tuscany')),
                    engine.query(query('benchmark_gap','earlyChildhoodPotentialCapacityRate',towns=[code],benchmark='tuscany'))]
            else:
                calculations=[engine.query(query('absolute_change','tourismPresences',towns=[code],periods=['2023','2025'])),
                    engine.query(query('benchmark_gap','tourismIntensity',towns=[code],benchmark='tuscany'))]
            for result in calculations:
                if result['status']!='computed':failures.extend(result['reasons'])
            relationship=copy.deepcopy(blocked[pilot]) if pilot in blocked else {
                'status':'not_requested','reasons':['shared_numerator_not_independent_evidence'],
                'explanation':'L’intensità deriva dalle stesse presenze: non si calcola una correlazione per confermare una relazione meccanica.'}
            readings.append(dict(id=pilot+':'+code,pilot=pilot,town=town['name'],geography=code,
                question=settings['question'],status='not_ready' if failures else 'ready_for_methodological_review',
                reasons=sorted(set(failures)),observations=observed,calculations=calculations,
                association=relationship,
                contextRelation='side_by_side_periods_and_universes_retained' if pilot in blocked else 'declared_flow_stock_ratio',
                hypothesis={'level':'hypothesis','text':settings['hypothesis'],'verified':False},
                proposal={'level':'proposal','text':settings['proposal'],'target':settings['target'],
                    'evidenceIds':[pilot+':'+code+':observations',pilot+':'+code+':calculations'],
                    'outcomeIndicatorsRequired':settings['outcomes'],'additionalDataRequired':settings['missing'],
                    'assumptions':['Bisogno e destinatari devono essere accertati localmente','Fattibilità, costi ed effetti non sono stimati da questi dati'],
                    'approved':False,'expectedEffect':None} ))
    return dict(schemaVersion=1,catalogSha256=engine.catalog_hash,catalogPath=engine.catalog_path,
        engineVersion=readings[0]['calculations'][0]['engineVersion'],
        status='not_ready' if any(r['status']=='not_ready' for r in readings) else 'ready_for_methodological_review',
        readings=readings,notes=['Prototipo A6.5 per revisione metodologica: nessuna nuova UI o lettura pubblicata',
        'Osservazione, calcolo, associazione, ipotesi e proposta restano separati',
        'Nessuna causalità, inferenza individuale, graduatoria di qualità o effetto di politica dedotto automaticamente'])


def markdown(report):
    def fmt(value):
        if value is None:return 'n.d.'
        return f'{value:.6f}'.replace('.',',') if isinstance(value,(float,int)) else str(value)
    lines=['# A6.5 — prime letture territoriali per revisione','',
        f"Catalogo effettivo: SHA-256 `{report['catalogSha256']}`; motore v{report['engineVersion']}. Stato: `{report['status']}`.",'',
        'Questo report è derivato dalle query, senza nuovi dati o modifiche alle pagine pubbliche. I periodi distinti sono affiancati, senza conversioni. Ogni ipotesi e proposta richiede revisione e dati aggiuntivi.','']
    for pilot,settings in PILOTS.items():
        lines += ['## '+settings['title'],'',settings['question'],'',
            {'ageing_care':'| Comune | Quota 85+ · 2026 | Assistenza domiciliare standardizzata · 2024 | Quota 85+ meno Toscana | Assistenza meno Versilia |',
             'work_childcare':'| Comune | Occupazione femminile · 2023 | Ricettività potenziale · 2024/25 | Occupazione meno Toscana | Ricettività meno Toscana |',
             'tourism_services':'| Comune | Notti registrate · 2025 | Notti 2025 / residenti 2026 | Variazione notti 2023→2025 | Intensità meno Toscana |'}[pilot],
            '|---|---|---|---|---|']
        cohort=[r for r in report['readings'] if r['pilot']==pilot]
        for row in cohort:
            if row['status']=='not_ready':
                lines.append('| '+row['town']+' | Non disponibile: '+', '.join(row['reasons'])+' | — | — | — |');continue
            obs=[f"{fmt(o['observation']['value'])} {o['observation']['unit']} · {o['observation']['period']}" for o in row['observations']]
            calcs=[]
            for c in row['calculations']:
                result=c['result'];label='Δ 2023→2025' if c['query']['operation']=='absolute_change' else 'Comune − '+result['benchmarkScope']
                calcs.append(f"{label}: {fmt(result['value'])} {result['unit']} · {result.get('period',result.get('endPeriod'))}")
            lines.append('| '+' | '.join([row['town']]+obs+calcs)+' |')
        first=cohort[0]
        lines += ['', '**Definizioni e periodi.**']
        for o in first['observations']:
            obs=o['observation'];lines.append(f"- {o['label']}: {obs['definition']}; {obs['periodBasis']}; universo: {obs['population']}.")
        relation=first['association']
        lines += ['', '**Calcolo congiunto / associazione.** '+relation['status']+': '+', '.join(relation.get('reasons',[]))+'.',
            '', '**Ipotesi da verificare.** '+settings['hypothesis'],'', '**Opzione da valutare.** '+settings['proposal'],
            '', '**Destinatari.** '+settings['target'],'', '**Indicatori di risultato da predisporre.**']
        lines.extend('- '+item for item in settings['outcomes']);lines+=['','**Dati mancanti per decidere.**']
        lines.extend('- '+item for item in settings['missing']);lines+=['']
    sources={}
    for reading in report['readings']:
        for item in reading['observations']:
            for e in item['observation']['evidence']:
                if e.get('kind')!='catalog_snapshot':sources[e['path']]=e
        for calc in reading['calculations']:
            for obs in calc['observations']:
                for e in obs['evidence']:
                    if e.get('kind')!='catalog_snapshot' and e.get('path'):sources[e['path']]=e
    lines+=['## Evidenze riproducibili','','| Snapshot | SHA-256 | Percorso ufficiale dichiarato |','|---|---|---|']
    for path,e in sorted(sources.items()):lines.append(f"| `{path}` | `{e['sha256']}` | {e.get('sourceUrl','')} |")
    lines+=['','Gli snapshot attestano gli input letti, non la disponibilità live. Il JSON generato dalla stessa CLI conserva osservazioni, Pointer, unità, universi, fonti, formule, periodi, esclusioni e hash per ogni risultato. ARS mantiene il tasso standardizzato: i suoi conteggi grezzi non sono pesi utilizzabili per aggregarlo. La ricettività educativa è potenziale, non frequenza o bisogno insoddisfatto. Presenze/intensità turistiche escludono locazioni ed escursionisti e non misurano un picco giornaliero.','',
        'Riproduzione: `python scripts/semantic_territorial_readings.py --format markdown --output /tmp/a6-readings.md`; per le evidenze complete usare `--format json`. Il catalogo predefinito è quello effettivo `dist/data/site-data.json`, dopo build.','']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--catalog',type=Path,default=ROOT/'dist/data/site-data.json')
    parser.add_argument('--format',choices=['json','markdown'],default='json')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    report=build_readings(QueryEngine(args.catalog,layer='effective'))
    body=markdown(report) if args.format=='markdown' else json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if args.output:args.output.write_text(body,encoding='utf-8')
    else:print(body,end='')
    return 0 if report['status']=='ready_for_methodological_review' else 1


if __name__=='__main__':raise SystemExit(main())
