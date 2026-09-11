#!/usr/bin/env python3
"""Materializza la v1.36.0: classificazioni territoriali, costa Istat e UCS 2007–2019."""
from __future__ import annotations

import json
import runpy
from collections import Counter
from pathlib import Path

from territorio_ucs_config import (
    DETAIL_KEYS, EXPECTED_BASE_METRIC_COUNT, EXPECTED_RELEASE_METRIC_COUNT,
    LAND_COVER_SECTION_KEY, MACRO_KEYS, MACRO_SUM_TOLERANCE_PCT,
    MUNICIPALITY_ORDER, NEW_METRIC_KEYS, PROFILE_SECTION_KEY, SOURCE_PATH, YEARS,
)

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data/site-data.json"
REGISTRY = ROOT / "data/source-registry.json"
SOURCE = ROOT / SOURCE_PATH
RUNTIME_PATCH = ROOT / "scripts/patch_territorio_ucs_runtime.py"

ISTAT_CLASS_URL = "https://www.istat.it/comunicato-stampa/geografie-funzionali-per-lanalisi-territoriale/"
ISTAT_GEO_URL = "https://www.istat.it/classificazione/principali-statistiche-geografiche-sui-comuni/"
TOSCANA_UCS_URL = "https://www502.regione.toscana.it/geonetwork/srv/api/records/r_toscan:0d4d6640-9a1c-47a4-9a5d-a85cdb36927c"


def _pct(ha: float, total: float) -> float:
    return float(ha) / float(total) * 100.0


def _cover_tables(snapshot: dict) -> tuple[dict, dict, dict]:
    cover = snapshot["landCover"]
    keys = cover["valueOrder"]
    municipalities: dict[str, dict] = {}
    for town in MUNICIPALITY_ORDER:
        raw = cover["municipalities"][town]
        total = float(raw["totalHa"])
        yearly = {}
        for year in YEARS:
            values = raw["rows"][str(year)]
            yearly[str(year)] = {
                "totalHa": total,
                "categories": {
                    key: {"ha": float(values[index]), "pct": _pct(values[index], total)}
                    for index, key in enumerate(keys)
                },
            }
        municipalities[town] = yearly

    aggregate = {}
    for year in YEARS:
        total = sum(municipalities[town][str(year)]["totalHa"] for town in MUNICIPALITY_ORDER)
        categories = {}
        for key in keys:
            ha = sum(
                municipalities[town][str(year)]["categories"][key]["ha"]
                for town in MUNICIPALITY_ORDER
            )
            categories[key] = {"ha": ha, "pct": _pct(ha, total)}
        aggregate[str(year)] = {"totalHa": total, "categories": categories}

    transformation = {}
    for town in MUNICIPALITY_ORDER:
        total = municipalities[town]["2007"]["totalHa"]
        changed = float(cover["transformation2007_2019"][town]["changedHa"])
        transformation[town] = {"changedHa": changed, "changedPct": _pct(changed, total), "totalHa": total}
    return municipalities, aggregate, transformation


