#!/usr/bin/env python3
"""Conservative linkage and complete canonical accessibility inventory checks."""
import argparse
from collections import Counter
from pathlib import Path

from audit_a7_accessibility import audit, path_pattern, structural_path
from semantic_query_engine import SUPPORTED
from a7_evidence_linkage import AcquisitionReferences, WitnessIndex, operands


def verify_linkage_guards():
    import base64
    import copy
    import gzip
    import hashlib
    import json
    import tempfile
    root = Path(__file__).resolve().parents[1]
    catalog = dict(metrics=dict(fixture=dict(rows=[dict(parts=[dict(value=17, numerator=17, denominator=100),
                                                              dict(value=17, numerator=17, denominator=100)],
                                                    totals={'2024': 17, '2025': 17})])))
    resolver = AcquisitionReferences(catalog, root)
    def reference(expression):
        return resolver.resolve(dict(metricId='fixture', state='ACQUIRED', evidence='structured:'+expression))
    def response(path, sha='a'*64, role='valuePointer', status='computed', kind='catalog_snapshot'):
        return dict(status=status, observations=[dict(value=17, evidence=[dict(kind=kind, sha256=sha, **{role:path})])])
    index = WitnessIndex('a'*64, catalog, root)
    compound = reference('rows.*.parts[0].numerator / rows.*.parts[0].denominator × 100')
    assert compound['status'] == 'resolved_paths' and len(compound['requirements']) == 2
    index.add(response('/metrics/fixture/rows/0/parts/0/numerator'), 'numerator')
    assert index.match(compound)['status'] == 'some_required_paths_witnessed'
    index.add(response('/metrics/fixture/rows/0/parts/0/denominator'), 'denominator')
    assert index.match(compound)['status'] == 'all_required_paths_witnessed'
    categories = reference('rows.*.parts.*.value')
    index.add(response('/metrics/fixture/rows/0/parts/0/value'), 'first_category')
    assert index.match(categories)['status'] == 'some_required_paths_witnessed'
    # Equal numbers, a different category/year, a bad hash or a definition
    # pointer must never prove the requested evidence path.
    for wrong in [response('/metrics/fixture/rows/0/parts/0/value',sha='b'*64),
                  response('/metrics/fixture/rows/0/parts/0/value',role='definitionPointer'),
                  response('/metrics/fixture/rows/0/parts/1/value'),
                  response('/metrics/fixture/rows/0/parts/0/value',status='not_computable'),
                  response('/metrics/fixture/rows/0/parts/0/absent')]:
        other = WitnessIndex('a'*64, catalog, root);other.add(wrong,'wrong')
        assert other.match(reference('rows.0.parts[0].value'))['status'] == 'no_path_witness_in_probe_scope'
    years = WitnessIndex('a'*64, catalog, root)
    years.add(response('/metrics/fixture/rows/0/totals/2025'),'year2025')
    assert years.match(reference('rows.0.totals.2024'))['status'] == 'no_path_witness_in_probe_scope'
    published = WitnessIndex('a'*64, catalog, root)
    published.add(response('/metrics/fixture/rows/0/parts/0/value',kind='published_benchmark'),'benchmark')
    assert published.match(reference('rows.0.parts.0.value'))['status'] == 'all_required_paths_witnessed'
    assert published.match(compound,inspected=False)['status'] == 'not_inspected'
    for invalid in ['rows.0.value arbitrary_text', 'rows.0.value /', 'sum(rows.*.parts.*.value', 'rows.0.value -> other']:
        assert operands(invalid) is None
    assert reference('rows.0.unknown')['status'] == 'unresolved_operand'
    assert resolver.resolve(dict(metricId='dependencyIndices',dimension='eta',state='ACQUIRED',
        evidence='structured:companion:parts_ratio_formula:ageDistribution:scale=100:7/7'))['status'] == 'formula_bridge_not_proven'
    same_path = response('/metrics/fixture/rows/0/parts/0/value')
    same_path['observations'][0]['period']='2025'
    years.add(same_path,'same_index_wrong_year')
    dated=reference('rows.0.parts.0.value');dated['requirements'][0]['period']='2024'
    assert years.match(dated)['status']=='no_path_witness_in_probe_scope'
    for key in ('population','populationDensity','municipalSurface'):
        catalog['metrics'][key]=dict(meta=dict(year=2026),rows=[dict(value=17)])
    bridge=resolver.resolve(dict(metricId='population',dimension='assoluto_normalizzato',state='ACQUIRED',
        evidence='structured:companion:normalized_companion_formula:populationDensity/municipalSurface:2026'))
    assert bridge['status']=='resolved_paths' and len(bridge['componentSelections'])==3
    assert index.match(bridge)['status']=='no_path_witness_in_probe_scope'
    catalog['metrics']['municipalSurface']['meta']['year']='hybrid geography reference'
    bridge=resolver.resolve(dict(metricId='population',dimension='assoluto_normalizzato',state='ACQUIRED',
        evidence='structured:companion:normalized_companion_formula:populationDensity/municipalSurface:2026'))
    assert bridge['status']=='resolved_paths' and bridge['componentSelections'][-1]['period'] is None
    catalog['metrics']['populationChange']=dict(meta=dict(year='2019–2026'),rows=[dict(value=17)])
    catalog['metrics']['population']['rows'][0]['series']=dict(years=[2019,2026],values=[18,17])
    change=resolver.resolve(dict(metricId='populationChange',dimension='numeratore_denominatore',state='ACQUIRED',
        evidence='structured:companion:series_change_formula:population:2019->2026:scale=100:7/7'))
    assert change['status']=='resolved_paths' and [c['period'] for c in change['componentSelections']]==['2019','2026']
    with tempfile.TemporaryDirectory() as temporary:
        folder=Path(temporary);(folder/'data').mkdir();payload=dict(records=[dict(value=1)])
        raw=json.dumps(payload).encode();packed=base64.b64encode(gzip.compress(raw,mtime=0))
        part=folder/'data/part.b64';part.write_bytes(packed)
        ev=dict(kind='reconstructed_source_snapshot',path='data/archive',sha256=hashlib.sha256(raw).hexdigest(),
                parts=[dict(path='data/part.b64',sha256=hashlib.sha256(packed).hexdigest())],valuePointer='/records/0/value')
        ref=dict(status='resolved_paths',requirements=[dict(namespace='storage:data',paths=['records/0/value'])])
        stored=WitnessIndex('a'*64,catalog,folder,{'data':payload})
        stored.add(dict(status='computed',observations=[dict(value=1,evidence=[ev])]),'storage')
        assert stored.match(ref)['status']=='all_required_paths_witnessed'
        typed=WitnessIndex('a'*64,catalog,folder,{'data':dict(records=[dict(value=True)])})
        assert typed.storage_namespace(ev) is None, 'boolean_payload_equated_with_numeric_payload'
        for field in ['sha256','part']:
            bad=copy.deepcopy(ev)
            if field=='part':bad['parts'][0]['sha256']='b'*64
            else:bad['sha256']='b'*64
            cached=WitnessIndex('a'*64,catalog,folder,{'data':payload})
            assert cached.storage_namespace(ev)=='storage:data'
            assert cached.storage_namespace(bad) is None, 'changed_part_reference_reused_cached_verification'
            stored=WitnessIndex('a'*64,catalog,folder,{'data':payload})
            stored.add(dict(status='computed',observations=[dict(value=1,evidence=[bad])]),'storage')
            assert stored.match(ref)['status']=='no_path_witness_in_probe_scope'


