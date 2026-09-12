#!/usr/bin/env python3
from pathlib import Path

P = Path('scripts/patch_territorio_v137_runtime.py')
s = P.read_text(encoding='utf-8')


def exact(old: str, new: str, expected: int, label: str) -> None:
    global s
    count = s.count(old)
    if count != expected:
        raise RuntimeError(f'{label}: attese {expected} occorrenze, trovate {count}')
    s = s.replace(old, new)

# renderCompareMetric: v1.33 ha già aggiunto ratioProfile + hydroRisk.
exact(
    "'financialProfile','demographicBreakdown','sexBreakdown']",
    "'financialProfile','ratioProfile','demographicBreakdown','sexBreakdown','hydroRisk']",
    2,
    'selectable compare post-fragilita',
)

# renderTownMetric: preserva hydroRisk mentre aggiunge territoryProfile.
exact(
    '    const selectable = distribution || omi || stock || securityMeasures || demographicBreakdown || sexBreakdown;\\n',
    '    const selectable = distribution || omi || stock || securityMeasures || demographicBreakdown || sexBreakdown || hydroRisk;\\n',
    1,
    'town selectable target',
)
exact(
    '    const selectable = distribution || omi || stock || securityMeasures || demographicBreakdown || sexBreakdown || territoryProfile;\\n',
    '    const selectable = distribution || omi || stock || securityMeasures || demographicBreakdown || sexBreakdown || hydroRisk || territoryProfile;\\n',
    1,
    'town selectable replacement',
)
exact(
    '((omi || stock || securityMeasures) ? options[0] : null)',
    '((omi || stock || securityMeasures || hydroRisk) ? options[0] : null)',
    2,
    'town summary hydro preservation',
)
exact(
    "(securityMeasures ? compositeSelectionAggregate(metric,'part-0') : null)",
    "(securityMeasures ? compositeSelectionAggregate(metric,'part-0') : (hydroRisk ? compositeSelectionAggregate(metric,metric.meta.defaultScenario) : null))",
    2,
    'town aggregate hydro preservation',
)
exact(
    "financialProfile ? `Indicatore ${initialFinancialReading.code}` : composite ?",
    "financialProfile ? `Indicatore ${initialFinancialReading.code}` : hydroRisk ? 'Matrice ufficiale ISPRA' : composite ?",
    1,
    'town overline target',
)
exact(
    "financialProfile ? `Indicatore ${initialFinancialReading.code}` : territoryProfile ? 'Letture territoriali' : composite ?",
    "financialProfile ? `Indicatore ${initialFinancialReading.code}` : territoryProfile ? 'Letture territoriali' : hydroRisk ? 'Matrice ufficiale ISPRA' : composite ?",
    1,
    'town overline replacement',
)
exact(
    "financialProfile ? initialFinancialReading.label : composite ?",
    "financialProfile ? initialFinancialReading.label : hydroRisk ? `Territorio e residenti · ${html(metric.meta.year)}` : composite ?",
    1,
    'town title target',
)
exact(
    "financialProfile ? initialFinancialReading.label : territoryProfile ? `${html(metric.meta.label)} · ${html(metric.meta.year)}` : composite ?",
    "financialProfile ? initialFinancialReading.label : territoryProfile ? `${html(metric.meta.label)} · ${html(metric.meta.year)}` : hydroRisk ? `Territorio e residenti · ${html(metric.meta.year)}` : composite ?",
    1,
    'town title replacement',
)
exact(
    "['drinkingWaterQuality','remediationProceedings'].includes(metric.meta.compositeType)",
    "['drinkingWaterQuality','remediationProceedings','hydroRisk'].includes(metric.meta.compositeType)",
    2,
    'town benchmark hydro preservation',
)

# renderIndicator: v1.33 ha già aggiunto la vista hydroRisk e il relativo aside.
exact(
    'indicatorComparisonTable(data, pageMetric, initialFinancialChoice)}</div><aside',
    'indicatorComparisonTable(data, pageMetric, initialFinancialChoice, initialHydroView)}</div><aside',
    1,
    'indicator comparison target hydro arg',
)
exact(
    'indicatorComparisonTable(data, pageMetric, territoryProfile ? initialTerritoryChoice : initialFinancialChoice)}</div><aside',
    'indicatorComparisonTable(data, pageMetric, territoryProfile ? initialTerritoryChoice : initialFinancialChoice, initialHydroView)}</div><aside',
    1,
    'indicator comparison replacement hydro arg',
)

generic = "`<span>${html(metric.meta.compositeType === 'distribution' ? compositeAggregateSummary(metric).label : metric.aggregate.label)}</span><strong>${html(metric.meta.compositeType === 'distribution' ? compositeAggregateSummary(metric).formatted : formatValue(metric.aggregate.value, metric.meta.unit))}</strong><p>${html(metric.meta.compositeType === 'distribution' ? (metric.aggregate.summaryNote || metric.aggregate.note) : metric.aggregate.note)}</p>`"
hydro = "`<span>${html(initialHydroAggregate.label)}</span><strong>${html(formatValue(initialHydroAggregate.value,initialHydroAggregate.unit))}</strong><p>${html(initialHydroAggregate.note || metric.aggregate.note || '')}</p>`"
exact(
    f"${{financialProfile ? financialProfileIndicatorAsideMarkup(metric,initialFinancialChoice) : {generic}}}",
    f"${{financialProfile ? financialProfileIndicatorAsideMarkup(metric,initialFinancialChoice) : hydroRisk ? {hydro} : {generic}}}",
    1,
    'indicator aside target hydro',
)
exact(
    f"${{financialProfile ? financialProfileIndicatorAsideMarkup(metric,initialFinancialChoice) : territoryProfile ? territoryProfileIndicatorAsideMarkup(metric,initialTerritoryChoice) : {generic}}}",
    f"${{financialProfile ? financialProfileIndicatorAsideMarkup(metric,initialFinancialChoice) : territoryProfile ? territoryProfileIndicatorAsideMarkup(metric,initialTerritoryChoice) : hydroRisk ? {hydro} : {generic}}}",
    1,
    'indicator aside replacement hydro',
)
exact(
    "<section class=\\\"indicator-benchmark page-width\\\">${financialProfile ? '' : benchmarkMarkup(metric, metric.aggregate, metric.meta.unit, null)}</section>",
    "<section class=\\\"indicator-benchmark page-width\\\">${(financialProfile || hydroRisk) ? '' : benchmarkMarkup(metric, metric.aggregate, metric.meta.unit, null)}</section>",
    1,
    'indicator benchmark target hydro',
)
exact(
    "<section class=\\\"indicator-benchmark page-width\\\">${(financialProfile || territoryProfile) ? '' : benchmarkMarkup(metric, metric.aggregate, metric.meta.unit, null)}</section>",
    "<section class=\\\"indicator-benchmark page-width\\\">${(financialProfile || territoryProfile || hydroRisk) ? '' : benchmarkMarkup(metric, metric.aggregate, metric.meta.unit, null)}</section>",
    1,
    'indicator benchmark replacement hydro',
)

P.write_text(s, encoding='utf-8')
print('patch territorio v1.37 riallineata al renderer post-fragilita v1.33')
