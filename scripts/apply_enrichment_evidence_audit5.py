#!/usr/bin/env python3
"""Estende le evidenze A3.2 della tranche audit-5 senza duplicare il catalogo pubblico."""
from __future__ import annotations

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "apply_enrichment_evidence.py"
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
        raise RuntimeError(f"A3.2 audit-5: dimensione già definita: {profile_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


def _add_metric(metric_id: str, dimension: str, state: str, evidence: str, reference: str = "") -> None:
    dimensions = METRIC_EVIDENCE.setdefault(metric_id, {})
    if dimension in dimensions:
        raise RuntimeError(f"A3.2 audit-5: override già definito: {metric_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


# MIM: i dataset nazionali sono collegabili all'anagrafica scuole, che espone
# Regione, Provincia e Comune. Il benchmark regionale/nazionale è quindi
# ricostruibile con definizione coerente.
_add_profile(
    "mim-school-year",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Il catalogo MIM pubblica dataset nazionali collegabili all'anagrafica delle scuole, che espone Regione, Provincia e Comune; gli stessi indicatori possono quindi essere aggregati con definizione coerente per Toscana e Italia.",
    "https://dati.istruzione.it/opendata/opendata/catalog/SCUANAGRAFEPAR20242520250831.csv",
)

# Pendolarismo 2021: matrice nazionale origine-destinazione tra Comuni.
_add_profile(
    "istat-commuting-irregular",
    "dettaglio_territoriale",
    AVAILABLE,
    "La matrice Istat 2021 contiene i flussi origine-destinazione tra Comuni dell'intero territorio italiano; gli stessi conteggi possono essere aggregati a scale territoriali più ampie del singolo Comune.",
    "https://www.istat.it/notizia/matrice-di-pendolarismo-per-lavoro/",
)
_add_profile(
    "istat-commuting-irregular",
    "benchmark_toscana_italia",
    AVAILABLE,
    "La matrice Istat 2021 usa un'unica definizione nazionale dei flussi origine-destinazione comunali, rendendo ricostruibili aggregati coerenti per Toscana e Italia sullo stesso periodo e universo.",
    "https://www.istat.it/notizia/matrice-di-pendolarismo-per-lavoro/",
)

# OpenBDAP: le 24 metriche del profilo misurano grandezze contabili o finanziarie
# dell'ente. Sesso ed età non sono dimensioni semantiche dell'oggetto misurato.
OPENBDAP_FINANCE_METRICS = (
    "cashReceiptsPerResident",
    "cashBalancePerResident",
    "currentRevenueAccruedPerResident",
    "currentExpenditureCommittedPerResident",
    "capitalExpenditureCommittedPerResident",
    "ownRevenueShare",
    "currentCollectionCapacity",
    "currentPaymentCapacity",
    "availableAdministrationResultPerResident",
    "rigidExpenditureShare",
    "educationMissionExpenditurePerResident",
    "socialMissionExpenditurePerResident",
    "environmentMissionExpenditurePerResident",
    "mobilityMissionExpenditurePerResident",
    "cultureSportMissionExpenditurePerResident",
    "tourismDevelopmentMissionExpenditurePerResident",
    "securityMissionExpenditurePerResident",
    "financialDebtProfile",
    "fcdePerResident",
    "yearEndCashFundPerResident",
    "generalAdministrationMissionExpenditurePerResident",
    "territorialPlanningMissionExpenditurePerResident",
    "civilProtectionMissionExpenditurePerResident",
    "economicDevelopmentMissionExpenditurePerResident",
)
for metric_id in OPENBDAP_FINANCE_METRICS:
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica misura una grandezza contabile o finanziaria dell'ente comunale; il sesso non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica misura una grandezza contabile o finanziaria dell'ente comunale; l'età non è una dimensione semantica dell'oggetto misurato.",
    )

# MIM studenti: la fonte espone direttamente fascia di età e genere.
_add_metric(
    "schoolStudents",
    "sesso",
    AVAILABLE,
    "Il Portale unico MIM pubblica il numero di studenti per anno di corso, classe e genere per scuole statali e paritarie.",
    "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti",
)
_add_metric(
    "schoolStudents",
    "eta",
    AVAILABLE,
    "Il Portale unico MIM pubblica il numero di studenti per anno di corso e fascia di età per scuole statali e paritarie.",
    "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti",
)
_add_metric(
    "studentsPerClass",
    "sesso",
    AVAILABLE,
    "Il dataset MIM studenti per anno di corso, classe e genere rende disponibile la componente studenti distinta per genere sullo stesso perimetro scolastico usato dalla metrica.",
    "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti",
)

# Conteggio sedi e indicatori edilizi: il sesso non è semanticamente applicabile.
for dimension in ("sesso", "eta"):
    _add_metric(
        "schoolSites",
        dimension,
        NOT_APPLICABLE,
        "La metrica conta sedi scolastiche come unità territoriali; una disaggregazione per sesso o età delle persone non ha significato per l'oggetto contato.",
    )
for metric_id in (
    "schoolBuildingSafetyDocs",
    "schoolBuildingAccessibility",
    "schoolBuildingFacilities",
    "schoolBuildingAge",
    "schoolBuildingTransport",
):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica descrive caratteristiche fisiche, documentali o funzionali degli edifici scolastici; il sesso non è una dimensione semantica dell'edificio.",
    )

