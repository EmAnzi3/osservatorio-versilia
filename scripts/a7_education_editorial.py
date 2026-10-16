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


def build_reading(bundle, commit, territorial_cases):
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
    def observations(cid):return [f for f in cases[cid]['facts'] if f['kind']=='observation']
    def focus(cid):
        rows = [f for f in observations(cid) if f['geography']==FOCUS]
        if len(rows)!=1 or rows[0]['value'] is None:raise ValueError('education_focus_missing:'+cid)
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
            bars.append(f'<li class="{"edu-focus" if f["geography"]==FOCUS else ""}" data-evidence-case="{cid}" data-evidence-pointer="{f["responsePointer"]}"><span class="edu-town">{name}{components}</span>{track}<strong>{number(v,0 if unit=="alunni" else 1)}{suffix}</strong></li>')
        available=len(values)
        coverage=f'{len(rows)} Comuni della Versilia' if len(rows)==7 else 'Massarosa e Viareggio: confronto descrittivo selezionato, non un gruppo di territori equivalenti'
        return f'''<figure class="edu-chart" data-education-case="{cid}"><figcaption><h4>{title}</h4><p>{explanation}</p></figcaption><p class="edu-chart-meta">Anno scolastico {E(base['period'])} · {coverage}. Valori disponibili: {available} su {len(rows)}.</p><ul class="edu-bars">{''.join(bars)}</ul><p class="edu-chart-meta">Scala da 0 a {number(maximum,0)} {unit}. Massarosa è evidenziata; Comuni in ordine alfabetico. Fonte: {source(cid)}.</p></figure>'''
    if any(f['value'] != 0 for f in observations('child_zero')):
        raise ValueError('education_zero_narrative_needs_review')
    period=focus('school_full_time')['period']
    lead='''<div class="edu-opening"><p class="edu-kicker">CRESCERE IN VERSILIA</p><h3>Un posto al nido.<br>Tempo per imparare.<br>Spazi da vivere.</h3><p class="edu-lead">Per una famiglia, l’offerta educativa entra nell’organizzazione di ogni giornata. Partiamo da Massarosa e guardiamo tutti i sette Comuni: quanti posti possono offrire i servizi, quanto è diffuso il tempo pieno e che cosa sappiamo degli edifici.</p><p class="edu-opening-foot">Tre aspetti da leggere insieme, senza confondere posti, frequenza e accesso effettivo.</p></div>'''
    # Textual claims are guarded by actual values; no stale narrative after a data update.
    if not 50 < focus('school_full_time')['value'] <= 100:raise ValueError('education_full_time_narrative_needs_review')
    findings=f'''<div class="edu-findings"><div><span class="edu-kicker">PRIMA INFANZIA</span><strong>{value('child_weighted')}%</strong><p>Capacità potenziale rispetto ai bambini di 3–36 mesi, non frequenza effettiva.</p></div><div><span class="edu-kicker">TEMPO PIENO</span><strong>{value('school_full_time')}%</strong><p>Alunni della primaria a tempo pieno nelle scuole del Comune.</p></div><div><span class="edu-kicker">VITA SCOLASTICA</span><strong>{value('school_students',0)}</strong><p>Alunni nelle scuole del Comune: possono abitare anche altrove.</p></div></div>'''
    overview='<div class="edu-cover-grid">'+lead+'<div class="edu-focus-facts"><p class="edu-kicker">MASSAROSA, TRE PUNTI DI PARTENZA</p>'+findings+'</div></div>'+chart('school_full_time','Il tempo pieno non ha la stessa diffusione in tutta la Versilia','A Massarosa riguarda oltre metà degli alunni della primaria. Qui il confronto comprende tutti i sette Comuni: il numero di alunni accanto alla quota aiuta a leggere anche le reti più piccole.')+'''<aside class="edu-reading-note"><span class="edu-kicker">LA DOMANDA CHE CONTA</span><h3>L’offerta incontra davvero le richieste delle famiglie?</h3><p>Per capirlo servono anche domande accolte, liste d’attesa, orari e tariffe. I capitoli mettono a fuoco ciò che i numeri descrivono e le informazioni da portare al tavolo.</p></aside>'''
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
        f'<p>A Massarosa gli alunni delle scuole del Comune sono <strong>{value("school_students",0)}</strong>. Il confronto comprende tutte le sette reti scolastiche, con dimensioni diverse: i conteggi assoluti non misurano la copertura dei bisogni.</p><h3>Che cosa approfondire</h3><p>Bacini di provenienza, capienza e iscrizioni per plesso, tempi di percorso e richieste di tempo pieno non accolte. Non si ricostruisce una domanda futura da una singola fotografia.</p>')
    chapter('spazi','Spazi e accessibilità','Le caratteristiche dichiarate degli edifici sono una parte della lettura, distinta dall’esperienza quotidiana degli alunni.',
        chart('school_access_defined','Accessibilità: la percentuale riguarda le risposte definite','La quota esclude le risposte non definite. Un valore del 100% non certifica l’accessibilità di tutte le scuole o di ogni percorso casa–scuola.')+
        '<h3>Che cosa approfondire</h3><p>Completezza delle risposte, verifiche per edificio e percorsi, barriere residue e bisogni degli alunni. Il dato dichiarato non è una certificazione tecnica di sicurezza o qualità.</p>')
    chapter('apprendimenti','Apprendimenti e giovani','L’offerta educativa va letta anche alla luce delle opportunità dei ragazzi, mantenendo distinti servizi, apprendimenti e percorsi di vita.',
        chart('invalsi_invalsiImplicitDispersion_g8_current','Apprendimenti: valori disponibili, senza graduatorie di qualità','Dispersione implicita al termine della secondaria di primo grado (grado 8): fragilità negli apprendimenti rilevate dalle prove. Non è il tasso di abbandono scolastico.')+
        '<h3>Perché il confronto richiede prudenza</h3><p>Il Comune è quello della scuola, non della residenza. I valori non disponibili rimangono visibili e non diventano zero. Contesto degli alunni e partecipazione alle prove sono necessari per interpretare le differenze; non si attribuiscono i risultati a una politica o alla qualità delle singole scuole.</p><h3>Oltre questi indicatori</h3><p>Transizioni verso formazione e lavoro, spazi di aggregazione e opportunità extrascolastiche richiedono evidenze ulteriori: questa lettura non esaurisce i bisogni dei giovani.</p>')
    public_boundary='La lettura descrive capacità dei servizi, organizzazione scolastica e alcuni aspetti degli apprendimenti. Per valutare l’adeguatezza ai bisogni e dimensionare posti o sedi occorrono domanda effettiva, bacini, frequenza e attese. Non identifica effetti causali o bisogni individuali.'
    gaps=''.join(f'<li>{E(gap)}</li>' for gap in q['missingData'])
    source_rows=''.join(f'<li><strong>{E(cases[cid]["facts"][0]["text"].split(" — ")[0])}</strong> · {E(observations(cid)[0]["period"])} · {source(cid)}</li>' for cid in refs if cid!='child_zero')
    chapter('decisioni','Dalle evidenze alle scelte','Un quadro per preparare approfondimenti e verificare gli interventi, senza prescrizioni automatiche.',
        '<h3>Le domande da portare al tavolo</h3><ul><li>Prima infanzia: l’ostacolo è il numero di posti, la tariffa, l’orario o la distanza?</li><li>Scuola: dove emergono richieste di tempo pieno o difficoltà di accesso per plesso?</li><li>Giovani: quali bisogni non sono osservabili attraverso le sole rilevazioni scolastiche?</li></ul><h3>Chi coinvolgere</h3><p>Comune e gestori dei servizi educativi; istituzioni scolastiche e amministrazione scolastica per l’organizzazione didattica; Regione per la programmazione di competenza. Titolarità degli edifici e competenze vanno verificate per ogni intervento.</p><h3>Opzioni da approfondire e monitoraggio</h3><p>Valutare posti, orari, sostegni alle tariffe e accessibilità richiede prima una ricognizione della domanda. Per monitorare eventuali interventi servono domande accolte e inevase, tempi di attesa, frequenza effettiva, costi per le famiglie e barriere rimosse, con una base precedente e periodi confrontabili. Sono fabbisogni informativi, non nuove serie già disponibili.</p><h3>Le informazioni ancora necessarie</h3><ul>'+gaps+'</ul><h3>Fonti e periodi della lettura</h3><ul class="edu-sources">'+source_rows+'</ul><p>Queste sono evidenze congelate nei periodi indicati, non una verifica della situazione attuale dei servizi. I confronti tra i sette Comuni sono descrittivi; non attestano equivalenza dei territori. Non si combinano percentuali con denominatori diversi.</p><details><summary>Confine della domanda e criteri di interpretazione</summary><p>'+E(public_boundary)+'</p><p>'+E(q['interpretationLimit'])+'</p></details>')
    return dict(schemaVersion=1,answerBoundaryPublic=public_boundary,editionDate=date.strftime('%d/%m/%Y'),pdfDate=date.strftime('%Y%m%d%H%M%S'),questionId=QUESTION,question=q['question'],territory='Massarosa',period=period,repositoryCommit=commit,
        bundleSha256=hashlib.sha256((json.dumps(bundle,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()).hexdigest(),
        requiredCaseRefs=refs,overview=overview,chapters=chapters,bindings=bindings,territorialCases=territorial_cases)


def report_html(reading, css):
    parts=[f'<section class="edu-print-page"><p class="edu-kicker">OSSERVATORIO VERSILIA / MASSAROSA</p><h1>Famiglie, servizi e scuola</h1><h2>{E(reading["question"])}</h2><p>Una lettura territoriale · Anno scolastico {E(reading["period"])} · Edizione {reading["editionDate"]}</p>'+reading['overview']+'</section>']
    for c in reading['chapters']:
        parts.append(f'<section class="edu-print-page"><p class="edu-kicker">MASSAROSA / OFFERTA EDUCATIVA</p><h2>{E(c["title"])}</h2>'+c['html'].replace('<details>', '<details open>')+'</section>')
    parts.append(f'<section class="edu-reproduction"><h2>Fonti e riproducibilità</h2><p>Rapporto generato dagli stessi risultati verificati utilizzati nella lettura web. I dati non sono aggiornati in tempo reale.</p><p>Versione del codice e delle fonti conservate:</p><p><a href="https://github.com/EmAnzi3/osservatorio-versilia/tree/{reading["repositoryCommit"]}">{reading["repositoryCommit"]}</a></p><p>Impronta delle evidenze (SHA256):<br>{reading["bundleSha256"]}</p><p>Gli identificativi e i risultati originali sono disponibili nell’esportazione tecnica della lettura web.</p><p><a href="https://osservatorioversilia.it/chiedi/?lettura=educazione">osservatorioversilia.it/chiedi/?lettura=educazione</a></p></section>')
    return '<!doctype html><html lang="it"><meta charset="utf-8"><title>Massarosa - Famiglie, servizi e scuola</title><style>'+css+'</style><main class="edu-report">'+''.join(parts)+'</main></html>'


def write_report(reading, css, path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        try:
            page=browser.new_page();page.set_content(report_html(reading,css));page.emulate_media(media='print')
            page.pdf(path=str(path),format='A4',print_background=True,display_header_footer=True,tagged=True,outline=True,
                margin={'top':'15mm','bottom':'18mm','left':'16mm','right':'16mm'},header_template='<span></span>',
                footer_template='<div style="font-family:Arial;font-size:8px;color:#405968;width:100%;text-align:center">Osservatorio Versilia · Massarosa / Offerta educativa · <span class="pageNumber"></span> / <span class="totalPages"></span></div>')
        finally:browser.close()
    # Chromium timestamps are the only wall-clock metadata; a fixed value makes
    # the report deterministic for the same verified source and editorial text.
    data=Path(path).read_bytes()
    data=re.sub(rb'/(CreationDate|ModDate) \(D:\d{14}\+00\x27?00\x27?\)',lambda m:b'/'+m[1]+b" (D:"+reading["pdfDate"].encode()+b"+00'00')",data)
    Path(path).write_bytes(data)
