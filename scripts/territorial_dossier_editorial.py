"""Editorial plans and readable dossiers, derived from verified deterministic responses."""
import math

CLASSIFICATIONS = {'supported', 'partially_supported', 'not_determinable'}


def validate_plans(dossier, evidence):
    plans = [dict(dossier['centralPlan'], question=dossier['centralQuestion'],
                  classification=dossier['classification'])] + dossier['secondaryQuestions']
    ids = [q['id'] for q in plans]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate_question_id')
    resolved = []
    for plan in plans:
        status = plan['classification']
        required, context = plan['requiredCaseRefs'], plan['contextCaseRefs']
        if status not in CLASSIFICATIONS:
            raise ValueError('unknown_question_classification')
        if len(set(required + context)) != len(required + context):
            raise ValueError('duplicate_question_case')
        if not plan['answer'] or not plan['question']:
            raise ValueError('missing_answer_boundary')
        if status == 'supported' and plan['missingData']:
            raise ValueError('supported_question_with_decision_gaps')
        if status != 'supported' and not plan['missingData']:
            raise ValueError('missing_information_gap')
        if status == 'not_determinable' and required:
            raise ValueError('undetermined_question_claims_required_answer')
        if status != 'not_determinable' and not required:
            raise ValueError('answer_without_required_evidence')
        for cid in required + context:
            if cid not in evidence:
                raise ValueError('unknown_question_case:' + cid)
            if evidence[cid]['verification'] != 'PASS':
                raise ValueError('unverified_question_case:' + cid)
        for cid in required:
            response = evidence[cid]['response']
            if response['status'] != 'computed':
                raise ValueError('required_case_not_computed:' + cid)
            if status == 'supported' and any(o['value'] is None for o in response['observations']):
                raise ValueError('supported_question_with_missing_observations')
        resolved.append(dict(**plan, results=[dict(caseId=c, role='answer_component' if c in required else 'context_only',
            query=evidence[c]['query'], response=evidence[c]['response'], verification=evidence[c]['verification']) for c in required + context],
            verificationScope='Numerics, provenance and declared coverage checked; editorial interpretation reviewed separately. No automatic certification of decision adequacy or causality.'))
    module_ids = [m['id'] for m in dossier['modules']]
    if len(set(module_ids)) != len(module_ids):
        raise ValueError('duplicate_module_id')
    for module in dossier['modules']:
        if not module['missingData']:
            raise ValueError('module_without_decision_gaps')
        for cid in module['availableCaseRefs']:
            if cid not in evidence or evidence[cid]['verification'] != 'PASS':
                raise ValueError('unknown_or_unverified_module_case:' + cid)
            if evidence[cid]['response']['status'] != 'computed':
                raise ValueError('module_context_not_computed:' + cid)
        expected = 'descriptive_components_available' if module['availableCaseRefs'] and module.get('evidenceRole') != 'context_only' else 'additional_data_required'
        if module['stage'] != expected:
            raise ValueError('module_maturity_overclaim')
    return resolved


def number(value, decimals=1):
    if value is None:
        return 'non disponibile'
    return f'{value:,.{decimals}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def observation(report, cid, code, period=None):
    e = report['evidence'][cid]
    if e['verification'] != 'PASS' or e['response']['status'] != 'computed':
        raise ValueError('unverified_story_input:' + cid)
    rows = [o for o in e['response']['observations'] if o['geography'] == code and (period is None or o['period'] == period)]
    if len(rows) != 1 or rows[0]['value'] is None:
        raise ValueError('ambiguous_or_missing_story_input:' + cid + '/' + code)
    return rows[0]


