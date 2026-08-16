#!/usr/bin/env python3
"""Discover official Istat SDMX dataflows relevant to provincial consumer prices."""
from __future__ import annotations

import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

URLS = [
    'https://esploradati.istat.it/SDMXWS/rest/dataflow/IT1/all/latest?references=none',
    'https://esploradati.istat.it/SDMXWS/rest/dataflow/all/all/latest?references=none',
]
OUT = Path('/tmp/istat-price-flows.json')


def local(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def main() -> None:
    errors = []
    payload = None
    source = None
    for url in URLS:
        try:
            request = urllib.request.Request(url, headers={
                'User-Agent': 'OsservatorioVersilia-data-audit/1.0',
                'Accept': 'application/vnd.sdmx.structure+xml;version=2.1',
            })
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = response.read()
            source = url
            break
        except Exception as exc:
            errors.append(f'{url}: {type(exc).__name__}: {exc}')
    if payload is None:
        raise RuntimeError('; '.join(errors))

    root = ET.fromstring(payload)
    found = []
    for node in root.iter():
        if local(node.tag) != 'Dataflow':
            continue
        names = [
            (child.text or '').strip()
            for child in node
            if local(child.tag) == 'Name' and (child.text or '').strip()
        ]
        text = ' | '.join(names)
        low = text.lower()
        if any(token in low for token in ('prezzi al consumo', 'consumer price', 'nic', 'foi')):
            found.append({
                'id': node.attrib.get('id'),
                'agencyID': node.attrib.get('agencyID'),
                'version': node.attrib.get('version'),
                'names': names,
            })
    result = {'source': source, 'errors': errors, 'matches': found}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not found:
        raise SystemExit('Nessun dataflow prezzi trovato')


if __name__ == '__main__':
    main()
