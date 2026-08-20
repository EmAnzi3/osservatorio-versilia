#!/usr/bin/env python3
"""Materializza la pagina pubblica /stato-dati/ e i metadata derivati.

Da eseguire dopo la build statica principale. Non modifica i dati canonici.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from data_status_model import STATUS_META, build_public_status
from site_chrome import ensure_sitemap_entries, extract_native_shell

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON non valido: {path}")
    return value


def fmt_date(value: str) -> str:
    if not value:
        return "Non ancora registrato"
    try:
        from datetime import datetime

        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        months = [
            "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
            "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
        ]
        return f"{date.day} {months[date.month - 1]} {date.year}"
    except ValueError:
        return value


def metric_slug(metric: dict[str, Any]) -> str:
    import unicodedata

    value = str(metric.get("label") or "")
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def metric_href(metric: dict[str, Any]) -> str:
    return f"../indicatori/{metric_slug(metric)}/"


def next_release_markup(metric: dict[str, Any]) -> str:
    release = metric.get("nextExpectedRelease")
    if not isinstance(release, dict):
        return ""
    value = html.escape(str(release.get("value") or ""))
    if not value:
        return ""
    return f'<small class="status-next">Prossimo rilascio atteso: {value}</small>'


def read_native_shell() -> tuple[str, str, str, str]:
    """Riusa la shell canonica e ne verifica il contratto di navigazione."""
    try:
        shell = extract_native_shell(DIST, DIST / "stato-dati" / "index.html")
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if not shell.app_bundle:
        raise SystemExit("Runtime applicativo canonico non trovato")
    return shell.header, shell.footer, shell.styles, shell.app_bundle


def patch_status_runtime() -> None:
    """Consente al runtime canonico di montare shell/ricerca senza sovrascrivere #app."""
    path = DIST / "assets" / "app-bundle.js"
    if not path.exists():
        raise SystemExit("Bundle applicativo non trovato")
    text = path.read_text(encoding="utf-8")
    marker = "      else if (pageType === 'feedback') renderFeedback(data);\n      else renderNotFound();"
    replacement = (
        "      else if (pageType === 'feedback') renderFeedback(data);\n"
        "      else if (pageType === 'status') { /* contenuto prerenderizzato: non sostituire #app */ }\n"
        "      else renderNotFound();"
    )
    if marker not in text:
        if "pageType === 'status'" in text:
            return
        raise SystemExit("Punto di integrazione runtime stato dati non trovato")
    path.write_text(text.replace(marker, replacement, 1), encoding="utf-8")


