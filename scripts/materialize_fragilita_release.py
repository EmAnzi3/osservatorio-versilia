#!/usr/bin/env python3
"""Materializza la v1.33.0: fragilità territoriale e rischi nei renderer canonici."""
from __future__ import annotations

import json
import runpy
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "fragilita-comunale-v133.json"
ISTAT_URL = "https://www.istat.it/comunicato-stampa/la-fragilita-dei-comuni-italiani-anno-2022/"
IDROGEO_URL = "https://idrogeo.isprambiente.it/"

NEW_KEYS = (
    "municipalFragility",
    "protectedNaturalAreas",
    "essentialServicesAccessibility",
    "lowProductivityEmployment",
)

TOWN_ORDER = (
    "Massarosa",
    "Viareggio",
    "Camaiore",
    "Pietrasanta",
    "Seravezza",
    "Forte dei Marmi",
    "Stazzema",
)


def fmt(value: float, digits: int = 1, suffix: str = "") -> str:
    return f"{value:.{digits}f}".replace(".", ",") + suffix


def series(snapshot: dict, town: str, code: str) -> dict:
    rows = snapshot["istatByTown"][town]["series"][code]
    return {
        "years": [int(item["year"]) for item in rows],
        "values": [float(item["value"]) for item in rows],
    }


def town_identity(snapshot: dict, town: str) -> tuple[str, str]:
    item = snapshot["istatByTown"][town]
    return item["code"], item["slug"]


def simple_metric(snapshot: dict, *, key: str, theme: str, label: str, short: str,
                  description: str, unit: str, year: str, source: str, source_url: str,
                  values: dict[str, float], aggregate_value: float, aggregate_label: str,
                  aggregate_note: str, method_type: str, formula: str, caveat: str,
                  history_code: str | None = None, ordinal: dict | None = None,
                  polarity: str = "neutral", search_terms: list[str] | None = None) -> dict:
    rows = []
    for town in TOWN_ORDER:
        code, slug = town_identity(snapshot, town)
        value = float(values[town])
        item = {
            "town": town,
            "code": code,
            "slug": slug,
            "value": value,
            "formatted": fmt(value, 1, "%") if unit == "percent" else (f"{int(value)}/{ordinal['max']}" if ordinal else (fmt(value, 1, " min") if unit == "minutes" else str(value))),
            "series": series(snapshot, town, history_code) if history_code else None,
            "normalized": None,
            "benchmarkValue": value,
        }
        rows.append(item)
    meta = {
        "key": key,
        "theme": theme,
        "label": label,
        "shortLabel": short,
        "description": description,
        "unit": unit,
        "year": year,
        "source": source,
        "polarity": polarity,
        "comparisonReference": "aggregate",
    }
    if search_terms:
        meta["searchTerms"] = search_terms
    if ordinal:
        meta["ordinalScale"] = ordinal
        meta["fixedScaleMax"] = ordinal["max"]
        meta["suppressRank"] = True
    return {
        "meta": meta,
        "sourceUrl": source_url,
        "rows": rows,
        "aggregate": {
            "value": aggregate_value,
            "label": aggregate_label,
            "note": aggregate_note,
        },
        "normalizedAggregate": None,
        "method": {
            "type": method_type,
            "formula": formula,
            "caveat": caveat,
            "coverage": "7/7",
        },
    }


