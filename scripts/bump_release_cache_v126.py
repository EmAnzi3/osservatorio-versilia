#!/usr/bin/env python3
"""Allinea le revisioni cache/PWA alla release v1.26.0."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "20260830-v125-erp-arrears"
NEW = "20260831-v126-bonifica-rischio"
FILES = [
    ROOT / "assets/app.js",
    ROOT / "assets/export-v161.js",
    ROOT / "assets/ux-history.js",
    ROOT / "scripts/build_static_safe.py",
    ROOT / "scripts/build_static_brand.py",
]


def replace_token(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old in text:
        text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
    elif new not in text:
        raise RuntimeError(f"Token release non trovato in {path}")


def main() -> None:
    for path in FILES:
        replace_token(path, OLD, NEW)
    replace_token(ROOT / "service-worker.js", f"ov-pwa-{OLD}", f"ov-pwa-{NEW}")
    replace_token(ROOT / "scripts/build_static_brand.py", 'PWA_JS_REVISION = "catalog-v125"', 'PWA_JS_REVISION = "catalog-v126"')
    print("Cache/PWA revision v1.26.0 allineata")


if __name__ == "__main__":
    main()
