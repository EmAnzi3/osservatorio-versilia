#!/usr/bin/env python3
"""Estende le evidenze A3.2 della tranche audit-8 senza duplicare il catalogo pubblico."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "apply_enrichment_evidence_audit7.py"

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
        raise RuntimeError(f"A3.2 audit-8: dimensione già definita: {profile_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


def _add_metric(metric_id: str, dimension: str, state: str, evidence: str, reference: str = "") -> None:
    dimensions = METRIC_EVIDENCE.setdefault(metric_id, {})
    if dimension in dimensions:
        raise RuntimeError(f"A3.2 audit-8: override già definito: {metric_id}/{dimension}")
    dimensions[dimension] = _annotation(state, evidence, reference)


# SIOPE: i prospetti aggregati ufficiali consentono confronti per Regione,
# Provincia e circoscrizione. Le metriche del profilo misurano flussi di cassa
# dell'ente, quindi sesso/età non sono dimensioni semantiche del fenomeno.
_add_profile(
    "siope-monthly",
    "benchmark_toscana_italia",
    AVAILABLE,
    "SIOPE consente prospetti aggregati per enti raggruppati per circoscrizione, Regione o Provincia e confronti territoriali sulla stessa classificazione dei flussi di cassa.",
    "https://www.siope.it/Siope/html/help_on_line.pdf",
)
for metric_id in (
    "capitalPayments",
    "currentPayments",
    "fiscalRecoveryActivity",
    "siopePayments",
):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica misura un flusso finanziario o un'attività di cassa dell'ente comunale; il sesso delle persone non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica misura un flusso finanziario o un'attività di cassa dell'ente comunale; l'età delle persone non è una dimensione semantica dell'oggetto misurato.",
    )
_add_metric(
    "fiscalRecoveryActivity",
    "numeratore_denominatore",
    NOT_APPLICABLE,
    "La metrica presenta grandezze monetarie di recupero tributario e accertamento e non è definita come rapporto, tasso o quota con numeratore e denominatore.",
)


# ISPRA costa: gli indicatori nazionali pubblicano serie multi-periodo, valori
# assoluti in km, percentuali, categorie e tabelle per Regione costiera.
COAST_PROTECTED_REF = "https://indicatoriambientali.isprambiente.it/it/coste/costa-protetta"
COAST_DYNAMICS_REF = "https://indicatoriambientali.isprambiente.it/it/coste/dinamica-litoranea"
for dimension, state, evidence, reference in (
    (
        "serie_storica",
        AVAILABLE,
        "ISPRA pubblica per la costa protetta rilevazioni 2000, 2006 e 2020 e per la dinamica litoranea più periodi omogenei dal 1950 al 2020.",
        COAST_DYNAMICS_REF,
    ),
    (
        "dettaglio_territoriale",
        AVAILABLE,
        "Le tavole ISPRA distinguono il totale nazionale e le singole Regioni costiere, con lunghezze e quote riferite ai rispettivi tratti di costa.",
        COAST_PROTECTED_REF,
    ),
    (
        "benchmark_toscana_italia",
        AVAILABLE,
        "Gli indicatori sono calcolati con la stessa metodologia per Italia e Regioni costiere, inclusa la Toscana, consentendo confronti territoriali coerenti.",
        COAST_PROTECTED_REF,
    ),
    (
        "assoluto_normalizzato",
        AVAILABLE,
        "Le tavole ISPRA affiancano lunghezze assolute in chilometri e quote percentuali di costa protetta o soggetta a variazione.",
        COAST_PROTECTED_REF,
    ),
    (
        "frequenza_infra_annuale",
        UNAVAILABLE,
        "La dinamica litoranea è aggiornata su intervalli pluriennali e la costa protetta su rilevazioni distanziate nel tempo; la fonte non diffonde una serie infra-annuale equivalente.",
        COAST_DYNAMICS_REF,
    ),
    (
        "numeratore_denominatore",
        AVAILABLE,
        "Le tavole riportano le lunghezze dei tratti appartenenti alle classi dell'indicatore e la lunghezza di costa di riferimento, rendendo disponibili le componenti delle percentuali.",
        COAST_DYNAMICS_REF,
    ),
    (
        "categorie_specifiche",
        AVAILABLE,
        "ISPRA distingue categorie di protezione e classi di dinamica della linea di costa, incluse stabilità, avanzamento e arretramento.",
        COAST_DYNAMICS_REF,
    ),
):
    _add_profile("ispra-coast-irregular", dimension, state, evidence, reference)
for metric_id in ("rigidDefenceProtectedCoast", "shorelineDynamics"):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica descrive una proprietà fisica o infrastrutturale della linea di costa; il sesso delle persone non è una dimensione semantica del fenomeno.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica descrive una proprietà fisica o infrastrutturale della linea di costa; l'età delle persone non è una dimensione semantica del fenomeno.",
    )


# ARPAT balneazione: il rapporto annuale pubblica campioni conformi/non conformi,
# classificazione delle aree, km di costa e distribuzione territoriale.
ARPAT_BATHING_REF = "https://www.arpat.toscana.it/pubblicazione/il-controllo-delle-acque-di-balneazione-stagione-2025/"
for dimension, evidence in (
    ("serie_storica", "ARPAT pubblica rapporti annuali della stagione balneare e confronta gli esiti con le annualità precedenti, mantenendo la stessa rete di controllo."),
    ("dettaglio_territoriale", "Il rapporto ARPAT distingue aree di balneazione e risultati per territorio costiero, con dettaglio per singole aree e Province."),
    ("benchmark_toscana_italia", "Il rapporto contiene il quadro complessivo della Toscana con cui confrontare i risultati delle singole aree e dei territori costieri."),
    ("assoluto_normalizzato", "ARPAT riporta conteggi di campioni e aree insieme alle rispettive percentuali e ai chilometri di costa classificati."),
    ("numeratore_denominatore", "Il rapporto pubblica sia i conteggi delle unità favorevoli/non conformi sia i totali di campioni, aree o costa di riferimento usati nelle percentuali."),
    ("categorie_specifiche", "La fonte distingue classi ufficiali di qualità delle acque e tipologie di esito dei campioni, incluse conformità e non conformità."),
):
    _add_profile("arpat-bathing-annual", dimension, AVAILABLE, evidence, ARPAT_BATHING_REF)
for metric_id in ("bathingNonCompliantSamples", "bathingWaterQuality"):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica descrive campioni o qualità delle acque di balneazione; il sesso delle persone non è una dimensione semantica del fenomeno ambientale.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica descrive campioni o qualità delle acque di balneazione; l'età delle persone non è una dimensione semantica del fenomeno ambientale.",
    )
_add_metric(
    "bathingNonCompliantSamples",
    "frequenza_infra_annuale",
    AVAILABLE,
    "Durante la stagione balneare ARPAT effettua e pubblica campionamenti ripetuti nelle singole aree, quindi gli esiti dei campioni sono disponibili a frequenza infra-annuale.",
    ARPAT_BATHING_REF,
)
_add_metric(
    "bathingWaterQuality",
    "frequenza_infra_annuale",
    UNAVAILABLE,
    "La classificazione ufficiale della qualità dell'area è attribuita su base annuale usando la serie pluriennale prevista dalla normativa; non esiste una classificazione infra-annuale equivalente.",
    ARPAT_BATHING_REF,
)


# Istat servizi sociali: rilevazione annuale con tavole comunali, regionali e
# nazionali, spesa totale e pro capite e articolazione per area di utenza.
ISTAT_SOCIAL_REF = "https://www.istat.it/comunicato-stampa/la-spesa-dei-comuni-per-i-servizi-sociali-anno-2022/"
for dimension, state, evidence in (
    ("serie_storica", AVAILABLE, "Istat pubblica annualmente la rilevazione sulla spesa sociale dei Comuni e mantiene tavole confrontabili fra annualità successive."),
    ("dettaglio_territoriale", AVAILABLE, "Le tavole Istat diffondono dati per Comune e aggregazioni territoriali superiori, incluse Province e Regioni."),
    ("benchmark_toscana_italia", AVAILABLE, "La stessa rilevazione copre l'intero territorio nazionale e pubblica aggregati regionali e nazionali confrontabili con quelli comunali."),
    ("assoluto_normalizzato", AVAILABLE, "Istat pubblica la spesa sociale complessiva e indicatori pro capite, rendendo disponibili forma assoluta e normalizzata."),
    ("frequenza_infra_annuale", UNAVAILABLE, "La rilevazione sulla spesa sociale dei Comuni ha periodicità annuale e non diffonde una serie mensile, trimestrale o semestrale equivalente."),
    ("numeratore_denominatore", AVAILABLE, "Le tavole rendono disponibili gli importi di spesa e le popolazioni o i totali di spesa usati per indicatori pro capite e quote per area di utenza."),
    ("categorie_specifiche", AVAILABLE, "La spesa è articolata per aree di utenza e tipologie di intervento/servizio secondo la classificazione della rilevazione Istat."),
):
    _add_profile("istat-social-services-annual", dimension, state, evidence, ISTAT_SOCIAL_REF)


# IRPEF MEF: per quattro metriche le tavole comunali espongono frequenze,
# ammontari e medie/classi necessari a ricostruire valori assoluti e rapporti.
MEF_IRPEF_REF = "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php"
for metric_id, evidence_abs, evidence_numden in (
    (
        "income",
        "Le tavole comunali MEF espongono frequenza, ammontare del reddito imponibile e valore medio, consentendo di affiancare ammontare assoluto e media per contribuente.",
        "Le tavole MEF pubblicano ammontare del reddito imponibile e frequenza dei contribuenti, le due componenti della media comunale.",
    ),
    (
        "incomeDistribution",
        "Le tavole MEF espongono il numero di contribuenti per classe di reddito e il totale dei contribuenti, consentendo conteggi assoluti e quote per classe.",
        "La distribuzione per classe deriva dal numero di contribuenti della classe sul totale dei contribuenti, entrambi pubblicati nelle tavole comunali MEF.",
    ),
    (
        "incomeSourceProfile",
        "Le tavole MEF per fonte di reddito riportano frequenza, ammontare e media, consentendo valori assoluti e normalizzati per contribuente della fonte.",
        "Per ciascuna fonte di reddito il MEF pubblica ammontare e frequenza dei contribuenti, componenti della relativa media.",
    ),
    (
        "pensionIncomeShare",
        "Le tavole MEF pubblicano l'ammontare dei redditi da pensione e l'ammontare complessivo dei redditi, permettendo di affiancare importi assoluti e quota percentuale.",
        "La quota dei redditi da pensione usa l'ammontare dei redditi pensionistici al numeratore e l'ammontare complessivo dei redditi al denominatore, entrambi presenti nelle tavole MEF.",
    ),
):
    _add_metric(metric_id, "assoluto_normalizzato", AVAILABLE, evidence_abs, MEF_IRPEF_REF)
    _add_metric(metric_id, "numeratore_denominatore", AVAILABLE, evidence_numden, MEF_IRPEF_REF)


# Percorsi: il dataset curato espone geometrie e tipologie nel perimetro Versilia.
# Non esistono nello stesso dataset benchmark Toscana/Italia, una versione
# normalizzata dei conteggi o osservazioni temporali infra-annuali equivalenti.
PERCORSI_REF = "https://osservatorioversilia.it/percorsi/metodo.html"
for dimension, state, evidence in (
    ("dettaglio_territoriale", AVAILABLE, "Le tracce versionate contengono geometrie puntuali e lineari che consentono un dettaglio territoriale molto più fine del Comune."),
    ("benchmark_toscana_italia", UNAVAILABLE, "Il dataset curato è costruito sul perimetro Versilia e non contiene un inventario metodologicamente equivalente per l'intera Toscana o per l'Italia."),
    ("assoluto_normalizzato", UNAVAILABLE, "Il dataset pubblica conteggi e geometrie dei percorsi ma non associa un denominatore territoriale o demografico per produrre una misura normalizzata equivalente."),
    ("frequenza_infra_annuale", UNAVAILABLE, "Il dataset è un inventario editoriale aggiornato quando cambia una fonte validata e non una serie di osservazioni mensili, trimestrali o semestrali dello stesso indicatore."),
    ("categorie_specifiche", AVAILABLE, "Le tracce sono classificate per tipologia di percorso e modalità, incluse categorie trekking, cammini, bici e MTB."),
):
    _add_profile("percorsi-curated", dimension, state, evidence, PERCORSI_REF)


# Geografie funzionali Istat: classificazioni territoriali armonizzate sull'intero
# Paese. Lunghezza di costa e classe territoriale non hanno sesso/età né un
# numeratore/denominatore statistico.
ISTAT_FUNCTIONAL_REF = "https://www.istat.it/comunicato-stampa/geografie-funzionali-per-lanalisi-territoriale/"
_add_profile(
    "istat-geografie-funzionali-2021",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Le geografie funzionali Istat applicano classificazioni armonizzate ai Comuni dell'intero territorio nazionale, consentendo confronti coerenti con Toscana e Italia.",
    ISTAT_FUNCTIONAL_REF,
)
_add_profile(
    "istat-geografie-funzionali-2021",
    "frequenza_infra_annuale",
    UNAVAILABLE,
    "Le classificazioni funzionali sono riferite a specifiche basi territoriali e anni di riferimento e non sono diffuse come serie mensili, trimestrali o semestrali equivalenti.",
    ISTAT_FUNCTIONAL_REF,
)
for metric_id in ("statisticalCoastlineLength", "territorialClassification"):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica descrive una proprietà o classificazione del territorio; il sesso delle persone non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica descrive una proprietà o classificazione del territorio; l'età delle persone non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "numeratore_denominatore",
        NOT_APPLICABLE,
        "La metrica è una lunghezza assoluta o una classificazione territoriale e non è definita come rapporto, tasso o quota.",
    )
_add_metric(
    "territorialClassification",
    "categorie_specifiche",
    AVAILABLE,
    "Istat assegna i Comuni a categorie territoriali strutturate, incluse geografie costiere, DEGURBA e altre classificazioni funzionali armonizzate.",
    ISTAT_FUNCTIONAL_REF,
)


# Catasto Rifiuti ISPRA: stesso impianto nazionale, con valori assoluti, pro
# capite, percentuali e componenti dei rapporti. Le metriche non descrivono
# caratteristiche demografiche delle persone.
ISPRA_WASTE_REF = "https://www.catasto-rifiuti.isprambiente.it/index.php?pg=ru"
_add_profile(
    "ispra-environment-annual",
    "benchmark_toscana_italia",
    AVAILABLE,
    "Il Catasto Rifiuti ISPRA copre tutti i Comuni italiani e pubblica dati aggregabili per Regione e a livello nazionale con la stessa metodologia.",
    ISPRA_WASTE_REF,
)
_add_profile(
    "ispra-environment-annual",
    "numeratore_denominatore",
    AVAILABLE,
    "Il Catasto Rifiuti pubblica quantità totali, raccolta differenziata, popolazione e costi insieme a percentuali e valori pro capite, rendendo disponibili le componenti dei rapporti del profilo.",
    ISPRA_WASTE_REF,
)
for metric_id in ("recycling", "residualWaste", "wastePerResident", "wasteServiceCost"):
    _add_metric(
        metric_id,
        "sesso",
        NOT_APPLICABLE,
        "La metrica misura produzione, gestione o costo dei rifiuti urbani del territorio; il sesso delle persone non è una dimensione semantica dell'oggetto misurato.",
    )
    _add_metric(
        metric_id,
        "eta",
        NOT_APPLICABLE,
        "La metrica misura produzione, gestione o costo dei rifiuti urbani del territorio; l'età delle persone non è una dimensione semantica dell'oggetto misurato.",
    )


# Biblioteche Regione Toscana: il rapporto IFLA definisce esplicitamente indice
# di prestito e indice di impatto tramite prestiti/abitanti e utenti attivi/
# abitanti. L'orario settimanale è invece una durata assoluta.
LIBRARIES_REF = "https://www.regione.toscana.it/-/il-valore-delle-biblioteche-pubbliche-di-ente-locale-e-della-cooperazione-bibliotecaria"
for metric_id, evidence_abs, evidence_numden in (
    (
        "libraryActiveBorrowersPer100",
        "Il monitoraggio regionale pubblica utenti attivi e indice di impatto per 100 abitanti, permettendo di affiancare conteggio assoluto e misura normalizzata.",
        "L'indice di impatto è definito come utenti attivi diviso popolazione residente per 100; monitoraggio e formula rendono disponibili le due componenti.",
    ),
    (
        "libraryLoansPerResident",
        "Il monitoraggio regionale pubblica prestiti e indice di prestito per abitante, permettendo di affiancare numero assoluto di prestiti e misura normalizzata.",
        "L'indice di prestito è definito come numero di prestiti diviso popolazione residente; la fonte pubblica le componenti della formula.",
    ),
):
    _add_metric(metric_id, "assoluto_normalizzato", AVAILABLE, evidence_abs, LIBRARIES_REF)
    _add_metric(metric_id, "numeratore_denominatore", AVAILABLE, evidence_numden, LIBRARIES_REF)
_add_metric(
    "libraryWeeklyOpeningHours",
    "assoluto_normalizzato",
    NOT_APPLICABLE,
    "La metrica misura direttamente una durata settimanale in ore; non esiste una forma assoluta/normalizzata distinta dello stesso indicatore.",
)
_add_metric(
    "libraryWeeklyOpeningHours",
    "numeratore_denominatore",
    NOT_APPLICABLE,
    "La metrica è una durata settimanale in ore e non è definita come rapporto, tasso o quota.",
)


def main() -> None:
    ns["main"]()


if __name__ == "__main__":
    main()