def build_page(status: dict[str, Any]) -> str:
    counts = status["counts"]
    themes = sorted({row["themeLabel"] for row in status["metrics"] if row["themeLabel"]})
    rows = []
    for row in status["metrics"]:
        rows.append(
            f'''<tr data-status="{html.escape(row['status'])}" data-theme="{html.escape(row['themeLabel'])}">
              <th scope="row"><a href="{metric_href(row)}">{html.escape(row['label'])}</a><small>{html.escape(row['themeLabel'])}</small></th>
              <td>{html.escape(row['publishedPeriod'] or '—')}</td>
              <td><span class="status-badge status-{html.escape(row['statusTone'])}">{html.escape(row['statusLabel'])}</span>{next_release_markup(row)}</td>
              <td>{html.escape(fmt_date(row['lastChecked']))}</td>
            </tr>'''
        )

    status_options = "".join(
        f'<option value="{html.escape(key)}">{html.escape(meta["label"])}</option>'
        for key, meta in STATUS_META.items()
    )
    theme_options = "".join(
        f'<option value="{html.escape(theme)}">{html.escape(theme)}</option>' for theme in themes
    )
    json_ld = json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "WebPage",
                    "name": "Stato dei dati · Osservatorio Versilia",
                    "url": "https://osservatorioversilia.it/stato-dati/",
                    "description": "Stato di aggiornamento, ultimo controllo e frequenza delle fonti per i 127 indicatori di Osservatorio Versilia.",
                    "inLanguage": "it-IT",
                    "isAccessibleForFree": True,
                },
                {
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {
                            "@type": "ListItem",
                            "position": 1,
                            "name": "Osservatorio Versilia",
                            "item": "https://osservatorioversilia.it/",
                        },
                        {
                            "@type": "ListItem",
                            "position": 2,
                            "name": "Stato dei dati",
                            "item": "https://osservatorioversilia.it/stato-dati/",
                        },
                    ],
                },
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    header, footer, native_styles, app_bundle = read_native_shell()
    app_bundle = html.escape(app_bundle, quote=True)

    return f'''<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Stato dei dati · Osservatorio Versilia</title>
  <meta name="description" content="Stato di aggiornamento, ultimo controllo e frequenza delle fonti per i 127 indicatori di Osservatorio Versilia.">
  <meta property="og:title" content="Stato dei dati · Osservatorio Versilia">
  <meta property="og:description" content="Quando sono stati controllati i dati, quale periodo è pubblicato e cosa sappiamo sul prossimo aggiornamento.">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="it_IT">
  <meta property="og:url" content="https://osservatorioversilia.it/stato-dati/">
  <meta property="og:site_name" content="Osservatorio Versilia">
  <meta property="og:image" content="https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg">
  <meta property="og:image:alt" content="Viareggio e le Alpi Apuane, immagine di Osservatorio Versilia">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Stato dei dati · Osservatorio Versilia">
  <meta name="twitter:description" content="Quando sono stati controllati i dati, quale periodo è pubblicato e cosa sappiamo sul prossimo aggiornamento.">
  <meta name="twitter:site" content="@OssVersilia">
  <meta name="twitter:image" content="https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg">
  <meta name="twitter:image:alt" content="Viareggio e le Alpi Apuane, immagine di Osservatorio Versilia">
  <link rel="canonical" href="https://osservatorioversilia.it/stato-dati/">
  <script type="application/ld+json">{json_ld}</script>
  <link rel="icon" href="../favicon.svg?v=20260807-ov" type="image/svg+xml">
  <link rel="manifest" href="../site.webmanifest?v=20260813-pwa8">
  {native_styles}
  <link rel="stylesheet" href="../assets/data-status.css">
  <meta name="theme-color" content="#0F3654">
</head>
<body class="antialiased" data-page="status" data-theme="" data-town="" data-prerendered="true" data-status-app-bundle="{app_bundle}">
{header}<div id="app"><main class="editorial-page data-status-main">
    <section class="editorial-hero page-width data-status-hero">
      <span class="overline">Trasparenza dei dati</span>
      <h1>Stato dei dati.</h1>
      <p>Un dato può essere precedente all'anno corrente ed essere comunque l'ultimo ufficialmente disponibile. Qui distinguiamo il <strong>periodo pubblicato</strong>, l'<strong>attualità rispetto alla fonte</strong> e la <strong>data dell'ultimo controllo</strong>.</p>
      <div class="data-status-check"><span>Ultimo controllo generale</span><strong>{html.escape(fmt_date(status['lastGeneralCheck']))}</strong></div>
    </section>

    <section class="method-detail page-width data-status-overview" aria-label="Riepilogo stato dati">
      <div class="section-heading"><div><span class="section-number">01</span><h2>Quadro generale</h2></div><p>Una fotografia del monitor: controlli eseguiti, verifiche ancora necessarie e nuovi rilasci da esaminare.</p></div>
      <ol class="principles-grid data-status-summary">
        <li><span>01</span><h3>Indicatori</h3><strong>{status['metricCount']}</strong></li>
        <li><span>02</span><h3>Ultimo dato verificato</h3><strong>{counts.get('current', 0)}</strong></li>
        <li><span>03</span><h3>Fonti controllate</h3><strong>{counts.get('source_checked', 0)}</strong></li>
        <li><span>04</span><h3>Nuovi rilasci da verificare</h3><strong>{counts.get('release_detected', 0)}</strong></li>
        <li><span>05</span><h3>Fonti con problemi</h3><strong>{counts.get('source_unavailable', 0) + counts.get('verification_required', 0)}</strong></li>
      </ol>
    </section>

    <section class="method-detail page-width data-status-explainer">
      <div class="section-heading"><div><span class="section-number">02</span><h2>Come leggere gli stati</h2></div><p>La raggiungibilità di una fonte non equivale automaticamente a un dato aggiornato.</p></div>
      <ul class="principles-grid data-status-legend">
        <li><span class="status-badge status-ok">Ultimo dato disponibile</span><p>Il periodo pubblicato coincide con l'ultimo periodo verificato sulla fonte.</p></li>
        <li><span class="status-badge status-neutral">Fonte controllata</span><p>La fonte è raggiungibile, ma il controllo automatico non può certificare da solo quale sia l'ultima annualità.</p></li>
        <li><span class="status-badge status-warn">Nuovo rilascio da verificare</span><p>Esiste un segnale di un periodo più recente; nessun valore viene pubblicato senza validazione.</p></li>
        <li><span class="status-badge status-problem">Fonte temporaneamente non verificabile</span><p>Il controllo non ha potuto accedere alla fonte; il dato pubblicato resta invariato.</p></li>
      </ul>
    </section>

    <section class="method-detail page-width data-status-table-section">
      <div class="section-heading"><div><span class="section-number">03</span><h2>Dettaglio dei 127 indicatori</h2></div><p>I filtri agiscono solo sulla vista e non modificano i dati.</p></div>
      <div class="data-status-filters">
        <label>Tematica<select data-status-theme><option value="">Tutte</option>{theme_options}</select></label>
        <label>Stato<select data-status-filter><option value="">Tutti</option>{status_options}</select></label>
        <span data-status-visible aria-live="polite"></span>
      </div>
      <div class="data-status-table-wrap">
        <table class="data-status-table">
          <thead><tr><th>Indicatore</th><th>Periodo</th><th>Stato</th><th>Ultimo controllo</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="independence-note page-width data-status-policy">
      <div><span class="overline">Metodo di pubblicazione</span><h2>Nessuna pubblicazione automatica.</h2></div>
      <p>Il monitor può rilevare cambiamenti o nuovi rilasci, ma resta distinta la sequenza <strong>rilevazione → validazione → pubblicazione</strong>. I nuovi valori entrano nel sito solo dopo verifica.</p>
    </section>
  </main></div>
{footer}<noscript><div class="app-error">Il sito richiede JavaScript per ricerca, filtri e navigazione interattiva.</div></noscript>
  <script src="../assets/data-status.js" defer></script>
</body>
</html>
'''


