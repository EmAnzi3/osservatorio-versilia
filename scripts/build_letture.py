#!/usr/bin/env python3
"""Generate /letture/ pages into dist from data/letture.json.

The configuration carries editorial structure only. Values, periods, sources and status
are loaded client-side from the canonical site data, source registry and monitor state.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
CONFIG = ROOT / "data" / "letture.json"


def shell(title: str, description: str, body_class: str, reading: str = "", depth: int = 1) -> str:
    prefix = "../" * depth
    reading_attr = f' data-reading="{html.escape(reading, quote=True)}"' if reading else ""
    return f'''<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta property="og:title" content="{html.escape(title, quote=True)}">
  <meta property="og:description" content="{html.escape(description, quote=True)}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="it_IT">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
  <link rel="manifest" href="{prefix}site.webmanifest">
  <link rel="stylesheet" href="{prefix}assets/original.css">
  <link rel="stylesheet" href="{prefix}assets/fonts.css">
  <link rel="stylesheet" href="{prefix}assets/fidelity.css">
  <link rel="stylesheet" href="{prefix}assets/letture.css?v=20260819-1">
</head>
<body class="antialiased {body_class}"{reading_attr}>
  <header class="site-header"><div class="site-header-inner">
    <a href="{prefix}" class="site-brand" aria-label="Osservatorio Versilia, torna alla home"><span class="site-brand-mark">O</span><span class="site-brand-copy"><strong>Osservatorio Versilia</strong><small>Versilia in numeri</small></span></a>
    <div class="site-header-actions"><nav aria-label="Navigazione principale"><a href="{prefix}#temi">Temi</a><a href="{prefix}#comuni">Comuni</a><a href="{prefix}progetto/">Il progetto</a><a href="{prefix}stato-dati/">Stato dei dati</a></nav></div>
  </div></header>
  <main id="reading-app" class="reading-main"><div class="app-loading" role="status">Caricamento della lettura…</div></main>
  <footer class="site-footer"><div class="footer-about"><strong>Osservatorio Versilia</strong><p>Un punto di accesso indipendente ai dati pubblici dei sette Comuni della Versilia.</p><p class="footer-disclaimer">Le Letture interpretano indicatori già pubblicati e non costituiscono un dataset autonomo.</p></div><nav class="footer-links"><a href="{prefix}progetto/">Il progetto</a><a href="{prefix}stato-dati/">Stato dei dati</a><a href="{prefix}segnala/">Segnala un dato</a></nav></footer>
  <script src="{prefix}assets/letture.js?v=20260819-1" defer></script>
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
