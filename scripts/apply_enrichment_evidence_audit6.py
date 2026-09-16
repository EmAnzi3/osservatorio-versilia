#!/usr/bin/env python3
"""Estende le evidenze A3.2 della tranche audit-6 senza duplicare il catalogo pubblico."""
from __future__ import annotations

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "apply_enrichment_evidence_audit5.py"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"

ns = runpy.run_path(str(BASE))
AVAILABLE = ns["AVAILABLE"]
UNAVAILABLE = ns["UNAVAILABLE"]
NOT_APPLICABLE = ns["NOT_APPLICABLE"]
EVIDENCE = ns["EVIDENCE"]
METRIC_EVIDENCE = ns["METRIC_EVIDENCE"]
_merge_dimensions = ns["_merge_dimensions"]


def _annotation(state: str, evidence: str, source_reference: str = "") -> dict:
    item = {"state": state, "evidence": evidence}
    if source_reference:
        item["sourceReference"] = source_reference
    return item


def _add_profile(profile_id: str, dimension: str, state: str, evidence: str, reference: str) -> None:
    dimensions = EVIDENCE.setdefault(profile_id, {})
    if dimension in dimensions:
        raise RuntimeError(f"A3.2 audit-6: dimensione già definita: {profile_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


def _add_metric(metric_id: str, dimension: str, state: str, evidence: str, reference: str = "") -> None:
    dimensions = METRIC_EVIDENCE.setdefault(metric_id, {})
    if dimension in dimensions:
        raise RuntimeError(f"A3.2 audit-6: override già definito: {metric_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


# OpenBDAP FET: i bilanci armonizzati sono confrontabili territorialmente e
# rendono disponibili le grandezze contabili alla base degli indicatori pro
# capite, percentuali e di capacità presenti nel profilo.
_add_profile(
    "openbdap-annual",
    "benchmark_toscana_italia",
    AVAILABLE,
    "OpenBDAP FET consente il confronto dei principali indicatori dei Comuni italiani e rende scaricabili i bilanci armonizzati per territorio regionale, permettendo benchmark coerenti almeno a scala Toscana e nazionale.",
    "https://openbdap.rgs.mef.gov.it/FET/Analizza",
)
_add_profile(
    "openbdap-annual",
    "numeratore_denominatore",
    AVAILABLE,
    "OpenBDAP FET pubblica i dati di bilancio armonizzati e le analisi pro capite da cui sono ricostruibili le componenti contabili e demografiche degli indicatori di rapporto, quota e valore per residente del profilo.",
    "https://openbdap.rgs.mef.gov.it/FET/Analizza",
)

# Conto Annuale RGS: i dataset annuali espongono genere, scale territoriali e
# valori assoluti insieme agli indicatori normalizzati. La frequenza resta annuale.
_add_profile(
    "rgs-conto-annuale-annual",
    "sesso",
    AVAILABLE,
    "Conto Annuale pubblica sistematicamente valori distinti per uomini e donne nelle tavole sul personale, incluse distribuzione geografica, età e formazione.",
    "https://contoannuale.rgs.mef.gov.it/it/web/sicosito/distribuzione-geografica-acc",
)
_add_profile(
    "rgs-conto-annuale-annual",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Conto Annuale consente letture per Regione e Comune e confronti con graduatorie nazionali, mantenendo la stessa definizione degli indicatori di personale.",
    "https://contoannuale.rgs.mef.gov.it/it/web/sicosito/dipendenti/abitanti-comune-acc",
)
_add_profile(
    "rgs-conto-annuale-annual",
    "assoluto_normalizzato",
    AVAILABLE,
    "Le tavole Conto Annuale affiancano consistenze assolute del personale alle misure normalizzate o percentuali; l'indicatore dipendenti/abitanti espone esplicitamente dipendenti, abitanti e rapporto per 1.000.",
    "https://contoannuale.rgs.mef.gov.it/it/web/sicosito/dipendenti/abitanti-comune-acc",
)
_add_profile(
    "rgs-conto-annuale-annual",
    "frequenza_infra_annuale",
    UNAVAILABLE,
    "Conto Annuale è una rilevazione riferita all'anno e le tavole del profilo sono pubblicate per annualità; non è diffusa una serie mensile, trimestrale o semestrale metodologicamente equivalente.",
    "https://contoannuale.rgs.mef.gov.it/it/web/sicosito/dati-pubblicati",
)

# Geografia Istat: superficie, altimetria e popolazione sono pubblicate per
# Comuni e unità territoriali sovracomunali; le misure non sono infra-annuali.
_add_profile(
    "istat-geografia-comunale-2021",
    "dettaglio_territoriale",
    AVAILABLE,
    "Istat diffonde superficie e caratteristiche geografiche per Comuni, Province e Regioni e rimanda alle Basi territoriali/SITUAS per il dettaglio delle unità territoriali.",
    "https://www.istat.it/classificazione/principali-statistiche-geografiche-sui-comuni/",
)
_add_profile(
    "istat-geografia-comunale-2021",
    "benchmark_toscana_italia",
    AVAILABLE,
    "La stessa pubblicazione Istat copre l'intero territorio nazionale e riporta misure coerenti per Comuni, Province, Regioni e totale nazionale, rendendo disponibili confronti Toscana/Italia.",
    "https://www.istat.it/classificazione/principali-statistiche-geografiche-sui-comuni/",
)
_add_profile(
    "istat-geografia-comunale-2021",
    "frequenza_infra_annuale",
    UNAVAILABLE,
    "Le statistiche geografiche comunali sono riferite a date o assetti territoriali annuali/censuari; per superficie, altimetria e fasce altimetriche non esiste una serie infra-annuale equivalente.",
    "https://www.istat.it/classificazione/principali-statistiche-geografiche-sui-comuni/",
)

# LaMMA/Copernicus: la base giornaliera e climatica rende disponibili serie
# storiche; il profilo combinato consente benchmark territoriali oltre il Comune.
_add_profile(
    "lamma-copernicus-climate",
    "serie_storica",
    AVAILABLE,
    "LaMMA pubblica archivi giornalieri grigliati di temperature e precipitazioni su più annualità, mentre il profilo conserva anche serie climatiche di lungo periodo.",
    "https://dati.lamma.toscana.it/dataset?tags=spazializzazione",
)
_add_profile(
    "lamma-copernicus-climate",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Il profilo combina griglie LaMMA sull'intera Toscana con Copernicus/ERA5-Land, base climatica territorialmente estesa da cui sono ricostruibili benchmark coerenti a scala regionale e nazionale.",
    "https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land",
)

# Il PMO del Consorzio Toscana Nord è circoscritto al proprio comprensorio:
# non pubblica un benchmark metodologicamente equivalente Toscana/Italia.
_add_profile(
    "cb1-pmo-status-2026",
    "benchmark_toscana_italia",
    UNAVAILABLE,
    "Il portale PMO descrive e localizza gli interventi del Consorzio Toscana Nord nel proprio comprensorio; non diffonde un indicatore omologo per l'intera Toscana o per l'Italia.",
    "https://cbtoscananord.it/comunicazione/pmo-manutenzione-mappa-navigabile/",
)


# Geografia fisica: sesso/età non sono dimensioni semantiche di superficie e
# profilo altimetrico. Densità e profilo altimetrico hanno invece componenti
# ricostruibili dalla stessa fonte ufficiale.
for metric_id in ("municipalSurface", "altitudeProfile"):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica descrive una proprietà fisica del territorio comunale; il sesso delle persone non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica descrive una proprietà fisica del territorio comunale; l'età delle persone non è una dimensione semantica dell'oggetto misurato.",
    )
_add_metric(
    "municipalSurface",
    "numeratore_denominatore",
    NOT_APPLICABLE,
    "La superficie comunale è una misura fisica assoluta in km² e non è definita come rapporto con numeratore e denominatore.",
)
_add_metric(
    "municipalSurface",
    "categorie_specifiche",
    NOT_APPLICABLE,
    "La metrica pubblica l'estensione territoriale complessiva del Comune; non è definita come distribuzione per categorie.",
)
_add_metric(
    "populationDensity",
    "numeratore_denominatore",
    AVAILABLE,
    "Istat rende disponibili popolazione residente e superficie territoriale, le due componenti della densità di popolazione.",
    "https://www.istat.it/classificazione/principali-statistiche-geografiche-sui-comuni/",
)
_add_metric(
    "populationDensity",
    "categorie_specifiche",
    NOT_APPLICABLE,
    "La densità di popolazione pubblicata è un rapporto territoriale complessivo e non una distribuzione per categorie specifiche.",
)
_add_metric(
    "altitudeProfile",
    "numeratore_denominatore",
    AVAILABLE,
    "Istat pubblica la composizione percentuale della superficie comunale per otto fasce altimetriche, ricostruibile come superficie della fascia sul totale comunale.",
    "https://www.istat.it/classificazione/principali-statistiche-geografiche-sui-comuni/",
)
_add_metric(
    "altitudeProfile",
    "categorie_specifiche",
    AVAILABLE,
    "Istat pubblica otto fasce altimetriche ufficiali e la percentuale di superficie comunale in ciascuna fascia.",
    "https://www.istat.it/classificazione/principali-statistiche-geografiche-sui-comuni/",
)

# Le quattro metriche climatiche sono proprietà fisiche del clima e trend:
# sesso, età e numeratore/denominatore non sono dimensioni semanticamente adatte.
for metric_id in (
    "climatePrecipitationTrend50y",
    "climateTemperatureTrend50y",
    "climateTmaxTrend",
    "climateTminTrend",
):
    for dimension, evidence in (
        ("sesso", "La metrica misura una proprietà fisica del clima; il sesso delle persone non è una dimensione semantica del fenomeno."),
        ("eta", "La metrica misura una proprietà fisica del clima; l'età delle persone non è una dimensione semantica del fenomeno."),
        ("numeratore_denominatore", "La metrica è un trend climatico stimato nel tempo e non è definita come rapporto tra un numeratore e un denominatore statistico."),
    ):
        _add_metric(metric_id, dimension, NOT_APPLICABLE, evidence)

# PMO: conteggi e valori economici di interventi non hanno sesso/età e non sono
# rapporti con numeratore/denominatore.
for metric_id in (
    "pabCompletedOperationalGrossValue",
    "pabInProgressOperationalGrossValue",
    "pabInterventionsCompleted",
    "pabInterventionsInProgress",
):
    for dimension, evidence in (
        ("sesso", "La metrica descrive interventi di manutenzione idraulica o il loro valore economico; il sesso non è una dimensione semantica dell'oggetto misurato."),
        ("eta", "La metrica descrive interventi di manutenzione idraulica o il loro valore economico; l'età delle persone non è una dimensione semantica dell'oggetto misurato."),
        ("numeratore_denominatore", "La metrica è un conteggio di interventi o un valore economico lordo e non è definita come rapporto, tasso o quota."),
    ):
        _add_metric(metric_id, dimension, NOT_APPLICABLE, evidence)

# MIM: i conteggi puri non hanno numeratore/denominatore; rapporti e percentuali
# sono ricostruibili dai record sottostanti dello stesso dominio open data.
for metric_id in ("schoolSites", "schoolStudents"):
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        NOT_APPLICABLE,
        "La metrica è un conteggio di sedi o studenti e non è definita come rapporto, tasso o quota.",
    )
