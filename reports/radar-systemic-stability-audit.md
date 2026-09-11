# Radar Opportunità — audit sistemico di stabilità

Data audit: 2026-09-11  
Baseline esaminata: `main` a `8d5fcaf0d8f91a846250dba6d9e2be7538f483df`

## Esito

I failure recenti non sono una sequenza di deterioramenti indipendenti dei dati.
Le cause ricorrenti sono due:

1. gate eseguiti su stati intermedi diversi dello stesso run;
2. stato tecnico delle fonti persistito soltanto dai run riusciti.

La stratificazione `daily -> revalidated -> resilient (h4) -> stable (h5) ->
audit_fixed` amplifica entrambi i rischi perché modifica a runtime le funzioni dei
livelli precedenti. La stabilizzazione mantiene per ora gli entry point
compatibili, ma sposta la decisione su invarianti condivisi e testabili.

## Matrice delle cause radice

| Run / failure | Causa tecnica | Vera perdita di affidabilità | Protezione già presente | Gap residuo alla baseline |
|---|---|---:|---|---|
| #37 (08/09) e #25 (02/09): `coverageHold=1`, `coverageAudit=fail` | Fallimenti live/PDF e fonti critiche valutati nello stesso run senza memoria affidabile dei run rossi | Non dimostrata; #38 è verde sullo stesso SHA di #37 | retry, browser fallback, grace h5 | la grace leggeva solo l'ultimo snapshot verde; i fallimenti consecutivi dei run rossi non avanzavano |
| #40 (09/09): 40 `continuityHold` | il corpus audit completo veniva iniettato dopo il confronto con lo snapshot precedente | No | riconciliazione finale | il gate aveva già osservato un output parziale; corretto dalla materializzazione/replay anticipati |
| #41 (10/09): continuity + coverage + regional | Sviluppo Toscana non ripropone `Avviso Mercati Rionali`; la misura regionale equivalente resta classificata su un canale diverso | No: la misura era aperta e documentata | identità cross-source deterministica | mancava la riconferma live del dettaglio canonico |
| #42 (10/09): coverage + regional dopo continuity recuperata | la riconferma live rimette la misura nell'output, ma il safety-net Regione era già stato valutato sulla fotografia precedente | No | dettaglio canonico live; alias `st-mercati-rionali-2026` | `coverageHold` regionale obsoleto non ricalcolato |
| #43 (10/09) e #44 (11/09): stesso blocco con diagnostica completa | identico difetto d'ordine del run #42; la nuova diagnostica lo rende visibile ma non lo risolve | No | artifact completo PR #173 | decisione finale composta da stati temporalmente incoerenti |
| Quality gate 11/09: Jazz 2027 ancora aperto dopo la scadenza del 10/09 | Il gate assumeva `application_open` per le schede legacy senza lifecycle, la funzione di expiry no; la materializzazione non applicava la transizione temporale agli snapshot già accettati | Sì per la scheda, non per il resto del corpus | Il refresh archiviava già entry scadute con lifecycle esplicito | Uniformare il default legacy e archiviare gli scaduti anche in materializzazione |
| Live replay PR #175: timeout HTTP + timeout Chromium + reader 403 su MiC Spettacolo | `DiscoveryFetchError` era un `RuntimeError`, fuori dal contratto di errori di rete catturati per singola fonte dal collector; il run abortiva prima dei gate e degli artifact | No: una singola fonte non prova una perdita complessiva di affidabilità | fallback HTTP/Chromium/reader e source health già presenti | Ricondurre l'esaurimento dei trasporti all'errore di rete source-scoped e lasciare decidere source health/coverage a fine run |

## Invarianti della pipeline stabilizzata

1. Discovery, iniezioni deterministiche e replay completano prima dei gate finali.
2. La continuity viene riconciliata e tenta il dettaglio canonico prima della
   completezza regionale.
3. Il safety-net regionale è idempotente: elimina soltanto le proprie precedenti
   code/hold e li ricostruisce sullo stato finale; non tocca hold di altri gate.
4. La coverage runtime viene valutata prima dell'unica assert finale, così una
   failure simultanea non nasconde gli altri blocker.
5. La diagnostica dell'ultimo run fallito alimenta il run seguente per la sola
   memoria tecnica delle fonti. Non promuove opportunità e non sostituisce una
   verifica primaria.
6. Timeout/403 isolati restano tollerabili; fallimenti persistenti di tutte le
   fonti ufficiali di una famiglia restano bloccanti.

## Failure intenzionalmente bloccanti

- opportunità pubblica del run precedente non scaduta, non riconciliata e non
  riconfermata da un dettaglio ufficiale verification-grade;
- candidato regionale comunale rimasto realmente irrisolto oltre la finestra di
  revisione;
- coverage hold di una verifica diretta;
- tutte le fonti ufficiali di una famiglia obbligatoria fuori grace;
- backtest sotto soglia;
- coverage contract non soddisfatto;
- output vuoto.

Reader proxy, pagine mirror non ufficiali e similarità fuzzy non eliminano
nessuno di questi blocker.

## Copertura di regressione

La suite giornaliera copre: listing false-negative con dettaglio aperto, dettaglio
chiuso, 404, redirect same-host, timeout/403, fonte primaria KO con secondaria OK,
famiglia critica KO persistente, identità cross-source, scadenza, failure coverage,
failure regionale, failure simultanei e run pulito. Il replay documentale storico
continua a verificare precision, recall e lifecycle senza fissare la prova di
stabilità a una sola data operativa.
