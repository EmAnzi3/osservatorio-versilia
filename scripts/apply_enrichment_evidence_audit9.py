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


# Evidenza source-level: solo dimensioni omogenee sull’intero profilo.
_add_profile('agenzia-entrate-omi-semestral', 'assoluto_normalizzato', UNAVAILABLE, 'OMI pubblica quotazioni già rapportate all’unità di superficie in €/m² e non un valore assoluto immobiliare territorialmente equivalente.', 'https://telematici.agenziaentrate.gov.it/pdf/guidaFornitureOMI.pdf')
_add_profile('agenzia-entrate-omi-semestral', 'benchmark_toscana_italia', AVAILABLE, 'La banca dati OMI copre i Comuni censiti negli archivi catastali su scala nazionale con la stessa struttura.', 'https://telematici.agenziaentrate.gov.it/pdf/guidaFornitureOMI.pdf')
_add_profile('agenzia-entrate-omi-semestral', 'categorie_specifiche', AVAILABLE, 'Le quotazioni sono distinte per tipologia immobiliare e stato di manutenzione/conservazione.', 'https://telematici.agenziaentrate.gov.it/pdf/guidaFornitureOMI.pdf')
_add_profile('agenzia-entrate-omi-semestral', 'dettaglio_territoriale', AVAILABLE, 'OMI pubblica intervalli di quotazione per singola zona territoriale omogenea all’interno dei Comuni censiti.', 'https://telematici.agenziaentrate.gov.it/pdf/guidaFornitureOMI.pdf')
_add_profile('agenzia-entrate-omi-semestral', 'frequenza_infra_annuale', AVAILABLE, 'Le quotazioni OMI sono pubblicate con cadenza semestrale.', 'https://telematici.agenziaentrate.gov.it/pdf/guidaFornitureOMI.pdf')
_add_profile('agenzia-entrate-omi-semestral', 'serie_storica', AVAILABLE, 'Le quotazioni OMI sono pubblicate per semestre e gli archivi consentono il confronto tra semestri successivi.', 'https://telematici.agenziaentrate.gov.it/pdf/guidaFornitureOMI.pdf')
_add_profile('erp-lucca-annual-balance-sheet', 'assoluto_normalizzato', AVAILABLE, 'I prospetti pubblicano importi cumulati di morosità e importi emessi, consentendo di affiancare valori assoluti e quota percentuale.', 'https://at.erplucca.it/default?path=75&t=1')
_add_profile('erp-lucca-annual-balance-sheet', 'benchmark_toscana_italia', UNAVAILABLE, 'La fonte ERP Lucca copre il proprio ambito di gestione e non pubblica un indicatore metodologicamente equivalente per l’intera Toscana o l’Italia.', 'https://at.erplucca.it/default?path=75&t=1')
_add_profile('erp-lucca-annual-balance-sheet', 'dettaglio_territoriale', AVAILABLE, 'I prospetti contabili usati per l’indicatore distinguono gli importi riferiti ai singoli Comuni soci/territori gestiti.', 'https://at.erplucca.it/default?path=75&t=1')
_add_profile('erp-lucca-annual-balance-sheet', 'frequenza_infra_annuale', UNAVAILABLE, 'La fonte utilizzata è il bilancio d’esercizio annuale e non pubblica una serie infra-annuale equivalente per Comune.', 'https://at.erplucca.it/default?path=75&t=1')
_add_profile('erp-lucca-annual-balance-sheet', 'serie_storica', AVAILABLE, 'I bilanci d’esercizio ERP Lucca pubblicano prospetti annuali e consentono la ricostruzione omogenea della morosità su più esercizi.', 'https://at.erplucca.it/default?path=75&t=1')
_add_profile('fee-blue-flag-annual', 'assoluto_normalizzato', UNAVAILABLE, 'La fonte pubblica l’elenco e quindi i conteggi delle località premiate, ma non un indicatore normalizzato territorialmente o demograficamente equivalente.', 'https://www.bandierablu.org/common/blueflag.asp?anno=2026&tipo=bb')
_add_profile('fee-blue-flag-annual', 'benchmark_toscana_italia', AVAILABLE, 'L’elenco è nazionale e permette confronti omogenei tra Toscana e totale Italia.', 'https://www.bandierablu.org/common/blueflag.asp?anno=2026&tipo=bb')
_add_profile('fee-blue-flag-annual', 'categorie_specifiche', UNAVAILABLE, 'L’elenco spiagge/località premiate non pubblica una disaggregazione interna stabile dell’indicatore per categorie specifiche.', 'https://www.bandierablu.org/common/blueflag.asp?anno=2026&tipo=bb')
_add_profile('fee-blue-flag-annual', 'dettaglio_territoriale', AVAILABLE, 'L’elenco ufficiale identifica Regione, Provincia, Comune e località premiata.', 'https://www.bandierablu.org/common/blueflag.asp?anno=2026&tipo=bb')
_add_profile('fee-blue-flag-annual', 'frequenza_infra_annuale', UNAVAILABLE, 'Bandiera Blu è un riconoscimento assegnato annualmente e non esiste una serie infra-annuale equivalente.', 'https://www.bandierablu.org/common/blueflag.asp?anno=2026&tipo=bb')
_add_profile('fee-blue-flag-annual', 'serie_storica', AVAILABLE, 'FEE pubblica elenchi annuali delle località Bandiera Blu selezionabili per anno, consentendo una serie storica del riconoscimento.', 'https://www.bandierablu.org/common/blueflag.asp?anno=2026&tipo=bb')
_add_profile('invalsi-open-dispersione-2025', 'assoluto_normalizzato', UNAVAILABLE, 'Il dataset pubblica punteggi o percentuali già calcolati e non una corrispondente grandezza assoluta omogenea dello stesso indicatore.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/eccellenza-accademica-e-dispersione-scolastica-implicita-valori-percentuali/')
_add_profile('invalsi-open-dispersione-2025', 'categorie_specifiche', AVAILABLE, 'La fonte consente analisi per materia e per caratteristiche di contesto come origine e tipologia di istituto, oltre al genere.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/eccellenza-accademica-e-dispersione-scolastica-implicita-valori-percentuali/')
_add_profile('invalsi-open-dispersione-2025', 'eta', UNAVAILABLE, 'La tavola ufficiale espone genere, origine, tipologia di istituto e annualità, ma non una disaggregazione per età degli studenti equivalente a quella richiesta.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/eccellenza-accademica-e-dispersione-scolastica-implicita-valori-percentuali/')
_add_profile('invalsi-open-dispersione-2025', 'frequenza_infra_annuale', UNAVAILABLE, 'La rilevazione e la pubblicazione sono annuali per anno scolastico; non esiste una serie infra-annuale equivalente dello stesso indicatore.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/eccellenza-accademica-e-dispersione-scolastica-implicita-valori-percentuali/')
_add_profile('invalsi-open-dispersione-2025', 'serie_storica', AVAILABLE, 'INVALSI rende i dati per annualità e mantiene archivi di più annualità delle rilevazioni di popolazione.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/eccellenza-accademica-e-dispersione-scolastica-implicita-valori-percentuali/')
_add_profile('invalsi-open-dispersione-2025', 'sesso', AVAILABLE, 'La tavola analitica INVALSI espone esplicitamente il genere tra le sottocategorie disponibili per le analisi.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/eccellenza-accademica-e-dispersione-scolastica-implicita-valori-percentuali/')
_add_profile('invalsi-open-risultati-2025', 'assoluto_normalizzato', UNAVAILABLE, 'Il dataset pubblica punteggi o percentuali già calcolati e non una corrispondente grandezza assoluta omogenea dello stesso indicatore.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/punteggi-e-percentuale-di-studenti-nei-livelli-di-competenza-per-ripartizioni-territoriali-e-caratteristiche-di-contesto/')
_add_profile('invalsi-open-risultati-2025', 'categorie_specifiche', AVAILABLE, 'La fonte consente analisi per materia e per caratteristiche di contesto come origine e tipologia di istituto, oltre al genere.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/punteggi-e-percentuale-di-studenti-nei-livelli-di-competenza-per-ripartizioni-territoriali-e-caratteristiche-di-contesto/')
_add_profile('invalsi-open-risultati-2025', 'eta', UNAVAILABLE, 'La tavola ufficiale espone genere, origine, tipologia di istituto e annualità, ma non una disaggregazione per età degli studenti equivalente a quella richiesta.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/punteggi-e-percentuale-di-studenti-nei-livelli-di-competenza-per-ripartizioni-territoriali-e-caratteristiche-di-contesto/')
_add_profile('invalsi-open-risultati-2025', 'frequenza_infra_annuale', UNAVAILABLE, 'La rilevazione e la pubblicazione sono annuali per anno scolastico; non esiste una serie infra-annuale equivalente dello stesso indicatore.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/punteggi-e-percentuale-di-studenti-nei-livelli-di-competenza-per-ripartizioni-territoriali-e-caratteristiche-di-contesto/')
_add_profile('invalsi-open-risultati-2025', 'serie_storica', AVAILABLE, 'INVALSI rende i dati per annualità e mantiene archivi di più annualità delle rilevazioni di popolazione.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/punteggi-e-percentuale-di-studenti-nei-livelli-di-competenza-per-ripartizioni-territoriali-e-caratteristiche-di-contesto/')
_add_profile('invalsi-open-risultati-2025', 'sesso', AVAILABLE, 'La tavola analitica INVALSI espone esplicitamente il genere tra le sottocategorie disponibili per le analisi.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/punteggi-e-percentuale-di-studenti-nei-livelli-di-competenza-per-ripartizioni-territoriali-e-caratteristiche-di-contesto/')
_add_profile('ispra-idrogeo-risk', 'assoluto_normalizzato', AVAILABLE, 'ISPRA affianca ai conteggi assoluti degli elementi esposti le percentuali sul totale di riferimento.', 'https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/dissesto-idrogeologico/indicatori-di-rischio')
_add_profile('ispra-idrogeo-risk', 'benchmark_toscana_italia', AVAILABLE, 'Gli indicatori sono nazionali e consentono confronti fra totale Italia e Regioni, inclusa la Toscana, con la stessa metodologia.', 'https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/dissesto-idrogeologico/indicatori-di-rischio')
_add_profile('ispra-idrogeo-risk', 'categorie_specifiche', AVAILABLE, 'La fonte distingue frane e alluvioni, classi/scenari di pericolosità e diverse categorie di elementi esposti.', 'https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/dissesto-idrogeologico/indicatori-di-rischio')
_add_profile('ispra-idrogeo-risk', 'dettaglio_territoriale', AVAILABLE, 'ISPRA pubblica la popolazione a rischio frane e alluvioni su base comunale e rende disponibili le mosaicature nazionali di pericolosità.', 'https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/dissesto-idrogeologico/indicatori-di-rischio')
_add_profile('ispra-idrogeo-risk', 'eta', UNAVAILABLE, 'Il set ufficiale degli indicatori IdroGEO pubblica la popolazione esposta complessiva e gli altri oggetti esposti, ma non una disaggregazione della popolazione a rischio per classi di età.', 'https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/dissesto-idrogeologico/indicatori-di-rischio')
_add_profile('ispra-idrogeo-risk', 'frequenza_infra_annuale', UNAVAILABLE, 'Le mosaicature e gli indicatori di rischio sono aggiornati per edizioni periodiche del rapporto; la fonte non diffonde una serie mensile, trimestrale o semestrale equivalente.', 'https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/dissesto-idrogeologico/indicatori-di-rischio')
_add_profile('ispra-idrogeo-risk', 'numeratore_denominatore', AVAILABLE, 'Per gli indicatori percentuali ISPRA pubblica sia il numero di elementi esposti sia la quota sul totale, rendendo ricostruibili numeratore e denominatore.', 'https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/dissesto-idrogeologico/indicatori-di-rischio')
_add_profile('ispra-idrogeo-risk', 'serie_storica', AVAILABLE, 'ISPRA ha pubblicato edizioni successive degli indicatori nazionali di rischio idrogeologico (2018, 2021 e 2024), con definizioni confrontabili per frane e alluvioni.', 'https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/dissesto-idrogeologico/indicatori-di-rischio')
_add_profile('ispra-idrogeo-risk', 'sesso', UNAVAILABLE, 'Il set ufficiale degli indicatori IdroGEO articola il rischio per popolazione, famiglie, edifici, imprese/servizi e beni culturali, ma non pubblica una disaggregazione della popolazione esposta per sesso.', 'https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/dissesto-idrogeologico/indicatori-di-rischio')
_add_profile('istat-water-irregular', 'assoluto_normalizzato', AVAILABLE, 'Istat pubblica i volumi assoluti di acqua immessa ed erogata e la percentuale di perdite della rete.', 'https://www.istat.it/comunicato-stampa/censimento-delle-acque-per-uso-civile-anno-2018/')
_add_profile('istat-water-irregular', 'benchmark_toscana_italia', AVAILABLE, 'La rilevazione è nazionale e rende disponibili aggregati territoriali coerenti per Regioni e Italia.', 'https://www.istat.it/comunicato-stampa/censimento-delle-acque-per-uso-civile-anno-2018/')
_add_profile('istat-water-irregular', 'categorie_specifiche', UNAVAILABLE, 'Per la percentuale di perdite della rete comunale la fonte non diffonde una scomposizione stabile dello stesso indicatore in categorie specifiche.', 'https://www.istat.it/comunicato-stampa/censimento-delle-acque-per-uso-civile-anno-2018/')
_add_profile('istat-water-irregular', 'dettaglio_territoriale', AVAILABLE, 'Il Censimento rende disponibili i volumi della distribuzione dell’acqua potabile con dettaglio territoriale fino alle reti comunali.', 'https://www.istat.it/comunicato-stampa/censimento-delle-acque-per-uso-civile-anno-2018/')
_add_profile('istat-water-irregular', 'frequenza_infra_annuale', UNAVAILABLE, 'Il Censimento delle acque ha periodicità censuaria/irregolare e non pubblica una serie infra-annuale comunale equivalente.', 'https://www.istat.it/comunicato-stampa/censimento-delle-acque-per-uso-civile-anno-2018/')
_add_profile('istat-water-irregular', 'serie_storica', AVAILABLE, 'Istat pubblica più edizioni del Censimento delle acque per uso civile e confronta i volumi e le perdite con precedenti rilevazioni censuarie.', 'https://www.istat.it/comunicato-stampa/censimento-delle-acque-per-uso-civile-anno-2018/')
_add_profile('mef-municipal-irpef-annual', 'assoluto_normalizzato', AVAILABLE, 'Aliquote, scaglioni ed esenzioni ufficiali permettono di affiancare la struttura percentuale alla corrispondente imposta assoluta su una base imponibile standardizzata.', 'https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/')
_add_profile('mef-municipal-irpef-annual', 'benchmark_toscana_italia', AVAILABLE, 'La banca dati copre i Comuni italiani con la stessa struttura, consentendo confronti fra Toscana e Italia.', 'https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/')
_add_profile('mef-municipal-irpef-annual', 'categorie_specifiche', AVAILABLE, 'La fonte distingue scaglioni/fasce di reddito, aliquote applicabili ed eventuali soglie di esenzione.', 'https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/')
_add_profile('mef-municipal-irpef-annual', 'dettaglio_territoriale', AVAILABLE, 'La banca dati è interrogabile per singolo Comune e Provincia.', 'https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/')
_add_profile('mef-municipal-irpef-annual', 'frequenza_infra_annuale', UNAVAILABLE, 'Aliquote ed esenzioni sono disciplinate per anno d’imposta e la fonte non pubblica una serie infra-annuale equivalente.', 'https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/')
_add_profile('mef-municipal-irpef-annual', 'serie_storica', AVAILABLE, 'La banca dati MEF consente di selezionare l’anno e conserva aliquote, scaglioni ed esenzioni delle annualità comunali.', 'https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/')
_add_profile('regione-toscana-prc-annual', 'benchmark_toscana_italia', AVAILABLE, 'Le stesse tavole PRC aggregano i dati per Comune, Provincia e intera Regione Toscana, consentendo un benchmark regionale coerente.', 'https://www.regione.toscana.it/piano-regionale-cave')
_add_profile('regione-toscana-prc-annual', 'categorie_specifiche', AVAILABLE, 'Il PRC distingue materiali da costruzione, industriali, ornamentali e relativi derivati e RTCave distingue tipo di materiale, tipo di cava e stato della cava.', 'https://www.regione.toscana.it/piano-regionale-cave')
_add_profile('regione-toscana-prc-annual', 'dettaglio_territoriale', AVAILABLE, 'Il PRC pubblica tavole e dati per cava e aggregazioni per Comune, Provincia e Regione, con dettaglio specifico per l’area Apuo-Versiliese.', 'https://www.regione.toscana.it/piano-regionale-cave')
_add_profile('regione-toscana-prc-annual', 'frequenza_infra_annuale', UNAVAILABLE, 'Il monitoraggio dell’attività estrattiva è basato su obblighi informativi annuali e il PRC non pubblica una serie infra-annuale metodologicamente equivalente.', 'https://www.regione.toscana.it/piano-regionale-cave')
_add_profile('sisbon-weekly', 'assoluto_normalizzato', AVAILABLE, 'ARPAT pubblica numero, superficie, densità e anche quote percentuali dei siti/procedimenti per stato o tipologia.', 'https://www.arpat.toscana.it/le-bonifiche-in-toscana/')
_add_profile('sisbon-weekly', 'benchmark_toscana_italia', AVAILABLE, 'ARPAT pubblica il totale regionale toscano con la stessa definizione usata per le disaggregazioni provinciali e comunali.', 'https://www.arpat.toscana.it/le-bonifiche-in-toscana/')
_add_profile('sisbon-weekly', 'categorie_specifiche', AVAILABLE, 'ARPAT distingue stato dell’iter e tipologia di attività e pubblica conteggi e superfici per tali categorie.', 'https://www.arpat.toscana.it/le-bonifiche-in-toscana/')
_add_profile('sisbon-weekly', 'dettaglio_territoriale', AVAILABLE, 'Gli indicatori sono disponibili su base provinciale e negli Annuari provinciali anche a livello comunale; SISBON espone il singolo procedimento.', 'https://www.arpat.toscana.it/le-bonifiche-in-toscana/')
_add_profile('sisbon-weekly', 'frequenza_infra_annuale', UNAVAILABLE, 'SISBON è una banca dati operativa aggiornata durante l’anno, ma la fonte non conserva una serie ufficiale mensile/trimestrale dello stesso conteggio; lo storico pubblicato è annuale.', 'https://www.arpat.toscana.it/le-bonifiche-in-toscana/')
_add_profile('sisbon-weekly', 'serie_storica', AVAILABLE, 'ARPAT pubblica indicatori sui procedimenti di bonifica per più annualità dal 2011 al 2025 e file con anni precedenti.', 'https://www.arpat.toscana.it/le-bonifiche-in-toscana/')