def result_lines(report, cid):
    r = report['evidence'][cid]['response']
    lines = [f"Richiesta `{cid}` — `{r['query']['operation']}`; esito `{r['status']}`."]
    if r['status'] != 'computed':
        return lines + ['Motivi: ' + ', '.join(r['reasons'])]
    units = {'percent': '%', 'currency': '€', 'millionCurrency': 'milioni €', 'people': 'persone/addetti secondo definizione', 'studentsPerClass': 'alunni/classe'}
    values = '; '.join(report['townNames'].get(o['geography'], o['geography']) + ' ' + o['period'] + ': ' + number(o['value']) + ' ' + units.get(o['unit'],o['unit']) for o in r['observations'])
    lines += ['', '**Risultati:** ' + values]
    result = r.get('result') or {}
    if isinstance(result.get('value'), (int, float)):
        lines += ['', 'Risultato dell’operazione: ' + number(result['value']) + ' ' + units.get(result.get('unit'), result.get('unit', '')) + '.']
    lines += ['', '**Universi e definizioni:** ' + '; '.join(sorted({o['population'] + ' — ' + o['definition'] for o in r['observations']})),
              '', '**Fonti:** ' + '; '.join(f'[{s}]({s})' for s in sorted({o['source'] for o in r['observations']})),
              '', '**Avvertenze:** ' + (', '.join(r['warnings']) or 'nessuna aggiuntiva')]
    return lines


def render_questions(report):
    lines = ['# Repertorio ragionato delle domande', '',
        'Le domande sostanziali sono distinte dai controlli metodologici. Ogni nuova domanda ha un piano esplicito: richieste necessarie → risultati → confine dell’interpretazione → informazioni mancanti. I risultati di contesto non certificano bisogni, efficacia o causalità.', '',
        'Le risposte numeriche sono verificate contro aspettative A6 indipendenti o ancore pubbliche dichiarate. Le interpretazioni sono una revisione editoriale, non un risultato automaticamente certificato dal software. Precisione integrale, puntatori, hash e richieste complete restano in `evidence.json` riproducibile.', '',
        '## Le 20 domande A6: baseline conservata', '', 'Autorità: `ci/a6-territorial-acceptance-questions.json`, immutato. I riferimenti includono casi fuori dalla selezione editoriale: la suite A6 ne conserva la verifica.']
    for q in report['baselineQuestionsPreserved']['questions']:
        lines += ['', f"### {q['id']} — {q['classification']}", '', q['question'], '',
            '**Fenomeno:** ' + q['problem'], '', '**Risposta oggi:** ' + q['answerToday'], '',
            '**Query verificate A6:** ' + ', '.join('`'+c+'`' for c in q['requestCaseIds']), '',
            '**Conclusioni escluse:** ' + q['unjustifiedConclusions'], '',
            '**Dati mancanti:** ' + '; '.join(q['missingData']), '', '**Valore:** ' + q['decisionValue']]
    lines += ['', '## Approfondimenti del programma', '',
        'Non sommare formulazioni, query e dossier come se fossero analisi complete. Le domande centrali sono programmi di indagine; le nuove domande restano parziali o non determinabili dove mancano le evidenze decisionali. I sotto-dossier sono descritti in [MODULES.md](MODULES.md).']
    for d in report['dossiers']:
        lines += ['', '### ' + d['title'], '', '**Competenze da verificare negli atti vigenti:** ' + d['competences'], '',
            '**Domande A6 riusate e approfondite, non nuove certificazioni:** ' + (', '.join(d['baselineQuestionRefs']) or 'nessuna corrispondenza diretta'), '', '**Opzioni da approfondire:** ' + d['optionsToInvestigate'], '', '**Monitoraggio:** ' + d['monitoring']]
        for q in d['questionEvidence']:
            lines += ['', f"#### {q['id']} — {q['classification']}", '', q['question'], '',
                '**Risposta oggi e interpretazione consentita:** ' + q['answer'], '',
                '**Informazioni mancanti:** ' + '; '.join(q['missingData']), '',
                '**Valore aggiunto:** ' + d['knowledgeValue'], '', d['interpretationLimit']]
            if not q['requiredCaseRefs']:
                lines += ['', 'Nessuna richiesta del catalogo attuale misura le variabili necessarie. Le eventuali richieste seguenti sono soltanto contesto.']
            if q['id'] == d['centralPlan']['id']:
                lines += ['', '**Piano centrale, dettagliato nelle domande seguenti:** ' + ', '.join('`'+c+'`' for c in q['requiredCaseRefs']) + ('; solo contesto: ' + ', '.join('`'+c+'`' for c in q['contextCaseRefs']) if q['contextCaseRefs'] else '')]
                continue
            for c in q['requiredCaseRefs'] + q['contextCaseRefs']:
                lines += ['', ('**Componente della risposta**' if c in q['requiredCaseRefs'] else '**Solo contesto**'), ''] + result_lines(report, c)
        lines += ['', '#### Controlli metodologici, separati dalle domande territoriali', '']
        lines += ['- ' + q['question'] + ' ' + q['reason'] for q in d['methodologicalChecks']]
    return '\n'.join(lines) + '\n'


