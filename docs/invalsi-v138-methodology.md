# INVALSI v1.38.0 — nota metodologica

## Perimetro

La v1.38.0 introduce quattro indicatori nel tema **Istruzione**:

- Risultati INVALSI;
- Livelli e traguardi di competenza;
- Dispersione scolastica implicita;
- Eccellenza accademica.

Il dato comunale è letto direttamente dagli open data INVALSI con:

- `Aggregato_territoriale = Comune plesso`;
- `aggregazione = Totale`.

Il Comune indica quindi **la localizzazione del plesso scolastico**, non la residenza dello studente. Non vengono ricostruiti valori comunali a partire dai singoli istituti o plessi.

## Fonti

1. INVALSI — *Punteggi e percentuale di studenti nei livelli di competenza per ripartizioni territoriali e caratteristiche di contesto*, file `Report_generale_agg_2025.csv`, aggiornato il 3 dicembre 2025. SHA-256 del file sorgente: `2d88f9c17c57eb3b1c6c51666a17fca3c2c7830239874bb9359e67a5abe1c474`.
2. INVALSI — *Eccellenza accademica e dispersione scolastica implicita — valori percentuali*, file `Report_generale_unito_dispersione_e_eccellenti_agg_2025.csv`, aggiornato il 3 dicembre 2025. SHA-256 del file sorgente: `d6e1889464d40c851e22d4bccc4d2749e4b4b13f0ad1635d188a34f7cb60bff9`.

La build pubblica è offline: usa uno snapshot compatto versionato, ricostruito da cinque frammenti gzip+base64. Il payload ricostruito è verificato prima della materializzazione con SHA-256 `bee5b0021704b2053277aa19df35d77ed0aa4b9e2cfc4dfa3d64c16a61c1fd65` e dimensione attesa di 70.859 byte.

## Risultati

L'indicatore principale usa `Punteggio_wle_medio`. La scala WLE viene mantenuta come punteggio numerico e non reinterpretata come percentuale.

Le 16 letture pubblicate coprono le combinazioni di grado e prova disponibili nel perimetro approvato: gradi 2, 5, 8, 10 e 13; Italiano, Matematica e, dove previsto, Inglese Reading e Listening.

## Livelli e traguardi

L'indicatore usa `Perc_traguardi` e conserva la distribuzione ufficiale nei livelli di competenza. Le etichette dipendono dalla prova e dal grado: livelli 1–5 per Italiano/Matematica dove previsti e livelli QCER per Inglese. Le categorie non vengono ricodificate.

## Benchmark

**Toscana** e **Italia** sono letti direttamente dalle righe ufficiali dello stesso dataset, con lo stesso anno, grado, materia e aggregazione della lettura comunale.

Non viene pubblicata una media Versilia INVALSI. I file non espongono il numero di studenti/prove valide necessario per una ponderazione corretta; `Percentuale_partecipazione` e `Pct_copertura` sono percentuali di copertura e non denominatori. È quindi vietata la media semplice dei valori comunali.

## Valori mancanti e copertura

I codici sorgente `888` e `999`, i valori assenti e le combinazioni territoriali non pubblicate sono convertiti in `null`/`n.d.`. Non vengono applicate stime, interpolazioni o trascinamenti.

Una parte degli `n.d.` è strutturale, soprattutto nei gradi della secondaria di II grado, perché non tutti i Comuni ospitano plessi che erogano quel grado. La presenza o assenza del dato non viene trasformata in zero.

Copertura corrente dei risultati 2024-25:

- grado 2: Italiano 5/7, Matematica 6/7;
- grado 5: 6/7 per tutte le prove pubblicate;
- grado 8: 4/7 per tutte le prove pubblicate;
- grado 10: 4/7 per Italiano e Matematica;
- grado 13: 4/7 per tutte le prove pubblicate.

## Serie storiche

La visualizzazione storica parte dalla finestra moderna comparabile definita nel gate dati:

- grado 2 Italiano/Matematica: 2018-19;
- grado 5 Italiano/Matematica: 2018-19;
- grado 5 Inglese: 2017-18;
- grado 8: 2017-18;
- grado 10 Italiano/Matematica: 2017-18;
- grado 13: 2018-19.

Il 2019-20 resta assente perché le prove nazionali non furono svolte. Per il grado 10 resta assente anche il 2020-21 nel dataset usato. I vuoti non vengono collegati da valori inventati.

## Granularità degli istituti

Il dettaglio per singola istituzione/plesso è stato esplorato ma non incorporato nella v1.38.0. I risultati analitici di scuola sono prevalentemente restituiti nell'Area Riservata INVALSI; i materiali RAV pubblici non presentano un livello numerico uniforme e una stessa istituzione autonoma può comprendere plessi situati in Comuni diversi. Un eventuale dettaglio futuro richiederà una fonte pubblica, uniforme e territorialmente riconducibile al singolo plesso.
