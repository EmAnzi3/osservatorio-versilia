#!/usr/bin/env python3
"""Estende le evidenze A3.2 della tranche audit-14 senza duplicare il catalogo pubblico."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "apply_enrichment_evidence_audit13.py"

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
        raise RuntimeError(f"A3.2 audit-14: dimensione già definita: {profile_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


def _add_metric(metric_id: str, dimension: str, state: str, evidence: str, reference: str = "") -> None:
    dimensions = METRIC_EVIDENCE.setdefault(metric_id, {})
    if dimension in dimensions:
        raise RuntimeError(f"A3.2 audit-14: override già definito: {metric_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


# PUN — Piattaforma Unica Nazionale dei punti di ricarica.
# La pagina territoriale ufficiale espone storico installazioni, scala
# Regione/Provincia/Comune e classificazione per potenza; la piattaforma è
# nazionale e aggiornata continuativamente. La metrica OV è già normalizzata per
# 1.000 residenti, mentre PUN rende disponibile il conteggio assoluto dei punti.
PUN_REF = "https://www.piattaformaunicanazionale.it/territory-idr"
PUN_MAP_REF = "https://www.piattaformaunicanazionale.it/eDriver"
for dimension, evidence in (
    ("serie_storica", "La pagina territoriale PUN pubblica statistiche sullo storico delle installazioni dei punti di ricarica."),
    ("dettaglio_territoriale", "PUN rende disponibili numero e distribuzione dei punti di ricarica per Regione, Provincia e Comune."),
    ("benchmark_toscana_italia", "La piattaforma copre l'intero territorio nazionale e consente letture territoriali coerenti per Toscana e Italia."),
    ("frequenza_infra_annuale", "PUN è una piattaforma operativa aggiornata continuativamente e, per le colonnine abilitate, espone anche informazioni in tempo reale."),
    ("categorie_specifiche", "Le statistiche PUN classificano le infrastrutture per potenza e la mappa espone ulteriori informazioni tecniche dei punti di ricarica."),
):
    _add_profile("pun-continuous", dimension, AVAILABLE, evidence, PUN_REF if dimension != "frequenza_infra_annuale" else PUN_MAP_REF)
for dimension, state, evidence, reference in (
    ("sesso", NOT_APPLICABLE, "La metrica misura infrastrutture di ricarica; il sesso delle persone non è una dimensione semantica dell'oggetto misurato.", ""),
    ("eta", NOT_APPLICABLE, "La metrica misura infrastrutture di ricarica; l'età delle persone non è una dimensione semantica dell'oggetto misurato.", ""),
    ("assoluto_normalizzato", AVAILABLE, "La metrica OV è espressa ogni 1.000 residenti, mentre PUN rende disponibile il numero assoluto dei punti di ricarica per territorio: la lettura assoluta può quindi essere affiancata a quella normalizzata già pubblicata.", PUN_REF),
):
    _add_metric("evPoints", dimension, state, evidence, reference)
# numeratore_denominatore resta volutamente aperto: il denominatore demografico
# della normalizzazione proviene da una fonte esterna a PUN.


# OpenBDAP / MOP — opere pubbliche.
# Il portale nazionale documenta l'intero ciclo di vita dell'opera, la
# distribuzione territoriale, l'andamento nel tempo e aggiornamenti infra-annuali.
# La metrica OV è pro capite; OpenBDAP fornisce gli importi assoluti sottostanti.
OPENBDAP_REF = "https://openbdap.rgs.mef.gov.it/it/Home/PerimetroInvestimentiPubblici"
OPENBDAP_ANALYZE_REF = "https://openbdap.rgs.mef.gov.it/it/IPU/Analizza"
for dimension, evidence, reference in (
    ("serie_storica", "Il MOP raccoglie informazioni sull'intero ciclo di vita delle opere e OpenBDAP consente di osservarne l'andamento nel tempo.", OPENBDAP_ANALYZE_REF),
    ("dettaglio_territoriale", "OpenBDAP consente di esplorare le opere e la loro distribuzione sul territorio nazionale.", OPENBDAP_ANALYZE_REF),
    ("benchmark_toscana_italia", "Il MOP è un sistema nazionale; il perimetro territoriale consente aggregazioni coerenti per Toscana e Italia.", OPENBDAP_REF),
    ("frequenza_infra_annuale", "L'area Opere Pubbliche viene aggiornata nel corso dell'anno e il portale descrive il quadro come in continuo aggiornamento.", OPENBDAP_REF),
    ("categorie_specifiche", "OpenBDAP espone fase procedurale, fonti di finanziamento e altre classificazioni del ciclo di vita delle opere pubbliche.", OPENBDAP_ANALYZE_REF),
):
    _add_profile("openbdap-continuous", dimension, AVAILABLE, evidence, reference)
for dimension, state, evidence, reference in (
    ("sesso", NOT_APPLICABLE, "La metrica misura valore e monitoraggio di opere pubbliche; il sesso delle persone non è una dimensione semantica dell'oggetto misurato.", ""),
    ("eta", NOT_APPLICABLE, "La metrica misura valore e monitoraggio di opere pubbliche; l'età delle persone non è una dimensione semantica dell'oggetto misurato.", ""),
    ("assoluto_normalizzato", AVAILABLE, "OpenBDAP pubblica gli importi assoluti delle opere monitorate, mentre la metrica OV espone il valore per residente; l'assoluto può quindi essere affiancato alla lettura normalizzata già pubblicata.", OPENBDAP_REF),
):
    _add_metric("publicWorks", dimension, state, evidence, reference)
# numeratore_denominatore resta aperto perché la popolazione residente usata come
# denominatore non appartiene alla fonte OpenBDAP.


# GAIA — qualità dell'acqua potabile.
# Il portale Laboratorio Analisi pubblica per località e semestre parametri,
# unità di misura, valori medi e limiti normativi. Non è una fonte regionale o
# nazionale e le concentrazioni sono misure dirette, non rapporti normalizzati.
GAIA_REF = "https://www.gaia-spa.it/analisiweb_v2/"
_add_profile(
    "gaia-quality-semiannual",
    "dettaglio_territoriale",
    AVAILABLE,
    "Il portale GAIA pubblica le analisi per singola area/località servita, offrendo una granularità inferiore al Comune.",
    GAIA_REF,
)
_add_profile(
    "gaia-quality-semiannual",
    "benchmark_toscana_italia",
    UNAVAILABLE,
    "GAIA pubblica i dati del proprio territorio di servizio e non un dataset omogeneo esteso all'intera Toscana o all'Italia.",
    GAIA_REF,
)
_add_profile(
    "gaia-quality-semiannual",
    "frequenza_infra_annuale",
    AVAILABLE,
    "Il portale indica esplicitamente il semestre di riferimento delle analisi, quindi la dimensione infra-annuale è disponibile.",
    GAIA_REF,
)
_add_profile(
    "gaia-quality-semiannual",
    "categorie_specifiche",
    AVAILABLE,
    "Per ogni località GAIA pubblica molteplici parametri fisico-chimici e microbiologici con unità e limiti normativi distinti.",
    GAIA_REF,
)
for dimension, evidence in (
    ("sesso", "La metrica descrive parametri di qualità dell'acqua; il sesso delle persone non è una dimensione semantica applicabile."),
    ("eta", "La metrica descrive parametri di qualità dell'acqua; l'età delle persone non è una dimensione semantica applicabile."),
    ("assoluto_normalizzato", "Le concentrazioni e gli altri parametri di laboratorio sono misure fisiche dirette; non esiste una coppia assoluto/normalizzato semanticamente equivalente della stessa misura."),
    ("numeratore_denominatore", "I valori di laboratorio pubblicati sono misure dirette e non rapporti, quote o tassi ricostruiti da un numeratore e un denominatore."),
):
    _add_metric("drinkingWaterQuality", dimension, NOT_APPLICABLE, evidence)
# serie_storica resta aperta: la periodicità semestrale non dimostra da sola la
# disponibilità di una serie storica omogenea per ogni località/parametro.


# Consorzio 1 Toscana Nord — PAB / portale manutenzioni.
# Il Consorzio pubblica PAB annuali e, nel portale 2026, dettaglio per Comune,
# corso d'acqua, intervento, stagione, tratto e importo. Il perimetro è consortile,
# non Toscana/Italia, e non esiste una normalizzazione ufficiale dei km-intervento.
CB1_REF = "https://cbtoscananord.it/comunicazione/pmo-manutenzione-mappa-navigabile/"
CB1_PAB_2024_REF = "https://cbtoscananord.it/wp-content/uploads/2024/11/PAB_A.pdf"
_add_profile(
    "cb1-pmo-2026",
    "serie_storica",
    AVAILABLE,
    "Il Consorzio pubblica Piani delle Attività di Bonifica annuali; sono disponibili almeno PAB 2024, PAB 2025 e il portale operativo 2026, consentendo confronti tra annualità ufficiali.",
    CB1_PAB_2024_REF,
)
_add_profile(
    "cb1-pmo-2026",
    "dettaglio_territoriale",
    AVAILABLE,
    "Il portale consente filtri per Comune e mostra corso d'acqua, intervento previsto, stagione, tratto e importo.",
    CB1_REF,
)
_add_profile(
    "cb1-pmo-2026",
    "benchmark_toscana_italia",
    UNAVAILABLE,
    "La fonte copre il comprensorio del Consorzio 1 Toscana Nord e non pubblica un dataset omogeneo per l'intera Toscana o l'Italia.",
    CB1_REF,
)
_add_profile(
    "cb1-pmo-2026",
    "assoluto_normalizzato",
    UNAVAILABLE,
    "Il portale pubblica metri o km-intervento programmati e importi, ma non una misura normalizzata equivalente per superficie, popolazione o lunghezza del reticolo.",
    CB1_REF,
)
_add_profile(
    "cb1-pmo-2026",
    "frequenza_infra_annuale",
    UNAVAILABLE,
    "Il PAB è uno strumento di programmazione annuale; le stagioni di intervento sono categorie del piano e non osservazioni periodiche mensili, trimestrali o semestrali della stessa metrica.",
    CB1_REF,
)
_add_profile(
    "cb1-pmo-2026",
    "categorie_specifiche",
    AVAILABLE,
    "Il portale distingue intervento previsto e stagione di inizio e permette filtri operativi sul piano dei lavori.",
    CB1_REF,
)
for dimension, evidence in (
    ("sesso", "La metrica misura lunghezza di interventi di manutenzione idraulica; il sesso delle persone non è applicabile."),
    ("eta", "La metrica misura lunghezza di interventi di manutenzione idraulica; l'età delle persone non è applicabile."),
    ("numeratore_denominatore", "La metrica è una somma di km-intervento programmati e non è definita come rapporto, quota o tasso."),
):
    _add_metric("pabProgrammedInterventionLength", dimension, NOT_APPLICABLE, evidence)


# Regione Toscana — portale RSA.
# Il portale copre le RSA autorizzate/accreditate/finanziate nel territorio
# regionale e consente ricerca comunale e dettaglio di struttura. Il conteggio OV
# non ha una normalizzazione ufficiale equivalente e l'elenco non costituisce una
# serie infra-annuale regolare.
RSA_REF = "https://www.regione.toscana.it/residenze-sanitarie-assistenziali"
RSA_PORTAL_REF = "https://servizi.toscana.it/RT/RSA/"
_add_profile(
    "regione-toscana-rsa",
    "dettaglio_territoriale",
    AVAILABLE,
    "Il portale RSA Toscana consente la ricerca per Comune e pubblica schede di struttura con indirizzi, servizi e informazioni di disponibilità.",
    RSA_PORTAL_REF,
)
_add_profile(
    "regione-toscana-rsa",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Il portale copre le RSA presenti nel territorio toscano e consente quindi un riferimento regionale coerente rispetto ai conteggi comunali.",
    RSA_REF,
)
_add_profile(
    "regione-toscana-rsa",
    "assoluto_normalizzato",
    UNAVAILABLE,
    "La fonte pubblica strutture e disponibilità di posti ma non una misura normalizzata equivalente del numero di RSA per popolazione o altra base territoriale.",
    RSA_PORTAL_REF,
)
_add_profile(
    "regione-toscana-rsa",
    "frequenza_infra_annuale",
    UNAVAILABLE,
    "L'elenco regionale viene aggiornato operativamente, ma la fonte non pubblica una serie periodica mensile, trimestrale o semestrale del numero di RSA accreditate.",
    RSA_REF,
)
for dimension, evidence in (
    ("sesso", "La metrica conta strutture RSA accreditate; il sesso delle persone non è una dimensione semantica del conteggio di strutture."),
    ("eta", "La metrica conta strutture RSA accreditate; l'età delle persone non è una dimensione semantica del conteggio di strutture."),
    ("numeratore_denominatore", "La metrica è un conteggio di strutture e non è definita come rapporto, quota o tasso."),
):
    _add_metric("accreditedRsaCount", dimension, NOT_APPLICABLE, evidence)
# serie_storica e categorie_specifiche restano aperte: la pagina corrente non
# dimostra una serie storica omogenea né una tassonomia di struttura stabile per
# il conteggio pubblicato da OV.


def main() -> None:
    ns["main"]()


if __name__ == "__main__":
    main()
