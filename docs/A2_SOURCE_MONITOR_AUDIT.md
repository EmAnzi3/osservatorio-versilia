# A2.1 — audit della copertura operativa del Source Monitor

Data audit: 2026-09-15
Baseline auditata: `d498d2f931773cf8c30a8e051ccb340133d567a6`

## Scopo

Questo audit verifica se il controllo periodico delle fonti opera sullo stesso perimetro degli indicatori effettivamente pubblicati dopo la chiusura di `A1`.

A1 ha già dimostrato la copertura **strutturale**: tutti i 225 indicatori pubblicati sono censiti, rappresentati nello Stato dati e risolvono una policy fonte valida. A2 deve dimostrare una cosa diversa: che il monitor operativo controlli realmente quel medesimo perimetro e conservi evidenza dell'ultimo controllo.

## Perimetri da non confondere

1. **Catalogo sorgente canonico** — `data/site-data.json`: 181 indicatori sulla baseline auditata.
2. **Effective Public Catalog** — `dist/data/site-data.json`: 225 indicatori nella release pubblicata v1.40.0.
3. **Stato operativo del monitor** — `data/source-monitor-state.json`: evidenza dei probe e degli stati per indicatore realmente registrati.

Il catalogo sorgente resta l'unica fonte canonica da mantenere manualmente. Il catalogo pubblico è una vista derivata dalla build; il monitor deve usare quella vista come perimetro operativo senza introdurre un secondo manifest canonico.

## Pipeline attuale del controllo mensile

Il workflow `.github/workflows/monthly-data-refresh.yml` esegue, prima del monitor, soltanto la materializzazione PNRR:

```text
materialize_pnrr_toscana_draft.py
→ patch_pnrr_toscana_review.py
→ monthly_data_check_status.py
```

`monthly_data_check_status.py` usa per default:

```text
--data  data/site-data.json
--state data/source-monitor-state.json
```

Il wrapper chiama poi `monthly_data_check.py`, che usa anch'esso `data/site-data.json` e `data/source-registry.json` come input predefiniti.

Di conseguenza il run mensile opera sul catalogo sorgente disponibile nel checkout, non sull'Effective Public Catalog prodotto dall'intera catena di materializzazione.

## Conteggi hard-coded osservati

`data/source-registry.json` dichiara attualmente:

```json
{
  "expectedMetricCount": 181,
  "expectedInlineMetricCount": 177,
  "expectedExternalMetricCount": 4
}
```

`monthly_data_check.py` confronta esplicitamente il dataset ricevuto con questi valori. Questa verifica è coerente con il catalogo sorgente, ma non dimostra la copertura dei 225 indicatori pubblicati.

Cambiare semplicemente `181` in `225` non sarebbe una correzione: farebbe fallire il monitor sul catalogo sorgente oppure richiederebbe di duplicare il catalogo pubblico. `A2.2` deve invece eliminare dal percorso operativo i conteggi che possono essere derivati dal catalogo effettivamente monitorato.

## Stato operativo persistito

La baseline `data/source-monitor-state.json` ha `schemaVersion: 2` e `checkedAt: 2026-08-31T17:19:31+02:00` come ultimo controllo generale registrato.

L'audit svolto durante A1 aveva già confrontato gli ID dello stato operativo con l'Effective Public Catalog e rilevato:

- 225 indicatori pubblicati;
- 180 indicatori presenti nello stato operativo;
- 45 indicatori pubblicati senza stato operativo corrispondente;
- i 45 mancanti comprendono tutti i 44 indicatori aggiunti dalla materializzazione pubblica rispetto al catalogo sorgente, più `financialDebtProfile`.

Il problema non riguarda la policy fonte: A1 ha verificato 225/225 policy valide. Il gap riguarda esclusivamente la prova operativa di controllo e freschezza.

## Causa radice

Il Source Monitor oggi usa come perimetro implicito il catalogo sorgente invece del catalogo effettivamente pubblicato:

```text
data/site-data.json (181)
→ materializzazione parziale PNRR
→ monthly_data_check_status.py
→ monthly_data_check.py
→ validazione contro expectedMetricCount=181
→ data/source-monitor-state.json
```

La release pubblica segue invece l'intera catena dichiarata dal contratto di build e arriva a 225 indicatori.

Per questo un run mensile può essere verde e corretto rispetto ai propri input senza costituire prova di copertura operativa dell'intero prodotto pubblico.

## Decisione A2.1

`A2.1` è chiuso con questa conclusione:

> il monitor deve derivare il proprio perimetro dagli ID dell'Effective Public Catalog e deve poter dimostrare per identità degli ID quali indicatori pubblicati sono stati controllati, non limitarsi a un conteggio atteso del catalogo sorgente.

## Vincoli per A2.2

La correzione deve rispettare questi vincoli:

- `data/site-data.json` resta l'unico catalogo canonico sorgente;
- nessun nuovo inventario manuale di 225 ID;
- nessun `expectedMetricCount = 225` introdotto come nuova costante operativa;
- il perimetro del run deve essere derivato dalla stessa vista pubblica formalizzata in A1;
- il report deve distinguere chiaramente `pubblicati`, `configurati`, `controllati` e `senza evidenza operativa`;
- gli stati storici possono essere conservati, ma il run corrente deve rendere evidente qualsiasi ID pubblico non coperto.

## Prossimo step

`A2.2` deve modificare il percorso del monitor affinché il dataset e il registry operativi siano derivati dalla release pubblica corrente, eliminando i conteggi attesi hard-coded dove il perimetro è già ricavabile dagli ID effettivamente monitorati.
