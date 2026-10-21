#!/usr/bin/env python3
"""Assemble a local guided-explorer preview; never change the public dist or deploy."""
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup
from bs4.dammit import EntitySubstitution
from bs4.formatter import HTMLFormatter
from a7_query_workbench import encode
from a7_runtime_package import package_runtime, require

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT/'experiments/a7-guided-explorer'


class PreserveAttributeOrder(HTMLFormatter):
    def attributes(self, tag):
        return tag.attrs.items()


def presentation(catalog):
    """Only derived display metadata, never operation permissions or observations."""
    body = Path(catalog).read_bytes()
    data = json.loads(body)
    metrics = {}
    for key, metric in data['metrics'].items():
        labels = {}
        for row in metric.get('rows', []):
            for part in row.get('parts') or []:
                if part.get('key') and part.get('label'):
                    labels['part:'+part['key']] = part['label']
        for index, parameter in enumerate(metric.get('parameterDefinitions', [])):
            if isinstance(parameter, dict) and (parameter.get('label') or parameter.get('name')):
                labels['parameter:'+str(index)] = parameter.get('label') or parameter['name']
        metrics[key] = dict(description=metric['meta'].get('description', ''),
                            unit=metric['meta'].get('unit'), unitLabel=metric['meta'].get('unitLabel'), views=labels)
    return dict(catalogSha256=hashlib.sha256(body).hexdigest(),
                themes={k:v['label'] for k,v in data['themes'].items()}, metrics=metrics)


def build(dist, runtime, output, *, public=False):
    dist, runtime, output = (Path(p).absolute() for p in (dist, runtime, output))
    require(not output.exists() and not output.is_symlink(), 'preview_output_already_exists')
    require(dist.resolve() not in output.resolve().parents and output.resolve() not in dist.resolve().parents,
            'overlapping_preview_directories')
    require(dist.is_dir() and (dist/'chiedi/index.html').is_file(), 'public_dist_required')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.a7-preview-', dir=output.parent) as tmp:
        stage = Path(tmp)/'site'
        shutil.copytree(dist, stage)
        # Preview must never install or replace a live site's service worker.
        page = stage/'chiedi/index.html'
        soup = BeautifulSoup(page.read_text(encoding='utf-8'), 'html.parser')
        # Re-embedding a canonical site for a subset preview must replace only
        # the derived explorer, never duplicate controls or retain mixed graphs.
        for panel in soup.select('#a7-explorer'):
            panel.decompose()
        for asset in soup.select('script[src], link[href]'):
            if (asset.get('src') or asset.get('href') or '').startswith('explorer-preview/'):
                asset.decompose()
        old_graph = stage/'chiedi/explorer-preview'
        if old_graph.exists():
            shutil.rmtree(old_graph)
        for script in ([] if public else soup.find_all('script', src=True)):
            if script['src'].split('?', 1)[0].endswith('/assets/pwa.js'):
                script.decompose()
        if not public:
            soup.head.append(soup.new_tag('meta', attrs={'name':'robots', 'content':'noindex,nofollow'}))
        graph = Path(tmp)/'graph'
        descriptor = package_runtime(runtime, stage/'data/site-data.json', graph/'package')
        metadata = 'export default '+encode(presentation(stage/'data/site-data.json'))+';\n'
        (graph/'presentation.mjs').write_text(metadata, encoding='utf-8')
        for name in ['explorer.mjs', 'explorer.css']:
            shutil.copyfile(ASSETS/name, graph/name)
        entry = ("const status=document.getElementById('explorer-status');\n"
            "async function boot(){try{const [{startExplorer},{default:presentation},{openPackagedRuntime}]=await Promise.all(["
            "import('./explorer.mjs'),import('./presentation.mjs'),import('./package/"+descriptor['entrypoint']+"')]);"
            "await startExplorer(openPackagedRuntime,presentation);}catch{status.textContent='Impossibile caricare e verificare questa versione. Riprova la stessa versione.';"
            "document.getElementById('explorer-retry').hidden=false;document.getElementById('explorer-retry').onclick=()=>location.reload();}}\nboot();\n")
        (graph/'entry.mjs').write_text(entry, encoding='utf-8')
        hashes = {p.relative_to(graph).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(graph.rglob('*')) if p.is_file()}
        relative = 'explorer-preview/'+hashlib.sha256(encode(hashes).encode()).hexdigest()+'/'
        destination = stage/'chiedi'/relative
        destination.parent.mkdir(parents=True)
        os.rename(graph, destination)
        panel = BeautifulSoup((ASSETS/'panel.html').read_text(encoding='utf-8'), 'html.parser')
        if public:
            hero = soup.select_one('.a7-hero')
            hero.select_one('h1 + p').string = 'Dai dati alle domande sul territorio: scegli una misura e un confronto, oppure consulta le letture tematiche.'
            hero.select_one('.notice').string = 'Ogni risultato riporta periodo, fonte e limiti. I confronti comunali non sono un aggregato della Versilia.'
            hero.select_one('.a7-how').string = 'Esplorazione dei dati · Letture tematiche · Dossier'
            soup.select_one('#scegli').string = 'Letture tematiche e dossier'
            panel.select_one('.explorer-eyebrow').string = 'ESPLORAZIONE DEI DATI · IN SVILUPPO'
            panel.select_one('.explorer-scope').string = 'Sono consultabili letture comunali, confronti fra i sette Comuni e serie dove disponibili. Il confronto non è un totale della Versilia. Altre operazioni del motore possono non essere ancora consultabili qui.'
        panel.section['data-explorer-graph'] = relative
        soup.select_one('#a7-guided').insert(1, panel.section)
        soup.head.append(soup.new_tag('link', rel='stylesheet', href=relative+'explorer.css'))
        soup.body.append(soup.new_tag('script', type='module', src=relative+'entry.mjs'))

        receipt = dict(schemaVersion=1, kind='a7-guided-explorer-preview',
                       publicIntegration=public, releaseSha256=descriptor['releaseSha256'],
                       scope=descriptor['scope'], metrics=descriptor['metrics'], views=descriptor['views'],
                       graph=relative, files=hashes)
        body = (encode(receipt)+'\n').encode()
        (stage/'explorer-preview.json').write_bytes(body)
        soup.select_one('#a7-explorer')['data-explorer-integrity'] = hashlib.sha256(body).hexdigest()
        page.write_text(soup.decode(formatter=PreserveAttributeOrder(
            entity_substitution=EntitySubstitution.substitute_xml)), encoding='utf-8')
        # One complete local site artifact, including its page-bound trust anchor.
        os.rename(stage, output)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    receipt = build(args.dist, args.runtime, args.output_dir)
    print(json.dumps({k:v for k,v in receipt.items() if k != 'files'}, indent=2))
