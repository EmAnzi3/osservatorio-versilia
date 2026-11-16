#!/usr/bin/env python3
"""Chiedi — interprete statico delle domande sul sito costruito.

Esegue con Node l'interprete e l'indice effettivamente pubblicati in dist (non una
copia di sviluppo) sulle domande di prova di `ci/chiedi-domande.json`, con attese
scritte a mano, comprese le domande di seguito di una conversazione (`after`).
Verifica che ogni domanda proposta dal suggeritore sia capita come promesso e che
le pagine «Fonte» dell'Osservatorio esistano. Poi controlla nel browser, a 1440 e
390 px: suggeritore, risposta e dati dell'esploratore, domanda di seguito, link
alla fonte, margini interni dei box e assenza di scorrimento orizzontale.
"""
import argparse
import functools
import http.server
import json
import subprocess
import threading
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT/'ci/chiedi-domande.json'

RUNNER = r"""
import {prepare,interpret,suggest} from %(ask)s;
import index from %(index)s;
const {cases,inputs}=JSON.parse(process.argv[1]);
const p=prepare(index);
const view=r=>({kind:r.kind,metric:r.metric?.key??null,association:r.association?.id??null,operation:r.selection?.domanda??null,town:r.selection?.comune??null,detail:r.selection?.dettaglio??null,benchmark:r.selection?.riferimento??null,size:r.size??null});
// Conversazione: ogni domanda precedente aggiorna l'ultima lettura riuscita.
const answers=cases.map(c=>{let prev=null;for(const q of [].concat(c.after||[])){const r=interpret(q,p,{previous:prev});if(r.kind==='reading')prev=r;}return view(interpret(c.question,p,{previous:prev}));});
const suggestions=inputs.map(i=>suggest(i,p).map(s=>({text:s.text,kind:s.kind,reading:s.reading,association:s.association??null,got:s.kind==='question'?view(interpret(s.text,p)):null})));
const pages=index.metrics.filter(m=>m.page).map(m=>m.page);
console.log(JSON.stringify({answers,suggestions,pages,metrics:index.metrics.length}));
"""
# Inizi di domanda come li scrive una persona: il suggeritore deve proporre qualcosa.
SUGGEST_INPUTS = ['redd', 'reddito a viar', 'quanti abit', 'disocc', 'turis', 'benz', 'case a forte', 'relazione tra reddito', 'rifiuti a massarosa', 'scuol']


def graph_dir(dist):
    receipt = json.loads((dist/'explorer-preview.json').read_text(encoding='utf-8'))
    graph = dist/'chiedi'/receipt['graph']
    assert (graph/'ask.mjs').is_file() and (graph/'ask-index.mjs').is_file(), 'chiedi_interpreter_not_published'
    return graph


def check_units(graph):
    """I conteggi pubblicati hanno il nome di ciò che contano: mai la parola generica «unità»."""
    text = (graph/'presentation.mjs').read_text(encoding='utf-8')
    metrics = json.loads(text[text.index('{'):text.rindex('}')+1])['metrics']
    missing = [k for k, m in metrics.items() if m.get('unit') in ('number', 'count') and m.get('unitLabel') is None]
    assert not missing, f'chiedi_count_without_noun:{missing}'
    assert metrics['population']['unitLabel'] == 'abitanti', metrics['population']