# Override metric-specific: sole eccezioni semantiche o componenti proprie della metrica.
_add_metric('blueFlagBeaches', 'eta', NOT_APPLICABLE, 'La metrica conta località/spiagge premiate; l’età non è una dimensione semantica dell’oggetto misurato.')
_add_metric('blueFlagBeaches', 'numeratore_denominatore', NOT_APPLICABLE, 'La metrica è un conteggio di località/spiagge premiate e non un rapporto o tasso.')
_add_metric('blueFlagBeaches', 'sesso', NOT_APPLICABLE, 'La metrica conta località/spiagge premiate; il sesso non è una dimensione semantica dell’oggetto misurato.')
_add_metric('erpArrears', 'eta', NOT_APPLICABLE, 'La metrica misura morosità contabile ERP; l’età degli assegnatari non è una dimensione della grandezza finanziaria pubblicata.')
_add_metric('erpArrears', 'numeratore_denominatore', AVAILABLE, 'La percentuale è ricostruibile dagli importi cumulati di morosità e dagli importi emessi pubblicati nei prospetti contabili.', 'https://at.erplucca.it/default?path=75&t=1')
_add_metric('erpArrears', 'sesso', NOT_APPLICABLE, 'La metrica misura morosità contabile ERP; il sesso degli assegnatari non è una dimensione della grandezza finanziaria pubblicata.')
_add_metric('extractivePlanning', 'assoluto_normalizzato', AVAILABLE, 'Le geometrie PRC consentono di calcolare sia la superficie assoluta interessata sia la quota sul territorio comunale usando i confini amministrativi ufficiali.', 'https://www.regione.toscana.it/piano-regionale-cave')
_add_metric('extractivePlanning', 'eta', NOT_APPLICABLE, 'La metrica descrive superfici pianificate o volumi estratti; l’età delle persone non è una dimensione semantica dell’oggetto misurato.')
_add_metric('extractivePlanning', 'numeratore_denominatore', AVAILABLE, 'La quota di territorio comunale interessata deriva dalla superficie PRC intersecata divisa per la superficie amministrativa comunale, entrambe ricostruibili dai dati regionali ufficiali.', 'https://www.regione.toscana.it/piano-regionale-cave')
_add_metric('extractivePlanning', 'serie_storica', UNAVAILABLE, 'Il PRC rende disponibile il quadro pianificatorio vigente e le sue varianti, ma non una serie storica omogenea della stessa superficie comunale pianificata.', 'https://www.regione.toscana.it/piano-regionale-cave')
_add_metric('extractivePlanning', 'sesso', NOT_APPLICABLE, 'La metrica descrive superfici pianificate o volumi estratti; il sesso delle persone non è una dimensione semantica dell’oggetto misurato.')
_add_metric('extractiveProduction', 'assoluto_normalizzato', AVAILABLE, 'Il PRC pubblica volumi estratti e anche volumi estratti per addetto, consentendo forma assoluta e normalizzata della produzione.', 'https://www.regione.toscana.it/piano-regionale-cave')
_add_metric('extractiveProduction', 'eta', NOT_APPLICABLE, 'La metrica descrive superfici pianificate o volumi estratti; l’età delle persone non è una dimensione semantica dell’oggetto misurato.')
_add_metric('extractiveProduction', 'numeratore_denominatore', NOT_APPLICABLE, 'La metrica pubblicata è il volume assoluto estratto; non è definita come rapporto, tasso o quota con un unico numeratore e denominatore.')
_add_metric('extractiveProduction', 'sesso', NOT_APPLICABLE, 'La metrica descrive superfici pianificate o volumi estratti; il sesso delle persone non è una dimensione semantica dell’oggetto misurato.')
_add_metric('invalsiAcademicExcellence', 'numeratore_denominatore', UNAVAILABLE, 'La fonte pubblica il valore percentuale dell’indicatore ma non i conteggi territoriali elementari necessari a ricostruire numeratore e denominatore.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/eccellenza-accademica-e-dispersione-scolastica-implicita-valori-percentuali/')
_add_metric('invalsiCompetence', 'numeratore_denominatore', UNAVAILABLE, 'La fonte pubblica la percentuale di studenti nei livelli di competenza ma non espone nel dataset aggregato i conteggi necessari a ricostruire un numeratore e un denominatore territoriale omogenei.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/punteggi-e-percentuale-di-studenti-nei-livelli-di-competenza-per-ripartizioni-territoriali-e-caratteristiche-di-contesto/')
_add_metric('invalsiImplicitDispersion', 'numeratore_denominatore', UNAVAILABLE, 'La fonte pubblica il valore percentuale dell’indicatore ma non i conteggi territoriali elementari necessari a ricostruire numeratore e denominatore.', 'https://serviziostatistico.invalsi.it/invalsi_ss_data/eccellenza-accademica-e-dispersione-scolastica-implicita-valori-percentuali/')
_add_metric('invalsiResults', 'numeratore_denominatore', NOT_APPLICABLE, 'Il punteggio medio WLE non è definito come rapporto con un singolo numeratore e denominatore.')
_add_metric('municipalIrpef', 'eta', NOT_APPLICABLE, 'La metrica applica la disciplina tributaria a uno scenario standard di reddito imponibile; l’età non è una dimensione generale dell’aliquota comunale.')
_add_metric('municipalIrpef', 'numeratore_denominatore', NOT_APPLICABLE, 'L’importo dovuto deriva dall’applicazione di aliquote/scaglioni alla base imponibile e non è un indicatore definito come rapporto statistico numeratore/denominatore.')
_add_metric('municipalIrpef', 'sesso', NOT_APPLICABLE, 'La metrica applica la disciplina tributaria a uno scenario standard di reddito imponibile; il sesso non è una dimensione dell’aliquota comunale.')
_add_metric('omiResidential', 'eta', NOT_APPLICABLE, 'La metrica descrive quotazioni immobiliari; l’età delle persone non è una dimensione semantica dell’immobile o della zona OMI.')
_add_metric('omiResidential', 'numeratore_denominatore', NOT_APPLICABLE, 'La quotazione in €/m² è un valore unitario di mercato/locazione e non è definita come un rapporto statistico con numeratore e denominatore pubblicati.')
_add_metric('omiResidential', 'sesso', NOT_APPLICABLE, 'La metrica descrive quotazioni immobiliari; il sesso non è una dimensione semantica dell’immobile o della zona OMI.')
_add_metric('remediationProceedings', 'eta', NOT_APPLICABLE, 'La metrica conta procedimenti/siti di bonifica; l’età delle persone non è una dimensione semantica dell’oggetto misurato.')
_add_metric('remediationProceedings', 'numeratore_denominatore', NOT_APPLICABLE, 'La metrica è un conteggio di procedimenti e non un rapporto, tasso o quota.')
_add_metric('remediationProceedings', 'sesso', NOT_APPLICABLE, 'La metrica conta procedimenti/siti di bonifica; il sesso delle persone non è una dimensione semantica dell’oggetto misurato.')
_add_metric('waterNetworkLosses', 'eta', NOT_APPLICABLE, 'La metrica descrive volumi e perdite della rete idrica; l’età non è una dimensione semantica del fenomeno.')
_add_metric('waterNetworkLosses', 'numeratore_denominatore', AVAILABLE, 'Istat pubblica acqua immessa e acqua erogata; la perdita percentuale è ricostruibile dalla loro differenza rapportata all’acqua immessa.', 'https://www.istat.it/comunicato-stampa/censimento-delle-acque-per-uso-civile-anno-2018/')
_add_metric('waterNetworkLosses', 'sesso', NOT_APPLICABLE, 'La metrica descrive volumi e perdite della rete idrica; il sesso non è una dimensione semantica del fenomeno.')


def main() -> None:
    ns["main"]()


if __name__ == "__main__":
    main()