def hydro_metric(snapshot: dict, *, key: str, label: str, short: str, description: str,
                 kind: str, year: str, population_year: int, scenarios: list[str],
                 default_scenario: str) -> dict:
    rows = []
    area_total = sum(float(snapshot["hazardsByTown"][town]["municipalAreaKm2"]) for town in TOWN_ORDER)
    pop_field = f"population{population_year}"
    population_total = sum(int(snapshot["hazardsByTown"][town][pop_field]) for town in TOWN_ORDER)
    aggregate_parts = []

    for scenario in scenarios:
        area_km2 = sum(float(snapshot["hazardsByTown"][town][kind][scenario]["areaKm2"]) for town in TOWN_ORDER)
        residents = sum(int(snapshot["hazardsByTown"][town][kind][scenario]["residents"]) for town in TOWN_ORDER)
        aggregate_parts.append({
            "key": scenario,
            "label": scenario,
            "selectorLabel": scenario,
            "areaKm2": area_km2,
            "areaPct": area_km2 / area_total * 100 if area_total else None,
            "residents": residents,
            "residentsPct": residents / population_total * 100 if population_total else None,
            "value": residents / population_total * 100 if population_total else None,
            "unit": "percent",
        })

    aggregate_default = next(part for part in aggregate_parts if part["key"] == default_scenario)
    for town in TOWN_ORDER:
        code, slug = town_identity(snapshot, town)
        hazard = snapshot["hazardsByTown"][town]
        parts = []
        for scenario in scenarios:
            item = hazard[kind][scenario]
            parts.append({
                "key": scenario,
                "label": scenario,
                "selectorLabel": scenario,
                "areaKm2": float(item["areaKm2"]),
                "areaPct": float(item["areaPct"]),
                "residents": int(item["residents"]),
                "residentsPct": float(item["residentsPct"]),
                "value": float(item["residentsPct"]),
                "unit": "percent",
            })
        default = next(part for part in parts if part["key"] == default_scenario)
        row = {
            "town": town,
            "code": code,
            "slug": slug,
            "value": default["residentsPct"],
            "formatted": fmt(default["residentsPct"], 1, "%"),
            "series": None,
            "normalized": None,
            "benchmarkValue": default["residentsPct"],
            "municipalAreaKm2": float(hazard["municipalAreaKm2"]),
            "populationBase": int(hazard[pop_field]),
            "populationReference": population_year,
            "parts": parts,
        }
        if kind == "landslide":
            row["hazardHistory"] = hazard.get("landslideP3P4History", [])
        rows.append(row)

    is_flood = kind == "flood"
    meta = {
        "key": key,
        "theme": "ambiente",
        "label": label,
        "shortLabel": short,
        "description": description,
        "unit": "percent",
        "year": year,
        "source": "ISPRA — IdroGEO",
        "polarity": "neutral",
        "compositeType": "hydroRisk",
        "selectorLabel": "Scenario di pericolosità" if is_flood else "Classe",
        "scenarioNote": (
            "Scenari non sommabili: P3, P2 e P1 rappresentano estensioni progressivamente maggiori della superficie potenzialmente allagabile. "
            "P2 comprende le aree P3 e P1 comprende le aree P2. Le percentuali indicano quindi l’esposizione complessiva in ciascuno scenario, "
            "non quote separate del territorio o della popolazione."
            if is_flood else None
        ),
        "defaultScenario": default_scenario,
        "populationReference": population_year,
        "comparisonReference": "aggregate",
        "searchTerms": ["rischio idrogeologico", "residenti esposti", "superficie esposta", "idrogeo", "frane" if not is_flood else "alluvioni"],
    }
    return {
        "meta": meta,
        "sourceUrl": IDROGEO_URL,
        "rows": rows,
        "aggregate": {
            "value": aggregate_default["residentsPct"],
            "label": f"Versilia · residenti esposti {default_scenario}",
            "note": (
                f"Quota calcolata sommando i residenti esposti dei sette Comuni e rapportandoli alla popolazione Istat {population_year}; "
                "la quota territoriale usa la superficie comunale complessiva."
            ),
            "parts": aggregate_parts,
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Dato ufficiale ISPRA IdroGEO",
            "formula": "Territorio: superficie interessata / superficie comunale × 100. Residenti: popolazione esposta / popolazione residente di riferimento × 100.",
            "caveat": (
                "Le due percentuali hanno denominatori diversi. "
                + ("P3, P2 e P1 sono scenari cumulativi e non vanno sommati: P2 comprende P3 e P1 comprende P2." if is_flood else "P4, P3, P2, P1 e AA sono classi distinte; P3+P4 è il campo ufficiale ISPRA e non viene ricalcolato dai valori arrotondati.")
                + f" La pericolosità è riferita al {year}; i residenti esposti usano Istat {population_year}."
            ),
            "coverage": "7/7",
        },
    }


