#!/usr/bin/env python3
"""A6.5 reviewable pilot readings, generated only from deterministic query results."""
import argparse
import copy
import hashlib
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
    'work_commuting': {
        'title':'Pendolarismo per lavoro e perimetro dei flussi',
        'question':'Quali ingressi, uscite, saldi e quote di lavoro nel proprio comune descrive il 2021?',
        'hypothesis':'Verificare origini, destinazioni, modi e orari prima di collegare i margini comunali a problemi di accessibilità. Un saldo non misura la domanda di trasporto attuale.',
        'proposal':'Valutare una ricognizione condivisa della mobilità per lavoro prima di dimensionare corse o infrastrutture.',
        'target':'Pendolari per lavoro abituale dell’universo 2021; non tutti gli occupati, gli studenti o gli spostamenti quotidiani.',
        'outcomes':['Tempi e affidabilità degli spostamenti osservati su percorsi e periodi definiti','Accessibilità effettiva delle destinazioni di lavoro per gli utenti rilevati'],
        'missing':['Coppie origine-destinazione, modi, orari e tempi di viaggio','Flussi aggiornati e domanda effettiva, compreso il pendolarismo per studio','Costi, capacità e qualità dei servizi di trasporto'],
    },
    'school_organization': {
        'title':'Organizzazione scolastica e popolazioni distinte',
        'question':'Quanti alunni sono registrati nelle scuole locali, con quale rapporto alunni/classi e quota primaria a tempo pieno?',
        'hypothesis':'Verificare iscrizioni, bacini intercomunali e domanda di orari: alunni delle scuole locali e bambini residenti non sono la stessa popolazione.',
        'proposal':'Valutare una ricognizione di accessi e domanda educativa prima di decidere cambi di classi, sedi o orari.',
        'target':'Alunni delle scuole localizzate nel comune nell’anno scolastico 2024/25; non automaticamente tutti i bambini residenti.',
        'outcomes':['Accessi, tempi di attesa e spostamenti degli alunni con bacino dichiarato','Compatibilità degli orari offerti con la domanda osservata'],
        'missing':['Residenza, età e flussi degli iscritti, incluse scuole fuori comune','Domanda, capacità effettiva, costi, orari e accessibilità delle singole sedi','Esiti scolastici e periodi/universi omogenei per valutarli'],
    },
}