def verify(catalog):
    verify_linkage_guards()
    from audit_a7_accessibility import artifact_capabilities
    assert artifact_capabilities(None, '0'*64) == (set(), None)
    try:
        artifact_capabilities(Path(catalog).parent.parent, '0'*64)
    except ValueError as error:
        assert str(error) == 'interface_catalog_mismatch'
    else:
        raise AssertionError('interface_different_catalog_accepted')
    report = audit(catalog, Path(catalog).parent/'source-registry.json', site=Path(catalog).parent.parent)
    assert report['interfaceArtifact']['status'] == 'PASS'
    assert report['interfaceSummary']['prepared_native_defaults'] > 0
    assert all(o['artifactGeneralExplorer'] != 'prepared_native_defaults' for v in report['views'] for o in v['operations'] if o['operation'] not in ('observe','lookup','compare','series','benchmark_gap','weighted_ratio'))
    import json
    descriptor = json.loads((Path(catalog).parent.parent/'explorer-preview.json').read_text())
    benchmark_views = [o for v in report['views'] for o in v['operations']
                       if o['operation'] == 'benchmark_gap' and o['artifactGeneralExplorer'] == 'prepared_native_defaults']
    assert bool(benchmark_views) == (descriptor.get('interfaceVersion', 1) >= 2), 'benchmark_ui_scope_not_attested'
    aggregation_views = [o for v in report['views'] for o in v['operations']
                         if o['operation'] == 'weighted_ratio' and o['artifactGeneralExplorer'] == 'prepared_native_defaults']
    assert bool(aggregation_views) == (descriptor.get('interfaceVersion', 1) >= 3), 'aggregation_ui_scope_not_attested'
    assert all(o['requestScope'] == 'all_seven_towns_native_weighted_ratio' for o in aggregation_views)
    rows = report['acquisition']
    assert len(rows) == report['acquisitionSummary']['pairCount']
    assert len({(r['metricId'], r['dimension']) for r in rows}) == len(rows)
    assert len({v['metric'] for v in report['views']}) == report['acquisitionSummary']['publicMetricCount']
    for view in report['views']:
        assert {r['operation'] for r in view['operations']} == set(SUPPORTED)
        assert all(r['publicGeneralExplorer'] == 'publication_not_inspected' for r in view['operations'])
        # No runtime supplied: no declaration masquerades as materialization.
        assert all(r['static'] in ('not_inspected', 'not_admitted') for r in view['operations'])
    assert all(not r['accessEvidencePaths'] for r in rows)
    assert all(r['linkage'] == ('acquired_access_not_proven' if r['state'] == 'ACQUIRED' else 'not_acquired') for r in rows)
    assert all(r['staticAccess']['status'] == 'not_inspected' for r in rows)
    assert sum(report['workbenchAccessSummary'].values()) == len(rows)
    assert report['nativeProbes'] and not report['staticProbes']
    for row in rows:
        if row['workbenchAccess']['status'] == 'all_required_paths_witnessed':
            assert row['state'] == 'ACQUIRED' and row['acquisitionReference']['status'] == 'resolved_paths'
            assert row['workbenchAccess']['matched'] and not row['workbenchAccess']['unmatched']
        for match in row['workbenchAccess']['matched']:
            assert report['nativeProbes'][match['proof']]['status'] == 'computed'
    assert structural_path(dict(evidence='structured:rows.0.sexDimension')) == 'rows/*/sexDimension'
    assert structural_path(dict(evidence='structured:rows.0.parts.15.series')) == 'rows/*/parts/15/series'
    assert path_pattern('/metrics/m/rows/0/parts/1/value') == path_pattern('/metrics/m/rows/6/parts/1/value')
    assert path_pattern('/metrics/m/rows/0/parts/1/value') != path_pattern('/metrics/m/rows/0/parts/2/value')
    assert path_pattern('/metrics/m/rows/0/totals/2024') != path_pattern('/metrics/m/rows/0/totals/2025')
    for evidence in ('structured:companion:history:x:rows.0.series', 'structured:rows.*.a / rows.*.b × 100', 'structured:route:page.html:data', 'text mentioning sex'):
        assert structural_path(dict(evidence=evidence)) is None
    totals = Counter()
    for counts in report['independentExpectations'].values():
        totals.update(counts)
    # Counts derived from original expectations, not hardcoded release totals.
    from semantic_question_suite import QUESTIONS
    import json
    assert sum(totals.values()) == len(json.loads(QUESTIONS.read_text())['questions'])
    assert all(op in report['independentExpectations'] for op in ('rank', 'benchmark_gap', 'absolute_change', 'relative_change', 'weighted_ratio', 'correlation'))
    print('A7 accessibility: A3 pairs, A6 view/operation inventory and independent workbench expectations PASS')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--catalog', type=Path, required=True)
    verify(p.parse_args().catalog)
