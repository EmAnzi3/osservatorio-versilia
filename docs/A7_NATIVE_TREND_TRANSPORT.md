# A7 — trend nativo: prova selettiva di trasporto

A6 DONE, A7 IN_PROGRESS. Incremento tecnico del passo A7.5.3, scelto dal
residuo della matrice #469: 202 viste dichiarano `trend`, ma la dichiarazione
non garantisce la calcolabilità della selezione. Nessuna nuova acquisizione.

## Perimetro

Il profilo opzionale `trends` genera una richiesta per vista dichiarata e per
Comune: `trend` con un solo Comune, senza periodi espliciti. A6 sceglie la serie
nativa e applica integralmente le proprie guardie su continuità, periodi,
copertura, universo e metodo. Non si selezionano finestre, estremi o anni dal
titolo. Non si scartano null, discontinuità o osservazioni per ottenere un trend.
Nessun `allowPartial` aggiunto, metodo modificabile o previsione.

La risposta originale conserva pendenza OLS, unità per anno, n, asse temporale,
`forecast=false`, osservazioni, fonti e avvertenze quando calcolabile. Un rifiuto
resta tale anche dopo il consenso alla visualizzazione delle osservazioni
parziali. Non misura automaticamente miglioramento, criticità o efficacia.
Non ordina Comuni per pendenza e non abilita associazioni.

La matrice conserva per ciascuna vista `nativeScopeProbe`: scope, chiavi del
ledger, conteggi computed/rifiutati e motivi originali. Le chiavi consentono di
risalire alle richieste esatte e ai digest delle risposte. Il riepilogo
`trendProbeSummary` conta selezioni nel perimetro, non nuove prove numeriche
indipendenti. Gli altri perimetri e le coppie di correlazione restano condizionali.

## Riproduzione

Dopo la build ordinaria del catalogo effettivo:

```bash
python scripts/build_a7_query_runtime.py --catalog dist/data/site-data.json \
  --profile trends --output-dir /tmp/a7-trends
python scripts/a7_runtime_package.py --catalog dist/data/site-data.json \
  --runtime /tmp/a7-trends --output-dir /tmp/a7-trends-package
python scripts/audit_a7_accessibility.py --catalog dist/data/site-data.json \
  --registry dist/data/source-registry.json --runtime /tmp/a7-trends \
  --output-dir /tmp/a7-trends-audit
```

Le directory di output devono essere nuove. I tre default e i profili scelti
dalla build pubblica restano invariati: questo incremento non presenta trend
nell’interfaccia generale. Il lettore supporta soltanto richieste esatte del
profilo opzionale; finestre, metodi, Comuni multipli o consenso nella richiesta
non vengono riscritti per trovare una risposta. Schema/hash/budget e pacchetto
atomico restano quelli canonici.

## Gate e incremento successivo

Il gate di trasporto esistente include il profilo: due build byte-identiche,
parità Python, lettura reale desktop/mobile, rifiuti e richieste fuori perimetro,
confezionamento e corruzioni. Le verifiche UI continuano a coprire i profili
presentati e accertano che il nuovo trasporto non abiliti controlli impliciti.
Quick e Full locali ordinari, CI Quick→Full effettivo e A3 sul medesimo candidato.
Misura completa, ambiente e attestazioni finali nella PR e nelle evidenze.

La futura integrazione pubblica richiede una presentazione comprensibile di
periodi effettivi, unità della pendenza, n, metodo e limiti, preview/browser e
misura del costo combinato. Non è autorizzata da questo profilo tecnico.
Pubblicazione della #469 e gate del nuovo candidato sono verifiche separate.

## Integrazione guidata candidata dopo #471

`A7_NATIVE_TREND_INTERFACE.md` descrive il successivo incremento, che sceglie
esplicitamente il profilo nella build pubblica candidata e ne verifica la
presentazione. Il comportamento tecnico isolato qui documentato conserva i
tre default e i propri limiti; non implica una pubblicazione già avvenuta.
