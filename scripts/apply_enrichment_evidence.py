#!/usr/bin/env python3
"""Materializza evidenze A3.2 riusabili nei source profile della release pubblica.

Le annotazioni source-level non enumerano indicatori e non costituiscono un secondo
catalogo. Gli override metric-specific sono ammessi solo per eccezioni semantiche
reali (per esempio NOT_APPLICABLE) e vengono applicati nello stesso workspace
effimero che costruisce l'Effective Public Catalog.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "source-registry.json"

AVAILABLE = "AVAILABLE_MISSING"
UNAVAILABLE = "SOURCE_UNAVAILABLE"
NOT_APPLICABLE = "NOT_APPLICABLE"

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
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "Istat rende disponibili il Censimento Agricoltura 2020 e il Censimento 2010 con le stesse principali famiglie di variabili e supporta confronti evolutivi.",
            "sourceReference": "https://www.istat.it/statistiche-per-temi/censimenti/agricoltura/7-censimento-generale/risultati/",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "Istat descrive il Censimento Agricoltura 2020 come banca dati nazionale con dettaglio fino al livello comunale, quindi con scale territoriali più ampie coerenti.",
            "sourceReference": "https://www.istat.it/dati/banche-dati/",
        },
        "benchmark_toscana_italia": {
            "state": AVAILABLE,
            "evidence": "Le Story Map e la dashboard del Censimento Agricoltura consentono comparazioni territoriali interne alla regione e rispetto alla ripartizione e all'Italia, con dati regionali, provinciali e comunali.",
            "sourceReference": "https://www.istat.it/notizia/lagricoltura-nelle-regioni-italiane/",
        },
        "assoluto_normalizzato": {
            "state": AVAILABLE,
            "evidence": "La dashboard comunale del Censimento Agricoltura consente di scaricare nello stesso prodotto dati assoluti e indicatori sulle principali variabili.",
            "sourceReference": "https://www.istat.it/notizia/lagricoltura-nelle-regioni-italiane/",
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
    "regione-toscana-biblioteche-annual": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "Regione Toscana pubblica una serie storica dal 1998 dei valori assoluti per singola biblioteca e degli indicatori IFLA a livello comunale.",
            "sourceReference": "https://www.regione.toscana.it/-/il-valore-delle-biblioteche-pubbliche-di-ente-locale-e-della-cooperazione-bibliotecaria",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "Il monitoraggio regionale contiene dati per singola biblioteca e indicatori comunali, quindi una granularità più fine del Comune e scale territoriali ulteriori.",
            "sourceReference": "https://www.regione.toscana.it/-/il-valore-delle-biblioteche-pubbliche-di-ente-locale-e-della-cooperazione-bibliotecaria",
        },
        "benchmark_toscana_italia": {
            "state": AVAILABLE,
            "evidence": "Gli indicatori IFLA comunali sono pubblicati con confronto territoriale rispetto al livello regionale e alla rete di appartenenza.",
            "sourceReference": "https://www.regione.toscana.it/-/il-valore-delle-biblioteche-pubbliche-di-ente-locale-e-della-cooperazione-bibliotecaria",
        },
        "frequenza_infra_annuale": {
            "state": UNAVAILABLE,
            "evidence": "Regione Toscana descrive il monitoraggio delle biblioteche come annuale; non è diffusa per questo set una serie infra-annuale omogenea.",
            "sourceReference": "https://www.regione.toscana.it/-/il-valore-delle-biblioteche-pubbliche-di-ente-locale-e-della-cooperazione-bibliotecaria",
        },
    },
    "ispra-environment-annual": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "Il Catasto Rifiuti ISPRA pubblica dati comunali su produzione e raccolta differenziata dal 2010 e dati sui costi dal 2011, consentendo serie storiche omogenee.",
            "sourceReference": "https://www.catasto-rifiuti.isprambiente.it/index.php?pg=ru",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "Il Catasto Rifiuti diffonde dati fino al dettaglio comunale e provinciale e consente il download dei dati comunali di ciascuna regione.",
            "sourceReference": "https://www.catasto-rifiuti.isprambiente.it/index.php?pg=ru",
        },
        "assoluto_normalizzato": {
            "state": AVAILABLE,
            "evidence": "Il Catasto Rifiuti espone valori assoluti di produzione e raccolta differenziata insieme a percentuali e valori pro capite; per i costi pubblica misure pro capite e per chilogrammo.",
            "sourceReference": "https://www.catasto-rifiuti.isprambiente.it/index.php?pg=findComune",
        },
        "frequenza_infra_annuale": {
            "state": UNAVAILABLE,
            "evidence": "Le serie comunali del Catasto Rifiuti sono pubblicate per anno; non è diffusa una serie mensile, trimestrale o semestrale equivalente delle stesse misure.",
            "sourceReference": "https://www.catasto-rifiuti.isprambiente.it/index.php?pg=ru",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "Il Catasto Rifiuti pubblica dettaglio per frazioni della raccolta differenziata e componenti dei costi del servizio di igiene urbana.",
            "sourceReference": "https://www.catasto-rifiuti.isprambiente.it/",
        },
    },
    "regione-toscana-gtfs-scheduled": {
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "Il GTFS regionale contiene fermate e coordinate delle corse, quindi una granularità territoriale più fine del Comune su tutta la Toscana.",
            "sourceReference": "https://dati.toscana.it/dataset/rt-oraritb",
        },
        "frequenza_infra_annuale": {
            "state": AVAILABLE,
            "evidence": "Il GTFS espone calendari di servizio e orari di arrivo e partenza per ogni corsa e fermata, rendendo disponibile una granularità temporale infra-annuale.",
            "sourceReference": "https://dati.toscana.it/dataset/rt-oraritb",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "Il dataset distingue aziende, fermate, linee, corse e modalità di trasporto tra treni, traghetti, tram e autobus.",
            "sourceReference": "https://dati.toscana.it/dataset/rt-oraritb",
        },
    },
    "istat-fragility-2022": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "Istat presenta l'Indice di Fragilità Comunale in serie storica e documenta l'evoluzione nel periodo 2018-2022.",
            "sourceReference": "https://www.istat.it/comunicato-stampa/la-fragilita-dei-comuni-italiani-anno-2022/",
        },
        "frequenza_infra_annuale": {
            "state": UNAVAILABLE,
            "evidence": "L'IFC è diffuso con riferimento annuale e la serie documentata è 2018-2022; non è prevista una cadenza infra-annuale equivalente.",
            "sourceReference": "https://www.istat.it/comunicato-stampa/la-fragilita-dei-comuni-italiani-anno-2022/",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "Istat integra l'indice con indicatori elementari e consente letture per domini territoriali e componenti del profilo di fragilità.",
            "sourceReference": "https://www.istat.it/comunicato-stampa/aggiornato-indice-di-fragilita-comunale/",
        },
    },
    "agcom-quarterly": {
        "serie_storica": {
            "state": AVAILABLE,
            "evidence": "La Broadband Map AGCOM mette a disposizione il confronto con mappe storicizzate e i report evidenziano le variazioni rispetto alla rilevazione precedente.",
            "sourceReference": "https://maps.agcom.it/",
        },
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "La reportistica Broadband Map AGCOM diffonde indicatori di copertura a livello comunale, provinciale e regionale.",
            "sourceReference": "https://geo.agcom.it/reportistica/",
        },
        "benchmark_toscana_italia": {
            "state": AVAILABLE,
            "evidence": "La Broadband Map consente il download dei tabulati comunali, provinciali e regionali e offre statistiche nazionali e regionali sulle tecnologie di accesso.",
            "sourceReference": "https://maps.agcom.it/",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "La Broadband Map distingue tecnologie e prestazioni di accesso, incluse reti fisse cablate, FTTH, FTTC/VDSL, FWA e reti mobili.",
            "sourceReference": "https://geo.agcom.it/visura/estratto-completo.html",
        },
    },
    "lamma-copernicus-climate": {
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "LaMMA pubblica temperature minime/massime e precipitazioni giornaliere su griglia regolare a 1 km per l'intera Toscana, più fine del livello comunale.",
            "sourceReference": "https://dati.lamma.toscana.it/dataset?tags=spazializzazione",
        },
        "frequenza_infra_annuale": {
            "state": AVAILABLE,
            "evidence": "LaMMA pubblica dataset giornalieri di temperature minime, massime e precipitazioni, quindi una frequenza molto più fine dell'anno.",
            "sourceReference": "https://dati.lamma.toscana.it/group/6e8d2ab2-6afd-47e4-a8a7-04675f25e383?groups=meteo",
        },
    },
    "cb1-pmo-status-2026": {
        "dettaglio_territoriale": {
            "state": AVAILABLE,
            "evidence": "Il portale PMO del Consorzio Toscana Nord espone i lavori per Comune, corso d'acqua e tratto, con dettaglio territoriale inferiore al Comune.",
            "sourceReference": "https://cbtoscananord.it/comunicazione/pmo-manutenzione-mappa-navigabile/",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "Il portale PMO consente filtri e campi per stagione, corso d'acqua, intervento previsto, tratto e importo, oltre allo scarico CSV.",
            "sourceReference": "https://cbtoscananord.it/comunicazione/pmo-manutenzione-mappa-navigabile/",
        },
    },
}


EVIDENCE.update(
    {
        "mef-municipal-tax-annual": {
            "frequenza_infra_annuale": {
                "state": UNAVAILABLE,
                "evidence": "Il profilo è costruito su aliquote e tariffe deliberate per singolo anno. Il Dipartimento delle Finanze organizza gli archivi IMU e degli altri tributi comunali per anno; non esiste per questi scenari standardizzati una serie mensile, trimestrale o semestrale metodologicamente equivalente.",
                "sourceReference": "https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_at/sceltaanno.htm",
            },
        },
        "istat-tourism-annual": {
            "frequenza_infra_annuale": {
                "state": UNAVAILABLE,
                "evidence": "La rilevazione Istat sulla Capacità degli esercizi ricettivi è definita con periodicità annuale e misura la capacità lorda riferita all'anno. Non pubblica una misura infra-annuale equivalente dei posti letto della stessa rilevazione.",
                "sourceReference": "https://indata.istat.it/ctur/index.php",
            },
        },
        "erp-lucca-annual-balance-sheet": {
            "frequenza_infra_annuale": {
                "state": UNAVAILABLE,
                "evidence": "Il profilo deriva dal bilancio d'esercizio ERP Lucca chiuso al 31 dicembre e approvato annualmente. La morosità ricostruita da questi prospetti non dispone nella stessa fonte di una serie mensile, trimestrale o semestrale metodologicamente equivalente.",
                "sourceReference": "https://at.erplucca.it/default?path=75&t=1",
            },
        },
    }
)



EVIDENCE.setdefault("ars-toscana-mixed", {}).update(
    {
        "frequenza_infra_annuale": {
            "state": UNAVAILABLE,
            "evidence": "La banca dati ARS 'La salute dei comuni' espone per ciascun indicatore il valore aggiornato all'ultimo anno disponibile e il relativo trend storico; il profilo è annuale o pluriennale secondo l'indicatore e non offre osservazioni mensili, trimestrali o semestrali metodologicamente equivalenti.",
            "sourceReference": "https://www.ars.toscana.it/aree-dintervento/la-salute-di/salute-dei-toscani/profilo-di-salute-dei-toscani/news/3394-da-oggi-tutti-gli-indicatori-dell-ars-accessibili-da-un-unica-pagina.html",
        },
    }
)



EVIDENCE.setdefault("cb1-pmo-status-2026", {}).update(
    {
        "frequenza_infra_annuale": {
            "state": AVAILABLE,
            "evidence": "Il Sistema Informativo Territoriale del Consorzio consente di seguire i lavori in tempo reale con aggiornamenti costanti durante l'esecuzione del Piano 2026; la pipeline conserva oggi uno snapshot puntuale e non acquisisce questa frequenza operativa.",
            "sourceReference": "https://cbtoscananord.it/contributo-bonifica-normativa-lavori-legittimo/",
        },
        "serie_storica": {
            "state": UNAVAILABLE,
            "evidence": "Il WFS governato del progetto pmo_stato_lavori espone lo stato operativo corrente degli interventi e i relativi campi di inizio/fine, ma non una sequenza versionata di snapshot storici dello stesso stato.",
            "sourceReference": "https://geoportale.cbtoscananord.it/",
        },
        "assoluto_normalizzato": {
            "state": UNAVAILABLE,
            "evidence": "Il WFS PMO espone conteggi di interventi, importi lordi e metri di attività come valori assoluti; non pubblica per queste metriche un corrispondente indicatore normalizzato per popolazione, superficie o altra base comparabile.",
            "sourceReference": "https://cbtoscananord.it/comunicazione/pmo-manutenzione-mappa-navigabile/",
        },
    }
)


METRIC_EVIDENCE = {
    metric_id: {
        "sesso": {
            "state": NOT_APPLICABLE,
            "evidence": "La metrica conta percorsi o itinerari territoriali; una disaggregazione per sesso non ha significato semantico per l'oggetto misurato.",
        },
        "eta": {
            "state": NOT_APPLICABLE,
            "evidence": "La metrica conta percorsi o itinerari territoriali; una disaggregazione per età non ha significato semantico per l'oggetto misurato.",
        },
        "numeratore_denominatore": {
            "state": NOT_APPLICABLE,
            "evidence": "La metrica è un conteggio di percorsi o itinerari e non è definita come rapporto, tasso, quota o indice con numeratore e denominatore.",
        },
    }
    for metric_id in (
        "slowMobilityRoutes",
        "slowMobilityTrekking",
        "slowMobilityCammini",
        "slowMobilityBici",
        "slowMobilityMtb",
    )
}

METRIC_EVIDENCE.update(
    {
        "evPoints": {
            "numeratore_denominatore": {
                "state": AVAILABLE,
                "evidence": "La Piattaforma Unica Nazionale rende disponibile per Comune il numero dei punti di ricarica. La pipeline pubblica il tasso ogni 1.000 residenti ma non conserva il conteggio assoluto come componente strutturata della metrica.",
                "sourceReference": "https://www.piattaformaunicanazionale.it/territory-idr",
            },
        },
        "pharmaciesPer1000": {
            "assoluto_normalizzato": {
                "state": AVAILABLE,
                "evidence": "L'open data del Ministero della Salute contiene l'elenco completo delle farmacie aperte al pubblico con il Comune di localizzazione, quindi il conteggio assoluto comunale è direttamente ricostruibile. La metrica pubblicata conserva soltanto la densità ogni 1.000 residenti.",
                "sourceReference": "https://www.dati.salute.gov.it/it/dataset/farmacie/",
            },
            "numeratore_denominatore": {
                "state": AVAILABLE,
                "evidence": "L'open data del Ministero della Salute contiene ogni farmacia con il Comune di localizzazione, rendendo disponibile il numeratore assoluto; il denominatore demografico è governato separatamente. Il conteggio comunale non è però conservato nella metrica pubblicata.",
                "sourceReference": "https://www.dati.salute.gov.it/it/dataset/farmacie/",
            },
        },
        "tourismStructuresPer1000": {
            "assoluto_normalizzato": {
                "state": AVAILABLE,
                "evidence": "Regione Toscana pubblica per il 2025 la consistenza delle strutture ricettive per Comune e tipologia. La pipeline conserva la densità 2025 ogni 1.000 residenti, mentre il conteggio strutturato presente nel dettaglio canonico è riferito al 2024 e non è quindi un assoluto comparabile già acquisito per il target 2025.",
                "sourceReference": "https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025%C2%A0",
            },
            "numeratore_denominatore": {
                "state": AVAILABLE,
                "evidence": "La tabella ufficiale Toscana 2025 espone la consistenza delle strutture ricettive per Comune e tipologia, quindi il numeratore 2025 è disponibile alla fonte; il denominatore demografico è governato separatamente. La pipeline non conserva oggi il numeratore 2025 come componente strutturata della metrica.",
                "sourceReference": "https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025%C2%A0",
            },
        },
        "roadFinesPerResident": {
            "assoluto_normalizzato": {
                "state": AVAILABLE,
                "evidence": "Istat definisce l'indicatore come Totale proventi violazioni al codice della strada / Popolazione residente media e identifica come fonte il Rendiconto proventi violazione codice della strada del Ministero dell'Interno. La banca dati Finanza Locale violazioniCdS pubblica i rendiconti comunali trasmessi al Ministero, nei quali il Quadro 1 espone il totale proventi; il canonico conserva invece soltanto il valore per abitante e la serie.",
                "sourceReference": "https://finanzalocale.interno.gov.it/apps/floc.php/violazioniCdS/index",
            },
            "numeratore_denominatore": {
                "state": AVAILABLE,
                "evidence": "Il Portale Finanza Locale del Ministero pubblica i rendiconti comunali violazioniCdS con il totale proventi; Istat documenta che il rapporto usa quel totale come numeratore e la popolazione residente media come denominatore. Nel canonico roadFinesPerResident i due componenti non sono conservati come campi strutturati, pur essendo disponibili nelle fonti ufficiali governate.",
                "sourceReference": "https://finanzalocale.interno.gov.it/apps/floc.php/violazioniCdS/index",
            },
        },
    }
)


METRIC_EVIDENCE.update(
    {
        "agriculturalUsedArea": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura ettari di superficie agricola utilizzata localizzati nel territorio comunale. Il sesso non è una dimensione semantica della superficie misurata.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura ettari di superficie agricola utilizzata localizzati nel territorio comunale. L'età non è una dimensione semantica della superficie misurata.",
            },
        },
        "averageAgriculturalFarmSize": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura la dimensione fisica media delle aziende in ettari per azienda; una disaggregazione per sesso descriverebbe eventualmente il conduttore, non l'oggetto metrico superficie/azienda.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura la dimensione fisica media delle aziende in ettari per azienda; una disaggregazione per età descriverebbe eventualmente il conduttore, non l'oggetto metrico superficie/azienda.",
            },
        },
        "cropProfile": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica descrive ettari di territorio per tipologia di coltura. Il sesso non è una dimensione semantica della superficie o della coltura misurata.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica descrive ettari di territorio per tipologia di coltura. L'età non è una dimensione semantica della superficie o della coltura misurata.",
            },
        },
        "irrigatedAgriculturalArea": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura superficie irrigata in ettari e relativa quota sulla SAU. Il sesso non è una dimensione semantica della superficie irrigata.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura superficie irrigata in ettari e relativa quota sulla SAU. L'età non è una dimensione semantica della superficie irrigata.",
            },
        },
        "forestCoverIndex": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica descrive copertura forestale e superficie del territorio; una disaggregazione per sesso non è semanticamente applicabile all'oggetto fisico misurato.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica descrive copertura forestale e superficie del territorio; una disaggregazione per età non è semanticamente applicabile all'oggetto fisico misurato.",
            },
        },
        "landCoverProfile": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica descrive la composizione fisica dell'uso/copertura del suolo per categorie territoriali. Il sesso non è una dimensione semantica dell'oggetto misurato.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica descrive la composizione fisica dell'uso/copertura del suolo per categorie territoriali. L'età non è una dimensione semantica dell'oggetto misurato.",
            },
        },
        "extractiveSites": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica conta e classifica siti estrattivi censiti. Il sesso non è una dimensione semantica dei siti fisici misurati.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica conta e classifica siti estrattivi censiti. L'età non è una dimensione semantica dei siti fisici misurati.",
            },
        },
    }
)


for metric_id, dimensions in {
        "emsResponseTimeP75": {
            "numeratore_denominatore": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica pubblica un percentile temporale espresso in minuti. Non è un rapporto, tasso, quota o indice generato da una coppia numeratore/denominatore.",
            },
        },
        "extractiveSites": {
            "numeratore_denominatore": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica è un conteggio diretto di siti estrattivi censiti (COUNT DISTINCT) e non è definita come rapporto, tasso, quota o indice.",
            },
        },
        "hospitals": {
            "numeratore_denominatore": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica è il conteggio diretto dei presidi ospedalieri localizzati nel Comune e non è definita come rapporto, tasso, quota o indice.",
            },
        },
        "lifeExpectancy": {
            "numeratore_denominatore": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica pubblica la speranza di vita in anni come indicatore sintetico di tavola di mortalità; non è un rapporto, tasso o quota rappresentabile tramite una singola coppia numeratore/denominatore.",
            },
        },
        "municipalStaffTraining": {
            "numeratore_denominatore": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica pubblica valori RGS di giornate e medie di formazione, inclusa la Media Totale, senza definire il valore esposto come rapporto, tasso, quota o indice con componenti numeratore/denominatore.",
            },
        },
        "population": {
            "numeratore_denominatore": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica è il numero diretto di residenti al 1° gennaio e non è definita come rapporto, tasso, quota o indice.",
            },
        },
        "tourismBeds": {
            "numeratore_denominatore": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica è il conteggio diretto dei posti letto disponibili nelle strutture ricettive e non è definita come rapporto, tasso, quota o indice.",
            },
        },
}.items():
    METRIC_EVIDENCE.setdefault(metric_id, {}).update(dimensions)



for metric_id, dimensions in {
        "economyActivityAtlas": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica descrive attività economiche e codici ATECO localizzati nel Comune. Il sesso non è una dimensione semantica dell'attività economica misurata; riguarderebbe eventualmente persone collegate all'impresa, cioè un oggetto diverso.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica descrive attività economiche e codici ATECO localizzati nel Comune. L'età non è una dimensione semantica dell'attività economica misurata; riguarderebbe eventualmente persone collegate all'impresa, cioè un oggetto diverso.",
            },
        },
        "erpArrears": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura la morosità ERP come grandezza economica riferita al patrimonio/gestione. Il sesso descriverebbe eventualmente gli assegnatari o debitori, non la grandezza economica pubblicata.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura la morosità ERP come grandezza economica riferita al patrimonio/gestione. L'età descriverebbe eventualmente gli assegnatari o debitori, non la grandezza economica pubblicata.",
            },
        },
        "roadFinesPerResident": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura i proventi da sanzioni al Codice della strada rapportati alla popolazione residente media. Il sesso non è una dimensione della grandezza economica pubblicata; descriverebbe eventualmente trasgressori o residenti, cioè un oggetto diverso.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura i proventi da sanzioni al Codice della strada rapportati alla popolazione residente media. L'età non è una dimensione della grandezza economica pubblicata; descriverebbe eventualmente trasgressori o residenti, cioè un oggetto diverso.",
            },
        },
}.items():
    METRIC_EVIDENCE.setdefault(metric_id, {}).update(dimensions)



for metric_id, dimensions in {
        "climateTemperatureTrend50y": {
            "assoluto_normalizzato": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica è una variazione di temperatura espressa in °C derivata dalla tendenza territoriale. Una versione per abitante, per superficie o percentuale non sarebbe una normalizzazione coerente della stessa misura fisica.",
            },
        },
        "climateTmaxTrend": {
            "assoluto_normalizzato": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura temperature massime e relativa tendenza in °C. La temperatura è già una grandezza intensiva: normalizzarla per popolazione, superficie o in percentuale produrrebbe un indicatore diverso e non metodologicamente equivalente.",
            },
        },
        "climateTminTrend": {
            "assoluto_normalizzato": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura temperature minime e relativa tendenza in °C. La temperatura è già una grandezza intensiva: normalizzarla per popolazione, superficie o in percentuale produrrebbe un indicatore diverso e non metodologicamente equivalente.",
            },
        },
        "emsResponseTimeP75": {
            "assoluto_normalizzato": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica è il 75° percentile di un intervallo temporale espresso in minuti. Non esiste un corrispondente valore assoluto da normalizzare per abitante, superficie, famiglia o percentuale senza cambiare l'oggetto statistico misurato.",
            },
        },
        "lifeExpectancy": {
            "assoluto_normalizzato": {
                "state": NOT_APPLICABLE,
                "evidence": "La speranza di vita è un indicatore sintetico di tavola di mortalità espresso in anni. Una normalizzazione per popolazione, superficie, famiglia o percentuale non rappresenterebbe la stessa misura.",
            },
        },
        "municipalImuStandard": {
            "assoluto_normalizzato": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica è già un importo teorico standardizzato su una base imponibile fissa di 100.000 €. L'aliquota percentuale è un parametro della formula, non una versione normalizzata dello stesso importo; ulteriori normalizzazioni definirebbero un indicatore diverso.",
            },
        },
        "tariStandardHousehold": {
            "assoluto_normalizzato": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica è già una spesa annua standardizzata su una stessa utenza teorica di 3 componenti e 100 m². Le componenti tariffarie per m² sono input della formula, non una versione normalizzata del costo totale; normalizzare ulteriormente cambierebbe l'indicatore.",
            },
        },
}.items():
    METRIC_EVIDENCE.setdefault(metric_id, {}).update(dimensions)



for metric_id, dimensions in {
        "population": {
            "frequenza_infra_annuale": {
                "state": AVAILABLE,
                "evidence": "Istat Demo diffonde il Bilancio demografico mensile con popolazione residente a dettaglio comunale. La metrica pubblicata usa oggi lo stock al 1° gennaio e non acquisisce la serie mensile.",
                "sourceReference": "https://demo.istat.it/app/?i=D7B",
            },
        },
        "populationChange": {
            "frequenza_infra_annuale": {
                "state": AVAILABLE,
                "evidence": "Istat Demo rende disponibile la popolazione residente mese per mese a livello comunale; da due stock mensili è ricostruibile una variazione coerente. La pipeline conserva oggi solo la variazione tra annualità.",
                "sourceReference": "https://demo.istat.it/app/?i=D7B",
            },
        },
        "naturalDemographicDynamics": {
            "frequenza_infra_annuale": {
                "state": AVAILABLE,
                "evidence": "Il Bilancio demografico mensile Istat pubblica per Comune nascite e decessi del mese di riferimento, quindi le componenti della dinamica naturale sono disponibili a frequenza infra-annuale ma non sono acquisite nella metrica pubblicata.",
                "sourceReference": "https://demo.istat.it/app/?i=D7B",
            },
        },
        "internalResidentialMobility": {
            "frequenza_infra_annuale": {
                "state": AVAILABLE,
                "evidence": "Il Bilancio demografico mensile Istat pubblica a livello comunale i trasferimenti di residenza interni avvenuti nel mese di riferimento. La pipeline espone oggi solo l'aggregato annuale.",
                "sourceReference": "https://demo.istat.it/app/?i=D7B",
            },
        },
        "foreignResidentialMobility": {
            "frequenza_infra_annuale": {
                "state": AVAILABLE,
                "evidence": "Il Bilancio demografico mensile Istat pubblica a livello comunale il movimento migratorio con l'estero del mese di riferimento. La pipeline espone oggi solo l'aggregato annuale.",
                "sourceReference": "https://demo.istat.it/app/?i=D7B",
            },
        },
        "totalResidentialMobility": {
            "frequenza_infra_annuale": {
                "state": AVAILABLE,
                "evidence": "Il Bilancio demografico mensile Istat pubblica a livello comunale trasferimenti interni e movimento migratorio con l'estero, le stesse componenti che generano la mobilità residenziale complessiva. La pipeline conserva oggi solo l'aggregato annuale.",
                "sourceReference": "https://demo.istat.it/app/?i=D7B",
            },
        },
        "ageDistribution": {
            "frequenza_infra_annuale": {
                "state": UNAVAILABLE,
                "evidence": "La distribuzione per età deriva da POSAS, che Istat Demo pubblica come popolazione residente per sesso, età e stato civile al 1° gennaio di ciascun anno. Il Bilancio demografico mensile non espone l'età, quindi non esiste nella stessa fonte una serie infra-annuale equivalente della struttura per età.",
                "sourceReference": "https://demo.istat.it/app/?i=POS",
            },
        },
        "dependencyIndices": {
            "frequenza_infra_annuale": {
                "state": UNAVAILABLE,
                "evidence": "Gli indici di dipendenza sono calcolati sulle classi di età POSAS al 1° gennaio. Istat Demo non diffonde la struttura per età con cadenza mensile, quindi le componenti necessarie non sono disponibili a frequenza infra-annuale comparabile.",
                "sourceReference": "https://demo.istat.it/app/?i=POS",
            },
        },
        "foreignResidents": {
            "frequenza_infra_annuale": {
                "state": UNAVAILABLE,
                "evidence": "Istat Demo pubblica la popolazione straniera residente per sesso ed età al 1° gennaio e il relativo bilancio demografico su base annuale. Il bilancio mensile comunale riguarda la popolazione complessiva e non offre uno stock mensile equivalente per cittadinanza.",
                "sourceReference": "https://demo.istat.it/app/?i=STR&l=it",
            },
        },
        "roadSafety": {
            "frequenza_infra_annuale": {
                "state": AVAILABLE,
                "evidence": "La rilevazione Istat degli incidenti stradali con lesioni è svolta a cadenza mensile e i microdati contengono mese e giorno dell'evento. La metrica pubblicata aggrega invece gli incidenti su base annuale.",
                "sourceReference": "https://www.istat.it/microdati/rilevazione-degli-incidenti-stradali-con-lesioni-a-persone-3/",
            },
        },
        "roadFinesPerResident": {
            "frequenza_infra_annuale": {
                "state": UNAVAILABLE,
                "evidence": "La metrica usa i proventi rendicontati da sanzioni al Codice della strada pubblicati nella serie annuale Istat/Ministero dell'Interno. La fonte governata non espone per lo stesso indicatore una serie mensile, trimestrale o semestrale metodologicamente equivalente.",
                "sourceReference": "https://www.istat.it/storage/misura-comune/15c-Infrastrutture-e-mobilita-per-tassi-di-motorizzazione-e-proventi-dalle-sanzioni.xlsx",
            },
        },
        "incomeVsInflation": {
            "frequenza_infra_annuale": {
                "state": UNAVAILABLE,
                "evidence": "Il reddito imponibile comunale MEF è diffuso per anno di dichiarazione/anno d'imposta. Anche se il NIC Istat esiste a frequenza mensile, la componente reddituale vincola l'indicatore combinato a una frequenza annuale; non esiste quindi una misura infra-annuale comparabile dello stesso indicatore.",
                "sourceReference": "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes&search_class%5B0%5D=cCOMUNE",
            },
        },
}.items():
    METRIC_EVIDENCE.setdefault(metric_id, {}).update(dimensions)



for metric_id, dimensions in {
        "disability064Per1000": {
            "sesso": {"state": UNAVAILABLE, "evidence": "La batteria regionale pubblica il solo indicatore comunale complessivo per la popolazione 0-64, senza disaggregazione per sesso.", "sourceReference": "https://www.regione.toscana.it/statistiche/indicatori-comunali-per-le-politiche-locali"},
            "eta": {"state": UNAVAILABLE, "evidence": "La batteria regionale pubblica il valore complessivo 0-64 e non una scomposizione per classi di età interne alla fascia.", "sourceReference": "https://www.regione.toscana.it/statistiche/indicatori-comunali-per-le-politiche-locali"},
            "assoluto_normalizzato": {"state": UNAVAILABLE, "evidence": "Il metadato ufficiale definisce l'indicatore come persone 0-64 con disabilità per 1.000 residenti 0-64; i CSV della batteria diffondono il valore dell'indicatore, non anche il corrispondente conteggio assoluto.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "numeratore_denominatore": {"state": UNAVAILABLE, "evidence": "Il metadato descrive il rapporto per 1.000 ma la batteria CSV non espone separatamente persone con disabilità e popolazione 0-64 come componenti dell'indicatore.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "categorie_specifiche": {"state": UNAVAILABLE, "evidence": "La batteria regionale diffonde un unico valore comunale dell'indicatore e non pubblica categorie di gravità o tipologia di disabilità per questa metrica.", "sourceReference": "https://www.regione.toscana.it/statistiche/indicatori-comunali-per-le-politiche-locali"},
        },
        "emsResponseTimeP75": {
            "sesso": {"state": UNAVAILABLE, "evidence": "La batteria regionale pubblica il 75° percentile comunale del tempo di risposta 118 senza disaggregazione per sesso.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "eta": {"state": UNAVAILABLE, "evidence": "La batteria regionale pubblica il 75° percentile comunale del tempo di risposta 118 senza disaggregazione per età.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "categorie_specifiche": {"state": UNAVAILABLE, "evidence": "Il metadato ufficiale espone un unico indicatore P3 sul tempo tra allarme e arrivo del primo mezzo; la batteria non fornisce categorie di intervento o priorità per questa metrica.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
        },
        "foreignBornSoleProprietorShare": {
            "sesso": {"state": UNAVAILABLE, "evidence": "La batteria regionale diffonde la sola percentuale comunale di ditte individuali con conduttore nato all'estero, senza scomposizione per sesso.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "eta": {"state": UNAVAILABLE, "evidence": "La batteria regionale diffonde la sola percentuale comunale di ditte individuali con conduttore nato all'estero, senza classi di età del titolare.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "assoluto_normalizzato": {"state": UNAVAILABLE, "evidence": "Il metadato definisce una percentuale; i file ufficiali della batteria pubblicano l'indicatore percentuale senza il corrispondente conteggio assoluto delle ditte con titolare nato all'estero.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "numeratore_denominatore": {"state": UNAVAILABLE, "evidence": "La batteria pubblica la percentuale finale e non espone separatamente, per la stessa metrica, numeratore e totale delle ditte individuali attive.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "categorie_specifiche": {"state": UNAVAILABLE, "evidence": "La batteria regionale non articola l'indicatore per paese di nascita, settore ATECO o altra categoria del titolare.", "sourceReference": "https://www.regione.toscana.it/statistiche/indicatori-comunali-per-le-politiche-locali"},
        },
        "innovationBusinessShare": {
            "sesso": {"state": UNAVAILABLE, "evidence": "La batteria regionale pubblica la quota di imprese nei settori dell'innovazione senza disaggregazione per sesso.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "eta": {"state": UNAVAILABLE, "evidence": "La batteria regionale pubblica la quota di imprese nei settori dell'innovazione senza disaggregazione per età.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "assoluto_normalizzato": {"state": UNAVAILABLE, "evidence": "Il dato ufficiale è una percentuale di imprese attive; la batteria non pubblica, insieme alla quota, il conteggio assoluto delle imprese incluse.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "numeratore_denominatore": {"state": UNAVAILABLE, "evidence": "Il metadato elenca le divisioni ATECO considerate innovative ma i CSV della batteria non espongono separatamente imprese innovative e totale imprese come componenti della quota.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "categorie_specifiche": {"state": UNAVAILABLE, "evidence": "Le divisioni ATECO che definiscono l'insieme innovazione sono documentate nel metadato, ma la batteria diffonde solo la quota aggregata e non valori distinti per singola divisione.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
        },
        "municipalOnlineServicesAdvanced": {
            "sesso": {"state": UNAVAILABLE, "evidence": "L'indicatore riguarda servizi comunali online e la batteria non pubblica una disaggregazione degli utenti per sesso.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "eta": {"state": UNAVAILABLE, "evidence": "L'indicatore riguarda servizi comunali online e la batteria non pubblica una disaggregazione degli utenti per età.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "assoluto_normalizzato": {"state": UNAVAILABLE, "evidence": "La batteria diffonde la percentuale di servizi ai livelli massimi di disponibilità, non anche il numero assoluto dei servizi corrispondenti.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "numeratore_denominatore": {"state": UNAVAILABLE, "evidence": "Il metadato Istat/Regione descrive la percentuale ma i file della batteria non espongono separatamente numero di servizi avanzati e paniere totale usato nel calcolo.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "categorie_specifiche": {"state": UNAVAILABLE, "evidence": "Il metadato descrive i livelli 3 e 4 ma la batteria pubblica il valore aggregato dell'indicatore senza valori separati per livello o tipologia di servizio.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
        },
        "organicAgriculturalAreaShare": {
            "sesso": {"state": UNAVAILABLE, "evidence": "La batteria regionale pubblica la quota comunale di SAU biologica senza disaggregazione per sesso dei conduttori.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "eta": {"state": UNAVAILABLE, "evidence": "La batteria regionale pubblica la quota comunale di SAU biologica senza classi di età dei conduttori.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "assoluto_normalizzato": {"state": UNAVAILABLE, "evidence": "La batteria diffonde la percentuale di SAU biologica e non il corrispondente valore assoluto della superficie biologica per la stessa metrica.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "numeratore_denominatore": {"state": UNAVAILABLE, "evidence": "Il metadato definisce una quota di SAU biologica ma la batteria non espone separatamente SAU biologica e SAU totale come componenti strutturate.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "categorie_specifiche": {"state": UNAVAILABLE, "evidence": "La batteria non articola la quota di SAU biologica per coltura, classe aziendale o altra categoria agricola.", "sourceReference": "https://www.regione.toscana.it/statistiche/indicatori-comunali-per-le-politiche-locali"},
        },
        "youthOtherStatus": {
            "sesso": {"state": UNAVAILABLE, "evidence": "La batteria regionale diffonde la quota complessiva dei 15-24enni in altra condizione professionale senza disaggregazione per sesso.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "eta": {"state": UNAVAILABLE, "evidence": "La fascia 15-24 è il perimetro dell'indicatore; la batteria non la scompone in ulteriori classi o età puntuali.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "assoluto_normalizzato": {"state": UNAVAILABLE, "evidence": "La batteria pubblica la quota percentuale dei giovani in altra condizione professionale, non anche il conteggio assoluto corrispondente.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "numeratore_denominatore": {"state": UNAVAILABLE, "evidence": "Il metadato definisce la quota sui giovani 15-24, ma i CSV della batteria non espongono separatamente numeratore e popolazione 15-24 usati nel calcolo.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
            "categorie_specifiche": {"state": UNAVAILABLE, "evidence": "La batteria espone un'unica modalità aggregata 'altra condizione professionale' e non pubblica la composizione interna per specifica condizione.", "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"},
        },
        "tourismBeds": {
            "serie_storica": {"state": AVAILABLE, "evidence": "La rilevazione Istat sulla capacità ricettiva è annuale ed è disponibile su più annualità comparabili; la pipeline pubblica oggi il solo anno corrente per tourismBeds.", "sourceReference": "https://indata.istat.it/ctur/index.php"},
            "sesso": {"state": UNAVAILABLE, "evidence": "La rilevazione misura strutture, letti, camere e bagni; non osserva persone per sesso per la capacità ricettiva.", "sourceReference": "https://indata.istat.it/ctur/index.php"},
            "eta": {"state": UNAVAILABLE, "evidence": "La rilevazione misura strutture, letti, camere e bagni; non osserva persone per età per la capacità ricettiva.", "sourceReference": "https://indata.istat.it/ctur/index.php"},
            "dettaglio_territoriale": {"state": AVAILABLE, "evidence": "Istat diffonde la capacità ricettiva a livello comunale e anche a livelli territoriali più ampi, inclusi provincia, regione e Italia.", "sourceReference": "https://www.istat.it/tavole-di-dati/capacita-degli-esercizi-ricettivi-anno-2010/"},
            "benchmark_toscana_italia": {"state": AVAILABLE, "evidence": "La stessa rilevazione Istat diffonde dati comparabili a livello regionale e nazionale oltre al Comune, quindi sono disponibili benchmark Toscana/Italia coerenti.", "sourceReference": "https://www.istat.it/tavole-di-dati/capacita-degli-esercizi-ricettivi-anno-2010/"},
            "categorie_specifiche": {"state": AVAILABLE, "evidence": "La rilevazione distingue tipologie di struttura ricettiva e, per gli alberghi, anche classe dimensionale; tali categorie non sono acquisite nella metrica tourismBeds.", "sourceReference": "https://indata.istat.it/ctur/index.php"},
        },
}.items():
    METRIC_EVIDENCE.setdefault(metric_id, {}).update(dimensions)



for metric_id, dimensions in {
        "libraryActiveBorrowersPer100": {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "Il tracciato ufficiale del monitoraggio biblioteche espone gli iscritti attivi totali e per classi d'età, ma non contiene campi di disaggregazione per sesso.",
                "sourceReference": "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf",
            },
            "eta": {
                "state": AVAILABLE,
                "evidence": "Il Dataset Biblioteche espone IscrittiAttivi014, IscrittiAttivi1524, IscrittiAttivi2564 e IscrittiAttivi65+, quindi la distribuzione per età degli utenti attivi è disponibile alla fonte ma non acquisita nella metrica pubblicata.",
                "sourceReference": "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf",
            },
            "categorie_specifiche": {
                "state": UNAVAILABLE,
                "evidence": "Per gli iscritti attivi il tracciato ufficiale espone il totale e le classi d'età, già ricondotte alla dimensione eta; non pubblica ulteriori categorie native comparabili per lo stesso indicatore comunale.",
                "sourceReference": "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf",
            },
        },
        "libraryLoansPerResident": {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "Il tracciato dei prestiti non contiene campi per sesso degli utenti.",
                "sourceReference": "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf",
            },
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "Il dataset distingue i prestiti della sezione ragazzi ma non pubblica i prestiti per classi di età degli utenti; la categoria editoriale 'ragazzi' non equivale a una disaggregazione anagrafica.",
                "sourceReference": "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf",
            },
            "categorie_specifiche": {
                "state": AVAILABLE,
                "evidence": "Il Dataset Biblioteche distingue PrestitiRagazzi, PrestitiMultimediali e varie componenti del prestito interbibliotecario oltre ai PrestitiTotali; queste categorie native non sono acquisite dalla metrica pubblicata.",
                "sourceReference": "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf",
            },
        },
        "libraryWeeklyOpeningHours": {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "L'orario di apertura è rilevato come caratteristica della biblioteca e il dataset non contiene una disaggregazione per sesso.",
                "sourceReference": "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf",
            },
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "L'orario di apertura è rilevato come caratteristica della biblioteca e il dataset non contiene una disaggregazione per età.",
                "sourceReference": "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf",
            },
            "categorie_specifiche": {
                "state": AVAILABLE,
                "evidence": "Il tracciato ufficiale distingue IndiceAperturaMattino, Pomeriggio, Sera, Sabato e Festivo oltre alle OreSettimanali; le fasce/giorni di apertura costituiscono categorie native disponibili ma non acquisite nella metrica pubblicata.",
                "sourceReference": "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf",
            },
        },
}.items():
    METRIC_EVIDENCE.setdefault(metric_id, {}).update(dimensions)



for metric_id in (
        "averageGrossRemunerationPerEmployee",
        "labourCost",
        "labourProductivity",
        "turnoverPerPersonEmployed",
):
    METRIC_EVIDENCE.setdefault(metric_id, {}).update(
        {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "Le tavole Frame SBS Territoriale diffuse a livello comunale descrivono unità locali, occupazione, attività economica, localizzazione e variabili del conto economico; non pubblicano l'indicatore economico comunale disaggregato per sesso degli addetti.",
                "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
            },
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "Le tavole Frame SBS Territoriale diffuse a livello comunale descrivono unità locali, occupazione, attività economica, localizzazione e variabili del conto economico; non pubblicano l'indicatore economico comunale disaggregato per età degli addetti.",
                "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
            },
        }
    )



for metric_id, annotation in {
        "economyActivityAtlas": {
            "state": UNAVAILABLE,
            "evidence": "La diffusione regionale InfoCamere usata per l'atlante economico è organizzata per annualità e pubblica imprese registrate, attive, cessate e nuove iscritte nell'anno; non rende disponibile una serie mensile o trimestrale comunale metodologicamente equivalente per questo indicatore.",
            "sourceReference": "https://www.regione.toscana.it/-/imprese-movimento-anagrafico-e-unit%C3%A0-locali-in-toscana-dati-infocamere-2024",
        },
        "landCoverProfile": {
            "state": UNAVAILABLE,
            "evidence": "La fonte UCS Toscana espone edizioni discrete della copertura del suolo (2007, 2010, 2013, 2016, 2019), non osservazioni mensili, trimestrali o semestrali della stessa classificazione territoriale.",
            "sourceReference": "https://www502.regione.toscana.it/geoscopio/servizi/wms/USO_E_COPERTURA_DEL_SUOLO.htm",
        },
        "tourismIntensity": {
            "state": AVAILABLE,
            "evidence": "La Banca dati Turismo della Regione Toscana deriva dalla rilevazione Istat sul movimento dei clienti, svolta mensilmente, e rende disponibili serie mensili di arrivi e presenze; la metrica pubblicata non acquisisce questa frequenza infra-annuale.",
            "sourceReference": "https://www.regione.toscana.it/statistiche/banca-dati-turismo",
        },
}.items():
    METRIC_EVIDENCE.setdefault(metric_id, {}).update(
        {"frequenza_infra_annuale": annotation}
    )


for metric_id, indicator_id in {
        "diagnosticImagingServices": 1325,
        "elderlyHomeCare": 260,
        "emergencyAccess": 1657,
        "lifeExpectancy": 1290,
        "mortalityAll": 1438,
        "mortalityCancer": 1499,
        "mortalityCirculatory": 1327,
        "mortalityRespiratory": 1606,
        "permanentRsaAssisted": 261,
        "specialistVisits7Psr": 1425
}.items():
    METRIC_EVIDENCE.setdefault(metric_id, {}).update(
        {
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "L'export ufficiale ARS dell'indicatore contiene il valore complessivo e, dove previsto, la dimensione sesso, ma non espone strati per classe di età; l'età è usata per la standardizzazione e non come disaggregazione pubblicata della metrica.",
                "sourceReference": f"https://www.ars.toscana.it/banche-dati/dettaglio_indicatore-{indicator_id}",
            },
        }
    )


METRIC_EVIDENCE.setdefault("chronicTotal", {}).update(
    {
        "assoluto_normalizzato": {
            "state": AVAILABLE,
            "evidence": "ARS documenta per la prevalenza dei malati cronici sia il numero di persone sia la prevalenza/tasso standardizzato; il catalogo pubblico conserva oggi soltanto il tasso standardizzato.",
            "sourceReference": "https://www.ars.toscana.it/images/a_ns_pubblicazioni/relazioni/welfare_salute_2025/VOL_3_WES_2025.pdf",
        },
        "numeratore_denominatore": {
            "state": AVAILABLE,
            "evidence": "La scheda metodologica ARS della prevalenza dei malati cronici dichiara esplicitamente numeratore (residenti prevalenti per almeno una patologia MaCro) e denominatore (popolazione residente al 1° gennaio), componenti non acquisite nella metrica pubblicata.",
            "sourceReference": "https://www.ars.toscana.it/images/a_ns_pubblicazioni/relazioni/welfare_salute_2025/VOL_3_WES_2025.pdf",
        },
    }
)

METRIC_EVIDENCE.setdefault("hospitalizedAll", {}).update(
    {
        "sesso": {
            "state": AVAILABLE,
            "evidence": "Il portale ARS La salute dei comuni espone i soggetti ricoverati per tutte le cause con selezione Totale/Maschi/Femmine; la metrica pubblicata non acquisisce il dettaglio per sesso.",
            "sourceReference": "https://www.ars.toscana.it/banche-dati/dettaglio_indicatore-1332-soggetti-ricoverati-tutte-le-cause",
        },
        "assoluto_normalizzato": {
            "state": AVAILABLE,
            "evidence": "La famiglia di indicatori ARS sui soggetti ricoverati pubblica il numero di ricoverati insieme a tasso grezzo e tasso standardizzato per età; la metrica pubblicata conserva oggi il solo tasso standardizzato.",
            "sourceReference": "https://www.ars.toscana.it/banche-dati/dettaglio_indicatore-1332-soggetti-ricoverati-tutte-le-cause",
        },
        "numeratore_denominatore": {
            "state": AVAILABLE,
            "evidence": "La metodologia ARS dei soggetti ricoverati usa come numeratore i residenti ricoverati almeno una volta e come denominatore la popolazione residente del periodo; tali componenti non sono acquisite nella metrica pubblicata.",
            "sourceReference": "https://www.ars.toscana.it/banche-dati/dettaglio_indicatore-1332-soggetti-ricoverati-tutte-le-cause",
        },
    }
)



METRIC_EVIDENCE.setdefault("incomeVsInflation", {}).update(
    {
        "sesso": {
            "state": UNAVAILABLE,
            "evidence": "Il dataset MEF su base comunale utilizzato per la componente reddituale non incrocia il Comune con il sesso dei contribuenti; le statistiche per sesso sono diffuse in classificazioni separate e non sono metodologicamente combinabili con il valore comunale della metrica.",
            "sourceReference": "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes",
        },
        "eta": {
            "state": UNAVAILABLE,
            "evidence": "Il dataset MEF su base comunale utilizzato per la componente reddituale non incrocia il Comune con le classi di età dei contribuenti; le statistiche per età sono diffuse in classificazioni separate e non sono metodologicamente combinabili con il valore comunale della metrica.",
            "sourceReference": "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes",
        },
        "benchmark_toscana_italia": {
            "state": AVAILABLE,
            "evidence": "MEF diffonde le principali variabili IRPEF anche per aggregazioni territoriali superiori al Comune e ISTAT diffonde il NIC nazionale; è quindi disponibile un confronto territoriale coerente della componente reddituale, non acquisito nella metrica pubblicata.",
            "sourceReference": "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes",
        },
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "Il dataset comunale MEF conserva classi di reddito e principali fonti di reddito con frequenze e ammontari; queste categorie native non sono esposte dalla metrica Redditi vs inflazione.",
            "sourceReference": "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes",
        },
    }
)

METRIC_EVIDENCE.setdefault("roadSafety", {}).update(
    {
        "assoluto_normalizzato": {
            "state": AVAILABLE,
            "evidence": "La tavola Istat sugli incidenti stradali contiene i conteggi di incidenti, morti e feriti insieme agli indicatori normalizzati/rapportati pubblicati; la metrica espone oggi i tassi ma non acquisisce in forma strutturata tutti i corrispondenti valori assoluti.",
            "sourceReference": "https://www.istat.it/storage/misura-comune/15a-Infrastrutture-e-mobilita-incidenti-stradali.xlsx",
        },
        "numeratore_denominatore": {
            "state": AVAILABLE,
            "evidence": "La tavola Istat rende disponibili le componenti che generano incidentalità, mortalità e lesività (incidenti, morti, feriti e popolazione di riferimento); la metrica pubblicata non acquisisce tutte le coppie numeratore/denominatore come componenti strutturate.",
            "sourceReference": "https://www.istat.it/storage/misura-comune/15a-Infrastrutture-e-mobilita-incidenti-stradali.xlsx",
        },
    }
)

METRIC_EVIDENCE.setdefault("roadFinesPerResident", {}).update(
    {
        "categorie_specifiche": {
            "state": AVAILABLE,
            "evidence": "La fonte Istat/Ministero dell'Interno sui proventi da sanzioni distingue componenti dei proventi, inclusa la quota riferita ai limiti di velocità. La metrica pubblicata usa solo il totale; il campo specifico resta disponibile alla fonte pur con il caveat metodologico già documentato dall'Osservatorio.",
            "sourceReference": "https://www.istat.it/storage/misura-comune/15c-Infrastrutture-e-mobilita-per-tassi-di-motorizzazione-e-proventi-dalle-sanzioni.xlsx",
        },
    }
)



for metric_id in ("socialSpendingByUserArea", "socialSpendingPerResident"):
    METRIC_EVIDENCE.setdefault(metric_id, {}).update(
        {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "La rilevazione Istat sugli interventi e servizi sociali diffonde spesa e utenti per area di utenza e tipologia di servizio, ma non una disaggregazione comunale della spesa per sesso delle persone beneficiarie.",
                "sourceReference": "https://www.istat.it/tavole-di-dati/interventi-e-servizi-sociali-dei-comuni/",
            },
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "La rilevazione Istat articola la spesa per aree di utenza (famiglie e minori, disabili, anziani, ecc.) ma non pubblica, per la stessa metrica comunale, classi d'età quantitative dei beneficiari.",
                "sourceReference": "https://www.istat.it/tavole-di-dati/interventi-e-servizi-sociali-dei-comuni/",
            },
        }
    )



METRIC_EVIDENCE.setdefault("municipalStaffTraining", {}).update(
    {
        "eta": {
            "state": UNAVAILABLE,
            "evidence": "L'API RGS Formazione pubblica giornate e medie per totale, uomini e donne; le fasce di età sono disponibili in un diverso dataset sullo stock di personale e non sono incrociate con la formazione per ente.",
            "sourceReference": "https://contoannuale.rgs.mef.gov.it/web/sicosito/assenze-e-turnover/formazione-acc",
        },
    }
)

for dimension in ("sesso", "eta"):
    METRIC_EVIDENCE.setdefault("taxpayersAdultPopulationRate", {}).update(
        {
            dimension: {
                "state": UNAVAILABLE,
                "evidence": "Le statistiche MEF IRPEF su base comunale pubblicano numero di contribuenti e variabili reddituali per Comune; le classificazioni anagrafiche sono diffuse in dataset separati e non sono incrociate con il Comune, quindi non consentono lo stesso tasso comunale disaggregato.",
                "sourceReference": "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes&search_class%5B0%5D=cCOMUNE",
            },
        }
    )


def _merge_dimensions(target: dict, dimensions: dict, owner: str) -> int:
    applied = 0
    for dimension, annotation in dimensions.items():
        existing = target.get(dimension)
        if existing is not None and existing != annotation:
            raise RuntimeError(f"A3.2: evidenza già presente ma diversa: {owner}/{dimension}")
        target[dimension] = annotation
        applied += 1
    return applied


def main() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    profiles = registry.get("sourceProfiles")
    if not isinstance(profiles, dict):
        raise RuntimeError("A3.2: sourceProfiles assente dal registry")

    applied_profiles = 0
    for profile_id, dimensions in EVIDENCE.items():
        profile = profiles.get(profile_id)
        if not isinstance(profile, dict):
            raise RuntimeError(f"A3.2: source profile mancante: {profile_id}")
        target = profile.setdefault("enrichmentDimensions", {})
        if not isinstance(target, dict):
            raise RuntimeError(f"A3.2: enrichmentDimensions non-oggetto: {profile_id}")
        applied_profiles += _merge_dimensions(target, dimensions, profile_id)

    overrides = registry.setdefault("metricOverrides", {})
    if not isinstance(overrides, dict):
        raise RuntimeError("A3.2: metricOverrides non-oggetto nel registry")

    applied_metrics = 0
    for metric_id, dimensions in METRIC_EVIDENCE.items():
        override = overrides.setdefault(metric_id, {})
        if not isinstance(override, dict):
            raise RuntimeError(f"A3.2: metric override non-oggetto: {metric_id}")
        target = override.setdefault("enrichmentDimensions", {})
        if not isinstance(target, dict):
            raise RuntimeError(f"A3.2: enrichmentDimensions override non-oggetto: {metric_id}")
        applied_metrics += _merge_dimensions(target, dimensions, metric_id)

    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "A3.2 evidence materializzata: "
        f"{applied_profiles} dimensioni su {len(EVIDENCE)} profili; "
        f"{applied_metrics} override su {len(METRIC_EVIDENCE)} metriche"
    )


if __name__ == "__main__":
    main()
