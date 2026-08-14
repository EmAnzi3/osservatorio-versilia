#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VG = ROOT / 'assets' / 'visual-grammar.js'
UX = ROOT / 'assets' / 'ux-history.js'


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Patch non applicabile: {label}')
    return text.replace(old, new, 1)


def patch_visual_grammar(text):
    text = replace_once(
        text,
        "    comunita: 'administrative'\n  };",
        "    comunita: 'administrative',\n    sicurezza: 'territorial'\n  };",
        'scope sicurezza',
    )
    text = replace_once(
        text,
        "    'tourismDevelopmentMissionExpenditurePerResident',\n    'publicWorks',",
        "    'tourismDevelopmentMissionExpenditurePerResident',\n    'securityMissionExpenditurePerResident',\n    'roadFinesPerResident',\n    'publicWorks',",
        'metriche amministrative sicurezza',
    )
    text = replace_once(
        text,
        "    'roadInjuries',\n    'thirdSector'",
        "    'roadInjuries',\n    'roadSafety',\n    'thirdSector'",
        'roadSafety territoriale',
    )
    text = replace_once(
        text,
        "    if (kind === 'per1000') return `${formatted} ogni 1.000`;\n    if (kind === 'eurm2')",
        "    if (kind === 'per1000') return `${formatted} ogni 1.000`;\n    if (kind === 'per100') return `${formatted} ogni 100`;\n    if (kind === 'per10k') return `${formatted} ogni 10.000`;\n    if (kind === 'eurm2')",
        'formati assi sicurezza',
    )
    text = replace_once(
        text,
        "    if (!choice || !['stock','omi','mobility'].includes(type)) return null;\n    if (type === 'stock') {",
        "    if (!choice || !['stock','omi','mobility','securityMeasures'].includes(type)) return null;\n    if (type === 'securityMeasures') {\n      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);\n      const part = row?.parts?.[index] || {};\n      return { value: part.value, unit: part.unit || metric?.meta?.unit || '' };\n    }\n    if (type === 'stock') {",
        'selezione visual grammar',
    )
    # seconda occorrenza: aggregate
    text = replace_once(
        text,
        "    if (!choice || !['stock','omi','mobility'].includes(type)) return null;\n    if (type === 'stock') {",
        "    if (!choice || !['stock','omi','mobility','securityMeasures'].includes(type)) return null;\n    if (type === 'securityMeasures') {\n      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);\n      const part = metric.aggregate?.parts?.[index] || {};\n      return { value: part.value, label:`Versilia · ${part.label || metric.meta.label}`, unit:part.unit || metric?.meta?.unit || '' };\n    }\n    if (type === 'stock') {",
        'aggregate visual grammar',
    )
    text = replace_once(
        text,
        "    const unit = first?.unit || unitFor(firstRow, metric, normalized);\n    // Nei compositi selezionabili",
        "    const unit = first?.unit || compositeAggregate?.unit || unitFor(firstRow, metric, normalized);\n    // Nei compositi selezionabili",
        'unità aggregate visual grammar',
    )
    text = replace_once(
        text,
        "    const selectablePercent = metric?.meta?.compositeType === 'stock' && container.dataset.compositeChoice && unitKind(unit) === 'percent';",
        "    const selectablePercent = ['stock','securityMeasures'].includes(metric?.meta?.compositeType) && container.dataset.compositeChoice && unitKind(unit) === 'percent';",
        'scala percentuale aderente',
    )
    return text


def patch_ux_history(text):
    text = replace_once(
        text,
        "    if (!['distribution','omi','stock'].includes(metric?.meta?.compositeType)) return metric;",
        "    if (!['distribution','omi','stock','securityMeasures'].includes(metric?.meta?.compositeType)) return metric;",
        'ux history compositi supportati',
    )
    anchor = "    if (metric.meta.compositeType === 'stock') {\n      const count = choice === 'count';"
    insert = "    if (metric.meta.compositeType === 'securityMeasures') {\n      const index = Math.max(0, Number(String(choice || 'part-0').replace('part-','')) || 0);\n      const template = metric.rows?.[0]?.parts?.[index] || metric.aggregate?.parts?.[index] || {};\n      const unit = template.unit || metric.meta.unit;\n      clone.meta.unit = unit;\n      clone.meta.label = template.label || metric.meta.label;\n      clone.rows = metric.rows.map(row => {\n        const part = row.parts?.[index] || {};\n        const value = Number(part.value);\n        let formatted = 'n.d.';\n        if (Number.isFinite(value)) {\n          if (unit === 'currency') formatted = `${number1.format(value)} €`;\n          else if (unit === 'percent') formatted = `${percent1.format(value)}%`;\n          else if (unit === 'per1000') formatted = `${number1.format(value)} ogni 1.000`;\n          else if (unit === 'per100') formatted = `${number1.format(value)} ogni 100`;\n          else if (unit === 'per10k') formatted = `${number1.format(value)} ogni 10.000`;\n          else formatted = number1.format(value);\n        }\n        const series = row.componentSeries?.[part.selectorLabel || template.selectorLabel] || row.componentSeries?.[template.selectorLabel] || row.series;\n        return { ...row, value, formatted, series };\n      });\n      return clone;\n    }\n" + anchor
    text = replace_once(text, anchor, insert, 'ux history securityMeasures selection')
    text = replace_once(
        text,
        "    if (!shell || !['distribution','omi','stock'].includes(metric?.meta?.compositeType)) return;",
        "    if (!shell || !['distribution','omi','stock','securityMeasures'].includes(metric?.meta?.compositeType)) return;",
        'ux history town current support',
    )
    text = replace_once(
        text,
        "    const resolvedChoice = choice || (metric?.meta?.compositeType === 'omi' ? 'sale' : metric?.meta?.compositeType === 'stock' ? 'share' : 'summary');",
        "    const resolvedChoice = choice || (metric?.meta?.compositeType === 'omi' ? 'sale' : metric?.meta?.compositeType === 'stock' ? 'share' : metric?.meta?.compositeType === 'securityMeasures' ? 'part-0' : 'summary');",
        'ux history default security choice',
    )
    text = replace_once(
        text,
        "  function currentCompositeChoice() {\n    return document.querySelector('[data-composite-choice]')?.value || 'summary';\n  }",
        "  function currentCompositeChoice() {\n    return document.querySelector('select[data-composite-choice]')?.value || document.querySelector('select[data-composite-component]')?.value || 'summary';\n  }",
        'ux history read current choice',
    )
    return text


def main():
    vg = patch_visual_grammar(VG.read_text(encoding='utf-8'))
    ux = patch_ux_history(UX.read_text(encoding='utf-8'))
    VG.write_text(vg, encoding='utf-8')
    UX.write_text(ux, encoding='utf-8')
    print('Layer visuali securityMeasures aggiornati')


if __name__ == '__main__':
    main()
