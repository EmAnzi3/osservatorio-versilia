#!/usr/bin/env python3
"""A6.4 first deterministic query engine over the validated canonical catalog."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
from statistics import median
from pathlib import Path
from urllib.parse import urlparse

from semantic_model_contract import validate_semantic_model_contract
from semantic_operations import assess, coverage_matrix, finite
from semantic_query_adapters import CENSUS, census_context, census_observation, benchmark_observation, AGE_BANDS, age_context, age_observation
import semantic_query_territorial_adapters as territorial
import semantic_query_ars_adapters as ars
import semantic_query_business_adapters as business
import semantic_query_census_adapters as census
import semantic_query_finance_adapters as finance
import semantic_query_distinct_finance_adapters as distinct
import semantic_query_demography_school_adapters as demography
import semantic_query_commuting_adapters as commuting
import semantic_query_environment_adapters as environment
import semantic_query_agriculture_adapters as agriculture
import semantic_query_geography_adapters as geography
import semantic_query_soil_adapters as soil
import semantic_query_territory_adapters as territory
import semantic_query_hazard_adapters as hazard
import semantic_query_fragility_adapters as fragility
import semantic_query_coast_adapters as coast
import semantic_query_bathing_adapters as bathing
import semantic_query_maritime_adapters as maritime
import semantic_query_extractive_adapters as extractive
import semantic_query_remediation_adapters as remediation
import semantic_query_pab_adapters as pab
import semantic_query_climate_adapters as climate
import semantic_query_agriculture_profile_adapters as profiles
import semantic_query_classification_adapters as classification

ROOT = Path(__file__).resolve().parents[1]
VERSION = '27'
SUPPORTED = ('compare', 'series', 'absolute_change', 'relative_change', 'rank', 'trend', 'correlation', 'percentage_points', 'weighted_ratio', 'benchmark_gap', 'anomaly')
TEMPORAL = ('series', 'absolute_change', 'relative_change', 'trend', 'percentage_points')
SNAPSHOT = 'data/source-snapshots/istat-demography-lotto-a-2026-08.json'


def digest(body):
    return hashlib.sha256(body).hexdigest()


def annual(period):
    token = str(period)
    if not re.fullmatch(r'[0-9]{4}', token):
        raise ValueError(f'unsupported_annual_period:{token}')
    return token


def period_token(key, period):
    if key in climate.KEYS:return climate.token(key,period)
    if key in pab.KEYS:return pab.token(key,period)
    if key in remediation.KEYS:return remediation.token(key,period)
    if key in extractive.KEYS:return extractive.token(key,period)
    if key in maritime.KEYS:return maritime.token(key,period)
    if key in bathing.KEYS:return bathing.token(key,period)
    if key in coast.KEYS:return coast.token(key,period)
    if key in fragility.KEYS:return fragility.token(key,period)
    if key in hazard.KEYS:return hazard.token(key,period)
    if key in territory.KEYS:return territory.token(key,period)
    if key in soil.KEYS:return soil.token(key,period)
    if key in geography.KEYS:return geography.token(key,period)
    if key in demography.KEYS:return demography.token(key,period)
    if key in business.KEYS:return business.token(key,period)
    if key in ars.KEYS:return ars.token(period)
    if key=='earlyChildhoodPotentialCapacityRate':
        token=str(period)
        if not re.fullmatch(r'[0-9]{4}/[0-9]{2}',token):
            raise ValueError('educational_year_token_required')
        return token
    return annual(period)


def dimensions(key):
    if key in classification.KEYS:return classification.dimensions(key)
    if key in profiles.KEYS:return profiles.dimensions(key)
    if key in climate.KEYS:return climate.dimensions(key)
    if key in pab.KEYS:return pab.dimensions(key)
    if key in remediation.KEYS:return remediation.dimensions(key)
    if key in extractive.KEYS:return extractive.dimensions(key)
    if key in maritime.KEYS:return maritime.dimensions(key)
    if key in bathing.KEYS:return bathing.dimensions(key)
    if key in coast.KEYS:return coast.dimensions(key)
    if key in fragility.KEYS:return fragility.dimensions(key)
    if key in hazard.KEYS:return hazard.dimensions(key)
    if key in territory.KEYS:return territory.dimensions(key)
    if key in soil.KEYS:return soil.dimensions(key)
    if key in geography.KEYS:return geography.dimensions(key)
    if key in agriculture.KEYS:return agriculture.dimensions(key)
    if key in demography.KEYS:return demography.dimensions(key)
    if key in distinct.KEYS:return distinct.dimensions(key)
    if key in census.KEYS:return census.dimensions(key)
    if key in business.KEYS:return business.dimensions(key)
    if key in ars.KEYS:return ars.dimensions(key)
    if key=='ageDistribution':return list(AGE_BANDS)
    if key=='population':return ['total','sex:men','sex:women']
    if key=='elderlyHomeCare':return list(territorial.SEX)
    return ['total']


def operations(key, dimension, unit):
    if key in classification.KEYS:return classification.operations(key,dimension)
    if key in profiles.KEYS:return profiles.operations(key,dimension)
    if key in climate.KEYS:return climate.operations(key,dimension)
    if key in pab.KEYS:return pab.operations(key,dimension)
    if key in remediation.KEYS:return remediation.operations(key,dimension)
    if key in extractive.KEYS:return extractive.operations(key,dimension)
    if key in maritime.KEYS:return maritime.operations(key,dimension)
    if key in bathing.KEYS:return bathing.operations(key,dimension)
    if key in coast.KEYS:return coast.operations(key,dimension)
    if key in fragility.KEYS:return fragility.operations(key)
    if key in hazard.KEYS:return [o for o in SUPPORTED if (o not in TEMPORAL or o=='series' and dimension==hazard.HISTORY) and o!='benchmark_gap' and (o!='weighted_ratio' or hazard.weighted(key,dimension))]
    if key in territory.KEYS:return [o for o in SUPPORTED if o not in TEMPORAL and o!='benchmark_gap' and (o!='weighted_ratio' or territory.weighted(key,dimension))]
    if key in soil.KEYS:return [o for o in SUPPORTED if (o not in TEMPORAL or o=='series') and (o!='weighted_ratio' or soil.weighted(key,dimension)) and (o!='benchmark_gap' or soil.scopes(key,dimension))]
    if key in geography.KEYS:return [o for o in SUPPORTED if o not in TEMPORAL and (o!='weighted_ratio' or geography.weighted(key,dimension)) and (o!='benchmark_gap' or geography.scopes(key,dimension))]
    if key in agriculture.KEYS:return [o for o in SUPPORTED if o not in TEMPORAL and (o!='weighted_ratio' or agriculture.weighted(key,dimension)) and (o!='benchmark_gap' or agriculture.scopes(key,dimension)) and o!='percentage_points']
    if key in environment.KEYS:
        return [o for o in SUPPORTED if (o!='weighted_ratio' or key in environment.RATIOS) and (o!='percentage_points' or unit=='percent') and not (key in environment.WASTE and o in TEMPORAL and o!='series')]
    if key in commuting.KEYS:
        return [o for o in SUPPORTED if o not in TEMPORAL and (o not in ('weighted_ratio','benchmark_gap') or key in commuting.RATIOS)]
    if key in demography.KEYS:
        current_only=key in (demography.SITES,*demography.STUDENTS,*demography.BUILDINGS) or '|sex:' in dimension or dimension.startswith('sex:')
        return [o for o in SUPPORTED if (o!='benchmark_gap' or demography.benchmark_scopes(key,dimension)) and (o!='weighted_ratio' or demography.weighted(key,dimension)) and (o!='percentage_points' or unit=='percent') and not (current_only and o in TEMPORAL) and not (key==demography.CHANGE and o=='trend')]
    if key in distinct.KEYS:
        return [o for o in SUPPORTED if o!='benchmark_gap' and (o!='weighted_ratio' or distinct.weighted(key,dimension)) and (o!='percentage_points' or unit=='percent') and not (key==distinct.WORKS and o in TEMPORAL) and not (key==distinct.FISCAL and o in TEMPORAL and o!='series') and not (key==distinct.SECURITY and o=='trend')]
    if key in finance.KEYS:
        return [o for o in SUPPORTED if o!='benchmark_gap' and (o!='weighted_ratio' or key in finance.RATIOS) and (o!='percentage_points' or unit=='percent')]
    if key in census.KEYS:
        return [o for o in SUPPORTED if (o!='weighted_ratio' or key in census.RATIOS) and (o!='benchmark_gap' or census.benchmark_scopes(key,dimension)) and (o!='percentage_points' or unit=='percent') and not (key=='householdSize' and o in TEMPORAL) and not (key=='diplomaPlus' and dimension in ('total','age:25-64|sex:total') and o=='trend')]
    if key in business.KEYS:
        return [o for o in SUPPORTED if (o!='weighted_ratio' or key in business.RATIOS) and (o!='benchmark_gap' or business.benchmark_scopes(key,dimension)) and (o!='percentage_points' or unit=='percent') and not (key=='microUnits' and o in TEMPORAL) and not (key in business.CHANGES and o=='trend')]
    if key in ars.KEYS:
        rolling='-' in ars._SPECS[key]['period']
        historical=key=='lifeExpectancy' or dimension=='total'
        return [o for o in SUPPORTED if o not in ('weighted_ratio','percentage_points') and (historical or o not in TEMPORAL) and not (rolling and o=='trend')]
    current_only=key=='ageDistribution' or key in territorial.CURRENT_ONLY or (key=='population' and dimension!='total')
    return [o for o in SUPPORTED if
        (o!='weighted_ratio' or key in CENSUS or key=='ageDistribution' or key in territorial.RATIOS) and
        (o!='benchmark_gap' or key in CENSUS or key=='income' or key=='ageDistribution' or key in territorial.RATIOS or key=='elderlyHomeCare') and
        (o!='percentage_points' or unit=='percent') and (not current_only or o not in TEMPORAL)]


def mean(values):
    return math.fsum(values) / len(values)


def ranks(values):
    """Ascending average ranks, including ties, for Spearman."""
    ordered = sorted(range(len(values)), key=lambda i: values[i])
    result = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and values[ordered[end]] == values[ordered[start]]:
            end += 1
        rank = (start + 1 + end) / 2
        for i in ordered[start:end]:
            result[i] = rank
        start = end
    return result


def coefficient(x, y, method):
    if method == 'spearman':
        x, y = ranks(x), ranks(y)
    # Scaling keeps finite magnitudes from overflowing in squared deviations.
    sx, sy = max(abs(v) for v in x), max(abs(v) for v in y)
    if sx == 0 or sy == 0:
        return None
    x, y = [v / sx for v in x], [v / sy for v in y]
    mx, my = mean(x), mean(y)
    dx, dy = [v - mx for v in x], [v - my for v in y]
    denominator = math.sqrt(math.fsum(v*v for v in dx) * math.fsum(v*v for v in dy))
    if denominator == 0:
        return None
    return max(-1.0, min(1.0, math.fsum(a*b for a, b in zip(dx, dy)) / denominator))


def calculate(operation, observations, policy):
    """Only called after the shared A6.2–3 eligibility gate."""
    usable = [o for o in observations if finite(o.get('value')) and not o.get('notApplicable') and not o.get('dataUnavailable')]
    values = [o['value'] for o in usable]
    if operation in ('compare', 'series'):
        return {'observations': usable}
    if operation == 'rank':
        ordered = sorted(usable, key=lambda o: (-o['value'], o['geography']))
        value_rank = {}
        for i, o in enumerate(ordered, 1):
            value_rank.setdefault(o['value'], i)
        return {'ranking': [{'geography': o['geography'], 'value': o['value'], 'rank': value_rank[o['value']]} for o in ordered], 'direction':'descending', 'ties':'competition'}
    if operation in ('absolute_change', 'relative_change', 'percentage_points'):
        delta = values[1] - values[0]
        return {'value': delta / values[0] * 100 if operation == 'relative_change' else delta,
                'unit': 'percent_change' if operation == 'relative_change' else 'percentage_points' if usable[0]['unit']=='percent' else usable[0]['unit'],
                'startPeriod':usable[0]['period'], 'endPeriod':usable[1]['period']}
    if operation == 'weighted_ratio':
        numerator = math.fsum(o['numerator'] for o in usable)
        denominator = math.fsum(o['denominator'] for o in usable)
        return {'value':numerator / denominator * usable[0]['scale'], 'unit':usable[0]['unit'],
                'numerator':numerator, 'denominator':denominator, 'scale':usable[0]['scale'],
                'geographies':[o['geography'] for o in usable], 'period':usable[0]['period'],
                'aggregation':'ratio of sums; not mean of municipal ratios',
                **{k:usable[0][k] for k in ('numeratorPeriod','denominatorPeriod') if k in usable[0]}}
    if operation == 'benchmark_gap':
        municipal,benchmark = usable
        return {'value':municipal['value']-benchmark['value'],
                'unit':'percentage_points' if municipal['unit']=='percent' else municipal['unit'],
                'municipalValue':municipal['value'], 'benchmarkValue':benchmark['value'],
                'geography':municipal['geography'], 'benchmarkScope':benchmark['geography'],
                'period':municipal['period'], 'direction':'municipal minus benchmark',
                **{k:municipal[k] for k in ('numeratorPeriod','denominatorPeriod') if k in municipal}}
    if operation == 'anomaly':
        ordered=sorted(values)
        def quantile(p):
            position=(len(ordered)-1)*p
            lo=math.floor(position);hi=math.ceil(position)
            return ordered[lo]*(hi-position)+ordered[hi]*(position-lo) if lo!=hi else ordered[lo]
        if len(ordered)<4:
            raise ValueError('anomaly_requires_four_usable_observations')
        q1,q3=quantile(.25),quantile(.75)
        iqr=q3-q1
        if iqr<=0:
            raise ValueError('anomaly_zero_interquartile_range')
        lower,upper=q1-1.5*iqr,q3+1.5*iqr
        return dict(n=len(values),q1=q1,q3=q3,median=median(ordered),iqr=iqr,
                    lowerFence=lower,upperFence=upper,unit=usable[0]['unit'],
                    rule='tukey_1_5_iqr',quantileMethod='linear interpolation: (n-1)*p, type 7',
                    observations=[dict(geography=o['geography'],value=o['value'],
                        classification='below_fence' if o['value']<lower else 'above_fence' if o['value']>upper else 'within_fences') for o in usable],
                    inference='descriptive peer screen; no error, quality or policy-priority claim')
    if operation == 'trend':
        axis = policy['timeAxis']
        mx, my = mean(axis), mean(values)
        slope = math.fsum((x-mx)*(y-my) for x,y in zip(axis,values)) / math.fsum((x-mx)**2 for x in axis)
        return {'slope':slope, 'unit':('percentage_points' if usable[0]['unit']=='percent' else usable[0]['unit'])+'/year', 'n':len(values), 'timeAxis':axis,
                'method':'OLS slope', 'forecast':False}
    if operation == 'correlation':
        groups = {}
        field = 'geography' if policy['axis'] == 'municipalities' else 'period'
        for o in usable:
            groups.setdefault((o['metric'],o['dimension']), {})[o[field]] = o
        a,b = list(groups.values())
        keys = sorted(set(a)&set(b))
        x,y = [a[k]['value'] for k in keys], [b[k]['value'] for k in keys]
        r = coefficient(x,y,policy['method'])
        if r is None:
            raise ValueError('numerically_constant_variable')
        influence = []
        if len(keys) >= 4:
            for i,k in enumerate(keys):
                influence.append({'excludedKey':k, 'coefficient':coefficient(x[:i]+x[i+1:],y[:i]+y[i+1:],policy['method'])})
        return {'coefficient':r, 'method':policy['method'], 'axis':policy['axis'], 'n':len(keys),
                'pairedKeys':keys, 'pairs':[{'key':k,'x':a[k],'y':b[k]} for k in keys],
                'leaveOneOut':influence, 'pValue':None, 'confidenceInterval':None,
                'inference':'descriptive association; no causal or significance claim'}
    raise ValueError('calculator_not_implemented')


class QueryEngine:
    def __init__(self, catalog_path, *, repository_root=ROOT, layer='source'):
        self.path = Path(catalog_path)
        validate_semantic_model_contract(self.path, layer=layer)
        self.root = Path(repository_root)
        body = self.path.read_bytes()
        self._catalog = json.loads(body)
        self.catalog_hash = digest(body)
        try:
            self.catalog_path = str(self.path.resolve().relative_to(self.root.resolve()))
        except ValueError:
            self.catalog_path = str(self.path.resolve())
        self.files = {}
        self.module_hash = digest(Path(__file__).read_bytes())
        self.policy_hash = digest((ROOT/'ci/semantic-operations-contract.json').read_bytes())
        self.codes = {str(t['code']) for t in self._catalog['towns']}

    @property
    def catalog(self):
        return copy.deepcopy(self._catalog)

    def file(self, relative):
        if relative not in self.files:
            path = self.root / relative
            body = path.read_bytes()
            self.files[relative] = (json.loads(body), {'path':relative,'sha256':digest(body)})
        return self.files[relative]

    def context(self, key, dimension="total"):
        metric = self._catalog['metrics'][key]
        meta = metric['meta']
        if key in classification.KEYS:return classification.context(metric,key,dimension)
        if key in profiles.KEYS:return profiles.context(metric,key,dimension)
        if key in climate.KEYS:return climate.context(metric,key,dimension)
        if key in pab.KEYS:return pab.context(metric,key,dimension)
        if key in remediation.KEYS:return remediation.context(metric,key,dimension)
        if key in extractive.KEYS:return extractive.context(metric,key,dimension)
        if key in maritime.KEYS:return maritime.context(metric,key,dimension)
        if key in bathing.KEYS:return bathing.context(metric,key,dimension)
        if key in coast.KEYS:return coast.context(metric,key,dimension)
        if key in fragility.KEYS:return fragility.context(metric,key,dimension)
        if key in hazard.KEYS:return hazard.context(metric,key,dimension)
        if key in territory.KEYS:return territory.context(metric,key,dimension)
        if key in soil.KEYS:return soil.context(metric,key,dimension)
        if key in geography.KEYS:return geography.context(metric,key,dimension)
        if key in agriculture.KEYS:return agriculture.context(metric,key,dimension)
        if key in environment.KEYS:return environment.context(metric,key,dimension)
        if key in commuting.KEYS:return commuting.context(metric,key,dimension)
        if key in demography.KEYS:return demography.context(metric,key,dimension)
        if key in distinct.KEYS:return distinct.context(metric,key,dimension)
        if key in finance.KEYS:return finance.context(metric,key,dimension)
        if key in census.KEYS:return census.context(metric,key,dimension)
        if key in business.KEYS:return business.context(metric,key,dimension)
        if key in ars.KEYS:return ars.context(metric,key,dimension)
        if key in territorial.NEW_KEYS or (key=='population' and dimension!='total'):
            return territorial.context(metric,key,dimension)
        if key == 'ageDistribution':
            return age_context(metric,dimension)
        if key in CENSUS:
            return census_context(metric,key)
        if key == 'population':
            if meta.get('unit') != 'number' or metric.get('sourceUrl') != 'https://demo.istat.it/' or 'gennaio' not in meta.get('description','').lower():
                raise ValueError('population_definition_changed')
            return dict(unit='number', population='resident population at January 1', definition='resident population stock at January 1',
                        method='Istat POSAS published annual stock', frequency='annual', periodBasis='stock at January 1 of reference year', adapter='istat-posas-population/v1')
        if key == 'income':
            if meta.get('unit') != 'currency' or urlparse(metric.get('sourceUrl','')).hostname != 'www1.finanze.gov.it' or 'imponibile' not in meta.get('description','').lower() or 'stessa definizione MEF' not in meta.get('longHistoryNote',''):
                raise ValueError('income_definition_changed')
            return dict(unit='currency', population='declarants with taxable income frequency', definition='taxable income amount / corresponding frequency, nominal euro',
                        method='MEF published taxable mean income', frequency='annual', periodBasis='income tax year; distinct from publication year', adapter='mef-taxable-income/v1')
        raise ValueError('adapter_not_implemented')

    def observation(self, key, row_index, period, *, historical, dimension="total"):
        if key in classification.KEYS:return classification.observation(self,key,row_index,dimension,period,historical)
        if key in profiles.KEYS:return profiles.observation(self,key,row_index,dimension,period,historical)
        if key in climate.KEYS:return climate.observation(self,key,row_index,dimension,period,historical)
        if key in pab.KEYS:return pab.observation(self,key,row_index,dimension,period,historical)
        if key in remediation.KEYS:return remediation.observation(self,key,row_index,dimension,period,historical)
        if key in extractive.KEYS:return extractive.observation(self,key,row_index,dimension,period,historical)
        if key in maritime.KEYS:return maritime.observation(self,key,row_index,dimension,period,historical)
        if key in bathing.KEYS:return bathing.observation(self,key,row_index,dimension,period,historical)
        if key in coast.KEYS:return coast.observation(self,key,row_index,dimension,period,historical)
        if key in fragility.KEYS:return fragility.observation(self,key,row_index,dimension,period,historical)
        if key in hazard.KEYS:return hazard.observation(self,key,row_index,dimension,period,historical)
        if key in territory.KEYS:return territory.observation(self,key,row_index,dimension,period,historical)
        if key in soil.KEYS:return soil.observation(self,key,row_index,dimension,period,historical)
        if key in geography.KEYS:return geography.observation(self,key,row_index,dimension,period,historical)
        if key in agriculture.KEYS:return agriculture.observation(self,key,row_index,dimension,period,historical)
        if key in environment.KEYS:return environment.observation(self,key,row_index,dimension,period,historical)
        if key in commuting.KEYS:return commuting.observation(self,key,row_index,dimension,period,historical)
        if key in demography.KEYS:return demography.observation(self,key,row_index,dimension,period,historical)
        if key in distinct.KEYS:return distinct.observation(self,key,row_index,dimension,period,historical)
        if key in finance.KEYS:return finance.observation(self,key,row_index,dimension,period,historical)
        if key in census.KEYS:return census.observation(self,key,row_index,dimension,period,historical)
        if key in business.KEYS:return business.observation(self,key,row_index,dimension,period,historical)
        if key in ars.KEYS:return ars.observation(self,key,row_index,dimension,period,historical)
        metric = self._catalog['metrics'][key]
        meta = metric['meta']
        row = metric['rows'][row_index]
        context = self.context(key,dimension)
        pointer = f'/metrics/{key}/rows/{row_index}'
        if key in territorial.CURRENT_ONLY or (key=='population' and dimension!='total'):
            if period_token(key,meta['year'])!=period:
                raise ValueError('current_period_mismatch')
            historical=False
            value=row.get('value');pointer+='/value'
            period_pointer=f'/metrics/{key}/meta/year'
        elif key == 'ageDistribution':
            if annual(meta['year'])!=period:
                raise ValueError('current_period_mismatch')
            historical=False # Explicit 2026 selection still uses the current composite carrier.
            value,index,components,ref,source=age_observation(self,row,period,dimension)
            pointer += f'/parts/{index}/value'
            period_pointer=f'/metrics/{key}/meta/year'
        elif historical:
            series = row.get('series')
            if not isinstance(series,dict):
                raise ValueError('series_not_available')
            periods = list(map(annual,series['years']))
            if period not in periods:
                raise ValueError(f'period_not_available:{key}:{row["code"]}:{period}')
            index = periods.index(period)
            value = series['values'][index]
            pointer += f'/series/values/{index}'
            period_pointer = f'/metrics/{key}/rows/{row_index}/series/years/{index}'
        else:
            if annual(meta['year']) != period:
                raise ValueError('current_period_mismatch')
            value = row.get('value')
            pointer += '/value'
            period_pointer = f'/metrics/{key}/meta/year'
        evidence = [{'kind':'catalog_snapshot','sha256':self.catalog_hash,'path':self.catalog_path,
                     'valuePointer':pointer,'periodPointer':period_pointer}]
        warnings = []
        if key in territorial.NEW_KEYS:
            value,suffix,components,refs,source,notes=territorial.observation(self,key,row,dimension,period,value)
            if suffix:pointer=f'/metrics/{key}/rows/{row_index}'+suffix
            evidence[0]['valuePointer']=pointer
            evidence.extend(refs);warnings.extend(notes)
        elif key=='population' and dimension!='total':
            value,suffix,components,refs,source,notes=territorial.population_sex(self,metric,row,dimension,period)
            evidence[0]['valuePointer']=f'/metrics/{key}/rows/{row_index}'+suffix
            evidence.extend(refs);warnings.extend(notes)
        elif key == 'ageDistribution':
            evidence.append(ref)
        else:
            source = metric['sourceUrl']
            components = {}
        if key in territorial.NEW_KEYS or (key=='population' and dimension!='total'):
            pass
        elif key in CENSUS:
            components,ref,source = census_observation(self,key,row,period,value)
            evidence.append(ref)
            if key == 'nonOccupiedHomesPer1000':
                warnings.append('non_resident_occupied_homes_are_not_necessarily_vacant')
        elif key == 'population':
            snapshot, ref = self.file(SNAPSHOT)
            records = snapshot['posas']['towns'][row['town']]
            records = [r for r in records if annual(r['year']) == period]
            sources = [s for s in snapshot['posas']['sources'] if annual(s['year']) == period]
            if len(records) != 1 or len(sources) != 1:
                raise ValueError('posas_record_or_source_missing')
            if value is not None and value != records[0]['population']:
                raise ValueError('posas_catalog_snapshot_mismatch')
            source = sources[0]['url']
            evidence.append(dict(ref,kind='source_snapshot',record=f'posas.towns.{row["town"]}.year={period}',
                                 generatedAt=snapshot.get('generatedAt'),status=snapshot.get('status'),sourceUrl=source))
        elif key != 'ageDistribution':
            if historical and period == str(meta['year']) and finite(value) and finite(row.get('value')) and value != row['value']:
                raise ValueError('published_current_series_mismatch')
            # Historical raw archives are not versioned here: published series
            # and the explicit homogeneity note are the available evidence.
            evidence.append({'kind':'published_method_note','pointer':'/metrics/income/meta/longHistoryNote','text':meta['longHistoryNote'], 'sha256':self.catalog_hash})
            warnings.extend(['nominal_income_not_purchasing_power','raw_income_archive_not_verified_by_adapter'])
        obs = dict(context, **components, metric=key, dimension=dimension, geography=str(row['code']), period=period,
                   value=value, source=source, evidence=evidence, provenance=evidence,
                   notApplicable=bool(row.get('notApplicable')) if not historical else False,
                   dataUnavailable=bool(row.get('dataUnavailable')) if not historical else value is None)
        return obs,warnings

    def select(self, selector, operation):
        if not isinstance(selector,dict) or set(selector)-{'metric','dimension','towns','periods'}:
            raise ValueError('invalid_selector_fields')
        key = selector.get('metric')
        if key not in self._catalog['metrics']:
            raise ValueError('unknown_metric')
        dimension=selector.get('dimension','total')
        if dimension not in dimensions(key):
            raise ValueError('explicit_age_band_required' if key=='ageDistribution' else 'dimension_adapter_not_implemented')
        self.context(key,dimension)
        if key in classification.KEYS:classification.selection_guard(key,dimension,operation)
        if key in climate.KEYS:
            self._climate_validation={}
            climate.selection_guard(key,dimension,operation)
        if key in profiles.KEYS:profiles.selection_guard(key,dimension,operation)
        if key in geography.KEYS and operation in TEMPORAL:raise ValueError('geography_history_not_frozen')
        if key in agriculture.KEYS and operation in TEMPORAL:raise ValueError('agriculture_single_census_no_history')
        if key in pab.KEYS:
            self._pab_validation=None
            pab.selection_guard(key,dimension,operation)
        if key in remediation.KEYS:remediation.selection_guard(key,dimension,operation)
        if key in extractive.KEYS:extractive.selection_guard(key,dimension,operation)
        if key in maritime.KEYS:maritime.selection_guard(key,dimension,operation)
        if key in bathing.KEYS:bathing.selection_guard(key,dimension,operation)
        if key in coast.KEYS:coast.selection_guard(key,dimension,operation)
        if key in fragility.KEYS:fragility.selection_guard(key,operation)
        if key in hazard.KEYS:hazard.selection_guard(key,dimension,operation)
        if key in territory.KEYS:territory.selection_guard(key,operation)
        if key in soil.KEYS:soil.selection_guard(key,operation)
        if key in environment.KEYS:environment.selection_guard(key,operation)
        if key in commuting.KEYS and operation in TEMPORAL:raise ValueError('commuting_history_not_frozen')
        if key=='diplomaPlus' and dimension in ('total','age:25-64|sex:total') and operation=='trend':raise ValueError('census_method_break_trend_not_supported')
        if key in business.CHANGES and operation=='trend':raise ValueError('business_cumulative_trend_not_supported')
        if key=='microUnits' and operation in TEMPORAL:raise ValueError('business_series_not_available')
        if key in ars.KEYS and operation in TEMPORAL:
            if 'age:' in dimension or (dimension!='total' and key!='lifeExpectancy'):raise ValueError('ars_historical_dimension_not_available')
            if operation=='trend' and '-' in ars._SPECS[key]['period']:raise ValueError('ars_window_trend_not_supported')
        if key=='ageDistribution' and operation in TEMPORAL:
            raise ValueError('age_historical_dimension_not_available')
        if (key in territorial.CURRENT_ONLY or (key=='population' and dimension!='total')) and operation in TEMPORAL:
            raise ValueError('historical_dimension_not_available')
        towns = selector.get('towns',sorted(self.codes))
        if not isinstance(towns,list) or not towns or any(not isinstance(c,str) or c not in self.codes for c in towns) or len(towns)!=len(set(towns)):
            raise ValueError('unknown_or_duplicate_geography')
        if key in demography.KEYS:demography.selection_guard(key,dimension,operation)
        if key in distinct.KEYS:distinct.selection_guard(key,dimension,operation,towns)
        periods = selector.get('periods')
        historical = periods is not None or operation in TEMPORAL
        selected_rows=climate.rows(self,key) if key in climate.KEYS else self._catalog['metrics'][key]['rows']
        rows = {str(r['code']):(i,r) for i,r in enumerate(selected_rows)}
        if historical and periods is None:
            if len(towns) != 1:
                raise ValueError('temporal_query_requires_one_geography')
            if key in climate.KEYS:periods=climate.available_periods(self,key,dimension,rows[towns[0]][1])
            elif key in extractive.KEYS:periods=extractive.available_periods(self,key,dimension,rows[towns[0]][1])
            elif key in bathing.KEYS:periods=bathing.available_periods(self,key,dimension,rows[towns[0]][1])
            elif key in fragility.KEYS:periods=fragility.available_periods(self,key,dimension,rows[towns[0]][1])
            elif key in hazard.KEYS:periods=hazard.available_periods(self,key,dimension,rows[towns[0]][1])
            elif key in soil.KEYS:periods=soil.available_periods(self,key,dimension,rows[towns[0]][1])
            elif key in environment.KEYS:periods=environment.available_periods(self,key,dimension,rows[towns[0]][1])
            elif key in demography.KEYS:periods=demography.available_periods(self,key,dimension,rows[towns[0]][1])
            elif key in distinct.KEYS:periods=distinct.available_periods(self,key,dimension,rows[towns[0]][1])
            elif key in finance.KEYS:periods=finance.available_periods(self,key,dimension,rows[towns[0]][1])
            elif key in census.KEYS:periods=census.available_periods(self,key,dimension,rows[towns[0]][1])
            elif key in business.KEYS:periods=business.available_periods(self,key,dimension,rows[towns[0]][1])
            elif key in ars.KEYS:periods=ars.available_periods(self,key,dimension)
            else:
                series = rows[towns[0]][1].get('series')
                if not isinstance(series,dict):raise ValueError('series_not_available')
                periods = sorted((period_token(key,p) for p in series['years']),key=int)
        elif periods is None:
            periods = [climate.default_period(dimension) if key in climate.KEYS else period_token(key,self._catalog['metrics'][key]['meta']['year'])]
        if not isinstance(periods,list) or not periods:
            raise ValueError('empty_period_selection')
        periods = [period_token(key,p) for p in periods]
        if key=='diplomaPlus' and dimension in ('total','age:25-64|sex:total') and operation in ('absolute_change','relative_change','percentage_points') and '2024' in periods and any(int(p)<2024 for p in periods):raise ValueError('census_method_break_change_not_supported')
        if len(periods) != len(set(periods)):
            raise ValueError('duplicate_period')
        if operation in TEMPORAL and (len(towns)!=1 or periods!=sorted(periods,key=demography.order if key in demography.KEYS else business.order if key in business.KEYS else ars.order if key in ars.KEYS else int)):
            raise ValueError('temporal_query_requires_ordered_periods_and_one_geography')
        if operation in ('compare','rank','weighted_ratio','benchmark_gap','anomaly') and len(periods)!=1:
            raise ValueError('cross_section_requires_one_period')
        result,warnings = [],[]
        for code in sorted(towns):
            if code not in rows:
                raise ValueError('municipal_row_not_available')
            for period in periods:
                use_history=historical and not (key in (*ars.KEYS,*business.KEYS,*census.KEYS,*finance.KEYS,*distinct.KEYS,*demography.KEYS,*environment.KEYS,*agriculture.KEYS,*geography.KEYS,*soil.KEYS,*territory.KEYS,*hazard.KEYS,*fragility.KEYS,*coast.KEYS,*bathing.KEYS,*maritime.KEYS,*extractive.KEYS,*remediation.KEYS,*pab.KEYS) and operation not in TEMPORAL and period==period_token(key,self._catalog['metrics'][key]['meta']['year']))
                observation,notes = self.observation(key,rows[code][0],period,historical=use_history,dimension=dimension)
                result.append(observation);warnings.extend(notes)
        return result,warnings

    def query(self, request):
        # Copy prevents mutation of a request from changing a returned result.
        request = copy.deepcopy(request)
        result = {'schemaVersion':1, 'engineVersion':VERSION, 'engineSha256':self.module_hash,
                  'adapterImplementationSha256':digest((ROOT/'scripts/semantic_query_adapters.py').read_bytes()),
                  'pabAdapterSha256':digest((ROOT/'scripts/semantic_query_pab_adapters.py').read_bytes()),
                  'classificationAdapterSha256':digest((ROOT/'scripts/semantic_query_classification_adapters.py').read_bytes()),
                  'agricultureProfileAdapterSha256':digest((ROOT/'scripts/semantic_query_agriculture_profile_adapters.py').read_bytes()),
                  'climateAdapterSha256':digest((ROOT/'scripts/semantic_query_climate_adapters.py').read_bytes()),
                  'remediationAdapterSha256':digest((ROOT/'scripts/semantic_query_remediation_adapters.py').read_bytes()),
                  'extractiveAdapterSha256':digest((ROOT/'scripts/semantic_query_extractive_adapters.py').read_bytes()),
                  'maritimeAdapterSha256':digest((ROOT/'scripts/semantic_query_maritime_adapters.py').read_bytes()),
                  'bathingAdapterSha256':digest((ROOT/'scripts/semantic_query_bathing_adapters.py').read_bytes()),
                  'coastAdapterSha256':digest((ROOT/'scripts/semantic_query_coast_adapters.py').read_bytes()),
                  'fragilityAdapterSha256':digest((ROOT/'scripts/semantic_query_fragility_adapters.py').read_bytes()),
                  'hazardAdapterSha256':digest((ROOT/'scripts/semantic_query_hazard_adapters.py').read_bytes()),
                  'territoryAdapterSha256':digest((ROOT/'scripts/semantic_query_territory_adapters.py').read_bytes()),
                  'soilAdapterSha256':digest((ROOT/'scripts/semantic_query_soil_adapters.py').read_bytes()),
                  'geographyAdapterSha256':digest((ROOT/'scripts/semantic_query_geography_adapters.py').read_bytes()),
                  'agricultureAdapterSha256':digest((ROOT/'scripts/semantic_query_agriculture_adapters.py').read_bytes()),
                  'environmentAdapterSha256':digest((ROOT/'scripts/semantic_query_environment_adapters.py').read_bytes()),
                  'commutingAdapterSha256':digest((ROOT/'scripts/semantic_query_commuting_adapters.py').read_bytes()),
                  'demographySchoolAdapterSha256':digest((ROOT/'scripts/semantic_query_demography_school_adapters.py').read_bytes()),
                  'distinctFinanceAdapterSha256':digest((ROOT/'scripts/semantic_query_distinct_finance_adapters.py').read_bytes()),
                  'financeAdapterSha256':digest((ROOT/'scripts/semantic_query_finance_adapters.py').read_bytes()),
                  'censusAdapterSha256':digest((ROOT/'scripts/semantic_query_census_adapters.py').read_bytes()),
                  'businessAdapterSha256':digest((ROOT/'scripts/semantic_query_business_adapters.py').read_bytes()),
                  'arsAdapterSha256':digest((ROOT/'scripts/semantic_query_ars_adapters.py').read_bytes()),
                  'territorialAdapterSha256':digest((ROOT/'scripts/semantic_query_territorial_adapters.py').read_bytes()),
                  'policySha256':self.policy_hash, 'eligibilitySha256':digest((ROOT/'scripts/semantic_operations.py').read_bytes()),
                  'catalogSha256':self.catalog_hash, 'catalogPath':self.catalog_path,
                  'query':request, 'status':'not_computable','reasons':[], 'warnings':[],
                  'observations':[], 'excluded':[], 'result':None,
                  'interpretationLevel':'calculation'}
        try:
            if not isinstance(request,dict) or set(request)-{'operation','selectors','allowPartial','method','axis','purpose','benchmark','rule','reference'}:
                raise ValueError('invalid_query_fields')
            operation = request.get('operation')
            if operation not in SUPPORTED:
                raise ValueError('operation_not_implemented')
            if operation != 'correlation' and set(request)&{'method','axis'}:
                raise ValueError('fields_not_applicable_to_operation')
            if operation not in ('correlation','anomaly') and 'purpose' in request:
                raise ValueError('fields_not_applicable_to_operation')
            if operation != 'anomaly' and set(request)&{'rule','reference'}:
                raise ValueError('fields_not_applicable_to_operation')
            if operation != 'benchmark_gap' and 'benchmark' in request:
                raise ValueError('fields_not_applicable_to_operation')
            selectors = request.get('selectors')
            if not isinstance(selectors,list) or len(selectors)!=(2 if operation=='correlation' else 1):
                raise ValueError('invalid_selector_count')
            if 'allowPartial' in request and not isinstance(request['allowPartial'],bool):
                raise ValueError('allowPartial_must_be_boolean')
            observations,notes = [],[]
            for selector in selectors:
                selected,warnings = self.select(selector,operation)
                observations.extend(selected);notes.extend(warnings)
            if operation == 'compare' and selectors[0]['metric'] in classification.KEYS:
                result['interpretationLevel'] = 'category_lookup'
            if operation == 'benchmark_gap':
                if len(observations)!=1:
                    raise ValueError('benchmark_query_requires_one_municipality')
                key=selectors[0]['metric']
                adapter=profiles.benchmark if key in profiles.KEYS else coast.benchmark if key in coast.KEYS else fragility.benchmark if key in fragility.KEYS else hazard.benchmark if key in hazard.KEYS else territory.benchmark if key in territory.KEYS else soil.benchmark if key in soil.KEYS else geography.benchmark if key in geography.KEYS else agriculture.benchmark if key in agriculture.KEYS else environment.benchmark if key in environment.KEYS else commuting.benchmark if key in commuting.KEYS else demography.benchmark if key in demography.KEYS else distinct.benchmark if key in distinct.KEYS else finance.benchmark if key in finance.KEYS else census.benchmark if key in census.KEYS else business.benchmark if key in business.KEYS else ars.benchmark if key in ars.KEYS else territorial.benchmark if key=='ageDistribution' or key in territorial.NEW_KEYS else benchmark_observation
                observations.append(adapter(self,key,request.get('benchmark'),observations[0]))
                notes.append('benchmark_gap_is_not_policy_priority')
            result['observations'] = observations
            policy = {'allowPartial':request.get('allowPartial',False)}
            if operation == 'weighted_ratio':
                if not (selectors[0]['metric'] in profiles.KEYS and profiles.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))) and not (selectors[0]['metric'] in pab.KEYS and pab.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))) and not (selectors[0]['metric'] in remediation.KEYS and remediation.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))) and not (selectors[0]['metric'] in extractive.KEYS and extractive.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))) and not (selectors[0]['metric'] in maritime.KEYS and maritime.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))) and not (selectors[0]['metric'] in bathing.KEYS and bathing.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))) and not (selectors[0]['metric'] in coast.KEYS and coast.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))) and not (selectors[0]['metric'] in hazard.KEYS and hazard.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))) and not (selectors[0]['metric'] in territory.KEYS and territory.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))) and not (selectors[0]['metric'] in soil.KEYS and soil.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))) and not (selectors[0]['metric'] in geography.KEYS and geography.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))) and not (selectors[0]['metric'] in agriculture.KEYS and agriculture.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))) and selectors[0]['metric'] not in environment.RATIOS and selectors[0]['metric'] not in CENSUS and selectors[0]['metric']!='ageDistribution' and selectors[0]['metric'] not in territorial.RATIOS and selectors[0]['metric'] not in business.RATIOS and selectors[0]['metric'] not in census.RATIOS and selectors[0]['metric'] not in finance.RATIOS and selectors[0]['metric'] not in commuting.RATIOS and not (selectors[0]['metric'] in demography.KEYS and demography.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))) and not (selectors[0]['metric'] in distinct.KEYS and distinct.weighted(selectors[0]['metric'],selectors[0].get('dimension','total'))):
                    raise ValueError('verified_ratio_adapter_required')
                policy['disjointPopulationEvidence'] = {'method':('official disjoint municipal census attribution; same selected characteristic and native census universe; individual holding IDs not replayed; no sum across overlapping characteristics and no organic-area pooling' if selectors[0]['metric'] in profiles.KEYS else 'disjoint municipal export scopes; reviewed distinct WFS features, same operational status / all operational features; no approved A-1 denominator, punctual double counting or physical network proxy' if selectors[0]['metric'] in pab.KEYS else 'distinct regional SISBON IDs assigned once to disjoint municipalities; administrative active / all registered proceedings, not risk or effectiveness' if selectors[0]['metric'] in remediation.KEYS else 'disjoint municipal territories; same PRC planning category union and intersection, hectares / native municipal hectares, never sums of G GP ACC or excavated areas' if selectors[0]['metric'] in extractive.KEYS else 'distinct SID idconc assigned once to four coastal municipalities by frozen municipal and non-municipal territorial assignment; native counts or amounts due within selected scope, never collections or municipal revenue' if selectors[0]['metric'] in maritime.KEYS else 'disjoint four coastal municipalities; same selected ARPAT classification basis or sample scope; native areas, classified kilometres or sample counts; targeted supplementary controls not exposure risk' if selectors[0]['metric'] in bathing.KEYS else 'disjoint four coastal municipal source segments; same selected class and ISPRA universe; native kilometres weighting, never Istat coastline or residents' if selectors[0]['metric'] in coast.KEYS else 'disjoint official municipal areas or census residence counts; same selected hazard scenario and source references; no sums across nested scenarios' if selectors[0]['metric'] in hazard.KEYS else 'disjoint Istat 2026 municipal partition; native per-category clipped surfaces or full network lengths reconciled to frozen union, no sums of overlapping categories or source feature presences' if selectors[0]['metric'] in territory.KEYS else 'distinct municipal territories; same source edition, native category hectares / own source area or resident denominator; no sums of nested classes' if selectors[0]['metric'] in soil.KEYS else 'disjoint municipal territories; native forest hectares or resident population / surface; explicit component reference periods' if selectors[0]['metric'] in geography.KEYS else 'disjoint municipal localized land or holdings assigned by farm center; same selected scope, native additive components' if selectors[0]['metric'] in agriculture.KEYS else 'distinct municipal distribution-network volume pairs; water-input weighting, not residents' if selectors[0]['metric'] in environment.RATIOS else 'disjoint municipalities of residence or destination; gross municipal work flows include moves within selected group; same-municipality retention is not group retention' if selectors[0]['metric'] in commuting.KEYS else 'distinct municipality school locations/buildings and field response counts; pupils are not resident children' if selectors[0]['metric'] in (*demography.STUDENTS,*demography.BUILDINGS) else 'distinct municipality accounting entities; additive amounts in the same exercise and denominator basis' if selectors[0]['metric'] in (*finance.KEYS,*distinct.KEYS) else 'distinct workplace municipality codes; additive ASIA/Frame components in the selected economic scope' if selectors[0]['metric'] in business.KEYS else 'distinct official municipality codes; additive source counts by residence'),
                    'geographies':[o['geography'] for o in observations],
                    'snapshotSha256':observations[0]['evidence'][1]['sha256']}
            if operation == 'benchmark_gap':
                policy['benchmarkComparabilityEvidence'] = {'adapter':observations[0]['adapter'],
                    'period':observations[0]['period'], 'benchmarkSnapshot':observations[1]['evidence'][0],
                    'universe':observations[0]['population'],'definition':observations[0]['definition']}
            if operation == 'anomaly':
                if request.get('rule')!='tukey_1_5_iqr' or request.get('reference')!='selected_municipalities':
                    raise ValueError('explicit_supported_anomaly_rule_and_reference_required')
                if not isinstance(request.get('purpose'),str) or not request['purpose'].strip():
                    raise ValueError('explicit_anomaly_purpose_required')
                policy.update(anomalyRule='tukey_1_5_iqr',referenceDistributionEvidence={
                    'scope':'selected_municipalities','purpose':request['purpose'],
                    'selectedGeographies':[o['geography'] for o in observations],
                    'catalogSha256':self.catalog_hash,'valueEvidence':[o['evidence'] for o in observations],
                    'exclusionsRequireOptIn':True})
                notes.extend(['small_peer_group_no_inferential_claim','anomaly_is_not_data_error_or_policy_priority','reference_selection_changes_fences'])
            if operation in TEMPORAL:
                temporal_usable = [o for o in observations if finite(o.get('value')) and not o['notApplicable'] and not o['dataUnavailable']]
                policy['periodOrder'] = [o['period'] for o in temporal_usable]
                if operation == 'trend':
                    policy['timeAxis'] = [demography.order(o['period']) if o['metric'] in demography.KEYS else int(o['period']) for o in temporal_usable]
            if operation == 'correlation':
                agriculture.correlation_guard(observations)
                if any(o['metric'] in agriculture.KEYS for o in observations):notes.append('agriculture_shared_components_and_size_are_not_independent_effects')
                hazard.correlation_guard(observations,request.get("axis"))
                if any(o["metric"] in hazard.KEYS for o in observations):notes.append("hazard_exposure_maps_and_shared_population_area_do_not_establish_causality")
                territory.correlation_guard(observations,request.get("axis"))
                if any(o["metric"] in territory.KEYS for o in observations):notes.append("territory_overlapping_categories_network_subsets_and_shared_area_require_interpretation")
                soil.correlation_guard(observations,request.get("axis"))
                environment.correlation_guard(observations,request.get("axis"))
                if any(o["metric"] in environment.KEYS for o in observations):notes.append("environment_shared_components_and_resident_normalization_require_interpretation")
                commuting.correlation_guard(observations,request.get("axis"))
                demography.correlation_guard(observations,request.get("axis"))
                distinct.correlation_guard(observations,request.get('axis'))
                if any(o['metric'] in distinct.KEYS for o in observations):notes.append('accounting_bases_denominator_dates_and_shared_components_require_interpretation')
                if request.get('axis')=='periods' and any(o['metric']=='diplomaPlus' and o['dimension'] in ('total','age:25-64|sex:total') for o in observations):raise ValueError('census_method_break_temporal_correlation_not_supported')
                if request.get('axis')=='periods' and any(o['metric'] in business.CHANGES for o in observations):raise ValueError('business_cumulative_temporal_correlation_not_supported')
                if any(o['metric'] in finance.KEYS for o in observations):notes.append('accounting_bases_denominator_dates_and_shared_components_require_interpretation')
                if any(o['metric'] in business.KEYS for o in observations):notes.append('economic_universes_and_shared_components_require_interpretation')
                if request.get('axis')=='periods' and any(o['frequency'].startswith('rolling_') for o in observations):
                    raise ValueError('ars_overlapping_window_correlation_not_supported')
                if all(s['metric']=='ageDistribution' for s in selectors):
                    notes.append('compositional_age_shares_share_denominator')
                if len({o['periodBasis'] for o in observations}) > 1:
                    notes.append('stock_and_flow_reference_periods_differ')
                purpose = request.get('purpose')
                if not isinstance(purpose,str) or not purpose.strip():
                    raise ValueError('explicit_pair_selection_purpose_required')
                policy.update(axis=request.get('axis'), method=request.get('method'),pairComparabilityEvidence={'purpose':purpose,'adapters':[o['adapter'] for o in observations]})
                if policy['axis']=='municipalities' and any(len(set(o['period'] for o in observations if o['metric']==s['metric']))!=1 for s in selectors):
                    raise ValueError('cross_section_requires_one_period')
            assessment = assess(operation,observations,policy=policy)
            result.update(reasons=assessment['reasons'],warnings=sorted(set(notes+assessment['warnings'])),
                          coverage=assessment['coverage'],formula=assessment['formula'],policy=policy)
            result['excluded'] = [{'observation':observations[i], 'reason':'not_applicable' if observations[i]['notApplicable'] else 'data_unavailable_or_missing'} for i in assessment['coverage']['excludedIndices']]
            if operation=='correlation':
                field = 'geography' if policy['axis']=='municipalities' else 'period'
                groups = []
                for selector in selectors:
                    groups.append({o[field]:o for o in observations if o['metric']==selector['metric'] and o['dimension']==selector.get('dimension','total') and finite(o.get('value')) and not o['notApplicable'] and not o['dataUnavailable']})
                common = set(groups[0])&set(groups[1])
                union = set(o[field] for o in observations)
                result['pairCoverage'] = {'requested':len(union),'paired':len(common),'excludedKeys':sorted(union-common)}
                for key in sorted(union-common):
                    result['excluded'].append({'pairingKey':key,'reason':'no_usable_pair'})
                result['interpretationLevel'] = 'association'
            if assessment['eligible']:
                computed = calculate(operation,observations,policy)
                # JSON disallows silently publishing NaN/Infinity results.
                json.dumps(computed,allow_nan=False)
                result.update(status='computed',result=computed)
        except (ValueError,KeyError,TypeError,OSError,OverflowError,ZeroDivisionError) as exc:
            result['reasons'].append(str(exc))
        return copy.deepcopy(result)

    def coverage(self):
        matrix = coverage_matrix(self.catalog)
        for entry in matrix:
            try:
                declared=dimensions(entry['metric'])
                self.context(entry['metric'],declared[0])
                contexts={};states={}
                for d in declared:
                    try:
                        contexts[d]=self.context(entry['metric'],d)
                        states[d]={'status':'adapter_present_query_preconditions_apply'}
                    except ValueError as exc:
                        states[d]={'status':'not_supported','reason':str(exc)}
                per_dimension={d:operations(entry['metric'],d,c['unit']) for d,c in contexts.items()}
                dims=list(contexts)
                entry['engine'] = {'adapter':contexts[dims[0]]['adapter'], 'dimensions':dims,
                    'operations':per_dimension[dims[0]],'operationsByDimension':per_dimension,
                    'dimensionStatus':states,'benchmarkScopes':(profiles.scopes(entry['metric'],dims[0]) if entry['metric'] in profiles.KEYS else [] if entry['metric'] in (*classification.KEYS,*climate.KEYS,*bathing.KEYS,*maritime.KEYS,*extractive.KEYS,*remediation.KEYS,*pab.KEYS) else coast.scopes(entry['metric'],dims[0]) if entry['metric'] in coast.KEYS else fragility.scopes(entry['metric']) if entry['metric'] in fragility.KEYS else [] if entry['metric'] in hazard.KEYS else [] if entry['metric'] in territory.KEYS else soil.scopes(entry['metric'],dims[0]) if entry['metric'] in soil.KEYS else geography.scopes(entry['metric'],dims[0]) if entry['metric'] in geography.KEYS else agriculture.scopes(entry['metric'],dims[0]) if entry['metric'] in agriculture.KEYS else ['tuscany','italy'] if entry['metric'] in (*environment.KEYS,*commuting.RATIOS) else demography.benchmark_scopes(entry['metric'],dims[0]) if entry['metric'] in demography.KEYS else census.benchmark_scopes(entry['metric']) if entry['metric'] in census.KEYS else business.benchmark_scopes(entry['metric']) if entry['metric'] in business.KEYS else ['versilia'] if entry['metric'] in ars.LEGACY_ONLY else ['tuscany','versilia'] if entry['metric'] in ars.KEYS or entry['metric']=='elderlyHomeCare' else ['tuscany'] if entry['metric'] in territorial.RATIOS else ['tuscany','italy'] if entry['metric'] in CENSUS or entry['metric'] in ('income','ageDistribution') else []),'status':'adapter_present_query_preconditions_apply'}
            except ValueError as exc:
                entry['engine'] = {'status':'not_supported','reason':str(exc)}
        return matrix


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog',type=Path,default=ROOT/'data/site-data.json')
    parser.add_argument('--layer',choices=['source','effective'],default='source')
    parser.add_argument('--query',type=Path)
    parser.add_argument('--coverage',action='store_true')
    parser.add_argument('--examples',type=Path)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    engine = QueryEngine(args.catalog,layer=args.layer)
    if sum((args.coverage,bool(args.query),bool(args.examples))) != 1:
        parser.error('choose --query, --examples or --coverage')
    if args.examples:
        examples=json.loads(args.examples.read_text())['examples']
        payload=[{'id':e['id'],'output':engine.query(e['query'])} for e in examples]
    else:
        payload = engine.coverage() if args.coverage else engine.query(json.loads(args.query.read_text()))
    body = json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if args.output:
        args.output.write_text(body,encoding='utf-8')
    else:
        print(body,end='')


if __name__=='__main__':
    main()
