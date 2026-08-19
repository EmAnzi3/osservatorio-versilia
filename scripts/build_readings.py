#!/usr/bin/env python3
# Build /letture/ from editorial configuration and canonical Osservatorio data.
from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from data_status_model import build_public_status
from build_data_status import fmt_date, read_native_shell

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
CONFIG = ROOT / "data" / "readings.json"

CLIMATE_SERIES = {
    "climateTemperatureTrend50y": ("meteo-clima-poc.json", "temperature", "°C", 2),
    "climatePrecipitationTrend50y": ("meteo-clima-poc.json", "precipitation", "mm", 0),
    "climateTminTrend": ("meteo-clima-minmax-poc.json", "tmin", "°C", 2),
    "climateTmaxTrend": ("meteo-clima-minmax-poc.json", "tmax", "°C", 2),
}
FORBIDDEN_EDITORIAL_KEYS = {
    "year", "period", "publishedPeriod", "source", "sourceUrl",
    "value", "formatted", "statusLabel", "lastChecked",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON non valido: {path}")
    return value


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFD", str(value).lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def rebase_shell(fragment: str, prefix: str) -> str:
    return fragment.replace('href="../', f'href="{prefix}').replace('src="../', f'src="{prefix}')


def validate_config(config: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
    readings = config.get("readings")
    if config.get("status") != "draft-noindex":
        raise SystemExit("Le Letture devono restare draft-noindex durante il collaudo")
    if not isinstance(readings, list) or not readings:
        raise SystemExit("data/readings.json non contiene Letture")
    seen: set[str] = set()
    for reading in readings:
        if not isinstance(reading, dict):
            raise SystemExit("Configurazione Lettura non valida")
        forbidden = FORBIDDEN_EDITORIAL_KEYS & set(reading)
        if forbidden:
            raise SystemExit(
                f"Lettura {reading.get('slug')}: metadata canonici duplicati: {sorted(forbidden)}"
            )
        slug = str(reading.get("slug") or "").strip()
        if not slug or slug != slugify(slug) or slug in seen:
            raise SystemExit(f"Slug Lettura non valido o duplicato: {slug!r}")
        seen.add(slug)
        metrics = reading.get("metrics")
        if not isinstance(metrics, list) or not metrics:
            raise SystemExit(f"Lettura {slug}: lista indicatori assente")
        primary = str(reading.get("primaryMetric") or "")
        if primary not in metrics:
            raise SystemExit(f"Lettura {slug}: indicatore principale fuori dal perimetro")
        missing = [key for key in metrics if key not in data.get("metrics", {})]
        if missing:
            raise SystemExit(f"Lettura {slug}: indicatori inesistenti: {missing}")
    return readings


def metric_href(key: str, metric: dict[str, Any], depth: str = "../../") -> str:
    storage = metric.get("dataStorage") or {}
    if storage.get("type") == "external-climate":
        return f"{depth}confronta/ambiente/?indicatore={key}"
    label = metric.get("meta", {}).get("label") or key
    return f"{depth}indicatori/{slugify(label)}/"


def fmt_number(value: float, unit: str, decimals: int = 1) -> str:
    if unit in {"percent", "%"}:
        return f"{value:.{decimals}f}%".replace(".", ",")
    if unit in {"celsius", "°C"}:
        return f"{value:.{decimals}f} °C".replace(".", ",")
    if unit == "mm":
        return f"{value:,.0f} mm".replace(",", ".")
    if unit in {"euro", "currency"}:
        return f"€ {value:,.0f}".replace(",", ".")
    if unit in {"count", "number"}:
        return f"{value:,.0f}".replace(",", ".")
    return (
        f"{value:,.{decimals}f}"
        .replace(",", "X").replace(".", ",").replace("X", ".")
    )


def climate_rows(key: str) -> list[dict[str, Any]]:
    filename, series_key, unit, decimals = CLIMATE_SERIES[key]
    payload = load(ROOT / "data" / filename)
    rows = []
    for town, series in payload["municipalities"].items():
        latest = series["latestComplete"]
        value = float(latest[series_key])
        rows.append(
            {"town": town, "value": value, "formatted": fmt_number(value, unit, decimals)}
        )
    return sorted(rows, key=lambda row: row["town"].casefold())


def display_rows(key: str, metric: dict[str, Any]) -> list[dict[str, Any]]:
    if key in CLIMATE_SERIES:
        return climate_rows(key)
    source_rows = metric.get("rows") if isinstance(metric.get("rows"), list) else []
    result = []
    for row in source_rows:
        if not isinstance(row, dict) or not row.get("town"):
            continue
        formatted = row.get("formatted")
        if not formatted and isinstance(row.get("value"), (int, float)):
            formatted = fmt_number(
                float(row["value"]), str(metric.get("meta", {}).get("unit") or "")
            )
        result.append(
            {
                "town": str(row["town"]),
                "value": row.get("value"),
                "formatted": str(formatted or "—"),
            }
        )
    return sorted(result, key=lambda row: row["town"].casefold())


def public_status(
    data: dict[str, Any], registry: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], str]:
    public = build_public_status(data, registry, state)
    return (
        {row["key"]: row for row in public["metrics"]},
        str(public.get("lastGeneralCheck") or state.get("checkedAt") or ""),
    )


def metric_card(
    key: str, data: dict[str, Any], statuses: dict[str, dict[str, Any]]
) -> str:
    metric = data["metrics"][key]
    meta = metric.get("meta", {})
    status = statuses[key]
    href = metric_href(key, metric)
    return f'''<article class="reading-evidence-card">
      <div><span>{html.escape(status["themeLabel"])}</span><h3>{html.escape(str(meta.get("label") or key))}</h3></div>
      <dl>
        <div><dt>Periodo</dt><dd>{html.escape(status["publishedPeriod"] or "—")}</dd></div>
        <div><dt>Fonte</dt><dd>{html.escape(status["source"] or "—")}</dd></div>
        <div><dt>Stato</dt><dd>{html.escape(status["statusLabel"])}</dd></div>
      </dl>
      <a href="{html.escape(href, quote=True)}">Apri il dato <span aria-hidden="true">→</span></a>
    </article>'''


def primary_table(
    key: str, data: dict[str, Any], statuses: dict[str, dict[str, Any]]
) -> str:
    metric = data["metrics"][key]
    meta = metric.get("meta", {})
    status = statuses[key]
    rows = display_rows(key, metric)
    href = metric_href(key, metric)
    if not rows:
        return f'''<article class="reading-primary-empty"><p>Questo indicatore non espone una graduatoria comunale semplice. La Lettura rimanda alla scheda canonica, dove sono mantenute definizione e struttura complete.</p><a href="{html.escape(href, quote=True)}">Apri {html.escape(str(meta.get("label") or key))} →</a></article>'''
    body = "".join(
        f'<tr><th scope="row">{html.escape(row["town"])}</th><td>{html.escape(row["formatted"])}</td></tr>'
        for row in rows
    )
    return f'''<div class="reading-primary-table-wrap"><table class="reading-primary-table">
      <thead><tr><th>Comune</th><th>{html.escape(str(meta.get("shortLabel") or meta.get("label") or "Valore"))}</th></tr></thead>
      <tbody>{body}</tbody>
    </table></div>
    <div class="reading-primary-meta">
      <span>Periodo pubblicato: <strong>{html.escape(status["publishedPeriod"] or "—")}</strong></span>
      <span>{html.escape(status["statusLabel"])}</span>
      <a href="{html.escape(href, quote=True)}">Vai alla scheda completa →</a>
    </div>'''


def json_ld_for(reading: dict[str, Any], url: str) -> str:
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": reading["title"],
            "description": reading["description"],
            "url": url,
            "inLanguage": "it-IT",
            "isAccessibleForFree": True,
            "about": {"@type": "Place", "name": "Versilia, Toscana, Italia"},
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def page_head(
    title: str,
    description: str,
    canonical: str,
    native_styles: str,
    json_ld: str,
    prefix: str,
) -> str:
    return f'''<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>{html.escape(title)} · Osservatorio Versilia</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta property="og:title" content="{html.escape(title, quote=True)} · Osservatorio Versilia">
  <meta property="og:description" content="{html.escape(description, quote=True)}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="it_IT">
  <meta property="og:url" content="{html.escape(canonical, quote=True)}">
  <meta property="og:site_name" content="Osservatorio Versilia">
  <meta property="og:image" content="https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
  <script type="application/ld+json">{json_ld}</script>
  <link rel="icon" href="{prefix}favicon.svg?v=20260807-ov" type="image/svg+xml">
  <link rel="manifest" href="{prefix}site.webmanifest?v=20260813-pwa8">
  {native_styles}
  <link rel="stylesheet" href="{prefix}assets/readings.css">
  <meta name="theme-color" content="#0F3654">
</head>'''


def build_reading(
    reading: dict[str, Any],
    data: dict[str, Any],
    statuses: dict[str, dict[str, Any]],
    general_checked: str,
    header: str,
    footer: str,
    native_styles: str,
) -> str:
    primary = reading["primaryMetric"]
    evidence = reading["metrics"]
    missing_status = [key for key in evidence if key not in statuses]
    if missing_status:
        raise SystemExit(
            f"Lettura {reading['slug']}: stato inesistente per {missing_status}"
        )
    canonical = f"https://osservatorioversilia.it/letture/{reading['slug']}/"
    cards = "".join(metric_card(key, data, statuses) for key in evidence)
    head = page_head(
        reading["title"],
        reading["description"],
        canonical,
        native_styles,
        json_ld_for(reading, canonical),
        "../../",
    )
    return f'''{head}
<body class="antialiased" data-page="reading" data-reading="{html.escape(reading["slug"], quote=True)}" data-prerendered="true">
{header}<div id="app"><main class="editorial-page reading-main">
  <div class="breadcrumbs page-width"><a href="../../">Home</a><span>›</span><a href="../">Letture</a><span>›</span><strong>{html.escape(reading["title"])}</strong></div>
  <section class="reading-hero page-width">
    <span class="overline">Percorso di lettura · dati, non opinioni</span>
    <h1>{html.escape(reading["question"])}</h1>
    <p>{html.escape(reading["description"])}</p>
    <div class="reading-answer"><span>In una frase</span><strong>{html.escape(reading["answer"])}</strong></div>
  </section>

  <section class="reading-section page-width" aria-labelledby="reading-primary">
    <div class="section-heading"><div><span class="section-number">01</span><h2 id="reading-primary">Il dato principale</h2></div><p>{html.escape(reading["primaryIntro"])}</p></div>
    {primary_table(primary, data, statuses)}
  </section>

  <section class="reading-section page-width reading-evidence" aria-labelledby="reading-context">
    <div class="section-heading"><div><span class="section-number">02</span><h2 id="reading-context">Il contesto che serve</h2></div><p>Ogni tessera rimanda al dato canonico. Periodo, fonte e stato sono derivati dal sistema di monitoraggio dell’Osservatorio.</p></div>
    <div class="reading-evidence-grid">{cards}</div>
  </section>

  <section class="reading-section page-width reading-interpretation" aria-labelledby="reading-interpretation">
    <div class="section-heading"><div><span class="section-number">03</span><h2 id="reading-interpretation">Cosa possiamo leggere</h2></div><p>L’interpretazione resta separata dai dati che la sostengono.</p></div>
    <div class="reading-interpretation-grid"><article><span>Supportato dai dati</span><p>{html.escape(reading["supported"])}</p></article><article><span>Il limite da ricordare</span><p>{html.escape(reading["caveat"])}</p></article></div>
  </section>

  <section class="reading-section page-width reading-method" aria-labelledby="reading-method">
    <div class="section-heading"><div><span class="section-number">04</span><h2 id="reading-method">Metodo e tracciabilità</h2></div><p>La Lettura non possiede un proprio dataset: usa gli indicatori pubblicati e i loro metadata.</p></div>
    <div class="reading-method-note"><p><strong>Ultimo controllo generale:</strong> {html.escape(fmt_date(general_checked) if general_checked else "—")}</p><p>Se un indicatore viene aggiornato, questa pagina cambia soltanto dopo la normale sequenza <strong>rilevazione → validazione → pubblicazione</strong>.</p><a href="../../stato-dati/">Apri Stato dei dati →</a></div>
  </section>

  <nav class="reading-back page-width" aria-label="Altre letture"><a href="../">← Tutte le Letture</a></nav>
</main></div>
{footer}<noscript><div class="app-error">I contenuti principali sono già disponibili; JavaScript serve per ricerca e navigazione interattiva.</div></noscript>
  <script src="../../assets/app-bundle.js" defer></script>
</body>
</html>'''


def build_index(
    readings: list[dict[str, Any]],
    header: str,
    footer: str,
    native_styles: str,
) -> str:
    cards = "".join(
        f'''<article class="reading-index-card"><span>{i:02d}</span><h2>{html.escape(item["title"])}</h2><p>{html.escape(item["question"])}</p><a href="./{html.escape(item["slug"], quote=True)}/">Apri la Lettura →</a></article>'''
        for i, item in enumerate(readings, 1)
    )
    canonical = "https://osservatorioversilia.it/letture/"
    head = page_head(
        "Letture",
        "Percorsi guidati che collegano indicatori, confronti e contesto senza duplicare i dati dell’Osservatorio.",
        canonical,
        native_styles,
        json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "CollectionPage",
                "name": "Letture · Osservatorio Versilia",
                "url": canonical,
                "inLanguage": "it-IT",
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "../",
    )
    return f'''{head}
<body class="antialiased" data-page="readings" data-prerendered="true">
{header}<div id="app"><main class="editorial-page reading-main">
  <section class="reading-hero page-width">
    <span class="overline">Percorsi di lettura</span>
    <h1>Domande reali, dati verificabili.</h1>
    <p>Le Letture mettono in sequenza indicatori già pubblicati per aiutare a capire un fenomeno senza trasformare l’Osservatorio in una testata o in un feed di opinioni.</p>
    <div class="reading-answer"><span>Regola editoriale</span><strong>dato → confronto → contesto → interpretazione</strong></div>
  </section>
  <section class="reading-section page-width">
    <div class="section-heading"><div><span class="section-number">01</span><h2>Set iniziale</h2></div><p>Set di collaudo: le pagine restano noindex finché non viene autorizzata la pubblicazione.</p></div>
    <div class="reading-index-grid">{cards}</div>
  </section>
</main></div>
{footer}<noscript><div class="app-error">I contenuti principali sono già disponibili; JavaScript serve per ricerca e navigazione interattiva.</div></noscript>
  <script src="../assets/app-bundle.js" defer></script>
</body>
</html>'''


def patch_runtime() -> None:
    path = DIST / "assets" / "app-bundle.js"
    if not path.exists():
        raise SystemExit("Bundle applicativo assente prima della build Letture")
    text = path.read_text(encoding="utf-8")
    if "pageType === 'reading' || pageType === 'readings'" in text:
        return
    original = (
        "      else if (pageType === 'feedback') renderFeedback(data);\n"
        "      else renderNotFound();"
    )
    status_only = (
        "      else if (pageType === 'feedback') renderFeedback(data);\n"
        "      else if (pageType === 'status') { /* contenuto prerenderizzato: non sostituire #app */ }\n"
        "      else renderNotFound();"
    )
    full = (
        "      else if (pageType === 'feedback') renderFeedback(data);\n"
        "      else if (pageType === 'status') { /* contenuto prerenderizzato: non sostituire #app */ }\n"
        "      else if (pageType === 'reading' || pageType === 'readings') { /* contenuto prerenderizzato: non sostituire #app */ }\n"
        "      else renderNotFound();"
    )
    if status_only in text:
        text = text.replace(status_only, full, 1)
    elif original in text:
        text = text.replace(original, full, 1)
    else:
        raise SystemExit("Punto di integrazione runtime Letture non trovato")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    data = load(ROOT / "data" / "site-data.json")
    config = load(CONFIG)
    readings = validate_config(config, data)
    registry = load(ROOT / "data" / "source-registry.json")
    state = load(ROOT / "data" / "source-monitor-state.json")
    statuses, general_checked = public_status(data, registry, state)

    header, footer, native_styles, _ = read_native_shell()
    nested_header = rebase_shell(header, "../../")
    nested_footer = rebase_shell(footer, "../../")
    nested_styles = rebase_shell(native_styles, "../../")
    patch_runtime()

    target = DIST / "letture"
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(
        build_index(readings, header, footer, native_styles), encoding="utf-8"
    )
    for reading in readings:
        page = target / reading["slug"] / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(
            build_reading(
                reading,
                data,
                statuses,
                general_checked,
                nested_header,
                nested_footer,
                nested_styles,
            ),
            encoding="utf-8",
        )
    print(
        f"Letture materializzate: {len(readings)} + indice; "
        "noindex mantenuto per il collaudo."
    )


if __name__ == "__main__":
    main()
