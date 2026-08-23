#!/usr/bin/env python3
"""Materializza il Radar nella route definitiva, ma solo nella build di collaudo.

La pagina resta deliberatamente fuori da navigazione, home e sitemap e mantiene
noindex finché non viene autorizzata la pubblicazione. Il normale workflow Pages
non invoca questo script.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import build_opportunity_preview_v04 as route_builder
import build_opportunity_preview_v043 as radar_v043

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "reports" / "runtime" / "opportunities-v04.json"
DEFAULT_DIST = ROOT / "dist"
TARGET_ROUTE = "opportunita"


def build(payload_path: Path, dist: Path) -> Path:
    # Riusa il renderer v0.4.3 collaudato, cambiando soltanto la route di output.
    route_builder.TARGET_ROUTE = TARGET_ROUTE
    target = radar_v043.build(payload_path, dist)

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
        "<strong>Pagina di collaudo, non pubblicata.</strong> La route definitiva resta fuori da sitemap, home e navigazione pubblica fino all'approvazione finale.",
        1,
    )
    target.write_text(text, encoding="utf-8")

    check = target.read_text(encoding="utf-8")
    if 'name="robots" content="noindex,nofollow,noarchive"' not in check:
        raise SystemExit("Il Radar di collaudo deve restare noindex/nofollow/noarchive")
    if "Radar opportunità · Collaudo integrazione" not in check:
        raise SystemExit("Etichetta di collaudo non materializzata")
    if "Tutte le fonti monitorate" not in check:
        raise SystemExit("Filtro Fonti completo assente")

    sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8") if (dist / "sitemap.xml").exists() else ""
    if "https://osservatorioversilia.it/opportunita/" in sitemap:
        raise SystemExit("/opportunita/ non deve ancora comparire nella sitemap")

    nav = re.search(
        r'<nav\b[^>]*aria-label="Navigazione principale"[^>]*>(.*?)</nav>',
        check,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not nav or re.search(r'>\s*Opportunità\s*<', nav.group(1), flags=re.IGNORECASE):
        raise SystemExit("La voce Opportunità non deve ancora essere esposta nell'header")

    home = dist / "index.html"
    if home.exists() and re.search(r'href=["\'][^"\']*opportunita/', home.read_text(encoding="utf-8"), flags=re.I):
        raise SystemExit("La home non deve ancora linkare il Radar")
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
