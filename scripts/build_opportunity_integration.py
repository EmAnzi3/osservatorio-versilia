#!/usr/bin/env python3
"""Materializza il Radar nella route definitiva, ma solo nella build di collaudo.

La route resta noindex e fuori dalla sitemap. Per rendere il collaudo utile, la
build locale simula anche la futura collocazione pubblica del Radar in header,
home e footer. Il normale workflow Pages non invoca questo script.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import build_opportunity_preview_v04 as route_builder
import build_opportunity_preview_v043 as radar_v043

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "reports" / "runtime" / "opportunities-v04.json"
DEFAULT_DIST = ROOT / "dist"
TARGET_ROUTE = "opportunita"


def _route_href(path: Path, dist: Path) -> str:
    relative = os.path.relpath(dist / TARGET_ROUTE, path.parent).replace(os.sep, "/")
    if relative == ".":
        return "./"
    return relative.rstrip("/") + "/"


def _inject_header_link(text: str, href: str, *, current: bool = False) -> str:
    if 'data-opportunity-nav="header"' in text:
        return text
    current_attr = ' aria-current="page"' if current else ""
    link = f'<a href="{href}" data-opportunity-nav="header"{current_attr}>Opportunità</a>'
    pattern = re.compile(
        r'(<nav\b[^>]*aria-label="Navigazione principale"[^>]*>.*?<a\b[^>]*>\s*Comuni\s*</a>)',
        flags=re.IGNORECASE | re.DOTALL,
    )
    text, count = pattern.subn(rf"\1\n              {link}", text, count=1)
    if count != 1:
        raise RuntimeError("Impossibile collocare Opportunità dopo Comuni nell'header")
    return text


def _inject_footer_link(text: str, href: str, *, current: bool = False) -> str:
    if 'data-opportunity-nav="footer"' in text:
        return text
    current_attr = ' aria-current="page"' if current else ""
    link = f'<a href="{href}" data-opportunity-nav="footer"{current_attr}>Opportunità</a>'
    text = text.replace(
        'class="footer-links" aria-label="Informazioni sul progetto"',
        'class="footer-links" aria-label="Navigazione e informazioni"',
        1,
    )
    pattern = re.compile(
        r'(<nav\b[^>]*class="[^"]*footer-links[^"]*"[^>]*>)',
        flags=re.IGNORECASE,
    )
    text, count = pattern.subn(rf"\1\n          {link}", text, count=1)
    if count != 1:
        raise RuntimeError("Impossibile collocare Opportunità nel footer")
    return text


def _home_callout(total: int, configured: int) -> str:
    source_copy = f"{configured} fonti monitorate" if configured else "una rete di fonti pubbliche monitorate"
    return f'''<section class="project-callout page-width opportunity-home-callout" aria-labelledby="opportunita-home-title" data-opportunity-home-link>
      <div><span class="overline">Nuovo strumento</span><h2 id="opportunita-home-title">Radar Opportunità</h2></div>
      <div><p>Finanziamenti, bandi e programmi utili ai Comuni della Versilia. Oggi il Radar raccoglie <strong>{total} opportunità correnti</strong> da <strong>{source_copy}</strong>, con fonte ufficiale e requisiti di accesso.</p><a class="text-link" href="opportunita/">Esplora le opportunità <b>→</b></a></div>
    </section>'''


def _inject_home_callout(text: str, total: int, configured: int) -> str:
    if "data-opportunity-home-link" in text:
        return text
    pattern = re.compile(
        r'(<section\b[^>]*class="[^"]*towns-section[^"]*"[^>]*id="comuni"[^>]*>.*?</section>)',
        flags=re.IGNORECASE | re.DOTALL,
    )
    text, count = pattern.subn(rf"\1\n{_home_callout(total, configured)}", text, count=1)
    if count != 1:
        raise RuntimeError("Impossibile collocare il Radar in home dopo i Comuni")
    return text


def _simulate_public_placement(dist: Path, total: int, configured: int) -> None:
    """Mostra nello ZIP di collaudo la futura collocazione, senza toccare Pages."""
    target = (dist / TARGET_ROUTE / "index.html").resolve()
    for path in dist.rglob("*.html"):
        if path.name == "offline.html":
            continue
        text = path.read_text(encoding="utf-8")
        href = _route_href(path, dist)
        current = path.resolve() == target
        if 'aria-label="Navigazione principale"' in text:
            text = _inject_header_link(text, href, current=current)
        if "footer-links" in text:
            text = _inject_footer_link(text, href, current=current)
        if path.resolve() == (dist / "index.html").resolve():
            text = _inject_home_callout(text, total, configured)
        path.write_text(text, encoding="utf-8")


def build(payload_path: Path, dist: Path) -> Path:
    # Riusa il renderer v0.4.3 collaudato, cambiando soltanto la route di output.
    route_builder.TARGET_ROUTE = TARGET_ROUTE
    target = radar_v043.build(payload_path, dist)

    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    total = len(payload.get("opportunities") or [])
    configured = int((((payload.get("sourceCoverage") or {}).get("summary") or {}).get("configured")) or 0)

    text = target.read_text(encoding="utf-8")
    text = text.replace(
        "<title>Anteprima Radar Opportunità · Osservatorio Versilia</title>",
        "<title>Radar Opportunità · Collaudo · Osservatorio Versilia</title>",
        1,
    )
    text = text.replace(
        'content="Anteprima non pubblica del Radar Opportunità Versilia v0.4.3."',
        'content="Collaudo non pubblico del Radar Opportunità per i Comuni della Versilia."',
        1,
    )
    text = text.replace(
        "Radar opportunità · Anteprima v0.4.3",
        "Radar opportunità · Collaudo integrazione",
        1,
    )
    text = text.replace(
        "<strong>Anteprima tecnica, non pubblicata.</strong> La route è fuori dalla sitemap e dalla navigazione pubblica.",
        "<strong>Pagina di collaudo, non pubblicata.</strong> In questo ZIP vedi la futura collocazione in header, home e footer; il sito pubblico non è stato modificato.",
        1,
    )
    target.write_text(text, encoding="utf-8")

    _simulate_public_placement(dist, total, configured)

    check = target.read_text(encoding="utf-8")
    if 'name="robots" content="noindex,nofollow,noarchive"' not in check:
        raise SystemExit("Il Radar di collaudo deve restare noindex/nofollow/noarchive")
    if "Radar opportunità · Collaudo integrazione" not in check:
        raise SystemExit("Etichetta di collaudo non materializzata")
    if "Tutte le fonti monitorate" not in check:
        raise SystemExit("Filtro Fonti completo assente")
    if 'data-opportunity-nav="header"' not in check or 'data-opportunity-nav="footer"' not in check:
        raise SystemExit("Collocazione futura del Radar non visibile in header/footer")

    sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8") if (dist / "sitemap.xml").exists() else ""
    if "https://osservatorioversilia.it/opportunita/" in sitemap:
        raise SystemExit("/opportunita/ non deve ancora comparire nella sitemap")

    home = dist / "index.html"
    home_text = home.read_text(encoding="utf-8") if home.exists() else ""
    if 'data-opportunity-home-link' not in home_text or 'href="opportunita/"' not in home_text:
        raise SystemExit("La simulazione deve mostrare il Radar anche in home")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    args = parser.parse_args()
    print(f"Radar integrato in modalità collaudo: {build(args.data, args.dist)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