def validate_snapshot(snapshot: dict) -> None:
    if snapshot.get("municipalityOrder") != MUNICIPALITY_ORDER:
        raise RuntimeError("v1.36: perimetro comunale non canonico.")
    classifications = snapshot.get("classifications", {})
    coastline = snapshot.get("coastlineKm", {})
    if list(classifications) != MUNICIPALITY_ORDER or list(coastline) != MUNICIPALITY_ORDER:
        raise RuntimeError("v1.36: classificazioni/costa non coprono i sette Comuni.")

    littoral = sum(bool(classifications[t]["littoral"]) for t in MUNICIPALITY_ORDER)
    coastal = sum(bool(classifications[t]["coastalZone"]) for t in MUNICIPALITY_ORDER)
    degurba = Counter(int(classifications[t]["degurba"]) for t in MUNICIPALITY_ORDER)
    if (littoral, coastal, degurba) != (4, 6, Counter({2: 6, 3: 1})):
        raise RuntimeError(f"v1.36: matrice territoriale inattesa: {littoral}, {coastal}, {dict(degurba)}.")

    coast_sum = 0.0
    for town in MUNICIPALITY_ORDER:
        value = coastline[town]
        if classifications[town]["littoral"]:
            if value is None or float(value) <= 0:
                raise RuntimeError(f"v1.36: {town} litoraneo senza lunghezza Istat.")
            coast_sum += float(value)
        elif value is not None:
            raise RuntimeError(f"v1.36: {town} non litoraneo con costa valorizzata.")
    if abs(coast_sum - 26.770816231) > 1e-6:
        raise RuntimeError(f"v1.36: somma linea litoranea inattesa: {coast_sum:.9f} km.")

    cover = snapshot.get("landCover", {})
    if cover.get("years") != YEARS:
        raise RuntimeError("v1.36: anni UCS non canonici.")
    definitions = cover.get("categoryDefinitions", [])
    keys = cover.get("valueOrder", [])
    if keys != [item["key"] for item in definitions] or set(keys) != set(MACRO_KEYS + DETAIL_KEYS):
        raise RuntimeError("v1.36: schema categorie UCS incoerente.")
    if list(cover.get("municipalities", {})) != MUNICIPALITY_ORDER:
        raise RuntimeError("v1.36: matrice UCS comunale incompleta.")

    municipalities, aggregate, transformations = _cover_tables(snapshot)
    for town in MUNICIPALITY_ORDER:
        raw = cover["municipalities"][town]
        if list(map(int, raw["rows"])) != YEARS:
            raise RuntimeError(f"v1.36: {town} non copre i cinque anni.")
        total = float(raw["totalHa"])
        if total <= 0:
            raise RuntimeError(f"v1.36: totale UCS non valido per {town}.")
        for year in YEARS:
            values = municipalities[town][str(year)]["categories"]
            if len(raw["rows"][str(year)]) != len(keys):
                raise RuntimeError(f"v1.36: {town} {year} vettore UCS incompleto.")
            if abs(sum(values[key]["pct"] for key in MACRO_KEYS) - 100.0) > MACRO_SUM_TOLERANCE_PCT:
                raise RuntimeError(f"v1.36: {town} {year} macroclassi non chiudono al 100%.")
            if values["forest"]["ha"] > values["forest_seminatural_total"]["ha"] + 1e-5:
                raise RuntimeError(f"v1.36: {town} {year} bosco > macroclasse 3.")
            if values["seminativi"]["ha"] + values["permanent_crops"]["ha"] > values["agricultural"]["ha"] + 1e-5:
                raise RuntimeError(f"v1.36: {town} {year} seminativi+permanenti > agricolo.")

    for year in YEARS:
        total = aggregate[str(year)]["totalHa"]
        if total <= 0:
            raise RuntimeError("v1.36: totale UCS Versilia non valido.")
        for key in keys:
            item = aggregate[str(year)]["categories"][key]
            if abs(item["pct"] - item["ha"] / total * 100.0) > 1e-9:
                raise RuntimeError(f"v1.36: aggregato {year} {key} non ponderato per superficie.")

    for town, item in transformations.items():
        if not (0 <= item["changedHa"] <= item["totalHa"]):
            raise RuntimeError(f"v1.36: trasformazione fuori dominio per {town}.")


def _identity_rows(site: dict) -> dict[str, dict]:
    rows = {row["town"]: row for row in site["metrics"]["population"]["rows"]}
    if set(MUNICIPALITY_ORDER) - set(rows):
        raise RuntimeError("v1.36: population non copre i sette Comuni.")
    return rows


def _id(row: dict) -> dict:
    return {"town": row["town"], "code": row["code"], "slug": row["slug"]}


