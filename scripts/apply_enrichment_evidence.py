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
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "L'indicatore regionale pubblica un unico valore comunale delle persone 0-64 anni con disabilità riconosciuta per 1.000 residenti 0-64. Nei metadati e nella batteria comunale non è esposta una disaggregazione per sesso.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "La fonte regionale definisce e pubblica l'indicatore sulla fascia complessiva 0-64 anni; non espone classi d'età interne metodologicamente equivalenti per questo indicatore comunale.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
        },
        "emsResponseTimeP75": {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "La batteria regionale pubblica il 75° percentile comunale del tempo di risposta 118 come valore aggregato; non rende disponibile lo stesso percentile distinto per sesso.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "La batteria regionale pubblica il 75° percentile comunale del tempo di risposta 118 come valore aggregato; non rende disponibile lo stesso percentile per classi d'età.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
        },
        "foreignBornSoleProprietorShare": {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "La fonte regionale pubblica la quota comunale di ditte individuali attive con titolare nato all'estero, senza una disaggregazione del titolare per sesso.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "La fonte regionale pubblica la quota comunale di ditte individuali attive con titolare nato all'estero, senza classi d'età del titolare per lo stesso indicatore.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
        },
        "innovationBusinessShare": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica è la quota di imprese attive appartenenti a specifiche divisioni ATECO. Il sesso non è una dimensione dell'impresa o del settore economico misurato.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica è la quota di imprese attive appartenenti a specifiche divisioni ATECO. L'età non è una dimensione dell'impresa o del settore economico misurato.",
            },
        },
        "municipalOnlineServicesAdvanced": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura la quota dei servizi comunali offerti online ai livelli più avanzati; il sesso non è una dimensione semantica dei servizi digitali conteggiati.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura la quota dei servizi comunali offerti online ai livelli più avanzati; l'età non è una dimensione semantica dei servizi digitali conteggiati.",
            },
        },
        "organicAgriculturalAreaShare": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura la quota di superficie agricola utilizzata coltivata con metodo biologico. Il sesso non è una dimensione della superficie fisica misurata.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura la quota di superficie agricola utilizzata coltivata con metodo biologico. L'età non è una dimensione della superficie fisica misurata.",
            },
        },
        "youthOtherStatus": {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "La batteria regionale pubblica la quota comunale dei giovani 15-24 anni in altra condizione professionale come valore aggregato; non espone lo stesso indicatore per sesso.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "La batteria regionale definisce la metrica sull'intera fascia 15-24 anni e non pubblica classi d'età interne comparabili per lo stesso indicatore comunale.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
        },
        "averageGrossRemunerationPerEmployee": {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "Le tavole Frame SBS Territoriale diffondono gli indicatori economici delle unità locali per territorio, attività economica, classe dimensionale e governance; non pubblicano la retribuzione lorda media comunale distinta per sesso.",
                "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
            },
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "Le tavole Frame SBS Territoriale diffondono gli indicatori economici delle unità locali per territorio, attività economica, classe dimensionale e governance; non pubblicano la retribuzione lorda media comunale per classi d'età.",
                "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
            },
        },
        "labourCost": {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "Il Frame SBS Territoriale pubblica il costo del lavoro delle unità locali con dettaglio territoriale/economico ma non lo disaggrega per sesso nel rilascio comunale governato.",
                "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
            },
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "Il Frame SBS Territoriale pubblica il costo del lavoro delle unità locali con dettaglio territoriale/economico ma non lo disaggrega per età nel rilascio comunale governato.",
                "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
            },
        },
        "labourProductivity": {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "La produttività territoriale è pubblicata dal Frame SBS come valore aggiunto per addetto delle unità locali; il rilascio ufficiale non espone una versione comunale distinta per sesso.",
                "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
            },
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "La produttività territoriale è pubblicata dal Frame SBS come valore aggiunto per addetto delle unità locali; il rilascio ufficiale non espone una versione comunale per classi d'età.",
                "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
            },
        },
        "turnoverPerPersonEmployed": {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "Il Frame SBS Territoriale diffonde fatturato e addetti per unità locale e territorio senza una disaggregazione comunale per sesso necessaria a costruire lo stesso rapporto.",
                "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
            },
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "Il Frame SBS Territoriale diffonde fatturato e addetti per unità locale e territorio senza una disaggregazione comunale per età necessaria a costruire lo stesso rapporto.",
                "sourceReference": "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/",
            },
        },
        "libraryActiveBorrowersPer100": {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "Il tracciato ufficiale del monitoraggio biblioteche contiene iscritti attivi totali e per classi d'età, ma non campi per sesso; lo stesso indicatore comunale non è quindi disaggregabile per sesso dalla fonte governata.",
                "sourceReference": "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf",
            },
            "eta": {
                "state": AVAILABLE,
                "evidence": "Il tracciato ufficiale espone gli iscritti attivi al prestito nelle classi 0-14, 15-24, 25-64 e 65+; la pipeline pubblica oggi soltanto l'indicatore totale per 100 residenti.",
                "sourceReference": "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf",
            },
        },
        "libraryLoansPerResident": {
            "sesso": {
                "state": UNAVAILABLE,
                "evidence": "Il tracciato ufficiale pubblica i prestiti totali e alcune categorie documentarie/di servizio, ma non il sesso dell'utente; non è disponibile una versione dello stesso indicatore per sesso.",
                "sourceReference": "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf",
            },
            "eta": {
                "state": UNAVAILABLE,
                "evidence": "Il tracciato distingue i prestiti totali e i prestiti della sezione ragazzi, ma non i prestiti per classi d'età dell'utente; la voce 'ragazzi' non è una disaggregazione anagrafica metodologicamente equivalente.",
                "sourceReference": "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf",
            },
        },
        "libraryWeeklyOpeningHours": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura ore medie settimanali di apertura di un servizio bibliotecario. Il sesso non è una dimensione semanticamente pertinente dell'orario di apertura.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica misura ore medie settimanali di apertura di un servizio bibliotecario. L'età non è una dimensione semanticamente pertinente dell'orario di apertura.",
            },
        },
        "tourismBeds": {
            "sesso": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica conta i posti letto disponibili nelle strutture ricettive; il sesso non è una dimensione del bene fisico conteggiato.",
            },
            "eta": {
                "state": NOT_APPLICABLE,
                "evidence": "La metrica conta i posti letto disponibili nelle strutture ricettive; l'età non è una dimensione del bene fisico conteggiato.",
            },
        },
}.items():
    METRIC_EVIDENCE.setdefault(metric_id, {}).update(dimensions)



