"""Distinct accounting carriers; frozen evidence never certifies live availability."""
import math
from urllib.parse import urlparse

from semantic_operations import finite

DEBT = 'financialDebtProfile'
FISCAL = 'fiscalRecoveryActivity'
WORKS = 'publicWorks'
SECURITY = 'securityMissionExpenditurePerResident'
KEYS = (DEBT, FISCAL, WORKS, SECURITY)
DEBT_SNAPSHOT = 'data/source-snapshots/salute-finanziaria-v129.json'
FISCAL_SNAPSHOT = 'data/source-snapshots/fiscal-lotto-b-2025.json'
BILANCI = 'data/source-snapshots/bilanci-v1.6.0.json'
CANONICAL = 'data/site-data.json'
DEBT_PARTS = ('debtPerResident', 'interestShare', 'debtSustainability')
FISCAL_PARTS = ('recoveryPerResident', 'recoveryTotal', 'daitContribution')


def dimensions(key):
    return ['total', *('part:' + p for p in (DEBT_PARTS if key == DEBT else FISCAL_PARTS))] if key in (DEBT, FISCAL) else ['total']


def part(key, dimension):
    if dimension not in dimensions(key):
        raise ValueError('distinct_finance_dimension_not_reviewed')
    return (DEBT_PARTS[0] if key == DEBT else FISCAL_PARTS[0]) if dimension == 'total' and key in (DEBT, FISCAL) else dimension.removeprefix('part:')


def weighted(key, dimension):
    p = part(key, dimension)
    return (key == DEBT and p in DEBT_PARTS[:2]) or (key == FISCAL and p == FISCAL_PARTS[0])


def close(value, expected, tolerance=1e-7):
    if value is not None and (not finite(value) or not finite(expected) or not math.isclose(value, expected, rel_tol=0, abs_tol=tolerance)):
        raise ValueError('distinct_finance_catalog_source_mismatch')


def context(metric, key, dimension):
    p = part(key, dimension)
    host = urlparse(metric.get('sourceUrl', '')).hostname
    if host != ('bdap-opendata.rgs.mef.gov.it' if key == FISCAL else 'openbdap.rgs.mef.gov.it'):
        raise ValueError('distinct_finance_source_changed')
    if metric['meta']['unit'] != ('eurPerResident' if key == DEBT else 'currency'):
        raise ValueError('distinct_finance_unit_changed')
    definitions = {
        'debtPerResident': 'year-end D1 financing debt / exercise January 1 residents',
        'interestShare': 'interest commitments / current revenue accruals * 100',
        'debtSustainability': 'reviewed PDI 10.3; documented scale corrections and component reconstruction',
        'recoveryPerResident': 'December cumulative verification/control local tax receipts / dataset populationIstat',
        'recoveryTotal': 'December cumulative verification/control local tax receipts, nominal euro',
        'daitContribution': 'DAIT grant 2025 for state-tax receipts 2024 following municipal referrals',
    }
    definition = definitions.get(p, 'monitored BDAP-MOP project stock per resident; not annual spending' if key == WORKS else 'Mission 03 current and capital commitments per resident; not security outcomes')
    unit = 'percent' if key == DEBT and p != 'debtPerResident' else 'currency'
    basis = 'grant allocation 2025; underlying state-tax receipts 2024' if p == 'daitContribution' else 'monitoring stock labelled 2026; exact observation date not frozen' if key == WORKS else 'accounting exercise; component and denominator references explicit'
    return dict(unit=unit, population='municipal accounting or project perimeter; normalization is not beneficiaries', definition=definition,
                method=definition, frequency='annual', periodBasis=basis, adapter='distinct-finance/' + key + '/' + p + '/v1')


