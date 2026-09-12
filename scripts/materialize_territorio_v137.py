#!/usr/bin/env python3
"""Materializza la v1.37.0: suolo, aree protette, reticolo e grafo viario.

Il materializzatore e' intenzionalmente offline e fail-closed: usa esclusivamente
lo snapshot ufficiale versionato in data/source-snapshots/territorio-v137-official.json.
Nessun dato viene scaricato durante la build pubblica.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "territorio-v137-official.json"

RELEASE = "v1.37.0"
EXPECTED_BEFORE = 202
EXPECTED_AFTER = 203
TOWNS = [
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
]
PATCHED_KEYS = {
    "landUse",
    "landUseChange",
    "protectedNaturalAreas",
    "managedReticulumLength",
}
NEW_KEYS = {"roadNetworkProfile"}
EXPECTED_KEYS = PATCHED_KEYS | NEW_KEYS


def finite(value, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"v1.37: valore non numerico: {label}") from exc
    if not math.isfinite(number):
        raise RuntimeError(f"v1.37: valore non finito: {label}")
    return number


def nonnegative(value, label: str) -> float:
    number = finite(value, label)
    if number < 0:
        raise RuntimeError(f"v1.37: valore negativo non ammesso: {label}={number}")
    return number


def close(actual: float, expected: float, label: str, *, abs_tol: float = 1e-6, rel_tol: float = 1e-7) -> None:
    if not math.isclose(actual, expected, rel_tol=rel_tol, abs_tol=abs_tol):
        raise RuntimeError(f"v1.37: controllo fallito {label}: {actual} != {expected}")


def fmt(value: float, digits: int, suffix: str = "") -> str:
    return f"{value:.{digits}f}".replace(".", ",") + suffix


def identities(site: dict) -> dict[str, dict]:
    population = site.get("metrics", {}).get("population", {})
    rows = {row.get("town"): row for row in population.get("rows", [])}
    if set(rows) != set(TOWNS):
        raise RuntimeError("v1.37: population non fornisce identita' 7/7.")
    return rows


def identity(row: dict) -> dict:
    return {"town": row["town"], "code": row["code"], "slug": row["slug"]}


def validate_snapshot(snapshot: dict) -> None:
    if snapshot.get("schemaVersion") != 1 or snapshot.get("release") != RELEASE:
        raise RuntimeError("v1.37: schema/release snapshot non canonico.")
    if snapshot.get("municipalityOrder") != TOWNS:
        raise RuntimeError("v1.37: ordine/perimetro comunale non canonico.")

    required_sources = {"ispraSoil", "regioneProtectedAreas", "regioneHydrography", "regioneIterNet"}
    if set(snapshot.get("sources", {})) != required_sources:
        raise RuntimeError("v1.37: blocco fonti incompleto o inatteso.")
    for source_key, source in snapshot["sources"].items():
        if not source.get("publisher") or not source.get("page") or not source.get("reference"):
            raise RuntimeError(f"v1.37: metadati fonte incompleti: {source_key}")

    soil = snapshot.get("landUse", {})
    years = soil.get("years")
    if years != [2006, 2012, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]:
        raise RuntimeError("v1.37: annualita' ISPRA suolo inattese.")
    if list(soil.get("municipalities", {})) != TOWNS:
        raise RuntimeError("v1.37: stock suolo non 7/7.")
    for town in TOWNS:
        item = soil["municipalities"][town]
        area_ha = nonnegative(item.get("municipalAreaHa"), f"{town}.municipalAreaHa")
        if area_ha <= 0:
            raise RuntimeError(f"v1.37: superficie comunale nulla: {town}")
        rows = item.get("rows", {})
        if list(map(int, rows)) != years:
            raise RuntimeError(f"v1.37: serie stock incompleta: {town}")
        for year in years:
            row = rows[str(year)]
            consumed_ha = nonnegative(row.get("consumedHa"), f"{town}.{year}.consumedHa")
            pct = nonnegative(row.get("consumedPct"), f"{town}.{year}.consumedPct")
            close(pct, consumed_ha / area_ha * 100, f"{town}.{year}.consumedPct", abs_tol=0.03)
            sqm_raw = row.get("sqmPerResident")
            if year >= 2019:
                sqm = nonnegative(sqm_raw, f"{town}.{year}.sqmPerResident")
                if sqm <= 0:
                    raise RuntimeError(f"v1.37: m2/residente non valido: {town} {year}")
            elif sqm_raw is not None:
                raise RuntimeError(f"v1.37: m2/residente inatteso prima del 2019: {town} {year}")

    changes = snapshot.get("landUseChange", {})
    change_years = changes.get("years")
    if change_years != [2012, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]:
        raise RuntimeError("v1.37: annualita' ISPRA variazione inattese.")
    if list(changes.get("municipalities", {})) != TOWNS:
        raise RuntimeError("v1.37: variazione suolo non 7/7.")
    for town in TOWNS:
        rows = changes["municipalities"][town].get("rows", {})
        if list(map(int, rows)) != change_years:
            raise RuntimeError(f"v1.37: serie variazione incompleta: {town}")
        for year in change_years:
            row = rows[str(year)]
            nonnegative(row.get("grossHa"), f"{town}.{year}.grossHa")
            net = finite(row.get("netHa"), f"{town}.{year}.netHa")
            gross = float(row["grossHa"])
            if net > gross + 1e-6:
                raise RuntimeError(f"v1.37: netto > lordo: {town} {year}")

    protected = snapshot.get("protectedNaturalAreas", {})
    expected_categories = ["parksReserves", "anpil", "natura2000", "zsc", "zps", "ramsar"]
    if protected.get("categoryOrder") != expected_categories:
        raise RuntimeError("v1.37: categorie aree protette inattese.")
    if list(protected.get("municipalities", {})) != TOWNS:
        raise RuntimeError("v1.37: aree protette non 7/7.")
    for town in TOWNS:
        item = protected["municipalities"][town]
        area = nonnegative(item.get("municipalAreaHa"), f"{town}.protected.municipalAreaHa")
        total = nonnegative(item.get("totalUnionHa"), f"{town}.protected.totalUnionHa")
        if total > area + 1e-5:
            raise RuntimeError(f"v1.37: unione protetta > superficie comunale: {town}")
        categories = item.get("categoriesHa", {})
        if list(categories) != expected_categories:
            raise RuntimeError(f"v1.37: categorie protette incomplete: {town}")
        for key in expected_categories:
            value = nonnegative(categories[key], f"{town}.protected.{key}")
            if value > area + 1e-5:
                raise RuntimeError(f"v1.37: categoria protetta > superficie comunale: {town}/{key}")

    reticulum = snapshot.get("reticulum", {})
    if list(reticulum.get("municipalities", {})) != TOWNS:
        raise RuntimeError("v1.37: reticolo non 7/7.")
    for town in TOWNS:
        item = reticulum["municipalities"][town]
        area = nonnegative(item.get("municipalAreaKm2"), f"{town}.reticulum.area")
        full_km = nonnegative(item.get("fullNetworkKm"), f"{town}.reticulum.full")
        managed_km = nonnegative(item.get("managedNetworkKm"), f"{town}.reticulum.managed")
        if area <= 0 or full_km < managed_km - 1e-6:
            raise RuntimeError(f"v1.37: reticolo incoerente: {town}")
        close(finite(item.get("fullNetworkDensity"), f"{town}.reticulum.density"), full_km / area,
              f"{town}.reticulum.density", abs_tol=1e-6)

    roads = snapshot.get("roadNetworkProfile", {})
    if list(roads.get("municipalities", {})) != TOWNS:
        raise RuntimeError("v1.37: grafo viario non 7/7.")
    for town in TOWNS:
        item = roads["municipalities"][town]
        area = nonnegative(item.get("municipalAreaKm2"), f"{town}.roads.area")
        graph = nonnegative(item.get("graphKm"), f"{town}.roads.graph")
        if area <= 0:
            raise RuntimeError(f"v1.37: area viaria non valida: {town}")
        close(finite(item.get("graphDensity"), f"{town}.roads.density"), graph / area,
              f"{town}.roads.density", abs_tol=1e-6)

    # Gli aggregati Versilia devono essere prodotti sul perimetro dissolto, non come
    # media delle percentuali o somma cieca delle geometrie comunali.
    for block, fields in (
        (protected, ("municipalAreaHa", "totalUnionHa")),
        (reticulum, ("unionAreaKm2", "fullNetworkKm", "managedNetworkKm")),
        (roads, ("unionAreaKm2", "graphKm")),
    ):
        versilia = block.get("versilia")
        if not isinstance(versilia, dict):
            raise RuntimeError("v1.37: aggregato Versilia mancante.")
        for field in fields:
            nonnegative(versilia.get(field), f"versilia.{field}")

    close(reticulum["versilia"]["fullNetworkDensity"],
          reticulum["versilia"]["fullNetworkKm"] / reticulum["versilia"]["unionAreaKm2"],
          "Versilia.reticulum.fullNetworkDensity")
    close(roads["versilia"]["graphDensity"],
          roads["versilia"]["graphKm"] / roads["versilia"]["unionAreaKm2"],
          "Versilia.roads.graphDensity")


def make_land_use(snapshot: dict, ids: dict[str, dict]) -> dict:
    block = snapshot["landUse"]
    years = block["years"]
    sqm_years = [year for year in years if year >= 2019]
    rows = []
    for town in TOWNS:
        item = block["municipalities"][town]
        latest = item["rows"]["2024"]
        rows.append({
            **identity(ids[town]),
            "value": float(latest["consumedPct"]),
            "formatted": fmt(float(latest["consumedPct"]), 2, "%"),
            "parts": [
                {"key": "percent", "label": "% territorio", "value": float(latest["consumedPct"]), "unit": "percent"},
                {"key": "hectares", "label": "Suolo consumato", "value": float(latest["consumedHa"]), "unit": "ha"},
                {"key": "sqmPerResident", "label": "Per residente", "value": float(latest["sqmPerResident"]), "unit": "sqm_per_resident"},
            ],
            "seriesByView": {
                "percent": {"years": years, "values": [float(item["rows"][str(y)]["consumedPct"]) for y in years]},
                "hectares": {"years": years, "values": [float(item["rows"][str(y)]["consumedHa"]) for y in years]},
                "sqmPerResident": {"years": sqm_years, "values": [float(item["rows"][str(y)]["sqmPerResident"]) for y in sqm_years]},
            },
            "municipalAreaHa": float(item["municipalAreaHa"]),
            "series": None,
            "normalized": None,
            "benchmarkValue": None,
        })
    latest = block["versilia"]["rows"]["2024"]
    return {
        "meta": {
            "key": "landUse", "theme": "ambiente", "label": "Suolo consumato", "shortLabel": "Suolo consumato",
            "description": "Suolo consumato ISPRA: stock in ettari, quota della superficie territoriale e metri quadrati per residente. Non coincide con le superfici artificializzate UCS.",
            "unit": "percent", "year": "2006, 2012, 2015–2024", "source": "ISPRA — Consumo di suolo",
            "polarity": "neutral", "compositeType": "soilStockProfile", "defaultView": "percent",
            "searchTerms": ["consumo di suolo", "suolo consumato", "ISPRA", "ettari", "m2 per residente"],
        },
        "sourceUrl": snapshot["sources"]["ispraSoil"]["page"], "years": years, "rows": rows,
        "aggregate": {
            "value": float(latest["consumedPct"]), "label": "Versilia · suolo consumato",
            "note": "Quota Versilia = Σ suolo consumato / Σ superficie territoriale; il valore per residente usa Σ m² consumati / Σ residenti.",
            "parts": [
                {"key": "percent", "label": "% territorio", "value": float(latest["consumedPct"]), "unit": "percent"},
                {"key": "hectares", "label": "Suolo consumato", "value": float(latest["consumedHa"]), "unit": "ha"},
                {"key": "sqmPerResident", "label": "Per residente", "value": float(latest["sqmPerResident"]), "unit": "sqm_per_resident"},
            ],
            "seriesByView": {
                "percent": {"years": years, "values": [float(block["versilia"]["rows"][str(y)]["consumedPct"]) for y in years]},
                "hectares": {"years": years, "values": [float(block["versilia"]["rows"][str(y)]["consumedHa"]) for y in years]},
                "sqmPerResident": {"years": sqm_years, "values": [float(block["versilia"]["rows"][str(y)]["sqmPerResident"]) for y in sqm_years]},
            },
        },
        "normalizedAggregate": None,
        "method": {"type": "Dato ufficiale ISPRA", "formula": "Stock: ha; quota: ha consumati / ha territoriali × 100; pro capite: m² consumati / residenti.", "caveat": "Stock e quota seguono le annualita' ISPRA 2006, 2012 e 2015–2024. Il dato m²/residente è mostrato nel periodo 2019–2024, sovrapposto alla serie demografica canonica disponibile; nessuna interpolazione.", "coverage": "7/7"},
    }


def make_land_use_change(snapshot: dict, ids: dict[str, dict]) -> dict:
    block = snapshot["landUseChange"]
    years = block["years"]
    rows = []
    for town in TOWNS:
        item = block["municipalities"][town]
        latest = item["rows"]["2024"]
        rows.append({
            **identity(ids[town]), "value": float(latest["netHa"]), "formatted": fmt(float(latest["netHa"]), 2, " ha"),
            "parts": [
                {"key": "gross", "label": "Consumo lordo", "value": float(latest["grossHa"]), "unit": "ha"},
                {"key": "net", "label": "Consumo netto", "value": float(latest["netHa"]), "unit": "ha"},
            ],
            "seriesByView": {
                "gross": {"years": years, "values": [float(item["rows"][str(y)]["grossHa"]) for y in years]},
                "net": {"years": years, "values": [float(item["rows"][str(y)]["netHa"]) for y in years]},
            },
            "series": None, "normalized": None, "benchmarkValue": None,
        })
    latest = block["versilia"]["rows"]["2024"]
    return {
        "meta": {
            "key": "landUseChange", "theme": "ambiente", "label": "Consumo di suolo annuale", "shortLabel": "Consumo annuale",
            "description": "Variazione annuale ISPRA distinta tra consumo di suolo lordo e netto. Il netto può essere negativo per ripristini o riclassificazioni.",
            "unit": "ha", "year": "2012, 2015–2024", "source": "ISPRA — Consumo di suolo",
            "polarity": "neutral", "compositeType": "soilChangeProfile", "defaultView": "net",
            "searchTerms": ["consumo di suolo lordo", "consumo di suolo netto", "ISPRA", "variazione annuale"],
        },
        "sourceUrl": snapshot["sources"]["ispraSoil"]["page"], "years": years, "rows": rows,
        "aggregate": {
            "value": float(latest["netHa"]), "label": "Versilia · consumo netto 2024",
            "note": "Aggregato Versilia ottenuto sommando gli ettari dei sette Comuni per la stessa annualita' e la stessa definizione ISPRA.",
            "parts": [
                {"key": "gross", "label": "Consumo lordo", "value": float(latest["grossHa"]), "unit": "ha"},
                {"key": "net", "label": "Consumo netto", "value": float(latest["netHa"]), "unit": "ha"},
            ],
            "seriesByView": {
                "gross": {"years": years, "values": [float(block["versilia"]["rows"][str(y)]["grossHa"]) for y in years]},
                "net": {"years": years, "values": [float(block["versilia"]["rows"][str(y)]["netHa"]) for y in years]},
            },
        },
        "normalizedAggregate": None,
        "method": {"type": "Dato ufficiale ISPRA", "formula": "Versilia = Σ ettari comunali per annualita' e vista (lordo/netto).", "caveat": "Lordo e netto sono grandezze diverse; i valori negativi del netto sono ammessi e non sono trasformati in zero.", "coverage": "7/7"},
    }


def make_protected(snapshot: dict, ids: dict[str, dict]) -> dict:
    block = snapshot["protectedNaturalAreas"]
    categories = block["categoryOrder"]
    labels = block["categoryLabels"]
    rows = []
    for town in TOWNS:
        item = block["municipalities"][town]
        pct = float(item["totalUnionHa"]) / float(item["municipalAreaHa"]) * 100
        parts = [{"key": "total", "label": "Totale protetto (unione)", "value": pct, "unit": "percent", "ha": float(item["totalUnionHa"])}]
        parts += [{"key": key, "label": labels[key], "value": float(item["categoriesHa"][key]) / float(item["municipalAreaHa"]) * 100, "unit": "percent", "ha": float(item["categoriesHa"][key])} for key in categories]
        rows.append({**identity(ids[town]), "value": pct, "formatted": fmt(pct, 1, "%"), "parts": parts, "municipalAreaHa": float(item["municipalAreaHa"]), "series": None, "normalized": None, "benchmarkValue": None})
    versilia = block["versilia"]
    pct = float(versilia["totalUnionHa"]) / float(versilia["municipalAreaHa"]) * 100
    parts = [{"key": "total", "label": "Totale protetto (unione)", "value": pct, "unit": "percent", "ha": float(versilia["totalUnionHa"])}]
    parts += [{"key": key, "label": labels[key], "value": float(versilia["categoriesHa"][key]) / float(versilia["municipalAreaHa"]) * 100, "unit": "percent", "ha": float(versilia["categoriesHa"][key])} for key in categories]
    return {
        "meta": {"key": "protectedNaturalAreas", "theme": "ambiente", "label": "Territorio in aree naturali protette", "shortLabel": "Aree protette", "description": "Superficie ricadente nelle aree protette e nei siti Natura 2000 della Regione Toscana. Il totale e' l'unione geometrica delle tutele e non la somma delle categorie sovrapposte.", "unit": "percent", "year": block["referenceLabel"], "source": "Regione Toscana — Aree protette / Natura 2000 / Ramsar", "polarity": "neutral", "compositeType": "protectedAreasProfile", "defaultView": "total", "searchTerms": ["aree protette", "parchi", "riserve", "ANPIL", "Natura 2000", "ZSC", "ZPS", "Ramsar"]},
        "sourceUrl": snapshot["sources"]["regioneProtectedAreas"]["page"], "categoryDefinitions": [{"key": key, "label": labels[key]} for key in categories], "rows": rows,
        "aggregate": {"value": pct, "label": "Versilia · territorio protetto", "note": "Totale su geometrie dissolte: le sovrapposizioni tra categorie sono conteggiate una sola volta.", "parts": parts},
        "normalizedAggregate": None,
        "method": {"type": "Elaborazione GIS su perimetri ufficiali Regione Toscana", "formula": "Totale = area(unione geometrica delle tutele ∩ Comune). Quota = totale / superficie comunale × 100.", "caveat": "Le categorie possono sovrapporsi e non vanno sommate. I riferimenti temporali dei layer restano distinti e sono documentati nello snapshot.", "coverage": "7/7"},
    }


def make_reticulum(snapshot: dict, ids: dict[str, dict]) -> dict:
    block = snapshot["reticulum"]
    rows = []
    for town in TOWNS:
        item = block["municipalities"][town]
        rows.append({
            **identity(ids[town]), "value": float(item["fullNetworkKm"]), "formatted": fmt(float(item["fullNetworkKm"]), 1, " km"),
            "parts": [
                {"key": "full", "label": "Reticolo complessivo", "value": float(item["fullNetworkKm"]), "unit": "km"},
                {"key": "managed", "label": "Reticolo in gestione", "value": float(item["managedNetworkKm"]), "unit": "km"},
                {"key": "density", "label": "Densita' del reticolo", "value": float(item["fullNetworkDensity"]), "unit": "km_per_km2"},
            ],
            "municipalAreaKm2": float(item["municipalAreaKm2"]), "series": None, "normalized": None, "benchmarkValue": None,
        })
    versilia = block["versilia"]
    return {
        "meta": {"key": "managedReticulumLength", "theme": "ambiente", "label": "Reticolo idrografico", "shortLabel": "Reticolo idrografico", "description": "Lunghezza del reticolo idrografico regionale nel territorio comunale, con distinzione del reticolo attribuito alla gestione del Consorzio 1 Toscana Nord e densita' lineare.", "unit": "km", "year": block["referenceLabel"], "source": "Regione Toscana — reticolo idrografico e di gestione", "polarity": "neutral", "compositeType": "hydroNetworkProfile", "defaultView": "full", "searchTerms": ["reticolo idrografico", "Toscana Nord", "bonifica", "densita' reticolo", "corsi d'acqua"]},
        "sourceUrl": snapshot["sources"]["regioneHydrography"]["page"], "rows": rows,
        "aggregate": {"value": float(versilia["fullNetworkKm"]), "label": "Versilia · reticolo complessivo", "note": "Il totale del reticolo e' ricalcolato sul perimetro dissolto dei sette Comuni per evitare doppi conteggi sulle linee di confine.", "parts": [
            {"key": "full", "label": "Reticolo complessivo", "value": float(versilia["fullNetworkKm"]), "unit": "km"},
            {"key": "managed", "label": "Reticolo in gestione", "value": float(versilia["managedNetworkKm"]), "unit": "km"},
            {"key": "density", "label": "Densita' del reticolo", "value": float(versilia["fullNetworkDensity"]), "unit": "km_per_km2"},
        ]},
        "normalizedAggregate": None,
        "method": {"type": "Elaborazione GIS su reticolo ufficiale Regione Toscana", "formula": "Lunghezza dopo clip sul Comune; densita' = km reticolo complessivo / km² comunali. Versilia su unione dissolta dei sette Comuni.", "caveat": "Il reticolo e' una rete lineare: non rappresenta la superficie occupata da acqua.", "coverage": "7/7"},
    }


def make_roads(snapshot: dict, ids: dict[str, dict]) -> dict:
    block = snapshot["roadNetworkProfile"]
    rows = []
    for town in TOWNS:
        item = block["municipalities"][town]
        rows.append({
            **identity(ids[town]), "value": float(item["graphKm"]), "formatted": fmt(float(item["graphKm"]), 1, " km"),
            "parts": [
                {"key": "length", "label": "Lunghezza del grafo", "value": float(item["graphKm"]), "unit": "km"},
                {"key": "density", "label": "Densita' del grafo", "value": float(item["graphDensity"]), "unit": "km_per_km2"},
            ],
            "municipalAreaKm2": float(item["municipalAreaKm2"]), "series": None, "normalized": None, "benchmarkValue": None,
        })
    versilia = block["versilia"]
    return {
        "meta": {"key": "roadNetworkProfile", "theme": "ambiente", "label": "Grafo viario Iter.Net", "shortLabel": "Grafo viario", "description": "Lunghezza degli elementi stradali del grafo Iter.Net della Regione Toscana e densita' rispetto alla superficie territoriale.", "unit": "km", "year": "2022", "source": "Regione Toscana — Iter.Net 4.48", "polarity": "neutral", "compositeType": "roadNetworkProfile", "defaultView": "length", "searchTerms": ["strade", "grafo viario", "Iter.Net", "rete stradale", "densita' stradale"]},
        "sourceUrl": snapshot["sources"]["regioneIterNet"]["page"], "rows": rows,
        "aggregate": {"value": float(versilia["graphKm"]), "label": "Versilia · grafo viario Iter.Net", "note": "Lunghezza ricalcolata sul perimetro dissolto dei sette Comuni; la densita' usa la superficie della stessa unione.", "parts": [
            {"key": "length", "label": "Lunghezza del grafo", "value": float(versilia["graphKm"]), "unit": "km"},
            {"key": "density", "label": "Densita' del grafo", "value": float(versilia["graphDensity"]), "unit": "km_per_km2"},
        ]},
        "normalizedAggregate": None,
        "method": {"type": "Elaborazione GIS su grafo Iter.Net 4.48", "formula": "Lunghezza degli elementi stradali dopo clip; densita' = km grafo / km². Versilia su unione dissolta.", "caveat": "Iter.Net rappresenta gli assi degli elementi stradali e puo' distinguere le carreggiate; il valore non va interpretato come chilometri di strade univoche al centrolinea.", "coverage": "7/7"},
    }


def install_road_metric(site: dict) -> None:
    environment = site.get("themes", {}).get("ambiente")
    if not environment:
        raise RuntimeError("v1.37: tema Ambiente assente.")
    sections = environment.get("sections", [])
    profile = next((s for s in sections if s.get("key") == "profilo-territoriale"), None)
    if not profile:
        raise RuntimeError("v1.37: sezione profilo-territoriale assente.")
    metrics = [key for key in profile.get("metrics", []) if key != "roadNetworkProfile"]
    anchor = metrics.index("statisticalCoastlineLength") + 1 if "statisticalCoastlineLength" in metrics else len(metrics)
    metrics.insert(anchor, "roadNetworkProfile")
    profile["metrics"] = metrics
    environment["metrics"] = [key for section in sections for key in section.get("metrics", [])]


def patch_registry(registry: dict, snapshot: dict, metric_count: int, external_count: int) -> None:
    registry["expectedMetricCount"] = metric_count
    registry["expectedExternalMetricCount"] = external_count
    registry["expectedInlineMetricCount"] = metric_count - external_count
    profiles = registry.setdefault("sourceProfiles", {})
    profiles["ispra-consumo-suolo-2024"] = {
        "publisher": "ISPRA", "frequency": "annual", "frequencyLabel": "Annuale",
        "expectedRelease": "Secondo la pubblicazione annuale ISPRA", "acquisitionMethod": "Estratto comunale ufficiale ISPRA; snapshot versionato, nessuna interpolazione.",
        "licenseName": "Condizioni di riuso ISPRA", "licenseUrl": snapshot["sources"]["ispraSoil"]["page"],
    }
    profiles["regione-toscana-aree-protette-v137"] = {
        "publisher": "Regione Toscana", "frequency": "irregular", "frequencyLabel": "Secondo gli aggiornamenti dei perimetri ufficiali",
        "expectedRelease": "Secondo gli atti e archivi geografici regionali", "acquisitionMethod": "Intersezione GIS dei perimetri ufficiali; totale su unione geometrica dissolta.",
        "licenseName": "Open data Regione Toscana", "licenseUrl": snapshot["sources"]["regioneProtectedAreas"]["page"],
    }
    profiles["regione-toscana-reticolo-v137"] = {
        "publisher": "Regione Toscana", "frequency": "irregular", "frequencyLabel": "Secondo gli aggiornamenti del reticolo e degli atti di gestione",
        "expectedRelease": "Secondo la fonte", "acquisitionMethod": "Clip GIS del reticolo sul perimetro comunale e versiliese dissolto.",
        "licenseName": "Open data Regione Toscana", "licenseUrl": snapshot["sources"]["regioneHydrography"]["page"],
    }
    profiles["regione-toscana-iternet-448"] = {
        "publisher": "Regione Toscana", "frequency": "irregular", "frequencyLabel": "Snapshot ufficiale Iter.Net 4.48",
        "expectedRelease": "Dataset revisionato il 9 giugno 2022", "acquisitionMethod": "Clip GIS degli elementi stradali Iter.Net 4.48 sul perimetro comunale e versiliese dissolto.",
        "licenseName": "Open data Regione Toscana", "licenseUrl": snapshot["sources"]["regioneIterNet"]["page"],
    }
    mapping = registry.setdefault("sourceProfileByUrl", {})
    mapping[snapshot["sources"]["ispraSoil"]["page"]] = "ispra-consumo-suolo-2024"
    mapping[snapshot["sources"]["regioneProtectedAreas"]["page"]] = "regione-toscana-aree-protette-v137"
    mapping[snapshot["sources"]["regioneHydrography"]["page"]] = "regione-toscana-reticolo-v137"
    mapping[snapshot["sources"]["regioneIterNet"]["page"]] = "regione-toscana-iternet-448"
    overrides = registry.setdefault("metricOverrides", {})
    overrides["landUse"] = {"profile": "ispra-consumo-suolo-2024"}
    overrides["landUseChange"] = {"profile": "ispra-consumo-suolo-2024"}
    overrides["protectedNaturalAreas"] = {"profile": "regione-toscana-aree-protette-v137"}
    overrides["managedReticulumLength"] = {"profile": "regione-toscana-reticolo-v137"}
    overrides["roadNetworkProfile"] = {"profile": "regione-toscana-iternet-448"}


def main() -> None:
    if not SNAPSHOT.exists():
        raise RuntimeError("v1.37: snapshot ufficiale territorio-v137-official.json mancante.")
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    validate_snapshot(snapshot)
    site = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    metrics = site.setdefault("metrics", {})
    if len(metrics) != EXPECTED_BEFORE:
        raise RuntimeError(f"v1.37: baseline canonica inattesa: {len(metrics)} indicatori, attesi {EXPECTED_BEFORE}.")
    if not PATCHED_KEYS.issubset(metrics):
        raise RuntimeError(f"v1.37: metriche da migliorare mancanti: {sorted(PATCHED_KEYS - set(metrics))}")
    if NEW_KEYS & set(metrics):
        raise RuntimeError("v1.37: roadNetworkProfile esiste gia' prima del materializzatore.")

    ids = identities(site)
    built = {
        "landUse": make_land_use(snapshot, ids),
        "landUseChange": make_land_use_change(snapshot, ids),
        "protectedNaturalAreas": make_protected(snapshot, ids),
        "managedReticulumLength": make_reticulum(snapshot, ids),
        "roadNetworkProfile": make_roads(snapshot, ids),
    }
    if set(built) != EXPECTED_KEYS:
        raise RuntimeError("v1.37: perimetro metriche costruite diverso dal contratto approvato.")
    metrics.update(built)
    install_road_metric(site)
    if len(metrics) != EXPECTED_AFTER:
        raise RuntimeError(f"v1.37: catalogo finale {len(metrics)}, attesi {EXPECTED_AFTER}.")
    if len(metrics) != len(set(metrics)):
        raise RuntimeError("v1.37: ID indicatori duplicati.")

    site.update({"version": RELEASE, "release_version": "1.37.0", "updated": "12 settembre 2026"})
    SITE_DATA.write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    external = sum(m.get("dataStorage", {}).get("type") == "external-climate" for m in metrics.values())
    patch_registry(registry, snapshot, len(metrics), external)
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("v1.37.0 materializzata: 203 indicatori; 4 metriche territoriali migliorate + roadNetworkProfile.")


if __name__ == "__main__":
    main()