def _classification_metric(snapshot: dict, identities: dict[str, dict]) -> dict:
    rows = []
    source = snapshot["classifications"]
    for town in MUNICIPALITY_ORDER:
        item = source[town]
        rows.append({
            **_id(identities[town]), "value": int(item["degurba"]),
            "formatted": f"DEGURBA {int(item['degurba'])}",
            "classification": {
                "littoral": bool(item["littoral"]), "coastalZone": bool(item["coastalZone"]),
                "degurba": int(item["degurba"]), "degurbaLabel": item["degurbaLabel"],
            },
            "series": None, "normalized": None, "benchmarkValue": None,
        })
    counts = {
        "littoral": sum(bool(v["littoral"]) for v in source.values()),
        "coastalZone": sum(bool(v["coastalZone"]) for v in source.values()),
        "degurba2": sum(int(v["degurba"]) == 2 for v in source.values()),
        "degurba3": sum(int(v["degurba"]) == 3 for v in source.values()),
    }
    return {
        "meta": {
            "key": "territorialClassification", "theme": "ambiente",
            "label": "Classificazioni territoriali", "shortLabel": "Classificazioni",
            "description": "Litoraneità, appartenenza alle zone costiere e grado di urbanizzazione (DEGURBA) dei sette Comuni.",
            "unit": "number", "year": "2021", "source": "Istat — Geografie funzionali / SITUAS",
            "polarity": "neutral", "compositeType": "territorialClassification",
            "primaryLabel": "Grado di urbanizzazione",
            "searchTerms": ["DEGURBA", "litoraneità", "zona costiera", "urbanizzazione", "territorio"],
        },
        "sourceUrl": ISTAT_CLASS_URL, "rows": rows,
        "aggregate": {
            "value": counts["coastalZone"], "label": "Comuni in zona costiera",
            "note": "6 Comuni su 7 ricadono nella zona costiera Istat; le classi DEGURBA non vengono mediate.",
            "classificationCounts": counts,
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Classificazioni territoriali ufficiali",
            "formula": "Attributi categoriali comunali; nessuna media tra Comuni.",
            "caveat": "Litoraneità e zona costiera sono concetti distinti.",
            "coverage": "7/7",
        },
    }


def _coastline_metric(snapshot: dict, identities: dict[str, dict]) -> dict:
    rows, total = [], 0.0
    for town in MUNICIPALITY_ORDER:
        value = snapshot["coastlineKm"][town]
        if value is None:
            rows.append({
                **_id(identities[town]), "value": None, "formatted": "n.a.", "notApplicable": True,
                "applicabilityNote": "Comune non litoraneo nella classificazione Istat.",
                "series": None, "normalized": None, "benchmarkValue": None,
            })
        else:
            value = float(value); total += value
            rows.append({
                **_id(identities[town]), "value": value,
                "formatted": f"{value:.3f}".replace(".", ",") + " km", "notApplicable": False,
                "series": None, "normalized": None, "benchmarkValue": value,
            })
    return {
        "meta": {
            "key": "statisticalCoastlineLength", "theme": "ambiente",
            "label": "Linea litoranea statistica", "shortLabel": "Linea litoranea",
            "description": "Lunghezza della linea litoranea statistica Istat per i Comuni direttamente confinanti con il mare.",
            "unit": "km", "year": "31 dicembre 2021", "source": "Istat — Linea litoranea",
            "polarity": "neutral",
            "searchTerms": ["costa", "linea litoranea", "litoraneità", "chilometri costa", "Istat"],
        },
        "sourceUrl": ISTAT_GEO_URL, "rows": rows,
        "aggregate": {
            "value": total, "label": "Versilia · linea litoranea statistica",
            "note": "Somma dei quattro Comuni litoranei Istat; non coincide con i soli chilometri delle aree di balneazione ARPAT.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Dato geografico ufficiale",
            "formula": "SHAPE_Leng Istat convertito da metri a chilometri; somma sui quattro Comuni litoranei.",
            "caveat": "La linea statistica può comprendere strutture antropiche.",
            "coverage": "4/4 Comuni litoranei; 3/7 n.a.",
        },
    }


def _series(yearly: dict, key: str) -> dict:
    return {
        "years": YEARS,
        "ha": [yearly[str(year)]["categories"][key]["ha"] for year in YEARS],
        "pct": [yearly[str(year)]["categories"][key]["pct"] for year in YEARS],
    }


