#!/usr/bin/env python3
'''Materializza Economia II · Atlante nel checkout effimero della release.'''
from __future__ import annotations

import base64
import gzip
import json
import re
import runpy
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
ATLAS_DIR = ROOT / "data" / "economy-atlas"
METADATA = ATLAS_DIR / "metadata.json"
APP_00 = ROOT / "assets" / "app-parts" / "00.txt"
APP_02 = ROOT / "assets" / "app-parts" / "02.txt"
APP_04 = ROOT / "assets" / "app-parts" / "04.txt"
APP_LOADER = ROOT / "assets" / "app.js"
STATIC_CSS = ROOT / "assets" / "static.css"
BUILD_STATIC = ROOT / "scripts" / "build_static.py"
ATLAS_RUNTIME = ROOT / "assets" / "economy-atlas.js"
ATLAS_SOURCE_DIR = ROOT / "assets" / "economy-atlas-src"

METRIC_KEY = "economyActivityAtlas"
RELEASE_VERSION = "v1.31.0"
RELEASE_UPDATED = "6 settembre 2026"
CANONICAL_ROUTE = "confronta/economia/atlante-attivita-economiche/"
SOURCE_URL = "https://www.regione.toscana.it/-/banca-dati-imprese-toscana"
SOURCE_LABEL = "Regione Toscana — Banca dati Imprese / Registro Imprese InfoCamere"

MATERIALIZED_PATHS = (
    "data/site-data.json",
    "data/source-registry.json",
    "assets/app-parts/00.txt",
    "assets/app-parts/02.txt",
    "assets/app-parts/04.txt",
    "assets/app.js",
    "assets/static.css",
    "scripts/build_static.py",
)


def _replace_exact(text: str, old: str, new: str, label: str, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"Patch Atlante {label}: attese {expected} occorrenze, trovate {count}")
    return text.replace(old, new, expected)


def _replace_regex(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"Patch Atlante {label}: pattern non trovato o ambiguo ({count})")
    return updated


def ensure_release_baseline() -> None:
    data = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    metrics = data.get("metrics", {})
    if METRIC_KEY in metrics:
        return
    agriculture_keys = {
        "agriculturalRenewalAndLeadership",
        "agriculturalDiversificationAndModernization",
    }
    if agriculture_keys.issubset(metrics):
        if len(metrics) != 183:
            raise RuntimeError(f"Baseline release inatteso prima dell'Atlante: {len(metrics)} indicatori")
        return
    if len(metrics) != 181:
        raise RuntimeError(f"Catalogo base inatteso prima di Agricoltura II: {len(metrics)} indicatori")
    runpy.run_path(str(ROOT / "scripts" / "materialize_agricoltura_ii_release.py"), run_name="__main__")
    data = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    if len(data.get("metrics", {})) != 183 or not agriculture_keys.issubset(data.get("metrics", {})):
        raise RuntimeError("Agricoltura II non ha prodotto il baseline pubblico 183")


def load_atlas_payload() -> tuple[dict, dict]:
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    if metadata.get("codes") != 1228:
        raise RuntimeError(f"Numero codici Atlante inatteso: {metadata.get('codes')}")
    if metadata.get("classification") != "Ateco2007":
        raise RuntimeError(f"Classificazione Atlante inattesa: {metadata.get('classification')}")
    if metadata.get("runtime_years") != [2014, 2025]:
        raise RuntimeError(f"Finestra runtime inattesa: {metadata.get('runtime_years')}")
    pieces = []
    for name in metadata.get("files", []):
        path = ATLAS_DIR / name
        if not path.exists():
            raise RuntimeError(f"Chunk Atlante mancante: {name}")
        pieces.append(path.read_text(encoding="utf-8").strip())
    payload = json.loads(gzip.decompress(base64.b64decode("".join(pieces))).decode("utf-8"))
    if payload.get("v") != 2 or len(payload.get("c", [])) != 1228:
        raise RuntimeError("Payload Atlante compatto non coerente con metadata")
    if payload.get("y", [None])[0] != 2014 or payload.get("y", [None])[-1] != 2025:
        raise RuntimeError("Serie runtime Atlante inattesa")
    return metadata, payload


