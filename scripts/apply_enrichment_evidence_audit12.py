#!/usr/bin/env python3
"""Estende le evidenze A3.2 della tranche audit-12 senza duplicare il catalogo pubblico."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "apply_enrichment_evidence_audit10.py"

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
        raise RuntimeError(f"A3.2 audit-12: dimensione già definita: {profile_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


def _add_metric(metric_id: str, dimension: str, state: str, evidence: str, reference: str = "") -> None:
    dimensions = METRIC_EVIDENCE.setdefault(metric_id, {})
    if dimension in dimensions:
        raise RuntimeError(f"A3.2 audit-12: override già definito: {metric_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


# MIT / SID: il catalogo open data 2026 pubblica record geolocalizzati delle
# concessioni, canone dovuto per l'anno in corso, estensione temporale e frequenza
# di aggiornamento irregolare. Il catalogo conserva inoltre snapshot ufficiali
# 2018, 2021, 2022 e 2026, quindi lo storico e benchmark territoriali sono
# ricostruibili, ma non esiste una frequenza infra-annuale regolare né una misura
# normalizzata equivalente pubblicata dalla fonte.
MIT_SID_REF = "https://dati.mit.gov.it/catalog/dataset/concessioni-demaniali-marittime-a-agosto-2026"
MIT_SID_CATALOG_REF = "https://dati.mit.gov.it/catalog/dataset/?q=concessioni%20demaniali%20marittime"
_add_profile(
    "mit-sid-demanio-irregular",
    "serie_storica",
    AVAILABLE,
    "Il catalogo MIT conserva snapshot ufficiali delle concessioni demaniali marittime in più anni (almeno 2018, 2021, 2022 e 2026), permettendo di ricostruire l'evoluzione sia del numero di concessioni sia dei canoni dovuti.",
    MIT_SID_CATALOG_REF,
)
_add_profile(
    "mit-sid-demanio-irregular",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Il dataset SID è nazionale e geolocalizzato; i record possono quindi essere aggregati per Toscana e Italia per costruire benchmark territoriali coerenti.",
    MIT_SID_REF,
)
_add_profile(
    "mit-sid-demanio-irregular",
    "assoluto_normalizzato",
    UNAVAILABLE,
    "La fonte MIT pubblica consistenze delle concessioni e valore del canone dovuto, ma non una misura normalizzata equivalente (per abitante, costa o altra base territoriale) appartenente allo stesso dataset.",
    MIT_SID_REF,
)
_add_profile(
    "mit-sid-demanio-irregular",
    "frequenza_infra_annuale",
    UNAVAILABLE,
    "Il catalogo MIT dichiara esplicitamente frequenza di aggiornamento 'Irregolare'; non è disponibile una serie mensile, trimestrale o semestrale regolare compatibile con questa dimensione.",
    MIT_SID_REF,
)
for metric_id in ("maritimeConcessions", "maritimeConcessionFeesDue"):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica descrive concessioni demaniali o importi amministrativi, non persone da disaggregare per sesso.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica descrive concessioni demaniali o importi amministrativi, non persone da disaggregare per classi di età.",
    )
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        NOT_APPLICABLE,
        "La metrica è una consistenza o una somma di canoni e non è definita come rapporto, quota o tasso con numeratore e denominatore omogenei.",
    )


# MEF / Dipartimento Finanze: gli open data IRPEF 2025 (a.i. 2024) espongono
# classificazioni ufficiali per sesso e classi di età, comprese le variabili di
# reddito e le caratteristiche dei pensionati. Usiamo override metric-specific e
# non estendiamo l'evidenza al rapporto contribuenti/popolazione adulta, che usa un
# denominatore demografico esterno alla fonte MEF.
MEF_IRPEF_REF = "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes"
for metric_id in ("income", "incomeDistribution", "incomeSourceProfile", "pensionIncomeShare"):
    _add_metric(
        metric_id,
        "sesso",
        AVAILABLE,
        "Gli open data IRPEF del Dipartimento delle Finanze pubblicano classificazioni per sesso con numero di contribuenti e variabili reddituali; l'arricchimento è quindi disponibile alla fonte ma non materializzato in questa metrica.",
        MEF_IRPEF_REF,
    )
    _add_metric(
        metric_id,
        "eta",
        AVAILABLE,
        "Gli open data IRPEF del Dipartimento delle Finanze pubblicano classificazioni per classi di età con numero di contribuenti e variabili reddituali; l'arricchimento è quindi disponibile alla fonte ma non materializzato in questa metrica.",
        MEF_IRPEF_REF,
    )


# 7° Censimento Agricoltura: sesso ed età sono caratteristiche esplicite del capo
# azienda e sono direttamente pertinenti alla metrica di ricambio/leadership.
AGRI_REF = "https://www.istat.it/statistiche-per-temi/censimenti/agricoltura/7-censimento-generale/risultati/"
AGRI_AGE_REF = "https://www.istat.it/tavole-di-dati/7-censimento-generale-dellagricoltura-dati-per-eta-del-capo-azienda-anno-2020/"
_add_metric(
    "agriculturalRenewalAndLeadership",
    "sesso",
    AVAILABLE,
    "Il 7° Censimento Agricoltura diffonde il profilo dei capi azienda anche per genere; questa dimensione è direttamente pertinente alla lettura della leadership agricola.",
    AGRI_REF,
)
_add_metric(
    "agriculturalRenewalAndLeadership",
    "eta",
    AVAILABLE,
    "Istat pubblica tavole dedicate all'età del capo azienda e al ricambio generazionale, incluse classi <=40 anni e oltre 40 anni; la dimensione è direttamente pertinente alla metrica.",
    AGRI_AGE_REF,
)


def main() -> None:
    ns["main"]()


if __name__ == "__main__":
    main()
