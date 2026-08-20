#!/usr/bin/env python3
"""Costruisce /pnrr/ nel preview della PR e collega i due indicatori PNRR.

Lo script lavora esclusivamente sulla cartella ``dist`` già materializzata. La
sorgente dei dati è ``pnrrDeepDive`` aggiunta alla working copy dal materializer
Regione Toscana. Non modifica i dati canonici del repository.
"""
from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from site_chrome import ensure_sitemap_entries, extract_native_shell

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA_PATH = DIST / "data" / "site-data.json"
PAGE_PATH = DIST / "pnrr" / "index.html"
PNRR_KEYS = ("pnrrFunding", "pnrrConcluded")
SOCIAL_IMAGE = "https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg"
SOCIAL_IMAGE_ALT = "Viareggio e le Alpi Apuane, immagine di Osservatorio Versilia"
TWITTER_SITE = "@OssVersilia"
PAGE_TITLE = "Dentro il PNRR · Osservatorio Versilia"
PAGE_DESCRIPTION = "Progetti PNRR dei sette Comuni della Versilia, avanzamento ReGiS e dettaglio delle opere fisiche."
SOCIAL_DESCRIPTION = "101 progetti, avanzamento ReGiS e 22 opere fisiche nella fotografia Regione Toscana dell'11 agosto 2026."


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def format_eur(value: Any) -> str:
    number = float(value or 0)
    text = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {text}"


def format_millions(value: Any) -> str:
    return f"€ {float(value or 0) / 1_000_000:.2f} mln".replace(".", ",")


def format_percent(value: Any, digits: int = 1) -> str:
    return f"{float(value or 0):.{digits}f}%".replace(".", ",")


def read_native_shell() -> tuple[str, str, str]:
    try:
        shell = extract_native_shell(DIST, PAGE_PATH)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    return shell.header, shell.footer, shell.styles


def patch_runtime() -> None:
    path = DIST / "assets" / "app-bundle.js"
    if not path.exists():
        raise SystemExit("Bundle applicativo non trovato")
    text = path.read_text(encoding="utf-8")
    if "pageType === 'pnrr'" in text or "['status', 'pnrr', 'special'].includes(pageType)" in text:
        return
    marker = (
        "      else if (pageType === 'status') { /* contenuto prerenderizzato: non sostituire #app */ }\n"
        "      else renderNotFound();"
    )
    replacement = (
        "      else if (pageType === 'status') { /* contenuto prerenderizzato: non sostituire #app */ }\n"
        "      else if (pageType === 'pnrr') { /* approfondimento prerenderizzato: non sostituire #app */ }\n"
        "      else renderNotFound();"
    )
    if marker not in text:
        raise SystemExit("Punto di integrazione runtime PNRR non trovato: eseguire dopo build_data_status.py")
    path.write_text(text.replace(marker, replacement, 1), encoding="utf-8")


def state_class(status: str) -> str:
    lookup = {
        "Collaudo completato": "complete",
        "Collaudo avviato": "progress",
        "Lavori in esecuzione": "execution",
        "Contratto stipulato": "contract",
        "Stipula in corso": "contract",
    }
    return lookup.get(status, "progress")


def town_rows(deep: dict[str, Any]) -> str:
    rows = []
    for item in deep["towns"]:
        rows.append(
            "<tr>"
            f"<th scope=\"row\">{html.escape(item['town'])}</th>"
            f"<td class=\"is-number\">{item['projects']}</td>"
            f"<td class=\"is-number\">{item['concluded']}</td>"
            f"<td class=\"is-number\">{format_percent(item['concludedPercent'], 1)}</td>"
            f"<td class=\"is-number\">{format_eur(item['funding'])}</td>"
            "</tr>"
        )
    return "".join(rows)