for metric_id in (
    "studentsPerClass",
    "primaryFullTimeShare",
    "schoolBuildingSafetyDocs",
    "schoolBuildingAccessibility",
    "schoolBuildingFacilities",
    "schoolBuildingAge",
    "schoolBuildingTransport",
):
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        AVAILABLE,
        "Il dominio open data MIM rende disponibili i record elementari necessari a ricostruire la componente favorevole e il totale di riferimento usati nel rapporto o nella percentuale pubblicata.",
        "https://dati.istruzione.it/opendata/",
    )

# Frame SBS / ASIA. Sesso ed età sono applicabili solo alle metriche basate sui
# lavoratori; per grandezze economiche o conteggi di unità locali sono N/A.
BUSINESS_WORKER_DEMOGRAPHIC_METRICS = (
    "industryWorkerShare",
    "localEmployees",
    "employeesPerLocalUnit",
    "localEmployeesChange",
)
for metric_id in BUSINESS_WORKER_DEMOGRAPHIC_METRICS:
    for dimension in ("sesso", "eta"):
        _add_metric(
            metric_id,
            dimension,
            AVAILABLE,
            "Il Registro Istat ASIA-Occupazione collega lavoratore e impresa e contiene caratteristiche demografiche del lavoratore, incluse sesso ed età, compatibili con la disaggregazione delle misure occupazionali.",
            "https://siqual.istat.it/SIQual/visualizza.do?id=8889017&language=IT&refresh=true",
        )

