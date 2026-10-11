"""Frozen 2025 standardized municipal tax scenarios; never a personal tax calculator."""
import math
from decimal import Decimal, ROUND_HALF_UP

from semantic_operations import finite
from semantic_query_library_adapters import TOWNS, fingerprint

TARI, IMU, IRPEF = KEYS = ('tariStandardHousehold', 'municipalImuStandard', 'municipalIrpef')
COSTS = 'data/source-snapshots/costi-fiscalita-validated-2026-08.json'
RULES = 'data/source-snapshots/costi-fiscalita-redditi-draft-2026-08.json'
SCENARIOS = (20000, 30000, 50000)
PATHS = {TARI:COSTS, IMU:COSTS, IRPEF:RULES}
URLS = {TARI:'https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_at/', IMU:'https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_imu/', IRPEF:'https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/'}
UNITS = {TARI:'currency2', IMU:'currency', IRPEF:'currency2'}
HASHES = {'data/source-snapshots/costi-fiscalita-validated-2026-08.json': ('e14f1a1c9fd4a0f636eff84aa880079e370ccee63cd09d772d0288f682132dac', '2aecadf3c93bdcffc699bcaff7de2295ebec6d521f89ebd3a787be5d3c6e329d'), 'data/source-snapshots/costi-fiscalita-redditi-draft-2026-08.json': ('b1a8ccfb23e106182804e5475587ec7f1380c70e88de277e3382515a39a3af03', 'adb8d7d27c000f10202ae24227cf406bf909ba65b1433c0b3a24ae1ce6649b6d')}
FORMULAS = {'tariStandardHousehold': '100 m² × quota fissa + quota variabile per 3 componenti; TEFA 5%; + 7,60 € di componenti perequative ARERA 2025.', 'municipalImuStandard': '100.000 € × aliquota IMU 2025 della categoria «Altri fabbricati».', 'municipalIrpef': "Per ciascuno scenario: se il reddito imponibile non supera la soglia di esenzione, imposta = 0; altrimenti si applicano all'intero imponibile l'aliquota unica o gli scaglioni progressivi pubblicati dal MEF."}
NOTES = ['municipal_tax_standard_scenarios_not_personal_bill_or_revenue',
         'municipal_tax_arithmetic_mean_each_municipality_equal_weight',
         'municipal_tax_single_2025_snapshot_not_current_tax_advice',
         'municipal_tax_not_service_quality_or_household_burden']


def money(value):
    return float(Decimal(str(value)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))


def irpef_amount(rule, income):
    # Only the three frozen scenarios are exposed; missing exemption is not a general rule.
    if income not in SCENARIOS: raise ValueError('municipal_tax_unreviewed_income_scenario')
    if rule['exemption'] is not None and income <= rule['exemption']: return 0.0
    if rule['scheme'] == 'flat': return money(Decimal(income)*Decimal(str(rule['ratePercent']))/100)
    lower = 0; amount = Decimal(0)
    for bracket in rule['brackets']:
        upper = bracket['upTo']
        width = max(0, min(income, upper if upper is not None else income)-lower)
        amount += Decimal(width)*Decimal(str(bracket['ratePercent']))/100
        if upper is None or income <= upper: break
        lower = upper
    return money(amount)


def equal(actual, expected):
    if not finite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9):
        raise ValueError('municipal_tax_public_native_mismatch')


def frozen(engine, path):
    value, ref = engine.file(path)
    if ref.get('path') != path or (ref.get('sha256'),fingerprint(value)) != HASHES[path]:
        raise ValueError('municipal_tax_frozen_input_changed')
    return value, ref


def dimensions(key):
    if key == IMU: return ['total','ratePercent']
    if key == IRPEF: return ['total']+['income:'+str(n) for n in SCENARIOS]+['effectiveRate:20000']
    return ['total']


def scopes(key, dim): return []
def operations(key, dim): return ['compare','rank']


def selection_guard(key, dim, op):
    if op in ('series','absolute_change','relative_change','percentage_points','trend'):
        raise ValueError('municipal_tax_single_snapshot_no_history')
    if op == 'weighted_ratio': raise ValueError('municipal_tax_scenarios_not_additive_population')
    if op == 'benchmark_gap': raise ValueError('municipal_tax_geographic_benchmark_not_frozen')
    if op == 'anomaly': raise ValueError('municipal_tax_peer_anomaly_not_reviewed')
    if op == 'correlation': raise ValueError('municipal_tax_pair_not_jointly_reviewed')


