#!/usr/bin/env python3
"""Keep the economy context legend separate from composite-indicator semantics."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP05 = ROOT / 'assets' / 'app-parts' / '05.txt'
CSS = ROOT / 'assets' / 'fidelity.css'

app = APP05.read_text(encoding='utf-8')
old = '<div class="composite-legend"><span>━ ${html(c.incomeLabel)}</span><span>┅ ${html(c.priceLabel)}</span><span>┈ ${html(c.realLabel)}</span></div>'
new = '<div class="income-inflation-legend"><span>━ ${html(c.incomeLabel)}</span><span>┅ ${html(c.priceLabel)}</span><span>┈ ${html(c.realLabel)}</span></div>'
if old in app:
    app = app.replace(old, new, 1)
elif new not in app:
    raise RuntimeError('Income/inflation legend markup not found')
APP05.write_text(app, encoding='utf-8')

css = CSS.read_text(encoding='utf-8')
rule = '''
/* Economy context legend: visually aligned with chart legends, but deliberately
   not a .composite-legend because it is not part of a composite indicator. */
.income-inflation-legend{display:flex;flex-wrap:wrap;gap:8px 15px;margin:0 0 20px;padding-bottom:14px;border-bottom:1px solid var(--theme-line,#d5dddb)}
.income-inflation-legend span{display:inline-flex;align-items:center;gap:6px;color:var(--muted);font-size:9px;font-weight:700}
'''
if '.income-inflation-legend{' not in css:
    css += '\n' + rule
CSS.write_text(css, encoding='utf-8')
print('Income/inflation legend isolated from composite indicator DOM')