BUSINESS_OBJECT_METRICS = (
    "businessValueAdded",
    "industryValueAddedShare",
    "localUnits",
    "microUnits",
    "localUnitsChange",
    "businessTurnover",
    "valueAddedTurnoverShare",
    "grossOperatingMargin",
)
for metric_id in BUSINESS_OBJECT_METRICS:
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica misura una grandezza economica dell'unità locale/impresa o un conteggio di unità economiche; il sesso non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica misura una grandezza economica dell'unità locale/impresa o un conteggio di unità economiche; l'età delle persone non è una dimensione semantica dell'oggetto misurato.",
    )

BUSINESS_RATIO_METRICS = (
    "labourProductivity",
    "industryValueAddedShare",
    "industryWorkerShare",
    "microUnits",
    "employeesPerLocalUnit",
    "localUnitsChange",
    "localEmployeesChange",
    "turnoverPerPersonEmployed",
    "valueAddedTurnoverShare",
    "averageGrossRemunerationPerEmployee",
)
for metric_id in BUSINESS_RATIO_METRICS:
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        AVAILABLE,
        "Le tavole Frame SBS Territoriale rendono disponibili gli aggregati economici e occupazionali sottostanti necessari a ricostruire numeratore e denominatore della metrica.",
        "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
    )
