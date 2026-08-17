#!/usr/bin/env python3
"""Aggiunge al build statico la pagina Stato dei dati e il pannello indicatori."""
from __future__ import annotations

from datetime import date
import json
import shutil
from pathlib import Path

from data_status import build_public_payload

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_status_page() -> None:
    source = ROOT / "stato-dati"
    target = DIST / "stato-dati"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def write_public_status() -> dict:
    data = load_json(ROOT / "data" / "site-data.json")
    registry = load_json(ROOT / "data" / "source-registry.json")
    state = load_json(ROOT / "data" / "source-monitor-state.json")
    payload = build_public_payload(data, registry, state)
    target = DIST / "data" / "data-status.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def inject_indicator_assets() -> int:
    count = 0
    for path in sorted((DIST / "indicatori").glob("*/index.html")):
        text = path.read_text(encoding="utf-8")
        if "assets/data-status.css" not in text:
            text = text.replace("</head>", '  <link rel="stylesheet" href="../../assets/data-status.css">\n</head>')
        if "assets/data-status.js" not in text:
            text = text.replace("</body>", '  <script src="../../assets/data-status.js" defer></script>\n</body>')
        path.write_text(text, encoding="utf-8")
        count += 1
    return count


def patch_sitemap() -> None:
    sitemap = DIST / "sitemap.xml"
    if not sitemap.exists():
        return
    text = sitemap.read_text(encoding="utf-8")
    url = "https://osservatorioversilia.it/stato-dati/"
    if url in text:
        return
    lastmod = date.today().isoformat()
    entry = f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod></url>\n"
    text = text.replace("</urlset>", entry + "</urlset>")
    sitemap.write_text(text, encoding="utf-8")


def main() -> None:
    if not DIST.exists():
        raise SystemExit("dist/ non esiste: eseguire prima la build statica")
    ensure_status_page()
    payload = write_public_status()
    indicator_count = inject_indicator_assets()
    patch_sitemap()
    expected = int(payload.get("summary", {}).get("metricCount", 0))
    if expected != 127:
        raise SystemExit(f"Attesi 127 indicatori nello stato pubblico, trovati {expected}")
    if indicator_count != 123:
        raise SystemExit(f"Attese 123 pagine indicatore canoniche, trovate {indicator_count}")
    print(f"Stato dati: {expected} indicatori; pannello in {indicator_count} pagine canoniche")


if __name__ == "__main__":
    main()