def work_rows(deep: dict[str, Any]) -> str:
    works = sorted(deep["physicalWorks"]["works"], key=lambda row: (row["town"], row["title"]))
    rows = []
    for item in works:
        rows.append(
            f'<tr data-pnrr-work="true" data-town="{html.escape(item["town"], quote=True)}" '
            f'data-status="{html.escape(item["status"], quote=True)}">'
            f'<td>{html.escape(item["town"])}</td>'
            f'<th scope="row" class="pnrr-work-title">{html.escape(item["title"])}'
            f'<small>CUP {html.escape(item["cup"])}</small></th>'
            f'<td><span class="pnrr-state pnrr-state-{state_class(item["status"])}">{html.escape(item["status"])}</span></td>'
            f'<td class="is-number">{format_eur(item["funding"])}</td>'
            '</tr>'
        )
    return "".join(rows)


def build_page(data: dict[str, Any]) -> str:
    deep = data.get("pnrrDeepDive")
    if not isinstance(deep, dict):
        raise SystemExit("pnrrDeepDive assente: eseguire prima materialize_pnrr_toscana_draft.py")
    totals = deep["totals"]
    works = deep["physicalWorks"]
    header, footer, native_styles = read_native_shell()
    theme = str(data["metrics"]["pnrrFunding"]["meta"].get("theme") or "")

    status_cards = "".join(
        f'''<li class="pnrr-work-status-card"><span>{html.escape(item['status'])}</span><strong>{item['count']}</strong><small>{format_millions(item['funding'])} di quota PNRR</small></li>'''
        for item in works["statusSummary"]
    )
    json_ld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": PAGE_TITLE,
            "url": "https://osservatorioversilia.it/pnrr/",
            "description": PAGE_DESCRIPTION,
            "inLanguage": "it-IT",
            "isAccessibleForFree": True,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return f'''<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(PAGE_TITLE)}</title>
  <meta name="description" content="{html.escape(PAGE_DESCRIPTION, quote=True)}">
  <meta property="og:title" content="{html.escape(PAGE_TITLE, quote=True)}">
  <meta property="og:description" content="{html.escape(SOCIAL_DESCRIPTION, quote=True)}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="it_IT">
  <meta property="og:url" content="https://osservatorioversilia.it/pnrr/">
  <meta property="og:site_name" content="Osservatorio Versilia">
  <meta property="og:image" content="{SOCIAL_IMAGE}">
  <meta property="og:image:alt" content="{html.escape(SOCIAL_IMAGE_ALT, quote=True)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(PAGE_TITLE, quote=True)}">
  <meta name="twitter:description" content="{html.escape(SOCIAL_DESCRIPTION, quote=True)}">
  <meta name="twitter:site" content="{TWITTER_SITE}">
  <meta name="twitter:image" content="{SOCIAL_IMAGE}">
  <meta name="twitter:image:alt" content="{html.escape(SOCIAL_IMAGE_ALT, quote=True)}">
  <link rel="canonical" href="https://osservatorioversilia.it/pnrr/">
  <script type="application/ld+json">{json_ld}</script>
  <link rel="icon" href="../favicon.svg?v=20260820-ov3" type="image/svg+xml">
  <link rel="manifest" href="../site.webmanifest?v=20260813-pwa8">
  {native_styles}
  <link rel="stylesheet" href="../assets/pnrr-deep-dive.css">
  <meta name="theme-color" content="#0F3654">
</head>
<body class="antialiased" data-page="pnrr" data-theme="{html.escape(theme, quote=True)}" data-town="" data-prerendered="true">
{header}<div id="app"><main class="editorial-page pnrr-deep-dive-main" data-theme="{html.escape(theme, quote=True)}">
    <nav class="breadcrumbs page-width" aria-label="Percorso"><a href="../">Home</a><span>›</span><strong>Dentro il PNRR</strong></nav>

    <section class="editorial-hero page-width pnrr-deep-dive-hero">
      <span class="overline">Approfondimento territoriale</span>
      <h1>Dentro il PNRR.</h1>
      <p>Non solo quanto è stato finanziato, ma <strong>quali progetti</strong> risultano in attuazione e a che punto sono le <strong>opere fisiche</strong>. La lettura usa la fotografia ufficiale Regione Toscana e mantiene separati avanzamento amministrativo e collaudo effettivo.</p>
      <div class="pnrr-snapshot-note"><span>Fotografia <strong>{html.escape(deep['snapshot'])}</strong></span><span>Fonte <strong>{html.escape(deep['source'])}</strong></span></div>
    </section>

    <section class="method-detail page-width" aria-labelledby="pnrr-quadro-title">
      <div class="section-heading"><div><span class="section-number">01</span><h2 id="pnrr-quadro-title">Il quadro</h2></div><p>I valori riguardano i progetti PNRR o PNRR-PNC in cui uno dei sette Comuni è soggetto attuatore.</p></div>
      <ol class="pnrr-summary-grid">
        <li class="pnrr-summary-card is-featured"><span>Progetti censiti</span><strong>{totals['projects']}</strong><small>PNRR / PNRR-PNC · PNC puro escluso</small></li>
        <li class="pnrr-summary-card"><span>Fase 5 · conclusione</span><strong>{totals['concluded']}</strong><small>{format_percent(totals['concluded'] / totals['projects'] * 100, 1)} dei progetti</small></li>
        <li class="pnrr-summary-card"><span>Quota PNRR</span><strong>{format_millions(totals['funding'])}</strong><small>Finanziamento censito, non spesa effettuata</small></li>
        <li class="pnrr-summary-card"><span>Opere fisiche</span><strong>{works['count']}</strong><small>{format_percent(works['fundingSharePercent'], 1)} delle risorse PNRR censite</small></li>
      </ol>
      <div class="pnrr-table-scroll" style="margin-top:28px"><table class="pnrr-table"><thead><tr><th>Comune</th><th class="is-number">Progetti</th><th class="is-number">Fase 5</th><th class="is-number">Quota fase 5</th><th class="is-number">Quota PNRR</th></tr></thead><tbody>{town_rows(deep)}</tbody></table></div>
    </section>

    <section class="method-detail page-width" aria-labelledby="pnrr-fasi-title">
      <div class="section-heading"><div><span class="section-number">02</span><h2 id="pnrr-fasi-title">A che punto sono i progetti</h2></div><p>Le macrofasi ReGiS descrivono l'avanzamento amministrativo del progetto, non certificano da sole che un'opera sia collaudata.</p></div>
      <ol class="pnrr-phase-grid">
        <li class="pnrr-phase-card"><span>5. Conclusione</span><strong>{totals['concluded']}</strong><small>Progetti classificati nella macrofase finale ReGiS</small></li>
        <li class="pnrr-phase-card"><span>4. Esecuzione</span><strong>{totals['execution']}</strong><small>Progetti nella fase esecutiva</small></li>
        <li class="pnrr-phase-card"><span>3. Stipula</span><strong>{totals['contracting']}</strong><small>Progetto ancora nella fase di stipula</small></li>
      </ol>
      <div class="pnrr-method-note"><p><strong>Perché non scriviamo “74 progetti realizzati”?</strong> Per le opere fisiche il dettaglio ReGiS mostra che molte sono già nella macrofase 5 ma hanno ancora il collaudo avviato. Per questo il sito mantiene distinta la fase amministrativa dallo stato effettivo dell'opera.</p></div>
    </section>

    <section class="method-detail page-width" aria-labelledby="pnrr-opere-title">
      <div class="section-heading"><div><span class="section-number">03</span><h2 id="pnrr-opere-title">Le 22 opere fisiche</h2></div><p>Il campo “natura” separa lavori pubblici, opere e impiantistica dai servizi digitali e dagli acquisti di beni.</p></div>
      <ol class="pnrr-work-status-grid">{status_cards}</ol>
      <div class="pnrr-table-scroll"><table class="pnrr-table"><thead><tr><th>Comune</th><th>Opera</th><th>Stato ReGiS di dettaglio</th><th class="is-number">Quota PNRR</th></tr></thead><tbody>{work_rows(deep)}</tbody></table></div>
      <div class="pnrr-method-note"><p>Le 22 opere assorbono <strong>{format_eur(works['funding'])}</strong>, pari al <strong>{format_percent(works['fundingSharePercent'], 1)}</strong> della quota PNRR censita nei 101 progetti. “Collaudo completato”, “collaudo avviato” e gli altri stati sono riportati come classificazioni ReGiS, senza reinterpretazioni.</p></div>
    </section>

    <section class="method-detail page-width" aria-labelledby="pnrr-metodo-title">
      <div class="section-heading"><div><span class="section-number">04</span><h2 id="pnrr-metodo-title">Fonte e metodo</h2></div><p>La Regione Toscana diventa la fonte pubblica e operativa; ReGiS resta una delle provenienze amministrative integrate nel dataset regionale.</p></div>
      <div class="indicator-governance-grid"><dl><div><dt>Fonte utilizzata</dt><dd>{html.escape(deep['source'])}</dd></div><div><dt>Fotografia</dt><dd>{html.escape(deep['snapshot'])}</dd></div><div><dt>Perimetro</dt><dd>PNRR e PNRR-PNC · PNC puro escluso</dd></div><div><dt>Soggetto</dt><dd>Comune come soggetto attuatore</dd></div><div><dt>Deduplicazione</dt><dd>id_progetto</dd></div><div><dt>Conclusione</dt><dd>fase_avanzamento_da_regis = 5. conclusione</dd></div></dl><div><h3>Cosa rimane fuori, per ora</h3><p>Percentuale di spesa, date previste/effettive e stato gare/CIG non vengono trasformati in indicatori finché non è completata una validazione specifica dei rispettivi denominatori e campi.</p><div class="pnrr-source-row"><a class="source-pill" href="{html.escape(deep['sourceUrl'], quote=True)}" target="_blank" rel="noreferrer">Open Data Regione Toscana ↗</a><a class="button-link" href="../indicatori/risorse-pnrr-per-residente/">Risorse PNRR per residente →</a></div></div></div>
    </section>
  </main></div>
{footer}<noscript><div class="app-error">Il sito richiede JavaScript per ricerca e navigazione interattiva.</div></noscript>
  <script src="../assets/app-bundle.js" defer></script>
  <script src="../assets/social-presence.js" defer></script>
</body>
</html>
'''


