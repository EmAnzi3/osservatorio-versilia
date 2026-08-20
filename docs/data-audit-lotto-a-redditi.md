# Lotto A · Redditi e fiscalità

## Scopo

Seconda tranche del pacchetto di candidati pensato anche per le future letture editoriali dell’Osservatorio Versilia. La base è `main` dopo la pubblicazione della prima tranche Demografia (PR #78) e resta vincolante il contratto globale della PR #79 (`docs/coerenza-interfaccia.md`).

## Esito della tranche

| Candidato | Fonte | Esito | Implementazione |
|---|---|---|---|
| Contribuenti ogni 100 adulti | MEF + Istat | **VERIFY** | Il numeratore MEF è disponibile 7/7, ma il denominatore “adulti” non viene scelto arbitrariamente tra 15+, 18+ o altra fascia. Nessuna pubblicazione finché la definizione non è metodologicamente chiusa. |
| Reddito dichiarato per fonte: dipendente, pensione, autonomo, impresa ecc. | MEF · Redditi e principali variabili IRPEF su base comunale | **PROMOSSO** | Materializzato nello snapshot `mef-income-lotto-a-2024.json` come dataset di approfondimento con frequenze e ammontari delle fonti MEF. Nessuna card separata per fonte. |
| Peso dei redditi da pensione | MEF · Redditi e principali variabili IRPEF su base comunale | **PROMOSSO** | Nuovo indicatore `pensionIncomeShare`: ammontare reddito da pensione / ammontare reddito complessivo × 100; copertura 7/7. |
| Distribuzione completa per fasce di reddito | MEF · Redditi e principali variabili IRPEF su base comunale | **PROMOSSA** | Otto classi MEF conservate nello snapshot e collegate a `incomeDistribution`. La card pubblica mantiene i quattro gruppi già validati: le celle MEF vuote restano `null` e non vengono trasformate in falsi zeri. |

## Fonte primaria verificata

Dipartimento delle Finanze — Open Data Dichiarazioni, **2025 a.i. 2024**, pubblicato il **23 aprile 2026**. Il dataset comunale espone numero contribuenti, reddito da lavoro dipendente e assimilati, reddito da pensione, reddito da lavoro autonomo, redditi d’impresa, reddito da partecipazione, reddito complessivo e otto fasce complete di reddito.

URL di riferimento: `https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes`

Archivio CSV ufficiale: `Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip`.

## Gate tecnico superato

Il probe `scripts/probe_mef_income_lotto_a.py` ha verificato:

- schema reale del CSV: **53 colonne**, separatore `;`, codifica UTF-8 con BOM;
- **7/7 Comuni** individuati univocamente tramite denominazione e codice Istat;
- presenza di `Numero contribuenti`;
- presenza di frequenza e ammontare del reddito da pensione;
- presenza di frequenza e ammontare del reddito complessivo;
- presenza delle fonti reddituali necessarie al dataset editoriale;
- presenza delle otto fasce MEF complete.

La materializzazione `scripts/materialize_income_lotto_a.py` conserva inoltre le celle vuote come `null`. Questo è rilevante, per esempio, per alcune classi reddituali alte o fonti con numerosità ridotta: nessun valore mancante viene reinterpretato come zero.

## Risultato nel catalogo

Dopo Demografia Lotto A la nuova tranche porta il catalogo di build a **130 indicatori complessivi: 126 inline + 4 climatici esterni**. L’unica nuova card è `pensionIncomeShare`; i dataset per fonte e per fasce complete non aumentano il numero degli indicatori pubblici.

`incomeDistribution` resta il composito pubblico già validato a quattro gruppi, ma ora è collegato al dataset completo a otto classi per future letture editoriali.

## Contratto UI e dati

- nuovi indicatori solo nella fonte canonica `data/site-data.json`;
- dataset di dettaglio non diventano automaticamente nuove card;
- renderer, storico, tooltip e formattazione riusano i componenti canonici;
- nessuna cella vuota della fonte viene trasformata in zero;
- `n.d.` e `n.a.` conservano il significato definito dalla #79;
- nessun dato annuale parziale;
- il collaudo finale deve passare `scripts/test_site_consistency.py` e i controlli browser desktop/mobile della #79.