for metric_id, dimensions in {
        "disability064Per1000": {
            "assoluto_normalizzato": {
                "state": UNAVAILABLE,
                "evidence": "La batteria regionale pubblica l'indicatore sintetico delle persone 0-64 anni con disabilità per 1.000 residenti 0-64; nel rilascio degli indicatori comunali non è esposto il conteggio assoluto companion necessario alla coppia assoluto/normalizzato.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "numeratore_denominatore": {
                "state": UNAVAILABLE,
                "evidence": "I metadati definiscono il tasso sulla popolazione 0-64, ma la batteria comunale diffonde il valore dell'indicatore senza pubblicare come campi separati numeratore e denominatore.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "categorie_specifiche": {
                "state": UNAVAILABLE,
                "evidence": "Il rilascio comunale espone un unico indicatore aggregato 0-64 anni con disabilità anche gravi e non pubblica, per lo stesso indicatore, categorie di disabilità o gravità.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
        },
        "foreignBornSoleProprietorShare": {
            "assoluto_normalizzato": {
                "state": UNAVAILABLE,
                "evidence": "La batteria regionale pubblica la percentuale di ditte individuali attive con conduttore nato all'estero, ma non affianca il corrispondente conteggio assoluto nello stesso rilascio comunale.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "numeratore_denominatore": {
                "state": UNAVAILABLE,
                "evidence": "Il valore diffuso è una percentuale sintetica; il file degli indicatori comunali non espone separatamente il numero di ditte con conduttore nato all'estero e il totale delle ditte individuali attive.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "categorie_specifiche": {
                "state": UNAVAILABLE,
                "evidence": "Per questo indicatore la batteria comunale non pubblica disaggregazioni per settore, paese di nascita o altra categoria del conduttore.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
        },
        "innovationBusinessShare": {
            "assoluto_normalizzato": {
                "state": UNAVAILABLE,
                "evidence": "La fonte regionale diffonde la quota percentuale di imprese attive nei settori dell'innovazione e non il corrispondente conteggio assoluto companion nello stesso rilascio comunale.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "numeratore_denominatore": {
                "state": UNAVAILABLE,
                "evidence": "I metadati identificano le divisioni ATECO incluse, ma la batteria pubblica l'indicatore percentuale aggregato senza i due conteggi che ne formano numeratore e denominatore.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "categorie_specifiche": {
                "state": UNAVAILABLE,
                "evidence": "Le divisioni ATECO che definiscono il perimetro sono documentate, ma il file degli indicatori comunali non diffonde valori separati per ciascuna divisione per questa metrica.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
        },
        "municipalOnlineServicesAdvanced": {
            "assoluto_normalizzato": {
                "state": UNAVAILABLE,
                "evidence": "La batteria regionale diffonde la percentuale di servizi comunali offerti online al massimo livello di disponibilità senza affiancare il relativo conteggio assoluto dei servizi.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "numeratore_denominatore": {
                "state": UNAVAILABLE,
                "evidence": "Il rilascio comunale espone la quota sintetica dei servizi ai livelli avanzati, non i conteggi separati dei servizi avanzati e dei servizi complessivamente considerati.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "categorie_specifiche": {
                "state": UNAVAILABLE,
                "evidence": "I metadati descrivono i livelli 3 e 4 della rilevazione ICT, ma la batteria comunale non pubblica per questa metrica valori distinti per livello o per tipologia di servizio.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
        },
        "organicAgriculturalAreaShare": {
            "assoluto_normalizzato": {
                "state": UNAVAILABLE,
                "evidence": "La batteria regionale pubblica la percentuale di SAU coltivata con metodo biologico e non affianca nello stesso rilascio comunale la superficie biologica assoluta.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "numeratore_denominatore": {
                "state": UNAVAILABLE,
                "evidence": "Il file degli indicatori comunali diffonde la quota percentuale di SAU biologica senza esporre separatamente come campi la SAU biologica e la SAU totale usate nel rapporto.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "categorie_specifiche": {
                "state": UNAVAILABLE,
                "evidence": "La batteria pubblica un valore aggregato della quota biologica e non espone, per questa metrica, categorie di coltura o altre disaggregazioni agricole.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
        },
        "youthOtherStatus": {
            "assoluto_normalizzato": {
                "state": UNAVAILABLE,
                "evidence": "La fonte regionale diffonde la percentuale dei giovani 15-24 anni in altra condizione professionale senza il corrispondente conteggio assoluto companion nel rilascio comunale.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "numeratore_denominatore": {
                "state": UNAVAILABLE,
                "evidence": "La batteria pubblica la quota sintetica sulla fascia 15-24 anni e non espone come campi separati il numero di giovani in altra condizione e la popolazione di riferimento.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
            "categorie_specifiche": {
                "state": UNAVAILABLE,
                "evidence": "L'indicatore regionale aggrega la voce 'altra condizione professionale' e non la scompone in categorie ulteriori nel file comunale.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
        },
        "emsResponseTimeP75": {
            "categorie_specifiche": {
                "state": UNAVAILABLE,
                "evidence": "Il metadato regionale definisce un unico 75° percentile dell'intervallo tra allarme e arrivo del primo mezzo; la batteria comunale non espone lo stesso percentile per priorità, tipologia di mezzo o altra categoria d'intervento.",
                "sourceReference": "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1",
            },
        },
        "tourismBeds": {
            "serie_storica": {
                "state": AVAILABLE,
                "evidence": "La rilevazione Istat sulla capacità ricettiva è annuale e viene diffusa su annualità successive; la pipeline governata conserva oggi il dato pubblicato senza acquisire una serie storica strutturata della metrica.",
                "sourceReference": "https://indata.istat.it/ctur/index.php",
            },
            "dettaglio_territoriale": {
                "state": AVAILABLE,
                "evidence": "Istat rileva i posti letto a livello di singolo Comune e diffonde gli stessi aggregati anche a scale territoriali più ampie, rendendo disponibile un dettaglio territoriale coerente oltre alla vista comunale governata.",
                "sourceReference": "https://www.istat.it/informazioni-sulla-rilevazione/capacita-degli-esercizi-ricettivi/",
            },
            "benchmark_toscana_italia": {
                "state": AVAILABLE,
                "evidence": "Istat diffonde la capacità ricettiva e i posti letto per Italia e regioni con la stessa famiglia statistica, consentendo il benchmark Toscana/Italia coerente con il dato comunale.",
                "sourceReference": "https://noi-italia.istat.it/pagina.php?L=0&categoria=8&dove=ITALIA",
            },
            "categorie_specifiche": {
                "state": AVAILABLE,
                "evidence": "La rilevazione Istat distingue i posti letto per tipologia di struttura ricettiva e, per gli alberghi, anche per categoria e classe dimensionale; la pipeline pubblica oggi il totale senza questa disaggregazione strutturata.",
                "sourceReference": "https://indata.istat.it/ctur/index.php",
            },
        },
        "economyActivityAtlas": {
            "frequenza_infra_annuale": {
                "state": AVAILABLE,
                "evidence": "La Banca dati Imprese Toscana usa il Registro Imprese InfoCamere: per imprese registrate e attive l'anno in corso è riferito all'ultimo trimestre disponibile e la Regione pubblica anche serie storiche trimestrali dal 2009. La pipeline governa oggi l'atlante su base annuale.",
                "sourceReference": "https://www.regione.toscana.it/statistiche/banca-dati-imprese",
            },
        },
}.items():
    METRIC_EVIDENCE.setdefault(metric_id, {}).update(dimensions)


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
