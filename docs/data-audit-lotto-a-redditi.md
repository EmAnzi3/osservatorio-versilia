# Lotto A · Redditi e fiscalità

## Scopo

Seconda tranche del pacchetto di candidati pensato anche per le future letture editoriali dell’Osservatorio Versilia. La base è `main` dopo la pubblicazione della prima tranche Demografia (PR #78) e resta vincolante il contratto globale della PR #79 (`docs/coerenza-interfaccia.md`).

## Esito della tranche

| Candidato | Fonte | Esito | Implementazione |
|---|---|---|---|
| Contribuenti ogni 100 maggiorenni | MEF + Istat | **PROMOSSO** | Nuovo indicatore `taxpayersAdultPopulationRate`: numero contribuenti MEF / residenti di 18 anni e più al 1° gennaio 2026 × 100. È un rapporto ogni 100, non la percentuale degli adulti che paga l’IRPEF. |
| Reddito dichiarato per fonte: dipendente, pensione, autonomo, impresa ecc. | MEF · Redditi e principali variabili IRPEF su base comunale | **PROMOSSO** | Nuovo composito `incomeSourceProfile`: un solo indicatore con selettore per 7 fonti. Per ogni fonte mostra ammontare / frequenza dei contribuenti che la dichiarano; le frequenze non vengono sommate come persone uniche. |
| Peso dei redditi da pensione | MEF · Redditi e principali variabili IRPEF su base comunale | **PROMOSSO** | Indicatore `pensionIncomeShare`: ammontare reddito da pensione / ammontare reddito complessivo × 100; copertura 7/7. |
| Distribuzione completa per fasce di reddito | MEF · Redditi e principali variabili IRPEF su base comunale | **PROMOSSA** | `incomeDistribution` mantiene la sintesi a 4 gruppi e aggiunge un dettaglio pubblico espandibile con le 8 classi MEF originali. Le celle vuote restano `n.d.` e non diventano zero. |

## Fonti

Dipartimento delle Finanze — Open Data Dichiarazioni, **2025 a.i. 2024**, pubblicato il **23 aprile 2026**. Il dataset comunale espone numero contribuenti, reddito da lavoro dipendente e assimilati, reddito da pensione, reddito da lavoro autonomo, redditi d’impresa, reddito da partecipazione, reddito complessivo e otto fasce di reddito.

Per il denominatore dell’indicatore contribuenti/maggiorenni viene usato Istat POSAS: popolazione comunale per singola età al **1° gennaio 2026**, sommando le età 18+.

URL MEF: `https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes`

URL Istat: `https://demo.istat.it/`

## Gate tecnico

Il probe MEF ha verificato schema reale del CSV, copertura 7/7, numero contribuenti, frequenze e ammontari delle fonti e delle otto fasce. La materializzazione completa aggiunge anche il denominatore 18+ ricostruito dal dettaglio POSAS 2026.

Le celle non valorizzate dal MEF sono conservate come `null`/`n.d.`. In particolare non vengono imputati zeri nelle fonti o nelle classi di reddito con valori mancanti.

## Risultato nel catalogo

La build completa arriva a **132 indicatori complessivi: 128 inline + 4 climatici esterni**.

Nuovi indicatori pubblici della tranche:

- `incomeSourceProfile` — Reddito medio dichiarato per fonte;
- `pensionIncomeShare` — Peso dei redditi da pensione;
- `taxpayersAdultPopulationRate` — Contribuenti ogni 100 maggiorenni.

`incomeDistribution` non viene duplicato: la card esistente guadagna il dettaglio a 8 fasce, visibile sia nel confronto territoriale sia nelle schede comunali.

## Contratto UI e dati

- renderer, shell e controlli restano quelli canonici;
- nessuna fonte reddituale genera una card separata;
- il dettaglio a 8 fasce è espandibile e preserva gli `n.d.`;
- nessun dato annuale parziale;
- registry e monitor sono aggiornati insieme al catalogo;
- il collaudo finale deve passare sia i test specifici Redditi sia il gate globale desktop/mobile della #79.
