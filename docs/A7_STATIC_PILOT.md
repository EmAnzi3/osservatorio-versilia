# A7 — prima prova tecnica statica

Esperimento circoscritto sui dossier Massarosa lavoro e infanzia/scuola. Baseline integrata #429: main `4c4a03f7ad47a4261cf4c65de674dfbde0e5fba3`, tree `f450b7852e573b68014623dbb2b818ad0f70cc2b`, build/deploy `38566370077` e controllo live `38568149233` PASS il 14 ottobre 2026. A6 resta chiusa; questa prova non modifica adapter, catalogo, dati, 35 letture, due riepiloghi, interfacce o golden master.

## Che cosa dimostra

Il Python A6 originale esegue le richieste in build. Un modulo JavaScript legge successivamente risposte precalcolate come file statici, senza eseguire Python nel browser, acquisire dati online o usare un modello linguistico. Le frasi numeriche sono template controllati, ancorati ai valori A6: ogni frase dichiara periodo, unità e puntatore alla risposta; le osservazioni conservano universo, metodo, fonte, snapshot e puntatori originali. I risultati aggregati citano le componenti e la formula A6. Non si combinano automaticamente periodi o popolazioni differenti.

Le sei domande provengono dai piani centrale e secondari di `lavoro` e `infanzia` in `ci/territorial-dossier-program.json`; i loro 13 casi numerici provengono da `ci/semantic-verified-questions.json`. Tre rifiuti pertinenti mostrano storico non disponibile, anno educativo non convertibile in anno solare e copertura parziale non autorizzata. Il piccolo `scope.json` contiene esclusivamente riferimenti a dossier e casi, senza un nuovo inventario di indicatori, valori o definizioni.

Le sei domande restano **parzialmente supportate**, anche quando le componenti sono calcolabili. La prova non determina quanti posti nido servano, non misura gli effetti dell'offerta educativa sull'occupazione, non descrive la congiuntura del 2026 e non identifica territori certificati come comparabili. Le lacune e i confini editoriali si derivano dai piani canonici; i due dossier leggibili rimangono gli approfondimenti di riferimento.

## Richieste e risposte

Il lettore accetta esattamente una selezione: `question` (testo di una domanda curata), `questionId` oppure `caseId`. Può ricevere `dossierId` e `approvedPartial` booleano. Non accetta valori, metriche, annualità, operazioni o richieste A6 arbitrarie iniettate dal chiamante. I selettori effettivi si trovano nelle query canoniche incluse nel bundle: sono visibili nella risposta, senza default nascosti aggiunti dal lettore.

```javascript
import {loadPilot} from './reader.mjs';
// bundleText e trustedRelease provengono dalla stessa release verificata.
const pilot = await loadPilot(bundleText, trustedRelease);
pilot.resolve({questionId: 'lavoro-1'});
pilot.resolve({questionId: 'infanzia-2'}); // needs_confirmation, nessun componente numerico
pilot.resolve({questionId: 'infanzia-2', approvedPartial: true});
pilot.resolve({caseId: 'child_year_conversion'}); // resolved + not_computable A6
```

| Esito del lettore | Significato |
|---|---|
| `resolved` | Selezione riconosciuta; classificazione della domanda e status A6 delle componenti restano separati |
| `needs_clarification` | Testo non appartenente al repertorio esatto o selezione ambigua; offre domande verificate, senza numeri |
| `needs_confirmation` | Il piano include una richiesta con copertura parziale; consenso esplicito prima di mostrare i risultati |
| `out_of_scope` | ID, dossier o combinazione non disponibili nella prova |
| `invalid_request` | Tipo, selezione, consenso o campi non ammessi |

La normalizzazione riguarda soltanto maiuscole, spazi, apostrofi e punteggiatura finale. Non è un interprete generale: «Come va il lavoro?» o una domanda causale non vengono trasformate silenziosamente in un indicatore. La scelta del piano non autorizza classifiche politiche, previsioni o raccomandazioni automatiche.