def render_modules(report):
    lines = ['# Sotto-dossier e lacune informative', '',
        'Questa è una mappa del lavoro successivo, non una dichiarazione di nuovi dati acquisiti. “Componenti descrittive disponibili” significa che alcune query sono eseguibili; non significa dossier completo o domanda decisionale risolta.', '',
        'Ambiente/acqua/rifiuti e turismo condividono le stesse evidenze; non si sommano carichi o costi. Bilanci, opere e capacità amministrativa restano universi collegati ma distinti. Fonti metodologiche esterne studiate, come OpenCivitas, non diventano dataset acquisiti.', '']
    for d in report['dossiers']:
        lines += ['## ' + d['title'], '', '**Responsabilità e monitoraggio:** ' + d['competences'] + ' ' + d['monitoring'], '']
        for m in d['modules']:
            lines += ['### ' + m['title'], '', m['question'], '',
                '**Stadio:** ' + ('componenti descrittive disponibili; decisione da approfondire' if m['stage'] == 'descriptive_components_available' else 'ulteriori dati necessari; risposta non determinabile'), '',
                ('**Evidenze disponibili, soltanto contesto:** ' if m.get('evidenceRole') == 'context_only' else '**Evidenze disponibili:** ') + (', '.join('`'+c+'`' for c in m['availableCaseRefs']) or 'nessuna misura diretta acquisita'), '',
                '**Composizione:** ' + m['composition'], '', '**Informazioni necessarie:** ' + '; '.join(m['missingData']), '',
                '**Relazioni:** ' + ', '.join(m['relatedDossiers'] or d['relatedDossiers']), '']
    return '\n'.join(lines) + '\n'


def source_notes(report, ids):
    lines = ['## Fonti e riproducibilità', '',
        'I valori esposti sono arrotondati per la lettura. Il JSON riproducibile conserva tutta la precisione, richieste, risultati, hash degli snapshot e puntatori. Le fonti sotto sono quelle delle osservazioni acquisite, non una verifica della loro disponibilità online oggi.', '',
        f"Catalogo congelato `{report['catalogSha256']}`; motore `{report['engineSha256']}`.", '']
    for cid in ids:
        e = report['evidence'][cid];obs = e['response']['observations'];selector = e['query']['selectors'][0]
        lines += [f"- `{cid}`: `{e['query']['operation']}`, `{selector['metric']}`, dimensione `{selector.get('dimension','total')}`; periodi " + ', '.join(sorted({o['period'] for o in obs})) + '. ' + '; '.join(f'[{s}]({s})' for s in sorted({o['source'] for o in obs}))]
    lines += ['', 'Rigenerazione:', '', '```bash', 'python scripts/build_territorial_dossier_evidence.py --catalog dist/data/site-data.json --output-dir /tmp/territorial-dossiers', '```', '',
        'Riferimenti editoriali: [domande](QUESTIONS.md), [sotto-dossier](MODULES.md), [metodo](METHOD.md). Nessun nuovo dato, adapter o intervento pubblico è introdotto da questa analisi.']
    return '\n'.join(lines)