def build_metrics(snapshot: dict) -> dict[str, dict]:
    latest = {town: snapshot["istatByTown"][town]["latest2022"] for town in TOWN_ORDER}

    ifc_values = {town: latest[town]["COMP_FRAG_INDEX_DECILE"] for town in TOWN_ORDER}
    lowprod_values = {town: latest[town]["PERSEMP_LU_LOW_PRO_INDSERV_VENTILE"] for town in TOWN_ORDER}
    protected_values = {town: latest[town]["PROTECTED_NAT_AREAS"] for town in TOWN_ORDER}
    access_values = {town: latest[town]["INDEX_ACCES_ESSENT_SERVICES"] for town in TOWN_ORDER}

    area_total = sum(snapshot["hazardsByTown"][town]["municipalAreaKm2"] for town in TOWN_ORDER)
    protected_area = sum(snapshot["hazardsByTown"][town]["municipalAreaKm2"] * protected_values[town] / 100 for town in TOWN_ORDER)
    protected_aggregate = protected_area / area_total * 100

    return {
        "municipalFragility": simple_metric(
            snapshot,
            key="municipalFragility",
            theme="ambiente",
            label="Indice composito di fragilità comunale",
            short="Fragilità comunale",
            description="Indice Istat espresso in decili: 1 indica la fascia di minore fragilità relativa e 10 quella di maggiore fragilità relativa.",
            unit="decile",
            year="2022",
            source="Istat — Indice composito di fragilità comunale",
            source_url=ISTAT_URL,
            values=ifc_values,
            aggregate_value=float(statistics.median(ifc_values.values())),
            aggregate_label="Mediana dei 7 Comuni",
            aggregate_note="Mediana descrittiva dei decili comunali. I decili sono classi ordinali e non vengono mediati aritmeticamente.",
            method_type="Indice composito ufficiale Istat",
            formula="Decile dell’Indice composito di fragilità comunale: scala 1–10.",
            caveat="È una posizione relativa nella distribuzione comunale, non una misura cardinale: una distanza di un decile non equivale a una quantità costante di fragilità.",
            history_code="COMP_FRAG_INDEX_DECILE",
            ordinal={"min": 1, "max": 10, "minLabel": "minore fragilità relativa", "maxLabel": "maggiore fragilità relativa"},
            search_terms=["IFC", "indice fragilità", "fragilità comunale", "decile"],
        ),
        "protectedNaturalAreas": simple_metric(
            snapshot,
            key="protectedNaturalAreas",
            theme="ambiente",
            label="Territorio in aree naturali protette",
            short="Aree protette",
            description="Quota della superficie comunale compresa in aree protette EUAP e Natura 2000 secondo la fotografia territoriale usata da Istat per l’IFC.",
            unit="percent",
            year="2016–2021",
            source="Istat IFC — EUAP / Natura 2000",
            source_url=ISTAT_URL,
            values=protected_values,
            aggregate_value=protected_aggregate,
            aggregate_label="Versilia · quota territoriale",
            aggregate_note="Superficie protetta stimata sui sette Comuni divisa per la loro superficie complessiva; non è la media semplice delle percentuali comunali.",
            method_type="Dato territoriale ufficiale",
            formula="superficie in aree protette / superficie comunale × 100",
            caveat="È una fotografia, non una serie 2018–2022: EUAP ha riferimento 2016 e Natura 2000 aggiornamenti 2021 nell’elaborazione IFC.",
            polarity="neutral",
            search_terms=["aree protette", "Natura 2000", "EUAP", "parchi"],
        ),
        "essentialServicesAccessibility": simple_metric(
            snapshot,
            key="essentialServicesAccessibility",
            theme="ambiente",
            label="Accessibilità ai servizi essenziali",
            short="Accessibilità servizi",
            description="Tempo medio in auto dal centro comunale al Polo o Polo intercomunale più vicino secondo la classificazione delle aree interne.",
            unit="minutes",
            year="2019",
            source="Istat — Indice composito di fragilità comunale",
            source_url=ISTAT_URL,
            values=access_values,
            aggregate_value=float(statistics.median(access_values.values())),
            aggregate_label="Mediana dei 7 Comuni",
            aggregate_note="Mediana descrittiva dei tempi dei sette centri comunali; non rappresenta il tempo medio di viaggio della popolazione versiliese.",
            method_type="Indicatore di accessibilità territoriale",
            formula="Minuti in auto dal centro comunale al Polo/Polo intercomunale più vicino.",
            caveat="Riferimento effettivo 2019. Il valore 0 per Camaiore e Viareggio è coerente con il loro ruolo di Polo; le ripetizioni nell’export IFC non sono una serie storica.",
            polarity="negative",
            search_terms=["servizi essenziali", "aree interne", "polo", "accessibilità"],
        ),
        "lowProductivityEmployment": simple_metric(
            snapshot,
            key="lowProductivityEmployment",
            theme="economia",
            label="Addetti in unità locali a bassa produttività",
            short="Addetti a bassa produttività",
            description="Posizione in ventili della componente IFC relativa alla presenza di addetti in unità locali di industria e servizi a bassa produttività di settore.",
            unit="ventile",
            year="2022",
            source="Istat — Indice composito di fragilità comunale",
            source_url=ISTAT_URL,
            values=lowprod_values,
            aggregate_value=float(statistics.median(lowprod_values.values())),
            aggregate_label="Mediana dei 7 Comuni",
            aggregate_note="Mediana descrittiva dei ventili comunali. Il dato pubblicato è ordinale 1–20 e non viene trasformato in percentuale.",
            method_type="Componente ufficiale dell’IFC",
            formula="Ventile 1–20 della distribuzione comunale: valori più alti indicano maggiore presenza relativa della componente di fragilità.",
            caveat="Non misura direttamente la quota percentuale di addetti né il valore aggiunto prodotto. I ventili sono classi ordinali e non vengono mediati aritmeticamente.",
            history_code="PERSEMP_LU_LOW_PRO_INDSERV_VENTILE",
            ordinal={"min": 1, "max": 20, "minLabel": "minore presenza relativa", "maxLabel": "maggiore presenza relativa"},
            search_terms=["produttività", "addetti", "unità locali", "ventile", "bassa produttività"],
        ),
        "landslideExposure": hydro_metric(
            snapshot,
            key="landslideExposure",
            label="Pericolosità ed esposizione a frane",
            short="Frane",
            description="Superficie comunale e residenti interessati dalle classi di pericolosità da frana PAI, con P3+P4 mantenuto come campo ufficiale ISPRA.",
            kind="landslide",
            year="2024",
            population_year=2021,
            scenarios=["P3+P4", "P4", "P3", "P2", "P1", "AA"],
            default_scenario="P3+P4",
        ),
        "floodExposure": hydro_metric(
            snapshot,
            key="floodExposure",
            label="Pericolosità ed esposizione ad alluvioni",
            short="Alluvioni",
            description="Superficie comunale e residenti interessati dagli scenari di pericolosità idraulica P3, P2 e P1 della mosaicatura nazionale ISPRA.",
            kind="flood",
            year="2020",
            population_year=2011,
            scenarios=["P3", "P2", "P1"],
            default_scenario="P2",
        ),
    }


