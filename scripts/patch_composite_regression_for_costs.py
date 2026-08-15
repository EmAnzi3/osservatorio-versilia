#!/usr/bin/env python3
"""Align legacy regressions with the draft economy extension.

Temporary draft helper: production tests still encode the pre-extension
Economia/Redditi catalog, the old generic 'Reddito medio' wording and the
old two-point income history exported to PDF.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSITE_TEST = ROOT / 'scripts' / 'test_composite_indicators.py'
EXPORT_TEST = ROOT / 'scripts' / 'test_exports_v161.py'

text = COMPOSITE_TEST.read_text(encoding='utf-8')
replacements = {
    '''    assert data["themes"]["economia"]["sections"][0]["metrics"] == [\n        "income", "incomeDistribution",\n    ]''': '''    assert data["themes"]["economia"]["sections"][0]["metrics"] == [\n        "income", "incomeDistribution", "incomeVsInflation",\n    ]''',
    '''        aggregate_prefix = "Età media" if choice == "summary" and metric_key == "ageDistribution" else "Reddito medio" if choice == "summary" else "Versilia ·"''': '''        aggregate_prefix = "Età media" if choice == "summary" and metric_key == "ageDistribution" else "Reddito complessivo medio" if choice == "summary" else "Versilia ·"''',
    '''        assert all("Reddito medio" in text for text in page.locator(".composite-row-head > span").all_text_contents())''': '''        assert all("Reddito complessivo medio" in text for text in page.locator(".composite-row-head > span").all_text_contents())''',
}
for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise RuntimeError(f'Composite regression anchor missing: {old[:80]!r}')
COMPOSITE_TEST.write_text(text, encoding='utf-8')

export_text = EXPORT_TEST.read_text(encoding='utf-8')
old_export = '("confronta/economia/?indicatore=income", "economia.pdf", "Confronto a due punti 2023–2024")'
new_export = '("confronta/economia/?indicatore=income", "economia.pdf", "2011–2024")'
if old_export in export_text:
    export_text = export_text.replace(old_export, new_export, 1)
elif new_export not in export_text:
    raise RuntimeError('Export regression income-history anchor missing')
EXPORT_TEST.write_text(export_text, encoding='utf-8')

print('Legacy regression expectations aligned with economy draft')
