"""Independent fixed records, all-view replay and hostile INVALSI selections."""
import base64
import gzip
import hashlib
import json
import tempfile
from pathlib import Path

from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_invalsi_adapters as inv

# Manually transcribed official default-view municipal records, in canonical code order.
FIXED = (
    (185.2472, 212.5597, 197.6839, 197.7281, 187.8794, None, 196.1073),
    (94.6565, 100, 90.2778, 86.9565, 77.4648, None, 89.1089),
    (12.9167, None, 14.4444, 8.3969, None, None, 11.2766),
    (14.5833, None, 17.7778, 22.9008, None, None, 17.234),
)
BENCHMARKS = ((196.3952,194.9709),(90.52,92.2516),(10.3103,12.3307),(20.4153,18.5066))
HISTORY = (
    [93.3333, 85.5422, 81.3008, 92.233, 86.0697, 97.0732, 94.6565],
    [12.1739, 11.0169, 17.3745, 16.9065, 8.4034, 10.0877, 12.9167],
    [20.8696, 21.6102, 16.6023, 15.8273, 19.7479, 17.5439, 14.5833],
)


def query(key, op='compare', **selection):
    return dict(operation=op, selectors=[dict(metric=key, **selection)])


def regressions(path):
    # Decoder is independent of the adapter and never consumes engine outputs as expectations.
    bodies = [p.read_bytes() for p in sorted((ROOT/inv.DIRECTORY).glob('*.b64'))]
    raw = gzip.decompress(base64.b64decode(b''.join(b.strip() for b in bodies), validate=True))
    native = json.loads(raw); assert hashlib.sha256(raw).hexdigest() == inv.PAYLOAD_SHA
    e = QueryEngine(path, layer='effective'); catalog = e.catalog; replay = bench = levels = 0
    for ki, key in enumerate(inv.KEYS):
        q = query(key); rejected(e, q, 'partial_coverage_requires_opt_in')
        r = e.query(dict(q, allowPartial=True)); assert r['status'] == 'computed', r
        assert [o['value'] for o in r['observations']] == list(FIXED[ki]), (key, [o['value'] for o in r['observations']])
        assert r['coverage']['usable'] == (6 if ki < 2 else 4)
        for bi, scope in enumerate(('tuscany','italy')):
            g=e.query(dict(query(key,'benchmark_gap',towns=['046005']),benchmark=scope))
            assert g['status']=='computed' and g['observations'][1]['value']==BENCHMARKS[ki][bi],g
        for vi, v in enumerate(native[inv.BLOCKS[key]]['views']):
            dim = 'view:'+v['key']
            for code, name in inv.TOWNS.items():
                h = e.query(dict(query(key, 'series', towns=[code], dimension=dim), allowPartial=True))
                expected = v['municipalities'][name]['values']
                assert h['status'] == ('computed' if any(x is not None for x in expected) else 'not_computable'), h
                assert [o['period'] for o in h['observations']] == v['years']
                assert [o['value'] for o in h['observations']] == expected
                assert '2019-20' not in v['years']
                if v['grade'] == 10: assert '2020-21' not in v['years']
                for o in h['observations']:
                    for ev in o['provenance']:
                        if ev['kind'] == 'catalog_snapshot': assert pointer(catalog, ev['valuePointer']) == o['value']
                        else:
                            assert ev['kind'] == 'reconstructed_source_snapshot' and ev['sha256Basis'] == 'decoded_json_bytes'
                            assert pointer(native, ev['recordPointer']) == o['value']
                            assert all((ROOT/p['path']).is_file() and hashlib.sha256((ROOT/p['path']).read_bytes()).hexdigest() == p['sha256'] for p in ev['parts'])
                    assert 'numerator' not in o and 'denominator' not in o and not o['nativeComponentsAvailable']
                    if o['value'] is None: assert o['dataUnavailable'] and not o['notApplicable'] and o['missingReason']
                replay += len(expected)
            for scope in ('tuscany', 'italy'):
                for pi, period in enumerate(v['years']):
                    # Viareggio has a valid observation for all native views/periods.
                    g = e.query(dict(query(key, 'benchmark_gap', towns=['046033'], dimension=dim, periods=[period]), benchmark=scope))
                    assert g['status'] == 'computed', g
                    assert g['observations'][1]['value'] == v[scope]['values'][pi]
                    for ev in g['observations'][1]['provenance']:
                        assert pointer(catalog if ev['kind']=='catalog_snapshot' else native, ev.get('valuePointer') or ev['recordPointer']) == g['observations'][1]['value']
                    bench += 1
            if key == inv.KEYS[1]:
                for li, label in enumerate(v['levelLabels']):
                    ld = dim+'|level:level-'+str(li+1)
                    c = e.query(dict(query(key, dimension=ld), allowPartial=True)); assert c['status'] == 'computed', c
                    for o in c['observations']:
                        vals = v['municipalities'][inv.TOWNS[o['geography']]]['levels'][-1]
                        assert o['value'] == (None if vals is None else vals[li]) and o['levelLabel'] == label
                        assert pointer(catalog, o['provenance'][0]['valuePointer']) == o['value']
                        assert pointer(native, o['provenance'][1]['recordPointer']) == o['value']
                        levels += 1
                    for scope in ('tuscany','italy'):
                        g = e.query(dict(query(key, 'benchmark_gap', towns=['046033'], dimension=ld), benchmark=scope))
                        assert g['status']=='computed' and g['observations'][1]['value']==v[scope]['levels'][-1][li], g
                    rejected(e, query(key, 'series', towns=['046005'], dimension=ld), 'invalsi_level_history_not_published_in_catalog')
                    rejected(e, query(key, dimension=ld, periods=[v['years'][0]]), 'invalsi_level_history_not_published_in_catalog')
        if ki > 0:
            h = e.query(query(key, 'series', towns=['046005'])); assert h['status']=='computed'
            assert [o['value'] for o in h['observations']] == HISTORY[ki-1]
        for op in ('absolute_change','relative_change','percentage_points','trend'):
            rejected(e, query(key, op, towns=['046005']), 'invalsi_temporal_continuity_not_reviewed')
        rejected(e, query(key,'weighted_ratio'), 'invalsi_valid_student_denominators_unavailable')
        rejected(e, query(key,'anomaly'), 'invalsi_peer_anomaly_not_reviewed')
        for period in ('2025','2024/25','2024-24'):
            rejected(e, query(key,periods=[period]), 'invalsi_academic_year_required')
        rejected(e, query(key,periods=['2019-20']), 'invalsi_period_not_frozen')
        rejected(e, dict(query(key,'benchmark_gap',towns=['046005']),benchmark='versilia'), 'invalsi_benchmark_scope_not_reviewed')
        for pair in ([dict(metric=key),dict(metric='population')],[dict(metric='population'),dict(metric=key)]):
            rejected(e,dict(operation='correlation',selectors=pair,axis='municipalities',method='pearson',purpose='descriptive'), 'invalsi_pair_not_jointly_reviewed')
        mutations = [lambda m:m['meta'].update(unit='number'), lambda m:m['meta'].update(year='2025'),
                     lambda m:m['meta'].update(defaultView='g13'), lambda m:m.update(sourceUrl='https://example.com'),
                     lambda m:m['rows'][0].update(code='046030'), lambda m:m['rows'][0].update(town='Stazzema'),
                     lambda m:m['rows'][0].update(value=0), lambda m:m['rows'][5].update(value=0),
                     lambda m:m['rows'][0]['parts'][0].update(grade=99),
                     lambda m:m['rows'][0]['parts'][0].update(subject='Wrong'),
                     lambda m:m['viewDefinitions'][0].update(coverage='7/7'),
                     lambda m:m['rows'][0]['seriesByView'][inv.VIEWS[key][0]]['periodLabels'].__setitem__(0,'2024-25'),
                     lambda m:m['aggregate'].update(value=999), lambda m:m['nationalBenchmark']['parts'][0].update(value=999),
                     lambda m:m['rows'][0].update(ratioComponents=dict(numerator=1,denominator=100))]
        for mutation in mutations:
            g = QueryEngine(path, layer='effective'); mutation(g._catalog['metrics'][key])
            assert g.query(dict(q,allowPartial=True))['status']=='not_computable'
    level = 'view:g5-inglese-reading|level:level-1'
    r=e.query(query(inv.KEYS[1],towns=['046005','046013'],dimension=level))
    assert [o['value'] for o in r['observations']]==[5.3435,0], r
    for mutation in [lambda g:g._invalsi_payload[0]['results']['views'][0]['municipalities']['Camaiore']['values'].__setitem__(0,0),
                     lambda g:g._invalsi_payload[1].update(sha256='0'*64),
                     lambda g:g._invalsi_payload[1]['parts'][0].update(sha256='0'*64)]:
        g=QueryEngine(path,layer='effective'); inv.frozen(g); mutation(g)
        rejected(g,dict(query(inv.KEYS[0]),allowPartial=True),'invalsi_frozen_payload_changed')
    for field in ('levelLabels','levels'):
        g=QueryEngine(path,layer='effective'); p=g._catalog['metrics'][inv.KEYS[1]]['rows'][0]['parts'][0]
        if field=='levelLabels':p[field][0]='invented category'
        else:p[field][0]['value']=100
        assert g.query(query(inv.KEYS[1],towns=['046005','046013']))['status']=='not_computable'
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);d=root/inv.DIRECTORY;d.mkdir(parents=True)
        for i,b in enumerate(bodies):(d/f'part-{i:02}.b64').write_bytes(b)
        (d/'part-00.b64').write_bytes(bodies[0]+b' ')
        g=QueryEngine(path,layer='effective',repository_root=root)
        rejected(g,dict(query(inv.KEYS[0]),allowPartial=True),'invalsi_frozen_fragment_changed')
    print(f'INVALSI PASS: 28 fixed current cells, 21 fixed historical cells, eight fixed benchmarks, two fixed QCER levels; {replay} native historical cells, {bench} official benchmark cells, {levels} current level cells replayed; provenance reconstruction and hostile mutations')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