def replace_environment_sections(theme: dict) -> None:
    old_sections = list(theme.get("sections", []))
    management = [
        "pabProgrammedInterventionLength",
        "pabProgrammedInterventions",
        "pabProgrammedMaintenanceValue",
        "managedReticulumLength",
        "hydraulicWorksCensusElements",
        "pabInterventionsInProgress",
        "pabInterventionsCompleted",
        "pabInProgressOperationalGrossValue",
        "pabCompletedOperationalGrossValue",
    ]
    new_first = [
        {
            "key": "fragilita-rischi",
            "label": "Fragilità territoriale e rischi",
            "description": "Fragilità comunale, aree protette e accessibilità ai servizi, con lettura distinta di pericolosità territoriale ed esposizione della popolazione a frane e alluvioni.",
            "metrics": ["municipalFragility", "landslideExposure", "floodExposure", "protectedNaturalAreas", "essentialServicesAccessibility"],
        },
        {
            "key": "suolo-territorio",
            "label": "Suolo e territorio",
            "description": "Consumo di suolo e variazioni recenti della superficie consumata.",
            "metrics": ["landUse", "landUseChange"],
        },
        {
            "key": "gestione-rischio",
            "label": "Gestione del rischio e manutenzione",
            "description": "Reticolo in gestione, opere idrauliche, interventi e programmazione della manutenzione.",
            "metrics": management,
        },
    ]
    rest = [s for s in old_sections if s.get("key") not in {"territorio", "fragilita-rischi", "suolo-territorio", "gestione-rischio"}]
    theme["sections"] = new_first + rest
    theme["metrics"] = [key for section in theme["sections"] for key in section.get("metrics", [])]


