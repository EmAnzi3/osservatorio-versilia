#!/usr/bin/env python3
"""Contratto e riuso della shell pubblica di Osservatorio Versilia.

Header e footer canonici nascono dal renderer principale. Le pagine speciali
devono estrarli dalla build, non conservarne copie autonome. Questo modulo
centralizza l'estrazione, il rebasing dei link relativi e le invarianti minime
della navigazione globale.
"""
from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

HEADER_LINK_LABELS = ("Temi", "Comuni", "Il progetto", "Stato dati", "Segnala")
FOOTER_LINK_LABELS = (
    "Il progetto",
    "Stato dei dati",
    "Metodo",
    "Licenza",
    "Versioni dei dati",
    "Segnala un dato",
    "Contatti",
)


@dataclass(frozen=True)
class NativeShell:
    header: str
    footer: str
    styles: str
    app_bundle: str | None


def _link_labels(fragment: str, nav_pattern: str) -> tuple[str, ...]:
    match = re.search(nav_pattern, fragment, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ()
    labels = []
    for anchor in re.findall(r"<a\b[^>]*>(.*?)</a>", match.group(1), flags=re.IGNORECASE | re.DOTALL):
        text = re.sub(r"<[^>]+>", " ", anchor)
        labels.append(" ".join(html.unescape(text).split()))
    return tuple(labels)


def assert_navigation_contract(header: str, footer: str) -> None:
    """Fallisce se la shell non espone la navigazione globale completa."""
    header_labels = _link_labels(
        header,
        r'<nav\b[^>]*aria-label="Navigazione principale"[^>]*>(.*?)</nav>',
    )
    footer_labels = _link_labels(
        footer,
        r'<nav\b[^>]*class="[^"]*footer-links[^"]*"[^>]*>(.*?)</nav>',
    )
    if header_labels != HEADER_LINK_LABELS:
        raise RuntimeError(
            "Navigazione header fuori contratto: "
            f"attesa {HEADER_LINK_LABELS}, trovata {header_labels}"
        )
    if footer_labels != FOOTER_LINK_LABELS:
        raise RuntimeError(
            "Navigazione footer fuori contratto: "
            f"attesa {FOOTER_LINK_LABELS}, trovata {footer_labels}"
        )
    if header.count('data-data-status-nav="header"') != 1:
        raise RuntimeError("Lo header deve contenere un solo link canonico a Stato dati")
    if footer.count('data-data-status-nav="footer"') != 1:
        raise RuntimeError("Il footer deve contenere un solo link canonico a Stato dei dati")
    for token in ("site-header", "site-brand", "global-search-trigger"):
        if token not in header:
            raise RuntimeError(f"Elemento canonico assente dallo header: {token}")
    search = re.search(
        r'<button\b[^>]*class="[^"]*global-search-trigger[^"]*"[^>]*>(.*?)</button>',
        header,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not search:
        raise RuntimeError("La ricerca globale deve usare il pulsante canonico, non un fallback")
    if not re.search(r"<kbd\b[^>]*>\s*/\s*</kbd>", search.group(1), flags=re.DOTALL):
        raise RuntimeError("Scorciatoia / assente dal pulsante di ricerca canonico")
    if "site-footer" not in footer:
        raise RuntimeError("Footer canonico non riconoscibile")


def _rebase_url(value: str, source_path: Path, target_path: Path) -> str:
    split = urlsplit(html.unescape(value))
    if split.scheme or split.netloc or value.startswith(("#", "mailto:", "tel:", "data:")):
        return value
    if not split.path:
        return value

    resolved = (source_path.parent / split.path).resolve()
    relative = os.path.relpath(resolved, target_path.parent.resolve()).replace(os.sep, "/")
    if relative == ".":
        relative = "./"
    elif split.path.endswith("/") and not relative.endswith("/"):
        relative += "/"
    return urlunsplit(("", "", relative, split.query, split.fragment))


def rebase_fragment(fragment: str, source_path: Path, target_path: Path) -> str:
    """Ricalcola href/src relativi quando una shell viene copiata fra route."""
    pattern = re.compile(
        r'(?P<prefix>\b(?:href|src)=)(?P<quote>["\'])(?P<value>.*?)(?P=quote)',
        flags=re.IGNORECASE,
    )

    def replace(match: re.Match[str]) -> str:
        value = _rebase_url(match.group("value"), source_path, target_path)
        return f'{match.group("prefix")}{match.group("quote")}{value}{match.group("quote")}'

    return pattern.sub(replace, fragment)


def extract_native_shell(
    dist: Path,
    target_path: Path,
    *,
    template_relative: str = "progetto/index.html",
    require_bundle: bool = True,
) -> NativeShell:
    """Estrae la shell canonica e la adatta alla profondità della pagina target."""
    template_path = dist / template_relative
    if not template_path.exists():
        raise RuntimeError(f"Template nativo non trovato: {template_path}")
    text = template_path.read_text(encoding="utf-8")

    header_start = text.find('<div id="site-header-mount">')
    app_start = text.find('<div id="app">', header_start)
    footer_start = text.find('<div id="site-footer-mount">', app_start)
    footer_end = text.find("<noscript>", footer_start)
    if min(header_start, app_start, footer_start, footer_end) < 0:
        raise RuntimeError("Shell nativa non riconoscibile nel template")

    header = text[header_start:app_start]
    footer = text[footer_start:footer_end]
    head = text[:header_start]
    styles = re.findall(r'<link\b[^>]*rel="stylesheet"[^>]*>', head, flags=re.IGNORECASE)
    if not styles or not any("assets/fonts.css" in item for item in styles):
        raise RuntimeError("Stylesheet canonici non trovati nel template nativo")

    bundle_match = re.search(
        r'<script\b[^>]*src="([^"]*assets/app-bundle\.js[^"]*)"[^>]*></script>',
        text[footer_end:],
        flags=re.IGNORECASE,
    )
    if require_bundle and not bundle_match:
        raise RuntimeError("Runtime applicativo canonico non trovato")

    header = rebase_fragment(header, template_path, target_path)
    footer = rebase_fragment(footer, template_path, target_path)
    styles_markup = "\n  ".join(
        rebase_fragment(item, template_path, target_path) for item in styles
    )
    app_bundle = (
        _rebase_url(bundle_match.group(1), template_path, target_path)
        if bundle_match
        else None
    )
    assert_navigation_contract(header, footer)
    return NativeShell(header, footer, styles_markup, app_bundle)


def synchronize_native_page(
    dist: Path,
    target_path: Path,
    *,
    include_footer: bool = True,
) -> NativeShell:
    """Materializza shell e runtime canonici nei mount vuoti di una pagina speciale."""
    shell = extract_native_shell(dist, target_path)
    text = target_path.read_text(encoding="utf-8")
    header_mount = '<div id="site-header-mount"></div>'
    footer_mount = '<div id="site-footer-mount"></div>'
    if header_mount not in text:
        raise RuntimeError(f"Mount header canonico assente: {target_path}")
    text = text.replace(header_mount, shell.header.rstrip(), 1)
    if include_footer:
        if footer_mount not in text:
            raise RuntimeError(f"Mount footer canonico assente: {target_path}")
        text = text.replace(footer_mount, shell.footer.rstrip(), 1)
    elif footer_mount in text:
        raise RuntimeError(f"Footer non ammesso nella pagina full-screen: {target_path}")

    missing_styles = []
    for stylesheet in shell.styles.splitlines():
        item = stylesheet.strip()
        href = re.search(r'href="([^"]+)"', item)
        if href and f'href="{href.group(1)}"' not in text:
            missing_styles.append(f"  {item}")
    if missing_styles:
        text = text.replace("</head>", "\n".join(missing_styles) + "\n</head>", 1)

    if "assets/app-bundle.js" not in text:
        if not shell.app_bundle:
            raise RuntimeError("Runtime canonico non disponibile")
        text = text.replace(
            "</body>",
            f'  <script src="{shell.app_bundle}" defer></script>\n</body>',
            1,
        )
    if 'data-page="special"' not in text:
        raise RuntimeError(f"Pagina speciale priva di data-page=\"special\": {target_path}")
    if 'id="app"' not in text:
        raise RuntimeError(f"Pagina speciale priva del mount contenuto #app: {target_path}")
    target_path.write_text(text, encoding="utf-8")
    return shell


def ensure_sitemap_entries(dist: Path, urls: tuple[str, ...]) -> None:
    """Registra pagine generate dopo la build principale senza duplicati."""
    path = dist / "sitemap.xml"
    if not path.exists():
        raise RuntimeError("Sitemap non trovata nella build")
    text = path.read_text(encoding="utf-8")
    dates = re.findall(r"<lastmod>(\d{4}-\d{2}-\d{2})</lastmod>", text)
    lastmod = max(dates) if dates else None
    seen = set(re.findall(r"<loc>([^<]+)</loc>", text))
    additions = []
    for url in urls:
        if not url.startswith("https://osservatorioversilia.it/"):
            raise RuntimeError(f"URL sitemap fuori dominio canonico: {url}")
        if html.escape(url) in seen:
            continue
        suffix = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
        additions.append(f"  <url><loc>{html.escape(url)}</loc>{suffix}</url>")
        seen.add(html.escape(url))
    if additions:
        if "</urlset>" not in text:
            raise RuntimeError("Sitemap non riconoscibile")
        text = text.replace("</urlset>", "\n".join(additions) + "\n</urlset>", 1)
        path.write_text(text, encoding="utf-8")
