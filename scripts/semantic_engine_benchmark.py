#!/usr/bin/env python3
"""Reproducible workloads; environment-dependent timings, not a quality score."""
import argparse
import gc
import json
import os
from pathlib import Path
import platform
import statistics
import time
import tracemalloc

from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import run_suite


def percentile(values, probability):
    ordered=sorted(values);position=(len(ordered)-1)*probability
    low=int(position);high=min(low+1,len(ordered)-1)
    return ordered[low]+(ordered[high]-ordered[low])*(position-low)


def summarize(values):
    return dict(samples=len(values),minMs=min(values),medianMs=statistics.median(values),
                p95Ms=percentile(values,.95),maxMs=max(values))


def benchmark(catalog_path, *, rounds=30, initialization_rounds=5):
    if rounds<2 or initialization_rounds<2:raise ValueError('at_least_two_samples_required')
    make=lambda:QueryEngine(catalog_path,layer='effective')
    engine=make();suite=run_suite(engine)
    if suite['status']!='PASS':raise ValueError('correctness_suite_failed_before_benchmark')
    ids=['agriculture_profiles_female_pooled','agriculture_profiles_organic_series','agriculture_profiles_organic_pooling_refused','climate_temperature_current','climate_tmin_annual_trend','climate_precipitation_pooling_refused','pab_pabProgrammedInterventions','pab_pabInterventionsCompleted_share_pooled','pab_approved_operational_refused','remediation_total','remediation_pooled','remediation_history_refused','extractive_sites_active','extractive_prc_pooled','extractive_production_history','maritime_tourist_pooled','maritime_mean_due_pooled','maritime_median_weighting_refused','bathing_quality_pooled','bathing_samples_pooled','bathing_blue_history','coast_protection_pooled','coast_dynamics_erosion_pooled','coast_mixed_universe_refused','ifc_municipalFragility_series','ifc_access_tuscany_gap','ifc_lowProductivityEmployment_relative_change_refused','hazard_flood_pooled','hazard_landslide_pooled_area','hazard_mixed_maps_refused','territory_protected_pooled','territory_network_pooled','territory_mixed_reference_refused','soil_stock_pooled','soil_ucs_pooled','soil_mixed_edition_refused','geography_density_pooled','geography_forest_pooled','geography_mixed_reference','population_current','female_weighted','ars_gap','aligned_association','mismatched_association','ars_hypertension_age','ars_mortality_window_gap','business_frame_industry_weighted','business_endpoint_refused','census_young_employment','census_diploma_trend_refused','finance_cash_weighted','finance_benchmark_refused','distinct_debt_weighted','distinct_debt_osl_refused','demography_dependency','school_class_size','demography_aligned_events','school_calendar_year_refused','commuting_pooled_selfContainment','commuting_pooled_commuterBalanceRate','commuting_hybrid_pair_refused','environment_water_pooled','environment_rd_weighting_refused','environment_cost_gap','agriculture_pooled_size','agriculture_pooled_irrigated','agriculture_mixed_scope_refused']
    cases={r['id']:r for r in suite['results']};construction=[]
    for _ in range(initialization_rounds):
        start=time.perf_counter_ns();sample=make();construction.append((time.perf_counter_ns()-start)/1e6)
        del sample
    measurements=[]
    for identity in ids:
        case=cases[identity];query=case['actual']['query'];expected=case['expected']['status']
        first=[]
        for _ in range(initialization_rounds):
            fresh=make();start=time.perf_counter_ns();result=fresh.query(query)
            first.append((time.perf_counter_ns()-start)/1e6)
            if result['status']!=expected:raise ValueError('first_query_correctness_changed')
        engine.query(query);gc.collect();warm=[]
        for _ in range(rounds):
            start=time.perf_counter_ns();result=engine.query(query);warm.append((time.perf_counter_ns()-start)/1e6)
            if result['status']!=expected:raise ValueError('warm_query_correctness_changed')
        measurements.append(dict(id=identity,query=query,expectedStatus=expected,
            firstQueryFreshEngine=summarize(first),warmQuery=summarize(warm)))
    # Allocation tracing is deliberately separate from the latency samples.
    gc.collect();tracemalloc.start();memory_engine=make()
    for identity in ids:memory_engine.query(cases[identity]['actual']['query'])
    retained,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    try:cpu_quota=Path('/sys/fs/cgroup/cpu.max').read_text().strip()
    except OSError:cpu_quota='not_available'
    return dict(schemaVersion=1,catalogSha256=engine.catalog_hash,engineSha256=engine.module_hash,
        adapterImplementationHashes={k:v for k,v in suite['results'][0]['actual'].items() if k.endswith('AdapterSha256') or k=='adapterImplementationSha256'},
        questionManifestSha256=suite['manifestSha256'],correctnessSuite=suite['summary'],
        environment=dict(python=platform.python_version(),implementation=platform.python_implementation(),
            platform=platform.platform(),machine=platform.machine(),visibleCpuCount=os.cpu_count(),
            cpuQuota=cpu_quota,clock='perf_counter_ns',clockResolutionSeconds=time.get_clock_info('perf_counter').resolution),
        engineConstruction=summarize(construction),workloads=measurements,
        pythonAllocationBytes=dict(retained=retained,peak=peak,scope=f'one fresh engine plus {len(ids)} representative queries; tracemalloc, excludes native allocations'),
        notes=['Local sequential microbenchmark; not a production concurrency or load test',
            'Fresh engine means no application snapshot cache; operating-system filesystem cache is uncontrolled',
            'Warm query includes normal provenance/output construction, not network acquisition',
            'p95 uses linear interpolation at (n-1)*0.95; small samples are descriptive',
            'No hardware-independent latency threshold or completeness claim; compare runs in equivalent environments'])


def markdown(report):
    env=report['environment'];lines=['# A6 — baseline delle prestazioni','',
        f"Catalogo `{report['catalogSha256']}`; motore `{report['engineSha256']}`; domande `{report['questionManifestSha256']}`.",'',
        'Hash degli adapter: '+json.dumps(report.get('adapterImplementationHashes',{}),sort_keys=True)+'.','',
        f"Ambiente: Python {env['python']} {env['implementation']}, {env['platform']}, {env['machine']}; CPU visibili {env['visibleCpuCount']}, quota cgroup `{env['cpuQuota']}`.",'',
        'Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.','',
        '| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |','|---|---|---|---|---|']
    def row(label,s):return f"| {label} | {s['samples']} | {s['medianMs']:.3f} | {s['p95Ms']:.3f} | {s['maxMs']:.3f} |"
    lines.append(row('Costruzione/validazione motore',report['engineConstruction']))
    for w in report['workloads']:
        lines.append(row(w['id']+' · prima query, nuova istanza',w['firstQueryFreshEngine']))
        lines.append(row(w['id']+' · query con cache applicativa',w['warmQuery']))
    m=report['pythonAllocationBytes'];lines+=['',f"Allocazioni Python: picco {m['peak']/1024/1024:.3f} MiB; mantenute {m['retained']/1024/1024:.3f} MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.",'',
        'I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.','']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,default=ROOT/'dist/data/site-data.json')
    p.add_argument('--rounds',type=int,default=30);p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
    report=benchmark(args.catalog,rounds=args.rounds);args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'performance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (args.output_dir/'performance.md').write_text(markdown(report));print(report['engineConstruction'])


if __name__=='__main__':main()
