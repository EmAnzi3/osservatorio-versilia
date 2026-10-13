"""Native territorial totals: independent compact decode and public reconciliation.

The fixed 2025/2014 references were transcribed in PR #423 before this fix.
Their source is the frozen compact `tt` table, not materializer/query output.
Original Register CSVs are identified by metadata hashes but not replayed here.
"""
import base64
import copy
import gzip
import json
import re
from pathlib import Path

from materialize_economy_atlas_release import latest_town_totals, make_metric

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    '046005': ('Camaiore', 3907, 3822, 58),
    '046013': ('Forte dei Marmi', 1492, 1556, 13),
    '046018': ('Massarosa', 2053, 1940, 31),
    '046024': ('Pietrasanta', 3341, 3327, 43),
    '046028': ('Seravezza', 1413, 1437, 25),
    '046030': ('Stazzema', 260, 245, 2),
    '046033': ('Viareggio', 7992, 7998, 120),
}


def rejected(payload):
    try:
        latest_town_totals(payload)
    except RuntimeError:
        return
    raise AssertionError('Malformed territorial totals accepted')


def regressions(catalog_path):
    folder = ROOT / 'data/economy-atlas'
    meta = json.loads((folder / 'metadata.json').read_text())
    raw = json.loads(gzip.decompress(base64.b64decode(''.join(
        (folder / name).read_text().strip() for name in meta['files']))))
    before = copy.deepcopy(raw)
    catalog = json.loads(Path(catalog_path).read_text())
    native = latest_town_totals(raw)
    metric = make_metric(catalog, raw)
    published = catalog['metrics']['economyActivityAtlas']
    assert raw == before, 'Materializer mutated historical or category data'
    assert raw['y'] == list(range(2014, 2026))
    assert len({row[0] for row in raw['c']}) == len(raw['c']) == 1228
    assert set(EXPECTED) == {r['code'] for r in published['rows']}
    for row in published['rows']:
        name, first, last, direct = EXPECTED[row['code']]
        ti = next(i for i, t in enumerate(raw['t']) if t == [row['slug'], name])
        assert raw['tt'][ti][0] == first and raw['tt'][ti][-1] == last
        assert row['town'] == name and row['year'] == 2025
        assert row['value'] == native[row['slug']] == last
        assert row['formatted'] == f'{last:,}'.replace(',', '.')
        divisions = [r for r in raw['c'] if re.fullmatch(r'[A-Z] \d{2}', r[0])]
        assert sum(r[3 + ti][0][-1] or 0 for r in divisions) == direct
        assert row['value'] != direct
    assert published['rows'] == metric['rows']
    assert metric['aggregate']['value'] == published['aggregate']['value'] == 20325
    assert sum(v[3] for v in EXPECTED.values()) == 292
    assert sum(v[2] for v in EXPECTED.values()) == 20325
    # Category duplication/selection or all descendants never affects native totals.
    for categories in [[], raw['c'] * 2, list(reversed(raw['c']))]:
        altered = copy.deepcopy(raw)
        altered['c'] = categories
        assert latest_town_totals(altered) == native
    altered = copy.deepcopy(raw)
    altered['tt'][0][-1] = 0
    assert latest_town_totals(altered)[raw['t'][0][0]] == 0
    altered['tt'][0][0] = None
    assert latest_town_totals(altered)[raw['t'][0][0]] == 0
    assert altered['tt'][0][0] is None, 'No historical imputation'
    for value in [None, -1, True, 1.5, '3822']:
        altered = copy.deepcopy(raw)
        altered['tt'][0][-1] = value
        rejected(altered)
    for field, value in [('tt', raw['tt'][:-1]), ('tt', None),
                         ('t', raw['t'][:-1]), ('t', raw['t'][:-1] + raw['t'][:1]),
                         ('y', raw['y'][:-1]), ('y', raw['y'][:-1] + [2024])]:
        altered = copy.deepcopy(raw)
        altered[field] = value
        rejected(altered)
    altered = copy.deepcopy(raw)
    altered['tt'][0] = altered['tt'][0][:-1]
    rejected(altered)
    # Replay all 84 territorial cells through the public query interface.
    from semantic_query_engine import QueryEngine
    engine = QueryEngine(catalog_path, layer='effective')
    for row in published['rows']:
        ti = next(i for i, t in enumerate(raw['t']) if t[0] == row['slug'])
        result = engine.query(dict(operation='series', selectors=[dict(
            metric='economyActivityAtlas', dimension='territoryTotal', towns=[row['code']])]))
        assert result['status'] == 'computed', result
        assert [o['period'] for o in result['observations']] == [str(y) for y in raw['y']]
        assert [o['value'] for o in result['observations']] == raw['tt'][ti]
    print('Atlas totals PASS: 7 ISTAT identities, 20325 native vs 292 direct divisions; '
          '84 historical cells, zero/null/partial/duplicate/axis adversarial checks')


if __name__ == '__main__':
    regressions(ROOT / 'dist/data/site-data.json')
