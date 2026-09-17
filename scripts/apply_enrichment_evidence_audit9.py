#!/usr/bin/env python3
"""Estende le evidenze A3.2 della tranche audit-9 senza duplicare il catalogo pubblico."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "apply_enrichment_evidence_audit8.py"

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
        raise RuntimeError(f"A3.2 audit-9: dimensione già definita: {profile_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


def _add_metric(metric_id: str, dimension: str, state: str, evidence: str, reference: str = "") -> None:
    dimensions = METRIC_EVIDENCE.setdefault(metric_id, {})
    if dimension in dimensions:
        raise RuntimeError(f"A3.2 audit-9: override già definito: {metric_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


# ISPRA IdroGEO: indicatori nazionali per popolazione/superficie esposta,
# percentuali, classi di pericolosita' e dettaglio comunale/regionale.
IDROGEO_REF = "https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/dissesto-idrogeologico/indicatori-di-rischio"
for dimension, state, evidence in (
    ("sesso", UNAVAILABLE, "Il set ufficiale pubblica la popolazione esposta complessiva e gli altri oggetti esposti, ma non una disaggregazione della popolazione a rischio per sesso."),
    ("eta", UNAVAILABLE, "Il set ufficiale pubblica la popolazione esposta complessiva e gli altri oggetti esposti, ma non una disaggregazione della popolazione a rischio per classi di eta'."),
    ("dettaglio_territoriale", AVAILABLE, "ISPRA pubblica gli indicatori di rischio su base comunale e li aggrega a scale territoriali superiori."),
    ("benchmark_toscana_italia", AVAILABLE, "Gli stessi indicatori sono pubblicati per l'intero territorio nazionale e per le Regioni, inclusa la Toscana."),
    ("assoluto_normalizzato", AVAILABLE, "ISPRA affianca consistenze assolute di popolazione/superficie esposta e quote percentuali sul totale di riferimento."),
    ("frequenza_infra_annuale", UNAVAILABLE, "Gli indicatori di rischio sono aggiornati per edizioni/quadri conoscitivi e non come serie mensile, trimestrale o semestrale equivalente."),
    ("numeratore_denominatore", AVAILABLE, "Le consistenze esposte e i totali di popolazione o superficie di riferimento consentono di ricostruire le percentuali pubblicate."),
    ("categorie_specifiche", AVAILABLE, "La fonte distingue le classi di pericolosita' da frana PAI e gli scenari di pericolosita' idraulica P1/P2/P3."),
):
    _add_profile("ispra-idrogeo-risk", dimension, state, evidence, IDROGEO_REF)


# Piano regionale cave / RTCave: geometrie, cave, materiali e volumi sono
# territorializzati; il monitoraggio della produzione e' annuale.
PRC_REF = "https://www.regione.toscana.it/piano-regionale-cave"
PRC_MONITOR_REF = "https://www.regione.toscana.it/-/rilevamento-delle-attivita-estrattive"
for dimension, state, evidence, reference in (
    ("dettaglio_territoriale", AVAILABLE, "Il PRC e RTCave localizzano cave e geometrie di piano e consentono letture per Comune, Provincia e Regione.", PRC_REF),
    ("benchmark_toscana_italia", AVAILABLE, "Il quadro regionale usa la stessa base per tutti i Comuni toscani e pubblica aggregazioni regionali coerenti.", PRC_REF),
    ("frequenza_infra_annuale", UNAVAILABLE, "I quantitativi estratti sono comunicati annualmente e il quadro di piano non e' una rilevazione statistica infra-annuale equivalente.", PRC_MONITOR_REF),
    ("categorie_specifiche", AVAILABLE, "La banca dati distingue tipologia di materiale, tipologia e stato della cava; il PRC mantiene categorie di giacimento/area separate.", "https://cave.regione.toscana.it/"),
):
    _add_profile("regione-toscana-prc-annual", dimension, state, evidence, reference)
for metric_id in ("extractivePlanning", "extractiveProduction"):
    _add_metric(metric_id, "sesso", NOT_APPLICABLE, "La metrica descrive aree o volumi dell'attivita' estrattiva; il sesso delle persone non e' una dimensione semantica dell'oggetto misurato.")
    _add_metric(metric_id, "eta", NOT_APPLICABLE, "La metrica descrive aree o volumi dell'attivita' estrattiva; l'eta' delle persone non e' una dimensione semantica dell'oggetto misurato.")
_add_metric("extractivePlanning", "serie_storica", UNAVAILABLE, "Il PRC pubblica il quadro pianificatorio vigente e non una serie temporale omogenea annuale della stessa geometria/indicatore.", PRC_REF)
_add_metric("extractivePlanning", "assoluto_normalizzato", AVAILABLE, "Le geometrie ufficiali permettono di affiancare superficie assoluta in ettari e quota sulla superficie comunale.", PRC_REF)
_add_metric("extractiveProduction", "assoluto_normalizzato", UNAVAILABLE, "Il monitoraggio pubblica i quantitativi estratti; non diffonde una misura normalizzata equivalente per popolazione o superficie comunale.", PRC_MONITOR_REF)
_add_metric("extractivePlanning", "numeratore_denominatore", AVAILABLE, "La quota comunale deriva dall'area PRC intersecata e dall'area comunale di riferimento, entrambe ricostruibili dalle geometrie ufficiali.", PRC_REF)
_add_metric("extractiveProduction", "numeratore_denominatore", NOT_APPLICABLE, "La produzione estrattiva e' un volume in metri cubi e non e' definita come rapporto, tasso o quota.")


# INVALSI open data: benchmark e dettaglio territoriale sono gia' acquisiti nel
# catalogo; la fonte espone genere e categorie di contesto, non eta' anagrafica
# ne' osservazioni infra-annuali.
INVALSI_RESULTS_REF = "https://serviziostatistico.invalsi.it/invalsi_ss_data/punteggi-e-percentuale-di-studenti-nei-livelli-di-competenza-per-ripartizioni-territoriali-e-caratteristiche-di-contesto/"
INVALSI_DISP_REF = "https://serviziostatistico.invalsi.it/invalsi_ss_data/eccellenza-accademica-e-dispersione-scolastica-implicita-valori-percentuali/"
for profile_id, reference in (("invalsi-open-risultati-2025", INVALSI_RESULTS_REF), ("invalsi-open-dispersione-2025", INVALSI_DISP_REF)):
    _add_profile(profile_id, "sesso", AVAILABLE, "L'open data INVALSI espone sottocategorie per genere oltre a territorio, materia/grado e altre caratteristiche di contesto.", reference)
    _add_profile(profile_id, "eta", UNAVAILABLE, "La tavola analitica ufficiale articola i risultati per grado scolastico e caratteristiche di contesto ma non espone una dimensione anagrafica di eta' equivalente.", reference)
    _add_profile(profile_id, "frequenza_infra_annuale", UNAVAILABLE, "I risultati sono organizzati per annualita' scolastica; la fonte non pubblica osservazioni mensili, trimestrali o semestrali equivalenti.", reference)
    _add_profile(profile_id, "categorie_specifiche", AVAILABLE, "La fonte distingue grado, materia e ulteriori categorie analitiche come genere, origine e tipologia di istituto.", reference)
_add_metric("invalsiResults", "assoluto_normalizzato", NOT_APPLICABLE, "Il punteggio medio INVALSI e' una misura su scala di competenza; non esiste una forma assoluta dello stesso indicatore da affiancare al punteggio.")
_add_metric("invalsiResults", "numeratore_denominatore", NOT_APPLICABLE, "Il punteggio medio INVALSI non e' definito come rapporto con un singolo numeratore e denominatore.")
_add_metric("invalsiCompetence", "assoluto_normalizzato", UNAVAILABLE, "La tavola pubblica le percentuali nei livelli/traguardi ma non il corrispondente conteggio assoluto comunale degli studenti per la stessa cella analitica.", INVALSI_RESULTS_REF)
_add_metric("invalsiCompetence", "numeratore_denominatore", UNAVAILABLE, "La tavola pubblica percentuali dei livelli/traguardi ma non espone per ogni cella comunale i conteggi di numeratore e denominatore necessari alla ricostruzione.", INVALSI_RESULTS_REF)
for metric_id in ("invalsiImplicitDispersion", "invalsiAcademicExcellence"):
    _add_metric(metric_id, "assoluto_normalizzato", UNAVAILABLE, "L'open data ufficiale diffonde questi indicatori come valori percentuali e non il corrispondente conteggio assoluto comunale.", INVALSI_DISP_REF)
    _add_metric(metric_id, "numeratore_denominatore", UNAVAILABLE, "La tavola ufficiale diffonde il valore percentuale senza esporre nella stessa cella i conteggi elementari necessari alla ricostruzione del rapporto.", INVALSI_DISP_REF)


# OMI: banca dati nazionale, semestrale, per zona e tipologia immobiliare.
OMI_REF = "https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.htm"
for dimension, state, evidence in (
    ("serie_storica", AVAILABLE, "La consultazione OMI permette di selezionare semestri differenti e conserva le quotazioni per periodo."),
    ("dettaglio_territoriale", AVAILABLE, "Le quotazioni sono pubblicate per Provincia, Comune e singola zona OMI."),
    ("benchmark_toscana_italia", AVAILABLE, "La banca dati usa la stessa struttura su tutti i Comuni censiti negli archivi catastali, consentendo confronti regionali e nazionali."),
    ("assoluto_normalizzato", UNAVAILABLE, "La fonte pubblica valori unitari in euro/m2 e non il valore assoluto di una specifica unita' immobiliare equivalente."),
    ("frequenza_infra_annuale", AVAILABLE, "Le quotazioni OMI sono pubblicate con cadenza semestrale."),
    ("categorie_specifiche", AVAILABLE, "La fonte distingue destinazione, tipologia immobiliare e stato conservativo."),
):
    _add_profile("agenzia-entrate-omi-semestral", dimension, state, evidence, OMI_REF)
for dimension, evidence in (
    ("sesso", "La quotazione descrive una zona/tipologia immobiliare; il sesso delle persone non e' una dimensione semantica del valore unitario."),
    ("eta", "La quotazione descrive una zona/tipologia immobiliare; l'eta' delle persone non e' una dimensione semantica del valore unitario."),
    ("numeratore_denominatore", "La quotazione in euro/m2 e' un valore unitario estimativo pubblicato dalla fonte e non un rapporto statistico ricostruito da conteggi di numeratore/denominatore."),
):
    _add_metric("omiResidential", dimension, NOT_APPLICABLE, evidence)


# Istat acqua: perdite = volumi immessi/erogati e relativa percentuale.
WATER_REF = "https://www.istat.it/comunicato-stampa/censimento-delle-acque-per-uso-civile-anno-2018/"
for dimension, state, evidence in (
    ("dettaglio_territoriale", AVAILABLE, "Il Censimento delle acque pubblica dati territoriali sulle reti comunali e aggregati superiori."),
    ("benchmark_toscana_italia", AVAILABLE, "La rilevazione copre l'intero territorio nazionale con metodologia comune e consente confronti regionali/nazionali."),
    ("assoluto_normalizzato", AVAILABLE, "Istat pubblica i volumi assoluti delle perdite e la percentuale sul volume immesso in rete."),
    ("frequenza_infra_annuale", UNAVAILABLE, "Il Censimento delle acque per uso civile e' una rilevazione periodica e non una serie infra-annuale equivalente."),
    ("numeratore_denominatore", AVAILABLE, "La percentuale di perdita deriva dai volumi immessi ed erogati, pubblicati dalla rilevazione."),
    ("categorie_specifiche", UNAVAILABLE, "Per la percentuale di perdite della rete comunale la fonte non diffonde una scomposizione territoriale stabile dello stesso indicatore in categorie specifiche."),
):
    _add_profile("istat-water-irregular", dimension, state, evidence, WATER_REF)
_add_metric("waterNetworkLosses", "sesso", NOT_APPLICABLE, "La metrica misura una caratteristica tecnica della rete idrica; il sesso non e' una dimensione semantica del fenomeno.")
_add_metric("waterNetworkLosses", "eta", NOT_APPLICABLE, "La metrica misura una caratteristica tecnica della rete idrica; l'eta' non e' una dimensione semantica del fenomeno.")


# Bandiera Blu: elenco nazionale annuale per Regione, Comune e localita'.
BLUE_REF = "https://www.bandierablu.org/common/blueflag.asp?anno=2026&tipo=bb"
for dimension, state, evidence in (
    ("dettaglio_territoriale", AVAILABLE, "L'elenco ufficiale distingue Regione, Provincia, Comune e singole spiagge/localita' premiate."),
    ("benchmark_toscana_italia", AVAILABLE, "L'elenco copre l'intero territorio nazionale con la stessa struttura, consentendo conteggi comparabili per Toscana e Italia."),
    ("assoluto_normalizzato", UNAVAILABLE, "La fonte pubblica l'elenco/conteggio delle localita' premiate ma non una misura normalizzata equivalente per km di costa o popolazione."),
    ("frequenza_infra_annuale", UNAVAILABLE, "La Bandiera Blu e' assegnata per anno e non viene pubblicata come osservazione mensile, trimestrale o semestrale equivalente."),
    ("categorie_specifiche", UNAVAILABLE, "L'elenco delle spiagge premiate non pubblica una disaggregazione interna stabile dello stesso indicatore per categorie specifiche."),
):
    _add_profile("fee-blue-flag-annual", dimension, state, evidence, BLUE_REF)
_add_metric("blueFlagBeaches", "sesso", NOT_APPLICABLE, "La metrica conta spiagge/localita' premiate; il sesso non e' una dimensione semantica dell'oggetto contato.")
_add_metric("blueFlagBeaches", "eta", NOT_APPLICABLE, "La metrica conta spiagge/localita' premiate; l'eta' non e' una dimensione semantica dell'oggetto contato.")
_add_metric("blueFlagBeaches", "numeratore_denominatore", NOT_APPLICABLE, "La metrica e' un conteggio di localita' premiate e non e' definita come rapporto, tasso o quota.")


# Addizionale comunale IRPEF: archivio MEF annuale nazionale per Comune,
# con aliquote, scaglioni ed esenzioni.
IRPEF_REF = "https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/"
for dimension, state, evidence in (
    ("serie_storica", AVAILABLE, "Il portale consente di selezionare l'anno e conserva le aliquote/delibere comunali per annualita'."),
    ("dettaglio_territoriale", AVAILABLE, "La consultazione e' organizzata per Regione, Provincia e Comune."),
    ("benchmark_toscana_italia", AVAILABLE, "Lo stesso archivio copre i Comuni italiani e permette confronti omogenei tra Toscana e resto d'Italia."),
    ("frequenza_infra_annuale", UNAVAILABLE, "Aliquote ed esenzioni sono riferite all'anno d'imposta; non esiste una serie infra-annuale equivalente dello stesso indicatore."),
    ("categorie_specifiche", AVAILABLE, "Il portale distingue aliquote, fasce/scaglioni di reddito ed eventuali soglie di esenzione."),
):
    _add_profile("mef-municipal-irpef-annual", dimension, state, evidence, IRPEF_REF)
_add_metric("municipalIrpef", "sesso", NOT_APPLICABLE, "La metrica applica regole fiscali comunali a uno scenario di reddito standard; il sesso non modifica la struttura dell'aliquota comunale.")
_add_metric("municipalIrpef", "eta", NOT_APPLICABLE, "La metrica applica regole fiscali comunali a uno scenario di reddito standard; l'eta' non modifica la struttura dell'aliquota comunale.")
_add_metric("municipalIrpef", "assoluto_normalizzato", AVAILABLE, "Aliquote, scaglioni ed esenzioni pubblicati dal MEF permettono di affiancare all'importo assoluto dello scenario anche l'incidenza percentuale sul reddito imponibile.", IRPEF_REF)
_add_metric("municipalIrpef", "numeratore_denominatore", NOT_APPLICABLE, "L'importo annuo dello scenario e' il risultato dell'applicazione delle aliquote e non e' definito come un singolo rapporto statistico numeratore/denominatore.")


def main() -> None:
    ns["main"]()


if __name__ == "__main__":
    main()