`components` conserva query e risposta A6, comprese reasons, warnings, null, zero, esclusioni e campi condizionali. Un rifiuto prima di `assess()` rimane privo di coverage/formula/policy; un rifiuto successivo li può includere. `facts` è vuoto nei rifiuti. Le sole normalizzazioni dei percorsi riguardano il catalogo verificato: il percorso assoluto della macchina diventa `sha256:<hash>`, senza cambiare snapshot fonte, puntatori, hash o valori.

## Integrità, cache e sicurezza

`release.json` identifica bytes e SHA256 del bundle, catalogo, motore, casi, programma, scope, builder e lettore. `loadPilot` verifica il digest dei bytes e l'identità della release prima di risolvere una domanda. Il chiamante deve usare una release **fidata e fissata dalla build**, non un manifest fornito dalla domanda o generato da un interprete. SHA256 garantisce integrità rispetto a quel riferimento, non autenticità di un manifest ricevuto da una fonte non fidata. Anche il modulo JavaScript deve provenire dalla release/hosting fidati.

La chiave di cache contiene il digest del bundle, selezione e consenso. Ogni modifica di input, policy o adapter cambia gli hash contenuti nella risposta A6 e quindi il bundle. Ogni modifica dei generatori o dei piani invalida anch'essa la chiave. Risposte e descrizioni vengono copiate: una mutazione del chiamante non altera le successive letture o il riferimento di release.

Il modulo non accede a rete, DOM o storage e non interpreta HTML. I suoi testi sono dati; una futura UI dovrà inserirli come testo, mai tramite `innerHTML`. Non contiene credenziali e non memorizza o trasmette domande. La prova non introduce endpoint, modelli, infrastrutture esterne o una famiglia di pagine pubbliche.

## Riproduzione e misure

```bash
python scripts/build_a7_static_pilot.py --catalog dist/data/site-data.json --output-dir /tmp/a7-pilot
python scripts/test_a7_static_pilot.py --catalog dist/data/site-data.json --output-dir /tmp/a7-verification
```

Il primo comando produce bundle, release, misure di build e `answers.md`, una resa testuale delle sei risposte per la revisione, con fonti e limiti. Il secondo riproduce due build identiche, controlla aspettative indipendenti A6 e snapshot congelati, risposte integrali, puntatori dei numeri e limiti dei piani; esegue input ostili nel lettore Node e lo stesso modulo nel browser Chromium. Controlla null/zero, copertura INVALSI 4/7, consenso, rifiuti prima/dopo valutazione, mutazioni del chiamante e rifiuto di bundle alterati o release non coerenti. Il gate è registrato nel contratto workflow ed eseguito nel Quick **dopo** la materializzazione del catalogo effettivo; i gate approvati rimangono obbligatori e invariati.

`verification.json` misura durata di build, bytes JSON/gzip, caricamento del modulo/bundle, mediana e p95 di 100 risoluzioni in Node, heap del processo e caricamento in Chromium locale. Sono misure di laboratorio su quel toolchain, non prestazioni di rete o mobile e non una nuova soglia Lighthouse. Un browser reale conferma la parità della risposta col modulo Node; non è una verifica della futura esperienza conversazionale.

## Decisione successiva

La prova rende verificabile una strada statica per domande curate. Non sceglie l'architettura definitiva di Chiedi alla Versilia: l'interpretazione libera del testo rimane da progettare, mentre chiarimenti, fonti, rifiuti e determinismo sono già esercitati su questo perimetro. Prima di introdurre una UI occorre valutare con il proprietario l'utilità delle sei domande e il modo di presentare consenso e limiti; prima di scegliere servizi o modelli esterni occorre dimostrare quali casi prioritari non siano sostenibili con il modello statico.

Gli altri dossier restano nel programma approvato: non diventano completi per effetto di questa prova. Non sono richieste nuove acquisizioni per ampliare artificialmente il repertorio. A7.1–A7.4 hanno una prima verifica circoscritta, non una certificazione completa; A7.5 e la Definition of Done complessiva rimangono aperte.
