"""Independent register counts, compact replay and explicit hierarchy limits."""
import base64
import gzip
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from semantic_query_engine import QueryEngine,ROOT
from test_semantic_query_engine import rejected
import semantic_query_economy_atlas_adapters as a

TOTALS=(3822,1556,1940,3327,1437,245,7998)
FIRST_TOTALS=(3907,1492,2053,3341,1413,260,7992)
ACTIVE={'I 561011':(334,186,86,340,94,34,740),
        'C 3012':(10,0,21,3,0,None,114),
        'C 23701':(4,3,4,88,60,8,1),
        'R 93292':(100,104,None,110,2,None,130),
        'F 412':(141,37,84,76,37,7,281)}
FIRST={'I 561011':(258,154,80,284,72,34,518),
       'C 3012':(16,1,21,1,0,None,135),
       'C 23701':(2,4,6,89,67,6,5),
       'R 93292':(96,98,None,104,2,None,118),
       'F 412':(248,50,131,133,36,11,337)}
ARTISAN={'I 561011':(0,0,0,0,4,0,4), 'C 3012':(2,0,9,1,0,None,30),
         'C 23701':(3,1,2,44,18,2,0), 'R 93292':(0,0,None,0,0,None,0),
         'F 412':(90,8,47,41,15,6,97)}


def query(dim='territoryTotal',op='compare',**selection):
    return dict(operation=op,selectors=[dict(metric='economyActivityAtlas',dimension=dim,**selection)])


