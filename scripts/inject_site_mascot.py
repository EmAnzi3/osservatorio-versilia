#!/usr/bin/env python3
"""Inserisce Versilia, la mascotte che invita a Chiedi, in tutte le pagine pubbliche.

Ultimo passo di build_public_site.py (e del preflight): copre anche le pagine
costruite fuori dal renderer principale (dossier, Stato dati, Opportunità,
Percorsi). Escluse Chiedi stessa, la pagina offline e le pagine noindex.
Idempotente: rieseguito non duplica i riferimenti.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ASSETS = ("assets/mascotte.css", "assets/mascotte.js", "assets/mascotte/versilia-160.webp", "assets/mascotte/versilia-320.webp")
NOINDEX = re.compile(r'<meta\s+name="robots"\s+content="[^"]*noindex', re.IGNORECASE)


def excluded(rel: str, text: str) -> bool:
    return rel.startswith("chiedi/") or rel == "offline.html" or bool(NOINDEX.search(text))


def version(dist: Path) -> str:
    digest = hashlib.sha256()
    for name in ASSETS[:2]:
        digest.update((dist / name).read_bytes())
    return digest.hexdigest()[:10]


def inject(dist: Path = DIST) -> tuple[int, int]:
    for name in ASSETS:
        if not (dist / name).is_file():
            raise SystemExit(f"Asset della mascotte assente nel dist: {name}")
    tag = version(dist)
    done = skipped = 0
    for path in sorted(dist.rglob("*.html")):
        rel = path.relative_to(dist).as_posix()
        text = path.read_text(encoding="utf-8")
        if excluded(rel, text):
            skipped += 1
            continue
        if "</head>" not in text or "</body>" not in text:
            raise SystemExit(f"Pagina senza head/body: {rel}")
        prefix = os.path.relpath(dist, path.parent).replace(os.sep, "/")
        base = "" if prefix == "." else f"{prefix}/"
        text = re.sub(r'\s*<link rel="stylesheet" href="[^"]*assets/mascotte\.css[^"]*">', "", text)
        text = re.sub(r'\s*<script src="[^"]*assets/mascotte\.js[^"]*" defer></script>', "", text)
        text = text.replace("</head>", f'  <link rel="stylesheet" href="{base}assets/mascotte.css?v={tag}">\n</head>', 1)
        index = text.rfind("</body>")
        text = text[:index] + f'  <script src="{base}assets/mascotte.js?v={tag}" defer></script>\n' + text[index:]
        path.write_text(text, encoding="utf-8")
        done += 1
    return done, skipped


def main() -> int:
    dist = Path(sys.argv[1]) if len(sys.argv) > 1 else DIST
    done, skipped = inject(dist)
    if done < 100:
        raise SystemExit(f"Mascotte inserita in troppe poche pagine: {done}")
    print(f"Mascotte Versilia: {done} pagine, {skipped} escluse (Chiedi, offline, noindex)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