for metric_id in (
    "businessValueAdded",
    "localUnits",
    "localEmployees",
    "businessTurnover",
    "labourCost",
    "grossOperatingMargin",
):
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        NOT_APPLICABLE,
        "La metrica è un valore assoluto o un conteggio e non è definita come rapporto, tasso, quota o indice con numeratore e denominatore.",
    )

BUSINESS_ABSOLUTE_NORMALIZED_METRICS = (
    "businessValueAdded",
    "labourProductivity",
    "industryValueAddedShare",
    "industryWorkerShare",
    "microUnits",
    "localEmployees",
    "employeesPerLocalUnit",
    "localUnitsChange",
    "localEmployeesChange",
    "businessTurnover",
    "turnoverPerPersonEmployed",
    "valueAddedTurnoverShare",
    "averageGrossRemunerationPerEmployee",
)
for metric_id in BUSINESS_ABSOLUTE_NORMALIZED_METRICS:
    _add_metric(
        metric_id,
        "assoluto_normalizzato",
        AVAILABLE,
        "Frame SBS Territoriale pubblica nello stesso dominio aggregati assoluti economici/occupazionali e indicatori derivati, rendendo ricostruibile la lettura assoluta e quella normalizzata della metrica.",
        "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
    )


def main() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    profiles = registry.get("sourceProfiles")
    if not isinstance(profiles, dict):
        raise RuntimeError("A3.2: sourceProfiles assente dal registry")

    applied_profiles = 0
    for profile_id, dimensions in EVIDENCE.items():
        profile = profiles.get(profile_id)
        if not isinstance(profile, dict):
            raise RuntimeError(f"A3.2: source profile mancante: {profile_id}")
        target = profile.setdefault("enrichmentDimensions", {})
        if not isinstance(target, dict):
            raise RuntimeError(f"A3.2: enrichmentDimensions non-oggetto: {profile_id}")
        applied_profiles += _merge_dimensions(target, dimensions, profile_id)

    overrides = registry.setdefault("metricOverrides", {})
    if not isinstance(overrides, dict):
        raise RuntimeError("A3.2: metricOverrides non-oggetto nel registry")

    applied_metrics = 0
    for metric_id, dimensions in METRIC_EVIDENCE.items():
        override = overrides.setdefault(metric_id, {})
        if not isinstance(override, dict):
            raise RuntimeError(f"A3.2: metric override non-oggetto: {metric_id}")
        target = override.setdefault("enrichmentDimensions", {})
        if not isinstance(target, dict):
            raise RuntimeError(f"A3.2: enrichmentDimensions override non-oggetto: {metric_id}")
        applied_metrics += _merge_dimensions(target, dimensions, metric_id)

    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "A3.2 evidence materializzata: "
        f"{applied_profiles} dimensioni su {len(EVIDENCE)} profili; "
        f"{applied_metrics} override su {len(METRIC_EVIDENCE)} metriche"
    )


if __name__ == "__main__":
    main()
