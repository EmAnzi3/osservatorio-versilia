#!/usr/bin/env python3
"""Abilita pan e pinch Leaflet sui dispositivi touch e aggiorna il relativo gate."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: punto di aggancio non univoco ({count}) in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    guard = ROOT / "percorsi/mobile-scroll-guard.js"
    replace_once(guard,
        '''    if (mobile) {
      percorsiMap.dragging?.disable();
      percorsiMap.touchZoom?.disable();
      percorsiMap.scrollWheelZoom?.disable();
      container.dataset.mobileScrollSafe = 'true';
    } else {''',
        '''    if (mobile) {
      percorsiMap.dragging?.enable();
      percorsiMap.touchZoom?.enable();
      percorsiMap.scrollWheelZoom?.disable();
      container.dataset.mobileMapInteractive = 'true';
      delete container.dataset.mobileScrollSafe;
    } else {''', "Leaflet mobile")
    replace_once(guard,
        "      delete container.dataset.mobileScrollSafe;\n    }\n",
        "      delete container.dataset.mobileScrollSafe;\n      delete container.dataset.mobileMapInteractive;\n    }\n", "cleanup Leaflet")

    css = ROOT / "percorsi/osservatorio.css"
    replace_once(css,
        '''  body.percorsi-page #map{
    touch-action:pan-y pinch-zoom!important;
  }''',
        '''  body.percorsi-page #map{
    touch-action:none!important;
  }''', "touch-action")

    test = ROOT / "scripts/test_percorsi_mobile_list_contract.py"
    replace_once(test,
        "    require(runtime['dragging'] is False, f'Leaflet dragging deve essere disattivato su mobile in {label}: {runtime}')\n    require(runtime['touchZoom'] is False, f'Leaflet touchZoom deve essere disattivato su mobile in {label}: {runtime}')",
        "    require(runtime['dragging'] is True, f'Leaflet dragging deve essere attivo su mobile in {label}: {runtime}')\n    require(runtime['touchZoom'] is True, f'Leaflet touchZoom deve essere attivo su mobile in {label}: {runtime}')", "assert Leaflet")
    replace_once(test,
        "    require('pan-y' in runtime['touchAction'], f'La mappa deve consentire lo scroll verticale della pagina in {label}: {runtime}')",
        "    require(runtime['touchAction'] == 'none', f'La mappa deve catturare pan e pinch touch in {label}: {runtime}')", "assert touch-action")
    replace_once(test, "from playwright.sync_api import sync_playwright\n", "from playwright.sync_api import sync_playwright\nfrom test_percorsi_touch_gestures import verify_touch_gestures\n", "import touch test")
    replace_once(test,
        "        assert_mobile_list_contract(page, '360x800')\n\n        browser.close()",
        "        assert_mobile_list_contract(page, '360x800')\n        verify_touch_gestures(page, '360x800')\n\n        browser.close()", "run touch test")
    replace_once(test,
        "print('Contratto Percorsi mobile: lista utilizzabile, scroll di pagina recuperabile dalla mappa e controllo ↑ Percorsi sempre disponibile.')",
        "print('Contratto Percorsi mobile: lista utilizzabile, pan/pinch Leaflet attivi e controllo ↑ Percorsi sempre disponibile.')", "test message")
    print("Interazioni touch Percorsi materializzate.")


if __name__ == "__main__":
    main()