def carrier(metric, row, key, dimension):
    p = part(key, dimension)
    if key == DEBT:
        matches = [(i, x) for i, x in enumerate(row.get('parts', [])) if x.get('key') == p]
        if len(matches) != 1:
            raise ValueError('distinct_finance_missing_or_duplicate_part')
        i, selected = matches[0]
        if selected.get('unit') != ('eurPerResident' if p == 'debtPerResident' else 'percent2'):
            raise ValueError('distinct_finance_part_unit_changed')
        return selected, '/parts/' + str(i)
    if key == FISCAL and p != 'recoveryPerResident':
        i = FISCAL_PARTS.index(p)
        parts = row.get('parts', [])
        if len(parts) != 3 or parts[i].get('selectorLabel') != ('Recupero totale' if i == 1 else 'Contributo accertamento') or parts[i].get('unit') != 'currency':
            raise ValueError('distinct_finance_part_definition_changed')
        return parts[i], '/parts/' + str(i)
    return row, ''


def available_periods(engine, key, dimension, row):
    metric = engine._catalog['metrics'][key]
    selected, _ = carrier(metric, row, key, dimension)
    if key == WORKS:
        raise ValueError('distinct_finance_project_history_not_frozen')
    if key == FISCAL:
        return ['2025']
    series = selected.get('series')
    if not isinstance(series, dict):
        raise ValueError('distinct_finance_series_not_available')
    years = list(map(str, series['years']))
    if not years or len(years) != len(set(years)) or len(years) != len(series['values']):
        raise ValueError('distinct_finance_series_periods_mismatch')
    return sorted(years, key=int)