def indicator_status_block(metric: dict[str, Any]) -> str:
    return (
        f'<div data-data-status-row="period"><dt>Periodo pubblicato</dt><dd>{html.escape(metric["publishedPeriod"] or "—")}</dd></div>'
        f'<div data-data-status-row="state"><dt>Stato del dato</dt><dd>'
        f'<span class="status-badge status-{html.escape(metric["statusTone"])}">{html.escape(metric["statusLabel"])}</span>'
        f'<small class="indicator-status-note">{html.escape(metric["statusDescription"])}</small></dd></div>'
    )


def inject_indicator_status(status: dict[str, Any]) -> None:
    by_slug = {metric_slug(metric): metric for metric in status["metrics"]}
    found = 0
    for path in (DIST / "indicatori").glob("*/index.html"):
        metric = by_slug.get(path.parent.name)
        if not metric:
            continue
        text = path.read_text(encoding="utf-8")
        if "assets/data-status.css" not in text:
            text = text.replace(
                "</head>",
                '  <link rel="stylesheet" href="../../assets/data-status.css">\n</head>',
            )
        marker = '<div class="indicator-governance-grid"><dl>'
        if 'data-data-status-row="state"' not in text:
            if marker not in text:
                raise SystemExit(f"Blocco governance non trovato in {path}")
            text = text.replace(marker, marker + indicator_status_block(metric), 1)

        text = text.replace(
            "<dt>Ultimo controllo della fonte</dt>",
            "<dt>Ultimo controllo Osservatorio</dt>",
        )
        checked = html.escape(fmt_date(metric.get("lastChecked", "")))
        text, substitutions = re.subn(
            r'(<dt>Ultimo controllo Osservatorio</dt><dd>).*?(</dd>)',
            rf'\g<1>{checked}\g<2>',
            text,
            count=1,
        )
        if substitutions != 1:
            raise SystemExit(f"Data ultimo controllo non materializzata in {path}")

        release = metric.get("nextExpectedRelease")
        if isinstance(release, dict) and release.get("value"):
            release_value = html.escape(str(release["value"]))
            text, substitutions = re.subn(
                r'<dt>Prossimo aggiornamento atteso</dt><dd>.*?</dd>',
                f'<dt>Prossimo rilascio atteso</dt><dd>{release_value}</dd>',
                text,
                count=1,
            )
        else:
            text = text.replace(
                "<dt>Prossimo aggiornamento atteso</dt>",
                "<dt>Cadenza indicativa</dt>",
            )
        path.write_text(text, encoding="utf-8")
        found += 1

    if found != 123:
        raise SystemExit(f"Attese 123 schede indicatore statiche, aggiornate {found}")


def add_project_link() -> None:
    path = DIST / "progetto" / "index.html"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if "data-status-project-link" in text:
        return
    block = '''<section class="data-status-project-link page-width"><span class="overline">Trasparenza dei dati</span><h2>Quanto sono aggiornati i dati?</h2><p>Consulta periodo pubblicato, ultimo controllo e stato delle fonti per ogni indicatore.</p><a class="button-link" href="../stato-dati/">Apri lo stato dei dati →</a></section>'''
    text = text.replace("</main>", block + "</main>", 1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    data = load(ROOT / "data" / "site-data.json")
    registry = load(ROOT / "data" / "source-registry.json")
    state = load(ROOT / "data" / "source-monitor-state.json")
    status = build_public_status(data, registry, state)
    if status["metricCount"] != 127:
        raise SystemExit(f"Attesi 127 indicatori, trovati {status['metricCount']}")

    patch_status_runtime()
    status_path = DIST / "data" / "data-status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    page = DIST / "stato-dati" / "index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(build_page(status), encoding="utf-8")
    inject_indicator_status(status)
    add_project_link()
    ensure_sitemap_entries(DIST, ("https://osservatorioversilia.it/stato-dati/",))
    print(f"Stato dati materializzato nel layout nativo: {status['metricCount']} indicatori")


if __name__ == "__main__":
    main()