def regressions(path):
    from test_economy_atlas_totals import regressions as total_regressions
    total_regressions(path)
    e=QueryEngine(path,layer='effective');codes=sorted(a.TOWNS)
    for dim,period,values in [('territoryTotal','2025',TOTALS),('territoryTotal','2014',FIRST_TOTALS)]+[(f'ateco:{c}|{m}',y,v) for c in ACTIVE for m,y,v in [('active','2025',ACTIVE[c]),('active','2014',FIRST[c]),('artisan','2025',ARTISAN[c])]]:
        q=query(dim,periods=[period]);q['allowPartial']=True;r=e.query(q);assert r['status']=='computed',r
        assert len(r['observations'])==7
        for o,c,v in zip(r['observations'],codes,values):
            assert o['geography']==c and o['value']==v and o['period']==period and o['unit']=='number'
            assert o['dataUnavailable']==(v is None) and not o['nativeRecordReplayAvailable']
            assert not o['nativeComponentsAvailable'] and all(len(x['sha256'])==64 for x in o['provenance'])
            assert any(x.get('valuePointer') and x.get('decodedScope') for x in o['provenance'])
        assert set(a.NOTES)<=set(r['warnings'])
    assert sum(TOTALS)==20325 and e.catalog['metrics']['economyActivityAtlas']['aggregate']['value']==20325
    rejected(e,dict(operation='compare',selectors=[dict(metric='economyActivityAtlas')]),'atlas_explicit_view_required')
    rank=e.query(query('territoryTotal','rank'));assert rank['status']=='computed'
    assert [o['geography'] for o in rank['result']['ranking']]==['046033','046005','046024','046018','046013','046028','046030']
    series=e.query(query('territoryTotal','series',towns=['046018']));assert series['status']=='computed',series
    assert [o['value'] for o in series['observations']]==[2053,2025,2046,2022,2001,1995,1976,1984,2005,1969,1943,1940]
    rejected(e,query('ateco:C 3012|active'),'partial_coverage_requires_opt_in')
    partial=e.query(dict(query('ateco:C 3012|active'),allowPartial=True));assert partial['coverage']['usable']==6 and len(partial['excluded'])==1
    assert partial['excluded'][0]['observation']['geography']=='046030'
    for dim in ['ateco:C|active','ateco:C 30.12|active','ateco:C 999999|active','lq','artisanShare','regionalWeight','sumDescendants']:
        rejected(e,query(dim),'dimension_adapter_not_implemented')
    for op in ['absolute_change','relative_change','percentage_points','trend']:rejected(e,query(op=op),'atlas_temporal_continuity_not_reviewed')
    for op,reason in [('weighted_ratio','atlas_hierarchy_and_scope_pooling_not_reviewed'),('anomaly','atlas_peer_anomaly_not_reviewed')]:rejected(e,query(op=op),reason)
    rejected(e,dict(query(op='benchmark_gap'),benchmark='tuscany'),'atlas_absolute_regional_volume_not_municipal_benchmark')
    rejected(e,query('ateco:C 3012|artisan','series',towns=['046018']),'atlas_artisan_only_2025_frozen')
    rejected(e,query('ateco:I 561011|artisan',periods=['2014']),'atlas_artisan_only_2025_frozen')
    for y in ['2010','2013','2026']:rejected(e,query(periods=[y]),'atlas_only_2014_2025_frozen')
    for pair in [[dict(metric='economyActivityAtlas',dimension='territoryTotal'),dict(metric='localUnits')],[dict(metric='localUnits'),dict(metric='economyActivityAtlas',dimension='territoryTotal')]]:
        rejected(e,dict(operation='correlation',selectors=pair,axis='municipalities',method='pearson',purpose='descriptive'),'atlas_pair_not_jointly_reviewed')
    for mutate in [lambda m:m['rows'][0].update(value=1),lambda m:m['meta'].update(year='2026'),lambda m:m['method'].update(formula='exhaustive total'),lambda m:m['dataStorage']['compactSchema'].update(townSeriesIndex=1),lambda m:m.update(sourceUrl='other')]:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed';mutate(g._catalog['metrics']['economyActivityAtlas']);rejected(g,query(),'atlas_public_definition_or_values_changed')
    g=QueryEngine(path,layer='effective');g._catalog['towns'][0]['name']='Unknown';rejected(g,query(),'atlas_municipal_identity_changed')
    # Separate full compact-cell replay, independently decoded from the 10 chunks.
    folder=ROOT/'data/economy-atlas';meta=json.loads((folder/'metadata.json').read_text());raw=json.loads(gzip.decompress(base64.b64decode(''.join((folder/n).read_text().strip() for n in meta['files']))));data,taxonomy=a.payload()
    assert len(raw['c'])==len({r[0] for r in raw['c']})==1228 and raw['y']==list(range(2014,2026))
    assert len(a.dimensions('economyActivityAtlas'))==2457
    cells=nulls=0
    for ri,row in enumerate(raw['c']):
        for ti in range(7):
            for yi in range(12):
                v=row[3+ti][0][yi];assert v is None or type(v) is int and v>=0
                assert data['c'][ri][3+ti][0][yi]==v;cells+=1;nulls+=v is None
            v=row[3+ti][1];assert v is None or type(v) is int and v>=0
            assert data['c'][ri][3+ti][1]==v;cells+=1;nulls+=v is None
    for ti in range(7):
        for yi in range(12):assert data['tt'][ti][yi]==raw['tt'][ti][yi];cells+=1
    assert cells==111832
    try:data['c'][0][3][0][0]=999
    except TypeError:pass
    else:raise AssertionError('mutable decoded cache')
    original_root=a.ROOT
    try:
        with TemporaryDirectory(prefix='atlas-frozen-byte-') as temp:
            a.ROOT=Path(temp);dest=a.ROOT/'data/economy-atlas';dest.mkdir(parents=True)
            for n in a.FILES:(dest/n).write_bytes((folder/n).read_bytes())
            g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
            for n in ['metadata.json','atlas-00.b64','ateco-taxonomy-00.b64']:
                b=(dest/n).read_bytes();(dest/n).write_bytes(b+b' ');rejected(g,query(),'atlas_frozen_file_bytes_changed');(dest/n).write_bytes(b)
    finally:a.ROOT=original_root
    print(f'Atlas PASS: 119 fixed counts, exact categories and periods, 111832 compact cells including {nulls} nulls replayed separately; reconciled carrier20325/direct division292 distinction, frozen bytes, immutable cache and refusal boundaries; no original-register replay')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
