#!/usr/bin/env python3
"""Estende le evidenze A3.2 della tranche audit-15 senza duplicare il catalogo pubblico."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "apply_enrichment_evidence_audit14.py"

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
        raise RuntimeError(f"A3.2 audit-15: dimensione già definita: {profile_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


def _add_metric(metric_id: str, dimension: str, state: str, evidence: str, reference: str = "") -> None:
    dimensions = METRIC_EVIDENCE.setdefault(metric_id, {})
    if dimension in dimensions:
        raise RuntimeError(f"A3.2 audit-15: override già definito: {metric_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


# MIMIT — prezzi carburanti.
# Il Ministero pubblica il dataset quotidiano e un archivio storico trimestrale
# dei prezzi dalle estrazioni 2015 in avanti; l'anagrafica degli impianti contiene
# gli elementi territoriali necessari alle aggregazioni. Il prezzo e' gia' una
# misura unitaria euro/litro o euro/kg, non un conteggio da normalizzare.
MIMIT_FUEL_REF = "https://www.mimit.gov.it/it/open-data/elenco-dataset/carburanti-prezzi-praticati-e-anagrafica-degli-impianti"
MIMIT_FUEL_ARCHIVE_REF = "https://www.mimit.gov.it/it/open-data/elenco-dataset/carburanti-archivio-prezzi"
_add_profile(
    "mimit-fuel-daily",
    "serie_storica",
    AVAILABLE,
    "Il MIMIT pubblica un archivio storico dei prezzi praticati, organizzato per trimestre, con estrazioni disponibili dal 2015; una serie temporale omogenea puo' quindi essere ricostruita dalla fonte ufficiale.",
    MIMIT_FUEL_ARCHIVE_REF,
)
_add_profile(
    "mimit-fuel-daily",
    "dettaglio_territoriale",
    AVAILABLE,
    "Il dataset ufficiale abbina i prezzi all'anagrafica degli impianti; l'anagrafica contiene localizzazione e identificativo dell'impianto, consentendo aggregazioni territoriali piu' fini del Comune.",
    MIMIT_FUEL_REF,
)
_add_profile(
    "mimit-fuel-daily",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Il dataset MIMIT copre gli impianti sul territorio nazionale; i prezzi possono quindi essere aggregati in modo coerente per Toscana e Italia.",
    MIMIT_FUEL_REF,
)
for dimension, evidence in (
    ("sesso", "La metrica descrive prezzi praticati da impianti di distribuzione; il sesso delle persone non e' una dimensione semantica del prezzo."),
    ("eta", "La metrica descrive prezzi praticati da impianti di distribuzione; l'eta' delle persone non e' una dimensione semantica del prezzo."),
    ("assoluto_normalizzato", "Il prezzo e' gia' una misura unitaria espressa in euro per litro o euro per kg; non esiste una coppia assoluto/normalizzato semanticamente equivalente della stessa metrica."),
    ("numeratore_denominatore", "Il prezzo unitario pubblicato e' una misura osservata e non un rapporto statistico ricostruito da numeratore e denominatore territoriali."),
):
    _add_metric("fuelPrices", dimension, NOT_APPLICABLE, evidence)


# Istat — principali statistiche geografiche sui Comuni.
# Superficie e quota altimetrica sono caratteristiche fisiche; la densita'
# pubblicata da OV deriva invece da popolazione/superficie e la pagina geografica
# Istat non offre disaggregazioni della densita' per sesso o classe di eta'.
ISTAT_GEO_REF = "https://www.istat.it/classificazione/principali-statistiche-geografiche-sui-comuni/"
_add_metric(
    "municipalSurface",
    "assoluto_normalizzato",
    NOT_APPLICABLE,
    "La superficie comunale e' una misura fisica in kmq; non ha una coppia assoluto/normalizzato della stessa grandezza geografica.",
)
for dimension, evidence in (
    ("sesso", "La fonte geografica Istat pubblica superficie e classificazioni territoriali, non una densita' comunale disaggregata per sesso."),
    ("eta", "La fonte geografica Istat pubblica superficie e classificazioni territoriali, non una densita' comunale disaggregata per classi di eta'."),
):
    _add_metric("populationDensity", dimension, UNAVAILABLE, evidence, ISTAT_GEO_REF)
_add_metric(
    "populationDensity",
    "assoluto_normalizzato",
    NOT_APPLICABLE,
    "La densita' e' gia' una misura normalizzata per superficie; l'assoluto corrispondente e' la popolazione, che appartiene a una fonte demografica distinta e non alla stessa metrica geografica.",
)
_add_metric(
    "altitudeProfile",
    "serie_storica",
    NOT_APPLICABLE,
    "Il profilo altimetrico comunale descrive una caratteristica fisica del territorio e non un fenomeno osservato periodicamente nel tempo.",
)
_add_metric(
    "altitudeProfile",
    "assoluto_normalizzato",
    NOT_APPLICABLE,
    "Quota minima, media e massima sono misure fisiche in metri; non esiste una coppia assoluto/normalizzato semanticamente equivalente.",
)


# Istat — geografie funzionali e classificazioni territoriali.
# Le classificazioni sono diffuse a livello comunale e hanno edizioni storiche
# confrontabili (es. SLL dal 1981, FUA/DEGURBA 2011-2021). La linea costiera e le
# classi di comune costiero sono anch'esse territorialmente dettagliate.
ISTAT_FUNCTIONAL_REF = "https://www.istat.it/comunicato-stampa/geografie-funzionali-per-lanalisi-territoriale/"
ISTAT_SLL_REF = "https://www.istat.it/comunicato-stampa/la-nuova-geografia-dei-sistemi-locali-del-lavoro-anno-2021/"
ISTAT_COAST_REF = ISTAT_GEO_REF
_add_metric(
    "territorialClassification",
    "serie_storica",
    AVAILABLE,
    "Istat documenta l'evoluzione dei Sistemi locali del lavoro dal 1981 e diffonde aggiornamenti delle geografie funzionali e del grado di urbanizzazione; il confronto tra edizioni ufficiali e' quindi disponibile.",
    ISTAT_SLL_REF,
)
_add_metric(
    "territorialClassification",
    "dettaglio_territoriale",
    AVAILABLE,
    "Le geografie funzionali sono diffuse con tavole e file geografici basati sulla geografia comunale e assegnano le classificazioni ai singoli Comuni.",
    ISTAT_FUNCTIONAL_REF,
)
_add_metric(
    "territorialClassification",
    "assoluto_normalizzato",
    NOT_APPLICABLE,
    "La metrica e' una classificazione categoriale del territorio e non una misura quantitativa con forma assoluta e normalizzata.",
)
_add_metric(
    "statisticalCoastlineLength",
    "dettaglio_territoriale",
    AVAILABLE,
    "Istat pubblica le principali statistiche geografiche e la classificazione dei Comuni costieri a livello comunale, consentendo dettaglio territoriale coerente.",
    ISTAT_COAST_REF,
)
_add_metric(
    "statisticalCoastlineLength",
    "assoluto_normalizzato",
    UNAVAILABLE,
    "La fonte Istat pubblica la lunghezza/statistica territoriale e le classificazioni costiere, ma non una misura normalizzata equivalente della lunghezza di costa per popolazione o superficie.",
    ISTAT_COAST_REF,
)
_add_metric(
    "statisticalCoastlineLength",
    "categorie_specifiche",
    AVAILABLE,
    "Le statistiche geografiche Istat distinguono i Comuni e le zone costiere attraverso classificazioni territoriali ufficiali, utilizzabili come categorie specifiche della lettura costiera.",
    ISTAT_COAST_REF,
)
# La serie storica della lunghezza statistica della costa resta aperta: le
# edizioni delle classificazioni non dimostrano una serie omogenea della misura.


# Regione Toscana — Piani delle Attivita' di Bonifica.
# La Giunta approva i PAB annualmente; gli allegati ufficiali forniscono numero e
# valore programmato degli interventi. Non esiste nella fonte una normalizzazione
# territoriale omogenea, ne' una frequenza infra-annuale della stessa grandezza.
PAB_REF = "https://www.regione.toscana.it/-/manutenzione-del-reticolo-idrografico-piani-delle-attivit%C3%A0-dei-consorzi-di-bonifica"
_add_profile(
    "regione-toscana-pab-annual",
    "serie_storica",
    AVAILABLE,
    "I Piani delle Attivita' di Bonifica sono approvati annualmente dalla Giunta regionale; le diverse annualita' ufficiali consentono di ricostruire una serie dei valori programmati.",
    PAB_REF,
)
_add_profile(
    "regione-toscana-pab-annual",
    "assoluto_normalizzato",
    UNAVAILABLE,
    "Gli allegati PAB pubblicano interventi e importi programmati ma non una misura normalizzata equivalente per abitante, superficie o lunghezza del reticolo.",
    PAB_REF,
)
_add_profile(
    "regione-toscana-pab-annual",
    "frequenza_infra_annuale",
    UNAVAILABLE,
    "Il PAB e' approvato su base annuale; la fonte non pubblica osservazioni mensili, trimestrali o semestrali omogenee del numero o valore programmato.",
    PAB_REF,
)


# Regione Toscana — GTFS del trasporto pubblico programmato.
# Il dataset e' aggiornato continuativamente ma rappresenta il servizio corrente:
# non espone una serie storica ufficiale degli snapshot. Per le metriche OV per
# 1.000 abitanti, il feed fornisce il numeratore ma non il denominatore demografico.
GTFS_REF = "https://dati.toscana.it/dataset/rt-oraritb"
_add_profile(
    "regione-toscana-gtfs-scheduled",
    "serie_storica",
    UNAVAILABLE,
    "Il dataset GTFS ufficiale e' in continuo aggiornamento e pubblica corse, fermate, calendari e orari del servizio programmato corrente; non espone un archivio storico omogeneo degli snapshot del feed.",
    GTFS_REF,
)
for metric_id in ("scheduledTplTripsPer1000", "activeTplAccessPoints"):
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        UNAVAILABLE,
        "Il GTFS fornisce il numeratore operativo (corse o punti di accesso), ma non la popolazione residente usata da OV come denominatore della normalizzazione per 1.000 abitanti.",
        GTFS_REF,
    )


# Ministero del Lavoro — RUNTS.
# Il registro nazionale permette ricerca per Comune e sezione e pubblica liste
# datate degli enti iscritti/cancellati. E' un registro corrente, senza archivio
# storico ufficiale equivalente; non pubblica normalizzazioni per popolazione.
RUNTS_REF = "https://servizi.lavoro.gov.it/runts/it-it/Ricerca-enti"
RUNTS_LIST_REF = "https://servizi.lavoro.gov.it/runts/it-it/Lista-enti"
_add_profile(
    "runts-continuous",
    "serie_storica",
    UNAVAILABLE,
    "Il RUNTS pubblica lo stato corrente del registro e liste datate degli enti, ma non un archivio storico omogeneo degli snapshot del registro da cui ricostruire una serie temporale ufficiale.",
    RUNTS_LIST_REF,
)
_add_profile(
    "runts-continuous",
    "dettaglio_territoriale",
    AVAILABLE,
    "La ricerca pubblica RUNTS consente di filtrare gli enti per Comune e di consultare la sezione/tipologia dell'ente.",
    RUNTS_REF,
)
_add_profile(
    "runts-continuous",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Il RUNTS e' un registro nazionale; le liste ufficiali degli enti consentono aggregazioni coerenti per Toscana e Italia.",
    RUNTS_LIST_REF,
)
_add_profile(
    "runts-continuous",
    "assoluto_normalizzato",
    UNAVAILABLE,
    "Il registro pubblica enti e relative informazioni amministrative ma non una misura normalizzata equivalente del numero di enti per popolazione o altra base territoriale.",
    RUNTS_REF,
)
_add_profile(
    "runts-continuous",
    "frequenza_infra_annuale",
    AVAILABLE,
    "Le liste pubbliche RUNTS sono aggiornate e datate nel corso dell'anno; il registro e' operativo continuativamente, quindi la dimensione infra-annuale e' disponibile alla fonte.",
    RUNTS_LIST_REF,
)
for dimension, evidence in (
    ("sesso", "La metrica conta enti del Terzo settore iscritti al registro; il sesso delle persone non e' una dimensione semantica del conteggio di enti."),
    ("eta", "La metrica conta enti del Terzo settore iscritti al registro; l'eta' delle persone non e' una dimensione semantica del conteggio di enti."),
    ("numeratore_denominatore", "La metrica e' un conteggio di enti iscritti e non e' definita come rapporto, quota o tasso."),
):
    _add_metric("thirdSector", dimension, NOT_APPLICABLE, evidence)


def main() -> None:
    ns["main"]()


if __name__ == "__main__":
    main()