def _land_cover_metric(snapshot: dict, identities: dict[str, dict]) -> dict:
    municipalities, aggregate_yearly, transformations = _cover_tables(snapshot)
    definitions = snapshot["landCover"]["categoryDefinitions"]
    labels = {item["key"]: item["shortLabel"] for item in definitions}

    def row_for(town: str) -> dict:
        yearly = municipalities[town]
        latest = yearly["2019"]
        parts = [{
            "key": key, "label": labels[key], "value": latest["categories"][key]["pct"],
            "unit": "percent", "ha": latest["categories"][key]["ha"],
        } for key in MACRO_KEYS]
        value = latest["categories"]["artificialized"]["pct"]
        return {
            **_id(identities[town]), "value": value,
            "formatted": f"{value:.1f}".replace(".", ",") + "%",
            "parts": parts, "landCoverYears": YEARS,
            "coverSeries": {item["key"]: _series(yearly, item["key"]) for item in definitions},
            "totalHa": {str(year): yearly[str(year)]["totalHa"] for year in YEARS},
            "transformation": transformations[town],
            "series": None, "normalized": None, "benchmarkValue": None,
        }

    rows = [row_for(town) for town in MUNICIPALITY_ORDER]
    latest = aggregate_yearly["2019"]
    aggregate_series = {item["key"]: _series(aggregate_yearly, item["key"]) for item in definitions}
    parts = [{
        "key": key, "label": labels[key], "value": latest["categories"][key]["pct"],
        "unit": "percent", "ha": latest["categories"][key]["ha"],
    } for key in MACRO_KEYS]
    changed = sum(item["changedHa"] for item in transformations.values())
    total = sum(item["totalHa"] for item in transformations.values())
    return {
        "meta": {
            "key": "landCoverProfile", "theme": "ambiente",
            "label": "Uso e copertura del suolo", "shortLabel": "Copertura del suolo",
            "description": "Evoluzione 2007–2019 dell'Uso e Copertura del Suolo (UCS) della Regione Toscana, in ettari e quota del territorio cartografato.",
            "unit": "percent", "year": "2007–2019", "source": "Regione Toscana — UCS",
            "polarity": "neutral", "compositeType": "landCoverProfile",
            "primaryLabel": "Superficie artificializzata · 2019",
            "searchTerms": ["uso del suolo", "copertura del suolo", "UCS", "artificializzato", "agricolo", "boschi", "seminativi", "zone umide", "corpi idrici"],
        },
        "sourceUrl": TOSCANA_UCS_URL, "categoryDefinitions": definitions, "landCoverYears": YEARS,
        "rows": rows,
        "aggregate": {
            "value": latest["categories"]["artificialized"]["pct"],
            "label": "Versilia · superficie artificializzata 2019",
            "note": "Quota Versilia = Σ ettari categoria / Σ ettari UCS dei 7 Comuni; mai media semplice delle percentuali comunali.",
            "parts": parts, "coverSeries": aggregate_series,
            "totalHa": {str(year): aggregate_yearly[str(year)]["totalHa"] for year in YEARS},
            "transformation": {"changedHa": changed, "changedPct": _pct(changed, total), "totalHa": total},
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione geometrica su UCS Regione Toscana",
            "formula": "Comune: ha categoria / ha totali UCS. Versilia: Σ ha categoria / Σ ha totali UCS. Trasformazione: macroclasse livello 1 diversa tra 2007 e 2019.",
            "caveat": "Sottoclassi gerarchiche: non si sommano ai macrogruppi. Verde urbano UCS ≠ verde pubblico; artificializzato UCS ≠ consumo di suolo ISPRA; agricolo UCS ≠ SAU.",
            "coverage": "7/7 Comuni × 5 anni",
        },
    }


def build_metrics(site: dict, snapshot: dict) -> dict[str, dict]:
    validate_snapshot(snapshot)
    ids = _identity_rows(site)
    return {
        "territorialClassification": _classification_metric(snapshot, ids),
        "statisticalCoastlineLength": _coastline_metric(snapshot, ids),
        "landCoverProfile": _land_cover_metric(snapshot, ids),
    }


