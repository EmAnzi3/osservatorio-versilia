"""One public reading, derived only from the original verified A7 bundle.

Editorial choices reference existing cases; they are not a metric catalog.
The HTML used by the site and the printable report is generated together.
"""
from __future__ import annotations
import hashlib
import copy
import html
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

FOCUS = '046018'
QUESTION = 'infanzia-centrale'
NAMES = {'046005':'Camaiore','046013':'Forte dei Marmi','046018':'Massarosa','046024':'Pietrasanta','046028':'Seravezza','046030':'Stazzema','046033':'Viareggio'}
SOURCES = {'dati.toscana.it':'Regione Toscana', 'dati.istruzione.it':'Ministero dell’Istruzione e del Merito', 'serviziostatistico.invalsi.it':'INVALSI'}
E = html.escape
ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = 'Osservatorio Versilia'
WEBSITE = 'osservatorioversilia.it'
LICENSE_URL = 'https://creativecommons.org/licenses/by/4.0/deed.it'
REUSE_NOTE = ('Testi, elaborazioni e visualizzazioni originali sono disponibili con licenza '
    'CC BY 4.0, citando Osservatorio Versilia. Dati e materiali di terzi mantengono '
    'le condizioni d’uso e le licenze dei rispettivi titolari.')


def report_brand(town):
    """Use the existing canonical vector mark; no copied or remote logo asset."""
    mark = (ROOT/'assets/brand-mark.svg').read_text().strip()
    return '<div class="edu-report-brand">'+mark+'<div><strong>'+PUBLISHER+'</strong><span>Analisi territoriali · '+WEBSITE+'</span></div><p class="edu-kicker">'+E(town.upper())+'<br>OFFERTA EDUCATIVA</p></div>'


def number(value, precision=1):
    if value is None:return 'n.d.'
    return f'{value:,.{precision}f}'.replace(',', '\u0000').replace('.', ',').replace('\u0000', '.')


def territorial_evidence(bundle, catalog_path):
    """Expand existing school requests, without changing approved pilot answers."""
    from semantic_query_engine import QueryEngine, ROOT
    from semantic_methodological_checks import MethodologicalVerifier
    from build_a7_static_pilot import facts
    from build_territorial_dossier_evidence import portable_evidence
    engine = QueryEngine(catalog_path, layer='effective')
    if engine.catalog_hash != bundle['catalogSha256'] or engine.module_hash != bundle['engineSha256']:
        raise ValueError('education_catalog_mismatch')
    verifier = MethodologicalVerifier(catalog_path, ROOT)
    towns = [town['code'] for town in engine.catalog['towns']]
    result = {}
    for cid in ['school_students', 'school_class_size', 'school_full_time', 'school_access_defined']:
        query = copy.deepcopy(bundle['cases'][cid]['query'])
        query['selectors'][0]['towns'] = towns
        response = engine.query(query)
        errors = verifier.verify(response)
        if response['status'] != 'computed' or errors:
            raise ValueError('education_territorial_request_failed:'+cid+':'+str(errors))
        case = portable_evidence(dict(query=query, response=response,
            facts=facts(cid, response, engine.catalog), reference=bundle['cases'][cid]['reference']))
        previous = bundle['cases'][cid]['response']['observations']
        for observation in previous:
            if next(o for o in case['response']['observations'] if o['geography']==observation['geography']) != observation:
                raise ValueError('education_original_observation_changed:'+cid)
        result[cid] = case
    return result


