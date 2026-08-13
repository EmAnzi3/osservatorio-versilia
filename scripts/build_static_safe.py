#!/usr/bin/env python3
"""Safe private build wrapper for the static pre-render migration."""

from __future__ import annotations

import json
import os
import re

import build_static as build

# Dominio pubblico canonico dell'Osservatorio.
build.BASE_URL = "https://osservatorioversilia.it/"

_original_copy_source_tree = build.copy_source_tree
_original_bundle_application = build.bundle_application
_original_prepare_shells = build.prepare_shells
_original_inject_metadata = build.inject_metadata

UX_ASSET_VERSION = "20260809-2"
PUBLIC_CONTACT = "info@osservatorioversilia.it"
LEGACY_CONTACT = "contatti@osservatorioversilia.it"
SOCIAL_IMAGE = f"{build.BASE_URL}images/versilia-viareggio-apuane.jpg"
V170_VERSION_ENTRY = (
    "      ['2026.08.07-v1.7.0','7 agosto 2026','106 indicatori. "
    "Aggiunti dettaglio ISTAT ASIA su unità locali, addetti e settori ATECO, "
    "dati AGCOM FTTH verificati e controlli automatici rafforzati sulle fonti.'],\n"
)
V180_VERSION_ENTRY = (
    "      ['2026.08.09-v1.8.0','9 agosto 2026','106 indicatori. "
    "Aggiunte 106 schede canoniche degli indicatori, politica esplicita di aggiornamento "
    "delle fonti e sette serie comunali Istat omogenee 2021–2023.'],\n"
)
V190_VERSION_ENTRY = (
    "      ['2026.08.12-v1.9.0','12 agosto 2026','111 indicatori canonici in 11 temi. "
    "Integrati Percorsi e mobilità lenta nel dataset principale e separato il tema "
    "Sicurezza e territorio.'],\n"
)

if "bilanci" not in build.THEME_SLUGS:
    build.THEME_SLUGS.insert(2, "bilanci")
if "confronta/bilanci/" not in build.ROUTES:
    build.ROUTES.insert(build.ROUTES.index("progetto/"), "confronta/bilanci/")

SEARCH_ICON = (
    '<svg class="search-icon" xmlns="http://www.w3.org/2000/svg" '
    'width="16" height="16" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<circle cx="11" cy="11" r="8"></circle>'
    '<path d="m21 21-4.3-4.3"></path>'
    '</svg>'
)

OLD_PROJECT_COPY = (
    "offrire un punto di accesso chiaro ai dati che aiutano a leggere "
    "Massarosa e gli altri comuni della Versilia storica."
)
NEW_PROJECT_COPY = (
    "offrire un punto di accesso chiaro ai dati che aiutano a leggere "
    "i sette comuni della Versilia storica e il territorio nel suo insieme."
)

NUMBER_FORMAT_REPLACEMENTS = {
    "new Intl.NumberFormat('it-IT', { maximumFractionDigits: 0 })":
        "new Intl.NumberFormat('it-IT', { useGrouping: 'always', maximumFractionDigits: 0 })",
    "new Intl.NumberFormat('it-IT', { minimumFractionDigits: 1, maximumFractionDigits: 1 })":
        "new Intl.NumberFormat('it-IT', { useGrouping: 'always', minimumFractionDigits: 1, maximumFractionDigits: 1 })",
    "new Intl.NumberFormat('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })":
        "new Intl.NumberFormat('it-IT', { useGrouping: 'always', minimumFractionDigits: 2, maximumFractionDigits: 2 })",
    "new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })":
        "new Intl.NumberFormat('it-IT', { useGrouping: 'always', style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })",
}


def copy_source_tree_with_local_assets() -> None:
    _original_copy_source_tree()
    data_path = build.DIST / "data" / "site-data.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    crest_files = {
        "Camaiore": "camaiore.svg",
        "Forte dei Marmi": "forte-dei-marmi.svg",
        "Massarosa": "massarosa.png",
        "Pietrasanta": "pietrasanta.svg",
        "Seravezza": "seravezza.png",
        "Stazzema": "stazzema.webp",
        "Viareggio": "viareggio.svg",
    }
    data["crests"] = {
        town: f"/crests/{filename}" for town, filename in crest_files.items()
    }
    data_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def bundle_application_with_private_fixes() -> None:
    _original_bundle_application()
    bundle_path = build.DIST / "assets" / "app-bundle.js"
    bundle = bundle_path.read_text(encoding="utf-8")

    old_icon = '<span aria-hidden="true">⌕</span>'
    if old_icon in bundle:
        bundle = bundle.replace(old_icon, SEARCH_ICON)
    elif '<svg class="search-icon"' not in bundle:
        raise RuntimeError("Né l'icona testuale né la lente SVG sono presenti nel bundle")

    for old, new in NUMBER_FORMAT_REPLACEMENTS.items():
        if old in bundle:
            bundle = bundle.replace(old, new)
        elif new not in bundle:
            raise RuntimeError(f"Formatter numerico non trovato: {old}")

    if OLD_PROJECT_COPY in bundle:
        bundle = bundle.replace(OLD_PROJECT_COPY, NEW_PROJECT_COPY)
    elif NEW_PROJECT_COPY not in bundle:
        raise RuntimeError("Testo della pagina Il progetto non trovato nel bundle")

    if LEGACY_CONTACT in bundle:
        bundle = bundle.replace(LEGACY_CONTACT, PUBLIC_CONTACT)
    elif PUBLIC_CONTACT not in bundle:
        raise RuntimeError("Recapito pubblico dell'Osservatorio non trovato nel bundle")

    if "2026.08.12-v1.9.0" not in bundle:
        marker = "    const versions = [\n"
        if marker not in bundle or "2026.08.05-v1.6.0" not in bundle:
            raise RuntimeError("Elenco versioni del progetto non trovato nel bundle")
        entries = V190_VERSION_ENTRY
        if "2026.08.09-v1.8.0" not in bundle:
            entries += V180_VERSION_ENTRY
        if "2026.08.07-v1.7.0" not in bundle:
            entries += V170_VERSION_ENTRY
        bundle = bundle.replace(marker, marker + entries, 1)

    bundle_path.write_text(bundle, encoding="utf-8")


