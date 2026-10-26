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

## Prossimo passo

Il rollout pubblico degli incroci resta separato e richiede approvazione:
collegare questo piano al materializzatore pubblico, rimuovere il divieto
soltanto per il piano rivisto, preview reale, browser 1440/390/320, Quick/Full
locali e CI Quick→Full. Nuove coppie entrano solo dopo una revisione congiunta
A6, mai scelte dal coefficiente.