def install_sections(site: dict) -> None:
    environment = site["themes"].get("ambiente")
    if not environment:
        raise RuntimeError("v1.36: tema Ambiente non trovato.")
    sections, profile_found = [], False
    for raw in environment.get("sections", []):
        if raw.get("key") == LAND_COVER_SECTION_KEY:
            continue
        section = dict(raw)
        section["metrics"] = [key for key in section.get("metrics", []) if key not in NEW_METRIC_KEYS]
        if section.get("key") == PROFILE_SECTION_KEY:
            profile_found = True
            section["metrics"].extend(["territorialClassification", "statisticalCoastlineLength"])
        sections.append(section)
    if not profile_found:
        raise RuntimeError("v1.36: profilo-territoriale assente; il materializzatore deve seguire Biometria.")
    profile_index = next(i for i, section in enumerate(sections) if section["key"] == PROFILE_SECTION_KEY)
    sections.insert(profile_index + 1, {
        "key": LAND_COVER_SECTION_KEY, "label": "Uso e copertura del suolo",
        "description": "Serie UCS 2007–2019: composizione territoriale, dettaglio gerarchico e trasformazioni.",
        "metrics": ["landCoverProfile"],
    })
    environment["sections"] = sections
    environment["metrics"] = [key for section in sections for key in section.get("metrics", [])]


def patch_catalog(snapshot: dict) -> None:
    site = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    metrics = site.setdefault("metrics", {})
    already = sum(key in metrics for key in NEW_METRIC_KEYS)
    expected_before = EXPECTED_BASE_METRIC_COUNT + already
    if len(metrics) != expected_before:
        raise RuntimeError(f"v1.36: baseline materializzata {len(metrics)}, attese {expected_before}.")
    metrics.update(build_metrics(site, snapshot))
    install_sections(site)
    if len(metrics) != EXPECTED_RELEASE_METRIC_COUNT:
        raise RuntimeError(f"v1.36: catalogo finale {len(metrics)}, attese {EXPECTED_RELEASE_METRIC_COUNT}.")
    site.update({"version": "v1.36.0", "release_version": "1.36.0", "updated": "12 settembre 2026"})
    SITE_DATA.write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    external = sum(m.get("dataStorage", {}).get("type") == "external-climate" for m in metrics.values())
    registry["expectedMetricCount"] = len(metrics)
    registry["expectedExternalMetricCount"] = external
    registry["expectedInlineMetricCount"] = len(metrics) - external
    profiles = registry.setdefault("sourceProfiles", {})
    profiles["istat-geografie-funzionali-2021"] = {
        "publisher": "Istat", "frequency": "census_or_irregular",
        "frequencyLabel": "Censuaria o irregolare",
        "expectedRelease": "Secondo gli aggiornamenti Istat delle classificazioni territoriali",
        "acquisitionMethod": "Classificazioni comunali e linea litoranea statistica Istat.",
        "licenseName": "CC BY 4.0", "licenseUrl": "https://www.istat.it/note-legali/",
    }
    profiles["regione-toscana-ucs-2007-2019"] = {
        "publisher": "Regione Toscana", "frequency": "annual_or_irregular",
        "frequencyLabel": "Serie storica UCS disponibile 2007–2019",
        "expectedRelease": "Nessuna annualità omogenea successiva al 2019 inclusa in questa serie",
        "acquisitionMethod": "Aggregazione geometrica comunale del dataset poligonale UCS.",
        "licenseName": "CC BY", "licenseUrl": TOSCANA_UCS_URL,
    }
    mapping = registry.setdefault("sourceProfileByUrl", {})
    mapping.update({
        ISTAT_CLASS_URL: "istat-geografie-funzionali-2021",
        ISTAT_GEO_URL: "istat-geografie-funzionali-2021",
        TOSCANA_UCS_URL: "regione-toscana-ucs-2007-2019",
    })
    overrides = registry.setdefault("metricOverrides", {})
    overrides.update({
        "territorialClassification": {"profile": "istat-geografie-funzionali-2021"},
        "statisticalCoastlineLength": {"profile": "istat-geografie-funzionali-2021"},
        "landCoverProfile": {"profile": "regione-toscana-ucs-2007-2019"},
    })
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    snapshot = json.loads(SOURCE.read_text(encoding="utf-8"))
    validate_snapshot(snapshot)
    runpy.run_path(str(RUNTIME_PATCH), run_name="__main__")
    patch_catalog(snapshot)
    print("v1.36.0 materializzata: 201 indicatori; classificazioni, costa Istat e UCS 2007–2019.")


if __name__ == "__main__":
    main()