SELECTIONS = {
    'ageing_care':[('ageDistribution','age:85+'),('elderlyHomeCare','sex:total')],
    'work_childcare':[('femaleEmploymentRate','total'),('earlyChildhoodPotentialCapacityRate','total')],
    'tourism_services':[('tourismPresences','total'),('tourismIntensity','total')],
    'work_commuting':[(m,'total') for m in ('inboundCommuters','outboundCommuters','commuterBalance','selfContainment')],
    'school_organization':[(m,'total') for m in ('schoolStudents','studentsPerClass','primaryFullTimeShare')],
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
    for metric,dimension in dict.fromkeys(pair for pairs in SELECTIONS.values() for pair in pairs):
        # Partial comparison is only a container for individual observations.
        # Group calculations below still require complete coverage.
        comparisons[(metric,dimension)]=engine.query(query('compare',metric,dimension,allowPartial=True))
    blocked={}
    association_pairs={
        'ageing_care':SELECTIONS['ageing_care'],
        'work_childcare':SELECTIONS['work_childcare'],
        'work_commuting':[('selfContainment','total'),('commuterBalance','total')],
        'school_organization':[('schoolStudents','total'),('ageDistribution','age:0-14')],
    }
    for pilot,pair in association_pairs.items():
        blocked[pilot]=engine.query({'operation':'correlation','selectors':[{'metric':m,'dimension':d} for m,d in pair],
            'method':'spearman','axis':'municipalities','purpose':PILOTS[pilot]['question']+'; verificare allineamento, senza inferenza causale'})
    association_checks=[]
    for pilot,result in blocked.items():
        expected='computed' if pilot=='work_commuting' else 'not_computable'
        verified=result['status']==expected
        if expected=='computed':
            verified=verified and result['result']['n']==len(engine.codes) and result['result']['pairedKeys']==sorted(engine.codes) and 'association_not_causation' in result['warnings']
        else: verified=verified and 'paired_period_mismatch' in result['reasons']
        association_checks.append(dict(pilot=pilot,expectedStatus=expected,verified=bool(verified),
            scope='all_selected_municipalities_ecological'))
    readings=[]
    for town in sorted(catalog['towns'],key=lambda t:t['name']):
        code=str(town['code'])
        for pilot,settings in PILOTS.items():
            pairs=SELECTIONS[pilot]
            observed=[];failures=[]
            for m,d in pairs:
                result=comparisons[(m,d)]
                matches=[o for o in result['observations'] if o['geography']==code]
                if result['status']!='computed' or len(matches)!=1 or matches[0].get('value') is None or matches[0].get('dataUnavailable') or matches[0].get('notApplicable'):
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
            elif pilot=='tourism_services':
                calculations=[engine.query(query('absolute_change','tourismPresences',towns=[code],periods=['2023','2025'])),
                    engine.query(query('benchmark_gap','tourismIntensity',towns=[code],benchmark='tuscany'))]
            elif pilot=='work_commuting':
                calculations=[engine.query(query('benchmark_gap','selfContainment',towns=[code],benchmark='tuscany')),
                    engine.query(query('benchmark_gap','commuterBalanceRate',towns=[code],benchmark='tuscany'))]
            else:
                calculations=[engine.query(query('benchmark_gap',metric,towns=[code],benchmark='tuscany'))
                    for metric in ('studentsPerClass','primaryFullTimeShare')]
            for result in calculations:
                if result['status']!='computed':failures.extend(result['reasons'])
            relationship=copy.deepcopy(blocked[pilot]) if pilot in blocked else {
                'status':'not_requested','reasons':['shared_numerator_not_independent_evidence'],
                'explanation':'L’intensità deriva dalle stesse presenze: non si calcola una correlazione per confermare una relazione meccanica.'}
            readings.append(dict(id=pilot+':'+code,pilot=pilot,town=town['name'],geography=code,
                question=settings['question'],status='not_ready' if failures else 'ready_for_methodological_review',
                reasons=sorted(set(failures)),observations=observed,calculations=calculations,
                association=relationship,
                associationScope={'axis':'municipalities','geographies':sorted(engine.codes),'interpretation':'ecological_cohort_not_an_effect_or_association_within_this_town'},
                contextRelation='frozen_2021_work_marginals_shared_components' if pilot=='work_commuting' else 'side_by_side_periods_and_universes_retained' if pilot in blocked else 'declared_flow_stock_ratio',
                hypothesis={'level':'hypothesis','text':settings['hypothesis'],'verified':False},
                proposal={'level':'proposal','text':settings['proposal'],'target':settings['target'],
                    'evidenceIds':[pilot+':'+code+':observations',pilot+':'+code+':calculations'],
                    'outcomeIndicatorsRequired':settings['outcomes'],'additionalDataRequired':settings['missing'],
                    'assumptions':['Bisogno e destinatari devono essere accertati localmente','Fattibilità, costi ed effetti non sono stimati da questi dati'],
                    'approved':False,'expectedEffect':None} ))
    groups=[]
    for pilot,metrics,limitations in [
        ('work_commuting',('selfContainment','commuterBalanceRate','inboundCommutersRate','outboundCommutersRate'),
         ['Le entrate/uscite sommate includono movimenti fra comuni selezionati, non flussi lordi al confine della Versilia.',
          'L’autocontenimento ponderato riguarda il proprio comune, non l’intero gruppo.',
          'Saldo normalizzato: residenti 2021; tassi lordi: residenti 2026, distinti dai flussi 2021.']),
        ('school_organization',('studentsPerClass','primaryFullTimeShare'),
         ['Alunni/classi e tempo pieno usano componenti sommate, non medie di percentuali comunali.',
          'Il primo universo comprende gli alunni delle scuole locali; il secondo soltanto gli alunni della primaria.',
          'Non sono copertura dei bambini residenti, qualità scolastica o domanda insoddisfatta.']),
    ]:
        calculations=[engine.query(query('weighted_ratio',metric,towns=sorted(engine.codes))) for metric in metrics]
        groups.append(dict(id=pilot+':selected_municipalities',pilot=pilot,geographies=sorted(engine.codes),
            status='ready_for_methodological_review' if all(r['status']=='computed' for r in calculations) else 'not_ready',
            calculations=calculations,limitations=limitations))
    return dict(schemaVersion=2,catalogSha256=engine.catalog_hash,catalogPath=engine.catalog_path,
        readingImplementationSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        engineVersion=readings[0]['calculations'][0]['engineVersion'],
        status='not_ready' if any(r['status']=='not_ready' for r in readings+groups) or not all(c['verified'] for c in association_checks) else 'ready_for_methodological_review',
        readings=readings,groupReadings=groups,associationChecks=association_checks,notes=['Prototipo A6.5 per revisione metodologica: nessuna nuova UI o lettura pubblicata',
        'Osservazione, calcolo, associazione, ipotesi e proposta restano separati',
        'Nessuna causalità, inferenza individuale, graduatoria di qualità o effetto di politica dedotto automaticamente'])


def markdown(report):
    def fmt(value):
        if value is None:return 'n.d.'
        return f'{value:.6f}'.replace('.',',') if isinstance(value,(float,int)) else str(value)
    lines=['# A6.5 — prime letture territoriali per revisione','',
        f"Catalogo effettivo: SHA-256 `{report['catalogSha256']}`; motore v{report['engineVersion']}. Stato: `{report['status']}`.",'',
        f"Implementazione letture: SHA-256 `{report['readingImplementationSha256']}`; schema v{report['schemaVersion']}.",'',
        'Questo report è derivato dalle query, senza nuovi dati o modifiche alle pagine pubbliche. I periodi distinti sono affiancati, senza conversioni. Ogni ipotesi e proposta richiede revisione e dati aggiuntivi.','']
    for pilot,settings in PILOTS.items():
        lines += ['## '+settings['title'],'',settings['question'],'',
            {'ageing_care':'| Comune | Quota 85+ · 2026 | Assistenza domiciliare standardizzata · 2024 | Quota 85+ meno Toscana | Assistenza meno Versilia |',
             'work_childcare':'| Comune | Occupazione femminile · 2023 | Ricettività potenziale · 2024/25 | Occupazione meno Toscana | Ricettività meno Toscana |',
             'tourism_services':'| Comune | Notti registrate · 2025 | Notti 2025 / residenti 2026 | Variazione notti 2023→2025 | Intensità meno Toscana |',
             'work_commuting':'| Comune | Ingressi lavoro · 2021 | Uscite lavoro · 2021 | Saldo lavoro · 2021 | Nel proprio comune · 2021 | Quota meno Toscana | Saldo per 1.000 residenti 2021 meno Toscana |',
             'school_organization':'| Comune | Alunni scuole locali · 2024/25 | Alunni/classi · 2024/25 | Tempo pieno primaria · 2024/25 | Alunni/classi meno Toscana | Tempo pieno meno Toscana |'}[pilot],
            '|'+ '|'.join('---' for _ in range(1+len(SELECTIONS[pilot])+2))+'|']
        cohort=[r for r in report['readings'] if r['pilot']==pilot]
        for row in cohort:
            if row['status']=='not_ready':
                lines.append('| '+' | '.join([row['town'],'Non disponibile: '+', '.join(row['reasons'])]+['—']*(len(SELECTIONS[pilot])+1))+' |');continue
            obs=[f"{fmt(o['observation']['value'])} {o['observation']['unit']} · {o['observation']['period']}" for o in row['observations']]
            calcs=[]
            for c in row['calculations']:
                result=c['result'];label='Δ 2023→2025' if c['query']['operation']=='absolute_change' else 'Comune − '+result['benchmarkScope']
                calcs.append(f"{label}: {fmt(result['value'])} {result['unit']} · {result.get('period',result.get('endPeriod'))}")
            lines.append('| '+' | '.join([row['town']]+obs+calcs)+' |')
        first=next((r for r in cohort if r['observations']),cohort[0])
        lines += ['', '**Definizioni e periodi.**']
        for o in first['observations']:
            obs=o['observation'];lines.append(f"- {o['label']}: {obs['definition']}; {obs['periodBasis']}; universo: {obs['population']}.")
        relation=first['association']
        lines += ['', '**Calcolo congiunto / associazione.** '+relation['status']+': '+', '.join(relation.get('reasons',[]))+'.',
            'Perimetro: i sette comuni, non una relazione stimata all’interno del singolo comune. Associazione descrittiva ecologica; nessun effetto causale o inferenza individuale.',
            '', '**Ipotesi da verificare.** '+settings['hypothesis'],'', '**Opzione da valutare.** '+settings['proposal'],
            '', '**Destinatari.** '+settings['target'],'', '**Indicatori di risultato da predisporre.**']
        lines.extend('- '+item for item in settings['outcomes']);lines+=['','**Dati mancanti per decidere.**']
        lines.extend('- '+item for item in settings['missing']);lines+=['']
        for group in (g for g in report.get('groupReadings',[]) if g['pilot']==pilot):
            lines+=['**Riepilogo del gruppo dei sette comuni.** Stato: `'+group['status']+'`.','',
                '| Indicatore | Numeratore | Denominatore | Scala | Rapporto | Periodi numeratore / denominatore |',
                '|---|---|---|---|---|---|']
            for calc in group['calculations']:
                result=calc['result']
                if calc['status']!='computed':
                    lines.append('| '+calc['query']['selectors'][0]['metric']+' | Non disponibile: '+', '.join(calc['reasons'])+' | — | — | — | — |');continue
                obs=calc['observations'][0]
                lines.append('| '+' | '.join([obs['metric'],fmt(result['numerator']),fmt(result['denominator']),fmt(obs['scale']),fmt(result['value'])+' '+result['unit'],str(obs.get('numeratorPeriod',obs['period']))+' / '+str(obs.get('denominatorPeriod',obs['period']))])+' |')
            lines+=[''];lines.extend('- '+note for note in group['limitations']);lines+=['']
        if relation['status']=='computed':
            result=relation['result']
            sensitivity=[r['coefficient'] for r in result['leaveOneOut'] if r['coefficient'] is not None]
            lines+=['**Associazione descrittiva del gruppo.** '+result['method']+': coefficiente '+fmt(result['coefficient'])+
                '; n='+str(result['n'])+' comuni. Componenti condivise, dimensione demografica e dipendenze territoriali richiedono interpretazione. Nessuna causalità o significatività dedotta; p-value e intervallo di confidenza non stimati.','']
            if sensitivity:
                lines+=['Sensibilità escludendo un comune alla volta: coefficienti da '+fmt(min(sensitivity))+' a '+fmt(max(sensitivity))+'. È un controllo descrittivo, non un intervallo di confidenza. Le coppie e ciascuna esclusione sono conservate nel JSON.','']
    sources={}
    def remember(observation):
        for e in observation['evidence']:
            if e.get('kind')!='catalog_snapshot' and e.get('path'):
                sources[(e['path'],e['sha256'],e.get('sourceUrl') or '')]=e
    for reading in report['readings']:
        for item in reading['observations']:
            remember(item['observation'])
        for calc in reading['calculations']+[reading['association']]:
            for obs in calc.get('observations',[]):remember(obs)
    for group in report.get('groupReadings',[]):
        for calc in group['calculations']:
            for obs in calc['observations']:
                remember(obs)
    lines+=['## Evidenze riproducibili','','| Snapshot | SHA-256 | Percorso ufficiale dichiarato |','|---|---|---|']
    for (path,sha,url),e in sorted(sources.items()):lines.append(f"| `{path}` | `{sha}` | {url} |")
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
