#!/usr/bin/env python3
"""Allinea cache, build e contratto release alla v1.20.0 del lotto agricoltura."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(path: str, old: str, new: str, *, required: bool = True) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        if required:
            raise RuntimeError(f"Pattern non trovato in {path}: {old}")
        return
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    # Pre-allinea il loader: il materializzatore riconosce questa forma idempotente.
    p = ROOT / "assets/app.js"
    text = p.read_text(encoding="utf-8")
    if "20260826-v120" not in text:
        if "const VERSION = '20260826-v119';" in text:
            text = text.replace("const VERSION = '20260826-v119';", "const VERSION='20260826-v120';", 1)
        elif "const VERSION='20260826-v119';" in text:
            text = text.replace("const VERSION='20260826-v119';", "const VERSION='20260826-v120';", 1)
        else:
            raise RuntimeError("VERSION v119 non trovata in assets/app.js")
        p.write_text(text, encoding="utf-8")

    patch("scripts/build_static_safe.py", 'UX_ASSET_VERSION = "20260826-v119"', 'UX_ASSET_VERSION = "20260826-v120"')
    patch("scripts/build_static_brand.py", 'APP_BUNDLE_ASSET_VERSION = "20260826-v119"', 'APP_BUNDLE_ASSET_VERSION = "20260826-v120"')
    patch("scripts/build_static_brand.py", 'CHART_SURFACE_ASSET_VERSION = "20260826-v119"', 'CHART_SURFACE_ASSET_VERSION = "20260826-v120"')
    patch("scripts/build_static_brand.py", 'PWA_JS_REVISION = "catalog-v119"', 'PWA_JS_REVISION = "catalog-v120"')
    patch("service-worker.js", "ov-pwa-20260826-v119", "ov-pwa-20260826-v120")

    release_row = "      ['2026.08.26-v1.20.0','26 agosto 2026','154 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunto Agricoltura e territorio: aziende agricole, SAU territoriale e quota comunale, dimensione media aziendale, profilo colture e superficie irrigata dal 7° Censimento Istat 2020.'],\n"
    project = ROOT / "assets/app-parts/05.txt"
    text = project.read_text(encoding="utf-8")
    if "2026.08.26-v1.20.0" not in text:
        anchor = "      ['2026.08.26-v1.19.0','26 agosto 2026','149 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunti tre indicatori TPL programmato 7/7 da GTFS regionali: corse, punti di accesso attivi e ampiezza oraria del servizio.'],\n"
        if anchor not in text:
            raise RuntimeError("Riga release v1.19.0 non trovata")
        project.write_text(text.replace(anchor, release_row + anchor, 1), encoding="utf-8")

    test = ROOT / "scripts/test_catalog_release_v116.py"
    text = test.read_text(encoding="utf-8")
    replacements = {
        'release v1.19.0': 'release v1.20.0',
        'assert "2026.08.26-v1.19.0" in app and "149 indicatori complessivi" in app': 'assert "2026.08.26-v1.20.0" in app and "154 indicatori complessivi" in app',
        'assert "**v1.19.0** — 26 agosto 2026" in readme': 'assert "**v1.20.0** — 26 agosto 2026" in readme',
        'assert "149 indicatori" in readme and "145 con valori incorporati" in readme': 'assert "154 indicatori" in readme and "150 con valori incorporati" in readme',
        'assert \'UX_ASSET_VERSION = "20260826-v119"\' in build_safe': 'assert \'UX_ASSET_VERSION = "20260826-v120"\' in build_safe',
        'assert \'APP_BUNDLE_ASSET_VERSION = "20260826-v119"\' in build_brand': 'assert \'APP_BUNDLE_ASSET_VERSION = "20260826-v120"\' in build_brand',
        'assert \'CHART_SURFACE_ASSET_VERSION = "20260826-v119"\' in build_brand': 'assert \'CHART_SURFACE_ASSET_VERSION = "20260826-v120"\' in build_brand',
        'assert \'PWA_JS_REVISION = "catalog-v119"\' in build_brand': 'assert \'PWA_JS_REVISION = "catalog-v120"\' in build_brand',
        'assert "const VERSION = \'20260826-v119\'" in development_loader': 'assert "20260826-v120" in development_loader',
        'assert "ov-pwa-20260826-v119" in service_worker': 'assert "ov-pwa-20260826-v120" in service_worker',
    }
    for old, new in replacements.items():
        if new in text:
            continue
        if old not in text:
            raise RuntimeError(f"Contratto release: pattern non trovato: {old}")
        text = text.replace(old, new, 1)
    test.write_text(text, encoding="utf-8")

    print("Contratto release v1.20.0 allineato.")


if __name__ == "__main__":
    main()
