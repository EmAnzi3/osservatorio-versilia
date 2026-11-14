# Chiedi — domande in italiano (interprete statico)

Primo passo verso il chatbot dell'Osservatorio, deciso da Ema il 14 novembre 2026:
interprete statico nel browser, con la possibilità di aggiungere in seguito un
modello linguistico (LLM) sopra lo stesso contratto.

## Come funziona

1. In build, `scripts/a7_ask_index.py` scrive `ask-index.mjs` nel grafo
   dell'esploratore: per ogni indicatore del runtime pubblicato etichetta, nome
   breve, termini di ricerca, sezione, tema, i dettagli con nome leggibile (età,
   sesso, voci) e **solo le letture effettivamente consultabili**. Nessun valore.
   Contiene anche gli identificativi degli incroci rivisti.
2. Nel browser `ask.mjs` normalizza la domanda, riconosce Comuni, lettura
   (valore, confronto, ordine, serie, tendenza, variazione, Toscana/Italia,
   Versilia, fuori scala), dettaglio (età, sesso) e indicatore (punteggio sulle
   parole di etichetta e termini, sinonimi d'uso comune, concetti frequenti).
   Senza almeno una parola specifica dell'indicatore, o con meno di metà delle
   parole della domanda coperte, risponde che il catalogo non ha quel dato.
3. Il risultato è una **selezione** dell'esploratore esistente
   (`indicatore`, `dettaglio`, `domanda`, `comune`, `riferimento`), applicata
   come link condivisibile `#esplora&…`; per gli incroci l'evento
   `chiedi-association` con l'identificativo del passo rivisto. I numeri, i
   rifiuti, le fonti e i limiti restano quelli del motore A6 e
   dell'esploratore.
4. La frase di risposta (`summarize`) è costruita solo dall'evidenza del
   motore mostrata sotto, e solo quando la selezione dell'evidenza coincide con
   quella chiesta.

La risposta dice sempre come è stata capita la domanda, propone altri
indicatori vicini e chiede il Comune quando la lettura riguarda un Comune solo.

## Conversazione, suggeritore e fonti (seconda versione, 14 novembre 2026)

- **Domande di seguito.** L'ultima lettura riuscita resta come contesto
  («Stai parlando di: …», con il pulsante «Nuovo argomento»). Una domanda
  senza indicatore proprio ma con un Comune, una lettura, un riferimento o un
  attacco come «e…», «invece…» continua la precedente: «e Camaiore?», «e nel
  tempo?», «e rispetto alla Toscana?», «e le donne?» (il dettaglio conserva le
  età già scelte), «e fra i Comuni?». Con un nuovo indicatore e un attacco di
  seguito («e il reddito?») si tengono Comune e lettura. Una domanda con più di
  una parola nuova non coperta è trattata come domanda nuova, così «Che tempo
  farà domani a Viareggio?» resta fuori catalogo anche a metà conversazione.
- **Suggeritore.** Mentre si scrive compaiono fino a sei domande complete
  (schema combobox ARIA: frecce, Invio, Esc). Completa l'ultima parola sul
  vocabolario del catalogo, riconosce un Comune scritto a metà e propone le
  letture disponibili per gli indicatori più vicini; senza Comune offre
  «… a …» per sceglierlo. Ogni proposta è passata da `interpret` prima di
  essere mostrata e scartata se non verrebbe capita come annunciato. A casella
  vuota, durante una conversazione, propone i seguiti.
- **Parole e refusi.** Espressioni riscritte prima dell'analisi («non
  lavorano», «seconde case», «costo dei rifiuti», «escono per lavorare»…),
  nuovi sinonimi e concetti, correzione dei refusi sulle parole del catalogo
  (distanza 1, 2 per parole lunghe) e sui nomi dei Comuni («viaregio»). Se il
  primo indicatore non copre la domanda si prova fra i successivi più vicini.
- **Fonte.** Il link «Fonte» della risposta, delle tabelle di una misura e
  delle coppie degli incroci porta alla pagina dell'indicatore sull'Osservatorio
  (`indicatori/<slug>/`), che riporta origine, aggiornamento e metodo. Il link
  originale resta nel CSV e nell'evidenza. Per i pochi indicatori senza pagina
  propria (clima, atlante delle attività, affluenza) resta il link originale.

## Verifica

`scripts/test_chiedi_domande.py --dist dist` (nei controlli sul sito costruito)
esegue con Node l'interprete e l'indice pubblicati sulle 200 domande di
`ci/chiedi-domande.json`, con attese scritte a mano e riviste (anche domande
fuori catalogo, refusi e conversazioni con `after`), verifica che ogni proposta
del suggeritore sia capita come annunciato e che le pagine «Fonte» esistano, poi
controlla nel browser a 1440 e 390 px suggeritore da tastiera, risposta, valore
dal motore, domanda di seguito, link alla fonte, margine interno di almeno 8 px
dei testi nei box (anche nella vista «Due variabili») e assenza di scorrimento
orizzontale.

## Passaggio a un LLM

Un livello LLM dovrà produrre la stessa `selection` (o l'identificativo di un
incrocio rivisto), validata contro `ask-index.mjs` prima di essere applicata;
i numeri restano del motore. L'interprete statico resta il ripiego quando
l'LLM non è disponibile o si raggiunge il tetto di spesa. Servono un backend
leggero (per esempio un Worker) con chiave API, tetto di spesa e limite di
domande per visitatore, e una nota sulla privacy.
