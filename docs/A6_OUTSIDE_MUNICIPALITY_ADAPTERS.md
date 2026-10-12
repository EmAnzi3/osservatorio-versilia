# A6 — Lavoratori fuori Comune, quota censuaria 2021

Il lotto v53 abilita `outsideMunicipality` senza acquisizioni o modifiche ai dati/UI. Una sola vista `total`, confronto e rango dei sette valori pubblicati, riferimento esclusivo 2021, percentuale a un decimale. Il catalogo e il fingerprint sono identici in sorgente ed effettivo.

## Fonte e universi

Fonte dichiarata dal catalogo: Istat — Censimento permanente, mobilità; https://www.istat.it/statistiche-per-temi/censimenti/popolazione-e-abitazioni/risultati/ . Definizione pubblicata: occupati residenti che lavorano in un Comune diverso da quello di residenza. Questo lotto verifica il carrier pubblico congelato, non il rilascio originale, i microdati o i conteggi censuari; non certifica ulteriori dettagli dell’universo non conservati dal catalogo.

La matrice per lavoro già governata in `docs/A6_COMMUTING_ADAPTERS.md` riguarda una sottopopolazione di pendolari abituali, almeno tre giorni a settimana con ritorno giornaliero. I suoi margini non riconciliano la quota censuaria: Massarosa pubblica 62,9%, mentre 5.568 uscite / 7.800 pendolari residenti × 100 = 71,384615…%. `outsideMunicipality` non è quindi il complemento di `selfContainment`. Componenti e benchmark della matrice non vengono trasferiti alla quota censuaria. Le classificazioni A3 reali sono conservate: un’opportunità di acquisizione non certifica un rapporto riconciliato.

| Comune | Quota pubblicata 2021 |
|---|---:|
| Camaiore | 48,4% |
| Forte dei Marmi | 49,3% |
| Massarosa | 62,9% |
| Pietrasanta | 49,1% |
| Seravezza | 64,2% |
| Stazzema | 63,2% |
| Viareggio | 31,8% |

Il rango è descrittivo e non misura fabbisogno TPL, qualità, dipendenza territoriale o priorità politica. Non si deducono mezzi, frequenza, distanze, tempi, destinazioni, studio o effetti causali. Il riferimento 2021 non è una fotografia corrente. Lavorare in un altro Comune non significa uscire dalla Versilia.

## Componenti e aggregazioni

Numeratore e denominatore censuari non sono congelati separatamente: nessun conteggio retro-derivato dalla quota arrotondata, né rapporto nativo. La media pubblica 52,7% assegna lo stesso peso ai sette Comuni, non è la quota aggregata dei lavoratori della Versilia. Anche con componenti, sommare le uscite comunali includerebbe i movimenti tra Comuni del gruppo: occorrerebbe la matrice OD coerente per la quota fuori dal territorio selezionato. Pooling rifiutato; nessuna media territoriale sostituita al rapporto.

Storia, variazioni/trend, benchmark Toscana/Italia/Versilia, anomalie e coppie non revisionate sono rifiutati con motivi specifici. Sesso, studio, numeratore/denominatore, normalized/nativeRatio e fuori Versilia non sono viste abilitate.

## Evidenze e verifica

Sette ancore indipendenti in decimi di percentuale, ordine atteso, unità/periodo, puntatori con hash del catalogo, controesempio Massarosa, formule non equivalenti e prove ostili dopo cache su valori, identità, definizioni, storia/componenti aggiunte e benchmark. Il fingerprint dell’intero carrier viene verificato a ogni accesso. Nessun replay dei record originali dichiarato.

41 domande nuove; 3.501 precedenti invariate. Un caso legacy `commuting_census_share_refused` conserva ID e query di confronto, ma aggiorna testo/aspettativa alla consultazione ora abilitata, senza dichiarare equivalenza con la matrice. Report derivati `reports/a6-outside-municipality/`, audit completo, collegamenti e baseline prestazionale descrittiva; nessuna soglia di latenza di produzione.

Quick canonico locale prima del push; Full locale completo sequenziale e CI Quick→Full/A3 sullo stesso albero prima della prontezza al merge del proprietario. A6.4 resta parziale, A6.5–A6.6 aperte, A7 non avviata.
