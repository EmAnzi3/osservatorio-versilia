#!/usr/bin/env python3
"""Build di produzione con identità OV, PWA e Radar Opportunità pubblico."""
from __future__ import annotations

import json
import os
import re
import runpy
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BRAND_ASSET_VERSION = "20260824-ov4"
APP_BUNDLE_ASSET_VERSION = "20260830-v124-water-ui3"
PWA_ASSET_VERSION = "20260824-pwa9"
PWA_JS_REVISION = "catalog-v124"
MOBILE_ACCORDION_ASSET_VERSION = "20260809-3"
CHART_SURFACE_ASSET_VERSION = "20260826-v120"
OLD_MARK = '<span class="site-brand-mark">O</span>'
PWA_FILES = ("service-worker.js", "offline.html", "site.webmanifest")
PWA_ICONS = (
    "icon-180.png",
    "icon-192.png",
    "icon-512.png",
    "icon-maskable-512.png",
)


def decorative_mark() -> str:
    svg = (ROOT / "assets" / "brand-mark.svg").read_text(encoding="utf-8").strip()
    svg = re.sub(r"\s+role=\"img\"\s+aria-labelledby=\"[^\"]+\"", "", svg, count=1)
    svg = re.sub(r"\s*<title[^>]*>.*?</title>\s*", "", svg, flags=re.DOTALL)
    svg = re.sub(r"\s*<desc[^>]*>.*?</desc>\s*", "", svg, flags=re.DOTALL)
    svg = svg.replace(
        "<svg ",
        '<svg class="ov-mark-svg" aria-hidden="true" focusable="false" ',
        1,
    )
    return f'<span class="site-brand-mark" aria-hidden="true">{svg}</span>'


def inject_brand_styles(document: str, relative_root: str) -> str:
    token = "assets/brand.css"
    if token not in document:
        href = f"{relative_root}{token}?v={BRAND_ASSET_VERSION}"
        document = document.replace(
            "</head>",
            f'  <link rel="stylesheet" href="{href}">\n</head>',
        )
    return document


def inject_mobile_accordion_styles(document: str, relative_root: str) -> str:
    token = "assets/mobile-accordion-fix.css"
    if token not in document:
        href = f"{relative_root}{token}?v={MOBILE_ACCORDION_ASSET_VERSION}"
        document = document.replace(
            "</head>",
            f'  <link rel="stylesheet" href="{href}">\n</head>',
        )
    return document


def inject_chart_surface_styles(document: str, relative_root: str) -> str:
    token = "assets/chart-surfaces.css"
    if token not in document:
        href = f"{relative_root}{token}?v={CHART_SURFACE_ASSET_VERSION}"
        document = document.replace(
            "</head>",
            f'  <link rel="stylesheet" href="{href}">\n</head>',
        )
    return document


def cache_bust_favicon(document: str) -> str:
    return re.sub(
        r'href="([^"?]*favicon\.svg)(?:\?[^\"]*)?"',
        rf'href="\1?v={BRAND_ASSET_VERSION}"',
        document,
    )


def cache_bust_app_bundle(document: str) -> str:
    return re.sub(
        r'src="([^"?]*assets/app-bundle\.js)(?:\?[^\"]*)?"',
        rf'src="\1?v={APP_BUNDLE_ASSET_VERSION}"',
        document,
    )


def ensure_pwa_files() -> None:
    """Copia esplicitamente gli asset PWA nella build, indipendentemente dal builder base."""
    DIST.mkdir(parents=True, exist_ok=True)
    for name in PWA_FILES:
        source = ROOT / name
        if not source.exists():
            raise RuntimeError(f"File PWA sorgente mancante: {source}")
        shutil.copy2(source, DIST / name)

    target_dir = DIST / "pwa"
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in PWA_ICONS:
        source = ROOT / "pwa" / name
        if not source.exists():
            raise RuntimeError(f"Icona PWA sorgente mancante: {source}")
        shutil.copy2(source, target_dir / name)


def inject_pwa(document: str, relative_root: str) -> str:
    """Aggiunge metadata Apple/Android, CSS e bootstrap PWA a una pagina del sito."""
    document = re.sub(
        r'<meta\s+name="theme-color"\s+content="[^"]*"\s*/?>',
        '<meta name="theme-color" content="#0F3654">',
        document,
        flags=re.IGNORECASE,
    )

    metadata = []
    if 'name="theme-color"' not in document:
        metadata.append('<meta name="theme-color" content="#0F3654">')
    if 'name="mobile-web-app-capable"' not in document:
        metadata.append('<meta name="mobile-web-app-capable" content="yes">')
    if 'name="apple-mobile-web-app-capable"' not in document:
        metadata.append('<meta name="apple-mobile-web-app-capable" content="yes">')
    if 'name="apple-mobile-web-app-status-bar-style"' not in document:
        metadata.append('<meta name="apple-mobile-web-app-status-bar-style" content="default">')
    if 'name="apple-mobile-web-app-title"' not in document:
        metadata.append('<meta name="apple-mobile-web-app-title" content="Osservatorio Versilia">')
    if 'rel="apple-touch-icon"' not in document:
        metadata.append(
            f'<link rel="apple-touch-icon" sizes="180x180" '
            f'href="{relative_root}pwa/icon-180.png?v={PWA_ASSET_VERSION}">'
        )
    if metadata:
        document = document.replace("</head>", "  " + "\n  ".join(metadata) + "\n</head>")

    document = re.sub(
        r'href="([^"?]*site\.webmanifest)(?:\?[^\"]*)?"',
        rf'href="\1?v={PWA_ASSET_VERSION}"',
        document,
    )

    if "assets/pwa.css" not in document:
        document = document.replace(
            "</head>",
            f'  <link rel="stylesheet" href="{relative_root}assets/pwa.css?v={PWA_ASSET_VERSION}">\n</head>',
        )

    if "assets/pwa.js" not in document:
        document = document.replace(
            "</body>",
            f'  <script src="{relative_root}assets/pwa.js?v={PWA_ASSET_VERSION}&rev={PWA_JS_REVISION}" defer></script>\n</body>',
        )
    return document


