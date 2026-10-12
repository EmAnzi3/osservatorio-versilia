"""Independent municipal anchors, separate record replay, input/cache guards."""
import copy
import math
import tempfile
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from semantic_query_engine import QueryEngine,ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_pnrr_adapters as a

# Reviewed euro cents / project counts / phase-5 counts / POSAS residents.
ANCHORS={'046005':(327051141,16,11,31763),'046013':(133764446,15,10,6550),
         '046018':(596520814,11,10,21782),'046024':(947823798,12,10,22678),
         '046028':(248548563,12,9,12284),'046030':(205550234,11,10,2783),
         '046033':(1209051768,24,18,60680)}


def query(key='pnrrFunding',dim='total',op='compare',**selection):
    return dict(operation=op,selectors=[dict(metric=key,dimension=dim,**selection)])


def wanted(key,dim,c):
    cents,projects,concluded,residents=ANCHORS[c]
    if key=='pnrrFunding':return Fraction(cents,100 if dim=='fundingEuro' else 100*residents)
    if dim=='selectedProjects':return Fraction(projects)
    if dim=='concludedProjects':return Fraction(concluded)
    return Fraction(concluded*100,projects)


def regressions(path):
    e=QueryEngine(path,layer='effective');snap,ref=e.file(a.PATH)
    # Independent iteration, not adapter output or snapshot's stale perTown summaries.
    assert len(snap['records'])==101 and len({r['id_progetto'] for r in snap['records']})==101
    for c,(cents,projects,concluded,residents) in ANCHORS.items():
        rows=[r for r in snap['records'] if r['soggetto_attuatore']=='COMUNE DI '+a.TOWNS[c].upper()]
        assert len(rows)==projects
        assert sum(Decimal(r['importo_finanziato_pnrr']) for r in rows)==Decimal(cents)/100
        assert sum(r['fase_avanzamento_da_regis']=='5. conclusione' for r in rows)==concluded
    vr=[r for r in snap['records'] if r['soggetto_attuatore']=='COMUNE DI VIAREGGIO']
    assert sum(r['fase_avanzamento_da_monitoraggio_progetti']=='5. conclusione' for r in vr)==19
    assert ANCHORS['046033'][2]==18
    assert sum(r['codistat']!='046033' for r in vr)==6
    assert any(r['codistat']=='052031' and r['soggetto_attuatore']=='COMUNE DI STAZZEMA' for r in snap['records'])
    assert sum(r['data_fine_effettiva_chiusura_intervento'] not in ('','0001-01-01') for r in snap['records'])==1
    assert any(r['fase_avanzamento_da_regis']=='5. conclusione' and r['fase_regis']=='COLLAUDO avviata' for r in snap['records'])
    for key in a.KEYS:
        for dim in a.dimensions(key):
            r=e.query(query(key,dim));assert r['status']=='computed',r
            for o in r['observations']:
                assert math.isclose(o['value'],float(wanted(key,dim,o['geography'])),rel_tol=0,abs_tol=1e-8)
                assert o['period']==a.PERIOD and not o['nativeRecordReplayAvailable']
                assert pointer(e.catalog,o['evidence'][0]['valuePointer'])==o['value']
                records=[pointer(snap,p) for p in o['evidence'][1]['recordPointers']]
                assert len(records)==ANCHORS[o['geography']][1] and all(t['soggetto_attuatore']=='COMUNE DI '+a.TOWNS[o['geography']].upper() for t in records)
                if dim=='nativeRatio':
                    assert o['denominatorPeriod']==(a.POPULATION_PERIOD if key=='pnrrFunding' else a.PERIOD)
                    assert pointer(e.catalog,o['evidence'][2]['denominatorPointer'])==o['denominator']
                    assert pointer(e.catalog,o['evidence'][2]['numeratorPointer'])==o['numerator']
            r=e.query(query(key,dim,'rank'));assert r['status']=='computed',r
            assert [o['geography'] for o in r['result']['ranking']]==sorted(ANCHORS,key=lambda c:(-wanted(key,dim,c),c))
            assert e.query(query(key,dim,periods=['2026']))['observations'][0]['period']==a.PERIOD
            for op in ['series','absolute_change','relative_change','percentage_points','trend']:
                rejected(e,query(key,dim,op),'pnrr_portfolio_history_not_frozen')
            for op,reason in [('benchmark_gap','pnrr_geographic_benchmark_not_reviewed'),('anomaly','pnrr_peer_anomaly_not_reviewed')]:
                rejected(e,dict(query(key,dim,op),**({'benchmark':'tuscany'} if op=='benchmark_gap' else {})),reason)
            if dim!='nativeRatio':rejected(e,query(key,dim,'weighted_ratio'),'pnrr_native_ratio_dimension_required')
            for period in ['2025','2026-01-01','2026-09-24','2027']:
                rejected(e,query(key,dim,periods=[period]),'pnrr_period_not_frozen')
        for codes in [list(ANCHORS),['046005','046018']]:
            r=e.query(query(key,'nativeRatio','weighted_ratio',towns=codes));assert r['status']=='computed',r
            numerator=sum(ANCHORS[c][0] for c in codes)/100 if key=='pnrrFunding' else sum(ANCHORS[c][2] for c in codes)
            denominator=sum(ANCHORS[c][3 if key=='pnrrFunding' else 1] for c in codes)
            assert math.isclose(r['result']['value'],numerator/denominator*(1 if key=='pnrrFunding' else 100),rel_tol=0,abs_tol=1e-10)
        for selectors in [[dict(metric=key),dict(metric='population')],[dict(metric='population'),dict(metric=key)]]:
            rejected(e,dict(operation='correlation',selectors=selectors,axis='municipalities',method='pearson',purpose='descriptive'),'pnrr_pair_not_jointly_reviewed')
        for mutation in [lambda m:m['rows'][0].update(value=99),lambda m:m['meta'].update(year='2025'),
                         lambda m:m.update(sourceUrl='other'),lambda m:m['aggregate'].update(value=99),
                         lambda m:m['method'].update(formula='spent'),lambda m:m['rows'][0].update(series={'years':[2025],'values':[1]})]:
            g=QueryEngine(path,layer='effective');assert g.query(query(key))['status']=='computed'
            mutation(g._catalog['metrics'][key]);rejected(g,query(key),'pnrr_public_definition_or_values_changed')
    for mutation in [lambda s:s['records'][0].update(importo_finanziato_pnrr='99.00'),
                     lambda s:s['records'][0].update(fase_avanzamento_da_regis='5. conclusione'),
                     lambda s:s['records'][0].update(area='PNC'),lambda s:s.update(sourceSnapshotSha256='0'*64),
                     lambda s:s['records'].append(copy.deepcopy(s['records'][0])),lambda s:s['perTown'].clear()]:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
        mutation(g.files[a.PATH][0]);rejected(g,query(),'pnrr_frozen_input_changed')
    for field in ['funding','projects','concluded']:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
        g._catalog['pnrrDeepDive']['towns'][0][field]+=1
        rejected(g,query(),'pnrr_public_components_not_reconciled')
    g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
    g.files[a.PATH][1]['sha256']='0'*64;rejected(g,query(),'pnrr_frozen_input_changed')
    g=QueryEngine(path,layer='effective');g._catalog['metrics']['population']['rows'][0]['value']+=1
    rejected(g,query(),'pnrr_resident_denominator_changed')
    g=QueryEngine(path,layer='effective');g._catalog['towns'][0]['name']='Unknown'
    rejected(g,query(),'pnrr_municipal_identity_changed')
    with tempfile.TemporaryDirectory() as folder:
        g=QueryEngine(path,layer='effective');g.root=Path(folder)
        target=g.root/a.PATH;target.parent.mkdir(parents=True);target.write_text('{}')
        rejected(g,query(),'pnrr_frozen_input_changed')
    assert sum(v[0] for v in ANCHORS.values())==3668310764
    assert sum(v[1] for v in ANCHORS.values())==101 and sum(v[2] for v in ANCHORS.values())==78
    assert not math.isclose(sum(float(wanted('pnrrConcluded','total',c)) for c in ANCHORS)/7,78/101*100,abs_tol=1e-3)
    print('PNRR PASS: 49 fixed observations, 28 components, four pooled ratios, separate 101-record normalized replay, phase differences, pointers and hostile input/cache guards')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
