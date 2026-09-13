#!/usr/bin/env python3
"""Browser QA desktop/mobile per INVALSI v1.38.0."""
from __future__ import annotations

import argparse
import contextlib
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright


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


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--directory',default='dist'); ap.add_argument('--screenshots-dir',default='reports/invalsi-browser'); args=ap.parse_args()
    directory=Path(args.directory).resolve(); shots=Path(args.screenshots_dir).resolve(); shots.mkdir(parents=True,exist_ok=True)
    data=json.loads((directory/'data/site-data.json').read_text())
    assert data['version']=='v1.38.0' and len(data['metrics'])==207
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
        # Il lollipop usa Toscana come riferimento ufficiale; Italia è resa nel pannello benchmark.
        assert page.locator('.comparison-legend').get_by_text('Toscana',exact=False).count()>=1
        text=page.locator('#compare-bars').inner_text()
        assert 'Media semplice' not in text and 'media Versilia' not in text
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

        # Storico: per il profilo selezionato devono comparire i benchmark ufficiali, senza interpolare n.d.
        history_button=page.locator('#compare-bars [data-view-mode="history"]')
        if history_button.count():
            history_button.click(); page.wait_for_timeout(500)
            hist=page.locator('#compare-bars [data-view-pane="history"]')
            assert hist.count()==1
            htext=hist.inner_text()
            assert 'Toscana' in htext and 'Italia' in htext
            assert 'Versilia' not in htext
            page.screenshot(path=str(shots/'invalsi-risultati-storico-desktop.png'),full_page=True)
            report['checks'].append({'resultsHistory':'pass'})

        # Livelli/traguardi: stack INVALSI/QCER e benchmark nello stesso componente.
        page.goto(f'{base}/confronta/istruzione/?indicatore=invalsiCompetence',wait_until='networkidle'); wait_app(page)
        comp=page.locator('#compare-bars select[data-composite-component]')
        assert comp.count()==1 and comp.input_value()=='g5-inglese-reading'
        detail=page.locator('.invalsi-levels-detail')
        assert detail.count()==1 and detail.locator('.composite-stack').count()>=1
        dtext=detail.inner_text(); assert 'Toscana' in dtext and 'Italia' in dtext
        page.screenshot(path=str(shots/'invalsi-livelli-desktop.png'),full_page=True)
        report['checks'].append({'competenceLevels':'pass'})

        # Dispersione/eccellenza disponibili come indicatori distinti.
        for key,label in [('invalsiImplicitDispersion','Dispersione scolastica implicita'),('invalsiAcademicExcellence','Eccellenza accademica')]:
            page.goto(f'{base}/confronta/istruzione/?indicatore={key}',wait_until='networkidle'); wait_app(page)
            assert page.get_by_text(label,exact=True).count()>=1
            assert page.locator('#compare-bars select[data-composite-component]').count()==1
            assert 'Italia' in page.locator('#compare-bars').inner_text()
        report['checks'].append({'dispersionExcellence':'pass'})

        # Scheda comunale: non deve mai comparire una posizione rispetto alla Versilia.
        page.goto(f'{base}/comuni/massarosa/?tema=istruzione&indicatore=invalsiResults',wait_until='networkidle'); wait_app(page)
        page.get_by_role('heading',name='Massarosa',exact=True).wait_for(timeout=10_000)
        pos=page.locator('#town-topic .versilia-position')
        assert pos.count()==1
        ptext=pos.inner_text()
        assert 'Toscana' in ptext and 'Italia' in ptext
        assert 'media Versilia' not in ptext and 'Scostamento dalla Toscana' in ptext
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
