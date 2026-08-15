#!/usr/bin/env python3
"""Align the existing composite-indicator regression with the draft economy extension.

Temporary draft helper: the production test still encodes the pre-extension
Economia/Redditi catalog and the old generic 'Reddito medio' wording.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / 'scripts' / 'test_composite_indicators.py'

text = TEST.read_text(encoding='utf-8')
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
TEST.write_text(text, encoding='utf-8')
print('Composite regression expectations aligned with economy draft')
