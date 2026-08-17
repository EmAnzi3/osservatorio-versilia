# Aggiornamento mensile dei dati

## Obiettivo

Il controllo viene eseguito una volta al mese e può essere avviato anche manualmente. La procedura è prudenziale: verifica dati e fonti, registra lo stato degli indicatori, ma non pubblica valori senza controllo umano.

Il sistema separa sempre tre informazioni:

1. **periodo pubblicato**, preso dal catalogo canonico `data/site-data.json`;
2. **attualità rispetto alla fonte**, registrata soltanto quando esiste un'evidenza sufficiente sul periodo più recente;
3. **data dell'ultimo controllo Osservatorio**, prodotta dal monitor.

Un dato del 2024 può quindi risultare pienamente aggiornato nel 2026 se il 2024 è ancora l'ultimo periodo ufficialmente disponibile. L'età del dato non determina da sola lo stato.

## Architettura

Il sistema evolve i componenti già esistenti, senza introdurre un registro parallelo:

- `data/site-data.json` = **cosa pubblichiamo**: valori, periodo, fonte e metodo;
- `data/source-registry.json` = **come si aggiorna la fonte**: produttore, frequenza, cadenza indicativa, acquisizione e licenza;
- `data/source-monitor-state.json` = **cosa abbiamo verificato**: stato tecnico delle fonti e, con schemaVersion 2, stato per singolo indicatore.

La pagina pubblica `/stato-dati/` usa un file derivato durante la build (`dist/data/data-status.json`). Questo file non è una quarta fonte di verità e non viene mantenuto manualmente.

## Calendario

Il workflow `Controllo mensile dati` è programmato per il giorno 5 di ogni mese alle 05:17 UTC. Durante la revisione di una pull request il controllo viene eseguito in modalità offline: verifica struttura, copertura e coerenza del dataset senza contattare le fonti e senza generare notifiche operative.

## Cosa controlla

- presenza dei **127 indicatori** nel catalogo canonico e ripartizione attesa fra **123 incorporati e 4 climatici esterni**;
- copertura dei sette Comuni e codici Istat corretti;
- presenza di periodo, unità, fonte, metodo e formula;
- coerenza fra annualità e valori delle serie storiche;
- presenza, per ogni indicatore, di produttore, frequenza, cadenza di rilascio, modalità di acquisizione e licenza;
- raggiungibilità delle fonti ufficiali;
- modifica dei file ufficiali direttamente scaricabili;
- cambiamenti di URL, reindirizzamenti ed eventuali segnali HTTP;
- stato canonico di ogni indicatore.

## Stati degli indicatori

Gli stati pubblici sono distinti dagli esiti tecnici del workflow.

- `current` — **Ultimo dato disponibile**: il periodo pubblicato coincide con l'ultimo periodo verificato presso la fonte;
- `new_release_to_review` — **Nuovo rilascio da verificare**: è stato registrato un periodo più recente, ma non è ancora stato validato o pubblicato;
- `release_expected` — **Aggiornamento atteso**: è stata raggiunta una finestra di rilascio documentata, senza conferma di un nuovo dato;
- `source_unavailable` — **Fonte temporaneamente non verificabile**: il controllo non riesce ad accedere alla fonte;
- `verification_required` — **Verifica necessaria**: non esiste ancora evidenza sufficiente per certificare l'ultimo periodo disponibile.

`verification_required` non significa “dato vecchio”. È uno stato prudenziale: il sistema non presume che il periodo pubblicato sia ancora l'ultimo disponibile quando non può dimostrarlo.

## Prossimo rilascio

`expectedRelease` nel registro descrive la **cadenza indicativa** della fonte e non viene più presentato come una data certa.

Una vera previsione del prossimo rilascio viene esposta solo se la politica contiene `nextExpectedRelease` con una base documentata, per esempio:

```json
{
  "value": "2027-01",
  "precision": "month",
  "basis": "official_calendar",
  "evidenceUrl": "https://..."
}
```

Sono ammesse come basi automatiche soltanto `official_calendar` e `documented_schedule`. Una semplice frequenza annuale non genera da sola una data futura.

## Regola clima

Per i quattro indicatori climatici esterni resta valida la regola editoriale: **si pubblicano soltanto anni completi**. Periodi marcati `YTD`, `parziale`, `partial` o equivalenti non vengono trattati come una nuova annualità pubblicabile.

## Cosa non fa

- non stima dati mancanti;
- non interpola annualità per colmare buchi informativi;
- non sostituisce valori pubblicati;
- non considera una modifica HTML come prova automatica di un nuovo periodo;
- non effettua merge;
- non pubblica direttamente nuovi dati su GitHub Pages.

## Notifiche e registro

Per ogni esecuzione programmata o manuale il workflow:

1. crea, se necessario, l'issue `Registro controlli dati <anno>`;
2. aggiunge un commento con il rapporto mensile;
3. menziona `@EmAnzi3`;
4. conserva il rapporto completo come artifact per 90 giorni.

Ogni controllo **live riuscito** apre o aggiorna inoltre una PR mensile in bozza che registra `source-monitor-state.json`, anche quando l'esito tecnico è `no_changes`. Questo evita che il sito mostri una vecchia data di controllo soltanto perché le fonti non sono cambiate.

La PR mensile non modifica `data/site-data.json` automaticamente.

## Esiti tecnici del workflow

Gli esiti del monitor restano separati dagli stati dei singoli indicatori:

- `no_changes`: nessuna variazione sostanziale delle fonti;
- `baseline_required`: prima fotografia delle fonti;
- `changes_detected`: una fonte è stata aggiunta, rimossa, reindirizzata o un file ufficiale è cambiato;
- `attention_required`: il dataset non supera i controlli strutturali e il workflow fallisce.

Le fonti non raggiungibili vengono segnalate senza cancellare dati esistenti: alcuni portali istituzionali possono bloccare i controlli automatici.

## Flusso di aggiornamento

Il processo è volutamente separato:

**fonte → controllo → rilevazione → stato → revisione → validazione → eventuale pubblicazione**

Una variazione della fonte può produrre al massimo una segnalazione o una PR in bozza. L'aggiornamento dei valori deve poi:

1. acquisire il nuovo dato dalla fonte originale;
2. verificare che il periodo sia realmente nuovo e confrontabile;
3. conservare lo snapshot leggibile;
4. aggiornare anno, valori, serie, formula e fonte in modo coerente;
5. superare build e test;
6. essere verificato manualmente prima del merge.

## Esecuzione manuale

Aprire:

`Actions → Controllo mensile dati → Run workflow`

Lasciare attivo `Controlla anche le fonti online` per un controllo reale. Disattivarlo soltanto per verificare struttura e copertura senza traffico verso le fonti.
