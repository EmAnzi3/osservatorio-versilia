#!/usr/bin/env python3
"""Allinea le pagine editoriali al layout canonico già prerenderizzato.

Le pagine speciali conservano il proprio <main> e i propri asset specifici, ma
header, footer e asset strutturali vengono ricavati da pagine standard della
stessa profondità. In questo modo il preview locale usa esattamente la stessa
shell visuale del sito e non una sua imitazione.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

HEADER_RE = re.compile(r"<header\b[^>]*>.*?</header>", re.I | re.S)
FOOTER_RE = re.compile(r"<footer\b[^>]*>.*?</footer>", re.I | re.S)
HEAD_RE = re.compile(r"<head\b[^>]*>(.*?)</head>", re.I | re.S)
LINK_RE = re.compile(r"<link\b[^>]*>", re.I)
META_RE = re.compile(r"<meta\b[^>]*>", re.I)
PWA_SCRIPT_RE = re.compile(r'<script\b[^>]*src="[^"]*assets/pwa\.js[^"]*"[^>]*></script>', re.I)

STRUCTURAL_META_NAMES = {
    "theme-color",
    "mobile-web-app-capable",
    "apple-mobile-web-app-capable",
    "apple-mobile-web-app-status-bar-style",
    "apple-mobile-web-app-title",
}
STRUCTURAL_LINK_RELS = {"icon", "manifest", "apple-touch-icon", "stylesheet"}


def attr(tag: str, name: str) -> str:
    match = re.search(rf'\b{re.escape(name)}="([^"]*)"', tag, re.I)
    return match.group(1) if match else ""


def structural_head_tags(template: str) -> list[str]:
    head_match = HEAD_RE.search(template)
    if not head_match:
        raise RuntimeError("Head canonico non trovato")
    head = head_match.group(1)
    tags: list[str] = []
    for tag in LINK_RE.findall(head):
        rel = attr(tag, "rel").lower()
        if rel in STRUCTURAL_LINK_RELS:
            tags.append(tag)
    for tag in META_RE.findall(head):
        name = attr(tag, "name").lower()
        if name in STRUCTURAL_META_NAMES:
            tags.append(tag)
    return tags


def tag_key(tag: str) -> tuple[str, str]:
    if tag.lower().startswith("<link"):
        rel = attr(tag, "rel").lower()
        href = attr(tag, "href").split("?", 1)[0]
        return (rel, href.rsplit("/", 1)[-1])
    return ("meta", attr(tag, "name").lower())


def sync_page(target: Path, template: Path) -> None:
    if not target.exists():
        raise RuntimeError(f"Pagina editoriale mancante: {target}")
    if not template.exists():
        raise RuntimeError(f"Template canonico mancante: {template}")

    text = target.read_text(encoding="utf-8")
    canonical = template.read_text(encoding="utf-8")
    header = HEADER_RE.search(canonical)
    footer = FOOTER_RE.search(canonical)
    if not header or not footer:
        raise RuntimeError(f"Shell canonica incompleta: {template}")

    if not HEADER_RE.search(text) or not FOOTER_RE.search(text):
        raise RuntimeError(f"Shell editoriale incompleta: {target}")
    text = HEADER_RE.sub(header.group(0), text, count=1)
    text = FOOTER_RE.sub(footer.group(0), text, count=1)

    existing_head = HEAD_RE.search(text)
    if not existing_head:
        raise RuntimeError(f"Head editoriale mancante: {target}")
    existing = existing_head.group(1)
    existing_keys = {tag_key(tag) for tag in LINK_RE.findall(existing)}
    existing_keys |= {tag_key(tag) for tag in META_RE.findall(existing)}
    missing = [tag for tag in structural_head_tags(canonical) if tag_key(tag) not in existing_keys]
    if missing:
        text = text.replace("</head>", "  " + "\n  ".join(missing) + "\n</head>", 1)

    if "assets/pwa.js" not in text:
        pwa = PWA_SCRIPT_RE.search(canonical)
        if not pwa:
            raise RuntimeError(f"Bootstrap PWA canonico non trovato: {template}")
        text = text.replace("</body>", f"  {pwa.group(0)}\n</body>", 1)

    target.write_text(text, encoding="utf-8")


def main() -> None:
    depth1 = DIST / "progetto" / "index.html"
    depth2 = DIST / "confronta" / "demografia" / "index.html"

    targets: list[tuple[Path, Path]] = [
        (DIST / "confronta" / "meteo-clima" / "index.html", depth2),
        (DIST / "letture" / "index.html", depth1),
    ]
    reading_root = DIST / "letture"
    for path in sorted(reading_root.glob("*/index.html")):
        targets.append((path, depth2))

    for target, template in targets:
        sync_page(target, template)

    for target, _ in targets:
        text = target.read_text(encoding="utf-8")
        if 'class="ov-mark-svg"' not in text:
            raise RuntimeError(f"Marchio canonico assente dopo sync: {target}")
        if "assets/brand.css" not in text or "assets/pwa.css" not in text or "assets/pwa.js" not in text:
            raise RuntimeError(f"Asset strutturali mancanti dopo sync: {target}")

    print(f"Layout editoriale sincronizzato con la shell canonica: {len(targets)} pagine")


if __name__ == "__main__":
    main()