def context(metric, key, dim):
    meta = metric['meta']
    if (dim not in dimensions(key) or meta.get('key') != key or meta.get('year') != '2025'
            or meta.get('unit') != UNITS[key] or meta.get('polarity') != 'neutral'
            or metric.get('sourceUrl') != URLS[key] or metric.get('method',{}).get('formula') != FORMULAS[key]
            or meta.get('benchmark') is not None):
        raise ValueError('municipal_tax_definition_changed')
    if dim == 'effectiveRate:20000' and not all(isinstance(r.get('municipalIrpefScaleCompanion'),dict) for r in metric['rows']):
        raise ValueError('municipal_tax_effective_rate_companion_not_materialized')
    definition = ('resident domestic user, 3 people / 100 square metres, no personal concessions; TEFA 5% and ARERA 7.60 euro included' if key == TARI else
                  'second home A/2, other buildings rate, identical IMU taxable base 100000 euro, not market price or cadastral rent' if key == IMU else
                  'municipal IRPEF only, same theoretical taxable individual income; total aliases 20000 euro, state/regional IRPEF excluded')
    unit = 'percent' if dim in ('ratePercent','effectiveRate:20000') else UNITS[key]
    return dict(unit=unit,population='one identical theoretical tax scenario per municipality',definition=definition,
                method=FORMULAS[key]+('; '+dim if dim != 'total' else ''),frequency='annual_snapshot',periodBasis='2025 tax rules and fixed scenarios only',
                nativeComponentsAvailable=False,adapter='municipal-tax/'+key+'/'+dim+'/v1')


