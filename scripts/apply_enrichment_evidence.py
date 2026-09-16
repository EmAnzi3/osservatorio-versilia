#!/usr/bin/env python3
"""Materializza evidenze A3.2 riusabili nei source profile della release pubblica.

Le annotazioni sono source-level: non enumerano indicatori e non costituiscono un
secondo catalogo. Vengono applicate al registry nello stesso workspace effimero
che costruisce l'Effective Public Catalog, dopo gli overlay di release.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "source-registry.json"

AVAILABLE = "AVAILABLE_MISSING"
UNAVAILABLE = "SOURCE_UNAVAILABLE"

EVIDENCE = {
    "openbdap-annual": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "OpenBDAP FET consente di analizzare l'andamento degli indicatori comunali su più esercizi di bilancio.",
            "sourceReference": "https://openbdap.rgs.mef.gov.it/it/FET/Analizza",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "OpenBDAP FET analizza singoli enti e confronta Comuni e territori, esponendo scale territoriali ulteriori rispetto al singolo Comune.",
            "sourceReference": "https://openbdap.rgs.mef.gov.it/it/FET/Analizza",
        },
        "assoluto_normalizzato": {
            "state": AVAILABLE,
            "evidence": "OpenBDAP FET espone grandezze di bilancio totali e analisi pro capite dei Comuni.",
            "sourceReference": "https://openbdap.rgs.mef.gov.it/it/FET/Analizza",
        },
        "frequenza_infra_annuale": {
            "state": UNAVAILABLE,
            "evidence": "La sezione FET pubblica dati di bilancio per esercizio, basati su bilanci di previsione e rendiconti approvati; per questi indicatori non è diffusa una serie mensile, trimestrale o semestrale omogenea.",
            "sourceReference": "https://openbdap.rgs.mef.gov.it/it/FET",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "OpenBDAP FET disaggrega entrate e spese secondo classificazioni contabili, incluse categorie come titoli e missioni.",
            "sourceReference": "https://openbdap.rgs.mef.gov.it/it/FET",
        },
    },
    "istat-business-annual": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "Istat pubblica tavole annuali Frame SBS Territoriale con la stessa famiglia di aggregati economici su più annualità consecutive.",
            "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "Le tavole Istat Frame SBS territoriale diffondono risultati per livelli comunali, provinciali e regionali.",
            "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
        },
        "benchmark_toscana_italia": {
            "state": AVAILABLE,
            "evidence": "Le tavole Frame SBS Territoriale espongono gli stessi aggregati a scala comunale e regionale, rendendo disponibile il confronto coerente con la Toscana.",
            "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
        },
        "frequenza_infra_annuale": {
            "state": UNAVAILABLE,
            "evidence": "Frame SBS Territoriale è diffuso da Istat con periodo di riferimento annuale; le tavole territoriali della stessa famiglia non costituiscono una serie infra-annuale omogenea.",
            "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "Le tavole Istat Frame SBS territoriale espongono settore di attività economica e ulteriori disaggregazioni delle unità locali.",
            "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
        },
    },
    "istat-census-annual": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "La banca dati del Censimento permanente rende disponibili annualità 2018-2024 e serie storiche censuarie precedenti.",
            "sourceReference": "https://www.istat.it/statistiche-per-temi/censimenti/popolazione-e-abitazioni/risultati/",
        },
        "sesso": {
            "state": AVAILABLE,
            "evidence": "Il Censimento permanente diffonde annualmente dati della popolazione per sesso a livello regionale, provinciale e comunale.",
            "sourceReference": "https://www.istat.it/comunicato-stampa/censimento-permanente-popolazione-e-abitazioni/",
        },
        "eta": {
            "state": AVAILABLE,
            "evidence": "Il Censimento permanente diffonde annualmente dati della popolazione per età a livello regionale, provinciale e comunale.",
            "sourceReference": "https://www.istat.it/comunicato-stampa/censimento-permanente-popolazione-e-abitazioni/",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "I risultati censuari sono navigabili per territorio e sono disponibili anche a livello di sezione e area sub-comunale per le edizioni diffuse.",
            "sourceReference": "https://www.istat.it/notizia/dati-per-sezioni-di-censimento/",
        },
        "benchmark_toscana_italia": {
            "state": AVAILABLE,
            "evidence": "Il Censimento permanente diffonde dati comparabili a livello regionale, provinciale e comunale, consentendo il riferimento Toscana e nazionale.",
            "sourceReference": "https://www.istat.it/comunicato-stampa/censimento-permanente-popolazione-e-abitazioni/",
        },
        "frequenza_infra_annuale": {
            "state": UNAVAILABLE,
            "evidence": "Istat restituisce i dati del Censimento permanente con cadenza annuale; la fonte censuaria non pubblica per queste variabili una serie infra-annuale metodologicamente equivalente.",
            "sourceReference": "https://www.istat.it/comunicato-stampa/censimento-permanente-popolazione-e-abitazioni/",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "Il Censimento permanente diffonde, oltre a sesso ed età, cittadinanza, grado di istruzione e occupazione come disaggregazioni strutturate della popolazione.",
            "sourceReference": "https://www.istat.it/comunicato-stampa/censimento-permanente-popolazione-e-abitazioni/",
        },
    },
    "istat-demography-annual": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "Demo Istat consente la ricerca della stessa variabile per territorio e per tutti i periodi disponibili; i flussi demografici sono diffusi su più annualità.",
            "sourceReference": "https://demo.istat.it/app/?i=CDQ&l=it",
        },
        "sesso": {
            "state": AVAILABLE,
            "evidence": "Le basi Demo Istat usate dal profilo diffondono popolazione e bilanci demografici distinti per sesso.",
            "sourceReference": "https://demo.istat.it/app/?i=P02",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "Demo Istat espone selezioni e download per ripartizione, regione, provincia e Comune.",
            "sourceReference": "https://demo.istat.it/app/?i=POS",
        },
        "benchmark_toscana_italia": {
            "state": AVAILABLE,
            "evidence": "Le basi Demo Istat consentono letture coerenti a scala comunale, provinciale, regionale e nazionale.",
            "sourceReference": "https://demo.istat.it/app/?i=POS",
        },
    },
    "siope-monthly": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "OpenBDAP pubblica dataset SIOPE omogenei per annualità successive, rendendo ricostruibile la serie dei movimenti di cassa.",
            "sourceReference": "https://bdap-opendata.rgs.mef.gov.it/opendata/spd_rnd_spe_sio_reg09_01_2026?metadati=showall",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "I dataset SIOPE contengono tutti gli enti della regione e identificano ogni ente, permettendo aggregazioni territoriali ulteriori.",
            "sourceReference": "https://bdap-opendata.rgs.mef.gov.it/opendata/spd_rnd_spe_sio_reg09_01_2026?metadati=showall",
        },
        "assoluto_normalizzato": {
            "state": AVAILABLE,
            "evidence": "Il dataset SIOPE espone sia Importo cumulato sia Popolazione ISTAT, consentendo letture assolute e normalizzate per popolazione.",
            "sourceReference": "https://bdap-opendata.rgs.mef.gov.it/opendata/spd_rnd_spe_sio_reg09_01_2026?metadati=showall",
        },
        "frequenza_infra_annuale": {
            "state": AVAILABLE,
            "evidence": "Il dataset SIOPE espone il campo Anno/Mese calendario e movimenti cumulati mensili.",
            "sourceReference": "https://bdap-opendata.rgs.mef.gov.it/opendata/spd_rnd_spe_sio_reg09_01_2026?metadati=showall",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "Il dataset SIOPE espone Titolo e Codice Gestionale con relative descrizioni, quindi categorie contabili native della fonte.",
            "sourceReference": "https://bdap-opendata.rgs.mef.gov.it/opendata/spd_rnd_spe_sio_reg09_01_2026?metadati=showall",
        },
    },
    "ars-toscana-mixed": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "Il portale ARS dichiara per ciascun indicatore il valore aggiornato all'ultimo anno disponibile e il relativo trend storico.",
            "sourceReference": "https://www.ars.toscana.it/aree-dintervento/la-salute-di/salute-dei-toscani/profilo-di-salute-dei-toscani/news/3394-da-oggi-tutti-gli-indicatori-dell-ars-accessibili-da-un-unica-pagina.html",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "Il sistema ARS rende gli indicatori territoriali consultabili per Comune e, secondo il dominio, per Zona-distretto, Azienda USL e Regione Toscana.",
            "sourceReference": "https://www.ars.toscana.it/news-ns/5367-profili-di-salute-2025-delle-zone-distretto-toscane-online-i-nuovi-documenti-per-la-programmazione-sanitaria.html",
        },
        "benchmark_toscana_italia": {
            "state": AVAILABLE,
            "evidence": "ARS documenta per gli indicatori territoriali il confronto con la Regione Toscana, coerente con la dimensione di benchmark regionale A3.",
            "sourceReference": "https://www.ars.toscana.it/news-ns/5367-profili-di-salute-2025-delle-zone-distretto-toscane-online-i-nuovi-documenti-per-la-programmazione-sanitaria.html",
        },
    },
    "mim-school-year": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "Il catalogo open data MIM conserva distribuzioni dello stesso dataset per più anni scolastici consecutivi, rendendo ricostruibili serie omogenee per le variabili scolastiche pubblicate.",
            "sourceReference": "https://dati.istruzione.it/opendata/opendata/catalog/ALUCORSOINDCLASTA20232420240831.json",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "Il Portale unico dei dati della scuola pubblica anagrafe delle scuole e dataset di studenti ed edilizia a livello di singola istituzione o sede, granularità più fine del Comune.",
            "sourceReference": "https://dati.istruzione.it/opendata/progetto/",
        },
        "frequenza_infra_annuale": {
            "state": UNAVAILABLE,
            "evidence": "Le distribuzioni MIM del profilo sono organizzate per anno scolastico e data di consolidamento; non costituiscono una serie mensile, trimestrale o semestrale omogenea degli stessi indicatori.",
            "sourceReference": "https://dati.istruzione.it/opendata/opendata/catalog/ALUCORSOINDCLASTA20232420240831.json",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "Il catalogo MIM espone disaggregazioni proprie del dominio scolastico, tra cui anno di corso, classe, genere, fascia di età, tempo scuola, indirizzo e attributi degli edifici.",
            "sourceReference": "https://dati.istruzione.it/opendata/approfondimenti/statistiche/",
        },
    },
    "regione-toscana-tourism-annual": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "La banca dati Turismo Toscana consente interrogazioni per anno a partire dal 2005 e pubblica serie storiche mensili delle presenze.",
            "sourceReference": "https://www.regione.toscana.it/statistiche/banca-dati-turismo",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "La banca dati Turismo diffonde movimento e strutture per Regione, Provincia, Ambiti turistici e tabelle comunali ufficiali.",
            "sourceReference": "https://www.regione.toscana.it/statistiche/banca-dati-turismo",
        },
        "benchmark_toscana_italia": {
            "state": AVAILABLE,
            "evidence": "La banca dati Turismo espone le stesse misure per il dettaglio comunale/sub-regionale e per il totale regionale, rendendo disponibile un benchmark Toscana coerente per anno e dominio.",
            "sourceReference": "https://www.regione.toscana.it/statistiche/banca-dati-turismo",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "La fonte regionale disaggrega i dati per tipologia ricettiva e provenienza dei clienti, oltre alle componenti di capacità ricettiva.",
            "sourceReference": "https://www.regione.toscana.it/statistiche/banca-dati-turismo",
        },
    },
    "regione-toscana-indicatori-comunali": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "Regione Toscana diffonde annualmente la batteria degli indicatori comunali e rende disponibili i file 2018-2023 con visualizzazione dell'andamento nel tempo.",
            "sourceReference": "https://www.regione.toscana.it/-/indicatori-comunali-per-le-politiche-locali",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "L'interrogazione regionale permette il confronto tra Comuni e include il valore regionale annuale, quindi una scala territoriale più ampia del Comune.",
            "sourceReference": "https://www.regione.toscana.it/-/indicatori-comunali-per-le-politiche-locali",
        },
        "benchmark_toscana_italia": {
            "state": AVAILABLE,
            "evidence": "Regione Toscana specifica che tutti i grafici della dinamica degli indicatori comunali contengono il valore regionale annuale.",
            "sourceReference": "https://www.regione.toscana.it/-/indicatori-comunali-per-le-politiche-locali",
        },
        "frequenza_infra_annuale": {
            "state": UNAVAILABLE,
            "evidence": "Regione Toscana dichiara esplicitamente annuale l'aggiornamento della batteria degli indicatori comunali; non è disponibile una cadenza infra-annuale comune al set.",
            "sourceReference": "https://www.regione.toscana.it/-/indicatori-comunali-per-le-politiche-locali",
        },
    },
    "istat-agriculture-census-2020": {
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "Istat descrive il Censimento Agricoltura 2020 come banca dati nazionale con dettaglio fino al livello comunale, quindi con scale territoriali più ampie coerenti.",
            "sourceReference": "https://www.istat.it/dati/banche-dati/",
        },
        "frequenza_infra_annuale": {
            "state": UNAVAILABLE,
            "evidence": "Il profilo deriva dal 7° Censimento generale dell'Agricoltura 2020, una rilevazione censuaria puntuale che non fornisce osservazioni mensili, trimestrali o semestrali equivalenti.",
            "sourceReference": "https://www.istat.it/statistiche-per-temi/censimenti/agricoltura/7-censimento-generale/",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "Il Censimento Agricoltura diffonde aziende, superficie, coltivazioni, irrigazione, mezzi meccanici, allevamenti e forza lavoro come disaggregazioni proprie del dominio.",
            "sourceReference": "https://www.istat.it/dati/banche-dati/",
        },
    },
    "mef-irpef-annual": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "L'Open Data Dichiarazioni del Dipartimento delle Finanze pubblica le stesse principali variabili IRPEF comunali per annualità successive, incluse le serie storiche disponibili nel catalogo.",
            "sourceReference": "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes&search_class%5B0%5D=cCOMUNE",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "Il Dipartimento delle Finanze pubblica dati IRPEF sia comunali sia sub-comunali per CAP e rende disponibili anche classificazioni regionali.",
            "sourceReference": "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes&search_class%5B0%5D=cCOMUNE",
        },
        "benchmark_toscana_italia": {
            "state": AVAILABLE,
            "evidence": "L'Open Data Dichiarazioni pubblica classificazioni comunali e regionali delle principali variabili IRPEF, consentendo un confronto coerente con la Toscana per anno d'imposta.",
            "sourceReference": "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes",
        },
        "frequenza_infra_annuale": {
            "state": UNAVAILABLE,
            "evidence": "Le statistiche IRPEF del Dipartimento delle Finanze sono organizzate per anno di dichiarazione/anno d'imposta; non è diffusa una serie infra-annuale equivalente delle variabili comunali.",
            "sourceReference": "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes&search_class%5B0%5D=cCOMUNE",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "La fonte MEF espone classi di reddito, tipologie di contribuente e diverse componenti reddituali e fiscali come classificazioni strutturate.",
            "sourceReference": "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes",
        },
    },
    "agcom-quarterly": {
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "La reportistica Broadband Map AGCOM diffonde indicatori di copertura a livello comunale, provinciale e regionale.",
            "sourceReference": "https://geo.agcom.it/reportistica/",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "La Broadband Map distingue tecnologie e prestazioni di accesso, incluse reti fisse cablate, FTTH, FTTC/VDSL, FWA e reti mobili.",
            "sourceReference": "https://geo.agcom.it/visura/estratto-completo.html",
        },
    },
    "rgs-conto-annuale-annual": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "Il Conto Annuale consente il download dei microdati selezionando l'anno e pubblica analisi della struttura del personale e delle sue modifiche nel tempo.",
            "sourceReference": "https://contoannuale.rgs.mef.gov.it/web/sicosito/download",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "Il Conto Annuale pubblica la distribuzione del personale per Regione, Provincia e Comune e consente filtri territoriali nelle tabelle.",
            "sourceReference": "https://contoannuale.rgs.mef.gov.it/it/web/sicosito/dati-pubblicati",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "Il Conto Annuale pubblica disaggregazioni per comparto, contratto, categoria, qualifica, fascia retributiva, anzianità, titolo di studio e altre caratteristiche del personale.",
            "sourceReference": "https://contoannuale.rgs.mef.gov.it/it/web/sicosito/dati-pubblicati",
        },
    },
    "istat-commuting-irregular": {
        "serie_storica": {
            "state": UNAVAILABLE,
            "evidence": "La matrice 2021 è prodotta con il Censimento permanente integrato con registri e fonti amministrative; le matrici storiche precedenti derivano dai censimenti generali e non costituiscono una serie omogenea con la stessa metodologia.",
            "sourceReference": "https://www.istat.it/comunicato-stampa/la-nuova-geografia-dei-sistemi-locali-del-lavoro-anno-2021/",
        },
        "sesso": {
            "state": UNAVAILABLE,
            "evidence": "La release Istat 2021 della matrice di pendolarismo per lavoro descrive il file come conteggio origine-destinazione tra Comuni e non pubblica una disaggregazione per sesso nella matrice corrente.",
            "sourceReference": "https://www.istat.it/notizia/matrice-di-pendolarismo-per-lavoro/",
        },
        "eta": {
            "state": UNAVAILABLE,
            "evidence": "La release Istat 2021 della matrice di pendolarismo per lavoro pubblica i conteggi origine-destinazione degli occupati senza una dimensione per classe di età nella matrice corrente.",
            "sourceReference": "https://www.istat.it/notizia/matrice-di-pendolarismo-per-lavoro/",
        },
        "frequenza_infra_annuale": {
            "state": UNAVAILABLE,
            "evidence": "La matrice ufficiale è riferita al 31 dicembre 2021 ed è un prodotto censuario, non una rilevazione mensile, trimestrale o semestrale.",
            "sourceReference": "https://www.istat.it/notizia/matrice-di-pendolarismo-per-lavoro/",
        },
        "categorie_specifiche": {
            "state": UNAVAILABLE,
            "evidence": "La matrice 2021 pubblicata da Istat contiene il numero di persone che si spostano tra Comuni o all'interno dello stesso Comune; le disaggregazioni per mezzo, fascia oraria e durata documentate per il 2011 non sono pubblicate nella release 2021 corrente.",
            "sourceReference": "https://www.istat.it/notizia/matrici-di-contiguita-distanza-e-pendolarismo/",
        },
    },
}


def main() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    profiles = registry.get("sourceProfiles")
    if not isinstance(profiles, dict):
        raise RuntimeError("A3.2: sourceProfiles assente dal registry")

    applied = 0
    for profile_id, dimensions in EVIDENCE.items():
        profile = profiles.get(profile_id)
        if not isinstance(profile, dict):
            raise RuntimeError(f"A3.2: source profile mancante: {profile_id}")
        target = profile.setdefault("enrichmentDimensions", {})
        if not isinstance(target, dict):
            raise RuntimeError(f"A3.2: enrichmentDimensions non-oggetto: {profile_id}")
        for dimension, annotation in dimensions.items():
            existing = target.get(dimension)
            if existing is not None and existing != annotation:
                raise RuntimeError(
                    f"A3.2: evidenza già presente ma diversa: {profile_id}/{dimension}"
                )
            target[dimension] = annotation
            applied += 1

    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"A3.2 source-profile evidence materializzata: {applied} dimensioni su {len(EVIDENCE)} profili")


if __name__ == "__main__":
    main()