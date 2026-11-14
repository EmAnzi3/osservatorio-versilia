# A7 — perimetro preparato degli incroci (A7.5.4)

Terzo incremento A7.5.4, dopo il trasporto (#474) e l’anteprima guidata (#476).
A6 resta DONE e A7 IN_PROGRESS. Questo passo misura e rivede il perimetro di
richieste da preparare; non pubblica l’interfaccia degli incroci e non cambia
default, materializzatore pubblico, interfaccia v6 o divieto
`public=True, associations=True`.

## Misura sul catalogo effettivo

Fonte: le 202 associazioni già presenti fra le domande verificate A6
(`ci/semantic-verified-questions.json`), eseguite dal motore A6 sul catalogo
effettivo (`catalogSha256` `1416209c…`, 26 ottobre 2026).

- **6 calcolate**, tutte fra i sette Comuni con Spearman e n = 7.
- **196 rifiuti** originali A6. La gran parte (175) è `*_not_jointly_reviewed`
  o equivalente: la coppia non è stata rivista congiuntamente. Gli altri
  riguardano periodi diversi, universi o riferimenti non comparabili,
  stock/flusso o operazioni non attestate.

Il perimetro calcolabile è quindi limitato dalla revisione metodologica A6, non
dal costo di trasporto. Il costo misurato è marginale:

| Piano | Componenti | Risposte gzip aggiunte | Manifest aggiunto |
| --- | --- | --- | --- |
| 6 calcolate | 6 | ≈ 39,9 KB | ≈ 4,9 KB |
| 6 calcolate + 26 rifiuti tipo | 32 | ≈ 132 KB | ≈ 22 KB |

Sul runtime pubblico completo (8 profili, 225 metriche) il piano da 32
componenti porta le richieste da 50.523 a 50.555 e i byte gzip da 127.146.205 a
127.278.520 (+0,10%). Le cifre sono misure di trasporto, non nuovi casi
numerici indipendenti.

## Revisione e decisione del proprietario

Decisione di Ema del 26 ottobre 2026:

1. **Perimetro = le 6 associazioni calcolabili.** I selettori pubblici non
   offrono coppie che danno sempre un rifiuto. I rifiuti restano consultabili
   nelle domande verificate e nei gate, non nel menu degli incroci.
2. **Motivi in italiano.** Le richieste originali avevano un motivo in inglese
   (“Technical seven-town descriptive example…”) o generico. Il piano
   `ci/a7-association-perimeter.json` usa motivi italiani espliciti. Sono nuove
   richieste esatte: selettori, asse e metodo identici a quelli verificati; A6
   le esegue in modo nativo e il risultato coincide con quello della richiesta
   originale, salvo l’eco del motivo.

Le sei associazioni: popolazione × reddito imponibile medio (2024); addetti
nelle unità locali × occupazione femminile; dinamica naturale × mobilità
residenziale (2024); tempo pieno nella primaria × mense scolastiche (2024/25);
pendolari in entrata × in uscita; autocontenimento del lavoro × saldo
pendolare.

Nell’anteprima su runtime completo le etichette delle variabili vengono dal
catalogo canonico; a 320 px la pagina non scorre orizzontalmente. Su un runtime
ridotto a una metrica le altre variabili mostrano l’ID tecnico: per questo la
misura richiede la build pubblica completa.

## Gate

`scripts/test_a7_association_perimeter.py`, nei controlli sul catalogo effettivo
di Quick/Full (`ci/workflow-contract.json`), verifica che:

- il piano rispetti il contratto del workbench (≤ 32 componenti, ≤ 100.000 byte);
- gli ID coincidano, nell’ordine, con le associazioni calcolabili verificate:
  se A6 ne rende calcolabile un’altra, il gate fallisce e chiede una revisione
  invece di allargare il perimetro da solo;
- ogni richiesta differisca dall’originale soltanto per il motivo, in italiano e
  con il limite causale esplicito;
- risposta italiana e originale coincidano campo per campo, salvo il motivo, e
  rispettino le attese A6 (coefficiente, n = 7, avvertenze);
- il costo aggiunto resti entro 80 KB gzip di risposte e 12 KB di manifest.

## Rollout pubblico (14 novembre 2026)

Su richiesta di Ema gli incroci sono pubblicati in «Chiedi», limitati al piano
rivisto. `materialize_a7_public_explorer.py` costruisce il runtime pubblico con
`ci/a7-association-perimeter.json` e integra l'interfaccia «Due variabili».
`build_a7_explorer_preview.py` accetta `public=True, associations=True` solo se
il piano del runtime coincide passo per passo con quello rivisto; qualunque
altro piano resta rifiutato con `association_interface_preview_only`.
`a7_explorer_release.validate_explorer` richiede nel sito pubblico
`associationInterface = reviewed_plan_public`, l'interfaccia degli incroci e il
piano nel manifest. Nuove coppie entrano solo dopo una revisione congiunta A6,
mai scelte dal coefficiente.

## Perimetro allargato (14 novembre 2026)

Su richiesta di Ema («valuta se c'è altro oltre ai 6») ho cercato, fra gli
indicatori principali dei temi e altri d'uso frequente (44 con un solo periodo
fra i sette Comuni), le coppie che il motore A6 già calcola: 65. Ne ho scelte 11
per pertinenza alle domande dei cittadini, **senza guardare il coefficiente**,
escludendo coppie con componenti condivise ovvie (per esempio divario di genere
e occupazione femminile) o puramente contabili:

- reddito × diploma; reddito × disoccupazione; reddito × occupazione;
  diploma × disoccupazione (2024);
- reddito × rifiuti per residente; differenziata × costo del servizio rifiuti;
  rifiuti per residente × costo del servizio (2024);
- popolazione × indice di vecchiaia (2026);
- intensità turistica × spesa corrente per residente; intensità turistica ×
  spesa per ordine pubblico e sicurezza (2025);
- abitazioni non occupate × patrimonio abitativo per 1.000 residenti (2023).

Ogni coppia ha una domanda verificata in `ci/semantic-verified-questions.json`
con coefficiente atteso calcolato a parte dai ranghi (frazione esatta, o
Pearson sui ranghi medi quando ci sono pari merito) e un motivo italiano con il
limite causale. Il piano passa da 6 a 17 componenti (+≈109 KB gzip di risposte,
+≈14 KB di manifest); il gate ora limita il costo per componente con lo stesso
margine di prima.

Coppie oggi rifiutate dal motore (`*_pair_not_jointly_reviewed`, periodi
diversi) restano fuori: aggiungerle richiede una revisione dell'adapter, non
del solo piano.
