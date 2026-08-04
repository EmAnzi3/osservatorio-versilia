#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

PAYLOAD = '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'

files = json.loads(gzip.decompress(base64.b64decode(PAYLOAD)).decode("utf-8"))
for rel, content in files.items():
    path = Path(rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

build_path = Path("scripts/build_static.py")
build = build_path.read_text(encoding="utf-8")
if '"welfare",' not in build:
    old = '    "salute",\n]'
    new = '    "salute",\n    "welfare",\n]'
    if old not in build:
        raise RuntimeError("Elenco dei temi non riconosciuto in build_static.py")
    build = build.replace(old, new, 1)
build_path.write_text(build, encoding="utf-8")

test_path = Path("scripts/test_static.py")
test = test_path.read_text(encoding="utf-8")
test = test.replace(
    'assert len(html_files) >= 20, f"Pagine HTML insufficienti: {len(html_files)}"',
    'assert len(html_files) >= 21, f"Pagine HTML insufficienti: {len(html_files)}"',
)

static_marker = "    # V1.2_LOCAL_STATIC_ASSERTIONS\n"
if static_marker not in test:
    anchor = '    assert "Massarosa" in massarosa\n    assert "Fonte" in massarosa or "fonte" in massarosa\n'
    block = (
        anchor
        + static_marker
        + '    welfare_path = DIST / "confronta" / "welfare" / "index.html"\n'
        + '    assert welfare_path.exists(), "Pagina Welfare assente"\n'
        + '    welfare_html = welfare_path.read_text(encoding="utf-8")\n'
        + '    assert "Welfare e servizi" in welfare_html, "Titolo Welfare assente"\n'
        + '    assert "Copertura dei servizi per l’infanzia" in welfare_html, "Indicatore nidi assente"\n'
        + '    assert "Copertura FTTH" in welfare_html, "Indicatore FTTH assente"\n'
    )
    if anchor not in test:
        raise RuntimeError("Punto di inserimento statico non riconosciuto in test_static.py")
    test = test.replace(anchor, block, 1)

bundle_marker = "    # V1.2_LOCAL_BUNDLE_ASSERTIONS\n"
if bundle_marker not in test:
    anchor = "    assert bundle.count(\"useGrouping: 'always'\") >= 4, \"Raggruppamento delle migliaia non forzato\"\n"
    block = (
        anchor
        + bundle_marker
        + '    for token in ["welfare:", "nurseryCoverage", "omiSaleMin", "metric-catalog"]:\n'
        + '        assert token in bundle, f"Elemento v1.2 assente dal bundle: {token}"\n'
    )
    if anchor not in test:
        raise RuntimeError("Punto di inserimento bundle non riconosciuto in test_static.py")
    test = test.replace(anchor, block, 1)

browser_marker = "        # V1.2_LOCAL_BROWSER_ASSERTIONS\n"
if browser_marker not in test:
    anchor = '        assert 68 <= nav_top <= 72, f"Navigazione temi non sticky: {nav_top}"\n\n'
    block = (
        anchor
        + browser_marker
        + '        page.goto(base + "confronta/welfare/", wait_until="networkidle")\n'
        + '        page.wait_for_selector(".topic-dashboard")\n'
        + '        assert page.locator("h1").first.text_content().strip() == "Welfare e servizi"\n'
        + '        assert page.locator(".metric-catalog .metric-group").count() >= 4, "Catalogo Welfare non raggruppato"\n'
        + '        assert page.locator("[data-metric=\\"nurseryCoverage\\"]").count() >= 1\n'
        + '        assert page.locator("[data-metric=\\"ftthCoverage\\"]").count() >= 1\n\n'
    )
    if anchor not in test:
        raise RuntimeError("Punto di inserimento browser non riconosciuto in test_static.py")
    test = test.replace(anchor, block, 1)

mobile_marker = "        # V1.2_LOCAL_MOBILE_ASSERTIONS\n"
if mobile_marker not in test:
    anchor = '        mobile_page.wait_for_selector(".global-search-trigger")\n'
    block = (
        anchor
        + mobile_marker
        + '        assert mobile_page.locator(".theme-card").count() == 10, "La home non mostra 10 temi"\n'
        + "        welfare_card = mobile_page.locator('.theme-card[data-theme=\"welfare\"]')\n" 
        + '        assert welfare_card.count() == 1 and welfare_card.is_visible(), "Carta Welfare assente su smartphone"\n'
    )
    if anchor not in test:
        raise RuntimeError("Punto di inserimento mobile non riconosciuto in test_static.py")
    test = test.replace(anchor, block, 1)

test_path.write_text(test, encoding="utf-8")
print(f"UI locale v1.2 applicata: {len(files)} file, tema Welfare e test estesi")
