#!/usr/bin/env python3
"""Extract the official annual NIC all-items series for Toscana, 2011-2024.

The Istat dissemination system uses two historical bases over the period needed
for the MEF income comparison:
- tax/price years 2011-2015: NIC annual average, base 2010=100 (flow 167_34)
- 2016 onward: NIC annual average, base 2015=100 (flow 167_742)

The script performs only two SDMX queries (Istat rate limit: 5/min/IP), then
chain-links the two official index series and rebases the result to 2011=100.
No municipal or provincial CPI is imputed to the seven Versilia municipalities.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = 'https://esploradati.istat.it/SDMXWS/rest/data'
UA = {'User-Agent': 'OsservatorioVersilia-data-audit/1.0', 'Accept': 'application/xml'}
QUERIES = [
    {
        'label': 'NIC Toscana annuale base 2010',
        'flow': '167_34',
        'key': 'A.00.ITI1.4.10',
        'start': 2011,
        'end': 2015,
        'baseYear': 2010,
    },
    {
        'label': 'NIC Toscana annuale base 2015',
        'flow': '167_742',
        'key': 'A.ITI1.40.4.00',
        'start': 2016,
        'end': 2024,
        'baseYear': 2015,
    },
]


def local(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def fetch(query: dict) -> tuple[str, bytes]:
    url = f"{ROOT}/{query['flow']}/{query['key']}?startPeriod={query['start']}&endPeriod={query['end']}"
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return url, response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read()[:2000].decode('utf-8', errors='replace')
        raise RuntimeError(f"Istat SDMX HTTP {exc.code} for {url}: {body}") from exc


def parse_sdmx(raw: bytes) -> dict[int, float]:
    root = ET.fromstring(raw)
    observations: dict[int, float] = {}
    # Generic SDMX 2.1 usually uses <Obs><ObsDimension value="YYYY"/><ObsValue value="..."/></Obs>.
    for obs in root.iter():
        if local(obs.tag) != 'Obs':
            continue
        period = None
        value = None
        # Compact SDMX may carry TIME_PERIOD / OBS_VALUE directly on Obs.
        for key, val in obs.attrib.items():
            lk = local(key).upper()
            if lk in {'TIME_PERIOD', 'TIME'}:
                period = val
            elif lk in {'OBS_VALUE', 'VALUE'}:
                value = val
        for child in list(obs):
            name = local(child.tag)
            if name in {'ObsDimension', 'Time'}:
                period = child.attrib.get('value') or child.attrib.get('id') or (child.text or '').strip()
            elif name == 'ObsValue':
                value = child.attrib.get('value') or (child.text or '').strip()
        if period and value is not None and re.fullmatch(r'20\d{2}', str(period)):
            observations[int(period)] = float(str(value).replace(',', '.'))
    if observations:
        return observations

    # Structure-specific SDMX sometimes exposes attributes on arbitrary observation elements.
    for elem in root.iter():
        attrs = {local(k).upper(): v for k, v in elem.attrib.items()}
        period = attrs.get('TIME_PERIOD') or attrs.get('TIME')
        value = attrs.get('OBS_VALUE') or attrs.get('VALUE')
        if period and value is not None and re.fullmatch(r'20\d{2}', period):
            observations[int(period)] = float(value.replace(',', '.'))
    if not observations:
        preview = raw[:3000].decode('utf-8', errors='replace')
        raise RuntimeError(f'nessuna osservazione SDMX riconosciuta; preview={preview}')
    return observations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=Path('/tmp/nic-toscana-2011-2024.json'))
    args = parser.parse_args()

    raw_series = []
    for query in QUERIES:
        url, raw = fetch(query)
        values = parse_sdmx(raw)
        expected = set(range(query['start'], query['end'] + 1))
        if set(values) != expected:
            raise RuntimeError(f"{query['label']}: anni inattesi {sorted(values)}; attesi {sorted(expected)}")
        raw_series.append({'query': query, 'url': url, 'values': values})
        print(query['label'] + ': ' + ', '.join(f'{year}={values[year]:.3f}' for year in sorted(values)))

    old = raw_series[0]['values']
    new = raw_series[1]['values']
    # Rebase old segment to 2011=100. The new series is base 2015=100, so its
    # values express changes relative to the 2015 price level. Link it to the
    # rebased 2015 level of the previous official series.
    linked: dict[int, float] = {}
    for year, value in old.items():
        linked[year] = value / old[2011] * 100.0
    linked_2015 = linked[2015]
    for year, value in new.items():
        linked[year] = linked_2015 * value / 100.0

    # A price index should not jump implausibly at the base splice in a low-inflation year.
    splice_change = (linked[2016] / linked[2015] - 1.0) * 100.0
    if not -5.0 <= splice_change <= 10.0:
        raise RuntimeError(f'variazione 2015-2016 implausibile al raccordo: {splice_change:.2f}%')

    annual_rates = {str(year): round((linked[year] / linked[year - 1] - 1.0) * 100.0, 3)
                    for year in range(2012, 2025)}
    snapshot = {
        'schemaVersion': 1,
        'source': 'Istat - Indice dei prezzi al consumo per l’intera collettività (NIC)',
        'territory': {'code': 'ITI1', 'label': 'Toscana', 'level': 'region'},
        'measure': 'Indice generale, media annua',
        'linkedBase': '2011=100',
        'years': list(range(2011, 2025)),
        'values': [round(linked[year], 4) for year in range(2011, 2025)],
        'annualRatesPercent': annual_rates,
        'splice2015to2016Percent': round(splice_change, 3),
        'sourceSeries': [
            {
                'label': item['query']['label'],
                'flow': item['query']['flow'],
                'key': item['query']['key'],
                'baseYear': item['query']['baseYear'],
                'url': item['url'],
                'values': {str(year): value for year, value in item['values'].items()},
            }
            for item in raw_series
        ],
        'note': (
            'Serie regionale Toscana; non rappresenta né il Comune di Lucca né la Provincia di Lucca. '
            'Il raccordo 2015/2016 concatena due serie ufficiali NIC con basi 2010 e 2015 e presenta il risultato in base 2011=100.'
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('NIC Toscana linked 2011=100: ' + ', '.join(f'{year}={linked[year]:.2f}' for year in range(2011, 2025)))
    print(f'Snapshot: {args.out}')


if __name__ == '__main__':
    main()
