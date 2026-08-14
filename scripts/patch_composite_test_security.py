#!/usr/bin/env python3
from pathlib import Path

path = Path('scripts/test_composite_indicators.py')
text = path.read_text(encoding='utf-8')
text = text.replace('"""Verifica dati, UI e responsive dei tre indicatori compositi."""', '"""Verifica dati, UI e responsive degli indicatori compositi."""')
text = text.replace(
    'COMPOSITE_KEYS = {"ageDistribution", "internalResidentialMobility", "incomeDistribution", "foreignResidents", "foreignResidentialMobility", "totalResidentialMobility", "omiResidential"}',
    'COMPOSITE_KEYS = {"ageDistribution", "internalResidentialMobility", "incomeDistribution", "foreignResidents", "foreignResidentialMobility", "totalResidentialMobility", "omiResidential", "roadSafety", "roadFinesPerResident"}'
)
text = text.replace('    assert len(data["metrics"]) == 119\n', '    assert len(data["metrics"]) == registry["expectedMetricCount"]\n')
text = text.replace('    assert len(data["metrics"]) - len(external_metrics) == 115\n', '    assert len(data["metrics"]) - len(external_metrics) == registry["expectedInlineMetricCount"]\n')
anchor = '''    mobility = data["metrics"]["internalResidentialMobility"]
    assert mobility["meta"]["theme"] == "demografia"'''
insert = '''    road_safety = data["metrics"]["roadSafety"]
    assert road_safety["meta"]["compositeType"] == "securityMeasures"
    assert [part["unit"] for part in road_safety["rows"][0]["parts"]] == ["per1000", "per100", "per100", "per10k"]
    assert all(len(row["parts"]) == 4 for row in road_safety["rows"])
    road_fines = data["metrics"]["roadFinesPerResident"]
    assert road_fines["meta"]["compositeType"] == "securityMeasures"
    assert [part["unit"] for part in road_fines["rows"][0]["parts"]] == ["currency", "percent"]
    assert all(len(row["parts"]) == 2 for row in road_fines["rows"])

    mobility = data["metrics"]["internalResidentialMobility"]
    assert mobility["meta"]["theme"] == "demografia"'''
if insert not in text:
    if anchor not in text:
        raise RuntimeError('Anchor static security non trovato')
    text = text.replace(anchor, insert, 1)

browser_anchor = '''        page.goto(base + "confronta/demografia/?indicatore=internalResidentialMobility", wait_until="networkidle")'''
browser_insert = '''        for metric_key, option_count in (("roadSafety", 4), ("roadFinesPerResident", 2)):
            page.goto(base + f"confronta/sicurezza/?indicatore={metric_key}", wait_until="networkidle")
            page.wait_for_selector("select[data-composite-component]")
            component = page.locator("select[data-composite-component]")
            assert component.locator("option").count() == option_count
            assert page.locator("#compare-bars .bar-row").count() == 7
            first_axis = page.locator("#compare-bars .comparison-axis").inner_text()
            component.select_option(f"part-{option_count - 1}")
            page.wait_for_function(
                "choice => document.querySelector('#compare-bars .comparison-bars')?.dataset.compositeChoice === choice",
                arg=f"part-{option_count - 1}",
            )
            changed_axis = page.locator("#compare-bars .comparison-axis").inner_text()
            assert first_axis != changed_axis

        page.goto(base + "confronta/demografia/?indicatore=internalResidentialMobility", wait_until="networkidle")'''
if browser_insert not in text:
    if browser_anchor not in text:
        raise RuntimeError('Anchor browser security non trovato')
    text = text.replace(browser_anchor, browser_insert, 1)

path.write_text(text, encoding='utf-8')
print('test_composite_indicators.py allineato')