# Pendolarismo: la matrice OD contiene i conteggi necessari ai rapporti di
# mobilità esterna/autocontenimento; i conteggi puri non hanno num/den.
for metric_id in ("inboundCommuters", "outboundCommuters", "commuterBalance"):
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        NOT_APPLICABLE,
        "La metrica è un conteggio o una differenza di conteggi di pendolari e non è definita come rapporto, tasso, quota o indice con numeratore e denominatore.",
    )
for metric_id in ("outsideMunicipality", "selfContainment"):
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        AVAILABLE,
        "La matrice Istat origine-destinazione pubblica i conteggi comunali necessari a ricostruire sia il numeratore sia il totale degli occupati del Comune usato come denominatore della quota.",
        "https://www.istat.it/notizia/matrice-di-pendolarismo-per-lavoro/",
    )

# Turismo: la banca dati ufficiale elenca tipologia ricettiva, provenienza,
# territorio, risorsa e periodo, ma non sesso/età dei clienti.
TOURISM_MOVEMENT_METRICS = (
    "tourismPresences",
    "tourismSeasonality",
    "foreignTourismShare",
    "tourismIntensity",
    "tourismArrivals",
    "tourismAverageStay",
)
for metric_id in TOURISM_MOVEMENT_METRICS:
    _add_metric(
        metric_id,
        "sesso",
        UNAVAILABLE,
        "La banca dati Turismo della Regione Toscana elenca le dimensioni di classificazione del movimento clienti (tipologia ricettiva, provenienza, territorio, risorsa e periodo) ma non diffonde il sesso dei clienti nel dominio usato.",
        "https://www.regione.toscana.it/statistiche/banca-dati-turismo",
    )
    _add_metric(
        metric_id,
        "eta",
        UNAVAILABLE,
        "La banca dati Turismo della Regione Toscana elenca le dimensioni di classificazione del movimento clienti (tipologia ricettiva, provenienza, territorio, risorsa e periodo) ma non diffonde l'età dei clienti nel dominio usato.",
        "https://www.regione.toscana.it/statistiche/banca-dati-turismo",
    )

for metric_id in ("tourismBedsPer1000", "tourismStructuresPer1000"):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica misura lo stock di capacità o strutture ricettive; il sesso non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica misura lo stock di capacità o strutture ricettive; l'età delle persone non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "frequenza_infra_annuale",
        UNAVAILABLE,
        "Il dominio Strutture ricettive della banca dati regionale pubblica per esercizi, letti e camere il numero medio presente nell'anno; non diffonde per queste misure una serie infra-annuale equivalente.",
        "https://www.regione.toscana.it/statistiche/banca-dati-turismo",
    )

for metric_id in ("tourismPresences", "foreignTourismShare", "tourismArrivals", "tourismAverageStay"):
    _add_metric(
        metric_id,
        "frequenza_infra_annuale",
        AVAILABLE,
        "La banca dati Turismo regionale diffonde mensilmente arrivi e presenze e consente la classificazione per provenienza; per questa metrica è quindi disponibile una granularità infra-annuale compatibile.",
        "https://www.regione.toscana.it/statistiche/banca-dati-turismo",
    )
_add_metric(
    "tourismSeasonality",
    "frequenza_infra_annuale",
    NOT_APPLICABLE,
    "La metrica misura la concentrazione delle presenze nei tre mesi principali rispetto all'intero anno: per definizione è un indicatore annuale di stagionalità, non una misura infra-annuale.",
)

for metric_id in ("tourismPresences", "tourismArrivals"):
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        NOT_APPLICABLE,
        "La metrica è un conteggio ufficiale di movimento turistico e non è definita come rapporto, tasso, quota o indice.",
    )
_add_metric(
    "tourismSeasonality",
    "numeratore_denominatore",
    AVAILABLE,
    "La banca dati regionale diffonde le presenze mensili e annuali necessarie a ricostruire il numeratore dei tre mesi principali e il denominatore delle presenze annue.",
    "https://www.regione.toscana.it/statistiche/banca-dati-turismo",
)
_add_metric(
    "foreignTourismShare",
    "numeratore_denominatore",
    AVAILABLE,
    "La banca dati regionale diffonde le presenze per provenienza e il totale delle presenze, rendendo disponibili numeratore estero e denominatore complessivo della quota.",
    "https://www.regione.toscana.it/statistiche/banca-dati-turismo",
)
_add_metric(
    "tourismAverageStay",
    "numeratore_denominatore",
    AVAILABLE,
    "La banca dati regionale diffonde nello stesso dominio arrivi e presenze, le due componenti della permanenza media.",
    "https://www.regione.toscana.it/statistiche/banca-dati-turismo",
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
