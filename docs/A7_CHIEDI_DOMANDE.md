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

## Verifica

`scripts/test_chiedi_domande.py --dist dist` (nei controlli sul sito costruito)
esegue con Node l'interprete e l'indice pubblicati sulle domande di
`ci/chiedi-domande.json`, con attese scritte a mano (anche domande fuori
catalogo), poi controlla nel browser a 1440 e 390 px risposta, valore dal
motore e assenza di scorrimento orizzontale.

## Passaggio a un LLM

Un livello LLM dovrà produrre la stessa `selection` (o l'identificativo di un
incrocio rivisto), validata contro `ask-index.mjs` prima di essere applicata;
i numeri restano del motore. L'interprete statico resta il ripiego quando
l'LLM non è disponibile o si raggiunge il tetto di spesa. Servono un backend
leggero (per esempio un Worker) con chiave API, tetto di spesa e limite di
domande per visitatore, e una nota sulla privacy.
