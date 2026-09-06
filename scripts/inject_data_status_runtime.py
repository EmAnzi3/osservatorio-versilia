#!/usr/bin/env python3
"""Incorpora i metadata di stato nelle schede indicatore prerenderizzate.

L'applicazione principale può rerenderizzare il contenuto di #app nel browser.
Per evitare fetch e mantenere i metadata derivati disponibili anche dopo quel
rerender, ogni scheda riceve un piccolo payload JSON locale e l'enhancer comune.
L'enhancer viene inoltre caricato sulle pagine pubbliche per mantenere un accesso
stabile a /stato-dati/ nella navigazione principale e nel footer.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
SOCIAL_IMAGE = "https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg"


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def italian_date(value: str) -> str:
    if not value:
        return "Non ancora registrato"
    from datetime import datetime

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    months = [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
    ]
    return f"{parsed.day} {months[parsed.month - 1]} {parsed.year}"


def enrich_status_page(payload: dict) -> None:
    path = DIST / "stato-dati" / "index.html"
    text = path.read_text(encoding="utf-8")
    if "../assets/fonts.css" not in text:
        text = text.replace(
            '<link rel="canonical" href="https://osservatorioversilia.it/stato-dati/">',
            '<link rel="canonical" href="https://osservatorioversilia.it/stato-dati/">\n'
            '  <link rel="stylesheet" href="../assets/fonts.css">',
            1,
        )

    if 'property="og:url"' not in text:
        social = f'''  <meta property="og:url" content="https://osservatorioversilia.it/stato-dati/">
  <meta property="og:site_name" content="Osservatorio Versilia">
  <meta property="og:image" content="{SOCIAL_IMAGE}">
  <meta property="og:image:alt" content="Versilia, Viareggio e Alpi Apuane">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Stato dei dati · Osservatorio Versilia">
  <meta name="twitter:description" content="Quando sono stati controllati i dati, quale periodo è pubblicato e cosa sappiamo sul prossimo aggiornamento.">
  <meta name="twitter:site" content="@OssVersilia">
  <meta name="twitter:image" content="{SOCIAL_IMAGE}">
  <meta name="twitter:image:alt" content="Versilia, Viareggio e Alpi Apuane">
'''
        text = text.replace(
            '  <meta property="og:locale" content="it_IT">\n',
            '  <meta property="og:locale" content="it_IT">\n' + social,
            1,
        )

    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    limited = int(counts.get("source_access_limited", 0) or 0)
    if "Controllo automatico limitato</h3>" not in text:
        new_release = '<li><span>04</span><h3>Nuovi rilasci da verificare</h3>'
        replacement = (
            f'<li><span>04</span><h3>Controllo automatico limitato</h3><strong>{limited}</strong></li>\n'
            '        <li><span>05</span><h3>Nuovi rilasci da verificare</h3>'
        )
        if new_release not in text:
            raise SystemExit("Card riepilogo nuovi rilasci non trovata in /stato-dati/")
        text = text.replace(new_release, replacement, 1)
        text = text.replace(
            '<li><span>05</span><h3>Fonti con problemi</h3>',
            '<li><span>06</span><h3>Fonti con problemi</h3>',
            1,
        )

    if "Il portale ufficiale limita le richieste automatizzate" not in text:
        source_checked_card = (
            '<li><span class="status-badge status-neutral">Fonte controllata</span>'
            '<p>La fonte è raggiungibile, ma il controllo automatico non può certificare da solo quale sia l\'ultima annualità.</p></li>'
        )
        limited_card = (
            source_checked_card
            + '<li><span class="status-badge status-neutral">Controllo automatico limitato</span>'
            '<p>Il portale ufficiale limita le richieste automatizzate; la fonte resta sottoposta a verifica manuale.</p></li>'
        )
        if source_checked_card not in text:
            raise SystemExit("Legenda Fonte controllata non trovata in /stato-dati/")
        text = text.replace(source_checked_card, limited_card, 1)

    path.write_text(text, encoding="utf-8")


def ensure_status_sitemap_lastmod() -> None:
    path = DIST / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    url = "https://osservatorioversilia.it/stato-dati/"
    bare = f"<url><loc>{url}</loc></url>"
    complete = f"<url><loc>{url}</loc><lastmod>{date.today().isoformat()}</lastmod></url>"
    if bare in text:
        text = text.replace(bare, complete, 1)
        path.write_text(text, encoding="utf-8")


def inject_global_enhancer() -> int:
    asset = DIST / "assets" / "data-status.js"
    injected = 0
    for path in DIST.rglob("*.html"):
        if path.name == "offline.html":
            continue
        text = path.read_text(encoding="utf-8")
        if "assets/data-status.js" in text:
            continue
        relative = Path(os.path.relpath(asset, path.parent)).as_posix()
        text = text.replace(
            "</body>",
            f'  <script src="{relative}" defer></script>\n</body>',
            1,
        )
        path.write_text(text, encoding="utf-8")
        injected += 1
    return injected


def main() -> None:
    status_path = DIST / "data" / "data-status.json"
    payload = json.loads(status_path.read_text(encoding="utf-8"))
    metrics = payload.get("metrics") or []
    inline_metrics = [
        item for item in metrics
        if not item.get("isExternalClimate") and not item.get("isSpecialRoute")
    ]
    expected_inline = len(inline_metrics)
    by_slug = {slugify(str(item["label"])): item for item in metrics}
    injected = 0

    for path in (DIST / "indicatori").glob("*/index.html"):
        metric = by_slug.get(path.parent.name)
        if not metric:
            continue
        text = path.read_text(encoding="utf-8")
        if 'id="ov-indicator-status"' in text:
            injected += 1
            continue

        local = {
            "publishedPeriod": metric.get("publishedPeriod") or "—",
            "statusLabel": metric.get("statusLabel") or "Verifica necessaria",
            "statusTone": metric.get("statusTone") or "problem",
            "statusDescription": metric.get("statusDescription") or "",
            "lastCheckedLabel": italian_date(str(metric.get("lastChecked") or "")),
            "cadenceNote": metric.get("cadenceNote") or "",
            "nextExpectedRelease": metric.get("nextExpectedRelease"),
        }
        encoded = json.dumps(local, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        block = (
            f'<script type="application/json" id="ov-indicator-status">{encoded}</script>\n'
            '  <script src="../../assets/data-status.js" defer></script>\n'
        )
        text = text.replace("</body>", block + "</body>", 1)
        path.write_text(text, encoding="utf-8")
        injected += 1

    if injected != expected_inline:
        raise SystemExit(
            f"Attese {expected_inline} schede indicatore inline, payload incorporato in {injected}"
        )
    enrich_status_page(payload)
    ensure_status_sitemap_lastmod()
    global_pages = inject_global_enhancer()
    print(
        f"Payload stato dati incorporato nelle {expected_inline} schede indicatore; "
        f"enhancer navigazione aggiunto a {global_pages} pagine ulteriori"
    )


if __name__ == "__main__":
    main()
