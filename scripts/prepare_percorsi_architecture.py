#!/usr/bin/env python3
"""Prepara in CI l'architettura draft Percorsi senza contaminare il dataset canonico.

Il passaggio viene eseguito solo per la seconda build della PR Percorsi:
- integra Mobilita lenta nella normale grammatica degli indicatori;
- sposta sicurezza stradale e criminalita nel tema Sicurezza e territorio;
- aggiunge i cinque indicatori cartografici derivati dal dataset validato;
- rende disponibile la route /confronta/sicurezza/;
- rimuove i vecchi box speciali Percorsi dal renderer.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA_PATH = ROOT / "data" / "site-data.json"
STATS_PATH = ROOT / "percorsi" / "data" / "site_stats.json"
BUILD_STATIC = ROOT / "scripts" / "build_static.py"
APP_PARTS = ROOT / "assets" / "app-parts"

SLOW_METRICS = (
    ("slowMobilityRoutes", "Percorsi disponibili", "Percorsi pubblici che attraversano il Comune", "routes", "percorsi"),
    ("slowMobilityTrekking", "Trekking", "Percorsi trekking che attraversano il Comune", "trekking", "percorsi trekking"),
    ("slowMobilityCammini", "Cammini", "Cammini che attraversano il Comune", "cammino", "cammini"),
    ("slowMobilityBici", "Bici", "Percorsi ciclabili che attraversano il Comune", "bicycle", "percorsi bici"),
    ("slowMobilityMtb", "MTB", "Percorsi MTB che attraversano il Comune", "mtb", "percorsi MTB"),
)


def slugify(value: str) -> str:
    import unicodedata
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def metric_rows(data: dict, stats: dict, field: str) -> list[dict]:
    rows = []
    for town in data["towns"]:
        slug = slugify(town["name"])
        item = stats["municipalities"][slug]
        value = int(item["routes"] if field == "routes" else item["by_mode"].get(field, 0))
        rows.append({
            "town": town["name"],
            "code": town["code"],
            "slug": slug,
            "value": value,
            "formatted": str(value),
            "series": None,
            "normalized": None,
            "benchmarkValue": value,
        })
    return rows


def add_slow_metric(data: dict, stats: dict, key: str, short: str, label: str, field: str, noun: str) -> None:
    rows = metric_rows(data, stats, field)
    unique_total = int(stats["versilia"]["routes"] if field == "routes" else stats["versilia"]["by_mode"].get(field, 0))
    mean_value = sum(row["value"] for row in rows) / len(rows)
    if field == "routes":
        description = (
            "Numero di sentieri, cammini e percorsi ciclabili pubblici A0/B1 che attraversano il territorio comunale. "
            "Uno stesso percorso puo interessare piu Comuni."
        )
        unique_note = f"In Versilia sono pubblicati {unique_total} percorsi unici; i conteggi comunali non sono sommabili."
    else:
        description = (
            f"Numero di {noun} pubblici A0/B1 che attraversano il territorio comunale. "
            "Uno stesso percorso puo interessare piu Comuni."
        )
        unique_note = f"In Versilia sono pubblicati {unique_total} {noun} unici; i conteggi comunali non sono sommabili."

    data["metrics"][key] = {
        "meta": {
            "key": key,
            "theme": "mobilita",
            "label": label,
            "shortLabel": short,
            "description": description,
            "unit": "count",
            "year": "12 agosto 2026",
            "source": "Osservatorio Versilia — Percorsi Versilia",
            "polarity": "neutral",
        },
        "sourceUrl": "https://osservatorioversilia.it/percorsi/metodo.html",
        "rows": rows,
        "aggregate": {
            "value": mean_value,
            "label": "Media semplice dei 7 Comuni",
            "note": unique_note,
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione cartografica Osservatorio Versilia",
            "formula": "Conteggio dei percorsi pubblici A0/B1 che attraversano il territorio comunale.",
            "caveat": "I conteggi comunali non sono additivi: uno stesso percorso puo attraversare piu Comuni. I chilometri comunali non sono pubblicati finche le geometrie non vengono intersecate con i confini amministrativi ufficiali.",
            "coverage": "7/7",
        },
    }


def augment_site_data() -> None:
    data = json.loads(SITE_DATA_PATH.read_text(encoding="utf-8"))
    stats = json.loads(STATS_PATH.read_text(encoding="utf-8"))

    mobility = data["themes"]["mobilita"]
    mobility["description"] = "Pendolarismo, parco veicolare, ricarica elettrica, connettivita digitale e mobilita lenta."
    mobility["metrics"] = [key for key in mobility["metrics"] if key != "roadInjuries"]
    mobility["sections"] = [section for section in mobility["sections"] if section.get("key") != "sicurezza"]

    slow_keys = [entry[0] for entry in SLOW_METRICS]
    for key, short, label, field, noun in SLOW_METRICS:
        add_slow_metric(data, stats, key, short, label, field, noun)
    mobility["metrics"].extend(slow_keys)
    mobility["sections"].append({
        "key": "mobilita-lenta",
        "label": "Mobilita lenta",
        "description": "Sentieri, cammini e percorsi ciclabili pubblici verificati nel territorio.",
        "metrics": slow_keys,
    })
    mobility["featured"] = ["outsideMunicipality", "ftthCoverageDesi", "slowMobilityRoutes"]

    road = data["metrics"]["roadInjuries"]
    road["meta"]["theme"] = "sicurezza"
    road["method"]["caveat"] = (
        "Il numero di feriti dipende anche dall'intensita del traffico e dalla funzione stradale del territorio; "
        "non misura da solo il rischio individuale."
    )

    security = {
        "key": "sicurezza",
        "number": "07",
        "label": "Sicurezza e territorio",
        "question": "Quanto e sicuro il territorio e quali fenomeni emergono?",
        "description": "Sicurezza stradale e criminalita, distinguendo i dati comunali da quelli disponibili solo a scala sovracomunale.",
        "metrics": ["roadInjuries"],
        "sections": [{
            "key": "sicurezza-stradale",
            "label": "Sicurezza stradale",
            "description": "Incidenti e persone coinvolte, con confronto comunale omogeneo.",
            "metrics": ["roadInjuries"],
        }],
        "featured": ["roadInjuries"],
    }

    ordered = {}
    for key, theme in data["themes"].items():
        if key == "abitare":
            ordered["sicurezza"] = security
        ordered[key] = theme
    for index, theme in enumerate(ordered.values(), start=1):
        theme["number"] = f"{index:02d}"
    data["themes"] = ordered

    # Mantiene anche il riepilogo cartografico usato dalla pagina mappa.
    data["percorsi"] = stats
    SITE_DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_app_parts() -> None:
    files = sorted(APP_PARTS.glob("[0-9][0-9].txt"))
    if len(files) != 7:
        raise RuntimeError(f"Attesi 7 app-parts, trovati {len(files)}")

    # Icona per il nuovo tema.
    p0 = files[0]
    text = p0.read_text(encoding="utf-8")
    if "sicurezza:" not in text:
        pattern = r"(\n    mobilita: '[^\n]+',\n)"
        replacement = r"\1    sicurezza: '<path d=\"M20 13c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V5l8-3 8 3z\"></path><path d=\"m9 12 2 2 4-4\"></path>',\n"
        text, count = re.subn(pattern, replacement, text, count=1)
        if count != 1:
            raise RuntimeError("Impossibile aggiungere icona Sicurezza")
    p0.write_text(text, encoding="utf-8")

    # Rimuove i vecchi box speciali e sposta la criminalita nel nuovo tema.
    for path in files:
        text = path.read_text(encoding="utf-8")
        text = text.replace("${themeKey === 'mobilita' ? percorsiQuickMarkup(data) : ''}", "")
        text = text.replace("      ${themeKey === 'mobilita' ? percorsiCompareMarkup(data) : ''}\n", "")
        text = text.replace("      ${themeKey === 'mobilita' ? percorsiTownMarkup(data, town) : ''}\n", "")
        text = text.replace("${themeKey === 'mobilita' ? crimeMarkup(data) : ''}", "${themeKey === 'sicurezza' ? crimeMarkup(data) : ''}")
        text = text.replace("themeKey === 'mobilita' ? crimeMarkup(data) : ''", "themeKey === 'sicurezza' ? crimeMarkup(data) : ''")
        text = text.replace("if (themeKey === 'mobilita') installCrimeInteractions(data);", "if (themeKey === 'sicurezza') installCrimeInteractions(data);")

        # Per gli indicatori di mobilita lenta la cartografia e un'azione dell'indicatore,
        # non un box autonomo dentro la pagina.
        text = text.replace(
            'benchmark.innerHTML = benchmarkMarkup(metric, aggregate, unit, null);',
            "benchmark.innerHTML = metricKey.startsWith('slowMobility') ? '' : benchmarkMarkup(metric, aggregate, unit, null);",
        )
        text = text.replace(
            '<div class="data-actions"><a href="${indicatorHref(metric)}">Scheda indicatore</a><button type="button" data-download>',
            '<div class="data-actions"><a href="${indicatorHref(metric)}">Scheda indicatore</a>${metricKey.startsWith(\'slowMobility\') ? `<a href="${route(\'percorsi/\')}">Esplora la cartografia</a>` : \'\'}<button type="button" data-download>',
        )
        text = text.replace(
            '${townBenchmarkMarkup(metric, row, town)}',
            "${metricKey.startsWith('slowMobility') ? '' : townBenchmarkMarkup(metric, row, town)}",
        )
        text = text.replace(
            '<div class="data-actions town-data-actions"><a href="${indicatorHref(metric)}">Scheda indicatore</a><button type="button" data-share>',
            '<div class="data-actions town-data-actions"><a href="${indicatorHref(metric)}">Scheda indicatore</a>${metricKey.startsWith(\'slowMobility\') ? `<a href="${route(\'percorsi/?comune=\' + encodeURIComponent(town.name))}">Esplora sulla mappa</a>` : \'\'}<button type="button" data-share>',
        )
        path.write_text(text, encoding="utf-8")


def patch_build_routes() -> None:
    text = BUILD_STATIC.read_text(encoding="utf-8")
    if '    "sicurezza",' not in text:
        needle = '    "salute",\n]'
        if needle not in text:
            raise RuntimeError("Lista THEME_SLUGS non riconosciuta")
        text = text.replace(needle, '    "salute",\n    "sicurezza",\n]', 1)
    BUILD_STATIC.write_text(text, encoding="utf-8")


def main() -> None:
    if not STATS_PATH.exists():
        raise RuntimeError("Statistiche Percorsi mancanti")
    augment_site_data()
    patch_app_parts()
    patch_build_routes()
    print("Architettura draft pronta: Mobilita lenta integrata, Sicurezza e territorio separata, renderer senza box speciali.")


if __name__ == "__main__":
    main()