def latest_town_totals(payload: dict) -> dict[str, int]:
    latest = len(payload["y"]) - 1
    divisions = [
        row for row in payload["c"]
        if re.fullmatch(r"[A-Z]\s+\d{2}", str(row[0] or ""))
    ]
    if not divisions:
        raise RuntimeError("Divisioni ATECO non trovate nel payload")
    totals: dict[str, int] = {}
    for town_index, (slug, name) in enumerate(payload["t"]):
        total = 0
        seen = False
        for row in divisions:
            value = row[3 + town_index][0][latest]
            if value is None:
                continue
            total += int(value)
            seen = True
        if not seen:
            raise RuntimeError(f"Nessuna UL aggregabile per {name}")
        totals[slug] = total
    return totals


def make_metric(data: dict, payload: dict) -> dict:
    totals = latest_town_totals(payload)
    towns_by_slug = {
        re.sub(r"[^a-z0-9]+", "-", town["name"].lower()).strip("-"): town
        for town in data.get("towns", [])
    }
    rows = []
    for slug, name in payload["t"]:
        site_town = towns_by_slug.get(slug)
        if not site_town:
            raise RuntimeError(f"Comune Atlante non presente nel catalogo: {name}")
        value = totals[slug]
        rows.append({
            "town": name,
            "code": site_town["code"],
            "slug": slug,
            "value": value,
            "formatted": f"{value:,}".replace(",", "."),
            "normalized": None,
            "benchmarkValue": None,
            "year": 2025,
        })

    aggregate_value = sum(row["value"] for row in rows)
    return {
        "meta": {
            "key": METRIC_KEY,
            "theme": "economia",
            "label": "Atlante delle attività economiche",
            "shortLabel": "Atlante attività economiche",
            "description": (
                "Esplora 1.228 codici ATECO e confronta unità locali attive, "
                "specializzazione, peso toscano, quota artigiana e storico 2014–2025 "
                "nei sette Comuni della Versilia."
            ),
            "unit": "number",
            "year": "2025",
            "source": SOURCE_LABEL,
            "update": "Annuale",
            "freshness": "Ultimo anno consolidato disponibile",
            "polarity": "neutral",
            "context": "Struttura del sistema produttivo",
            "keywords": [
                "ateco", "attività economiche", "imprese", "unità locali",
                "registro imprese", "infocamere", "artigianato", "specializzazione"
            ],
            "sortable": False,
            "periodType": "annual",
            "detailGroup": "economia",
            "detailRoute": CANONICAL_ROUTE,
            "sourceMeta": {
                "publisher": "Regione Toscana — Ufficio regionale di Statistica / InfoCamere",
                "note": (
                    "Dati comunali del Registro Imprese. L'Atlante usa la tassonomia "
                    "ATECO 2007 aggiornamento 2022 e mantiene separati i dati Istat ASIA sugli addetti."
                ),
            },
        },
        "sourceUrl": SOURCE_URL,
        "rows": rows,
        "aggregate": {
            "value": aggregate_value,
            "label": "Versilia · unità locali attive",
            "note": "Somma delle unità locali attive dei sette Comuni nel 2025.",
        },
        "method": {
            "type": "Atlante gerarchico ATECO",
            "formula": (
                "Valori diretti quando pubblicati dalla fonte; ai livelli privi di valore diretto "
                "l'interfaccia somma i discendenti disponibili e segnala il dato derivato."
            ),
            "coverage": "7/7 Comuni · storico 2014–2025 · 1.228 codici",
        },
        "dataStorage": {
            "type": "special-route",
            "detailRoute": CANONICAL_ROUTE,
        },
    }