def patch_catalog(snapshot: dict) -> None:
    data = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    metrics = data.setdefault("metrics", {})
    built = build_metrics(snapshot)
    metrics.update(built)

    environment = data.get("themes", {}).get("ambiente")
    economy = data.get("themes", {}).get("economia")
    if not environment or not economy:
        raise RuntimeError("Temi ambiente/economia non trovati")
    replace_environment_sections(environment)

    production = next((s for s in economy.get("sections", []) if s.get("key") == "produzione"), None)
    if not production:
        raise RuntimeError("Sezione Economia/Sistema produttivo non trovata")
    prod_metrics = [k for k in production.get("metrics", []) if k != "lowProductivityEmployment"]
    anchor = prod_metrics.index("labourProductivity") + 1 if "labourProductivity" in prod_metrics else min(2, len(prod_metrics))
    prod_metrics.insert(anchor, "lowProductivityEmployment")
    production["metrics"] = prod_metrics
    economy["metrics"] = [key for section in economy.get("sections", []) for key in section.get("metrics", [])]

    data["version"] = "v1.33.0"
    data["release_version"] = "1.33.0"
    data["updated"] = "10 settembre 2026"
    SITE_DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    external = sum(m.get("dataStorage", {}).get("type") == "external-climate" for m in metrics.values())
    registry["expectedMetricCount"] = len(metrics)
    registry["expectedExternalMetricCount"] = external
    registry["expectedInlineMetricCount"] = len(metrics) - external

    profiles = registry.setdefault("sourceProfiles", {})
    profiles["istat-fragility-2022"] = {
        "publisher": "Istat",
        "frequency": "irregular",
        "frequencyLabel": "Secondo gli aggiornamenti Istat dell’Indice composito di fragilità comunale",
        "expectedRelease": "Secondo la fonte",
        "acquisitionMethod": "Dataset comunali Istat dell’Indice composito di fragilità comunale e delle sue componenti, con conservazione dei riferimenti temporali effettivi.",
        "licenseName": "Condizioni di riuso Istat",
        "licenseUrl": ISTAT_URL,
    }
    profiles["ispra-idrogeo-risk"] = {
        "publisher": "ISPRA",
        "frequency": "irregular",
        "frequencyLabel": "Secondo gli aggiornamenti delle mosaicature nazionali IdroGEO",
        "expectedRelease": "Secondo la fonte",
        "acquisitionMethod": "Indicatori comunali di rischio idrogeologico ISPRA IdroGEO: superficie e popolazione esposta per classe/scenario.",
        "licenseName": "Condizioni di riuso ISPRA",
        "licenseUrl": IDROGEO_URL,
    }
    by_url = registry.setdefault("sourceProfileByUrl", {})
    by_url[ISTAT_URL] = "istat-fragility-2022"
    by_url[IDROGEO_URL] = "ispra-idrogeo-risk"
    overrides = registry.setdefault("metricOverrides", {})
    for key in ("municipalFragility", "protectedNaturalAreas", "essentialServicesAccessibility", "lowProductivityEmployment"):
        overrides[key] = {"profile": "istat-fragility-2022"}
    for key in ("landslideExposure", "floodExposure"):
        overrides[key] = {"profile": "ispra-idrogeo-risk"}
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if not SNAPSHOT.exists():
        raise RuntimeError("Snapshot fragilità v1.33.0 mancante")
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if snapshot.get("towns") and set(snapshot["towns"]) != set(TOWN_ORDER):
        raise RuntimeError("Copertura comuni snapshot non 7/7")
    try:
        runpy.run_path(str(ROOT / "scripts" / "patch_fragilita_runtime.py"), run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (None, 0):
            raise
    patch_catalog(snapshot)
    print("Fragilità territoriale e rischi v1.33.0 materializzati nei renderer canonici.")


if __name__ == "__main__":
    main()
