"""Independent fixed inventory counts, memberships, provenance and cached attacks."""
import base64
from collections import Counter
import gzip
import json
from pathlib import Path
import tempfile

from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_slow_mobility_adapters as s

# Total, trekking, cammini, bicycle, MTB. Transcribed inventory references.
FIXED = {'046005': (11,3,2,5,1), '046013': (2,0,0,2,0),
         '046018': (5,0,1,3,1), '046024': (6,2,1,3,0),
         '046028': (15,12,1,2,0), '046030': (25,23,0,2,0),
         '046033': (4,0,0,3,1)}
INDEX = {'slowMobilityRoutes':0,'slowMobilityTrekking':1,
         'slowMobilityCammini':2,'slowMobilityBici':3,'slowMobilityMtb':4}


def query(key='slowMobilityRoutes', op='compare', **selection):
    return dict(operation=op,selectors=[dict(dict(metric=key,dimension='total'),**selection)])


def regressions(path):
    e=QueryEngine(path,layer='effective');count=0
    # Separate decoder, including original coordinates; anchors above are not engine output.
    original=[r for p in sorted((ROOT/'percorsi/data').glob('routes-part-*.b64'))
              for r in json.loads(gzip.decompress(base64.b64decode(p.read_text())))]
    assert len(original)==41 and len({r['p']['id'] for r in original})==41
    assert Counter(r['p']['quality_code'] for r in original)=={'A0':30,'B1':11}
    assert Counter(r['p']['primary_mode'] for r in original)=={'trekking':31,'cammino':2,'bicycle':7,'mtb':1}
    assert sum(len(r['p']['municipalities']) for r in original)==68
    mtb=next(r['p'] for r in original if r['p']['id']=='mm-vrg-mtb-05')
    assert mtb['municipalities']==['Camaiore','Massarosa','Viareggio'] and mtb['primary_mode']=='mtb'
    bicycle=next(r['p'] for r in original if r['p']['id']=='mm-vrg-cyc-03')
    assert bicycle['municipalities']==['Camaiore','Forte dei Marmi','Pietrasanta','Seravezza','Stazzema','Viareggio']
    for key in s.KEYS:
        result=e.query(query(key));assert result['status']=='computed',result
        assert set(s.NOTES)<=set(result['warnings'])
        for o in result['observations']:
            count+=1;code=o['geography'];town=s.TOWNS[code]
            assert o['value']==FIXED[code][INDEX[key]]
            assert o['unit']=='count' and o['period']==s.PERIOD
            assert not o['notApplicable'] and not o['dataUnavailable']
            assert o['nativeRecordReplayAvailable'] and not o['nativeComponentsAvailable']
            expected=sorted(r['p']['id'] for r in original if town in r['p']['municipalities'] and (s.MODES[key] is None or r['p']['primary_mode']==s.MODES[key]))
            assert o['countedRouteIds']==expected
            assert pointer(e.catalog,o['provenance'][0]['valuePointer'])==o['value']
            assert len(o['provenance'])==8
            for p in o['provenance'][1:6]:
                assert p['encoding']=='base64+gzip+json' and p['decodedSha256']
                for ptr in p['recordPointers']:
                    rows=e.files[p['path']][0];i=int(ptr.split('/')[1]);assert rows[i]['p']['id'] in expected
                assert all(set(r)=={'p'} for r in e.files[p['path']][0])
        ranked=e.query(query(key,'rank'));assert ranked['status']=='computed',ranked
        assert [r['geography'] for r in ranked['result']['ranking']]==sorted(FIXED,key=lambda c:(-FIXED[c][INDEX[key]],c))
        for op in ['series','absolute_change','relative_change','percentage_points','trend']:
            rejected(e,query(key,op),'slow_mobility_inventory_history_editorial_not_territorial_series')
        rejected(e,query(key,'weighted_ratio'),'slow_mobility_municipal_memberships_overlap_no_pooling')
        rejected(e,query(key,'anomaly'),'slow_mobility_inventory_peer_anomaly_not_reviewed')
        for scope in ['tuscany','versilia']:
            rejected(e,dict(query(key,'benchmark_gap'),benchmark=scope),'slow_mobility_geographic_benchmark_not_reviewed')
        for period in ['2025','2027','2026-01-01']:
            rejected(e,query(key,periods=[period]),'slow_mobility_period_not_frozen')
        assert e.query(query(key,periods=[s.PERIOD]))['status']=='computed'
        for dim in ['nativeRatio','view:normalized','kilometres','quality:A0','denominator']:
            rejected(e,query(key,dimension=dim),'dimension_adapter_not_implemented')
        for pair in [[dict(metric=key),dict(metric='population')],[dict(metric='population'),dict(metric=key)]]:
            rejected(e,dict(operation='correlation',selectors=pair,axis='municipalities',method='pearson',purpose='descriptive'),'slow_mobility_shared_route_records_pair_not_reviewed')
        mutations=[lambda m:m['meta'].update(year='2025'),lambda m:m['meta'].update(unit='km'),
                   lambda m:m.update(sourceUrl='https://example.com'),lambda m:m['rows'][0].update(value=False),
                   lambda m:m['rows'][0].update(town='Unknown'),lambda m:m['rows'][0].update(dataUnavailable=True),
                   lambda m:m['rows'][0].update(series={'years':[2025],'values':[1]}),
                   lambda m:m['aggregate'].update(value=999),lambda m:m['method'].update(caveat='Additive counts')]
        for mutate in mutations:
            g=QueryEngine(path,layer='effective');assert g.query(query(key))['status']=='computed';mutate(g._catalog['metrics'][key])
            rejected(g,query(key),'slow_mobility_public_definition_or_values_changed')
    assert count==35
    assert [sum(v[i] for v in FIXED.values()) for i in range(5)]==[68,40,5,20,3]
    assert [len({r for o in e.query(query(k))['observations'] for r in o['countedRouteIds']}) for k in s.KEYS]==[41,31,2,7,1]
    attacks=[lambda p:p.update(id='unknown'),lambda p:p.update(primary_mode='mtb'),
             lambda p:p.update(municipalities=['Unknown']),lambda p:p.update(municipalities=['Camaiore','Camaiore']),
             lambda p:p.update(quality_code='B2'),lambda p:p.update(public_default=False),
             lambda p:p.update(publication_status='draft'),lambda p:p.update(source_url='https://example.com'),
             lambda p:p.update(temporal_status='current_safe')]
    for attack in attacks:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
        attack(g.files['percorsi/data/routes-part-00.b64'][0][0]['p'])
        rejected(g,query(),'slow_mobility_frozen_route_part_changed')
    g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
    g.files['percorsi/data/routes-part-00.b64'][1]['decodedSha256']='0'*64
    rejected(g,query(),'slow_mobility_frozen_route_part_changed')
    for relative,mutate in [('percorsi/data/site_stats.json',lambda d:d['versilia'].update(routes=68)),
                            ('percorsi/data/site_stats.json',lambda d:d['municipalities']['stazzema'].update(routes=0)),
                            ('percorsi/data/master_summary.json',lambda d:d.update(public_total=93))]:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed';mutate(g.files[relative][0])
        rejected(g,query(),'slow_mobility_frozen_inventory_metadata_changed')
    g=QueryEngine(path,layer='effective');g._catalog['towns'][0]['name']='Unknown'
    rejected(g,query(),'slow_mobility_municipal_identity_changed')
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp)/'percorsi/data/routes-part-00.b64';p.parent.mkdir(parents=True);p.write_bytes(b'changed')
        g=QueryEngine(path,repository_root=temp,layer='effective')
        rejected(g,query(),'slow_mobility_frozen_route_part_changed')
    print('Slow mobility PASS: 35 fixed counts, 41 native public route records / 68 memberships; primary modes, zeros/ties, nonadditivity, provenance, frozen dates and hostile cached edits; original geometry intersections not replayed')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
