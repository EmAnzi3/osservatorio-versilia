#!/usr/bin/env python3
"""Rifiniture della preview Percorsi approvate dopo la verifica visuale.

Il file viene eseguito soltanto nella seconda build della PR draft, dopo
``prepare_percorsi_architecture.py`` e prima del prerender finale. Mantiene
quindi intatto il sito canonico durante i test di regressione iniziali.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_PARTS = ROOT / "assets" / "app-parts"
VISUAL_GRAMMAR = ROOT / "assets" / "visual-grammar.js"
FIDELITY_CSS = ROOT / "assets" / "fidelity.css"
PERCORSI_APP = ROOT / "percorsi" / "app.js"
PERCORSI_INDEX = ROOT / "percorsi" / "index.html"

PALETTE = {
    "trekking": "#176b4a",
    "cammino": "#c66a00",
    "bicycle": "#0077a8",
    "mtb": "#b23a48",
}


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Patch non applicabile ({label}): occorrenze={count}")
    return text.replace(old, new, 1)


def patch_integer_count_axes() -> None:
    text = VISUAL_GRAMMAR.read_text(encoding="utf-8")
    old = """    const n = Number(value);\n    const formatted = Math.abs(n) >= 100 ? number0.format(n) : number1.format(n);\n    const kind = unitKind(unit);"""
    new = """    const n = Number(value);\n    const kind = unitKind(unit);\n    const formatted = kind === 'count' ? number0.format(n) : (Math.abs(n) >= 100 ? number0.format(n) : number1.format(n));"""
    if "kind === 'count' ? number0.format(n)" not in text:
        text = replace_once(text, old, new, "assi interi per conteggi")

    old_scale = """    if (min >= 0) {\n      min = 0;\n      max = max === 0 ? 1 : max * 1.05;\n      return { min, max, kind: 'absolute' };\n    }"""
    new_scale = """    if (min >= 0) {\n      min = 0;\n      max = max === 0 ? 1 : max * 1.05;\n      if (unitKind(unit) === 'count') max = Math.max(1, Math.ceil(max));\n      return { min, max, kind: 'absolute' };\n    }"""
    if "unitKind(unit) === 'count') max = Math.max(1, Math.ceil(max))" not in text:
        text = replace_once(text, old_scale, new_scale, "estremo intero per conteggi")
    VISUAL_GRAMMAR.write_text(text, encoding="utf-8")


def patch_renderer_hierarchy() -> None:
    files = sorted(APP_PARTS.glob("[0-9][0-9].txt"))
    if len(files) != 7:
        raise RuntimeError(f"Attesi 7 app-parts, trovati {len(files)}")

    helper = """  function slowMobilityMapHref(townName, metricKey) {\n    const modes = {\n      slowMobilityTrekking: 'trekking',\n      slowMobilityCammini: 'cammino',\n      slowMobilityBici: 'bicycle',\n      slowMobilityMtb: 'mtb'\n    };\n    const params = new URLSearchParams({ comune: townName });\n    if (modes[metricKey]) params.set('tipo', modes[metricKey]);\n    return route(`percorsi/?${params.toString()}`);\n  }\n\n"""

    for path in files:
        text = path.read_text(encoding="utf-8")

        if "function renderTownMetric(data, town, themeKey, metricKey, onMetricSelect)" in text:
            if "function slowMobilityMapHref" not in text:
                anchor = "  function renderTownMetric(data, town, themeKey, metricKey, onMetricSelect) {"
                text = replace_once(text, anchor, helper + anchor, "helper deep-link cartografia")

            old_layout = """      ${metricControls(data, themeKey, metricKey, true)}\n      <div class=\"town-metric-layout\">"""
            new_layout = """      ${metricControls(data, themeKey, metricKey, true)}\n      ${metricKey.startsWith('slowMobility') ? `<div class=\"slow-mobility-map-entry\"><span>Vedi sulla mappa i percorsi di ${html(town.name)} corrispondenti alla selezione.</span><a href=\"${slowMobilityMapHref(town.name, metricKey)}\">Esplora sulla mappa <b>→</b></a></div>` : ''}\n      <div class=\"town-metric-layout\">"""
            if "slow-mobility-map-entry" not in text:
                text = replace_once(text, old_layout, new_layout, "CTA cartografia vicino ai filtri")

            old_bottom = "${metricKey.startsWith('slowMobility') ? `<a href=\"${route('percorsi/?comune=' + encodeURIComponent(town.name))}\">Esplora sulla mappa</a>` : ''}"
            new_bottom = "${metricKey.startsWith('slowMobility') ? `<a href=\"${slowMobilityMapHref(town.name, metricKey)}\">Esplora sulla mappa</a>` : ''}"
            if old_bottom in text:
                text = text.replace(old_bottom, new_bottom, 1)

        old_order = """      <section id=\"compare-benchmark\" class=\"page-width\"></section>\n      <section id=\"compare-tools\" class=\"compare-post-benchmark-tools page-width\"></section>\n      ${themeKey === 'sicurezza' ? crimeMarkup(data) : ''}\n      <section class=\"topic-town-links page-width\">"""
        new_order = """      <section id=\"compare-benchmark\" class=\"page-width\"></section>\n      ${themeKey === 'sicurezza' ? crimeMarkup(data) : ''}\n      <section id=\"compare-tools\" class=\"compare-post-benchmark-tools page-width\"></section>\n      <section class=\"topic-town-links page-width\">"""
        if old_order in text:
            text = text.replace(old_order, new_order, 1)

        path.write_text(text, encoding="utf-8")


