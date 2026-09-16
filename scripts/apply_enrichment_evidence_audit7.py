#!/usr/bin/env python3
"""Estende le evidenze A3.2 della tranche audit-7 senza duplicare il catalogo pubblico."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "apply_enrichment_evidence_audit6.py"

ns = runpy.run_path(str(BASE))
AVAILABLE = ns["AVAILABLE"]
UNAVAILABLE = ns["UNAVAILABLE"]
NOT_APPLICABLE = ns["NOT_APPLICABLE"]
EVIDENCE = ns["EVIDENCE"]
METRIC_EVIDENCE = ns["METRIC_EVIDENCE"]


def _annotation(state: str, evidence: str, source_reference: str = "") -> dict:
    item = {"state": state, "evidence": evidence}
    if source_reference:
        item["sourceReference"] = source_reference
    return item


def _add_profile(profile_id: str, dimension: str, state: str, evidence: str, reference: str) -> None:
    dimensions = EVIDENCE.setdefault(profile_id, {})
    if dimension in dimensions:
        raise RuntimeError(f"A3.2 audit-7: dimensione già definita: {profile_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


def _add_metric(metric_id: str, dimension: str, state: str, evidence: str, reference: str = "") -> None:
    dimensions = METRIC_EVIDENCE.setdefault(metric_id, {})
    if dimension in dimensions:
        raise RuntimeError(f"A3.2 audit-7: override già definito: {metric_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


# AGCOM Broadband Map: la reportistica è aggiornata per trimestri, pubblica
# conteggi di famiglie raggiunte/non raggiunte insieme alle percentuali e usa
# lo stesso perimetro nazionale/regionale/comunale.
_add_profile(
    "agcom-quarterly",
    "frequenza_infra_annuale",
    AVAILABLE,
    "La Broadband Map AGCOM pubblica aggiornamenti e rapporti riferiti ai singoli trimestri, rendendo disponibile una frequenza infra-annuale omogenea.",
    "https://geo.agcom.it/reportistica/",
)
for metric_id in (
    "ftthCoverageDesi",
    "ftthReachedHouseholds",
    "ftthUnreachedHouseholds",
    "ftthCoverage20m",
):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica misura copertura di rete o famiglie raggiunte dalla rete; il sesso delle persone non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica misura copertura di rete o famiglie raggiunte dalla rete; l'età delle persone non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "assoluto_normalizzato",
        AVAILABLE,
        "I rapporti Broadband Map pubblicano nello stesso quadro i conteggi assoluti delle famiglie raggiunte/non raggiunte e le corrispondenti percentuali di copertura.",
        "https://geo.agcom.it/reportistica/",
    )
for metric_id in ("ftthCoverageDesi", "ftthCoverage20m"):
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        AVAILABLE,
        "La reportistica AGCOM espone famiglie raggiunte e totale delle famiglie, componenti necessarie a ricostruire la percentuale di copertura.",
        "https://geo.agcom.it/reportistica/",
    )
for metric_id in ("ftthReachedHouseholds", "ftthUnreachedHouseholds"):
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        NOT_APPLICABLE,
        "La metrica è un conteggio di famiglie e non è definita come rapporto, tasso o quota.",
    )


# GTFS Toscana: il feed usa uno standard unico per corse, fermate e calendario
# sull'intera regione, consentendo un benchmark regionale coerente.
_add_profile(
    "regione-toscana-gtfs-scheduled",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Il dataset GTFS regionale copre treni, traghetti, tram e autobus nell'intera Toscana con lo stesso standard, rendendo ricostruibile un benchmark regionale coerente.",
    "https://dati.toscana.it/dataset/rt-oraritb",
)
for metric_id in ("scheduledTplTripsPer1000", "activeTplAccessPoints", "tplServiceSpan"):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica descrive l'offerta programmata di trasporto o i punti di accesso al servizio; il sesso non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica descrive l'offerta programmata di trasporto o i punti di accesso al servizio; l'età non è una dimensione semantica dell'oggetto misurato.",
    )
_add_metric(
    "tplServiceSpan",
    "assoluto_normalizzato",
    NOT_APPLICABLE,
    "L'ampiezza giornaliera del servizio è una durata oraria e non ha una forma assoluta/normalizzata semanticamente equivalente.",
)
_add_metric(
    "tplServiceSpan",
    "numeratore_denominatore",
    NOT_APPLICABLE,
    "L'ampiezza giornaliera del servizio è una durata e non un rapporto con numeratore e denominatore.",
)


# ISPRA consumo di suolo: il repository ufficiale pubblica serie storiche e
# indicatori annuali dal livello nazionale a quello comunale, sia in ettari sia
# in percentuale/pro capite.
for dimension, state, evidence in (
    ("serie_storica", AVAILABLE, "ISPRA mette a disposizione la serie storica completa della cartografia e degli indicatori sul consumo di suolo."),
    ("dettaglio_territoriale", AVAILABLE, "Gli indicatori ISPRA sono scaricabili per ogni livello amministrativo, dal nazionale al comunale."),
    ("benchmark_toscana_italia", AVAILABLE, "La stessa base ISPRA calcola gli indicatori a livello nazionale, regionale, provinciale e comunale, consentendo confronti Toscana/Italia."),
    ("assoluto_normalizzato", AVAILABLE, "ISPRA pubblica consumo di suolo in ettari e percentuale e rende disponibili anche indicatori pro capite."),
    ("frequenza_infra_annuale", UNAVAILABLE, "Il monitoraggio ufficiale pubblica gli indicatori per ogni anno; non è diffusa una serie infra-annuale equivalente delle stesse misure."),
):
    _add_profile(
        "ispra-consumo-suolo-2024",
        dimension,
        state,
        evidence,
        "https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/suolo/il-consumo-di-suolo/i-dati-sul-consumo-di-suolo",
    )
for metric_id in ("landUse", "landUseChange"):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica descrive una trasformazione fisica del territorio; il sesso non è una dimensione semantica del fenomeno.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica descrive una trasformazione fisica del territorio; l'età non è una dimensione semantica del fenomeno.",
    )
_add_metric(
    "landUse",
    "numeratore_denominatore",
    AVAILABLE,
    "ISPRA pubblica superficie consumata in ettari e percentuale sulla superficie territoriale, rendendo disponibili le componenti del rapporto.",
    "https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/suolo/il-consumo-di-suolo/i-dati-sul-consumo-di-suolo",
)
_add_metric(
    "landUseChange",
    "numeratore_denominatore",
    NOT_APPLICABLE,
    "La metrica pubblicata è la variazione annuale in ettari e non è definita come rapporto, tasso o quota.",
)
_add_metric(
    "landUseChange",
    "categorie_specifiche",
    AVAILABLE,
    "ISPRA distingue consumo di suolo e consumo di suolo netto e pubblica più indicatori della trasformazione annuale.",
    "https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/suolo/il-consumo-di-suolo/i-dati-sul-consumo-di-suolo",
)


# ACI/Istat parco veicolare: serie annuali, confronti territoriali, conteggi e
# indicatori per abitante, oltre alle classificazioni ambientali dei veicoli.
for dimension, state, evidence in (
    ("serie_storica", AVAILABLE, "Istat pubblica gli indicatori del parco veicolare su annualità consecutive e documenta l'evoluzione temporale delle misure."),
    ("dettaglio_territoriale", AVAILABLE, "Gli indicatori sono diffusi per Comuni e aggregazioni territoriali, con dettaglio almeno comunale."),
    ("benchmark_toscana_italia", AVAILABLE, "La pubblicazione usa la stessa definizione per Italia, ripartizioni territoriali e Comuni, consentendo benchmark coerenti."),
    ("assoluto_normalizzato", AVAILABLE, "La fonte combina consistenze del parco e indicatori normalizzati per popolazione o in quota percentuale."),
    ("frequenza_infra_annuale", UNAVAILABLE, "Il parco veicolare è pubblicato con periodo di riferimento annuale; non è diffusa una serie infra-annuale equivalente."),
    ("categorie_specifiche", AVAILABLE, "La fonte distingue classi emissive, alimentazioni e altre caratteristiche del parco veicolare."),
):
    _add_profile(
        "aci-istat-annual",
        dimension,
        state,
        evidence,
        "https://www.istat.it/comunicato-stampa/indicatori-del-parco-veicolare-anno-2024/",
    )
for metric_id in ("motorization", "pollutingCars"):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica descrive il parco autovetture; il sesso delle persone non è una dimensione semantica del veicolo contato.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica descrive il parco autovetture; l'età delle persone non è una dimensione semantica del veicolo contato.",
    )
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        AVAILABLE,
        "La fonte rende disponibili le consistenze del parco e le basi necessarie a ricostruire il rapporto per abitante o la quota delle classi emissive considerate.",
        "https://www.istat.it/comunicato-stampa/indicatori-del-parco-veicolare-anno-2024/",
    )


# PNRR Toscana: open data mensili, coordinate geografiche e stato fisico,
# finanziario e procedurale dei progetti.
for dimension, evidence in (
    ("dettaglio_territoriale", "Il dataset PNRR regionale include coordinate geografiche dei progetti, offrendo dettaglio territoriale inferiore al Comune."),
    ("benchmark_toscana_italia", "Il dataset applica lo stesso tracciato ai progetti dell'intera Toscana, permettendo aggregazioni e benchmark regionali coerenti."),
    ("frequenza_infra_annuale", "Regione Toscana dichiara una frequenza di aggiornamento di norma mensile per il dataset PNRR."),
    ("categorie_specifiche", "Il dataset distingue caratteristiche e stato di avanzamento fisico, finanziario e procedurale dei progetti."),
):
    _add_profile(
        "regione-toscana-pnrr-monthly",
        dimension,
        AVAILABLE,
        evidence,
        "https://dati.toscana.it/dataset/regione-toscana-pnrr",
    )
for metric_id in ("pnrrFunding", "pnrrConcluded"):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica descrive progetti o finanziamenti PNRR; il sesso non è una dimensione semantica del progetto finanziato.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica descrive progetti o finanziamenti PNRR; l'età non è una dimensione semantica del progetto finanziato.",
    )
_add_metric(
    "pnrrConcluded",
    "assoluto_normalizzato",
    AVAILABLE,
    "Il dataset pubblica i singoli progetti e il relativo stato procedurale, permettendo di affiancare al valore percentuale il conteggio assoluto dei progetti conclusi.",
    "https://dati.toscana.it/dataset/regione-toscana-pnrr",
)
_add_metric(
    "pnrrConcluded",
    "numeratore_denominatore",
    AVAILABLE,
    "Lo stato dei singoli progetti consente di ricostruire il numero di progetti conclusi e il totale dei progetti del perimetro.",
    "https://dati.toscana.it/dataset/regione-toscana-pnrr",
)


# Piani delle attività di bonifica: Regione Toscana approva annualmente i piani
# di tutti i sei Consorzi e rende consultabile il dettaglio cartografico dei lavori.
for dimension, evidence in (
    ("dettaglio_territoriale", "Il geoportale regionale dei Piani delle attività mostra i lavori con dettaglio crescente alla scala cartografica, oltre il livello comunale."),
    ("benchmark_toscana_italia", "La Regione approva con lo stesso quadro normativo i Piani annuali dei sei Consorzi di bonifica toscani, consentendo un confronto regionale coerente."),
    ("categorie_specifiche", "I Piani distinguono attività e interventi di manutenzione del reticolo e delle opere di bonifica secondo il programma annuale."),
):
    _add_profile(
        "regione-toscana-pab-annual",
        dimension,
        AVAILABLE,
        evidence,
        "https://www.regione.toscana.it/-/manutenzione-del-reticolo-idrografico-piani-delle-attivit%C3%A0-dei-consorzi-di-bonifica",
    )
for metric_id in ("pabProgrammedInterventions", "pabProgrammedMaintenanceValue"):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica descrive interventi di manutenzione idraulica programmati o il loro valore economico; il sesso non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica descrive interventi di manutenzione idraulica programmati o il loro valore economico; l'età non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        NOT_APPLICABLE,
        "La metrica è un conteggio di interventi o un valore economico programmato e non è definita come rapporto, tasso o quota.",
    )


# Ministero della Salute: il profilo è misto, quindi le evidenze sono metric-specific.
for dimension, state, evidence in (
    ("serie_storica", AVAILABLE, "Il Ministero pubblica le strutture di ricovero per anno di riferimento e rende disponibili annualità consecutive a partire dal 2010."),
    ("dettaglio_territoriale", AVAILABLE, "Il dataset delle strutture riporta indirizzo, Comune e Provincia per ciascuna struttura."),
    ("benchmark_toscana_italia", AVAILABLE, "Il dataset nazionale usa lo stesso tracciato per le strutture di tutte le Regioni, consentendo aggregazioni territoriali coerenti."),
    ("frequenza_infra_annuale", UNAVAILABLE, "Il dataset delle strutture di ricovero ha frequenza di aggiornamento annuale e non diffonde una serie infra-annuale equivalente."),
    ("categorie_specifiche", AVAILABLE, "Il Ministero distingue le strutture per tipologia, incluse Aziende Ospedaliere, Aziende Ospedaliere Universitarie e IRCCS pubblici."),
):
    _add_metric(
        "hospitals",
        dimension,
        state,
        evidence,
        "https://www.dati.salute.gov.it/it/dataset/aziende-ospedaliere-aziende-ospedaliere-universitarie-e-irccs-pubblici-anche-costituiti/",
    )
for dimension in ("sesso", "eta"):
    _add_metric(
        "hospitals",
        dimension,
        NOT_APPLICABLE,
        "La metrica conta strutture ospedaliere; sesso ed età delle persone non sono dimensioni semantiche della struttura fisica contata.",
    )
for dimension, evidence in (
    ("dettaglio_territoriale", "L'open data Farmacie riporta indirizzo completo, frazione, Comune, Provincia e Regione per ogni esercizio."),
    ("benchmark_toscana_italia", "Il dataset nazionale contiene l'elenco completo delle farmacie e consente aggregazioni coerenti per Toscana e Italia."),
    ("frequenza_infra_annuale", "Il Ministero dichiara per il dataset Farmacie una frequenza di aggiornamento giornaliera."),
    ("categorie_specifiche", "Il dataset comprende farmacie, succursali, dispensari e dispensari stagionali come tipologie distinguibili."),
):
    _add_metric(
        "pharmaciesPer1000",
        dimension,
        AVAILABLE,
        evidence,
        "https://www.dati.salute.gov.it/it/dataset/farmacie/",
    )
for dimension in ("sesso", "eta"):
    _add_metric(
        "pharmaciesPer1000",
        dimension,
        NOT_APPLICABLE,
        "La metrica misura la presenza territoriale di farmacie; sesso ed età delle persone non sono dimensioni semantiche dell'esercizio contato.",
    )


# Censimento permanente: per le metriche di rapporto il data warehouse e la
# documentazione Istat espongono le consistenze che costituiscono i rapporti.
CENSUS_ABSOLUTE_NORMALIZED = (
    "oldAgeIndex",
    "employmentRate",
    "unemploymentRate",
    "activityRate",
    "femaleEmploymentRate",
    "maleEmploymentRate",
    "diplomaPlus",
    "tertiary",
    "vacantHomes",
    "housingStockPer1000",
    "nonOccupiedHomesPer1000",
    "singleHouseholds",
    "householdSize",
    "cohabitingHouseholds",
)
for metric_id in CENSUS_ABSOLUTE_NORMALIZED:
    _add_metric(
        metric_id,
        "assoluto_normalizzato",
        AVAILABLE,
        "Istat documenta il rapporto e rende disponibili nel sistema censuario le consistenze di popolazione, occupati, famiglie o abitazioni che permettono di affiancare valori assoluti all'indicatore normalizzato.",
        "https://ottomilacensus.istat.it/documentazione/",
    )
_add_metric(
    "employmentGenderGap",
    "assoluto_normalizzato",
    NOT_APPLICABLE,
    "La metrica è lo scarto in punti percentuali fra due tassi; non esiste una forma assoluta semanticamente equivalente dello stesso divario.",
)
CENSUS_NUMERATOR_DENOMINATOR = (
    "cohabitingHouseholds",
    "femaleEmploymentRate",
    "householdSize",
    "housingStockPer1000",
    "maleEmploymentRate",
    "nonOccupiedHomesPer1000",
    "oldAgeIndex",
    "singleHouseholds",
    "vacantHomes",
)
for metric_id in CENSUS_NUMERATOR_DENOMINATOR:
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        AVAILABLE,
        "La documentazione censuaria Istat definisce l'indicatore come rapporto tra consistenze pubblicate nel data warehouse, rendendo disponibili numeratore e denominatore.",
        "https://ottomilacensus.istat.it/documentazione/",
    )
_add_metric(
    "employmentGenderGap",
    "numeratore_denominatore",
    NOT_APPLICABLE,
    "Il divario occupazionale di genere è la differenza tra due tassi già calcolati e non un singolo rapporto con numeratore e denominatore.",
)


# Fiscalità locale MEF: gli archivi ufficiali sono annuali, nazionali e
# organizzati per Regione/Comune; le due metriche sono scenari teorici in euro.
for dimension, evidence in (
    ("serie_storica", "Il portale della fiscalità locale conserva archivi distinti per anno delle delibere e dei regolamenti comunali."),
    ("dettaglio_territoriale", "Gli archivi MEF sono organizzati per Regione e Comune e rendono consultabili gli atti del singolo ente."),
    ("benchmark_toscana_italia", "Lo stesso archivio copre i Comuni di tutte le Regioni, permettendo confronti coerenti fra Toscana e resto d'Italia."),
    ("categorie_specifiche", "Gli atti e i prospetti distinguono tributi, aliquote, tariffe e categorie di applicazione previste dalla fiscalità comunale."),
):
    _add_profile(
        "mef-municipal-tax-annual",
        dimension,
        AVAILABLE,
        evidence,
        "https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/",
    )
for metric_id in ("tariStandardHousehold", "municipalImuStandard"):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica è un importo tributario teorico standardizzato sull'immobile o sull'utenza; il sesso non è una dimensione semantica dell'oggetto tassato.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica è un importo tributario teorico standardizzato sull'immobile o sull'utenza; l'età delle persone non è una dimensione semantica dell'oggetto tassato.",
    )
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        NOT_APPLICABLE,
        "La metrica è un importo annuo teorico in euro e non è definita come rapporto, tasso o quota con numeratore e denominatore.",
    )


def main() -> None:
    ns["main"]()


if __name__ == "__main__":
    main()
