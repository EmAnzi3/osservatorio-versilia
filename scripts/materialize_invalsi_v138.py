#!/usr/bin/env python3
"""Materializza la v1.38.0: risultati e competenze INVALSI.

La build resta offline e fail-closed: usa esclusivamente lo snapshot ufficiale
versionato in data/source-snapshots/invalsi-v138-official.json. Il dato comunale
è quello già aggregato da INVALSI alla scala "Comune plesso"; nessuna media di
scuole e nessuna media Versilia viene ricostruita.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "invalsi-v138-official.json"

RELEASE = "v1.38.0"
EXPECTED_BEFORE = 203
EXPECTED_AFTER = 207
TOWNS = [
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
]
NEW_KEYS = [
    "invalsiResults",
    "invalsiCompetence",
    "invalsiImplicitDispersion",
    "invalsiAcademicExcellence",
]
SOURCE_RESULTS = "invalsi-open-risultati-2025"
SOURCE_DISPERSION = "invalsi-open-dispersione-2025"


def finite_or_none(value, label: str):
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"v1.38: valore non numerico: {label}") from exc
    if not math.isfinite(number):
        raise RuntimeError(f"v1.38: valore non finito: {label}")
    return number


def pct_or_none(value, label: str):
    number = finite_or_none(value, label)
    if number is None:
        return None
    if number < 0 or number > 100:
        raise RuntimeError(f"v1.38: percentuale fuori dominio: {label}={number}")
    return number


def identities(site: dict) -> dict[str, dict]:
    population = site.get("metrics", {}).get("population", {})
    rows = {row.get("town"): row for row in population.get("rows", [])}
    if set(rows) != set(TOWNS):
        raise RuntimeError("v1.38: population non fornisce identita' 7/7.")
    return rows


def identity(row: dict) -> dict:
    return {"town": row["town"], "code": row["code"], "slug": row["slug"]}


def end_year(label: str) -> int:
    """2017-18 -> 2018; il sito usa anni numerici negli storici canonici."""
    try:
        start, end = str(label).split("-", 1)
        century = int(start[:2]) * 100
        value = century + int(end)
        if value < int(start):
            value += 100
        return value
    except Exception as exc:
        raise RuntimeError(f"v1.38: anno scolastico non valido: {label}") from exc


def series(years: list[str], values: list, *, period_labels: bool = True) -> dict:
    if len(years) != len(values):
        raise RuntimeError("v1.38: anni/valori disallineati.")
    return {
        "years": [end_year(year) for year in years],
        "values": [finite_or_none(value, f"series.{year}") for year, value in zip(years, values)],
        "periodLabels": list(years) if period_labels else None,
    }


def current(values: list):
    if not values:
        return None
    return finite_or_none(values[-1], "current")


def fmt(value, unit: str) -> str:
    number = finite_or_none(value, "fmt")
    if number is None:
        return "n.d."
    if unit == "percent":
        return f"{number:.1f}%".replace(".", ",")
    if unit == "invalsi_score":
        return f"{number:.1f}".replace(".", ",")
    return f"{number:.1f}".replace(".", ",")


def validate_series_block(block: dict, *, unit: str, require_levels: bool = False) -> None:
    years = block.get("years", [])
    if len(years) < 2 or years != sorted(years, key=end_year):
        raise RuntimeError(f"v1.38: serie non ordinata o troppo corta: {block.get('key')}")
    if block.get("latestYear") != years[-1]:
        raise RuntimeError(f"v1.38: latestYear incoerente: {block.get('key')}")
    if set(block.get("municipalities", {})) != set(TOWNS):
        raise RuntimeError(f"v1.38: perimetro comunale incompleto: {block.get('key')}")
    for scope, data in [
        *[(town, block["municipalities"][town]) for town in TOWNS],
        ("Toscana", block.get("tuscany", {})),
        ("Italia", block.get("italy", {})),
    ]:
        values = data.get("values", [])
        if len(values) != len(years):
            raise RuntimeError(f"v1.38: lunghezza serie incoerente {block.get('key')} / {scope}")
        for index, value in enumerate(values):
            if unit == "percent":
                pct_or_none(value, f"{block.get('key')}.{scope}.{years[index]}")
            else:
                score = finite_or_none(value, f"{block.get('key')}.{scope}.{years[index]}")
                if score is not None and not 50 <= score <= 350:
                    raise RuntimeError(f"v1.38: WLE fuori intervallo di sicurezza: {block.get('key')} / {scope}")
        participation = data.get("participation")
        if participation is not None:
            if len(participation) != len(years):
                raise RuntimeError(f"v1.38: partecipazione disallineata {block.get('key')} / {scope}")
            for index, value in enumerate(participation):
                pct_or_none(value, f"{block.get('key')}.{scope}.participation.{years[index]}")
        coverage = data.get("coverage")
        if coverage is not None:
            if len(coverage) != len(years):
                raise RuntimeError(f"v1.38: copertura disallineata {block.get('key')} / {scope}")
            for index, value in enumerate(coverage):
                pct_or_none(value, f"{block.get('key')}.{scope}.coverage.{years[index]}")
        if require_levels:
            levels = data.get("levels", [])
            if len(levels) != len(years):
                raise RuntimeError(f"v1.38: livelli disallineati {block.get('key')} / {scope}")
            for index, level_values in enumerate(levels):
                if level_values is None:
                    if values[index] is not None:
                        raise RuntimeError(f"v1.38: livelli mancanti con traguardo presente {block.get('key')} / {scope}")
                    continue
                expected_count = len(block.get("levelLabels", []))
                if len(level_values) != expected_count:
                    raise RuntimeError(f"v1.38: numero livelli errato {block.get('key')} / {scope}")
                cleaned = [pct_or_none(value, f"{block.get('key')}.{scope}.level.{index}") for value in level_values]
                traguardo = finite_or_none(values[index], "traguardo")
                if traguardo is not None:
                    if block.get("subject") in ("Italiano", "Matematica"):
                        expected = sum(value or 0 for value in cleaned[2:])
                    else:
                        expected = cleaned[-1]
                    if expected is None or not math.isclose(traguardo, expected, abs_tol=0.03):
                        raise RuntimeError(
                            f"v1.38: traguardo/livelli non riconciliano {block.get('key')} / {scope} / {years[index]}"
                        )


def validate_snapshot(snapshot: dict) -> None:
    if snapshot.get("schemaVersion") != 1 or snapshot.get("release") != RELEASE:
        raise RuntimeError("v1.38: schema/release snapshot non canonico.")
    if snapshot.get("municipalityOrder") != TOWNS:
        raise RuntimeError("v1.38: ordine/perimetro comunale non canonico.")
    if set(snapshot.get("sources", {})) != {"results", "dispersionExcellence"}:
        raise RuntimeError("v1.38: blocco fonti inatteso.")
    for key, source in snapshot["sources"].items():
        for field in ("publisher", "page", "reference", "fileName", "sha256", "sizeBytes"):
            if not source.get(field):
                raise RuntimeError(f"v1.38: metadato fonte mancante {key}.{field}")
    selection = snapshot.get("selection", {})
    if selection.get("aggregation") != "Totale" or selection.get("municipalScale") != "Comune plesso":
        raise RuntimeError("v1.38: scala/aggregazione snapshot non conforme al gate.")
    if selection.get("versiliaAggregate", "").startswith("Non pubblicato") is False:
        raise RuntimeError("v1.38: contratto aggregato Versilia mancante.")
    if selection.get("missingCodes") != [888, 999]:
        raise RuntimeError("v1.38: codici missing inattesi.")

    results = snapshot.get("results", {})
    if results.get("metric") != "Punteggio_wle_medio" or results.get("unit") != "invalsi_score":
        raise RuntimeError("v1.38: metrica risultati non canonica.")
    result_views = results.get("views", [])
    if len(result_views) != 16:
        raise RuntimeError(f"v1.38: attese 16 letture risultati, trovate {len(result_views)}.")
    for view in result_views:
        validate_series_block(view, unit="invalsi_score")
        if any(value is None for value in view["tuscany"]["values"]) or any(value is None for value in view["italy"]["values"]):
            raise RuntimeError(f"v1.38: benchmark incompleto risultati {view['key']}")

    competence = snapshot.get("competence", {})
    if competence.get("metric") != "Perc_traguardi" or competence.get("unit") != "percent":
        raise RuntimeError("v1.38: metrica competenze non canonica.")
    competence_views = competence.get("views", [])
    if len(competence_views) != 12:
        raise RuntimeError(f"v1.38: attese 12 letture competenze, trovate {len(competence_views)}.")
    for view in competence_views:
        validate_series_block(view, unit="percent", require_levels=True)
        if any(value is None for value in view["tuscany"]["values"]) or any(value is None for value in view["italy"]["values"]):
            raise RuntimeError(f"v1.38: benchmark incompleto competenze {view['key']}")

    for block_key in ("implicitDispersion", "academicExcellence"):
        block = snapshot.get(block_key, {})
        if block.get("unit") != "percent" or len(block.get("views", [])) != 2:
            raise RuntimeError(f"v1.38: blocco {block_key} non canonico.")
        for view in block["views"]:
            validate_series_block(view, unit="percent")
            if any(value is None for value in view["tuscany"]["values"]) or any(value is None for value in view["italy"]["values"]):
                raise RuntimeError(f"v1.38: benchmark incompleto {block_key} {view['key']}")

    # Gate di copertura corrente approvato: assenze naturali dell'offerta scolastica.
    expected_results = {
        "g2-italiano": "5/7", "g2-matematica": "6/7",
        "g5-italiano": "6/7", "g5-matematica": "6/7",
        "g5-inglese-reading": "6/7", "g5-inglese-listening": "6/7",
        "g8-italiano": "4/7", "g8-matematica": "4/7",
        "g8-inglese-reading": "4/7", "g8-inglese-listening": "4/7",
        "g10-italiano": "4/7", "g10-matematica": "4/7",
        "g13-italiano": "4/7", "g13-matematica": "4/7",
        "g13-inglese-reading": "4/7", "g13-inglese-listening": "4/7",
    }
    actual = {view["key"]: view["currentCoverage"] for view in result_views}
    if actual != expected_results:
        raise RuntimeError(f"v1.38: copertura corrente risultati diversa dal gate: {actual}")
    for block in (competence, snapshot["implicitDispersion"], snapshot["academicExcellence"]):
        for view in block["views"]:
            if view["currentCoverage"] not in {"4/7", "6/7"}:
                raise RuntimeError(f"v1.38: copertura non approvata {view['key']}={view['currentCoverage']}")


def part_from_view(view: dict, data: dict, unit: str, *, competence: bool = False) -> dict:
    value = current(data.get("values", []))
    result = {
        "key": view["key"],
        "label": view["selectorLabel"],
        "value": value,
        "formatted": fmt(value, unit),
        "unit": unit,
        "grade": int(view["grade"]),
        "gradeLabel": view["gradeLabel"],
        "subject": view.get("subject"),
        "subjectLabel": view.get("subjectLabel"),
        "academicYear": view["latestYear"],
        "coverage": view["currentCoverage"],
    }
    if competence:
        levels = data.get("levels", [])
        latest_levels = levels[-1] if levels else None
        result["levels"] = [
            {"key": f"level-{index + 1}", "label": label, "value": finite_or_none(latest_levels[index], f"{view['key']}.level")}
            for index, label in enumerate(view["levelLabels"])
        ] if latest_levels is not None else None
        result["levelLabels"] = list(view["levelLabels"])
    return result


def series_map(views: list[dict], source_getter) -> dict:
    return {view["key"]: series(view["years"], source_getter(view).get("values", [])) for view in views}


def make_metric(snapshot: dict, ids: dict[str, dict], *, block_key: str, metric_key: str, label: str,
                short_label: str, description: str, unit: str, source_key: str,
                default_view: str, search_terms: list[str], competence: bool = False,
                definition_note: str = "") -> dict:
    block = snapshot[block_key]
    views = block["views"]
    by_key = {view["key"]: view for view in views}
    if default_view not in by_key:
        raise RuntimeError(f"v1.38: default view assente {metric_key}.{default_view}")

    rows = []
    for town in TOWNS:
        parts = [part_from_view(view, view["municipalities"][town], unit, competence=competence) for view in views]
        default_part = next(part for part in parts if part["key"] == default_view)
        row = {
            **identity(ids[town]),
            "value": default_part["value"],
            "formatted": default_part["formatted"],
            "parts": parts,
            "series": series(by_key[default_view]["years"], by_key[default_view]["municipalities"][town]["values"]),
            "seriesByView": series_map(views, lambda item, town=town: item["municipalities"][town]),
            "normalized": None,
            "benchmarkValue": None,
        }
        if competence:
            row["invalsiLevelsByView"] = {
                view["key"]: {
                    "labels": view["levelLabels"],
                    "values": view["municipalities"][town].get("levels", [])[-1] if view["municipalities"][town].get("levels") else None,
                    "academicYear": view["latestYear"],
                }
                for view in views
            }
        rows.append(row)

    def benchmark(name: str, selector: str) -> dict:
        parts = [part_from_view(view, view[selector], unit, competence=competence) for view in views]
        default_part = next(part for part in parts if part["key"] == default_view)
        data = {
            "value": default_part["value"],
            "formatted": default_part["formatted"],
            "label": name,
            "note": f"Benchmark ufficiale INVALSI {name}; stesso anno, grado, prova e aggregazione del dato comunale.",
            "parts": parts,
            "series": series(by_key[default_view]["years"], by_key[default_view][selector]["values"]),
            "seriesByView": series_map(views, lambda item, selector=selector: item[selector]),
        }
        if competence:
            data["invalsiLevelsByView"] = {
                view["key"]: {
                    "labels": view["levelLabels"],
                    "values": view[selector].get("levels", [])[-1] if view[selector].get("levels") else None,
                    "academicYear": view["latestYear"],
                }
                for view in views
            }
        return data

    source = snapshot["sources"][source_key]
    coverage_values = sorted(set(view["currentCoverage"] for view in views))
    method_coverage = " · ".join(coverage_values) + " secondo grado/prova; n.d. mantenuti senza stime."
    meta = {
        "key": metric_key,
        "theme": "istruzione",
        "label": label,
        "shortLabel": short_label,
        "description": description,
        "unit": unit,
        "year": "2024-25",
        "source": "INVALSI — Servizio Statistico",
        "polarity": "neutral",
        "compositeType": "invalsiProfile",
        "defaultView": default_view,
        "selectorLabel": "Classe e prova",
        "comparisonReference": "aggregate",
        "aggregateLabel": "Toscana",
        "comparisonLabel": "Toscana",
        "comparisonOverline": "Rispetto alla Toscana",
        "comparisonDifference": "absolute",
        "comparisonNote": "Scostamento numerico rispetto al benchmark regionale INVALSI; Italia è mostrata come secondo riferimento.",
        "allowPartialHistory": True,
        "academicYearSeries": True,
        "invalsiDetail": "competence" if competence else "standard",
        "searchTerms": search_terms,
    }
    if definition_note:
        meta["definitionNote"] = definition_note

    return {
        "meta": meta,
        "sourceUrl": source["page"],
        "rows": rows,
        "aggregate": benchmark("Toscana", "tuscany"),
        "nationalBenchmark": benchmark("Italia", "italy"),
        "normalizedAggregate": None,
        "viewDefinitions": [
            {
                "key": view["key"], "label": view["selectorLabel"], "grade": view["grade"],
                "gradeLabel": view["gradeLabel"], "subject": view.get("subject"),
                "subjectLabel": view.get("subjectLabel"), "academicYear": view["latestYear"],
                "coverage": view["currentCoverage"], "years": view["years"],
                **({"levelLabels": view["levelLabels"]} if competence else {}),
            }
            for view in views
        ],
        "method": {
            "type": "Open data di popolazione INVALSI, aggregazione territoriale ufficiale",
            "formula": "Valore comunale letto direttamente da 'Comune plesso' con aggregazione Totale. Toscana e Italia lette direttamente dallo stesso dataset; nessuna media tra scuole o Comuni.",
            "caveat": "Il Comune identifica la localizzazione del plesso scolastico, non la residenza dello studente. Le assenze ufficiali restano n.d.; la media Versilia non è calcolata perché manca il denominatore di prove valide/studenti per una ponderazione corretta.",
            "coverage": method_coverage,
        },
    }


def build_metrics(snapshot: dict, ids: dict[str, dict]) -> dict:
    return {
        "invalsiResults": make_metric(
            snapshot, ids, block_key="results", metric_key="invalsiResults",
            label="Risultati INVALSI", short_label="Risultati INVALSI",
            description="Punteggio medio WLE delle prove INVALSI nelle scuole localizzate nel Comune, con letture per classe e prova e benchmark ufficiali Toscana e Italia.",
            unit="invalsi_score", source_key="results", default_view="g5-italiano",
            search_terms=["INVALSI", "prove", "Italiano", "Matematica", "Inglese", "WLE", "apprendimenti", "competenze"],
        ),
        "invalsiCompetence": make_metric(
            snapshot, ids, block_key="competence", metric_key="invalsiCompetence",
            label="Livelli e traguardi di competenza", short_label="Livelli e traguardi",
            description="Quota di studenti che raggiunge il traguardo previsto da INVALSI e distribuzione nei livelli di competenza per le prove che prevedono una restituzione per livelli.",
            unit="percent", source_key="results", default_view="g5-inglese-reading",
            search_terms=["INVALSI", "livelli", "traguardi", "competenza", "A1", "A2", "B2", "Italiano", "Matematica", "Inglese"],
            competence=True,
            definition_note="Italiano e Matematica: livelli 1–5 dove previsti. Inglese: livelli QCER coerenti con il grado. Le categorie sono conservate senza reinterpretazioni.",
        ),
        "invalsiImplicitDispersion": make_metric(
            snapshot, ids, block_key="implicitDispersion", metric_key="invalsiImplicitDispersion",
            label="Dispersione scolastica implicita", short_label="Dispersione implicita",
            description="Percentuale INVALSI di dispersione scolastica implicita alla fine del primo e del secondo ciclo, secondo la definizione ufficiale della fonte.",
            unit="percent", source_key="dispersionExcellence", default_view="g8",
            search_terms=["INVALSI", "dispersione implicita", "competenze insufficienti", "grado 8", "grado 13"],
            definition_note="La categoria è quella pubblicata da INVALSI e non viene reinterpretata come abbandono scolastico amministrativo.",
        ),
        "invalsiAcademicExcellence": make_metric(
            snapshot, ids, block_key="academicExcellence", metric_key="invalsiAcademicExcellence",
            label="Eccellenza accademica", short_label="Eccellenze INVALSI",
            description="Percentuale INVALSI di studenti classificati nell'eccellenza accademica alla fine del primo e del secondo ciclo, secondo la definizione ufficiale della fonte.",
            unit="percent", source_key="dispersionExcellence", default_view="g8",
            search_terms=["INVALSI", "eccellenza", "eccellenze", "grado 8", "grado 13", "apprendimenti"],
            definition_note="La categoria è conservata esattamente secondo la definizione INVALSI.",
        ),
    }


def install_metrics(site: dict) -> None:
    theme = site.get("themes", {}).get("istruzione")
    if not theme:
        raise RuntimeError("v1.38: tema Istruzione assente.")
    for section in theme.get("sections", []):
        section["metrics"] = [key for key in section.get("metrics", []) if key not in NEW_KEYS]
    sections = theme.setdefault("sections", [])
    sections[:] = [section for section in sections if section.get("key") != "invalsi"]
    sections.append({
        "key": "invalsi",
        "label": "Apprendimenti e competenze",
        "description": "Prove INVALSI delle scuole localizzate nei Comuni: risultati, livelli, dispersione implicita ed eccellenze.",
        "metrics": list(NEW_KEYS),
    })
    theme["metrics"] = [key for section in sections for key in section.get("metrics", [])]


def patch_registry(registry: dict, snapshot: dict, metric_count: int, external_count: int) -> None:
    registry["expectedMetricCount"] = metric_count
    registry["expectedExternalMetricCount"] = external_count
    registry["expectedInlineMetricCount"] = metric_count - external_count
    profiles = registry.setdefault("sourceProfiles", {})
    profiles[SOURCE_RESULTS] = {
        "publisher": "INVALSI",
        "frequency": "annual",
        "frequencyLabel": "Annuale",
        "expectedRelease": "Dopo la pubblicazione annuale degli open data territoriali INVALSI",
        "acquisitionMethod": "CSV open di popolazione; scala Comune plesso, aggregazione Totale; snapshot versionato e build offline.",
        "licenseName": "Licenza indicata dal Servizio Statistico INVALSI",
        "licenseUrl": snapshot["sources"]["results"]["page"],
    }
    profiles[SOURCE_DISPERSION] = {
        "publisher": "INVALSI",
        "frequency": "annual",
        "frequencyLabel": "Annuale",
        "expectedRelease": "Dopo la pubblicazione annuale degli open data territoriali INVALSI",
        "acquisitionMethod": "CSV open di popolazione su dispersione implicita ed eccellenza; snapshot versionato e build offline.",
        "licenseName": "Licenza indicata dal Servizio Statistico INVALSI",
        "licenseUrl": snapshot["sources"]["dispersionExcellence"]["page"],
    }
    mapping = registry.setdefault("sourceProfileByUrl", {})
    mapping[snapshot["sources"]["results"]["page"]] = SOURCE_RESULTS
    mapping[snapshot["sources"]["dispersionExcellence"]["page"]] = SOURCE_DISPERSION
    overrides = registry.setdefault("metricOverrides", {})
    overrides["invalsiResults"] = {"profile": SOURCE_RESULTS}
    overrides["invalsiCompetence"] = {"profile": SOURCE_RESULTS}
    overrides["invalsiImplicitDispersion"] = {"profile": SOURCE_DISPERSION}
    overrides["invalsiAcademicExcellence"] = {"profile": SOURCE_DISPERSION}


def main() -> None:
    if not SNAPSHOT.exists():
        raise RuntimeError("v1.38: snapshot ufficiale invalsi-v138-official.json mancante.")
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    validate_snapshot(snapshot)

    site = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    metrics = site.setdefault("metrics", {})
    if len(metrics) != EXPECTED_BEFORE:
        raise RuntimeError(f"v1.38: baseline inattesa: {len(metrics)} indicatori, attesi {EXPECTED_BEFORE}.")
    if set(NEW_KEYS) & set(metrics):
        raise RuntimeError("v1.38: una o piu' metriche INVALSI esistono gia' prima del materializzatore.")

    ids = identities(site)
    built = build_metrics(snapshot, ids)
    if list(built) != NEW_KEYS:
        raise RuntimeError("v1.38: perimetro metriche costruite diverso dal contratto.")
    metrics.update(built)
    install_metrics(site)

    if len(metrics) != EXPECTED_AFTER:
        raise RuntimeError(f"v1.38: catalogo finale {len(metrics)}, attesi {EXPECTED_AFTER}.")
    if len(metrics) != len(set(metrics)):
        raise RuntimeError("v1.38: ID indicatori duplicati.")

    # Contratto benchmark: nessuna metrica INVALSI può esporre una media Versilia.
    for key in NEW_KEYS:
        metric = metrics[key]
        if metric.get("aggregate", {}).get("label") != "Toscana":
            raise RuntimeError(f"v1.38: benchmark primario non Toscana: {key}")
        if metric.get("nationalBenchmark", {}).get("label") != "Italia":
            raise RuntimeError(f"v1.38: benchmark nazionale mancante: {key}")
        if metric["method"]["formula"].lower().find("nessuna media") < 0:
            raise RuntimeError(f"v1.38: contratto no-media mancante: {key}")

    site.update({"version": RELEASE, "release_version": "1.38.0", "updated": "13 settembre 2026"})
    SITE_DATA.write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    external = sum(m.get("dataStorage", {}).get("type") == "external-climate" for m in metrics.values())
    patch_registry(registry, snapshot, len(metrics), external)
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("v1.38.0 materializzata: 207 indicatori; 4 indicatori INVALSI con Toscana/Italia e nessuna media Versilia.")


if __name__ == "__main__":
    main()