def patch_cta_style() -> None:
    text = FIDELITY_CSS.read_text(encoding="utf-8")
    marker = "/* Percorsi: accesso cartografico contestuale */"
    if marker in text:
        return
    text += """

/* Percorsi: accesso cartografico contestuale */
.slow-mobility-map-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin: 12px 0 18px;
  padding: 12px 14px;
  border: 1px solid rgba(15, 54, 84, .22);
  border-radius: 12px;
  background: rgba(88, 162, 143, .10);
}
.slow-mobility-map-entry > span {
  color: #36566a;
  font-size: .82rem;
  line-height: 1.35;
}
.slow-mobility-map-entry > a {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
  padding: 9px 13px;
  border-radius: 999px;
  background: #0f3654;
  color: #fff;
  font-size: .78rem;
  font-weight: 750;
  text-decoration: none;
}
.slow-mobility-map-entry > a:hover,
.slow-mobility-map-entry > a:focus-visible {
  background: #174d70;
}
@media (max-width: 700px) {
  .slow-mobility-map-entry {
    align-items: flex-start;
    flex-direction: column;
  }
}
"""
    FIDELITY_CSS.write_text(text, encoding="utf-8")


def patch_map_palette_and_deep_links() -> None:
    app = PERCORSI_APP.read_text(encoding="utf-8")
    old_palette = 'const colors={trekking:"#176b4a",walk:"#176b4a",cammino:"#6e4ab5",bicycle:"#117b93",mtb:"#315b9d"};'
    new_palette = (
        'const colors={trekking:"#176b4a",walk:"#176b4a",cammino:"#c66a00",'
        'bicycle:"#0077a8",mtb:"#b23a48"};'
    )
    if old_palette in app:
        app = app.replace(old_palette, new_palette, 1)

    helper = (
        'function applyInitialUrlFilters(){const params=new URLSearchParams(location.search),'
        'comune=params.get("comune")||"",tipo=params.get("tipo")||"",allowed=new Set(["trekking","cammino","bicycle","mtb"]);'
        'state.municipality=comune;state.mode=allowed.has(tipo)?tipo:"all";const sel=document.getElementById("municipality");'
        'if(comune&&[...sel.options].some(o=>o.value===comune))sel.value=comune;'
        'document.querySelectorAll(".chip").forEach(x=>x.classList.toggle("active",x.dataset.mode===state.mode));'
        'applyFilters(Boolean(comune||state.mode!=="all"));if(!comune&&state.mode==="all")fitVersilia()}\n'
    )
    if "function applyInitialUrlFilters()" not in app:
        app = replace_once(app, "async function loadData(){", helper + "async function loadData(){", "filtri URL cartografia")
    old_load = "populateMunicipalities();buildMunicipalityBounds();applyFilters(false);fitVersilia()"
    if old_load in app:
        app = app.replace(old_load, "populateMunicipalities();buildMunicipalityBounds();applyInitialUrlFilters()", 1)
    PERCORSI_APP.write_text(app, encoding="utf-8")

    index = PERCORSI_INDEX.read_text(encoding="utf-8")
    replacements = {
        '<div class="leg"><span style="background:#176b4a"></span>Trekking</div>':
            f'<div class="leg"><span style="background:{PALETTE["trekking"]}"></span>Trekking</div>',
        '<div class="leg"><span style="background:#6e4ab5"></span>Cammini</div>':
            f'<div class="leg"><span style="background:{PALETTE["cammino"]}"></span>Cammini</div>',
        '<div class="leg"><span style="background:#117b93"></span>Bici</div>':
            f'<div class="leg"><span style="background:{PALETTE["bicycle"]}"></span>Bici</div>',
        '<div class="leg"><span style="background:#315b9d"></span>MTB</div>':
            f'<div class="leg"><span style="background:{PALETTE["mtb"]}"></span>MTB</div>',
    }
    for old, new in replacements.items():
        index = index.replace(old, new)
    index = index.replace('app.js?v=2', 'app.js?v=3')
    PERCORSI_INDEX.write_text(index, encoding="utf-8")


def main() -> None:
    patch_integer_count_axes()
    patch_renderer_hierarchy()
    patch_cta_style()
    patch_map_palette_and_deep_links()
    print("Rifiniture preview applicate: assi interi, CTA mappa contestuale, criminalità riposizionata, palette cartografica distinta.")


if __name__ == "__main__":
    main()