def prepare_shells_with_fonts() -> None:
    _original_prepare_shells()
    for path in build.DIST.rglob("*.html"):
        prefix = build.relative_asset_prefix(path)
        assets = "" if prefix == "." else f"{prefix}/"
        text = path.read_text(encoding="utf-8")

        stylesheets = (
            "fonts.css",
            "ux-experiment.css",
            "ux-background-match.css",
            "export-v161.css",
            "visual-grammar.css",
            "indicator-pages.css",
        )
        for stylesheet in stylesheets:
            token = f"assets/{stylesheet}"
            if token in text:
                continue
            version = "" if stylesheet == "fonts.css" else f"?v={UX_ASSET_VERSION}"
            text = text.replace(
                "</head>",
                f'  <link rel="stylesheet" href="{assets}{token}{version}">\n</head>',
            )

        scripts = (
            "ux-accordion.js",
            "ux-history-core.js",
            "ux-history.js",
            "export-v161.js",
            "visual-grammar.js",
        )
        missing_scripts = [
            f'  <script src="{assets}assets/{script}?v={UX_ASSET_VERSION}" defer></script>\n'
            for script in scripts
            if f"assets/{script}" not in text
        ]
        if missing_scripts:
            text = text.replace("</body>", "".join(missing_scripts) + "</body>")

        path.write_text(text, encoding="utf-8")


def inject_metadata_with_open_graph(document: str, route: str, data: dict) -> str:
    """Aggiunge metadati social coerenti con canonical e dominio pubblico."""
    document = _original_inject_metadata(document, route, data)
    canonical = build.canonical_url(route)
    patterns = (
        r'\s*<meta\s+property="og:url"[^>]*>',
        r'\s*<meta\s+property="og:site_name"[^>]*>',
        r'\s*<meta\s+property="og:image"[^>]*>',
        r'\s*<meta\s+property="og:image:alt"[^>]*>',
        r'\s*<meta\s+name="twitter:card"[^>]*>',
        r'\s*<meta\s+name="twitter:image"[^>]*>',
    )
    for pattern in patterns:
        document = re.sub(pattern, "", document, flags=re.IGNORECASE)
    social = (
        f'\n  <meta property="og:url" content="{canonical}">'
        '\n  <meta property="og:site_name" content="Osservatorio Versilia">'
        f'\n  <meta property="og:image" content="{SOCIAL_IMAGE}">'
        '\n  <meta property="og:image:alt" content="Viareggio e le Alpi Apuane, immagine di Osservatorio Versilia">'
        '\n  <meta name="twitter:card" content="summary_large_image">'
        f'\n  <meta name="twitter:image" content="{SOCIAL_IMAGE}">\n'
    )
    return document.replace("</head>", social + "</head>")


def normalize_prerendered_urls() -> None:
    """Remove temporary prerender state and keep the climate layer runtime-only."""
    localhost = re.compile(r"https?://127\.0\.0\.1:\d+/")
    climate_script = re.compile(
        r'\s*<script[^>]*data-ov-climate-v2[^>]*></script>',
        flags=re.IGNORECASE,
    )
    climate_style = re.compile(
        r'\s*<style\s+id="ov-climate-v2-style"[^>]*>.*?</style>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    for path in build.DIST.rglob("*.html"):
        prefix = os.path.relpath(build.DIST, path.parent).replace(os.sep, "/")
        replacement = "" if prefix == "." else f"{prefix}/"
        text = path.read_text(encoding="utf-8")
        text = localhost.sub(replacement, text)
        text = climate_script.sub("", text)
        text = climate_style.sub("", text)
        text = text.replace(
            '<body data-prerendered="true" class=',
            '<body class=',
        )
        text = text.replace(OLD_PROJECT_COPY, NEW_PROJECT_COPY)
        text = text.replace(LEGACY_CONTACT, PUBLIC_CONTACT)
        path.write_text(text, encoding="utf-8")

    project_path = build.DIST / "progetto" / "index.html"
    project_text = project_path.read_text(encoding="utf-8")
    if NEW_PROJECT_COPY not in project_text or OLD_PROJECT_COPY in project_text:
        raise RuntimeError("Testo della pagina Il progetto non aggiornato nella build")
    if "2026.08.12-v1.9.0" not in project_text or "111 indicatori" not in project_text:
        raise RuntimeError("Versione v1.9.0 non visibile nella pagina Il progetto")
    if LEGACY_CONTACT in project_text or PUBLIC_CONTACT not in project_text:
        raise RuntimeError("Recapito pubblico non coerente nella pagina Il progetto")


build.copy_source_tree = copy_source_tree_with_local_assets
build.bundle_application = bundle_application_with_private_fixes
build.prepare_shells = prepare_shells_with_fonts
build.inject_metadata = inject_metadata_with_open_graph

if __name__ == "__main__":
    build.main()
    normalize_prerendered_urls()
