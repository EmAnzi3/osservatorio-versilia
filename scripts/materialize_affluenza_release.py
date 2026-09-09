#!/usr/bin/env python3
"""Materializza Affluenza al voto nella release pubblica v1.32.0."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
APP_02 = ROOT / "assets" / "app-parts" / "02.txt"
BUILD_STATIC = ROOT / "scripts" / "build_static.py"

METRIC_KEY = "voterTurnout"
CANONICAL_ROUTE = "confronta/comunita/affluenza/"
SOURCE_URL = "https://elezionistorico.interno.gov.it/eligendo/opendata.php"
SOURCE_LABEL = "Ministero dell'Interno — DAIT / Eligendo"
VERSILIA = 62.932571147581285
LATEST = (
    ("Camaiore", "046005", "camaiore", 62.602431680451275),
    ("Forte dei Marmi", "046013", "forte-dei-marmi", 65.53630667158129),
    ("Massarosa", "046018", "massarosa", 62.66844119114956),
    ("Pietrasanta", "046024", "pietrasanta", 64.21848561759728),
    ("Seravezza", "046028", "seravezza", 60.46330543118552),
    ("Stazzema", "046030", "stazzema", 56.64423885618166),
    ("Viareggio", "046033", "viareggio", 63.2455207395893),
)


def make_metric() -> dict:
    return {
        "meta": {
            "key": METRIC_KEY,
            "theme": "comunita",
            "label": "Affluenza al voto",
            "shortLabel": "Affluenza al voto",
            "description": (
                "Consulta e confronta l'affluenza a Politiche, Europee, Regionali Toscana, "
                "Referendum ed elezioni comunali nei sette Comuni della Versilia."
            ),
            "unit": "%",
            "year": "2026",
            "source": SOURCE_LABEL,
            "update": "Per consultazione",
            "freshness": "Ultima consultazione ufficiale disponibile",
            "polarity": "neutral",
            "context": "Partecipazione civica",
            "keywords": ["affluenza", "elezioni", "votazioni", "referendum", "partecipazione civica", "politiche", "europee", "regionali", "comunali"],
            "sortable": False,
            "periodType": "irregular",
            "detailGroup": "comunita",
            "detailRoute": CANONICAL_ROUTE,
            "detailLabel": "Archivio affluenza",
            "sourceMeta": {
                "publisher": "Ministero dell'Interno — Dipartimento per gli Affari Interni e Territoriali",
                "note": "Affluenza ufficiale per consultazione e Comune; nessuna stima dei dati mancanti.",
            },
        },
        "sourceUrl": SOURCE_URL,
        "rows": [
            {
                "town": name,
                "code": code,
                "slug": slug,
                "value": value,
                "formatted": f"{value:.1f}%".replace(".", ","),
                "normalized": value,
                "benchmarkValue": VERSILIA,
                "year": 2026,
            }
            for name, code, slug, value in LATEST
        ],
        "aggregate": {
            "value": VERSILIA,
            "label": "Versilia · referendum costituzionale 22–23 marzo 2026",
            "note": "Affluenza calcolata sul totale di elettori e votanti dei sette Comuni.",
        },
        "method": {
            "type": "Archivio delle consultazioni elettorali",
            "formula": "Affluenza = votanti / elettori × 100.",
            "coverage": "7/7 Comuni; profondità storica secondo disponibilità ufficiale digitale.",
        },
        "dataStorage": {"type": "special-route", "detailRoute": CANONICAL_ROUTE},
    }


def patch_catalog() -> None:
    data = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    metrics = data.setdefault("metrics", {})
    metrics.setdefault(METRIC_KEY, make_metric())

    theme = data.get("themes", {}).get("comunita")
    if not theme:
        raise RuntimeError("Tema 'comunita' non trovato")
    if METRIC_KEY not in theme.setdefault("metrics", []):
        theme["metrics"].append(METRIC_KEY)

    sections = theme.setdefault("sections", [])
    section = next((s for s in sections if s.get("key") == "partecipazione-civica"), None)
    if section is None:
        section = {
            "key": "partecipazione-civica",
            "label": "Partecipazione civica",
            "description": "Affluenza alle consultazioni elettorali e serie storiche della partecipazione al voto.",
            "metrics": [],
        }
        sections.append(section)
    if METRIC_KEY not in section.setdefault("metrics", []):
        section["metrics"].append(METRIC_KEY)

    atlas = metrics.get("economyActivityAtlas")
    if atlas:
        atlas.setdefault("meta", {}).setdefault("detailLabel", "Atlante interattivo")

    data["version"] = "v1.32.0"
    data["release_version"] = "1.32.0"
    if "updated" in data:
        data["updated"] = "9 settembre 2026"
    SITE_DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    external = sum(
        m.get("dataStorage", {}).get("type") == "external-climate"
        for m in metrics.values()
    )
    # Nel registry storico "inline" significa incorporato nella release pubblica:
    # comprende anche le metriche special-route, ma non le quattro climatiche esterne.
    registry["expectedMetricCount"] = len(metrics)
    registry["expectedExternalMetricCount"] = external
    registry["expectedInlineMetricCount"] = len(metrics) - external
    profile = "dait-eligendo-irregular"
    registry.setdefault("sourceProfiles", {})[profile] = {
        "publisher": "Ministero dell'Interno — DAIT / Eligendo",
        "frequency": "irregular",
        "frequencyLabel": "Per consultazione elettorale",
        "expectedRelease": "Dopo ogni consultazione",
        "acquisitionMethod": (
            "Open Data e archivio elettorale ufficiale DAIT/Eligendo, con integrazione di fonti comunali "
            "ufficiali quando necessaria per le consultazioni locali."
        ),
        "licenseName": "Condizioni indicate dalla fonte ufficiale",
        "licenseUrl": SOURCE_URL,
    }
    registry.setdefault("sourceProfileByUrl", {})[SOURCE_URL] = profile
    registry.setdefault("metricOverrides", {})[METRIC_KEY] = {"profile": profile}
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_special_route_labels() -> None:
    text = APP_02.read_text(encoding="utf-8")
    old_controls = '''if (metric.dataStorage?.type === 'special-route') return `<a class="metric-route-link" href="${specialHref(metric)}"><span>Apri l'Atlante</span><small>Esplorazione ATECO <b>→</b></small></a>`;'''
    new_controls = '''if (metric.dataStorage?.type === 'special-route') return `<a class="metric-route-link" href="${specialHref(metric)}"><span>${html(meta.detailLabel || meta.label)}</span><small>Apri approfondimento <b>→</b></small></a>`;'''
    if old_controls in text:
        text = text.replace(old_controls, new_controls, 1)

    old_card = '''if (metric.dataStorage?.type === 'special-route') return `<a class="indicator-card special-route-card" href="${indicatorHref(metric)}?comune=${encodeURIComponent(townSlug)}"><span class="indicator-card-kicker">Atlante interattivo</span><h5>${html(metric.meta.label)}</h5><p>${html(metric.meta.description)}</p><span class="text-link">Esplora ${html(town.name)} <b>→</b></span></a>`;'''
    new_card = '''if (metric.dataStorage?.type === 'special-route') return `<a class="indicator-card special-route-card" href="${indicatorHref(metric)}?comune=${encodeURIComponent(townSlug)}"><span class="indicator-card-kicker">${html(metric.meta.detailLabel || 'Approfondimento')}</span><h5>${html(metric.meta.label)}</h5><p>${html(metric.meta.description)}</p><span class="text-link">Apri ${html(town.name)} <b>→</b></span></a>`;'''
    if old_card in text:
        text = text.replace(old_card, new_card, 1)

    if "meta.detailLabel || meta.label" not in text or "metric.meta.detailLabel || 'Approfondimento'" not in text:
        raise RuntimeError("Renderer special-route non reso generico")
    if "Apri l'Atlante" in text or "Esplorazione ATECO" in text:
        raise RuntimeError("Renderer special-route conserva etichette Atlante hardcoded")
    APP_02.write_text(text, encoding="utf-8")


def patch_builder_routes() -> None:
    text = BUILD_STATIC.read_text(encoding="utf-8")
    route_line = f'    "{CANONICAL_ROUTE}",\n'
    if route_line not in text:
        atlas_line = '    "confronta/economia/atlante-attivita-economiche/",\n'
        if atlas_line not in text:
            raise RuntimeError("Route Atlante non trovata prima della materializzazione Affluenza")
        text = text.replace(atlas_line, atlas_line + route_line, 1)
    BUILD_STATIC.write_text(text, encoding="utf-8")


def main() -> None:
    for path in (
        ROOT / "confronta" / "comunita" / "affluenza" / "index.html",
        ROOT / "assets" / "affluenza-v3.js",
        ROOT / "data" / "affluenza" / "archive-00.b64",
    ):
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"Asset Affluenza mancante: {path.relative_to(ROOT)}")
    patch_catalog()
    patch_special_route_labels()
    patch_builder_routes()
    print("Affluenza al voto v1.32.0 materializzata nella release pubblica.")


if __name__ == "__main__":
    main()
