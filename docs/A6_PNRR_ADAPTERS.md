# A6 — Finanziamenti e progetti PNRR

Due carrier, `pnrrFunding` e `pnrrConcluded`, sulla fotografia regionale del **25 settembre 2026**. `2026` è soltanto un alias di quella data: importi cumulati censiti, non flussi annuali. Nessuna nuova acquisizione o modifica dei dati pubblici.

## Perimetro e attribuzione

Snapshot versionato `data/source-snapshots/pnrr-toscana-2026-09-25.json`: 101 record selezionati, ID progetto globalmente unici; area PNRR o PNRR-PNC, PNC puro escluso, forma giuridica Comune. L'attribuzione segue **soggetto_attuatore**, non `codistat` o ubicazione. Sei progetti del Comune di Viareggio hanno localizzazione Camaiore; un progetto del Comune di Stazzema ha localizzazione Sarteano. Il portafoglio non misura tutti i progetti ubicati nel territorio, né tutti gli attuatori pubblici/privati.

Il replay riguarda i 101 record normalizzati congelati. Il CSV originario di 45.364 righe non è congelato integralmente: il relativo SHA documentale è riportato, senza dichiarare un replay originale o una nuova verifica live. Hash dei byte, fingerprint dell'intero oggetto e delle definizioni pubbliche sono verificati anche dopo cache. Il vecchio blocco `perTown` dello snapshot contiene confronti anteriori alla revisione pubblica: è conservato e fingerprintato, ma non usato come fonte dei valori correnti.

## Viste e rapporti

| Carrier | Dimensione | Unità / significato |
|---|---|---|
| pnrrFunding | total | euro PNRR censiti / residenti |
| pnrrFunding | nativeRatio | stesso valore con componenti e pooling delle somme |
| pnrrFunding | fundingEuro | somma `importo_finanziato_pnrr`, euro nominali |
| pnrrConcluded | total | progetti macrofase ReGiS 5 / progetti selezionati × 100 |
| pnrrConcluded | nativeRatio | stesso valore con conteggi e pooling delle somme |
| pnrrConcluded | concludedProjects | conteggio progetti macrofase ReGiS 5 |
| pnrrConcluded | selectedProjects | conteggio progetti nel portafoglio |

Tutte le viste ammettono consultazione, confronto e rango descrittivo sui sette Comuni. Non sostituiscono valori numerici con formattazioni UI arrotondate. Le somme degli importi sono calcolate in Decimal al centesimo. I residenti sono il carrier Istat POSAS **1 gennaio 2026**, con fingerprint separato e date distinte: denominatore pubblico verificato, nessun nuovo replay dei file POSAS originari in questo adapter.

Pooling solo `nativeRatio`, entro la stessa fotografia: euro / residenti oppure progetti in macrofase 5 / progetti selezionati. 36.683.107,64 € / 158.520 residenti = 231,40996492556144 €/residente; 78 / 101 × 100 = 77,22772277227723%. La media semplice dei tassi comunali non è il valore Versilia. ID globalmente unici e assegnazione esclusiva all'attuatore attestano l'additività, non il campo geografico di localizzazione.

## Stato e limiti

La definizione usa esclusivamente `fase_avanzamento_da_regis == '5. conclusione'`. Viareggio ha **18** progetti così classificati, contro **19** usando `fase_avanzamento_da_monitoraggio_progetti`. Quattro progetti in macrofase 5 riportano `COLLAUDO avviata`. Macrofase, collaudo, chiusura effettiva e apertura di un servizio restano distinti. Finanziamento censito non è erogazione, pagamento, spesa sostenuta, costo totale o cofinanziamento.

Nessuna storia del portafoglio omogenea congelata: serie, variazioni, trend e differenze temporali rifiutati. Benchmark geografici, anomalie e associazioni con altri carrier non revisionati rifiutati. Il riferimento Versilia è verificato come aggregato nativo; l'operazione `benchmark_gap` resta fuori dal lotto. Nessuna lettura di efficienza, efficacia o priorità inferita dai ranghi.

## Verifiche

Ancore indipendenti in centesimi, conteggi e residenti per sette Comuni; 49 osservazioni, 28 componenti, quattro aggregazioni (tutti / Camaiore e Massarosa, due carrier). Replay separato dei 101 record, casi di localizzazione diversa, divergenza delle fasi, collaudi avviati, puntatori ai record/catalogo e attacchi a byte, cache, hash, identità, definizioni, importi, fasi, residenti e riepiloghi. 134 domande aggiunte preservando integralmente le 3.188 precedenti. Report derivati in `reports/a6-pnrr/`; prestazioni descrittive, senza soglie portabili. Quick locale completo prima della pubblicazione; Full completo locale e CI Quick→Full/A3 sullo stesso albero prima della prontezza al merge del proprietario.
