#!/usr/bin/env python3
"""Include Percorsi Versilia e il relativo strato statistico nella build statica."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
SOURCE = ROOT / "percorsi"
TARGET = DIST / "percorsi"
INTEGRATION_ASSETS = ("percorsi-integration.css", "percorsi-integration.js")
INTEGRATION_VERSION = "20260812-3"
TOWN_SLUGS = (
    "camaiore",
    "forte-dei-marmi",
    "massarosa",
    "pietrasanta",
    "seravezza",
    "stazzema",
    "viareggio",
)

APP_HELPERS = r'''
  function percorsiMapHref(municipality = '') {
    const base = route('percorsi/');
    return municipality ? `${base}?comune=${encodeURIComponent(municipality)}` : base;
  }

  function percorsiModePills(byMode) {
    const modes = {
      trekking: ['Trekking', '#176b4a'],
      cammino: ['Cammini', '#6e4ab5'],
      bicycle: ['Bici', '#117b93'],
      mtb: ['MTB', '#315b9d']
    };
    return Object.entries(modes)
      .filter(([key]) => Number(byMode?.[key] || 0) > 0)
      .map(([key, meta]) => `<span><i style="background:${meta[1]}"></i>${html(meta[0])} ${Number(byMode[key])}</span>`)
      .join('');
  }

  function percorsiQuickMarkup(data) {
    const stats = data.percorsi;
    if (!stats?.versilia) return '';
    const v = stats.versilia;
    return `<aside class="slow-mobility-quick" data-percorsi-quick="versilia" aria-label="Percorsi e mobilità lenta">
      <div class="slow-mobility-quick-copy"><span>Mobilità lenta</span><strong>${Number(v.routes)} percorsi · ${Math.round(Number(v.km))} km</strong><small>Sentieri, cammini e ciclovie verificati nei 7 Comuni.</small></div>
      <div class="slow-mobility-quick-actions"><a href="#percorsi-statistiche">Statistiche</a><a href="${percorsiMapHref()}">Mappa →</a></div>
    </aside>`;
  }

  function percorsiCompareMarkup(data) {
    const stats = data.percorsi;
    if (!stats?.versilia || !stats?.municipalities) return '';
    const v = stats.versilia;
    const rows = Object.values(stats.municipalities)
      .sort((a, b) => a.name.localeCompare(b.name, 'it'))
      .map(item => `<tr><th scope="row">${html(item.name)}</th><td class="route-count">${Number(item.routes)}</td><td><div class="slow-mobility-mode-list">${percorsiModePills(item.by_mode)}</div></td><td><a href="${percorsiMapHref(item.name)}">Vedi sulla mappa →</a></td></tr>`)
      .join('');
    return `<section id="percorsi-statistiche" class="slow-mobility-overview page-width" data-percorsi-stats="versilia">
      <div class="slow-mobility-heading"><div><span class="overline">Mobilità lenta</span><h2>Percorsi, cammini e ciclovie della Versilia</h2><p>Una lettura statistica del patrimonio cartografico già verificato, affiancata alla mappa interattiva e ai download delle tracce.</p></div><a class="slow-mobility-link" href="${percorsiMapHref()}">Esplora la cartografia <span aria-hidden="true">→</span></a></div>
      <div class="slow-mobility-summary">
        <article class="slow-mobility-stat primary"><strong>${Number(v.routes)}</strong><span>percorsi pubblici</span></article>
        <article class="slow-mobility-stat primary"><strong>${Math.round(Number(v.km))}</strong><span>km di tracce nei 7 Comuni</span></article>
        <article class="slow-mobility-stat"><strong>${Number(v.by_mode?.trekking || 0)}</strong><span>Trekking</span></article>
        <article class="slow-mobility-stat"><strong>${Number(v.by_mode?.cammino || 0)}</strong><span>Cammini</span></article>
        <article class="slow-mobility-stat"><strong>${Number(v.by_mode?.bicycle || 0)}</strong><span>Bici</span></article>
        <article class="slow-mobility-stat"><strong>${Number(v.by_mode?.mtb || 0)}</strong><span>MTB</span></article>
      </div>
      <div class="slow-mobility-table-wrap"><table class="slow-mobility-table"><thead><tr><th>Comune</th><th>Percorsi</th><th>Tipologia</th><th>Cartografia</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="slow-mobility-note">${html(stats.definition?.municipality_count_note || '')} ${html(stats.definition?.municipality_km_note || '')}</p>
    </section>`;
  }

  function percorsiTownMarkup(data, town) {
    const stats = data.percorsi;
    const slug = normalize(town.name).replaceAll(' ', '-');
    const item = stats?.municipalities?.[slug];
    if (!item) return '';
    const modeCards = [
      ['trekking', 'Trekking'],
      ['cammino', 'Cammini'],
      ['bicycle', 'Bici'],
      ['mtb', 'MTB']
    ].filter(([key]) => Number(item.by_mode?.[key] || 0) > 0)
      .map(([key, label]) => `<article><strong>${Number(item.by_mode[key])}</strong><span>${html(label)}</span></article>`)
      .join('');
    return `<section class="slow-mobility-town" data-percorsi-stats="town">
      <div class="slow-mobility-heading"><div><span class="overline">Mobilità lenta</span><h3>Percorsi e mobilità lenta</h3><p>Tracce pubbliche verificate che attraversano il territorio di ${html(item.name)}.</p></div><a class="slow-mobility-link" href="${percorsiMapHref(item.name)}">Apri ${html(item.name)} sulla mappa <span aria-hidden="true">→</span></a></div>
      <div class="slow-mobility-town-grid"><div class="slow-mobility-town-total"><strong>${Number(item.routes)}</strong><span>percorsi pubblici che attraversano il Comune</span></div><div class="slow-mobility-town-modes">${modeCards}</div></div>
      <p class="slow-mobility-note">Il conteggio considera ogni percorso una sola volta nel Comune. I chilometri comunali saranno pubblicati solo dopo l’intersezione con i confini amministrativi ufficiali.</p>
    </section>`;
  }
'''


def inject_integration_assets(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"Pagina da integrare non trovata: {path}")
    text = path.read_text(encoding="utf-8")
    prefix = os.path.relpath(DIST, path.parent).replace(os.sep, "/")
    relative_root = "" if prefix == "." else f"{prefix}/"
    css = f"{relative_root}assets/percorsi-integration.css?v={INTEGRATION_VERSION}"
    js = f"{relative_root}assets/percorsi-integration.js?v={INTEGRATION_VERSION}"
    if "assets/percorsi-integration.css" not in text:
        text = text.replace("</head>", f'  <link rel="stylesheet" href="{css}">\n</head>')
    if "assets/percorsi-integration.js" not in text:
        text = text.replace("</body>", f'  <script src="{js}" defer></script>\n</body>')
    path.write_text(text, encoding="utf-8")


def patch_site_data() -> None:
    site_data_path = DIST / "data" / "site-data.json"
    stats_path = SOURCE / "data" / "site_stats.json"
    if not site_data_path.exists():
        raise RuntimeError(f"site-data.json non trovato: {site_data_path}")
    site_data = json.loads(site_data_path.read_text(encoding="utf-8"))
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    site_data["percorsi"] = stats
    site_data_path.write_text(json.dumps(site_data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"Patch app Percorsi non applicabile ({label}): occorrenze={text.count(old)}")
    return text.replace(old, new, 1)


def patch_app_bundle() -> None:
    path = DIST / "assets" / "app-bundle.js"
    if not path.exists():
        raise RuntimeError(f"app-bundle.js non trovato: {path}")
    text = path.read_text(encoding="utf-8")

    helper_anchor = "\n\n  function compareContextNav(data, activeTheme) {"
    if "function percorsiCompareMarkup(data)" not in text:
        text = replace_once(
            text,
            helper_anchor,
            f"\n{APP_HELPERS}\n  function compareContextNav(data, activeTheme) {{",
            "helper Percorsi",
        )

    old_dashboard = '<section class="topic-dashboard page-width" data-theme="${themeKey}"><aside class="topic-controls">${metricControls(data, themeKey, metricKey, true)}<div id="compare-definition"></div></aside><div id="compare-bars"></div></section>'
    new_dashboard = '<section class="topic-dashboard page-width" data-theme="${themeKey}"><aside class="topic-controls">${metricControls(data, themeKey, metricKey, true)}${themeKey === \'mobilita\' ? percorsiQuickMarkup(data) : \'\'}<div id="compare-definition"></div></aside><div id="compare-bars"></div></section>'
    text = replace_once(text, old_dashboard, new_dashboard, "richiamo confronto")

    old_compare_tools = '<section id="compare-tools" class="compare-post-benchmark-tools page-width"></section>\n      ${themeKey === \'mobilita\' ? crimeMarkup(data) : \'\'}'
    new_compare_tools = '<section id="compare-tools" class="compare-post-benchmark-tools page-width"></section>\n      ${themeKey === \'mobilita\' ? percorsiCompareMarkup(data) : \'\'}\n      ${themeKey === \'mobilita\' ? crimeMarkup(data) : \'\'}'
    text = replace_once(text, old_compare_tools, new_compare_tools, "statistiche confronto")

    old_town = '${metricControls(data, themeKey, metricKey, true)}\n      <div class="town-metric-layout">'
    new_town = '${metricControls(data, themeKey, metricKey, true)}\n      ${themeKey === \'mobilita\' ? percorsiTownMarkup(data, town) : \'\'}\n      <div class="town-metric-layout">'
    text = replace_once(text, old_town, new_town, "statistiche comunali")

    path.write_text(text, encoding="utf-8")


def main() -> None:
    if not SOURCE.exists():
        raise RuntimeError(f"Percorsi Versilia non trovato: {SOURCE}")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET)

    dist_assets = DIST / "assets"
    dist_assets.mkdir(parents=True, exist_ok=True)
    for name in INTEGRATION_ASSETS:
        source = ROOT / "assets" / name
        if not source.exists() or source.stat().st_size == 0:
            raise RuntimeError(f"Asset integrazione Percorsi mancante: {source}")
        shutil.copy2(source, dist_assets / name)

    patch_site_data()
    patch_app_bundle()

    inject_integration_assets(DIST / "confronta" / "mobilita" / "index.html")
    for slug in TOWN_SLUGS:
        inject_integration_assets(DIST / "comuni" / slug / "index.html")

    required = (
        TARGET / "index.html",
        TARGET / "app.js",
        TARGET / "data-loader.js",
        TARGET / "styles.css",
        TARGET / "data" / "master_summary.json",
        TARGET / "data" / "site_stats.json",
        DIST / "data" / "site-data.json",
        DIST / "assets" / "app-bundle.js",
        dist_assets / "percorsi-integration.css",
        dist_assets / "percorsi-integration.js",
    )
    missing = [str(path.relative_to(DIST)) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError(f"Build Percorsi incompleta: {', '.join(missing)}")

    merged = json.loads((DIST / "data" / "site-data.json").read_text(encoding="utf-8"))
    if merged.get("percorsi", {}).get("versilia", {}).get("routes") != 41:
        raise RuntimeError("Statistiche Percorsi non incorporate correttamente in site-data.json")
    bundle = (DIST / "assets" / "app-bundle.js").read_text(encoding="utf-8")
    for marker in ("percorsiQuickMarkup", "percorsiCompareMarkup", "percorsiTownMarkup"):
        if marker not in bundle:
            raise RuntimeError(f"Renderer Percorsi assente da app-bundle.js: {marker}")

    print("Percorsi Versilia incorporato nel renderer principale: cartografia + statistiche Versilia e 7 Comuni.")


if __name__ == "__main__":
    main()
