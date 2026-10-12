"""Independent fixed prices/densities, separate summary replay and hostile guards."""
import copy
import math
import statistics
import tempfile
from pathlib import Path
from semantic_query_engine import QueryEngine,ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_energy_adapters as a

# Independently reviewed published thousandths / hundredths, not engine answers.
CURRENT={'046005':(2030,2289),'046013':(2011,2242),'046018':(2077,2277),'046024':(2010,2230),'046028':(2030,2291),'046030':(None,None),'046033':(1994,2254)}
EV={'046005':54,'046013':595,'046018':46,'046024':132,'046028':24,'046030':72,'046033':79}
MASS_DAILY=[('2026-08-14',1987,2088),('2026-08-27',2018,2147),('2026-08-28',2018,2147),('2026-10-03',2097,2299),('2026-10-10',2077,2277)]
MASS_MONTHLY=[('2022-01',1764,1637,31),('2022-03',1994,1964,29),('2026-09',2112,2266,29)]


def query(key='fuelPrices',dim='total',op='compare',**sel):return dict(operation=op,selectors=[dict(metric=key,dimension=dim,**sel)])


def regressions(path):
    e=QueryEngine(path,layer='effective')
    for dim in ['total','fuel:benzina','fuel:gasolio']:
        r=e.query(dict(query(dim=dim),allowPartial=True));assert r['status']=='computed',r
        for o in r['observations']:
            wanted=CURRENT[o['geography']][1 if dim=='fuel:gasolio' else 0]
            assert o['value']==(None if wanted is None else wanted/1000)
            assert o['period']=='2026-10-10' and not o['nativeRecordReplayAvailable']
            snap,ref=e.file(o['evidence'][0]['path']);assert pointer(snap,o['evidence'][0]['valuePointer'])==o['value']
        assert len(r['excluded'])==1 and r['excluded'][0]['observation']['geography']=='046030'
        r=e.query(dict(query(dim=dim,op='rank'),allowPartial=True));assert r['status']=='computed',r
        assert [o['geography'] for o in r['result']['ranking']]==sorted((c for c in CURRENT if c!='046030'),key=lambda c:(-CURRENT[c][1 if dim=='fuel:gasolio' else 0],c))
    for dim in ['fuel:benzina','fuel:gasolio','monthly:benzina','monthly:gasolio']:
        series=e.query(query(dim=dim,op='series',towns=['046018']));assert series['status']=='computed',series
        assert len(series['observations'])==(57 if dim.startswith('monthly') else 5)
        anchors=MASS_MONTHLY if dim.startswith('monthly') else MASS_DAILY
        for anchor in anchors:
            p=anchor[0];r=e.query(query(dim=dim,periods=[p],towns=['046018','046033']));assert r['status']=='computed',r
            o=r['observations'][0];assert o['value']==anchor[2 if dim.endswith('gasolio') else 1]/1000
            if dim.startswith('monthly'):assert o['observationDays']==o['fuelObservationDays']==anchor[3]
    # Separate exhaustive replay into the normalized snapshots, including 124 nulls.
    cells=0;nulls=0
    for mode,(source,sha,obj) in a.FILES.items():
        snap,ref=e.file(source)
        for point in snap['points']:
            for fuel in ['benzina','gasolio']:
                dim=('monthly:' if mode=='monthly' else 'fuel:')+fuel
                r=e.query(dict(query(dim=dim,periods=[point['referenceDate']]),allowPartial=True));assert r['status']=='computed',r
                for o in r['observations']:
                    wanted=point['towns'][a.TOWNS[o['geography']]][fuel];assert o['value']==wanted
                    assert pointer(snap,o['evidence'][0]['valuePointer'])==wanted
                    cells+=1;nulls+=wanted is None
    assert (cells,nulls)==(868,124)
    r=e.query(query('evPoints'));assert r['status']=='computed',r
    for o in r['observations']:
        assert o['value']==EV[o['geography']]/100 and o['period']=='2026'
        assert not o['nativeComponentsAvailable'] and not o['nativeRecordReplayAvailable']
        assert pointer(e.catalog,o['evidence'][0]['valuePointer'])==o['value']
    assert e.query(query('evPoints',op='rank'))['status']=='computed'
    rejected(e,query('evPoints',op='series'),'energy_ev_history_not_frozen')
    for key in a.KEYS:
        for dim in a.dimensions(key):
            for op in ['absolute_change','relative_change','percentage_points','trend']:
                rejected(e,query(key,dim,op),'energy_temporal_continuity_not_reviewed')
            for op,reason in [('weighted_ratio','energy_native_pooling_not_reviewed'),('benchmark_gap','energy_geographic_benchmark_not_reviewed'),('anomaly','energy_peer_anomaly_not_reviewed')]:
                rejected(e,dict(query(key,dim,op),**({'benchmark':'tuscany'} if op=='benchmark_gap' else {})),reason)
            for selectors in [[dict(metric=key,dimension=dim),dict(metric='population')],[dict(metric='population'),dict(metric=key,dimension=dim)]]:
                rejected(e,dict(operation='correlation',selectors=selectors,axis='municipalities',method='pearson',purpose='descriptive'),'energy_pair_not_jointly_reviewed')
        for mutation in [lambda m:m['rows'][0].update(value=9),lambda m:m['meta'].update(year='2025'),lambda m:m['method'].update(caveat='certified components'),lambda m:m.update(sourceUrl='other'),lambda m:m['aggregate'].update(value=0)]:
            g=QueryEngine(path,layer='effective');g.query(dict(query(key),allowPartial=True));mutation(g._catalog['metrics'][key]);rejected(g,query(key),'energy_public_definition_or_values_changed')
    for mode,(source,sha,obj) in a.FILES.items():
        dim='monthly:benzina' if mode=='monthly' else 'fuel:benzina'
        for mutation in [lambda s:s['points'][0]['towns']['Massarosa'].update(benzina=4),lambda s:s['points'].append(copy.deepcopy(s['points'][0])),lambda s:s.update(provenance='other')]:
            g=QueryEngine(path,layer='effective');g.query(dict(query(dim=dim),allowPartial=True));mutation(g.files[source][0]);rejected(g,query(dim=dim),'energy_frozen_fuel_input_changed')
        g=QueryEngine(path,layer='effective');g.query(dict(query(dim=dim),allowPartial=True));g.files[source][1]['sha256']='0'*64;rejected(g,query(dim=dim),'energy_frozen_fuel_input_changed')
        with tempfile.TemporaryDirectory() as folder:
            g=QueryEngine(path,layer='effective');g.root=Path(folder);target=g.root/source;target.parent.mkdir(parents=True);target.write_text('{}');rejected(g,query(dim=dim),'energy_frozen_fuel_input_changed')
    g=QueryEngine(path,layer='effective');g.query(dict(query(dim='monthly:benzina'),allowPartial=True));g.files[a.FILES['monthly'][0]][0]['points'][-1]['towns']['Massarosa']['benzinaDays']=30
    rejected(g,query(dim='monthly:benzina'),'energy_frozen_fuel_input_changed')
    for key in a.KEYS:
        g=QueryEngine(path,layer='effective');g._catalog['towns'][0]['name']='Unknown';rejected(g,query(key),'energy_municipal_identity_changed')
    rejected(e,query(dim='monthly:benzina',periods=['2026-10-10']),'energy_period_not_frozen_for_selected_statistic')
    rejected(e,query(dim='fuel:benzina',periods=['2026-09']),'energy_period_not_frozen_for_selected_statistic')
    rejected(e,query(periods=['2026']),'energy_period_not_frozen')
    assert statistics.mean([statistics.median([1,1,4]),statistics.median([3,3,3])])!=statistics.median([1,1,4,3,3,3])
    print('Energy PASS: 21 current fuel anchors incl nulls, 7 EV densities, five daily and three monthly Massarosa pairs; separate 868-cell normalized replay incl 124 nulls, observed days, provenance, nonpooling and hostile cache/bytes; native archives and EV records not replayed')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
