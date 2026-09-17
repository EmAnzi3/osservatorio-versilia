#!/usr/bin/env python3
"""Estende le evidenze A3.2 della tranche audit-13 senza duplicare il catalogo pubblico."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "apply_enrichment_evidence_audit12.py"

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
        raise RuntimeError(f"A3.2 audit-13: dimensione già definita: {profile_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


def _add_metric(metric_id: str, dimension: str, state: str, evidence: str, reference: str = "") -> None:
    dimensions = METRIC_EVIDENCE.setdefault(metric_id, {})
    if dimension in dimensions:
        raise RuntimeError(f"A3.2 audit-13: override già definito: {metric_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


# Regione Toscana — censimento opere idrauliche DGRT 1155/2021.
# È una ricognizione cartografica regionale puntuale, con layer shape delle opere
# censite; non pubblica una serie temporale regolare né una normalizzazione del
# numero di elementi. Le tipologie geometriche e il perimetro regionale rendono
# invece disponibili dettaglio territoriale, benchmark Toscana e categorie.
HYDRAULIC_REF = "https://www.regione.toscana.it/-/censimento-delle-opere-idrauliche"
_add_profile(
    "regione-toscana-opere-idrauliche-2021",
    "serie_storica",
    UNAVAILABLE,
    "La fonte ufficiale pubblica la ricognizione approvata con DGRT 1155/2021 come censimento cartografico puntuale; non espone una serie storica omogenea dello stesso censimento.",
    HYDRAULIC_REF,
)
_add_profile(
    "regione-toscana-opere-idrauliche-2021",
    "dettaglio_territoriale",
    AVAILABLE,
    "La ricognizione è distribuita come dato geografico editabile in formato shape; le feature possono essere lette e aggregate a scale territoriali inferiori o superiori al Comune.",
    HYDRAULIC_REF,
)
_add_profile(
    "regione-toscana-opere-idrauliche-2021",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Il censimento copre il territorio regionale toscano e consente quindi di costruire un riferimento Toscana coerente per il numero di elementi censiti.",
    HYDRAULIC_REF,
)
_add_profile(
    "regione-toscana-opere-idrauliche-2021",
    "assoluto_normalizzato",
    UNAVAILABLE,
    "La fonte censisce elementi cartografici e ne permette il conteggio, ma non pubblica una misura normalizzata equivalente del numero di opere rispetto a popolazione, superficie o altra base territoriale.",
    HYDRAULIC_REF,
)
_add_profile(
    "regione-toscana-opere-idrauliche-2021",
    "frequenza_infra_annuale",
    UNAVAILABLE,
    "La ricognizione è un censimento approvato con atto del 2021 e non una serie mensile, trimestrale o semestrale.",
    HYDRAULIC_REF,
)
_add_profile(
    "regione-toscana-opere-idrauliche-2021",
    "categorie_specifiche",
    AVAILABLE,
    "La ricognizione cartografica distingue feature delle opere idrauliche e il progetto conserva separatamente elementi areali, lineari e puntuali; la classificazione per tipologia è quindi disponibile alla fonte.",
    HYDRAULIC_REF,
)
for dimension, evidence in (
    ("sesso", "La metrica conta elementi fisici di opere idrauliche; il sesso delle persone non è una dimensione semantica dell'oggetto misurato."),
    ("eta", "La metrica conta elementi fisici di opere idrauliche; l'età delle persone non è una dimensione semantica dell'oggetto misurato."),
    ("numeratore_denominatore", "La metrica è un conteggio di feature censite e non è definita come rapporto, quota o tasso con numeratore e denominatore."),
):
    _add_metric("hydraulicWorksCensusElements", dimension, NOT_APPLICABLE, evidence)


# Regione Toscana — reticolo idrografico e di gestione.
# La pagina ufficiale elenca versioni approvate dal 2013 al 2025, quindi la
# dimensione storica è disponibile; gli aggiornamenti sono però deliberativi e
# irregolari, non infra-annuali regolari. Il layer è regionale e georiferito.
RETICULUM_REF = "https://www.regione.toscana.it/-/reticolo-idrografico-e-di-gestione"
_add_profile(
    "regione-toscana-reticolo-v137",
    "serie_storica",
    AVAILABLE,
    "Regione Toscana elenca versioni del reticolo approvate nel 2013, 2016, 2019, 2020, 2021, 2022, 2024 e 2025, rendendo possibile un confronto storico tra snapshot ufficiali.",
    RETICULUM_REF,
)
_add_profile(
    "regione-toscana-reticolo-v137",
    "dettaglio_territoriale",
    AVAILABLE,
    "Il reticolo è distribuito come shapefile regionale georiferito e può essere interrogato o ritagliato a più scale territoriali.",
    RETICULUM_REF,
)
_add_profile(
    "regione-toscana-reticolo-v137",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Il layer ufficiale copre l'intera Toscana e consente di costruire un benchmark regionale omogeneo per lunghezza e caratteristiche del reticolo.",
    RETICULUM_REF,
)
_add_profile(
    "regione-toscana-reticolo-v137",
    "frequenza_infra_annuale",
    UNAVAILABLE,
    "Gli aggiornamenti del reticolo avvengono tramite atti regionali in anni non regolari; la fonte non pubblica osservazioni mensili, trimestrali o semestrali equivalenti.",
    RETICULUM_REF,
)
for dimension, evidence in (
    ("sesso", "La metrica misura una rete idrografica fisica; il sesso delle persone non è una dimensione semantica dell'oggetto misurato."),
    ("eta", "La metrica misura una rete idrografica fisica; l'età delle persone non è una dimensione semantica dell'oggetto misurato."),
):
    _add_metric("managedReticulumLength", dimension, NOT_APPLICABLE, evidence)


# Regione Toscana — aree protette: layer ufficiali regionali interrogabili e
# scaricabili. Le categorie sono già materializzate nel catalogo e vengono quindi
# lasciate al detector strutturale; lo stesso vale per ha/percentuale e rapporto
# area tutelata/superficie comunale, già presenti nel payload effettivo.
PROTECTED_REF = "https://www502.regione.toscana.it/geoscopio/servizi/wms/AREE_PROTETTE.htm"
_add_profile(
    "regione-toscana-aree-protette-v137",
    "dettaglio_territoriale",
    AVAILABLE,
    "I layer ufficiali delle aree protette sono georiferiti e interrogabili, quindi consentono dettaglio e aggregazione a più scale territoriali.",
    PROTECTED_REF,
)
_add_profile(
    "regione-toscana-aree-protette-v137",
    "benchmark_toscana_italia",
    AVAILABLE,
    "I tematismi coprono l'intero territorio toscano e consentono un riferimento regionale coerente per superficie interessata dalle tutele.",
    PROTECTED_REF,
)
_add_profile(
    "regione-toscana-aree-protette-v137",
    "frequenza_infra_annuale",
    UNAVAILABLE,
    "La fonte cartografica viene aggiornata secondo gli atti e i perimetri ufficiali e non pubblica una serie mensile, trimestrale o semestrale omogenea.",
    PROTECTED_REF,
)
for dimension, evidence in (
    ("sesso", "La metrica misura superficie territoriale sottoposta a tutela naturalistica; il sesso delle persone non è applicabile."),
    ("eta", "La metrica misura superficie territoriale sottoposta a tutela naturalistica; l'età delle persone non è applicabile."),
):
    _add_metric("protectedNaturalAreas", dimension, NOT_APPLICABLE, evidence)


# Regione Toscana — Iter.Net 4.48: snapshot geografico regionale della rete
# stradale con attributi amministrativi e di pavimentazione. Le letture lunghezza,
# densità e categorie sono già materializzate nel payload e non vengono annotate
# come AVAILABLE_MISSING.
ITERNET_REF = "https://www502.regione.toscana.it/geoscopio/download/grafo_stradale/"
_add_profile(
    "regione-toscana-iternet-448",
    "dettaglio_territoriale",
    AVAILABLE,
    "Iter.Net è un grafo stradale georiferito regionale in formato SHP; gli elementi possono essere letti e aggregati a più scale territoriali.",
    ITERNET_REF,
)
_add_profile(
    "regione-toscana-iternet-448",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Il grafo Iter.Net copre l'intera Toscana e permette di costruire un benchmark regionale omogeneo su lunghezze e attributi della rete.",
    ITERNET_REF,
)
_add_profile(
    "regione-toscana-iternet-448",
    "frequenza_infra_annuale",
    UNAVAILABLE,
    "La fonte usata è lo snapshot ufficiale Iter.Net 4.48 di giugno 2022 e non una serie mensile, trimestrale o semestrale.",
    ITERNET_REF,
)
for dimension, evidence in (
    ("sesso", "La metrica misura elementi fisici del grafo stradale; il sesso delle persone non è una dimensione semantica applicabile."),
    ("eta", "La metrica misura elementi fisici del grafo stradale; l'età delle persone non è una dimensione semantica applicabile."),
):
    _add_metric("roadNetworkProfile", dimension, NOT_APPLICABLE, evidence)


# Regione Toscana / ARPAT — SISBON. Il report pubblico è filtrabile e scaricabile
# in CSV, con localizzazione e stato del procedimento; il profilo è aggiornato con
# frequenza settimanale. Non esiste nella fonte una normalizzazione per popolazione
# o superficie del conteggio dei procedimenti.
SISBON_REF = "https://sira.arpat.toscana.it/apex/f?p=SISBON:REPORT_PER_RT::CSV:IR_REPORT_GEOSCOPIO"
SISBON_GUIDE_REF = "https://sira.arpat.toscana.it/apexfiles/sisbon/Breve_Guida_File_CSV.pdf"
_add_profile(
    "sisbon-weekly",
    "dettaglio_territoriale",
    AVAILABLE,
    "Il report SISBON contiene localizzazione e campi territoriali dei procedimenti e consente filtri e download CSV personalizzati.",
    SISBON_GUIDE_REF,
)
_add_profile(
    "sisbon-weekly",
    "benchmark_toscana_italia",
    AVAILABLE,
    "SISBON è il sistema regionale toscano dei procedimenti di bonifica; l'insieme dei record consente un benchmark Toscana omogeneo rispetto ai conteggi comunali.",
    SISBON_REF,
)
_add_profile(
    "sisbon-weekly",
    "assoluto_normalizzato",
    UNAVAILABLE,
    "Il report pubblico diffonde procedimenti e relativi stati ma non una misura normalizzata equivalente del numero di procedimenti per popolazione, superficie o altra base territoriale.",
    SISBON_REF,
)
_add_profile(
    "sisbon-weekly",
    "frequenza_infra_annuale",
    AVAILABLE,
    "Il profilo operativo SISBON è verificato con aggiornamento settimanale del flusso pubblico, quindi la dimensione infra-annuale è disponibile alla fonte.",
    SISBON_REF,
)
_add_profile(
    "sisbon-weekly",
    "categorie_specifiche",
    AVAILABLE,
    "Il report SISBON consente di selezionare campi e filtri sullo stato del procedimento e sulle caratteristiche del sito; le categorie di iter sono quindi disponibili alla fonte.",
    SISBON_GUIDE_REF,
)
for dimension, evidence in (
    ("sesso", "La metrica conta procedimenti di bonifica territoriali; il sesso delle persone non è una dimensione semantica dell'oggetto misurato."),
    ("eta", "La metrica conta procedimenti di bonifica territoriali; l'età delle persone non è una dimensione semantica dell'oggetto misurato."),
    ("numeratore_denominatore", "La metrica è un conteggio di procedimenti univoci per stato e non è definita come rapporto, quota o tasso con numeratore e denominatore."),
):
    _add_metric("remediationProceedings", dimension, NOT_APPLICABLE, evidence)


# Regione Toscana — servizi educativi 3-36 mesi. Il dataset ufficiale conserva
# risorse annuali dal 2014/15 al 2024/25, dati per Comune/Zona/Provincia, capacità
# per fasce di età e categorie di servizio. Il data dictionary non espone una
# disaggregazione per sesso. Assoluto/normalizzato e numeratore/denominatore sono
# già presenti nel payload effettivo e restano fuori dalle annotazioni manuali.
EARLY_REF = "https://dati.toscana.it/dataset/serviziprimainfanzia"
EARLY_GUIDE_REF = "https://dati.toscana.it/dataset/98ee6064-b61a-45e2-a790-86c55b278574/resource/4d9a09c0-3ccc-4086-8cf9-b5803b75288b/download/guida.pdf"
_add_profile(
    "regione-toscana-early-childhood",
    "serie_storica",
    AVAILABLE,
    "Il dataset ufficiale conserva risorse annuali dei servizi educativi per la prima infanzia dal 2014/15 al 2024/25, rendendo disponibile una serie storica omogenea per le principali grandezze.",
    EARLY_REF,
)
_add_profile(
    "regione-toscana-early-childhood",
    "sesso",
    UNAVAILABLE,
    "Il data dictionary ufficiale pubblica popolazione 3-36 mesi, strutture, ricettività, iscritti e domande, ma non una disaggregazione per sesso compatibile con questa metrica.",
    EARLY_REF,
)
_add_profile(
    "regione-toscana-early-childhood",
    "eta",
    AVAILABLE,
    "La fonte pubblica la ricettività per fasce 3-11, 12-23 e 24-36 mesi, quindi una disaggregazione per età è disponibile nel dominio della metrica.",
    EARLY_GUIDE_REF,
)
_add_profile(
    "regione-toscana-early-childhood",
    "dettaglio_territoriale",
    AVAILABLE,
    "Le risorse ufficiali espongono dati per Comune e, nelle annualità disponibili, anche per Zona e Provincia.",
    EARLY_REF,
)
_add_profile(
    "regione-toscana-early-childhood",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Il dataset copre l'intera Toscana e consente di costruire il riferimento regionale con le stesse grandezze comunali.",
    EARLY_REF,
)
_add_profile(
    "regione-toscana-early-childhood",
    "frequenza_infra_annuale",
    UNAVAILABLE,
    "Il dataset dichiara frequenza di aggiornamento annuale per anno educativo e non pubblica una cadenza mensile, trimestrale o semestrale equivalente.",
    EARLY_REF,
)
_add_profile(
    "regione-toscana-early-childhood",
    "categorie_specifiche",
    AVAILABLE,
    "Il data dictionary distingue nidi, servizi integrativi, titolarità pubblica/privata e fasce di ricettività, quindi le categorie specifiche del servizio sono disponibili alla fonte.",
    EARLY_REF,
)


def main() -> None:
    ns["main"]()


if __name__ == "__main__":
    main()
