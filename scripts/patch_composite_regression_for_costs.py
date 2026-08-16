#!/usr/bin/env python3
"""Align legacy regressions with the draft economy extension.

Temporary draft helper: production tests still encode the pre-extension
Economia/Redditi catalog, the old generic 'Reddito medio' wording and the
old two-point income history exported to PDF. Keep those canonical tests
unchanged in the repository and adapt their expectations only inside the
economy draft workflow.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSITE_TEST = ROOT / 'scripts' / 'test_composite_indicators.py'
EXPORT_TEST = ROOT / 'scripts' / 'test_exports_v161.py'
UX_TEST = ROOT / 'scripts' / 'test_ux_experiment.py'

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

ux_text = UX_TEST.read_text(encoding='utf-8')
old_income_history = '''        require(page.locator(".ux-two-point-row").count() == 7,\n                "Economia: confronto a due punti incompleto")\n        require("Confronto a due punti 2023–2024" in page.locator(".ux-history-head").inner_text(),\n                "Economia: intervallo a due punti non riconosciuto")'''
new_income_history = '''        require(page.locator(".ux-series-group").count() == 7,\n                "Economia: serie storica lunga incompleta")\n        require("Andamento 2011–2024" in page.locator(".ux-history-head").inner_text(),\n                "Economia: intervallo storico lungo non riconosciuto")'''
if old_income_history in ux_text:
    ux_text = ux_text.replace(old_income_history, new_income_history, 1)
elif new_income_history not in ux_text:
    raise RuntimeError('UX regression long-income anchor missing')

municipal_check = '''\n        page.goto(\n            base + "comuni/massarosa/?tema=economia&indicatore=income",\n            wait_until="networkidle",\n        )\n        page.wait_for_selector(".history-panel .ux-view-shell")\n        real_income_button = page.locator('[data-metric="incomeVsInflation"]')\n        require(real_income_button.count() == 1 and real_income_button.is_visible(),\n                "Scheda comunale Economia: pulsante Redditi vs inflazione assente")\n        real_income_button.click()\n        page.wait_for_selector('[data-metric="incomeVsInflation"].active')\n        require("indicatore=incomeVsInflation" in page.url,\n                "Scheda comunale Economia: click Redditi vs inflazione non aggiorna l’indicatore")\n        require("Redditi vs inflazione" in page.locator("#town-topic").inner_text(),\n                "Scheda comunale Economia: contenuto Redditi vs inflazione non renderizzato")\n        real_history_button = page.locator('.history-panel [data-view-mode="history"]')\n        require(not real_history_button.is_disabled(),\n                "Scheda comunale Economia: storico Redditi vs inflazione disabilitato")\n        real_history_button.click()\n        require(page.locator('.history-panel .ux-view-pane[data-view-pane="history"]').is_visible(),\n                "Scheda comunale Economia: storico Redditi vs inflazione non attivabile")\n        require(page.locator(".history-panel .ux-series-group").count() == 7,\n                "Scheda comunale Economia: storico Redditi vs inflazione incompleto")\n        require("Andamento 2016–2024" in page.locator(".history-panel .ux-history-head").inner_text(),\n                "Scheda comunale Economia: intervallo Redditi vs inflazione errato")\n'''
municipal_anchor = '''        require("Andamento 2011–2024" in page.locator(".ux-history-head").inner_text(),\n                "Economia: intervallo storico lungo non riconosciuto")\n'''
if municipal_check.strip() not in ux_text:
    if municipal_anchor not in ux_text:
        raise RuntimeError('UX regression municipal-income insertion anchor missing')
    ux_text = ux_text.replace(municipal_anchor, municipal_anchor + municipal_check, 1)
UX_TEST.write_text(ux_text, encoding='utf-8')

print('Legacy regression expectations aligned with economy draft')
