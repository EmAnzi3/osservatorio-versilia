#!/usr/bin/env python3
"""Aggiunge al build statico la pagina Stato dei dati e il pannello indicatori."""
from __future__ import annotations

from datetime import date
import html
import json
import re
import shutil
import unicodedata
from pathlib import Path

from data_status import build_public_payload

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFD", str(value).lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


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


def _status_badge(item: dict) -> str:
    severity = esc(item.get("statusSeverity") or "neutral")
    label = esc(item.get("statusLabel") or "Verifica necessaria")
    return f'<span class="data-status-badge is-{severity}"><span aria-hidden="true"></span>{label}</span>'


def _checked_label(value: object) -> str:
    text = str(value or "").strip()
    return text[:10] if text else "Non ancora registrato"


def prerender_status_page(payload: dict) -> None:
    """Scrive i 127 stati anche nell'HTML: la pagina resta utile senza JS."""
    path = DIST / "stato-dati" / "index.html"
    text = path.read_text(encoding="utf-8")
    items = sorted(
        payload.get("metrics", {}).values(),
        key=lambda item: (str(item.get("theme") or ""), str(item.get("label") or "")),
    )
    counts = payload.get("summary", {}).get("statusCounts", {})
    checked = int(payload.get("summary", {}).get("checkedMetricCount", 0) or 0)
    total = int(payload.get("summary", {}).get("metricCount", len(items)) or 0)

    cards = [
        ("Indicatori", total, "catalogo complessivo"),
        ("Controllati", checked, "con controllo fonte registrato"),
        ("Ultimo dato disponibile", counts.get("current", 0), "periodo confermato"),
        (
            "Da verificare",
            int(counts.get("new_release_to_review", 0) or 0)
            + int(counts.get("verification_required", 0) or 0),
            "rilasci o attualità da controllare",
        ),
        ("Fonti con problemi", counts.get("source_unavailable", 0), "temporaneamente non verificabili"),
    ]
    summary = "".join(
        f"<article><span>{esc(label)}</span><strong>{esc(value)}</strong><small>{esc(detail)}</small></article>"
        for label, value, detail in cards
    )

    rows = []
    for item in items:
        label = str(item.get("label") or item.get("metricKey") or "")
        href = f"../indicatori/{slugify(label)}/"
        source_status = item.get("sourceStatus")
        source_label = {
            "reachable": "Raggiungibile",
            "unavailable": "Non raggiungibile al controllo",
        }.get(source_status, "Non controllata")
        rows.append(
            f'<article class="data-status-row" data-status="{esc(item.get("status"))}" data-theme="{esc(item.get("theme"))}">'
            f'<div class="data-status-row-main"><span class="data-status-theme">{esc(item.get("theme"))}</span>'
            f'<h2><a href="{esc(href)}">{esc(label)}</a></h2><p>{esc(item.get("publisher"))}</p></div>'
            f'<div class="data-status-row-period"><span>Periodo</span><strong>{esc(item.get("publishedPeriod") or "—")}</strong></div>'
            f'<div class="data-status-row-state">{_status_badge(item)}<small>Controllo: {esc(_checked_label(item.get("checkedAt")))}</small></div>'
            '<details><summary>Dettagli aggiornamento</summary><dl>'
            f'<div><dt>Frequenza</dt><dd>{esc(item.get("frequencyLabel") or "Non determinabile")}</dd></div>'
            f'<div><dt>Cadenza indicativa</dt><dd>{esc(item.get("releaseCadenceLabel") or "Non determinabile")}</dd></div>'
            f'<div><dt>Stato della fonte</dt><dd>{esc(source_label)}</dd></div>'
            f'</dl><p>{esc(item.get("statusDescription") or "")}</p></details></article>'
        )

    static_markup = (
        f'<section class="data-status-summary" aria-label="Sintesi dello stato dei dati">{summary}</section>'
        f'<p class="data-status-count">{total} indicatori mostrati su {total}. Attiva JavaScript per usare filtri e ricerca.</p>'
        f'<div class="data-status-list" id="status-list">{"".join(rows)}</div>'
    )
    placeholder = '<div id="data-status-app"><div class="app-loading" role="status">Caricamento dello stato dei dati…</div></div>'
    if placeholder not in text:
        raise RuntimeError("Placeholder Stato dei dati non trovato")
    text = text.replace(placeholder, f'<div id="data-status-app">{static_markup}</div>')
    path.write_text(text, encoding="utf-8")


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
    prerender_status_page(payload)
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
