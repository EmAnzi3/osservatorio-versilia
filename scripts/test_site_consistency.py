#!/usr/bin/env python3
"""Gate finale per coerenza di shell, metadata, route e link pubblici.

Il test va eseguito dopo che tutte le pagine speciali sono state materializzate,
inclusi Stato dati, PNRR e Percorsi. Una nuova pagina HTML deve quindi riusare
la shell canonica oppure dichiarare qui un profilo esplicito.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from site_chrome import (
    FOOTER_LINK_LABELS,
    HEADER_LINK_LABELS,
    assert_navigation_contract,
)

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://osservatorioversilia.it/"
SPECIAL_PUBLIC_PAGES = {
    Path("confronta/meteo-clima/index.html"),
    Path("pnrr/index.html"),
    Path("stato-dati/index.html"),
    Path("percorsi/index.html"),
    Path("percorsi/metodo.html"),
}
NO_SHELL_PAGES = {Path("offline.html")}
NO_FOOTER_PAGES = {Path("percorsi/index.html")}


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def expected_pages() -> set[Path]:
    data = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
    pages = {
        Path("index.html"),
        Path("404.html"),
        Path("offline.html"),
        Path("progetto/index.html"),
        Path("segnala/index.html"),
        *SPECIAL_PUBLIC_PAGES,
    }
    pages.update(Path("comuni") / slugify(town["name"]) / "index.html" for town in data["towns"])
    pages.update(Path("confronta") / key / "index.html" for key in data["themes"])
    pages.update(
        Path("indicatori") / slugify(metric["meta"]["label"]) / "index.html"
        for metric in data["metrics"].values()
        if metric.get("dataStorage", {}).get("type") != "external-climate"
    )
    return pages


def meta_content(document: str, key: str, value: str) -> str | None:
    patterns = (
        rf'<meta\b[^>]*\b{key}="{re.escape(value)}"[^>]*\bcontent="([^"]*)"[^>]*>',
        rf'<meta\b[^>]*\bcontent="([^"]*)"[^>]*\b{key}="{re.escape(value)}"[^>]*>',
    )
    for pattern in patterns:
        match = re.search(pattern, document, flags=re.IGNORECASE)
        if match:
            return html.unescape(match.group(1)).strip()
    return None


def canonical_url(document: str) -> str | None:
    match = re.search(
        r'<link\b[^>]*rel="canonical"[^>]*href="([^"]+)"[^>]*>',
        document,
        flags=re.IGNORECASE,
    )
    if not match:
        match = re.search(
            r'<link\b[^>]*href="([^"]+)"[^>]*rel="canonical"[^>]*>',
            document,
            flags=re.IGNORECASE,
        )
    return html.unescape(match.group(1)).strip() if match else None


def route_url(path: Path) -> str:
    route = path.as_posix()
    if route == "index.html":
        route = ""
    elif route.endswith("/index.html"):
        route = route[: -len("index.html")]
    return urljoin(BASE_URL, route)


def shell_fragments(document: str) -> tuple[str | None, str | None]:
    header = re.search(r'<header\b[^>]*class="[^"]*site-header[^"]*"[^>]*>.*?</header>', document, re.I | re.S)
    footer = re.search(r'<footer\b[^>]*class="[^"]*site-footer[^"]*"[^>]*>.*?</footer>', document, re.I | re.S)
    return (header.group(0) if header else None, footer.group(0) if footer else None)


def nav_links(fragment: str, pattern: str) -> tuple[tuple[str, str], ...]:
    nav = re.search(pattern, fragment, flags=re.IGNORECASE | re.DOTALL)
    if not nav:
        return ()
    links = []
    for attrs, body in re.findall(r"<a\b([^>]*)>(.*?)</a>", nav.group(1), flags=re.I | re.S):
        href = re.search(r'href="([^"]+)"', attrs, flags=re.I)
        label = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", body)).split())
        links.append((label, html.unescape(href.group(1)) if href else ""))
    return tuple(links)


def assert_shell(path: Path, document: str, canonical: str) -> None:
    header, footer = shell_fragments(document)
    if path in NO_SHELL_PAGES:
        assert not header and not footer, f"La pagina speciale non deve montare la shell: {path}"
        return
    assert header, f"Header canonico assente: {path}"
    if path in NO_FOOTER_PAGES:
        assert not footer, f"La mappa full-screen non deve montare un footer nascosto: {path}"
        header_links = nav_links(
            header,
            r'<nav\b[^>]*aria-label="Navigazione principale"[^>]*>(.*?)</nav>',
        )
        assert tuple(label for label, _ in header_links) == HEADER_LINK_LABELS, path
        assert header.count('data-data-status-nav="header"') == 1, path
    else:
        assert footer, f"Footer canonico assente: {path}"
        assert_navigation_contract(header, footer)

    assert "site-brand" in header, f"Marchio assente: {path}"
    assert "global-search-trigger" in header, f"Accesso alla ricerca assente: {path}"
    assert re.search(
        r'<button\b[^>]*class="[^"]*global-search-trigger[^"]*"[^>]*>.*?<kbd\b[^>]*>\s*/\s*</kbd>.*?</button>',
        header,
        flags=re.I | re.S,
    ), f"Ricerca globale non eseguibile o scorciatoia assente: {path}"

    header_links = nav_links(
        header,
        r'<nav\b[^>]*aria-label="Navigazione principale"[^>]*>(.*?)</nav>',
    )
    expected_header = (
        ("Temi", BASE_URL + "#temi"),
        ("Comuni", BASE_URL + "#comuni"),
        ("Il progetto", BASE_URL + "progetto/"),
        ("Stato dati", BASE_URL + "stato-dati/"),
        ("Segnala", BASE_URL + "segnala/"),
    )
    resolved_header = tuple((label, urljoin(canonical, href)) for label, href in header_links)
    assert resolved_header == expected_header, f"Link header incoerenti in {path}: {resolved_header}"

    if footer:
        footer_links = nav_links(
            footer,
            r'<nav\b[^>]*class="[^"]*footer-links[^"]*"[^>]*>(.*?)</nav>',
        )
        expected_footer = (
            ("Il progetto", BASE_URL + "progetto/"),
            ("Stato dei dati", BASE_URL + "stato-dati/"),
            ("Metodo", BASE_URL + "progetto/#metodo"),
            ("Licenza", BASE_URL + "progetto/#licenza"),
            ("Versioni dei dati", BASE_URL + "progetto/#versioni"),
            ("Segnala un dato", BASE_URL + "segnala/"),
            ("Contatti", "mailto:info@osservatorioversilia.it"),
        )
        resolved_footer = tuple(
            (label, href if href.startswith("mailto:") else urljoin(canonical, href))
            for label, href in footer_links
        )
        assert tuple(label for label, _ in resolved_footer) == FOOTER_LINK_LABELS, path
        assert resolved_footer == expected_footer, f"Link footer incoerenti in {path}: {resolved_footer}"


def assert_metadata(path: Path, document: str) -> str | None:
    assert re.search(r'<html\b[^>]*lang="it"', document, flags=re.I), f"Lingua HTML assente: {path}"
    assert meta_content(document, "name", "viewport"), f"Viewport assente: {path}"
    assert re.search(r"<title>\s*\S", document, flags=re.I), f"Title assente: {path}"
    assert re.search(r"<h1\b", document, flags=re.I), f"H1 assente: {path}"
    assert meta_content(document, "name", "description"), f"Description assente: {path}"

    if path == Path("offline.html"):
        assert canonical_url(document) is None, "La pagina offline non deve avere canonical"
        assert "noindex" in (meta_content(document, "name", "robots") or ""), "Offline indicizzabile"
        return None

    canonical = canonical_url(document)
    expected = route_url(path)
    assert canonical == expected, f"Canonical incoerente in {path}: {canonical!r} != {expected!r}"
    assert document.lower().count('rel="canonical"') == 1, f"Canonical duplicata: {path}"

    social = {
        ("property", "og:title"),
        ("property", "og:description"),
        ("property", "og:type"),
        ("property", "og:locale"),
        ("property", "og:url"),
        ("property", "og:site_name"),
        ("property", "og:image"),
        ("property", "og:image:alt"),
        ("name", "twitter:card"),
        ("name", "twitter:title"),
        ("name", "twitter:description"),
        ("name", "twitter:site"),
        ("name", "twitter:image"),
        ("name", "twitter:image:alt"),
    }
    missing = [value for key, value in social if not meta_content(document, key, value)]
    assert not missing, f"Metadata social mancanti in {path}: {', '.join(sorted(missing))}"
    assert meta_content(document, "property", "og:url") == canonical, f"og:url incoerente: {path}"
    assert 'type="application/ld+json"' in document, f"JSON-LD assente: {path}"

    if path in {Path("404.html"), Path("confronta/meteo-clima/index.html")}:
        assert "noindex" in (meta_content(document, "name", "robots") or ""), f"Pagina tecnica indicizzabile: {path}"
    return canonical


def assert_internal_links(dist: Path, path: Path, document: str, canonical: str) -> None:
    for href in re.findall(r'<a\b[^>]*href="([^"]+)"', document, flags=re.I):
        href = html.unescape(href).strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        resolved = urlsplit(urljoin(canonical, href))
        if resolved.netloc != "osservatorioversilia.it":
            continue
        route = resolved.path.lstrip("/")
        target = dist / (route + "index.html" if not route or route.endswith("/") else route)
        assert target.exists(), f"Link interno rotto in {path}: {href} -> {target.relative_to(dist)}"


def source_assertions() -> None:
    core = (ROOT / "assets" / "app-parts" / "00.txt").read_text(encoding="utf-8")
    shell_runtime = (ROOT / "assets" / "app-parts" / "01.txt").read_text(encoding="utf-8")
    header = re.search(r'<header\b[^>]*class="site-header"[^>]*>.*?</header>', core, re.S)
    footer = re.search(r'<footer\b[^>]*class="site-footer"[^>]*>.*?</footer>', core, re.S)
    assert header and footer, "Shell sorgente non riconoscibile"
    assert_navigation_contract(header.group(0), footer.group(0))
    assert "if (footerMount) footerMount.innerHTML" in shell_runtime

    climate = (ROOT / "confronta" / "meteo-clima" / "index.html").read_text(encoding="utf-8")
    assert '<div id="site-header-mount"></div>' in climate
    assert '<div id="site-footer-mount"></div>' in climate
    assert 'data-page="special"' in climate and 'id="app"' in climate
    assert meta_content(climate, "property", "og:url") == BASE_URL + "confronta/meteo-clima/"

    map_source = (ROOT / "percorsi" / "index.html").read_text(encoding="utf-8")
    assert '<div id="site-header-mount"></div>' in map_source
    assert 'data-page="special"' in map_source and 'id="app"' in map_source
    assert meta_content(map_source, "property", "og:url") == BASE_URL + "percorsi/"

    method = (ROOT / "percorsi" / "metodo.html").read_text(encoding="utf-8")
    assert '<div id="site-header-mount"></div>' in method
    assert '<div id="site-footer-mount"></div>' in method
    assert 'data-page="special"' in method and 'id="app"' in method
    assert meta_content(method, "property", "og:url") == BASE_URL + "percorsi/metodo.html"
    assert "body{" not in method and "\n    a{" not in method, "Metodo modifica stili globali"

    climate_css = (ROOT / "assets" / "meteo-clima.css").read_text(encoding="utf-8")
    map_css = (ROOT / "percorsi" / "osservatorio.css").read_text(encoding="utf-8")
    map_app_css = (ROOT / "percorsi" / "styles.css").read_text(encoding="utf-8")
    special_css = climate_css + map_css + map_app_css
    assert ".site-header-inner" not in special_css, "Una pagina speciale sposta lo header canonico"
    assert not re.search(r":root\s*\{", map_app_css), "Percorsi sovrascrive le variabili globali della shell"
    assert not re.search(
        r"html\s*,\s*body\s*\{[^}]*font-family", map_app_css, re.S
    ), "Percorsi sovrascrive la tipografia globale della shell"
    assert "search_fallback_link" not in (
        ROOT / "scripts" / "copy_percorsi_dist.py"
    ).read_text(encoding="utf-8"), "Fallback ricerca vietato nelle pagine pubbliche"
    not_found = (ROOT / "404.html").read_text(encoding="utf-8")
    assert "noindex" in (meta_content(not_found, "name", "robots") or "")
    print("Contratto sorgente verificato: shell, pagine speciali e metadata coerenti.")


def build_assertions(dist: Path) -> None:
    assert dist.exists(), f"Build non trovata: {dist}"
    found = {path.relative_to(dist) for path in dist.rglob("*.html")}
    expected = expected_pages()
    assert found == expected, (
        f"Inventario pagine fuori contratto. Mancanti: {sorted(map(str, expected - found))}; "
        f"non classificate: {sorted(map(str, found - expected))}"
    )

    indexable = set()
    for relative in sorted(found):
        document = (dist / relative).read_text(encoding="utf-8")
        assert "app-loading" not in document, f"Skeleton residuo: {relative}"
        canonical = assert_metadata(relative, document)
        if canonical:
            assert_shell(relative, document, canonical)
            assert_internal_links(dist, relative, document, canonical)
            robots = meta_content(document, "name", "robots") or ""
            if "noindex" not in robots:
                indexable.add(canonical)

    sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_urls = set(re.findall(r"<loc>([^<]+)</loc>", sitemap))
    assert sitemap_urls == indexable, (
        f"Sitemap fuori contratto. Mancanti: {sorted(indexable - sitemap_urls)}; "
        f"in eccesso: {sorted(sitemap_urls - indexable)}"
    )
    print(f"Coerenza finale verificata: {len(found)} pagine, {len(indexable)} URL indicizzabili.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    parser.add_argument("--source-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_assertions()
    if not args.source_only:
        build_assertions(args.dist)


if __name__ == "__main__":
    main()