def check_interpreter(graph, dist):
    cases = json.loads(QUESTIONS.read_text(encoding='utf-8'))['questions']
    script = RUNNER % {'ask': json.dumps((graph/'ask.mjs').as_uri()), 'index': json.dumps((graph/'ask-index.mjs').as_uri())}
    payload = json.dumps({'cases': [{'question': c['question'], 'after': c.get('after')} for c in cases], 'inputs': SUGGEST_INPUTS})
    out = json.loads(subprocess.run(['node', '--input-type=module', '-e', script, payload],
                                    check=True, capture_output=True, text=True, timeout=180).stdout)
    failures = []
    for case, got in zip(cases, out['answers']):
        for field in ('kind', 'metric', 'association', 'operation', 'town', 'detail', 'benchmark', 'size'):
            if field in case and case[field] != got[field]:
                failures.append(f"{' → '.join([*([] if not case.get('after') else case['after']), case['question']])}: {field} atteso {case[field]!r}, ottenuto {got[field]!r}")
    assert not failures, 'Interprete Chiedi:\n' + '\n'.join(failures)
    assert sum(1 for c in cases if c.get('after')) >= 15, 'chiedi_follow_up_cases_missing'
    # Suggeritore: proposte non vuote, e ogni domanda proposta viene capita come annunciato.
    for text, items in zip(SUGGEST_INPUTS, out['suggestions']):
        assert items, f'chiedi_no_suggestion:{text}'
        for item in items:
            got = item['got']
            if item['kind'] != 'question':
                assert item['kind'] == 'complete' and item['text'].endswith('a …'), item
            elif item['association']:
                assert got['kind'] == 'association' and got['association'] == item['association'], item
            else:
                assert got['kind'] == 'reading' and got['operation'] == item['reading'], item
    assert any('Viareggio' in i['text'] for i in out['suggestions'][1]), 'chiedi_suggest_town_prefix'
    # «Fonte» porta alla pagina dell'indicatore dell'Osservatorio, che deve esistere.
    # Tutti: pagina indicatore, rotta dedicata (affluenza, atlante) o Meteo e clima.
    assert len(out['pages']) == out['metrics'], 'chiedi_source_pages_missing'
    for page in out['pages']:
        path = page.split('#')[0].split('?')[0]
        assert path.startswith(('../indicatori/', '../confronta/')) and (dist/'chiedi'/path/'index.html').resolve().is_file(), page
    for page in ('../confronta/comunita/affluenza/', '../confronta/economia/atlante-attivita-economiche/',
                 '../confronta/meteo-clima/?indicatore=temperature#temperature-min-max'):
        assert page in out['pages'], f'chiedi_dedicated_page_missing:{page}'
    return len(cases)


# Testi (titoli, paragrafi, etichette) a meno di 8 px dal bordo del box con sfondo o bordo che li contiene.
TIGHT_TEXT = """()=>{const out=[];const skip=['INPUT','SELECT','BUTTON','OPTION','TD','TH','TR','TABLE','TBODY','THEAD','A','SPAN','LI','SUMMARY'];
const framed=e=>{const cs=getComputedStyle(e);return cs.backgroundColor!=='rgba(0, 0, 0, 0)'||parseFloat(cs.borderLeftWidth)>0;};
for(const box of document.querySelectorAll('#a7-explorer *')){if(!box.offsetParent||skip.includes(box.tagName)||!framed(box)||box.getBoundingClientRect().width<120)continue;const r=box.getBoundingClientRect();
for(const t of box.querySelectorAll('h2,h3,h4,p,legend,label,figcaption')){if(!t.offsetParent||!t.textContent.trim())continue;let a=t.parentElement,inner=false;while(a&&a!==box){if(framed(a)){inner=true;break;}a=a.parentElement;}if(inner)continue;
const range=document.createRange();range.selectNodeContents(t);const tr=range.getBoundingClientRect();if(!tr.width)continue;if(Math.min(tr.left-r.left,r.right-tr.right)<8)out.push((box.id||box.className)+': '+t.textContent.trim().slice(0,40));}}return out;}"""


