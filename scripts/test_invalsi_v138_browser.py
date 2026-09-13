#!/usr/bin/env python3
"""Browser regression desktop/mobile per le superfici INVALSI introdotte in v1.38.0.

Il gate sorgenti resta rigorosamente ancorato alla v1.38; questo test browser
verifica invece che quelle superfici continuino a funzionare nella release
pubblica corrente, anche dopo l'aggiunta di indicatori successivi.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright


REQUIRED_METRICS = {
    "invalsiResults",
    "invalsiCompetence",
    "invalsiImplicitDispersion",
    "invalsiAcademicExcellence",
}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


@contextlib.contextmanager
def serve(directory: Path):
    handler=lambda *args,**kwargs: QuietHandler(*args,directory=str(directory),**kwargs)
    httpd=ThreadingHTTPServer(('127.0.0.1',0),handler); thread=threading.Thread(target=httpd.serve_forever,daemon=True); thread.start()
    try: yield f'http://127.0.0.1:{httpd.server_port}'
    finally: httpd.shutdown(); thread.join(timeout=5)


def wait_app(page):
    page.wait_for_selector('#app main',timeout=20_000); page.wait_for_timeout(700)


def release_tuple(value: str) -> tuple[int, int, int]:
    parts = str(value).strip().removeprefix('v').split('.')
    if len(parts) < 3:
        raise AssertionError(f'Release non valida: {value}')
    return tuple(int(part) for part in parts[:3])


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--directory',default='dist'); ap.add_argument('--screenshots-dir',default='reports/invalsi-browser'); args=ap.parse_args()
    directory=Path(args.directory).resolve(); shots=Path(args.screenshots_dir).resolve(); shots.mkdir(parents=True,exist_ok=True)
    data=json.loads((directory/'data/site-data.json').read_text())
    assert release_tuple(data['version']) >= (1, 38, 0), data['version']
    assert len(data['metrics']) >= 207, len(data['metrics'])
    assert REQUIRED_METRICS <= set(data['metrics']), REQUIRED_METRICS - set(data['metrics'])
    report={'checks':[],'consoleErrors':[],'pageErrors':[]}

    with serve(directory) as base, sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
        page.on('console',lambda msg: report['consoleErrors'].append(msg.text) if msg.type=='error' else None)
        page.on('pageerror',lambda exc: report['pageErrors'].append(str(exc)))

        page.goto(f'{base}/confronta/istruzione/?indicatore=invalsiResults',wait_until='networkidle'); wait_app(page)
        page.get_by_role('heading',name='Istruzione').wait_for(timeout=10_000)
        selector=page.locator('#compare-bars select[data-composite-component]')
        assert selector.count()==1 and selector.input_value()=='g5-italiano'
        assert page.locator('.comparison-bars .bar-row').count()>=7
        assert page.locator('.comparison-legend').get_by_text('Toscana',exact=False).count()>=1
        text=page.locator('#compare-bars').inner_text()
        assert 'Media semplice' not in text and 'Versilia ·' not in text
        assert 'nessuna media Versilia' in text
        assert 'Benchmark ufficiali' in text and 'Toscana' in text and 'Italia' in text
        default_values=page.locator('.comparison-bars .bar-row strong').all_text_contents()
        selector.select_option('g8-italiano'); page.wait_for_timeout(700)
        assert selector.input_value()=='g8-italiano'
        changed=page.locator('.comparison-bars .bar-row strong').all_text_contents()
        assert changed!=default_values
        assert page.locator('.comparison-bars .comparison-missing').count()>=3, 'Gli n.d. strutturali non sono visibili'
        updated_text=page.locator('#compare-bars').inner_text()
        assert 'Toscana' in updated_text and 'Italia' in updated_text
        page.screenshot(path=str(shots/'invalsi-risultati-desktop.png'),full_page=True)
        report['checks'].append({'resultsCurrent':'pass','tuscanyReference':'pass','italyBenchmarkPanel':'pass','structuralMissing':'pass'})

        history_button=page.locator('#compare-bars [data-view-mode="history"]')
        if history_button.count():
            history_button.click(); page.wait_for_timeout(500)
            hist=page.locator('#compare-bars [data-view-pane="history"]')
            assert hist.count()==1
            htext=hist.inner_text()
            assert 'Toscana' in htext and 'Italia' in htext
            assert 'Versilia' not in htext
            tuscany_line=hist.locator('.ux-series-group[data-history-town="toscana"] .ux-series-line')
            italy_line=hist.locator('.ux-series-group[data-history-town="italia"] .ux-series-line')
            assert tuscany_line.count()==1 and italy_line.count()==1
            tuscany_dash=tuscany_line.evaluate("el => getComputedStyle(el).strokeDasharray")
            italy_dash=italy_line.evaluate("el => getComputedStyle(el).strokeDasharray")
            assert tuscany_dash and italy_dash and tuscany_dash!='none' and italy_dash!='none' and tuscany_dash!=italy_dash, (tuscany_dash,italy_dash)
            assert hist.locator('.ux-history-legend button[data-history-select="toscana"]').count()==1
            assert hist.locator('.ux-history-legend button[data-history-select="italia"]').count()==1
            page.screenshot(path=str(shots/'invalsi-risultati-storico-desktop.png'),full_page=True)
            report['checks'].append({'resultsHistory':'pass','benchmarkDashStyles':'pass'})

        page.goto(f'{base}/confronta/istruzione/?indicatore=invalsiCompetence',wait_until='networkidle'); wait_app(page)
        comp=page.locator('#compare-bars select[data-composite-component]')
        assert comp.count()==1 and comp.input_value()=='g5-inglese-reading'
        detail=page.locator('.invalsi-levels-detail')
        assert detail.count()==1 and detail.locator('.composite-stack').count()>=1
        dtext=detail.inner_text(); assert 'Toscana' in dtext and 'Italia' in dtext
        page.screenshot(path=str(shots/'invalsi-livelli-desktop.png'),full_page=True)
        report['checks'].append({'competenceLevels':'pass'})

        for key,label in [('invalsiImplicitDispersion','Dispersione scolastica implicita'),('invalsiAcademicExcellence','Eccellenza accademica')]:
            page.goto(f'{base}/confronta/istruzione/?indicatore={key}',wait_until='networkidle'); wait_app(page)
            assert page.get_by_text(label,exact=True).count()>=1
            assert page.locator('#compare-bars select[data-composite-component]').count()==1
            assert 'Italia' in page.locator('#compare-bars').inner_text()
        report['checks'].append({'dispersionExcellence':'pass'})

        page.goto(f'{base}/comuni/massarosa/?tema=istruzione&indicatore=invalsiResults',wait_until='networkidle'); wait_app(page)
        page.get_by_role('heading',name='Massarosa',exact=True).wait_for(timeout=10_000)
        pos=page.locator('#town-topic .versilia-position')
        assert pos.count()==1
        ptext=pos.inner_text()
        overline=(pos.locator('.overline').text_content() or '').strip()
        assert 'Toscana' in ptext and 'Italia' in ptext
        assert 'media versilia' not in ptext.lower() and overline=='Scostamento dalla Toscana'
        page.screenshot(path=str(shots/'invalsi-massarosa-desktop.png'),full_page=True)
        report['checks'].append({'townBenchmarks':'pass'})

        mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
        mobile.on('console',lambda msg: report['consoleErrors'].append(f'mobile: {msg.text}') if msg.type=='error' else None)
        mobile.on('pageerror',lambda exc: report['pageErrors'].append(f'mobile: {exc}'))
        mobile.goto(f'{base}/confronta/istruzione/?indicatore=invalsiResults',wait_until='networkidle'); wait_app(mobile)
        overflow=mobile.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
        assert overflow<=1, f'Overflow orizzontale mobile: {overflow}px'
        msel=mobile.locator('#compare-bars select[data-composite-component]'); assert msel.count()==1
        msel.select_option('g13-inglese-listening'); mobile.wait_for_timeout(500)
        mtext=mobile.locator('#compare-bars').inner_text()
        assert 'Toscana' in mtext and 'Italia' in mtext
        assert mobile.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')<=1
        mobile.screenshot(path=str(shots/'invalsi-risultati-mobile.png'),full_page=True)
        report['checks'].append({'mobileContainment':'pass'})
        browser.close()

    assert not report['pageErrors'], report['pageErrors']
    assert not report['consoleErrors'], report['consoleErrors']
    out=shots.parent/'invalsi-browser-report.json'; out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('INVALSI browser QA OK:',out)
    return 0


if __name__=='__main__': raise SystemExit(main())