def teaser_markup() -> str:
    return '''<section class="pnrr-deep-dive-teaser page-width" data-pnrr-deep-dive-teaser="true"><div><span class="overline">Approfondimento</span><h2>Dentro il PNRR</h2><p>101 progetti, 74 in fase 5 e 22 opere fisiche lette con lo stato ReGiS di dettaglio. La macrofase “conclusione” resta distinta dal collaudo effettivo.</p></div><a class="button-link" href="../../pnrr/">Apri l'approfondimento <span>→</span></a></section>'''


def inject_indicator_teasers(data: dict[str, Any]) -> None:
    for key in PNRR_KEYS:
        metric = data["metrics"].get(key)
        if not isinstance(metric, dict):
            raise SystemExit(f"Indicatore PNRR assente: {key}")
        slug = slugify(str(metric["meta"]["label"]))
        path = DIST / "indicatori" / slug / "index.html"
        if not path.exists():
            raise SystemExit(f"Pagina indicatore PNRR non trovata: {path}")
        text = path.read_text(encoding="utf-8")
        if "assets/pnrr-deep-dive.css" not in text:
            text = text.replace("</head>", '  <link rel="stylesheet" href="../../assets/pnrr-deep-dive.css">\n</head>')
        if 'data-pnrr-deep-dive-teaser="true"' not in text:
            marker = '<section class="indicator-method page-width"'
            if marker not in text:
                raise SystemExit(f"Punto di inserimento PNRR non trovato in {path}")
            text = text.replace(marker, teaser_markup() + "\n      " + marker, 1)
        path.write_text(text, encoding="utf-8")


def main() -> int:
    if not DATA_PATH.exists():
        raise SystemExit("dist/data/site-data.json non trovato")
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    PAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAGE_PATH.write_text(build_page(data), encoding="utf-8")
    patch_runtime()
    inject_indicator_teasers(data)
    ensure_sitemap_entries(DIST, ("https://osservatorioversilia.it/pnrr/",))
    print("Bozza Dentro il PNRR costruita: /pnrr/ + collegamenti dai due indicatori")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
