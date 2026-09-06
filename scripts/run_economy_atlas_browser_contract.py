#!/usr/bin/env python3
"""Esegue il contratto browser v1.31 aggiungendo territorio, tooltip OV ed export."""
from __future__ import annotations

import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent / "test_economy_atlas_browser.py"
spec = importlib.util.spec_from_file_location("atlas_base_contract", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError("Contratto browser Atlante non caricabile")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)

_original_standalone = contract.test_standalone


def assert_tooltip_style(host):
    tooltip = host.locator(".ov-site-tooltip")
    tooltip.wait_for(state="visible", timeout=3000)
    styles = tooltip.evaluate(
        """el => {
          const s=getComputedStyle(el), y=getComputedStyle(el.querySelector('.chart-tooltip-year')), v=getComputedStyle(el.querySelector('.chart-tooltip-value'));
          return {background:s.backgroundColor,radius:s.borderRadius,year:y.fontSize,value:v.fontSize};
        }"""
    )
    assert styles == {
        "background": "rgb(16, 47, 69)",
        "radius": "8px",
        "year": "9px",
        "value": "11px",
    }, styles


def assert_csv_download(page, host, territory_slug: str, territory_name: str):
    button = host.locator("#atlasDownloadCsv")
    assert button.is_visible()
    with page.expect_download(timeout=10000) as info:
        button.click()
    download = info.value
    assert download.suggested_filename == f"atlante-attivita-economiche-{territory_slug}-2014-2025.csv"
    path = download.path()
    assert path is not None
    text = Path(path).read_text(encoding="utf-8-sig")
    assert text.startswith("Territorio;Codice ATECO;Livello;Descrizione;Anno;UL attive;UL artigiane (2025);Fonte")
    assert f"{territory_name};A;Sezione;" in text
    assert "Regione Toscana / Registro Imprese InfoCamere" in text


def test_standalone(page, base: str, width: int):
    _original_standalone(page, base, width)
    if width != 1440:
        return

    # Il contratto base termina su un nodo ATECO profondo. Ricarichiamo la
    # vista root per verificare export e tooltip su una pagina pulita.
    page.goto(base + contract.ATLAS_ROUTE, wait_until="networkidle")
    contract.wait_atlas(page)
    host = page.locator("ov-economy-atlas")

    assert host.locator(".atlas-export-actions button").count() == 2
    assert_csv_download(page, host, "versilia", "Versilia")
    page.evaluate("window.__atlasPrintCalled=false; window.print=()=>{window.__atlasPrintCalled=true}")
    host.locator("#atlasPrint").click()
    assert page.evaluate("window.__atlasPrintCalled") is True

    first_slice = host.locator("#donut .slice[data-atlas-tooltip]").first
    first_slice.wait_for(state="visible", timeout=5000)
    assert host.locator("#donut .slice title").count() == 0
    first_slice.hover()
    assert_tooltip_style(host)

    contract.choose_code(page, "68.31")
    lrow = host.locator("#analysis .lrow[data-atlas-tooltip]").first
    lrow.wait_for(state="visible", timeout=5000)
    assert lrow.get_attribute("title") is None
    lrow.hover()
    assert_tooltip_style(host)

    host.locator("#tabHistory").click()
    dot = host.locator("#analysis .trenddot[data-atlas-tooltip]").first
    dot.wait_for(state="visible", timeout=5000)
    dot.hover()
    assert_tooltip_style(host)
    assert host.locator("#analysis .trenddot title").count() == 0
    host.locator("#tabCurrent").click()


def test_territory(page, base: str):
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.goto(base + contract.ATLAS_ROUTE + "?comune=viareggio", wait_until="networkidle")
    contract.wait_atlas(page)
    host = page.locator("ov-economy-atlas")
    territory = host.locator("#territory")
    assert territory.input_value() == "viareggio"
    center = host.locator("#donutCenter").inner_text()
    assert "Viareggio" in center and "7.809" in center, center
    assert "Viareggio" in host.locator(".hero h1").inner_text()
    assert "Viareggio" in host.locator(".quick-title").inner_text()
    assert_csv_download(page, host, "viareggio", "Viareggio")

    contract.choose_code(page, "68.31")
    assert "Viareggio" in host.locator("#analysisHeading").inner_text()

    # Il cambio territorio conserva il nodo ATECO selezionato: cambia il contesto, non la domanda.
    territory.select_option("massarosa")
    page.wait_for_timeout(150)
    assert "comune=massarosa" in page.url
    selected = host.locator("#analysis .selected-title code").first.inner_text()
    assert "68.31" in selected, selected
    assert "Massarosa" in host.locator("#analysisHeading").inner_text()
    assert "Massarosa" in host.locator(".hero h1").inner_text()
    assert "Massarosa" in host.locator(".quick-title").inner_text()

    territory.select_option("")
    page.wait_for_timeout(150)
    assert "comune=" not in page.url
    selected = host.locator("#analysis .selected-title code").first.inner_text()
    assert "68.31" in selected, selected
    assert "Versilia" in host.locator(".quick-title").inner_text()
    assert "Massarosa" not in host.locator(".hero h1").inner_text()
    contract.assert_atlas_no_overflow(page)


contract.test_standalone = test_standalone
contract.test_territory = test_territory

if __name__ == "__main__":
    contract.main()