def apply_brand_and_pwa() -> None:
    ensure_pwa_files()
    mark = decorative_mark()

    bundle_path = DIST / "assets" / "app-bundle.js"
    bundle = bundle_path.read_text(encoding="utf-8")
    if OLD_MARK in bundle:
        bundle = bundle.replace(OLD_MARK, mark)
    elif 'class="ov-mark-svg"' not in bundle:
        raise RuntimeError("Marchio precedente non trovato nell'app bundle")
    bundle_path.write_text(bundle, encoding="utf-8")

    html_files = list(DIST.rglob("*.html"))
    if not html_files:
        raise RuntimeError("Nessuna pagina HTML trovata nella build")
    site_pages = [path for path in html_files if path.name != "offline.html"]

    for path in site_pages:
        text = path.read_text(encoding="utf-8")
        if OLD_MARK in text:
            text = text.replace(OLD_MARK, mark)
        prefix = os.path.relpath(DIST, path.parent).replace(os.sep, "/")
        relative_root = "" if prefix == "." else f"{prefix}/"
        text = inject_brand_styles(text, relative_root)
        text = inject_mobile_accordion_styles(text, relative_root)
        text = inject_chart_surface_styles(text, relative_root)
        text = cache_bust_favicon(text)
        text = cache_bust_app_bundle(text)
        text = inject_pwa(text, relative_root)
        path.write_text(text, encoding="utf-8")

    missing_mark = [
        path for path in site_pages
        if 'class="ov-mark-svg"' not in path.read_text(encoding="utf-8")
    ]
    if missing_mark:
        raise RuntimeError(f"Nuovo marchio assente in {len(missing_mark)} pagine")

    if OLD_MARK in bundle_path.read_text(encoding="utf-8"):
        raise RuntimeError("Il vecchio marchio O è ancora presente nell'app bundle")

    for relative in (*PWA_FILES, *(f"pwa/{name}" for name in PWA_ICONS)):
        path = DIST / relative
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"Asset PWA non incluso nella build: {relative}")


def select_opportunity_public_payload() -> Path:
    """Preferisce lo snapshot giornaliero verificato; la release resta il fallback."""
    release = ROOT / "data" / "opportunity-release.json"
    daily = ROOT / "data" / "opportunity-daily-public.json"
    if not daily.exists():
        return release

    release_payload = json.loads(release.read_text(encoding="utf-8"))
    daily_payload = json.loads(daily.read_text(encoding="utf-8"))
    release_date = str(release_payload.get("referenceDate") or "")
    daily_date = str(daily_payload.get("referenceDate") or "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", daily_date):
        raise RuntimeError("Snapshot Radar giornaliero con referenceDate non valida")
    if release_date and daily_date < release_date:
        return release
    if daily_payload.get("continuityHold") or daily_payload.get("coverageHold"):
        raise RuntimeError("Snapshot Radar giornaliero contiene hold bloccanti")
    if not (daily_payload.get("backtest") or {}).get("passed", False):
        raise RuntimeError("Snapshot Radar giornaliero con backtest non valido")
    if (daily_payload.get("coverageAudit") or {}).get("status") != "pass":
        raise RuntimeError("Snapshot Radar giornaliero con coverage audit non valido")
    if (daily_payload.get("regionalCompleteness") or {}).get("status") == "fail":
        raise RuntimeError("Snapshot Radar giornaliero con completezza Regione Toscana non valida")
    return daily


if __name__ == "__main__":
    # La build non materializza né riscrive data/opportunity-release.json: il baseline
    # resta canonico e immutabile; il daily verificato viene selezionato solo per dist.
    runpy.run_path(str(ROOT / "scripts" / "materialize_opportunity_public_shell.py"), run_name="__main__")
    runpy.run_path(str(ROOT / "scripts" / "materialize_percorsi_touch_release.py"), run_name="__main__")

    runpy.run_path(str(ROOT / "scripts" / "build_static_safe.py"), run_name="__main__")

    # Import dopo la materializzazione: il contratto di shell è quello pubblico.
    from site_chrome import synchronize_native_page

    synchronize_native_page(DIST, DIST / "confronta" / "meteo-clima" / "index.html")

    from build_opportunity_release import build as build_opportunity_release

    opportunity_payload = select_opportunity_public_payload()
    build_opportunity_release(opportunity_payload, DIST)
    apply_brand_and_pwa()
    print(f"Build statica completata con identità OV, PWA e Radar da {opportunity_payload.name}.")