def patch_catalog() -> None:
    data = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    _, payload = load_atlas_payload()
    metrics = data.setdefault("metrics", {})
    if METRIC_KEY not in metrics:
        metrics[METRIC_KEY] = make_metric(data, payload)

    theme = data["themes"]["economia"]
    if METRIC_KEY not in theme["metrics"]:
        theme["metrics"].append(METRIC_KEY)

    sections = theme.get("sections", [])
    production = next((section for section in sections if section.get("key") == "produzione"), None)
    if not production:
        raise RuntimeError("Sezione Economia 'produzione' non trovata")
    if METRIC_KEY not in production["metrics"]:
        production["metrics"].append(METRIC_KEY)

    data["version"] = RELEASE_VERSION
    if "updated" in data:
        data["updated"] = RELEASE_UPDATED
    SITE_DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    registry["expectedMetricCount"] = len(metrics)
    registry["expectedExternalMetricCount"] = 4
    registry["expectedInlineMetricCount"] = len(metrics) - 5
    registry.setdefault("sourceProfiles", {})["regione-toscana-infocamere-annual"] = {
        "publisher": "Regione Toscana — Ufficio regionale di Statistica / InfoCamere",
        "frequency": "annual",
        "frequencyLabel": "Annuale",
        "expectedRelease": "Dopo il consolidamento dei dati al 31 dicembre",
        "acquisitionMethod": (
            "Banca dati Imprese Toscana su Registro Imprese InfoCamere; selezione comunale per "
            "attività economica e unità locali attive, con snapshot e controlli di coerenza "
            "conservati nella repository."
        ),
        "licenseName": "Condizioni indicate dalla fonte ufficiale",
        "licenseUrl": SOURCE_URL,
    }
    registry.setdefault("sourceProfileByUrl", {})[SOURCE_URL] = "regione-toscana-infocamere-annual"
    registry.setdefault("metricOverrides", {})[METRIC_KEY] = {"profile": "regione-toscana-infocamere-annual"}
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_renderer() -> None:
    text = APP_00.read_text(encoding="utf-8")
    old = "  const indicatorSlug = (metric) => normalize(metric?.meta?.label).replaceAll(' ', '-');\n  const indicatorHref = (metric) => route(`indicatori/${indicatorSlug(metric)}/`);"
    new = "  const indicatorSlug = (metric) => normalize(metric?.meta?.label).replaceAll(' ', '-');\n  const indicatorHref = (metric) => {\n    const detailRoute = String(metric?.meta?.detailRoute || '').replace(/^\\/+/, '');\n    if (metric?.dataStorage?.type === 'special-route' && detailRoute) return route(detailRoute);\n    return route(`indicatori/${indicatorSlug(metric)}/`);\n  };"
    if "dataStorage?.type === 'special-route'" not in text:
        text = _replace_exact(text, old, new, "indicatorHref")
    APP_00.write_text(text, encoding="utf-8")

    text = APP_02.read_text(encoding="utf-8")
    if "metric-route-link" not in text:
        pattern = r"  function metricControls\(data, themeKey, metricKey, compact = true\) \{.*?\n  \}\n\n  function groupedIndicatorCards\(data, town, themeKey, activeKey\) \{.*?\n  \}\n"
        replacement = r'''  function metricControls(data, themeKey, metricKey, compact = true) {
    const theme = data.themes[themeKey];
    const groups = themeSections(theme);
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
        if (metric.dataStorage?.type === 'special-route') return `<a class="metric-route-link" href="${indicatorHref(metric)}"><span>${html(label)}</span><small>Atlante interattivo <b>→</b></small></a>`;
        return `<button type="button" role="tab" data-metric="${key}" class="${key === metricKey ? 'active' : ''}" aria-selected="${key === metricKey}" tabindex="${key === metricKey ? '0' : '-1'}">${html(label)}</button>`;
      }).join('')}</div>
    </section>`).join('')}</div>`;
  }

  function groupedIndicatorCards(data, town, themeKey, activeKey) {
    const theme = data.themes[themeKey];
    return themeSections(theme).map(section => `<section class="indicator-group" data-section="${html(section.key)}">
      <div class="indicator-group-heading"><div><span class="overline">Sezione</span><h4>${html(section.label)}</h4></div><p>${html(section.description || '')}</p></div>
      <div class="indicator-card-grid">${section.metrics.map(key => {
        const metric = data.metrics[key];
        if (metric.dataStorage?.type === 'special-route') return `<a class="indicator-card special-route-card" href="#atlante-attivita-economiche"><span class="indicator-card-kicker">Atlante interattivo</span><h5>${html(metric.meta.label)}</h5><p>${html(metric.meta.description)}</p><span class="text-link">Esplora nel profilo <b>↓</b></span></a>`;
        return indicatorCard(data, town, themeKey, key, activeKey);
      }).join('')}</div>
    </section>`).join('');
  }
'''
        text = _replace_regex(text, pattern, replacement, "controlli e card Atlante")
    APP_02.write_text(text, encoding="utf-8")

    text = APP_04.read_text(encoding="utf-8")
    if "economy-atlas-deep-dive" not in text:
        pattern = r"    if \(themeKey === 'economia'\) \{.*?\n    \}\n    if \(themeKey === 'mobilita'\) \{"
        replacement = r'''    if (themeKey === 'economia') {
      const e = detail.economy;
      const atlasMetric = data.metrics.economyActivityAtlas;
      return `<section class="topic-deep-dive economy-atlas-deep-dive" id="atlante-attivita-economiche"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Struttura economica</h3></div><p>Fasce di reddito e Atlante ATECO in un'unica lettura comunale. Gli addetti Istat ASIA restano nei dati strutturali, separati dai dati del Registro Imprese.</p></div>
        <div class="deep-facts-grid"><article class="deep-fact"><span>Dichiaranti</span><strong>${number0.format(town.taxpayers)}</strong><small>Anno ${html(e.incomeYear)}</small></article></div>
        <details class="detail-disclosure"><summary><span>Mostra le fasce di reddito</span><small>Distribuzione dei dichiaranti</small></summary><div><h4>Dichiaranti per fascia di reddito</h4><ul class="deep-list deep-list--income">${e.incomeBands.map(b => `<li><span>${html(b.label)}</span><span class="deep-list-value"><strong>${number0.format(b.people)}</strong><small>dichiaranti</small></span></li>`).join('')}</ul></div></details>
        <div class="atlas-native-heading"><div><span class="overline">Economia · Registro Imprese</span><h4>${html(atlasMetric.meta.label)}</h4><p>${html(atlasMetric.meta.description)}</p></div><a class="text-link" href="${indicatorHref(atlasMetric)}">Apri a tutta pagina <b>→</b></a></div>
        <ov-economy-atlas town="${normalize(town.name).replaceAll(' ', '-')}" embedded></ov-economy-atlas></section>`;
    }
    if (themeKey === 'mobilita') {'''
        text = _replace_regex(text, pattern, replacement, "deep dive Economia")
    APP_04.write_text(text, encoding="utf-8")


