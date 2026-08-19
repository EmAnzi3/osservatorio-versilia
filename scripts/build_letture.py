#!/usr/bin/env python3
"""Generate editorial readings and printable reports into dist.

Values, periods, sources and status remain canonical: all editorial/report pages load
site-data.json and source-monitor-state.json at runtime. Generated pages stay noindex
while PR #77 is a draft and are synchronized to the production site shell.
"""
from __future__ import annotations

import html
import json
import re
import runpy
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
CONFIG = ROOT / "data" / "letture.json"
SITE_DATA = ROOT / "data" / "site-data.json"
ASSET_VERSION = "20260819-3"


def brand_mark() -> str:
    svg = (ROOT / "assets" / "brand-mark.svg").read_text(encoding="utf-8").strip()
    svg = re.sub(r'\s+role="img"\s+aria-labelledby="[^"]+"', "", svg, count=1)
    svg = re.sub(r"\s*<title[^>]*>.*?</title>\s*", "", svg, flags=re.DOTALL)
    svg = re.sub(r"\s*<desc[^>]*>.*?</desc>\s*", "", svg, flags=re.DOTALL)
    svg = svg.replace("<svg ", '<svg class="ov-mark-svg" aria-hidden="true" focusable="false" ', 1)
    return f'<span class="site-brand-mark" aria-hidden="true">{svg}</span>'


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")


def common_head(prefix: str, title: str, description: str, extra_css: str) -> str:
    return f'''<meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <meta name="theme-color" content="#0F3654">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="default">
  <meta name="apple-mobile-web-app-title" content="Osservatorio Versilia">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta property="og:title" content="{html.escape(title, quote=True)}">
  <meta property="og:description" content="{html.escape(description, quote=True)}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="it_IT">
  <meta property="og:site_name" content="Osservatorio Versilia">
  <meta property="og:image" content="https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
  <link rel="manifest" href="{prefix}site.webmanifest">
  <link rel="apple-touch-icon" sizes="180x180" href="{prefix}pwa/icon-180.png">
  <link rel="stylesheet" href="{prefix}assets/original.css">
  <link rel="stylesheet" href="{prefix}assets/fonts.css">
  <link rel="stylesheet" href="{prefix}assets/fidelity.css">
  <link rel="stylesheet" href="{prefix}assets/brand.css">
  <link rel="stylesheet" href="{prefix}assets/pwa.css">
  {extra_css}'''


def header_footer(prefix: str, footer_note: str) -> tuple[str, str]:
    mark = brand_mark()
    header = f'''<header class="site-header"><div class="site-header-inner">
    <a href="{prefix}" class="site-brand" aria-label="Osservatorio Versilia, torna alla home">{mark}<span class="site-brand-copy"><strong>Osservatorio Versilia</strong><small>Versilia in numeri</small></span></a>
    <div class="site-header-actions"><nav aria-label="Navigazione principale"><a href="{prefix}#temi">Temi</a><a href="{prefix}#comuni">Comuni</a><a href="{prefix}progetto/">Il progetto</a><a href="{prefix}stato-dati/">Stato dei dati</a></nav></div>
  </div></header>'''
    footer = f'''<footer class="site-footer"><div class="footer-about"><strong>Osservatorio Versilia</strong><p>Un punto di accesso indipendente ai dati pubblici dei sette Comuni della Versilia.</p><p class="footer-disclaimer">{html.escape(footer_note)}</p></div><nav class="footer-links"><a href="{prefix}progetto/">Il progetto</a><a href="{prefix}stato-dati/">Stato dei dati</a><a href="{prefix}segnala/">Segnala un dato</a></nav></footer>'''
    return header, footer


def reading_shell(title: str, description: str, body_class: str, reading: str = "", depth: int = 1) -> str:
    prefix = "../" * depth
    reading_attr = f' data-reading="{html.escape(reading, quote=True)}"' if reading else ""
    header, footer = header_footer(prefix, "Capire la Versilia interpreta indicatori già pubblicati e non costituisce un dataset autonomo.")
    css = f'<link rel="stylesheet" href="{prefix}assets/letture.css?v={ASSET_VERSION}">\n  <link rel="stylesheet" href="{prefix}assets/letture-v3.css?v={ASSET_VERSION}">'
    return f'''<!doctype html>
<html lang="it"><head>
  {common_head(prefix, title, description, css)}
</head><body class="antialiased {body_class}"{reading_attr}>
  {header}
  <main id="reading-app" class="reading-main"><div class="app-loading" role="status">Caricamento della lettura…</div></main>
  {footer}
  <script src="{prefix}assets/letture.js?v={ASSET_VERSION}" defer></script>
  <script src="{prefix}assets/pwa.js?v=20260813-pwa8&rev=install-ui-off" defer></script>
</body></html>'''


