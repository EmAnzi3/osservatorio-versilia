# Storico mensile MIMIT — terzo trimestre 2026

Acquisizione del 4 ottobre 2026. La serie pubblica si estende da gennaio 2022–giugno 2026 a gennaio 2022–settembre 2026: 57 mesi, sei Comuni con impianti e Stazzema n.d. I 54 mesi precedenti e il dato puntuale del 3 ottobre restano invariati. Nessuna modifica al renderer, alla UI o ai golden master.

## Fonte e metodo

Il backfill esistente `scripts/backfill_fuel_history_mimit.py --start 2026-07 --end 2026-09` usa anagrafica giornaliera, prezzi self-service Benzina/Gasolio, mediana comunale giornaliera e media aritmetica delle mediane giornaliere disponibili.

| Mese | Giorni disponibili | Giorni calendario |
|---|---:|---:|
| Luglio | 31 | 31 |
| Agosto | 31 | 31 |
| Settembre | 29 | 30 |

L'archivio nazionale prezzi non contiene il CSV del **5 settembre 2026**. La media di settembre usa i 29 giorni disponibili per ciascun Comune/fuel coperto; nessuna interpolazione o sostituzione del giorno mancante. La copertura è registrata nello snapshot. Ottobre è in corso e non viene incluso come media mensile.

- [Archivio prezzi Q3](https://opendatacarburanti.mise.gov.it/categorized/prezzo_alle_8/2026/2026_3_tr.tar.gz): 51.564.119 byte, SHA-256 `6ec064ec4fe74f2381345df9762aaa5004422fb9871a30dc95c4d411077967a2`.
- [Archivio anagrafica Q3](https://opendatacarburanti.mise.gov.it/categorized/anagrafica_impianti_attivi/2026/2026_3_tr.tar.gz): 111.386.435 byte, SHA-256 `41f4c0d9c3b89cba3c6534f1d688c1bf1db3988425630d92c44b1d0365fe351f`.

Entrambi gli archivi ufficiali risultano pubblicati/modificati il 1° ottobre. Gli hash riguardano i file integralmente scaricati, non una HEAD o un contenuto parziale.

## Validazione

91 fotografie giornaliere, 3 mesi, 6 Comuni × 2 carburanti. Date senza duplicati; periodi luglio/agosto/settembre; copertura delle 36 medie riconciliata con i giorni disponibili. Stazzema mantiene null e zero giorni misurati. Prefisso storico di 54 mesi semanticamente identico alla versione precedente. La regressione browser esistente verifica 57 punti per ciascun Comune, gennaio 2022 e settembre 2026 come estremi. Esiti finali Quick/Full e pubblicazione riportati nella PR.
