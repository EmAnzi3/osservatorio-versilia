#!/usr/bin/env python3
"""Contratto statico della route /opportunita/ nella fase di collaudo."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

EXPECTED_NAV = ("Temi", "Comuni", "Opportunità", "Il progetto", "Stato dati", "Segnala")


def labels(fragment: str) -> tuple[str, ...]:
    values = []
    for anchor in re.findall(r"<a\b[^>]*>(.*?)</a>", fragment, flags=re.I | re.S):
        text = re.sub(r"<[^>]+>", " ", anchor)
        values.append(" ".join(text.split()))
    return tuple(values)


def run(dist: Path) -> None:
    target = dist / "opportunita" / "index.html"
    assert target.exists() and target.stat().st_size > 0, "Route /opportunita/ non materializzata"
    text = target.read_text(encoding="utf-8")

    assert 'name="robots" content="noindex,nofollow,noarchive"' in text
    assert "Radar opportunità · Collaudo integrazione" in text
    assert "Tutte le fonti monitorate" in text
    assert "UE · URBACT · monitorata" in text
    assert "Quality gate" not in text and ">Da verificare<" not in text and "coverageHold" not in text

    total_match = re.search(r'data-total-opportunities="(\d+)"', text)
    assert total_match, "Totale opportunità non esposto"
    total = int(total_match.group(1))
    cards = len(re.findall(r'\bdata-opportunity-card\b', text))
    assert total == cards and total > 0, f"Totale/card incoerenti: {total}/{cards}"

    nav = re.search(r'<nav\b[^>]*aria-label="Navigazione principale"[^>]*>(.*?)</nav>', text, flags=re.I | re.S)
    assert nav, "Header canonico non riconosciuto"
    assert labels(nav.group(1)) == EXPECTED_NAV, labels(nav.group(1))
    assert 'data-opportunity-nav="header"' in nav.group(1)
    assert "global-search-trigger" in text and "site-footer" in text
    assert 'data-opportunity-nav="footer"' in text

    source = re.search(r'<select\s+data-op-source>(.*?)</select>', text, flags=re.I | re.S)
    assert source, "Filtro Fonte assente"
    assert len(re.findall(r"<option\b", source.group(1), flags=re.I)) >= 40, "Rete fonti non completa"

    favicons = set(re.findall(r'(?:src|href)="([^"]*source-favicons/[^"]+)"', text))
    assert favicons, "Favicon locali non referenziati"
    for href in favicons:
        relative = href.split("?", 1)[0]
        path = (target.parent / relative).resolve()
        assert path.exists() and path.stat().st_size > 0, f"Favicon locale mancante: {href}"

    sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8")
    assert "https://osservatorioversilia.it/opportunita/" not in sitemap, "Route già in sitemap"

    home = (dist / "index.html").read_text(encoding="utf-8")
    assert 'data-opportunity-home-link' in home, "Blocco Radar non visibile nella home di collaudo"
    assert 'href="opportunita/"' in home, "Home di collaudo non collega il Radar"
    assert home.find('id="comuni"') < home.find("data-opportunity-home-link") < home.find('id="metodo"'), "Blocco Radar non collocato tra Comuni e Metodo"
    home_nav = re.search(r'<nav\b[^>]*aria-label="Navigazione principale"[^>]*>(.*?)</nav>', home, flags=re.I | re.S)
    assert home_nav and labels(home_nav.group(1)) == EXPECTED_NAV
    assert 'data-opportunity-nav="footer"' in home

    assert not (dist / "opportunita-preview").exists(), "Vecchia route preview presente nella build"

    print(f"Integrazione Radar statica OK: {total} opportunità; collocazione futura visibile in header, home e footer; sitemap ancora esclusa.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    args = parser.parse_args()
    run(args.dist)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