def build_reading(bundle, commit, territorial_cases, focus_code=FOCUS):
    if focus_code not in NAMES:
        raise ValueError('education_unknown_territory')
    town = NAMES[focus_code]
    date = datetime.fromisoformat(subprocess.check_output(['git','show','-s','--format=%cI',commit], cwd=Path(__file__).resolve().parents[1],text=True).strip()).astimezone(timezone.utc)
    q = next(q for q in bundle['questions'] if q['id'] == QUESTION)
    refs = q['requiredCaseRefs'] + q['contextCaseRefs']
    cases = {cid:bundle['cases'][cid] for cid in refs}
    if set(territorial_cases) != {'school_students','school_class_size','school_full_time','school_access_defined'}:
        raise ValueError('education_territorial_cases_missing')
    for cid, case in territorial_cases.items():
        rows = [f for f in case['facts'] if f['kind']=='observation']
        if len(rows)!=7 or {f['geography'] for f in rows}!=set(NAMES):
            raise ValueError('education_territorial_coverage_incomplete:'+cid)
    cases.update(territorial_cases)
    for cid, case in cases.items():
        for fact in case['facts']:
            if fact['kind'] == 'observation':
                observation = next(o for o in case['response']['observations'] if o['geography'] == fact['geography'])
                if fact['value'] != observation['value']:
                    raise ValueError('education_narrative_needs_review:'+cid)
    def observations(cid):return [f for f in cases[cid]['facts'] if f['kind']=='observation']
    def focus(cid):
        rows = [f for f in observations(cid) if f['geography']==focus_code]
        if len(rows)!=1:raise ValueError('education_focus_missing:'+cid)
        return rows[0]
    bindings = []
    def value(cid, precision=1):
        f=focus(cid);bindings.append({'caseId':cid,'pointer':f['responsePointer'],'value':f['value']})
        return f'<span data-evidence-case="{cid}" data-evidence-pointer="{f["responsePointer"]}">{number(f["value"],precision)}</span>'
    def source(cid):
        from urllib.parse import urlparse
        url=observations(cid)[0]['source'];name=SOURCES[urlparse(url).hostname]
        return f'<a href="{E(url,quote=True)}">{name}</a>'
    def chart(cid, title, explanation, unit='%', percent=True):
        rows=observations(cid);base=rows[0]
        keys=['period','unit','dimension','population','definition','method','source']
        if not all(all(f[k]==base[k] for k in keys) for f in rows):raise ValueError('education_non_comparable:'+cid)
        values=[f['value'] for f in rows if f['value'] is not None]
        if any(v<0 for v in values):raise ValueError('education_negative_chart:'+cid)
        maximum=100 if percent else max(1,math.ceil(max(values,default=1)))
        if any(v>maximum for v in values):raise ValueError('education_scale_exceeded:'+cid)
        bars=[]
        # Alphabetical order, never a performance ranking. Null rows retain their place.
        for f in sorted(rows,key=lambda f:NAMES[f['geography']]):
            name=NAMES[f['geography']];v=f['value'];missing=v is None
            observation=next(o for o in cases[cid]['response']['observations'] if o['geography']==f['geography'])
            components=''
            if observation.get('numerator') is not None and observation.get('denominator') is not None:
                numerator=number(observation['numerator'],0);denominator=number(observation['denominator'],0)
                label='alunni' if cid=='school_full_time' else 'risposte definite' if cid=='school_access_defined' else ''
                description=f'{numerator} alunni / {denominator} classi' if cid=='school_class_size' else f'{numerator} su {denominator} {label}'
                components=f'<small class="edu-components">{description}</small>'
            track='<span class="edu-missing">Non disponibile</span>' if missing else f'<span class="edu-track" aria-hidden="true"><span class="edu-bar" style="width:{100*v/maximum:.8f}%" data-value="{v}" data-maximum="{maximum}" data-geography="{f["geography"]}" data-period="{f["period"]}"></span></span>'
            suffix=' %' if percent and not missing else ''
            bars.append(f'<li class="{"edu-focus" if f["geography"]==focus_code else ""}" data-evidence-case="{cid}" data-evidence-pointer="{f["responsePointer"]}"><span class="edu-town">{name}{components}</span>{track}<strong>{number(v,0 if unit=="alunni" else 1)}{suffix}</strong></li>')
        available=len(values)
        coverage=f'{len(rows)} Comuni della Versilia' if len(rows)==7 else 'Massarosa e Viareggio: confronto descrittivo selezionato, non un gruppo di territori equivalenti'
        return f'''<figure class="edu-chart" data-education-case="{cid}"><figcaption><h4>{title}</h4><p>{explanation}</p></figcaption><p class="edu-chart-meta">Anno scolastico {E(base['period'])} · {coverage}. Valori disponibili: {available} su {len(rows)}.</p><ul class="edu-bars">{''.join(bars)}</ul><p class="edu-chart-meta">Scala da 0 a {number(maximum,0)} {unit}. {E(town)} è evidenziato nel confronto; Comuni in ordine alfabetico. <span class="edu-chart-credit">Elaborazione: {PUBLISHER} · Fonte: {source(cid)}.</span></p></figure>'''
    if any(f['value'] != 0 for f in observations('child_zero')):
        raise ValueError('education_zero_narrative_needs_review')
    period=focus('school_full_time')['period']
    lead=f'<div class="edu-opening"><p class="edu-kicker">CRESCERE A {E(town.upper())}</p><h3>Un posto al nido.<br>Tempo per imparare.<br>Spazi da vivere.</h3><p class="edu-lead">Per una famiglia, l’offerta educativa entra nell’organizzazione di ogni giornata. A {E(town)}, che cosa caratterizza i servizi e la rete scolastica? Leggiamo insieme prima infanzia, tempo pieno e spazi, nel confronto con gli altri Comuni della Versilia.</p><p class="edu-opening-foot">Posti disponibili, frequenza e accesso effettivo descrivono aspetti diversi.</p></div>'
    local_capacity=focus('child_weighted')['value']
    territorial_capacity=next(f for f in cases['child_weighted']['facts'] if f['kind']=='result')['value']
    full_time=focus('school_full_time')['value']
    relation='inferiore al' if local_capacity is not None and local_capacity<territorial_capacity else 'superiore al' if local_capacity is not None and local_capacity>territorial_capacity else 'uguale al'
    capacity_text=('Nessun posto potenziale censito per i bambini di 3–36 mesi del Comune; questo non esclude accessi in altri territori.' if local_capacity==0 else f'Posti potenziali ogni cento bambini di 3–36 mesi: valore {relation} rapporto della Versilia ({number(territorial_capacity)}%). Non misura iscritti o domande soddisfatte.' if local_capacity is not None else 'La capacità potenziale locale non è disponibile: nessuna stima sostituisce il dato.')
    time_text=('Il tempo pieno riguarda tutti gli alunni della primaria censiti.' if full_time==100 else 'Il tempo pieno riguarda più della metà degli alunni della primaria.' if full_time is not None and full_time>50 else 'Il tempo pieno riguarda metà degli alunni della primaria.' if full_time==50 else 'Il tempo pieno riguarda meno della metà degli alunni della primaria.' if full_time is not None else 'La diffusione del tempo pieno non è disponibile.')
    conclusions=[dict(id='capacita',caseId='child_weighted',text=capacity_text,question='Quanta domanda è accolta e quanta rimane in attesa?',reference='Confronto con il rapporto fra somme dei sette Comuni',period=focus('child_weighted')['period']),
        dict(id='tempo',caseId='school_full_time',text=time_text,question='La distribuzione per plesso e gli orari rispondono alle richieste?',reference='Alunni della primaria nelle scuole del Comune',period=focus('school_full_time')['period']),
        dict(id='rete',caseId='school_students',text=f'In media {number(focus("school_class_size")["value"])} alunni per classe. Iscritti e classi descrivono la rete, senza misurare da soli capienza o qualità.',question='Da dove arrivano gli alunni e come cambiano i bacini dei plessi?',reference='Scuole presenti nel Comune; residenza degli alunni distinta',period=focus('school_students')['period'])]
    for conclusion in conclusions:
        cid=conclusion['caseId'];fact=focus(cid)
        conclusion['evidence']=[dict(caseId=cid,pointer=fact['responsePointer'],value=fact['value'])]
    conclusions[0]['evidence'].append(dict(caseId='child_weighted',pointer='/result/value',value=territorial_capacity))
    class_fact=focus('school_class_size')
    conclusions[2]['evidence'].append(dict(caseId='school_class_size',pointer=class_fact['responsePointer'],value=class_fact['value']))
    cards=[]
    for i,(cid,label,unit,precision) in enumerate([('child_weighted','PRIMA INFANZIA','%',1),('school_full_time','TEMPO PIENO','%',1),('school_students','ALUNNI NELLE SCUOLE','',0)]):
        c=conclusions[i];suffix=unit if focus(cid)['value'] is not None else ''
        cards.append(f'<div data-conclusion="{c["id"]}"><span class="edu-kicker">{label}</span><strong>{value(cid,precision)}{suffix}</strong><p>{E(c["text"])}</p><small>{E(c["period"])} · {E(c["reference"])}</small><details><summary>La questione da approfondire</summary><p>{E(c["question"])}</p></details></div>')
    findings='<div class="edu-findings">'+''.join(cards)+'</div>'
    overview='<div class="edu-cover-grid">'+lead+f'<div class="edu-focus-facts"><p class="edu-kicker">{E(town.upper())}, CHE COSA EMERGE</p>'+findings+'</div></div>'+chart('school_full_time','Il tempo pieno non ha la stessa diffusione in tutta la Versilia',f'A {E(town)}: {time_text[0].lower()+time_text[1:]} Il numero di alunni accanto alla quota aiuta a leggere anche le reti più piccole.')+'<aside class="edu-reading-note"><span class="edu-kicker">LA DOMANDA CHE CONTA</span><h3>L’offerta incontra davvero le richieste delle famiglie?</h3><p>Per capirlo servono anche domande accolte, liste d’attesa, orari e tariffe. I capitoli mettono a fuoco ciò che i numeri descrivono e le informazioni da portare al tavolo.</p></aside>'
    chapters=[]
    def chapter(id,title,intro,body):chapters.append(dict(id=id,title=title,html=f'<p class="edu-chapter-number">{len(chapters)+1:02d} / ESPLORA IL TEMA</p><p class="edu-chapter-intro">{intro}</p>'+body))
    ratio=next(f for f in cases['child_weighted']['facts'] if f['kind']=='result')
    bindings.append({'caseId':'child_weighted','pointer':ratio['responsePointer'],'value':ratio['value']})
    chapter('nidi','Prima infanzia','Quanti posti possono offrire i servizi, rispetto ai bambini residenti?',
        chart('child_weighted','La capacità potenziale cambia molto tra i Comuni','Posti potenziali ogni cento bambini residenti tra 3 e 36 mesi. Il rapporto non misura domande accolte, frequenza o liste d’attesa.')+
        f'<h3>Leggere il totale senza confondere le medie</h3><p>Per la Versilia il rapporto ricostruito è <strong data-evidence-case="child_weighted" data-evidence-pointer="/result/value">{number(ratio["value"])}%</strong>: somma dei posti divisa per la somma dei bambini, non media semplice delle percentuali comunali.</p><p>Gli zeri di Seravezza e Stazzema sono valori presenti nella rilevazione. Non dimostrano che le famiglie non utilizzino servizi in altri Comuni e non misurano da soli il bisogno insoddisfatto.</p><h3>Che cosa approfondire</h3><p>Domande presentate e accolte, attese per età e zona, orari, tariffe e spostamenti tra Comuni. Servono per distinguere capacità teorica e possibilità concreta di usare il servizio.</p>')
    chapter('scuola','Tempo e organizzazione','Tra tempo pieno e dimensione delle classi, sette reti scolastiche da leggere nel loro contesto.',
        chart('school_full_time','Il tempo pieno: una componente dell’offerta','Alunni a tempo pieno sul totale degli alunni della primaria nelle scuole del Comune. Accanto alle quote, le dimensioni effettive di ciascuna rete.')+
        chart('school_class_size','Quanti alunni ci sono, in media, in una classe','La media sintetizza l’organizzazione della rete. Per capire le singole sedi occorre il dettaglio per plesso e ordine scolastico.',unit='alunni/classe',percent=False)+
        f'<p>A {E(town)} gli alunni delle scuole del Comune sono <strong>{value("school_students",0)}</strong>. Il confronto comprende tutte le sette reti scolastiche, con dimensioni diverse: i conteggi assoluti non misurano la copertura dei bisogni.</p><h3>Che cosa approfondire</h3><p>Bacini di provenienza, capienza e iscrizioni per plesso, tempi di percorso e richieste di tempo pieno non accolte. Non si ricostruisce una domanda futura da una singola fotografia.</p>')
    chapter('spazi','Spazi e accessibilità','Le caratteristiche dichiarate degli edifici sono una parte della lettura, distinta dall’esperienza quotidiana degli alunni.',
        chart('school_access_defined','Accessibilità: la percentuale riguarda le risposte definite','La quota esclude le risposte non definite. Un valore del 100% non certifica l’accessibilità di tutte le scuole o di ogni percorso casa–scuola.')+
        f'<p>A {E(town)} la quota delle risposte definite positive è {value("school_access_defined")}%. Il denominatore è riportato nel grafico: le risposte non definite non entrano nella quota.</p>'+
        '<h3>Che cosa approfondire</h3><p>Completezza delle risposte, verifiche per edificio e percorsi, barriere residue e bisogni degli alunni. Il dato dichiarato non è una certificazione tecnica di sicurezza o qualità.</p>')
    learning=focus('invalsi_invalsiImplicitDispersion_g8_current')
    learning_text=(f'<p>Per {E(town)} il dato di dispersione implicita al grado 8 non è disponibile nella rilevazione {E(learning["period"])}. Il dato mancante non viene sostituito con zero o con il valore di un altro Comune.</p>' if learning['value'] is None else f'<p>Per le scuole di {E(town)} la dispersione implicita al grado 8 è {value("invalsi_invalsiImplicitDispersion_g8_current")}%, nella rilevazione {E(learning["period"])}. Il fenomeno riguarda gli apprendimenti, non gli abbandoni.</p>')
    chapter('apprendimenti','Apprendimenti e giovani','L’offerta educativa va letta anche alla luce delle opportunità dei ragazzi, mantenendo distinti servizi, apprendimenti e percorsi di vita.',
        chart('invalsi_invalsiImplicitDispersion_g8_current','Apprendimenti: valori disponibili, senza graduatorie di qualità','Dispersione implicita al termine della secondaria di primo grado (grado 8): fragilità negli apprendimenti rilevate dalle prove. Non è il tasso di abbandono scolastico.')+
        learning_text+'<h3>Perché il confronto richiede prudenza</h3><p>Il Comune è quello della scuola, non della residenza. I valori non disponibili rimangono visibili e non diventano zero. Contesto degli alunni e partecipazione alle prove sono necessari per interpretare le differenze; non si attribuiscono i risultati a una politica o alla qualità delle singole scuole.</p><h3>Oltre questi indicatori</h3><p>Transizioni verso formazione e lavoro, spazi di aggregazione e opportunità extrascolastiche richiedono evidenze ulteriori: questa lettura non esaurisce i bisogni dei giovani.</p>')
    public_boundary='La lettura descrive capacità dei servizi, organizzazione scolastica e alcuni aspetti degli apprendimenti. Per valutare l’adeguatezza ai bisogni e dimensionare posti o sedi occorrono domanda effettiva, bacini, frequenza e attese. Non identifica effetti causali o bisogni individuali.'
    gaps=''.join(f'<li>{E(gap)}</li>' for gap in q['missingData'])
    source_rows=''.join(f'<li><strong>{E(cases[cid]["facts"][0]["text"].split(" — ")[0])}</strong> · {E(observations(cid)[0]["period"])} · {source(cid)}</li>' for cid in refs if cid!='child_zero')
    chapter('decisioni','Dalle evidenze alle scelte','Un quadro per preparare approfondimenti e verificare gli interventi, senza prescrizioni automatiche.',
        '<h3>Le domande da portare al tavolo</h3><ul><li>Prima infanzia: l’ostacolo è il numero di posti, la tariffa, l’orario o la distanza?</li><li>Scuola: dove emergono richieste di tempo pieno o difficoltà di accesso per plesso?</li><li>Giovani: quali bisogni non sono osservabili attraverso le sole rilevazioni scolastiche?</li></ul><h3>Chi coinvolgere</h3><p>Comune e gestori dei servizi educativi; istituzioni scolastiche e amministrazione scolastica per l’organizzazione didattica; Regione per la programmazione di competenza. Titolarità degli edifici e competenze vanno verificate per ogni intervento.</p><h3>Opzioni da approfondire e monitoraggio</h3><p>Valutare posti, orari, sostegni alle tariffe e accessibilità richiede prima una ricognizione della domanda. Per monitorare eventuali interventi servono domande accolte e inevase, tempi di attesa, frequenza effettiva, costi per le famiglie e barriere rimosse, con una base precedente e periodi confrontabili. Sono fabbisogni informativi, non nuove serie già disponibili.</p><h3>Le informazioni ancora necessarie</h3><ul>'+gaps+'</ul><h3>Fonti e periodi della lettura</h3><ul class="edu-sources">'+source_rows+'</ul><p>Queste sono evidenze congelate nei periodi indicati, non una verifica della situazione attuale dei servizi. I confronti tra i sette Comuni sono descrittivi; non attestano equivalenza dei territori. Non si combinano percentuali con denominatori diversi.</p><details><summary>Confine della domanda e criteri di interpretazione</summary><p>'+E(public_boundary)+'</p><p>'+E(q['interpretationLimit'])+'</p></details>')
    return dict(schemaVersion=2,focusCode=focus_code,conclusions=conclusions,answerBoundaryPublic=public_boundary,editionDate=date.strftime('%d/%m/%Y'),pdfDate=date.strftime('%Y%m%d%H%M%S'),questionId=QUESTION,question=q['question'],territory=town,townRoute='/comuni/'+town.lower().replace(' ','-')+'/',period=period,repositoryCommit=commit,
        bundleSha256=hashlib.sha256((json.dumps(bundle,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()).hexdigest(),
        requiredCaseRefs=refs,overview=overview,chapters=chapters,bindings=bindings,territorialCases=territorial_cases)


def build_education(bundle, commit, territorial_cases):
    readings={code:build_reading(bundle,commit,territorial_cases,code) for code in NAMES}
    model=dict(readings[FOCUS])
    # Shared query responses are stored once; these are product views, not a catalog.
    model['townReadings']={code:{k:v for k,v in reading.items() if k!='territorialCases'} for code,reading in readings.items()}
    return model


def report_html(reading, css):
    parts=[f'<section class="edu-print-page">{report_brand(reading["territory"])}<h1>Famiglie, servizi e scuola</h1><h2>{E(reading["question"])}</h2><p>Anno scolastico {E(reading["period"])} · Rapporto, edizione del {reading["editionDate"]}</p>'+reading['overview']+'</section>']
    for c in reading['chapters']:
        parts.append(f'<section class="edu-print-page"><p class="edu-kicker">{E(reading["territory"].upper())} / OFFERTA EDUCATIVA</p><h2>{E(c["title"])}</h2>'+c['html'].replace('<details>', '<details open>')+'</section>')
    parts.append(f'<section class="edu-reproduction"><h2>Fonti e riproducibilità</h2><p>Rapporto generato dagli stessi risultati verificati utilizzati nella lettura web. L’edizione identifica la versione del rapporto; i periodi dei dati sono indicati nei grafici e nelle fonti.</p><h3>Attribuzione e riuso</h3><p>{E(REUSE_NOTE)} <a href="{LICENSE_URL}">Licenza CC BY 4.0</a> · <a href="https://{WEBSITE}/progetto/#licenza">Condizioni di riuso del progetto</a>.</p><p>Pubblicazione civica indipendente, non documento ufficiale degli enti citati. Per usi ufficiali o amministrativi consultare la fonte originaria.</p><p>Versione del codice e delle fonti conservate:</p><p><a href="https://github.com/EmAnzi3/osservatorio-versilia/tree/{reading["repositoryCommit"]}">{reading["repositoryCommit"]}</a></p><p>Impronta del pilota originale (SHA256):<br>{reading["bundleSha256"]}</p><p>Gli identificativi e i risultati originali sono consultabili nei dettagli di verifica della lettura web.</p><p><a href="https://osservatorioversilia.it/chiedi/?lettura=educazione&amp;comune={reading["focusCode"]}">osservatorioversilia.it/chiedi/?lettura=educazione&amp;comune={reading["focusCode"]}</a></p></section>')
    return '<!doctype html><html lang="it"><meta charset="utf-8"><meta name="author" content="'+PUBLISHER+'"><title>'+E(reading['territory'])+' - Famiglie, servizi e scuola</title><style>'+css+'</style><main class="edu-report">'+''.join(parts)+'</main></html>'


def write_report(reading, css, path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        try:
            page=browser.new_page();page.set_content(report_html(reading,css));page.emulate_media(media='print')
            page.pdf(path=str(path),format='A4',print_background=True,display_header_footer=True,tagged=True,outline=True,
                margin={'top':'15mm','bottom':'18mm','left':'16mm','right':'16mm'},header_template='<span></span>',
                footer_template=f'<div style="font-family:Arial;font-size:8px;color:#405968;width:100%;margin:0 16mm;border-top:1px solid #c7d8df;padding-top:5px;display:flex;justify-content:space-between"><span>{PUBLISHER} · {WEBSITE}<br>{E(reading["territory"])} / Offerta educativa</span><span>Pagina <span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
        finally:browser.close()
    # Chromium timestamps are the only wall-clock metadata; a fixed value makes
    # the report deterministic for the same verified source and editorial text.
    data=Path(path).read_bytes()
    data=re.sub(rb'/(CreationDate|ModDate) \(D:\d{14}\+00\x27?00\x27?\)',lambda m:b'/'+m[1]+b" (D:"+reading["pdfDate"].encode()+b"+00'00')",data)
    Path(path).write_bytes(data)