def check_browser(dist):
    text = (graph_dir(dist)/'presentation.mjs').read_text(encoding='utf-8')
    described = json.loads(text[text.index('{'):text.rindex('}')+1])['metrics']
    from playwright.sync_api import sync_playwright

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(dist)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for width in (1440, 390):
                page = browser.new_page(viewport=dict(width=width, height=900))
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(f'http://127.0.0.1:{server.server_port}/chiedi/')
                page.wait_for_selector('#ask-input')
                page.wait_for_selector('#explorer-theme option:nth-child(2)', state='attached')
                # Suggeritore: proposte mentre si scrive, scelta da tastiera.
                page.click('#ask-input')
                page.keyboard.type('quanti abitanti ha viar', delay=20)
                page.wait_for_selector('#ask-suggest:not([hidden]) [role=option]')
                assert page.get_attribute('#ask-input', 'aria-expanded') == 'true'
                first = page.locator('#ask-suggest [role=option] .ask-suggestion-text').first.text_content()
                assert first == 'Popolazione residente a Viareggio', first
                page.keyboard.press('ArrowDown')
                assert page.get_attribute('#ask-input', 'aria-activedescendant') == 'ask-suggest-0'
                page.keyboard.press('Enter')
                page.wait_for_selector('#ask-log .ask-source a', state='attached')
                reply = page.locator('#ask-log .ask-reply').first.text_content()
                assert reply.startswith('Viareggio: '), 'chiedi_reply_missing'
                assert page.locator('#explorer-result').is_visible(), 'chiedi_result_not_shown'
                evidence = json.loads(page.locator('[data-explorer-evidence]').text_content())
                request = evidence['plan']['steps'][0]['request']
                assert request['operation'] == 'observe' and request['selectors'][0]['metric'] == 'population'
                # La frase riporta il valore esatto del motore, arrotondato solo per la lettura.
                value = evidence['steps'][0]['response']['observations'][0]['value']
                assert f'{round(value):,}'.replace(',', '.') in reply, 'chiedi_reply_not_from_engine'
                # I residenti si contano in abitanti, non nell'unità generica del conteggio.
                assert f"{round(value):,} abitanti".replace(',', '.') in reply and 'unità' not in reply, f'chiedi_reply_unit:{reply}'
                cells = page.locator('#explorer-result [data-observation-value]').all_text_contents()
                assert cells and all('abitanti' in c and 'unità' not in c for c in cells), f'chiedi_table_unit:{cells[:3]}'
                source = page.locator('#ask-log .ask-source a').first.get_attribute('href')
                assert source.startswith('../indicatori/') and (dist/'chiedi'/source/'index.html').resolve().is_file(), source
                table_source = page.locator('#explorer-result td a').first.get_attribute('href')
                assert table_source == source, table_source
                # Domanda di seguito: stesso indicatore, altro Comune.
                page.fill('#ask-input', 'e Camaiore?')
                page.click('#ask-send')
                page.wait_for_selector('#ask-log .ask-turn:first-child .ask-source a', state='attached')
                follow = page.locator('#ask-log .ask-turn').first
                assert follow.locator('.ask-reply').text_content().startswith('Camaiore: '), 'chiedi_follow_up_failed'
                assert 'Continuo dalla domanda precedente' in follow.text_content()
                assert 'Camaiore' in page.locator('#ask-context').text_content()
                # Due Comuni nominati: la frase li mette in primo piano, nell'ordine dei valori del motore.
                page.fill('#ask-input', 'Viareggio o Camaiore: chi ha più abitanti?')
                page.press('#ask-input', 'Enter')  # invio da tastiera: il suggeritore aperto copre il pulsante
                page.wait_for_selector('#ask-log .ask-turn:first-child .ask-reply', state='attached')
                pair_reply = page.locator('#ask-log .ask-turn').first.locator('.ask-reply').text_content()
                assert pair_reply.startswith('Viareggio ') and ', Camaiore ' in pair_reply and 'Valore più alto: Viareggio.' in pair_reply, f'chiedi_two_towns:{pair_reply}'
                assert 'in evidenza Viareggio e Camaiore' in page.locator('#ask-log .ask-turn').first.text_content()
                # Due Comuni senza indicatore: si chiede su che cosa confrontarli.
                page.focus('.ask-reset'); page.keyboard.press('Enter')  # da tastiera: l'intestazione fissa può coprirlo dopo lo scorrimento
                page.fill('#ask-input', 'Viareggio contro Camaiore')
                page.press('#ask-input', 'Enter')  # invio da tastiera: il suggeritore aperto copre il pulsante
                turn = page.locator('#ask-log .ask-turn').first
                assert 'Su quale indicatore vuoi confrontare Viareggio e Camaiore?' in turn.text_content(), turn.text_content()
                turn.locator('.ask-options button').first.focus(); page.keyboard.press('Enter')
                page.wait_for_selector('#ask-log .ask-turn:first-child .ask-reply', state='attached')
                chip_reply = page.locator('#ask-log .ask-turn').first.locator('.ask-reply').text_content()
                assert 'Viareggio' in chip_reply and 'Camaiore' in chip_reply and 'Sotto, tutti e sette i Comuni.' in chip_reply, f'chiedi_pair_chip:{chip_reply}'
                # «Il comune più grande»: per abitanti, con «Per superficie» a un clic.
                page.fill('#ask-input', 'Qual è il comune più grande?')
                page.press('#ask-input', 'Enter')
                turn = page.locator('#ask-log .ask-turn').first
                assert 'Ho inteso «grande» come numero di abitanti.' in turn.text_content(), turn.text_content()
                turn.locator('.ask-options button', has_text='Per superficie').focus(); page.keyboard.press('Enter')
                page.wait_for_function("() => /superficie/i.test(document.querySelector('#ask-log .ask-turn').textContent) && !/Ho inteso/.test(document.querySelector('#ask-log .ask-turn').textContent)")
                # Definizione: la descrizione del catalogo, la fonte e il passaggio al dato.
                page.fill('#ask-input', "Cos'è l'indice di vecchiaia?")
                page.press('#ask-input', 'Enter')
                turn = page.locator('#ask-log .ask-turn').first
                assert turn.locator('.ask-reply').text_content() == described['oldAgeIndex']['description'].strip(), turn.text_content()
                assert 'Fonte: ' in turn.text_content() and turn.locator('.ask-source a').count() == 1, turn.text_content()
                turn.locator('.ask-options button', has_text='Vedi i sette Comuni').focus(); page.keyboard.press('Enter')
                page.wait_for_selector('#ask-log .ask-turn:first-child .ask-reply', state='attached')
                assert 'Indice di vecchiaia' in page.locator('#ask-log .ask-turn').first.text_content(), 'chiedi_definition_to_data'
                # Testi dentro i box: mai attaccati al bordo (almeno 8 px).
                tight = page.evaluate(TIGHT_TEXT)
                assert not tight, f'chiedi_text_touches_box_edge:{tight}'
                page.click('#association-mode-pair')
                tight = page.evaluate(TIGHT_TEXT)
                assert not tight, f'chiedi_text_touches_box_edge:{tight}'
                page.click('#association-mode-measure')
                page.fill('#ask-input', 'Chi vincerà le elezioni?')
                page.click('#ask-send')
                assert 'Non ho trovato' in page.locator('#ask-log li').first.text_content(), 'chiedi_out_of_scope_answered'
                # Domanda senza risposta: email già compilata con il solo testo della domanda, nessun altro dato.
                href = page.locator('#ask-log li').first.locator('.ask-report a').get_attribute('href')
                mail = urllib.parse.urlsplit(href)
                fields = urllib.parse.parse_qs(mail.query)
                assert mail.scheme == 'mailto' and mail.path == 'info@osservatorioversilia.it', href
                assert fields['subject'] == ['Chiedi: domanda senza risposta'] and '«Chi vincerà le elezioni?»' in fields['body'][0], fields
                assert 'http' not in fields['body'][0] and set(fields) == {'subject', 'body'}, fields
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'chiedi_horizontal_scroll'
                assert not errors, errors
                page.close()
            browser.close()
    finally:
        server.shutdown()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist', type=Path, required=True)
    args = parser.parse_args()
    dist = args.dist.resolve()
    check_units(graph_dir(dist))
    count = check_interpreter(graph_dir(dist), dist)
    check_browser(dist)
    print(f'Chiedi domande PASS: {count} domande di prova (con seguiti), suggeritore, fonti dell’Osservatorio per tutti gli indicatori, risposta e dati nel browser a 1440 e 390 px')


if __name__ == '__main__':
    main()
