"""Verify the page-bound explorer graph locally or a bounded live sample."""
import gzip
import io
import re
import hashlib
import json
from html.parser import HTMLParser

ROOT_LIMIT = 2*1024*1024
PACKED_LIMIT = 8*1024*1024
RAW_LIMIT = 16*1024*1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def encode(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


def decode(body):
    def pairs(items):
        result = {}
        for key,value in items:
            require(key not in result, 'duplicate_explorer_json_key')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('nonfinite_explorer_json')
    return json.loads(body.decode('utf-8'),object_pairs_hook=pairs,parse_constant=invalid)


def schema(value):
    require(isinstance(value,dict) and type(value.get('schemaVersion')) is int
            and value['schemaVersion'] == 1, 'incompatible_explorer_schema')


class Embedding(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.panel=None; self.scripts=[]; self.feed(text)

    def handle_starttag(self, tag, attrs):
        values=dict(attrs)
        if values.get('id') == 'a7-explorer':
            require(self.panel is None and len(values)==len(attrs), 'duplicate_explorer_panel')
            self.panel=values
        if tag == 'script' and 'src' in values:
            self.scripts.append(values['src'])


def validate_explorer(read, *, full=False):
    page = Embedding(read('chiedi/index.html').decode('utf-8'))
    panel = page.panel
    require(panel is not None, 'explorer_panel_missing')
    graph = panel.get('data-explorer-graph', '')
    require(re.fullmatch(r'explorer-preview/[a-f0-9]{64}/', graph), 'invalid_explorer_graph')
    body = read('explorer-preview.json')
    require(len(body) <= 8*1024*1024 and digest(body) == panel.get('data-explorer-integrity'), 'explorer_integrity_mismatch')
    receipt = decode(body);schema(receipt)
    require(receipt.get('publicIntegration') is True and receipt.get('graph') == graph, 'explorer_embedding_mismatch')
    files = receipt['files']
    require(isinstance(files, dict) and files and len(files) <= 20000, 'invalid_explorer_inventory')
    for path, sha in files.items():
        require(isinstance(path, str) and not path.startswith('/') and all(p not in ('', '.', '..') for p in path.split('/'))
                and re.fullmatch(r'[a-zA-Z0-9._/-]+', path) and isinstance(sha, str)
                and re.fullmatch(r'[a-f0-9]{64}', sha), 'unsafe_explorer_reference')
    require(digest(encode(files).encode()) == graph.split('/')[1], 'explorer_graph_mismatch')
    prefix = 'chiedi/'+graph
    def checked(path, limit=RAW_LIMIT):
        require(path in files, 'unlisted_explorer_asset')
        data = read(prefix+path)
        require(len(data) <= limit and digest(data) == files[path], 'explorer_asset_integrity:'+path)
        return data
    require(graph+'entry.mjs' in page.scripts, 'explorer_entry_mismatch')
    # All UI/anchor/package modules; payloads remain selectively sampled live.
    for path in files:
        if not path.startswith('package/runtime/'):
            checked(path)
    manifest = 'package/runtime/'+receipt['releaseSha256']+'/release.json'
    require(files.get(manifest) == receipt['releaseSha256'], 'explorer_manifest_anchor_mismatch')
    root = decode(checked(manifest, ROOT_LIMIT));schema(root)
    require(root.get('kind') == 'a7-selective-query-runtime' and root.get('scope') == 'all_metrics', 'incomplete_public_explorer')
    require(len(root.get('metrics', [])) == receipt.get('metrics'), 'public_explorer_metric_count_mismatch')
    def artifact(ref):
        require(re.fullmatch(r'[a-f0-9]{64}\.json\.gz', ref['path']), 'invalid_explorer_block')
        path = manifest.rsplit('/',1)[0]+'/'+ref['path']
        packed = checked(path, PACKED_LIMIT)
        require(len(packed) == ref['bytes'] and digest(packed) == ref['sha256'], 'explorer_packed_integrity')
        with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream:
            raw = stream.read(RAW_LIMIT+1)
        require(len(raw) <= RAW_LIMIT and len(raw) == ref['rawBytes'] and digest(raw) == ref['rawSha256'], 'explorer_raw_integrity')
        return decode(raw)
    # Deterministic representative detail and response block. No numerical claim.
    require(root.get('metrics'), 'empty_explorer_runtime')
    detail = artifact(root['metrics'][0]['detail'])
    shard = next((r for v in detail['views'] for r in v['shards'].values()), None)
    require(shard is not None, 'explorer_response_missing')
    artifact(shard)
    if full:
        for path in files:
            checked(path)
    return dict(status='PASS', graph=graph, releaseSha256=receipt['releaseSha256'],
                coverage='all_file_hashes' if full else 'all_ui_modules_manifest_one_detail_one_response')
