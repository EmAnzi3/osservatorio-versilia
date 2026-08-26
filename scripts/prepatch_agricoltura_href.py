#!/usr/bin/env python3
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "assets/app-parts/03.txt"
t = p.read_text(encoding="utf-8")
new = "      const rowSlug=row.slug || normalize(row.town).replaceAll(' ','-');\n      const href=route(`comuni/${rowSlug}/?${query}`);"
if new not in t:
    old = "      const href = route(`comuni/${row.slug}/?${query}`);"
    if old not in t:
        raise RuntimeError("Href composite comunale non trovato")
    t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("Href comunali composite corretti.")
