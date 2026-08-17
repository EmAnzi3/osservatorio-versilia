#!/usr/bin/env python3
"""Fix fuel-price precision, missing values and comparison scaling in the draft UI."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VISUAL = ROOT / 'assets/visual-grammar.js'
UX = ROOT / 'assets/ux-history.js'
CORE = ROOT / 'assets/ux-history-core.js'


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Patch carburanti non trovato: {label}')
    return text.replace(old, new, 1)


def patch_visual():
    text = VISUAL.read_text(encoding='utf-8')
    text = replace_once(
        text,
        "  const number1 = groupedFormatter({ minimumFractionDigits: 1, maximumFractionDigits: 1 });\n  const number0 = groupedFormatter({ maximumFractionDigits: 0 });",
        "  const number1 = groupedFormatter({ minimumFractionDigits: 1, maximumFractionDigits: 1 });\n  const number2 = groupedFormatter({ minimumFractionDigits: 2, maximumFractionDigits: 2 });\n  const number3 = groupedFormatter({ minimumFractionDigits: 3, maximumFractionDigits: 3 });\n  const number0 = groupedFormatter({ maximumFractionDigits: 0 });",
        'formatter 2/3 decimali',
    )
    old = """    const kind = unitKind(unit);\n    const formatted = kind === 'count' ? number0.format(n) : (Math.abs(n) >= 100 ? number0.format(n) : number1.format(n));\n    if (kind === 'percent') return `${formatted}%`;"""
    new = """    const kind = unitKind(unit);\n    if (kind === 'eurliter') return `${number3.format(n)} €/l`;\n    if (kind === 'eurperresident') return `${number2.format(n)} €/ab`;\n    const formatted = kind === 'count' ? number0.format(n) : (Math.abs(n) >= 100 ? number0.format(n) : number1.format(n));\n    if (kind === 'percent') return `${formatted}%`;"""
    text = replace_once(text, old, new, 'assi carburanti/rifiuti')
    text = text.replace("    if (kind === 'eurliter') return `${formatted} €/l`;\n    if (kind === 'eurperresident') return `${formatted} €/ab`;\n", '')

    # La grammatica visuale può evolvere dopo la release v1.13. Se il ramo
    # carburanti è già presente, non richiedere più la forma storica esatta
    # della funzione scaleFor: il patcher deve restare idempotente.
    if "if (kind === 'eurliter') {" not in text:
        old = """    const allPercent = unitKind(unit) === 'percent' && numeric.every(value => value >= 0 && value <= 100);\n    if (allPercent) return { min: 0, max: 100, kind: 'percent' };\n\n    let min = Math.min(...numeric);\n    let max = Math.max(...numeric);"""
        new = """    const kind = unitKind(unit);\n    if (kind === 'eurliter') {\n      const rawMin = Math.min(...numeric);\n      const rawMax = Math.max(...numeric);\n      const spread = rawMax - rawMin;\n      const padding = Math.max(0.005, spread * 0.25);\n      const min = Math.floor((rawMin - padding) * 1000) / 1000;\n      const max = Math.ceil((rawMax + padding) * 1000) / 1000;\n      return { min, max: max > min ? max : min + 0.010, kind: 'focused' };\n    }\n\n    const allPercent = kind === 'percent' && numeric.every(value => value >= 0 && value <= 100);\n    if (allPercent) return { min: 0, max: 100, kind: 'percent' };\n\n    let min = Math.min(...numeric);\n    let max = Math.max(...numeric);"""
        text = replace_once(text, old, new, 'scala prezzi focalizzata')

    # Anche l'etichetta può essere stata rifattorizzata (per esempio in una
    # variabile scaleLabel). Se contiene già il caso focused, è completa.
    if "scale.kind === 'focused'" not in text:
        old = "scale.kind === 'percent' ? 'scala 0–100%' : scale.kind === 'signed' ? 'lo zero è evidenziato' : 'scala con origine a zero'"
        new = "scale.kind === 'percent' ? 'scala 0–100%' : scale.kind === 'signed' ? 'lo zero è evidenziato' : scale.kind === 'focused' ? 'scala adattata ai prezzi' : 'scala con origine a zero'"
        text = replace_once(text, old, new, 'etichetta scala prezzi')
    VISUAL.write_text(text, encoding='utf-8')


def patch_ux():
    text = UX.read_text(encoding='utf-8')
    text = replace_once(
        text,
        "  const number1 = formatterWithGrouping({ minimumFractionDigits: 1, maximumFractionDigits: 1 });\n  const euro0",
        "  const number1 = formatterWithGrouping({ minimumFractionDigits: 1, maximumFractionDigits: 1 });\n  const number3 = formatterWithGrouping({ minimumFractionDigits: 3, maximumFractionDigits: 3 });\n  const euro0",
        'formatter UX 3 decimali',
    )
    old = """        const part = row.parts?.[index] || {};\n        const value = Number(part.value);\n        let formatted = 'n.d.';\n        if (Number.isFinite(value)) {\n          if (unit === 'currency') formatted = `${number1.format(value)} €`;\n          else if (unit === 'percent') formatted = `${percent1.format(value)}%`;\n          else if (unit === 'per1000') formatted = `${number1.format(value)} ogni 1.000`;\n          else if (unit === 'per100') formatted = `${number1.format(value)} ogni 100`;\n          else if (unit === 'per10k') formatted = `${number1.format(value)} ogni 10.000`;\n          else formatted = number1.format(value);\n        }"""
    new = """        const part = row.parts?.[index] || {};\n        const rawValue = part.value;\n        const value = rawValue === null || rawValue === undefined || rawValue === '' ? undefined : Number(rawValue);\n        let formatted = 'n.d.';\n        if (Number.isFinite(value)) {\n          if (unit === 'currency') formatted = `${number1.format(value)} €`;\n          else if (unit === 'currency2') formatted = `${number1.format(value)} €`;\n          else if (unit === 'eurliter') formatted = `${number3.format(value)} €/l`;\n          else if (unit === 'eurPerResident') formatted = `${number1.format(value)} €/ab`;\n          else if (unit === 'percent') formatted = `${percent1.format(value)}%`;\n          else if (unit === 'per1000') formatted = `${number1.format(value)} ogni 1.000`;\n          else if (unit === 'per100') formatted = `${number1.format(value)} ogni 100`;\n          else if (unit === 'per10k') formatted = `${number1.format(value)} ogni 10.000`;\n          else formatted = number1.format(value);\n        }"""
    text = replace_once(text, old, new, 'valore composito carburanti')
    UX.write_text(text, encoding='utf-8')


def patch_core():
    text = CORE.read_text(encoding='utf-8')
    text = replace_once(
        text,
        "  function formatValue(value, unit) {\n    const number = Number(value);\n    if (!Number.isFinite(number)) return 'n.d.';",
        "  function formatValue(value, unit) {\n    if (value === null || value === undefined || value === '') return 'n.d.';\n    const number = Number(value);\n    if (!Number.isFinite(number)) return 'n.d.';",
        'null non uguale a zero',
    )
    text = replace_once(
        text,
        "      case 'currency': return `${formatNumber(number, 0)} €`;",
        "      case 'currency': return `${formatNumber(number, 0)} €`;\n      case 'currency2': return `${formatNumber(number, 2)} €`;\n      case 'eurliter': return `${formatNumber(number, 3)} €/l`;\n      case 'eurPerResident': return `${formatNumber(number, 2)} €/ab`;",
        'unità UX history core',
    )

    old = """  function comparisonBarsMarkup(metric, selectedSlug = '') {\n    const rows = [...metric.rows].sort((a, b) => Number(b.value) - Number(a.value));\n    const values = rows.map(row => Number(row.value)).filter(Number.isFinite);\n    const min = Math.min(0, ...values), max = Math.max(0, ...values);\n    const range = max - min || 1;\n    const zero = (0 - min) / range * 100;\n\n    return `<div class=\"ux-comparison-bars\">${rows.map((row, index) => {\n      const value = Number(row.value);\n      const start = value >= 0 ? zero : (value - min) / range * 100;\n      const width = Math.max(1, Math.abs(value) / range * 100);\n      const rowSlug = row.slug || slug(row.town);\n      const href = new URL(`comuni/${rowSlug}/?tema=${encodeURIComponent(metric.meta.theme)}&indicatore=${encodeURIComponent(metric.key || '')}`, ROOT).href;\n      return `<a class=\"ux-bar-row ${rowSlug === selectedSlug ? 'selected' : ''}\" href=\"${href}\"><span class=\"ux-bar-rank\">${index + 1}</span><span class=\"ux-bar-town\">${escapeHtml(row.town)}</span><span class=\"ux-bar-track\"><span class=\"ux-bar-zero\" style=\"left:${zero}%\"></span><span class=\"ux-bar-fill\" style=\"left:${start}%;width:${width}%\"></span></span><strong>${escapeHtml(row.formatted || formatValue(value, metric.meta.unit))}</strong></a>`;\n    }).join('')}</div>`;\n  }"""
    new = """  function comparisonBarsMarkup(metric, selectedSlug = '') {\n    const finiteValue = value => value === null || value === undefined || value === '' ? null : (Number.isFinite(Number(value)) ? Number(value) : null);\n    const rows = [...metric.rows].sort((a, b) => {\n      const av = finiteValue(a.value), bv = finiteValue(b.value);\n      if (av === null && bv === null) return String(a.town).localeCompare(String(b.town), 'it');\n      if (av === null) return 1;\n      if (bv === null) return -1;\n      return bv - av;\n    });\n    const values = rows.map(row => finiteValue(row.value)).filter(value => value !== null);\n    const focusedFuel = metric.meta.unit === 'eurliter' && values.length > 0;\n    let min, max;\n    if (focusedFuel) {\n      const rawMin = Math.min(...values), rawMax = Math.max(...values);\n      const spread = rawMax - rawMin;\n      const padding = Math.max(0.005, spread * 0.25);\n      min = Math.floor((rawMin - padding) * 1000) / 1000;\n      max = Math.ceil((rawMax + padding) * 1000) / 1000;\n      if (max <= min) max = min + 0.010;\n    } else {\n      min = Math.min(0, ...values);\n      max = Math.max(0, ...values);\n    }\n    const range = max - min || 1;\n    const zero = focusedFuel ? 0 : (0 - min) / range * 100;\n\n    const markup = rows.map((row, index) => {\n      const value = finiteValue(row.value);\n      const rowSlug = row.slug || slug(row.town);\n      const href = new URL(`comuni/${rowSlug}/?tema=${encodeURIComponent(metric.meta.theme)}&indicatore=${encodeURIComponent(metric.key || '')}`, ROOT).href;\n      if (value === null) {\n        return `<a class=\"ux-bar-row missing ${rowSlug === selectedSlug ? 'selected' : ''}\" href=\"${href}\"><span class=\"ux-bar-rank\">—</span><span class=\"ux-bar-town\">${escapeHtml(row.town)}</span><span class=\"ux-bar-track\"></span><strong>n.d.</strong></a>`;\n      }\n      const valuePosition = (value - min) / range * 100;\n      const start = focusedFuel ? 0 : (value >= 0 ? zero : valuePosition);\n      const width = focusedFuel ? Math.max(1, valuePosition) : Math.max(1, Math.abs(value) / range * 100);\n      return `<a class=\"ux-bar-row ${rowSlug === selectedSlug ? 'selected' : ''}\" href=\"${href}\"><span class=\"ux-bar-rank\">${index + 1}</span><span class=\"ux-bar-town\">${escapeHtml(row.town)}</span><span class=\"ux-bar-track\">${focusedFuel ? '' : `<span class=\"ux-bar-zero\" style=\"left:${zero}%\"></span>`}<span class=\"ux-bar-fill\" style=\"left:${start}%;width:${width}%\"></span></span><strong>${escapeHtml(row.formatted || formatValue(value, metric.meta.unit))}</strong></a>`;\n    }).join('');\n    const note = focusedFuel ? `<p class=\"comparison-note\">Scala adattata all’intervallo dei prezzi: non parte da zero, così le differenze di pochi centesimi restano leggibili.</p>` : '';\n    return `<div class=\"ux-comparison-bars\">${markup}</div>${note}`;\n  }"""
    text = replace_once(text, old, new, 'barre carburanti UX')
    CORE.write_text(text, encoding='utf-8')


def main():
    patch_visual()
    patch_ux()
    patch_core()
    print('Fuel UI patched: 3 decimals, n.d. preserved, focused price scale')


if __name__ == '__main__':
    main()
