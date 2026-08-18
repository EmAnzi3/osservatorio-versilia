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
    return f'''<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Stato dei dati · Osservatorio Versilia</title>
  <meta name="description" content="Stato di aggiornamento, ultimo controllo e frequenza delle fonti per i 127 indicatori di Osservatorio Versilia.">
  <link rel="canonical" href="https://osservatorioversilia.it/stato-dati/">
  <meta property="og:title" content="Stato dei dati · Osservatorio Versilia">
  <meta property="og:description" content="Quando sono stati controllati i dati, quale periodo è pubblicato e cosa sappiamo sul prossimo aggiornamento.">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="it_IT">
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../assets/original.css">
  <link rel="stylesheet" href="../assets/static.css">
  <link rel="stylesheet" href="../assets/fidelity.css">
  <link rel="stylesheet" href="../assets/data-status.css">
</head>
<body class="antialiased data-status-page">
  <header class="data-status-header"><div class="page-width"><a href="../" class="data-status-brand">OV <span>Osservatorio Versilia</span></a><a href="../progetto/">Il progetto</a></div></header>
  <main>
    <section class="data-status-hero page-width">
      <span class="overline">Trasparenza</span>
      <h1>Stato dei dati</h1>
      <p>Un dato può essere precedente all'anno corrente ed essere comunque l'ultimo ufficialmente disponibile. Qui separiamo il <strong>periodo pubblicato</strong>, l'<strong>attualità rispetto alla fonte</strong> e la <strong>data dell'ultimo controllo</strong>.</p>
      <p class="data-status-check">Ultimo controllo generale: <strong>{html.escape(fmt_date(status['lastGeneralCheck']))}</strong></p>
    </section>
    <section class="data-status-summary page-width" aria-label="Riepilogo stato dati">
      <article><span>Indicatori</span><strong>{status['metricCount']}</strong></article>
      <article><span>Ultimo dato verificato</span><strong>{counts.get('current', 0)}</strong></article>
      <article><span>Fonti controllate</span><strong>{counts.get('source_checked', 0)}</strong></article>
      <article><span>Nuovi rilasci da verificare</span><strong>{counts.get('release_detected', 0)}</strong></article>
      <article><span>Fonti con problemi</span><strong>{counts.get('source_unavailable', 0) + counts.get('verification_required', 0)}</strong></article>
    </section>
    <section class="data-status-explainer page-width">
      <h2>Come leggere gli stati</h2>
      <div class="data-status-legend">
        <p><span class="status-badge status-ok">Ultimo dato disponibile</span> il periodo pubblicato coincide con l'ultimo periodo verificato sulla fonte.</p>
        <p><span class="status-badge status-neutral">Fonte controllata</span> la fonte è raggiungibile, ma il controllo automatico non può certificare da solo quale sia l'ultima annualità.</p>
        <p><span class="status-badge status-warn">Nuovo rilascio da verificare</span> esiste un segnale di un periodo più recente; nessun valore viene pubblicato senza validazione.</p>
        <p><span class="status-badge status-problem">Fonte temporaneamente non verificabile</span> il controllo non ha potuto accedere alla fonte; il dato pubblicato resta invariato.</p>
      </div>
    </section>
    <section class="data-status-table-section page-width">
      <div class="section-heading"><div><span class="overline">127 indicatori</span><h2>Dettaglio</h2></div><p>I filtri agiscono solo sulla vista e non modificano i dati.</p></div>
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
    <section class="data-status-policy page-width">
      <h2>Nessuna pubblicazione automatica</h2>
      <p>Il monitor può rilevare cambiamenti o nuovi rilasci, ma resta distinta la sequenza <strong>rilevazione → validazione → pubblicazione</strong>. I nuovi valori entrano nel sito solo dopo verifica.</p>
    </section>
  </main>
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


def add_sitemap_entry() -> None:
    path = DIST / "sitemap.xml"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    url = "https://osservatorioversilia.it/stato-dati/"
    if url in text:
        return
    entry = f"  <url><loc>{url}</loc></url>\n"
    text = text.replace("</urlset>", entry + "</urlset>")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    data = load(ROOT / "data" / "site-data.json")
    registry = load(ROOT / "data" / "source-registry.json")
    state = load(ROOT / "data" / "source-monitor-state.json")
    status = build_public_status(data, registry, state)
    if status["metricCount"] != 127:
        raise SystemExit(f"Attesi 127 indicatori, trovati {status['metricCount']}")
    status_path = DIST / "data" / "data-status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    page = DIST / "stato-dati" / "index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(build_page(status), encoding="utf-8")
    inject_indicator_status(status)
    add_project_link()
    add_sitemap_entry()
    print(f"Stato dati materializzato: {status['metricCount']} indicatori")


if __name__ == "__main__":
    main()