def render_demos(report):
    """Numbers and comparative wording use the same checked inputs; never a second catalog."""
    mass, via = '046018', '046033'
    periods = {'census_employment_primary':'2024','business_asia_cumulative':'2018-2023','business_asia_employment':'2023','business_frame_industry_va':'2023','business_frame_industry_wages':'2023','child_weighted':'2024/25','school_class_size':'2024/25','school_full_time':'2024/25','school_students':'2024/25','invalsi_invalsiImplicitDispersion_g8_current':'2024-25'}
    def val(cid, geo=mass):
        return observation(report, cid, geo, periods[cid])['value']
    emp = 'census_employment_primary';growth = 'business_asia_cumulative';jobs = 'business_asia_employment'
    va = 'business_frame_industry_va';wage = 'business_frame_industry_wages';services = 'business_frame_services_history'
    # The prose directions must remain true; new data require an editorial review, not silently stale wording.
    if not (val(emp) > val(emp, via) and val(growth) < val(growth, via)):
        raise ValueError('labour_narrative_direction_changed')
    if not (observation(report, services, mass, '2023')['value'] > observation(report, services, mass, '2015')['value']):
        raise ValueError('services_narrative_direction_changed')
    capacity = 'child_weighted';size = 'school_class_size';full = 'school_full_time';students = 'school_students';outcomes = 'invalsi_invalsiImplicitDispersion_g8_current'
    if not (val(capacity) < val(capacity, via) and val(size) < val(size, via) and val(full) > val(full, via)):
        raise ValueError('education_narrative_direction_changed')
    for code in ('046028','046030'):
        if val(capacity, code) != 0:
            raise ValueError('zero_capacity_narrative_changed')
    capr = report['evidence'][capacity]['response']['result']
    rows = report['evidence'][capacity]['response']['observations']
    if {o['geography'] for o in rows} != set(report['townNames']) or any(o['period'] != '2024/25' for o in rows):
        raise ValueError('capacity_story_coverage_changed')
    partial = report['evidence'][outcomes]['response']['observations']
    if {o['geography'] for o in partial if o['value'] is None} != {'046013','046028','046030'}:
        raise ValueError('educational_outcome_missing_coverage_changed')
    if not math.isclose(capr['value'], sum(o['numerator'] for o in rows) / sum(o['denominator'] for o in rows) * 100, abs_tol=1e-10):
        raise ValueError('capacity_aggregate_not_ratio_of_sums')
    work = f'''# Massarosa: attività economiche e opportunità per i residenti

A Massarosa i dati descrivono un territorio con una base di attività locali cresciuta tra 2018 e 2023 e un tasso di occupazione residente 2024 superiore a quello di Viareggio. Le due informazioni sono utili insieme, ma riguardano periodi e popolazioni differenti: non dimostrano che la crescita delle attività abbia creato lavoro per i residenti.

## Che cosa osserviamo

| Misura | Periodo | Massarosa | Viareggio |
|---|---|---:|---:|
| Occupati fra i residenti di 25–64 anni | 2024 | {number(val(emp))}% | {number(val(emp,via))}% |
| Crescita cumulata delle unità locali ASIA rispetto al 2018 | 2018–2023 | +{number(val(growth))}% | +{number(val(growth,via))}% |
| Addetti medi annui nelle unità locali ASIA, sul luogo di lavoro | 2023 | {number(val(jobs),2)} | {number(val(jobs,via),2)} |
| Valore aggiunto industriale nominale | 2023 | {number(val(va),2)} milioni € | {number(val(va,via),2)} milioni € |
| Retribuzione lorda media per dipendente nell’industria | 2023 | {number(val(wage),0)} € | {number(val(wage,via),0)} € |

Il tasso di occupazione di Massarosa supera quello di Viareggio di {number(val(emp)-val(emp,via))} punti percentuali. La crescita cumulata delle unità locali ASIA è invece inferiore. Questo confronto rende visibili due dimensioni dello sviluppo: le condizioni dei residenti e l’attività localizzata. Non produce una graduatoria complessiva dei Comuni.

Gli addetti ASIA sono una media annua: per questo il valore può avere decimali. Non sono il numero dei residenti occupati. Gli importi industriali assoluti risentono anche della diversa dimensione delle economie locali; non sono misure di produttività per abitante.

## Una trasformazione osservabile nei servizi

A Massarosa il valore aggiunto dei servizi passa, in termini nominali, da {number(observation(report,services,mass,'2015')['value'],2)} milioni di euro nel 2015 a {number(observation(report,services,mass,'2023')['value'],2)} milioni nel 2023. La differenza verificata è {number(report['evidence'][services]['response']['result']['value'],2)} milioni.

È un segnale di cambiamento della produzione monetaria dei servizi. Non è crescita a prezzi costanti e non dimostra che lavoratori siano passati dall’industria ai servizi. Per rispondere a quella domanda occorrono un pannello settoriale omogeneo e informazioni sulle transizioni professionali. La retribuzione industriale media non descrive reddito disponibile, distribuzione dei salari o qualità dei contratti.

## Perché interessa chi deve decidere

Queste evidenze suggeriscono quali domande porre a imprese, servizi per il lavoro e formazione: quali professionalità vengono richieste? Quali residenti incontrano barriere di accesso? Gli spostamenti, gli orari e i servizi alle famiglie limitano alcune opportunità? Sono ipotesi di approfondimento; dai dati presentati non deriva automaticamente un programma di formazione, una nuova area produttiva o un incentivo.

Il Comune può approfondire accessibilità delle aree e servizi locali; politiche del lavoro e formazione richiedono il coinvolgimento regionale e degli attori competenti. Competenze e deleghe vanno verificate negli atti vigenti prima di definire un intervento.

## Che cosa manca e come seguire un eventuale intervento

Mancano dati recenti e contemporanei, transizioni dei residenti, profili richiesti, qualità e durata dei contratti. Non possiamo descrivere la congiuntura del 2026 con il solo dato ASIA 2023.

Per un programma specifico andrebbero definiti destinatari, accessi, completamenti e risultati occupazionali a distanza di tempo, mantenendo distinti partecipanti e popolazione residente. Una variazione comunale dopo l’intervento non ne dimostra l’effetto: servono un disegno di valutazione e un confronto appropriato.

## Il perimetro di questa dimostrazione

Viareggio è un confronto interno alla Versilia con dati compatibili per ciascuna misura, non un territorio certificato come simile a Massarosa. Differenze di dimensione, settori e pendolarismo vanno considerate; non è stato acquisito un pannello di territori comparabili.

L’Atlante Registro Imprese 2025 resta un universo distinto da ASIA: le sue 20.325 unità locali nei sette Comuni non possono essere aggiunte agli stock ASIA o usate come prosecuzione della stessa serie. Il totale è riconciliato dalla query `atlas_territory_2025`; nessuna somma dei livelli ATECO entra nelle misure sopra.

'''
    # The Atlas statement must also be verified, even though it is contextual to this story.
    atlas = report['evidence']['atlas_territory_2025']['response']['observations']
    if sum(o['value'] for o in atlas) != 20325:
        raise ValueError('atlas_context_changed')
    work += source_notes(report, [emp,growth,jobs,va,wage,services,'atlas_territory_2025']) + '\n'
    capacity_table = '\n'.join(f"| {report['townNames'][o['geography']]} | {number(o['numerator'],0)} | {number(o['denominator'],0)} | {number(o['value'])}% |" for o in rows)
    edu = f'''# Massarosa: infanzia, organizzazione scolastica e domande ancora aperte

A Massarosa convivono una ricettività educativa potenziale 0–3 relativamente contenuta e una quota di alunni della primaria a tempo pieno superiore a quella di Viareggio. Sono servizi, età e denominatori diversi. Separarli permette di individuare quali bisogni approfondire prima di proporre nuovi posti o modifiche alla rete scolastica.

## Servizi 0–3: partire dai posti potenziali, poi verificare la domanda

Nell’anno educativo 2024/25 Massarosa ha {number(observation(report,capacity,mass)['numerator'],0)} posti potenziali per {number(observation(report,capacity,mass)['denominator'],0)} bambini residenti di 3–36 mesi: {number(val(capacity))} posti ogni 100 bambini. Viareggio presenta {number(val(capacity,via))} posti ogni 100. Il confronto completo mette in luce situazioni locali diverse:

| Comune | Posti potenziali | Bambini residenti di 3–36 mesi | Posti ogni 100 bambini |
|---|---:|---:|---:|
{capacity_table}

Seravezza e Stazzema hanno zero posti locali nello snapshot, con denominatori positivi. Questo non prova che nessun bambino utilizzi un servizio: possono esserci accessi fuori Comune, non misurati qui. La ricettività potenziale non è frequenza effettiva né domanda insoddisfatta.

L’aggregato dei sette Comuni è {number(capr['value'])} posti ogni 100 bambini: {number(capr['numerator'],0)} posti divisi per {number(capr['denominator'],0)} bambini. È un rapporto fra somme, non la media semplice delle sette percentuali; resta un indicatore di capacità potenziale territoriale.

Prima di decidere un’espansione occorrono domande e liste di attesa, età e zona di residenza, tariffe, orari, posti effettivamente occupati e accessi intercomunali. Il rapporto attuale non consente di calcolare quanti nuovi posti servano.

## Scuola: classi e tempo pieno descrivono l’organizzazione

| Misura nelle scuole localizzate nel Comune | Anno scolastico | Massarosa | Viareggio |
|---|---|---:|---:|
| Alunni nel perimetro MIM acquisito | 2024/25 | {number(val(students),0)} | {number(val(students,via),0)} |
| Alunni per classe | 2024/25 | {number(val(size))} | {number(val(size,via))} |
| Alunni della primaria a tempo pieno | 2024/25 | {number(val(full))}% | {number(val(full,via))}% |

A Massarosa le classi hanno mediamente meno alunni e la quota primaria a tempo pieno è maggiore. Il primo rapporto usa tutti gli alunni e le classi del perimetro; il secondo usa soltanto gli alunni della primaria. Non si possono applicare le percentuali del tempo pieno al totale degli alunni né dedurre qualità didattica dalla dimensione delle classi.

Gli iscritti sono localizzati nelle scuole del Comune, non conteggiati per residenza. Questi dati non dicono se gli istituti siano pochi o troppi: occorrono bacini per sede, capacità, spostamenti e scenari demografici. La dichiarazione di accessibilità degli edifici è inoltre diversa dalla verifica concreta dei percorsi e dei servizi di trasporto.

## Risultati educativi: un segnale distinto dall’offerta

Il rischio di dispersione implicita pubblicato da INVALSI per il grado 8 (terza secondaria di primo grado) nel 2024–25 è {number(val(outcomes))}% a Massarosa e {number(val(outcomes,via))}% a Viareggio. Secondo le [note ufficiali INVALSI](https://serviziostatistico.invalsi.it/download/1024/eccellenza-accademica-e-dispersione-scolastica-implicita-valori-percentuali/11730/note_dispersione_e_eccellenti.csv), identifica risultati bassi insieme in italiano, matematica e inglese: livelli 1–2 nelle prime due prove e competenze inferiori ad A2 nelle due prove di inglese. La percentuale usa gli studenti con dati validi in tutte e quattro le prove. È un indicatore di fragilità negli apprendimenti, distinto dal conteggio degli abbandoni. Riguarda gli studenti testati nelle scuole localizzate, non tutti i giovani residenti e non gli stessi bambini descritti dai servizi 0–3 o dalla primaria.

La copertura dei sette Comuni è parziale: i valori mancanti di Forte dei Marmi, Seravezza e Stazzema restano non disponibili. Nessuna media territoriale viene ricostruita. Il segnale merita approfondimento su partecipazione alle prove e contesto degli alunni; non giustifica una classifica delle scuole né una spiegazione causale collegata al tempo pieno.

## Dall’osservazione a un’istruttoria utile

Si possono approfondire separatamente accessibilità dei servizi 0–3, organizzazione per plesso, trasporto e risultati educativi. Comune, scuole autonome e Regione hanno ruoli diversi; orari didattici, rete scolastica e servizi comunali richiedono verifiche congiunte delle competenze e degli atti vigenti.

Per eventuali interventi si potrebbero monitorare domande accolte e non accolte, tempi di accesso, utilizzo effettivo, costo per prestazione, continuità dei percorsi e risultati educativi con copertura dichiarata. Sono specifiche da costruire, non nuove misure già acquisite. Un cambiamento di indicatore dopo un intervento non basta a provarne l’efficacia.

Il collegamento con il lavoro femminile è una domanda pertinente, ma i dati disponibili non stimano l’effetto di nuovi posti sull’occupazione: mancano condizioni dei genitori, domanda effettiva e un disegno di valutazione. Anche le transizioni scuola–lavoro rimangono un sotto-dossier con lacune informative.

'''
    edu += source_notes(report, [capacity,'child_zero',students,size,full,'school_access_defined',outcomes]) + '\n'
    return {'MASSAROSA_LAVORO.md': work, 'MASSAROSA_INFANZIA_SCUOLA.md': edu}