def selection_guard(key, dimension, operation, towns):
    if key == WORKS and operation in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('distinct_finance_project_history_not_frozen')
    if key == FISCAL and operation in ('absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('distinct_finance_only_one_fiscal_period')
    if key == DEBT and '046018' in towns and operation in ('absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('distinct_finance_massarosa_osl_temporal_perimeter_not_attested')


def observation(engine, key, index, dimension, period, historical):
    metric = engine._catalog['metrics'][key]
    row = metric['rows'][index]
    p = part(key, dimension)
    ctx = context(metric, key, dimension)
    selected, suffix = carrier(metric, row, key, dimension)
    pointer = f'/metrics/{key}/rows/{index}' + suffix
    current = str(metric['meta']['year'])
    if key in (FISCAL, WORKS):
        if period != current:
            raise ValueError('distinct_finance_period_not_available')
        value = selected.get('value'); vp = pointer + '/value'; pp = f'/metrics/{key}/meta/year'
    elif historical:
        years = available_periods(engine, key, dimension, row)
        if period not in years:
            raise ValueError('distinct_finance_period_not_available')
        j = list(map(str, selected['series']['years'])).index(period)
        value = selected['series']['values'][j]; vp = pointer + f'/series/values/{j}'; pp = pointer + f'/series/years/{j}'
    else:
        if period != current:
            raise ValueError('distinct_finance_current_period_mismatch')
        value = selected.get('value'); vp = pointer + '/value'; pp = f'/metrics/{key}/meta/year'
        if key == DEBT and dimension == 'total':
            value = row.get('value'); vp = f'/metrics/{key}/rows/{index}/value'
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=vp, periodPointer=pp)]
    warnings = ['municipal_accounting_or_project_carrier_not_policy_effect', 'gross_municipal_amounts_not_consolidated_for_interentity_transfers']
    if ctx['unit'] == 'currency':
        warnings.append('nominal_finance_values_not_real_growth')
    components = {}; dates = {}; source = metric['sourceUrl']
    if key == DEBT:
        snap, ref = engine.file(DEBT_SNAPSHOT); raw = snap['towns'][row['town']]
        if raw['code'] != row['code'] or len(snap['years']) != len(set(snap['years'])):
            raise ValueError('distinct_finance_geography_or_years_changed')
        j = list(map(str, snap['years'])).index(period)
        for field in ('current_revenue', 'interest_commitments', 'debt_financing_d1', 'debt_sustainability_10_3', 'debt_sustainability_source', 'debt_sustainability_pdi_raw', 'title4_repayment', 'excluded_capital_transfers_10_3'):
            if len(raw[field]) != len(snap['years']):
                raise ValueError('distinct_finance_frozen_series_periods_mismatch')
        evidence.append(dict(ref, kind='source_snapshot', recordPointer=f'/towns/{row["town"]}', archives=snap['archives'][period], archiveVerification='frozen extraction hashes; original archives not reread'))
        source = snap['source']['portal_url']
        if p == 'debtSustainability':
            expected = raw['debt_sustainability_10_3'][j]; provenance = raw['debt_sustainability_source'][j]
            original = raw['debt_sustainability_pdi_raw'][j]
            if provenance == 'pdi': close(expected, original)
            elif provenance == 'pdi_scale_normalized':
                if row['town'] != 'Camaiore' or period not in ('2023', '2024'):
                    raise ValueError('distinct_finance_pdi_correction_not_reviewed')
                close(expected, original / 100)
            elif provenance == 'reconstructed_components':
                if row['town'] != 'Forte dei Marmi' or period not in ('2019', '2023', '2024', '2025'):
                    raise ValueError('distinct_finance_pdi_reconstruction_not_reviewed')
                numerator = raw['interest_commitments'][j] + raw['title4_repayment'][j] - raw['excluded_capital_transfers_10_3'][j]
                close(expected, numerator / raw['current_revenue'][j] * 100, 1e-6)
            else: raise ValueError('distinct_finance_pdi_provenance_not_reviewed')
            provenance_series = selected.get('provenanceSeries')
            if not isinstance(provenance_series, list) or len(provenance_series) != len(snap['years']) or provenance_series[j] != provenance:
                raise ValueError('distinct_finance_pdi_provenance_changed')
            evidence[-1]['annualProvenance'] = provenance
            warnings.append('pdi_10_3_rounded_or_corrected_no_implicit_weighting')
        else:
            if p == 'debtPerResident':
                bilanci, bref = engine.file(BILANCI); br = bilanci['raw'][row['town']]
                if br['code'] != row['code']: raise ValueError('distinct_finance_geography_or_years_changed')
                n = raw['debt_financing_d1'][j]; d = br['years'][period]['population_at_1_january']; scale = 1
                evidence.append(dict(bref, kind='denominator_snapshot', recordPointer=f'/raw/{row["town"]}/years/{period}/population_at_1_january'))
                dates = dict(numeratorPeriod=period, numeratorReferenceDate='31 dicembre ' + period, denominatorPeriod=period, denominatorReferenceDate='1 gennaio ' + period)
                warnings.append('d1_financing_debt_not_all_municipal_liabilities')
            else:
                n = raw['interest_commitments'][j]; d = raw['current_revenue'][j]; scale = 100
            if not finite(n) or not finite(d) or d <= 0: raise ValueError('distinct_finance_invalid_components')
            components = dict(numerator=n, denominator=d, scale=scale); expected = n / d * scale
        if row['town'] == 'Massarosa': warnings.append('massarosa_2019_distress_osl_liabilities_outside_ordinary_accounting_perimeter')
        warnings.append('debt_snapshot_archives_distinct_from_legacy_finance_release')
    elif key == FISCAL:
        snap, ref = engine.file(FISCAL_SNAPSHOT); raw = snap['towns'][row['town']]
        if str(snap['referenceYear']) != '2025' or raw['siopeMonth'] != '2025/12':
            raise ValueError('distinct_finance_fiscal_reference_changed')
        if metric['sourceUrl'] != snap['siopeMetadataUrl'] or metric['method'].get('siopeReferenceMonth') != raw['siopeMonth'] or metric['method'].get('additionalSource') != snap['daitUrl']:
            raise ValueError('distinct_finance_fiscal_reference_changed')
        evidence.append(dict(ref, kind='source_snapshot', recordPointer=f'/towns/{row["town"]}', limitation='frozen extraction; original CSV and complete DAIT beneficiary list not reread'))
        dates = dict(numeratorPeriod='2025', numeratorReferenceMonth='2025/12')
        if p == 'daitContribution':
            expected = raw['daitContribution2025Euro']; source = snap['daitUrl']
            dates = dict(numeratorPeriod='2024', allocationPeriod='2025')
            warnings += ['dait_2025_grant_underlying_state_tax_receipts_2024', 'dait_zero_is_absent_beneficiary_in_published_complete_list_not_no_tax_evasion']
        else:
            source = snap['siopeCsvUrl']; n = raw['verificationControlReceiptsEuro']; d = raw['populationIstat']
            if not finite(n) or not finite(d) or d <= 0: raise ValueError('distinct_finance_invalid_components')
            codes = raw['codes']
            if len({c['code'] for c in codes.values()}) != len(codes):
                raise ValueError('distinct_finance_fiscal_codes_changed')
            if any(not finite(c['amountEuro']) or 'verifica e controllo' not in c['label'].lower() for c in codes.values()):
                raise ValueError('distinct_finance_fiscal_codes_changed')
            close(math.fsum(c['amountEuro'] for c in codes.values()), n)
            close(math.fsum(raw['breakdownEuro'].values()), n)
            if row.get('sourceCodes') != codes or row.get('breakdownEuro') != raw['breakdownEuro'] or row.get('populationIstat') != d:
                raise ValueError('distinct_finance_fiscal_components_changed')
            expected = n if p == 'recoveryTotal' else n / d
            if p == 'recoveryPerResident':
                components = dict(numerator=n, denominator=d, scale=1)
                dates['denominatorBasis'] = 'populationIstat explicitly supplied by SIOPE; exact reference date not frozen'
                close(row['parts'][0]['value'], round(expected, 2)); close(raw['verificationControlReceiptsPerResidentEuro'], round(expected, 2))
                if historical:
                    if row.get('series', {}).get('years') != [2025] or len(row['series']['values']) != 1:
                        raise ValueError('distinct_finance_series_periods_mismatch')
                    close(row['series']['values'][0], expected)
                warnings.append('siope_dataset_population_date_not_attested_no_next_january_substitution')
            warnings += ['verification_control_receipts_not_tax_evasion_rate_or_office_effectiveness', 'december_cash_receipts_not_competence_accruals']
    else:
        canonical, ref = engine.file(CANONICAL); cm = canonical['metrics'][key]
        matches = [(i, r) for i, r in enumerate(cm['rows']) if r['code'] == row['code']]
        if len(matches) != 1 or str(cm['meta']['year']) != current or cm['sourceUrl'] != source or cm['meta']['unit'] != metric['meta']['unit']:
            raise ValueError('distinct_finance_canonical_context_changed')
        ci, cr = matches[0]
        if historical:
            years = list(map(str, cr['series']['years']))
            expected = cr['series']['values'][years.index(period)]
        else: expected = cr['value']
        evidence.append(dict(ref, kind='published_normalized_carrier', recordPointer=f'/metrics/{key}/rows/{ci}', sourceUrl=source,
                             limitation='canonical normalized value; original amounts and denominator not frozen, no raw reconciliation or weighting'))
        warnings.append('published_normalized_carrier_no_frozen_raw_components_or_weighting')
        warnings.append('monitored_projects_not_annual_spend_progress_or_disjoint_cups' if key == WORKS else 'mission_03_commitments_not_crime_staff_or_delivered_security')
    close(value, expected)
    if key == DEBT and period == current: close(selected.get('value'), expected)
    if key in (DEBT, SECURITY) and historical and period == current: close(selected.get('value'), value)
    if key == DEBT and p == 'debtPerResident' and period == current: close(row.get('value'), expected)
    return dict(ctx, **components, **dates, metric=key, dimension=dimension, geography=row['code'], period=period,
                value=value, source=source, evidence=evidence, provenance=evidence,
                notApplicable=bool(row.get('notApplicable')) if not historical else False,
                dataUnavailable=value is None or (bool(row.get('dataUnavailable')) if not historical else False)), warnings


def benchmark(engine, key, scope, municipal):
    raise ValueError('distinct_finance_benchmark_components_or_perimeter_not_frozen')


def correlation_guard(observations, axis):
    if axis == 'periods' and any(o['metric'] == DEBT and o['geography'] == '046018' for o in observations):
        raise ValueError('distinct_finance_massarosa_osl_temporal_perimeter_not_attested')
    if any(o['metric'] == FISCAL and part(FISCAL, o['dimension']) == 'daitContribution' for o in observations):
        raise ValueError('distinct_finance_dait_allocation_and_underlying_receipt_periods_not_aligned')
