#!/usr/bin/env python3
"""Generate /letture/ pages into dist from data/letture.json.

The configuration carries editorial structure only. Values, periods, sources and status
are loaded client-side from the canonical site data, source registry and monitor state.
Generated pages are preview-only (`noindex`) but use the production brand/PWA shell.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
CONFIG = ROOT / "data" / "letture.json"


def brand_mark() -> str:
    svg = (ROOT / "assets" / "brand-mark.svg").read_text(encoding="utf-8").strip()
    svg = re.sub(r"\s+role=\"img\"\s+aria-labelledby=\"[^\"]+\"", "", svg, count=1)
    svg = re.sub(r"\s*<title[^>]*>.*?</title>\s*", "", svg, flags=re.DOTALL)
    svg = re.sub(r"\s*<desc[^>]*>.*?</desc>\s*", "", svg, flags=re.DOTALL)
    svg = svg.replace("<svg ", '<svg class="ov-mark-svg" aria-hidden="true" focusable="false" ', 1)
    return f'<span class="site-brand-mark" aria-hidden="true">{svg}</span>'


def shell(title: str, description: str, body_class: str, reading: str = "", depth: int = 1) -> str:
    prefix = "../" * depth
    reading_attr = f' data-reading="{html.escape(reading, quote=True)}"' if reading else ""
    mark = brand_mark()
    return f'''<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
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
  <link rel="stylesheet" href="{prefix}assets/letture.css?v=20260819-1">
</head>
<body class="antialiased {body_class}"{reading_attr}>
  <header class="site-header"><div class="site-header-inner">
    <a href="{prefix}" class="site-brand" aria-label="Osservatorio Versilia, torna alla home">{mark}<span class="site-brand-copy"><strong>Osservatorio Versilia</strong><small>Versilia in numeri</small></span></a>
    <div class="site-header-actions"><nav aria-label="Navigazione principale"><a href="{prefix}#temi">Temi</a><a href="{prefix}#comuni">Comuni</a><a href="{prefix}progetto/">Il progetto</a><a href="{prefix}stato-dati/">Stato dei dati</a></nav></div>
  </div></header>
  <main id="reading-app" class="reading-main"><div class="app-loading" role="status">Caricamento della lettura…</div></main>
  <footer class="site-footer"><div class="footer-about"><strong>Osservatorio Versilia</strong><p>Un punto di accesso indipendente ai dati pubblici dei sette Comuni della Versilia.</p><p class="footer-disclaimer">Le Letture interpretano indicatori già pubblicati e non costituiscono un dataset autonomo.</p></div><nav class="footer-links"><a href="{prefix}progetto/">Il progetto</a><a href="{prefix}stato-dati/">Stato dei dati</a><a href="{prefix}segnala/">Segnala un dato</a></nav></footer>
  <script src="{prefix}assets/letture.js?v=20260819-1" defer></script>
  <script src="{prefix}assets/pwa.js?v=20260813-pwa8&rev=install-ui-off" defer></script>
</body>
</html>
'''


def main() -> None:
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    if not items:
        raise RuntimeError("Catalogo Letture vuoto")
    root = DIST / "letture"
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.html").write_text(
        shell(
            "Letture · Osservatorio Versilia",
            "Percorsi guidati dentro gli indicatori dell’Osservatorio Versilia, con dati, confronti, contesto, limiti e fonti.",
            "reading-index",
            depth=1,
        ),
        encoding="utf-8",
    )
    seen: set[str] = set()
    for item in items:
        slug = str(item.get("slug") or "").strip()
        title = str(item.get("title") or "").strip()
        if not slug or not title or slug in seen:
            raise RuntimeError(f"Lettura non valida o duplicata: {slug!r}")
        seen.add(slug)
        target = root / slug
        target.mkdir(parents=True, exist_ok=True)
        description = str(item.get("question") or payload.get("description") or title)
        (target / "index.html").write_text(
            shell(f"{title} · Letture · Osservatorio Versilia", description, "reading-detail", reading=slug, depth=2),
            encoding="utf-8",
        )
    print(f"Letture generate: {len(items)} + indice")


if __name__ == "__main__":
    main()
