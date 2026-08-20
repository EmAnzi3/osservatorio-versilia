# Lotto A · Redditi e fiscalità

## Scopo

Seconda tranche del pacchetto di candidati pensato anche per le future letture editoriali dell’Osservatorio Versilia. La base è `main` dopo la pubblicazione della prima tranche Demografia (PR #78) e resta vincolante il contratto globale della PR #79 (`docs/coerenza-interfaccia.md`).

Questa fase parte dall’audit della fonte primaria prima di aggiungere nuovi indicatori al catalogo.

## Candidati della tranche

| Candidato | Fonte | Stato iniziale | Decisione di questa fase |
|---|---|---|---|
| Contribuenti ogni 100 adulti | MEF + Istat | VERIFY | **Non materializzare finché non è definito un denominatore metodologicamente difendibile**. La fonte MEF fornisce i contribuenti, ma “adulti” non può essere scelto arbitrariamente tra 15+, 18+ o altra fascia. |
| Reddito dichiarato per fonte: dipendente, pensione, autonomo, impresa ecc. | MEF · Redditi e principali variabili IRPEF su base comunale | GO fonte | Verificare schema 2024, copertura 7/7 e materializzare come **dataset di approfondimento**, non come una card per ogni fonte reddituale. |
| Peso dei redditi da pensione | MEF · Redditi e principali variabili IRPEF su base comunale | GO fonte | Se il CSV espone ammontare del reddito da pensione e reddito complessivo omogenei 7/7, materializzare un indicatore percentuale con formula esplicita. |
| Distribuzione completa per fasce di reddito | MEF · Redditi e principali variabili IRPEF su base comunale | GO fonte | Rafforzare il composito `incomeDistribution` / dataset di dettaglio esistente senza creare una nuova card duplicata. |

## Fonte primaria verificata

Dipartimento delle Finanze — Open Data Dichiarazioni, **2025 a.i. 2024**, pubblicato il **23 aprile 2026**. Il dataset comunale dichiara tra le variabili: numero contribuenti, reddito da lavoro dipendente e assimilati, reddito da pensione, reddito da lavoro autonomo, redditi d’impresa, reddito da partecipazione, reddito complessivo e le fasce complete di reddito.

URL di riferimento: `https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes`

Archivio CSV ufficiale individuato dalla pagina MEF: `Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip`.

## Gate tecnico

Il probe `scripts/probe_mef_income_lotto_a.py` deve produrre un artifact che documenti:

- intestazioni reali del CSV, senza presupporre il nome esatto delle colonne;
- copertura effettiva dei sette Comuni;
- colonne candidate per numero contribuenti, reddito complessivo, reddito da pensione e altre fonti;
- colonne delle fasce di reddito;
- righe grezze dei sette Comuni, per poter validare semantica e unità prima della materializzazione.

Nessun dato entra in `data/site-data.json` in questo commit di audit. Dopo esito positivo del probe, la stessa Draft PR potrà materializzare i soli candidati che superano il gate.

## Contratto UI e dati

- nuovi indicatori solo nella fonte canonica `data/site-data.json`;
- dataset di dettaglio non diventano automaticamente nuove card;
- renderer, storico, tooltip e formattazione devono riusare i componenti canonici;
- Comuni in ordine alfabetico; nessun ranking/podio;
- `n.d.` e `n.a.` conservano il significato definito dalla #79;
- nessun dato annuale parziale;
- il collaudo finale deve passare `scripts/test_site_consistency.py` e i controlli browser della #79.