def report_shell(title: str, description: str, *, depth: int, reading: str = "", town: str = "", index: bool = False) -> str:
    prefix = "../" * depth
    attrs = []
    if reading:
        attrs.append(f'data-report-reading="{html.escape(reading, quote=True)}"')
    if town:
        attrs.append(f'data-report-town="{html.escape(town, quote=True)}"')
    if index:
        attrs.append('data-report-index="true"')
    attr_text = " " + " ".join(attrs) if attrs else ""
    header, footer = header_footer(prefix, "I Rapporti sono generati dagli stessi dati canonici dell’Osservatorio e sono ottimizzati per stampa/PDF.")
    css = f'<link rel="stylesheet" href="{prefix}assets/rapporti.css?v={ASSET_VERSION}">'
    return f'''<!doctype html>
<html lang="it"><head>
  {common_head(prefix, title, description, css)}
</head><body class="antialiased report-page"{attr_text}>
  {header}
  <main id="report-app"><div class="app-loading" role="status">Generazione del rapporto…</div></main>
  {footer}
  <script src="{prefix}assets/rapporti.js?v={ASSET_VERSION}" defer></script>
  <script src="{prefix}assets/pwa.js?v=20260813-pwa8&rev=install-ui-off" defer></script>
</body></html>'''


def main() -> None:
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    site_data = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    if not items:
        raise RuntimeError("Catalogo Capire la Versilia vuoto")

    reading_root = DIST / "letture"
    reading_root.mkdir(parents=True, exist_ok=True)
    (reading_root / "index.html").write_text(
        reading_shell("Capire la Versilia · Osservatorio Versilia", payload.get("description") or "Storie e chiavi di lettura costruite a partire dai dati dell’Osservatorio Versilia.", "reading-index", depth=1),
        encoding="utf-8",
    )
    seen: set[str] = set()
    for item in items:
        slug = str(item.get("slug") or "").strip()
        title = str(item.get("title") or "").strip()
        if not slug or not title or slug in seen:
            raise RuntimeError(f"Lettura non valida o duplicata: {slug!r}")
        seen.add(slug)
        target = reading_root / slug
        target.mkdir(parents=True, exist_ok=True)
        description = str(item.get("standfirst") or item.get("question") or payload.get("description") or title)
        (target / "index.html").write_text(
            reading_shell(f"{title} · Capire la Versilia · Osservatorio Versilia", description, "reading-detail", reading=slug, depth=2), encoding="utf-8"
        )

    reports_root = DIST / "rapporti"
    reports_root.mkdir(parents=True, exist_ok=True)
    (reports_root / "index.html").write_text(
        report_shell("Rapporti · Osservatorio Versilia", "Rapporti analitici e comunali esportabili, generati dai dati canonici dell’Osservatorio Versilia.", depth=1, index=True), encoding="utf-8"
    )
    pilot = next((item for item in items if item.get("status") == "pilot" and item.get("report", {}).get("enabled")), None)
    if pilot:
        report_slug = str(pilot["report"].get("slug") or f"lettura-{pilot['slug']}")
        target = reports_root / report_slug
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(
            report_shell(str(pilot["report"].get("title") or pilot["title"]), str(pilot["report"].get("subtitle") or pilot.get("standfirst") or ""), depth=2, reading=pilot["slug"]), encoding="utf-8"
        )

    towns = site_data.get("towns", [])
    for town in towns:
        name = str(town.get("name") or "").strip()
        if not name:
            continue
        town_slug = slugify(name)
        target = reports_root / f"comune-{town_slug}"
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(
            report_shell(f"Rapporto comunale · {name} · Osservatorio Versilia", f"Rapporto comunale di {name}: indicatori chiave, confronto Versilia, periodi e fonti.", depth=2, town=town_slug), encoding="utf-8"
        )

    print(f"Capire la Versilia: {len(items)} pagine; Rapporti: {1 + (1 if pilot else 0) + len(towns)} pagine")
    runpy.run_path(str(ROOT / "scripts" / "sync_editorial_layout.py"), run_name="__main__")


if __name__ == "__main__":
    main()
