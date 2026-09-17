#!/usr/bin/env python3
"""Estende le evidenze A3.2 della tranche audit-10 senza duplicare il catalogo pubblico."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "apply_enrichment_evidence_audit9.py"

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
        raise RuntimeError(f"A3.2 audit-10: dimensione già definita: {profile_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


def _add_metric(metric_id: str, dimension: str, state: str, evidence: str, reference: str = "") -> None:
    dimensions = METRIC_EVIDENCE.setdefault(metric_id, {})
    if dimension in dimensions:
        raise RuntimeError(f"A3.2 audit-10: override già definito: {metric_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


# Istat IFC: indice e componenti sono misure territoriali riferite ai Comuni,
# confrontabili su domini territoriali e rispetto al riferimento nazionale.
FRAGILITY_REF = "https://www.istat.it/comunicato-stampa/la-fragilita-dei-comuni-italiani-anno-2022/"
FRAGILITY_DASH_REF = "https://www.istat.it/comunicato-stampa/aggiornato-indice-di-fragilita-comunale/"
_add_profile(
    "istat-fragility-2022",
    "dettaglio_territoriale",
    AVAILABLE,
    "Istat pubblica l'IFC per tutti i Comuni e la dashboard consente letture per domini territoriali come aree interne e grado di urbanizzazione.",
    FRAGILITY_DASH_REF,
)
_add_profile(
    "istat-fragility-2022",
    "benchmark_toscana_italia",
    AVAILABLE,
    "L'IFC e le sue componenti sono diffusi sull'intero territorio nazionale; la metodologia usa inoltre il valore Italia 2018 come riferimento dell'indice composito.",
    FRAGILITY_DASH_REF,
)
for metric_id in ("municipalFragility", "essentialServicesAccessibility", "lowProductivityEmployment"):
    _add_metric(metric_id, "sesso", NOT_APPLICABLE, "La metrica misura una caratteristica territoriale del Comune, non una popolazione di individui da disaggregare per sesso.")
    _add_metric(metric_id, "eta", NOT_APPLICABLE, "La metrica misura una caratteristica territoriale del Comune, non una popolazione di individui da disaggregare per classi di età.")
    _add_metric(metric_id, "numeratore_denominatore", NOT_APPLICABLE, "La metrica pubblicata non è definita come quota o tasso ricostruito da un singolo numeratore e denominatore.")
_add_metric("municipalFragility", "assoluto_normalizzato", NOT_APPLICABLE, "L'IFC è un indice composito/posizione relativa; non esiste una misura assoluta dello stesso fenomeno da affiancare al valore indicizzato.")
_add_metric("essentialServicesAccessibility", "assoluto_normalizzato", NOT_APPLICABLE, "L'indicatore è un tempo di percorrenza in minuti; una coppia assoluto/normalizzato non è semanticamente definita per la stessa misura.")
_add_metric("lowProductivityEmployment", "assoluto_normalizzato", NOT_APPLICABLE, "L'indicatore pubblicato è una classe ordinale/ventile della distribuzione comunale; non è una coppia consistenza assoluta più tasso normalizzato.")


# MIM: studenti e classi sono disponibili come conteggi; il dataset del tempo
# scuola include il genere, mentre le basi di edilizia descrivono edifici e non
# popolazioni umane da disaggregare per età.
MIM_CLASS_REF = "https://dati.istruzione.it/opendata/opendata/catalog/ALUCORSOINDCLASTA"
MIM_AGE_REF = "https://dati.istruzione.it/opendata/opendata/catalog/ALUCORSOETASTA"
MIM_STUDENTS_REF = "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti"
MIM_BUILDINGS_REF = "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Edilizia+Scolastica"
_add_metric("studentsPerClass", "eta", NOT_APPLICABLE, "Il rapporto alunni/classi è definito sull'unità organizzativa classe; una classe di età non costituisce il denominatore organizzativo della metrica.")
_add_metric("studentsPerClass", "assoluto_normalizzato", AVAILABLE, "Il dataset MIM per anno di corso, classe e genere espone sia il numero di classi sia i conteggi degli alunni, consentendo di affiancare le consistenze assolute al rapporto alunni/classe.", MIM_CLASS_REF)
_add_metric("primaryFullTimeShare", "sesso", AVAILABLE, "I dataset MIM degli studenti e del tempo scuola includono il genere, permettendo una lettura della quota di tempo pieno distinta per sesso.", MIM_STUDENTS_REF)
_add_metric("primaryFullTimeShare", "eta", UNAVAILABLE, "Il dataset del tempo scuola è articolato per anno di corso e genere; il catalogo MIM pubblica l'età in un dataset separato che non incrocia la modalità di tempo scuola necessaria a questa quota.", MIM_AGE_REF)
_add_metric("primaryFullTimeShare", "assoluto_normalizzato", AVAILABLE, "La quota di tempo pieno deriva dai conteggi degli alunni per modalità di tempo scuola e dal totale degli alunni della primaria, disponibili negli open data MIM.", MIM_STUDENTS_REF)
_add_metric("schoolStudents", "assoluto_normalizzato", UNAVAILABLE, "Il dataset MIM diffonde i conteggi di alunni per scuola e classe ma non una misura normalizzata equivalente per popolazione residente o altra base territoriale esterna.", MIM_CLASS_REF)
for metric_id in (
    "schoolBuildingSafetyDocs",
    "schoolBuildingAccessibility",
    "schoolBuildingFacilities",
    "schoolBuildingAge",
    "schoolBuildingTransport",
):
    _add_metric(metric_id, "eta", NOT_APPLICABLE, "La metrica descrive caratteristiche fisiche o funzionali degli edifici scolastici; l'età delle persone non è una dimensione semantica dell'oggetto misurato.")


# Censimento Agricoltura: i rapporti usati per dimensione media e irrigazione
# sono ricostruibili da grandezze censuarie omogenee; i conteggi/ettari puri non
# vengono trasformati artificialmente in rapporti.
AGRI_REF = "https://www.istat.it/statistiche-per-temi/censimenti/agricoltura/7-censimento-generale/risultati/"
_add_metric("agriculturalFarms", "numeratore_denominatore", NOT_APPLICABLE, "La metrica è il numero di aziende agricole e non è definita come rapporto, tasso o quota.")
_add_metric("averageAgriculturalFarmSize", "numeratore_denominatore", AVAILABLE, "La dimensione media deriva dalla SAU delle aziende e dal numero di aziende con SAU; entrambe le grandezze sono diffuse dal Censimento Agricoltura.", AGRI_REF)
_add_metric("cropProfile", "numeratore_denominatore", NOT_APPLICABLE, "La metrica espone ettari per tipologia di coltura; le singole consistenze non sono definite come rapporto numeratore/denominatore.")
_add_metric("irrigatedAgriculturalArea", "numeratore_denominatore", AVAILABLE, "La quota di SAU irrigata è ricostruibile dalla superficie irrigata e dalla SAU del medesimo universo censuario, entrambe disponibili nelle basi Istat.", AGRI_REF)
_add_metric("agriculturalUsedArea", "numeratore_denominatore", AVAILABLE, "La quota della superficie comunale occupata da SAU usa la SAU censuaria come numeratore e la superficie comunale ufficiale di riferimento come denominatore; entrambe sono grandezze ufficiali Istat utilizzate dal progetto.", AGRI_REF)


def main() -> None:
    ns["main"]()


if __name__ == "__main__":
    main()