def patch_loader_and_build() -> None:
    text = APP_LOADER.read_text(encoding="utf-8")
    old = "    await loadScript(new URL(`./agricoltura-ii-draft.js?v=${VERSION}`, loader.src).href);"
    new = "    await Promise.all([\n      loadScript(new URL(`./agricoltura-ii-draft.js?v=${VERSION}`, loader.src).href),\n      loadScript(new URL(`./economy-atlas.js?v=${VERSION}`, loader.src).href)\n    ]);"
    if "./economy-atlas.js?v=" not in text:
        text = _replace_exact(text, old, new, "loader Atlante")
    APP_LOADER.write_text(text, encoding="utf-8")

    text = BUILD_STATIC.read_text(encoding="utf-8")
    old_filter = '    if metric.get("dataStorage", {}).get("type") != "external-climate"\n'
    new_filter = '    if metric.get("dataStorage", {}).get("type") not in {"external-climate", "special-route"}\n'
    if '"special-route"' not in text.split("INDICATOR_ROUTES", 1)[0]:
        text = _replace_exact(text, old_filter, new_filter, "route indicatori speciali")

    route_anchor = '    *[f"confronta/{slug}/" for slug in THEME_SLUGS],\n'
    route_line = f'    "{CANONICAL_ROUTE}",\n'
    if route_line not in text:
        text = _replace_exact(text, route_anchor, route_anchor + route_line, "route Atlante")

    text = re.sub(
        r'^\s*text = re\.sub\(r"\(\?:\\\.\\\./\)\*assets/ateco-detail\\\.css.*?\n',
        "",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^\s*text = re\.sub\(r"\(\?:\\\.\\\./\)\*assets/ateco-detail\\\.js.*?\n',
        "",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'\n        if "assets/ateco-detail\.css" not in text:\n'
        r'            text = text\.replace\("</head>", f\'  <link rel="stylesheet" href="\{assets\}assets/ateco-detail\.css">\\n</head>\'\)\n',
        "\n",
        text,
    )
    old_js = '''        if "assets/ateco-detail.js" not in text:
            text = text.replace(
                "</body>",
                f'  <script src="{assets}assets/ateco-detail.js" defer></script>\n</body>',
            )
'''
    new_js = '''        if "assets/economy-atlas.js" not in text:
            text = text.replace(
                "</body>",
                f'  <script src="{assets}assets/economy-atlas.js" defer></script>\n</body>',
            )
'''
    if "assets/economy-atlas.js" not in text:
        text = _replace_exact(text, old_js, new_js, "runtime Atlante statico")
    if "ateco-detail.js" in text or "ateco-detail.css" in text:
        raise RuntimeError("Riferimenti ateco-detail residui in build_static.py")
    BUILD_STATIC.write_text(text, encoding="utf-8")


def patch_integration_css() -> None:
    marker = "/* economy-atlas-native-integration */"
    text = STATIC_CSS.read_text(encoding="utf-8")
    if marker in text:
        return
    text += f'''\n\n{marker}\n.metric-route-link{{display:flex;align-items:center;justify-content:space-between;gap:12px;text-decoration:none;border:1px solid color-mix(in srgb,var(--theme-accent,#ad6247) 35%,#d9dfdd);border-radius:10px;padding:10px 12px;background:#fff;color:inherit}}\n.metric-route-link:hover{{border-color:var(--theme-accent,#ad6247);background:#faf6f2}}\n.metric-route-link small{{font-size:.72rem;color:#667780;white-space:nowrap}}\n.special-route-card{{text-decoration:none;color:inherit;display:flex;flex-direction:column;align-items:flex-start;min-width:0}}\n.special-route-card h5{{margin:.35rem 0 .55rem;font-size:1rem}}\n.special-route-card p{{margin:0 0 .8rem;color:#61717b;line-height:1.45}}\n.indicator-card-kicker{{font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;font-weight:800;color:#ad6247}}\n.economy-atlas-deep-dive{{scroll-margin-top:110px}}\n.atlas-native-heading{{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;margin:32px 0 14px;padding-top:24px;border-top:1px solid rgba(16,47,69,.14)}}\n.atlas-native-heading h4{{margin:.3rem 0 .4rem;font-size:clamp(1.35rem,2.2vw,1.85rem)}}\n.atlas-native-heading p{{max-width:760px;margin:0;color:#61717b;line-height:1.5}}\nov-economy-atlas{{display:block;min-width:0}}\n@media(max-width:700px){{.atlas-native-heading{{align-items:flex-start;flex-direction:column;gap:10px}}.metric-route-link{{align-items:flex-start;flex-direction:column;gap:4px}}}}\n'''
    STATIC_CSS.write_text(text, encoding="utf-8")


def materialize_runtime() -> None:
    parts = sorted(ATLAS_SOURCE_DIR.glob("[0-9][0-9].js"))
    if not parts:
        raise RuntimeError("Sorgenti runtime Atlante mancanti")
    runtime = "".join(path.read_text(encoding="utf-8") for path in parts)
    ATLAS_RUNTIME.write_text(runtime, encoding="utf-8")


def validate_runtime() -> None:
    if not ATLAS_RUNTIME.exists():
        raise RuntimeError("Runtime Atlante mancante")
    runtime = ATLAS_RUNTIME.read_text(encoding="utf-8")
    forbidden = ("MutationObserver", "fetch('https://", 'fetch("https://', "economy-atlas-parts")
    for token in forbidden:
        if token in runtime:
            raise RuntimeError(f"Runtime Atlante contiene dipendenza vietata: {token}")
    if "customElements.define('ov-economy-atlas'" not in runtime:
        raise RuntimeError("Custom element Atlante non definito")
    subprocess.run(["node", "--check", str(ATLAS_RUNTIME)], check=True)


def validate() -> None:
    data = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    metric = data.get("metrics", {}).get(METRIC_KEY)
    if not metric:
        raise RuntimeError("Metrica Atlante non materializzata")
    if len(data["metrics"]) != 184:
        raise RuntimeError(f"Catalogo release: attesi 184 indicatori, trovati {len(data['metrics'])}")
    if len(data["themes"]["economia"]["metrics"]) != 32:
        raise RuntimeError("Economia deve contenere 32 indicatori")
    if registry.get("expectedMetricCount") != 184 or registry.get("expectedInlineMetricCount") != 179:
        raise RuntimeError("Source registry non allineato a 184/179")
    production = next(
        section for section in data["themes"]["economia"]["sections"]
        if section["key"] == "produzione"
    )
    if production["metrics"].count(METRIC_KEY) != 1:
        raise RuntimeError("Atlante non inserito una sola volta in Struttura del sistema produttivo")
    if "e.topSectors.map" in APP_04.read_text(encoding="utf-8"):
        raise RuntimeError("Vecchio dettaglio ATECO per addetti ancora visibile in Economia")


def hide_expected_workspace_changes() -> None:
    subprocess.run(
        ["git", "update-index", "--assume-unchanged", *MATERIALIZED_PATHS],
        cwd=ROOT,
        check=True,
    )


def main() -> None:
    ensure_release_baseline()
    patch_catalog()
    patch_renderer()
    patch_loader_and_build()
    patch_integration_css()
    materialize_runtime()
    validate_runtime()
    validate()
    hide_expected_workspace_changes()
    print("Economia II release workspace: v1.31.0, 184 indicatori, Economia 32, Atlante ATECO nativo materializzato.")


if __name__ == "__main__":
    main()