def validated(engine, key):
    metric = engine._catalog['metrics'][key]; context(metric,key,'total')
    snap, ref = frozen(engine,PATHS[key]); raw = snap['municipalIrpef' if key == IRPEF else 'tari' if key == TARI else 'imu']
    rows = metric['rows']
    if (len(rows) != 7 or {r.get('code') for r in rows} != set(TOWNS)
            or {t['code']:t['name'] for t in engine._catalog['towns']} != TOWNS
            or set(raw['towns']) != set(TOWNS.values()) or raw['year'] != 2025):
        raise ValueError('municipal_tax_identity_or_period_changed')
    if key == IRPEF and (raw['scenarios'] != list(SCENARIOS) or metric['meta'].get('compositeType') != 'securityMeasures'):
        raise ValueError('municipal_tax_scenarios_changed')
    values = []; scenario_values = [[],[],[]]
    for row in rows:
        code = row['code']; name = TOWNS[code]; native = raw['towns'][name]
        if (row.get('town') != name or row.get('slug') != '-'.join(name.lower().split())
                or row.get('notApplicable') or row.get('dataUnavailable') or row.get('normalized') is not None
                or row.get('ratioComponents') is not None):
            raise ValueError('municipal_tax_identity_or_components_changed')
        if key == TARI:
            base = native.get('officialBase100sqm3people')
            if base is None: base = money(Decimal(str(native['fixedPerSqm']))*100+Decimal(str(native['variablePerYear'])))
            equal(native['baseCharge'],base); equal(native['tefa5Percent'],money(Decimal(str(base))*Decimal('.05')))
            value = money(Decimal(str(base))+Decimal(str(native['tefa5Percent']))+Decimal(str(native['equalization2025'])))
            equal(native['annualCost'],value)
            if row.get('tariffDetail') != native: raise ValueError('municipal_tax_tariff_detail_changed')
        elif key == IMU:
            value = money(Decimal(100000)*Decimal(str(native['ratePercent']))/100); equal(native['annualTax'],value); equal(row.get('ratePercent'),native['ratePercent'])
        else:
            if native['code'] != code: raise ValueError('municipal_tax_identity_or_period_changed')
            amounts = [irpef_amount(native,n) for n in SCENARIOS]; value = amounts[0]
            expected = [dict(label=f'Reddito imponibile {n:,.0f} €'.replace(',','.'),selectorLabel=f'{n:,.0f} €'.replace(',','.'),value=a,unit='currency2') for n,a in zip(SCENARIOS,amounts)]
            if any(not finite(p.get('value')) for p in row.get('parts',[])) or any(not finite(v) for s in (row.get('componentSeries') or {}).values() for v in s.get('values',[])) or row.get('parts') != expected or row.get('componentSeries') != {p['selectorLabel']:dict(years=[2025],values=[p['value']]) for p in expected}:
                raise ValueError('municipal_tax_scenarios_changed')
            for i,(n,a) in enumerate(zip(SCENARIOS,amounts)):
                equal(native['amounts'][str(n)],a); scenario_values[i].append(a)
            if 'municipalIrpefScaleCompanion' in row:
                companion = row.get('municipalIrpefScaleCompanion') or {}
                if (companion.get('year') != 2025 or companion.get('sourceSnapshot') != RULES or companion.get('normalizedUnit') != 'percent'):
                    raise ValueError('municipal_tax_companion_changed')
                for field,wanted in [('scenarioIncome',20000),('absolute',value),('normalized',value/20000*100)]: equal(companion.get(field),wanted)
        equal(row.get('value'),value); equal(row.get('benchmarkValue'),value);values.append(value)
        history = row.get('series')
        if history != dict(years=['2025'] if key == IMU else [2025],values=[value]) or not finite(history['values'][0]):
            raise ValueError('municipal_tax_history_changed')
    aggregate = metric.get('aggregate') or {};equal(aggregate.get('value'),math.fsum(values)/7)
    if aggregate.get('label') != 'Media semplice dei 7 comuni' or metric.get('normalizedAggregate') is not None:
        raise ValueError('municipal_tax_summary_changed')
    if key == IRPEF:
        parts = aggregate.get('parts') or []
        if len(parts) != 3: raise ValueError('municipal_tax_summary_changed')
        for i,p in enumerate(parts):
            if {k:p.get(k) for k in ('label','selectorLabel','unit')} != {k:expected[i][k] for k in ('label','selectorLabel','unit')}:
                raise ValueError('municipal_tax_summary_changed')
            equal(p.get('value'),math.fsum(scenario_values[i])/7)
    return raw, ref


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric,key,dim)
    raw,ref = validated(engine,key); row=metric['rows'][index]; native=raw['towns'][row['town']]
    if period != '2025': raise ValueError('municipal_tax_period_not_frozen')
    field = 'value'; record = '/'+('municipalIrpef' if key == IRPEF else 'tari' if key == TARI else 'imu')+'/towns/'+row['town']
    value = row['value']; notes=NOTES[:]
    if key == IMU:
        field = 'ratePercent' if dim == 'ratePercent' else 'value';value=row[field]
        record += '/ratePercent' if dim == 'ratePercent' else '/annualTax'
        extra = dict(standardTaxableBaseEuro=100000,ratePercent=native['ratePercent'],sourcePage=native['sourcePage'])
    elif key == TARI:
        record += '/annualCost';extra=dict(tariffComponents=native,standardPersons=3,standardSquareMetres=100,rounding='base and TEFA rounded separately to cents; ARERA added')
        notes += ['municipal_tax_tari_stazzema_official_base_not_reconstructed_fixed_variable','municipal_tax_source_normalized_snapshot_not_raw_document_replay']
    else:
        n = 20000 if dim in ('total','effectiveRate:20000') else int(dim.split(':')[1]);i=SCENARIOS.index(n)
        if dim == 'effectiveRate:20000': field='municipalIrpefScaleCompanion/normalized';value=row['municipalIrpefScaleCompanion']['normalized']
        elif dim != 'total': field=f'parts/{i}/value';value=row['parts'][i]['value']
        record += '/amounts/'+str(n);extra=dict(scenarioIncomeEuro=n,nativeAmountEuro=native['amounts'][str(n)],taxScheme=native,transformation='amount / 20000 × 100' if dim == 'effectiveRate:20000' else 'frozen municipal scenario amount')
        notes += ['municipal_tax_irpef_total_alias_20000','municipal_tax_irpef_effective_rate_not_marginal_rate','municipal_tax_missing_exemption_not_general_no_exemption_claim','municipal_tax_seravezza_municipal_confirmation_not_mef_row','municipal_tax_source_normalized_snapshot_not_raw_document_replay']
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/rows/{index}/{field}'),dict(ref,kind='source_snapshot',recordPointer=record,**extra)]
    return dict(ctx,metric=key,dimension=dim,geography=row['code'],period=period,value=value,source=URLS[key],evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=False,missingReason=None),notes
