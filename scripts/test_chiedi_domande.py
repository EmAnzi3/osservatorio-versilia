#!/usr/bin/env python3
"""Chiedi — interprete statico delle domande sul sito costruito.

Esegue con Node l'interprete e l'indice effettivamente pubblicati in dist (non una
copia di sviluppo) sulle domande di prova di `ci/chiedi-domande.json`, con attese
scritte a mano. Poi verifica nel browser che una domanda produca la risposta e i
dati verificati dell'esploratore, a 1440 e 390 px, senza scorrimento orizzontale.
"""
import argparse
import functools
import http.server
import json
import subprocess
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT/'ci/chiedi-domande.json'

RUNNER = r"""
import {prepare,interpret} from %(ask)s;
import index from %(index)s;
const questions=JSON.parse(process.argv[1]);
const p=prepare(index);
console.log(JSON.stringify(questions.map(q=>{const r=interpret(q,p);return {kind:r.kind,metric:r.metric?.key??null,association:r.association?.id??null,operation:r.selection?.domanda??null,town:r.selection?.comune??null,detail:r.selection?.dettaglio??null,benchmark:r.selection?.riferimento??null};})));
"""


def graph_dir(dist):
    receipt = json.loads((dist/'explorer-preview.json').read_text(encoding='utf-8'))
    graph = dist/'chiedi'/receipt['graph']
    assert (graph/'ask.mjs').is_file() and (graph/'ask-index.mjs').is_file(), 'chiedi_interpreter_not_published'
    return graph


def check_interpreter(graph):
    cases = json.loads(QUESTIONS.read_text(encoding='utf-8'))['questions']
    script = RUNNER % {'ask': json.dumps((graph/'ask.mjs').as_uri()), 'index': json.dumps((graph/'ask-index.mjs').as_uri())}
    out = subprocess.run(['node', '--input-type=module', '-e', script, json.dumps([c['question'] for c in cases])],
                         check=True, capture_output=True, text=True, timeout=120).stdout
    failures = []
    for case, got in zip(cases, json.loads(out)):
        for field in ('kind', 'metric', 'association', 'operation', 'town', 'detail', 'benchmark'):
            if field in case and case[field] != got[field]:
                failures.append(f"{case['question']}: {field} atteso {case[field]!r}, ottenuto {got[field]!r}")
    assert not failures, 'Interprete Chiedi:\n' + '\n'.join(failures)
    return len(cases)


def check_browser(dist):
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
                page.fill('#ask-input', 'Quanti abitanti ha Viareggio?')
                page.click('#ask-send')
                page.wait_for_selector('#ask-log .ask-reply')
                reply = page.locator('#ask-log .ask-reply').first.text_content()
                assert reply.startswith('Viareggio: '), 'chiedi_reply_missing'
                assert page.locator('#explorer-result').is_visible(), 'chiedi_result_not_shown'
                evidence = json.loads(page.locator('[data-explorer-evidence]').text_content())
                request = evidence['plan']['steps'][0]['request']
                assert request['operation'] == 'observe' and request['selectors'][0]['metric'] == 'population'
                # La frase riporta il valore esatto del motore, arrotondato solo per la lettura.
                value = evidence['steps'][0]['response']['observations'][0]['value']
                assert f'{round(value):,}'.replace(',', '.') in reply, 'chiedi_reply_not_from_engine'
                page.fill('#ask-input', 'Chi vincerà le elezioni?')
                page.click('#ask-send')
                assert 'Non ho trovato' in page.locator('#ask-log li').first.text_content(), 'chiedi_out_of_scope_answered'
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
    count = check_interpreter(graph_dir(dist))
    check_browser(dist)
    print(f'Chiedi domande PASS: {count} domande di prova, risposta e dati nel browser a 1440 e 390 px')


if __name__ == '__main__':
    main()
