#!/usr/bin/env python3
"""Refine Economia Atlas materialization for autonomous section and town context.

Runs immediately after materialize_economy_atlas_release.py in the preview
workspace. The changes are intentionally applied to the ephemeral release
sources used by the static builder.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data" / "site-data.json"
APP_02 = ROOT / "assets" / "app-parts" / "02.txt"
APP_04 = ROOT / "assets" / "app-parts" / "04.txt"
ACCORDION = ROOT / "assets" / "ux-accordion.js"

METRIC_KEY = "economyActivityAtlas"
SECTION_KEY = "atlante"
EXPECTED_SECTION_COUNTS = [6, 4, 10, 2, 9, 1]


def replace_one(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"Refine Atlante {label}: attesa 1 occorrenza, trovate {count}")
    return updated


def refine_catalog() -> None:
    data = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    theme = data["themes"]["economia"]
    if METRIC_KEY not in theme.get("metrics", []):
        raise RuntimeError("Metrica Atlante assente dal tema Economia")

    sections = []
    for section in theme.get("sections", []):
        if section.get("key") == SECTION_KEY:
            continue
        copy = dict(section)
        copy["metrics"] = [key for key in section.get("metrics", []) if key != METRIC_KEY]
        sections.append(copy)

    sections.append({
        "key": SECTION_KEY,
        "label": "Atlante delle attività economiche",
        "description": (
            "Esplora la classificazione ATECO per la Versilia o per un singolo Comune, "
            "con storico 2014–2025."
        ),
        "metrics": [METRIC_KEY],
    })
    theme["sections"] = sections

    counts = [len(section.get("metrics", [])) for section in sections]
    if counts != EXPECTED_SECTION_COUNTS:
        raise RuntimeError(f"Sezioni Economia inattese: {counts} != {EXPECTED_SECTION_COUNTS}")
    if sum(counts) != len(theme["metrics"]) or len(theme["metrics"]) != 32:
        raise RuntimeError(
            f"Conteggio Economia incoerente: sezioni={sum(counts)}, tema={len(theme['metrics'])}"
        )
    if len(data.get("metrics", {})) != 184:
        raise RuntimeError(f"Catalogo globale inatteso: {len(data.get('metrics', {}))}")

    SITE_DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def refine_metric_controls() -> None:
    text = APP_02.read_text(encoding="utf-8")
    replacement = r'''  function metricControls(data, themeKey, metricKey, compact = true) {
    const theme = data.themes[themeKey];
    const groups = themeSections(theme);
    const contextTown = pageType === 'town' ? String(document.body?.dataset?.town || '') : '';
    const specialHref = metric => {
      const href = indicatorHref(metric);
      return contextTown ? `${href}?comune=${encodeURIComponent(contextTown)}` : href;
    };
    const labelCounts = theme.metrics.reduce((counts, key) => {
      const label = data.metrics[key].meta.shortLabel;
      counts[label] = (counts[label] || 0) + 1;
      return counts;
    }, {});
    return `<div class="metric-switch metric-catalog ${compact ? 'compact-list' : ''}" role="tablist" aria-label="Indicatori di ${html(theme.label)}">${groups.map(section => `<section class="metric-group" data-section="${html(section.key)}">
      <div class="metric-group-heading"><strong>${html(section.label)}</strong>${compact && section.description ? `<span>${html(section.description)}</span>` : ''}</div>
      <div class="metric-group-buttons">${section.metrics.map(key => {
        const metric = data.metrics[key];
        const meta = metric.meta;
        const label = labelCounts[meta.shortLabel] > 1 ? meta.label : meta.shortLabel;
        if (metric.dataStorage?.type === 'special-route') return `<a class="metric-route-link" href="${specialHref(metric)}"><span>Apri l'Atlante</span><small>Esplorazione ATECO <b>→</b></small></a>`;
        return `<button type="button" role="tab" data-metric="${key}" class="${key === metricKey ? 'active' : ''}" aria-selected="${key === metricKey}" tabindex="${key === metricKey ? '0' : '-1'}">${html(label)}</button>`;
      }).join('')}</div>
    </section>`).join('')}</div>`;
  }

  function groupedIndicatorCards(data, town, themeKey, activeKey) {
    const theme = data.themes[themeKey];
    const townSlug = normalize(town.name).replaceAll(' ', '-');
    return themeSections(theme).map(section => `<section class="indicator-group" data-section="${html(section.key)}">
      <div class="indicator-group-heading"><div><span class="overline">Sezione</span><h4>${html(section.label)}</h4></div><p>${html(section.description || '')}</p></div>
      <div class="indicator-card-grid">${section.metrics.map(key => {
        const metric = data.metrics[key];
        if (metric.dataStorage?.type === 'special-route') return `<a class="indicator-card special-route-card" href="${indicatorHref(metric)}?comune=${encodeURIComponent(townSlug)}"><span class="indicator-card-kicker">Atlante interattivo</span><h5>${html(metric.meta.label)}</h5><p>${html(metric.meta.description)}</p><span class="text-link">Esplora ${html(town.name)} <b>→</b></span></a>`;
        return indicatorCard(data, town, themeKey, key, activeKey);
      }).join('')}</div>
    </section>`).join('');
  }
'''
    pattern = (
        r"  function metricControls\(data, themeKey, metricKey, compact = true\) \{.*?\n"
        r"  function groupedIndicatorCards\(data, town, themeKey, activeKey\) \{.*?\n  \}\n"
    )
    text = replace_one(text, pattern, replacement, "controlli catalogo")
    APP_02.write_text(text, encoding="utf-8")


def refine_town_deep_dive() -> None:
    text = APP_04.read_text(encoding="utf-8")
    replacement = r'''    if (themeKey === 'economia') {
      const e = detail.economy;
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Redditi dichiarati</h3></div><p>Dettaglio aggiuntivo delle fasce di reddito del Comune. L'Atlante ATECO è disponibile come sezione autonoma nel selettore Economia.</p></div>
        <div class="deep-facts-grid"><article class="deep-fact"><span>Dichiaranti</span><strong>${number0.format(town.taxpayers)}</strong><small>Anno ${html(e.incomeYear)}</small></article></div>
        <details class="detail-disclosure"><summary><span>Mostra le fasce di reddito</span><small>Distribuzione dei dichiaranti</small></summary><div><h4>Dichiaranti per fascia di reddito</h4><ul class="deep-list deep-list--income">${e.incomeBands.map(b => `<li><span>${html(b.label)}</span><span class="deep-list-value"><strong>${number0.format(b.people)}</strong><small>dichiaranti</small></span></li>`).join('')}</ul></div></details></section>`;
    }
    if (themeKey === 'mobilita') {'''
    pattern = r"    if \(themeKey === 'economia'\) \{.*?\n    \}\n    if \(themeKey === 'mobilita'\) \{"
    text = replace_one(text, pattern, replacement, "deep dive comunale")
    APP_04.write_text(text, encoding="utf-8")


def refine_accordion_counts() -> None:
    text = ACCORDION.read_text(encoding="utf-8")
    old = "querySelectorAll('button').length"
    count = text.count(old)
    if count != 2:
        raise RuntimeError(f"Conteggi accordion inattesi: {count}")
    text = text.replace(old, "querySelectorAll('button, a.metric-route-link').length")
    ACCORDION.write_text(text, encoding="utf-8")


def validate() -> None:
    data = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    theme = data["themes"]["economia"]
    sections = theme["sections"]
    counts = [len(section.get("metrics", [])) for section in sections]
    atlas_sections = [section for section in sections if METRIC_KEY in section.get("metrics", [])]
    if counts != EXPECTED_SECTION_COUNTS or sum(counts) != 32:
        raise RuntimeError(f"Conteggio visuale Economia non valido: {counts}")
    if len(atlas_sections) != 1 or atlas_sections[0].get("key") != SECTION_KEY:
        raise RuntimeError("Atlante non isolato nella sezione autonoma")
    production = next(section for section in sections if section.get("key") == "produzione")
    if len(production.get("metrics", [])) != 10 or METRIC_KEY in production.get("metrics", []):
        raise RuntimeError("Sistema produttivo deve restare a 10 indicatori senza Atlante")

    controls = APP_02.read_text(encoding="utf-8")
    if "?comune=${encodeURIComponent(contextTown)}" not in controls:
        raise RuntimeError("Deep link comunale Atlante assente")
    if 'data-section="${html(section.key)}"' not in controls:
        raise RuntimeError("Sezioni catalogo non materializzate")

    deep = APP_04.read_text(encoding="utf-8")
    if "<ov-economy-atlas" in deep or "atlas-native-heading" in deep:
        raise RuntimeError("Atlante ancora incorporato in fondo agli indicatori comunali")
    if "e.topSectors.map" in deep:
        raise RuntimeError("Vecchio dettaglio ATECO per addetti ancora visibile")

    accordion = ACCORDION.read_text(encoding="utf-8")
    if accordion.count("button, a.metric-route-link") < 2:
        raise RuntimeError("Conteggi accordion non includono le route speciali")


def hide_workspace_changes() -> None:
    subprocess.run(
        [
            "git", "update-index", "--assume-unchanged",
            "data/site-data.json",
            "assets/app-parts/02.txt",
            "assets/app-parts/04.txt",
            "assets/ux-accordion.js",
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> None:
    refine_catalog()
    refine_metric_controls()
    refine_town_deep_dive()
    refine_accordion_counts()
    validate()
    hide_workspace_changes()
    print("Economia Atlas UX raffinata: sezioni 6+4+10+2+9+1=32, Atlante autonomo e deep link comunali.")


if __name__ == "__main__":
    main()
