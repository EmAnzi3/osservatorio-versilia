# A7 — preview navigabile dei dossier Massarosa

Preview isolata integrata dal proprietario nella #433 (`4b972e4e8197064522bc3a058df2dcc70d8b0a1b`, tree `0ebe0e074e0a8effdd9faef1922019e37a4420e4`), con un incremento circoscritto per domanda scritta, chiarimento ed esportazione verificabile. A6 resta DONE e A7 IN_PROGRESS. È una preview isolata per revisione: nessuna route, shell, pagina pubblica, navigazione globale o golden master cambia.

## Esperienza da verificare

Il lettore sceglie lavoro oppure infanzia/scuola e una delle domande canoniche. La risposta mostra subito la classificazione parziale, il confine della risposta, ciò che non si può concludere e i dati mancanti per decidere. Seguono i fatti numerici già prodotti da A6, con periodi, universi, definizioni, metodi, fonti, snapshot e puntatori. Richiesta e risposta originali restano consultabili per componente. Il dossier completo è raggiungibile con un link al commit congelato.

La selezione usa gli ID restituiti dal lettore della #432: nessun nuovo repertorio, numero o indicatore è copiato nel codice UI. Non ci sono input liberi, interpretazione linguistica o raccomandazioni automatiche. Le sei domande restano parzialmente supportate. La vista non determina posti nido necessari, qualità complessiva dei servizi o trasformazioni congiunturali del 2026.

Il consenso precede l'esposizione di qualsiasi componente di un piano parziale. Annullare o cambiare domanda/ambito rimuove risultati e consenso: non si eredita l'autorizzazione della domanda precedente. Il lettore originale conserva i rifiuti anche dopo il consenso. Un bundle mancante, corrotto o non corrispondente alla release blocca la preview, senza mostrare numeri.

## Domanda scritta e chiarimento guidato

Il lettore può scrivere una domanda oppure scegliere dal repertorio. Il testo passa al modulo originale della #432: la corrispondenza riguarda soltanto domande canoniche, con la normalizzazione già approvata di maiuscole, spazi e punteggiatura. Una richiesta ampia, causale, di un altro territorio o di un periodo non previsto non viene trasformata in una query. La preview mostra le domande disponibili, senza numeri, e richiede una scelta esplicita; l'alternativa selezionata è una nuova domanda verificata, non una risposta alla richiesta iniziale.

Il campo è limitato a 2.048 caratteri e non viene memorizzato o trasmesso. Modificare il testo, cambiare selezione o annullare revoca risultati, consenso e download della risposta precedente. Il consenso delle componenti parziali resta necessario anche quando si arriva dal testo o da un suggerimento. La prova non introduce un classificatore semantico, un interprete libero o una conversazione.

## Esportazione verificabile

Dopo una risposta risolta è disponibile **Scarica la risposta verificabile (JSON)**. Il download conserva il piano canonico, la selezione esatta, il consenso, la release, il commit delle fonti e tutte le componenti A6 originali, comprese osservazioni, valori null/zero, puntatori, limiti, rifiuti e precisione. Non include testi ambigui o richieste precedenti. Conserva la modalità di selezione del lettore (testo canonico oppure ID), così il replay riproduce anche l’identità di cache; nel file il testo riconosciuto è quello canonico, non la digitazione originale. Il risultato è un file locale generato soltanto su azione del lettore: nessun endpoint, storage della domanda o invio a terzi.

Il JSON è un'evidenza portabile, non una nuova fonte canonica né un'autenticazione del file dopo la modifica da parte di terzi. Hash e commit consentono di risalire agli input congelati; la disponibilità corrente delle fonti resta distinta. Una risposta scaricata conserva i periodi di origine e non diventa un aggiornamento del dato.

## Build e distribuzione di revisione

```bash
python scripts/build_a7_dossier_preview.py --catalog dist/data/site-data.json --output-dir /tmp/a7-preview --repository-commit 4b972e4e8197064522bc3a058df2dcc70d8b0a1b
python -m http.server 8765 --directory /tmp/a7-preview
```

Aprire `http://localhost:8765/`. Il parametro commit deve essere disponibile come oggetto Git locale e identificare gli snapshot e dossier della build verificata. Il generatore risolve il commit e verifica il programma canonico, i dossier byte per byte e gli snapshot tramite gli hash dichiarati; per i sorgenti INVALSI ricostruiti verifica parti e SHA256 dei byte JSON decodificati. Commit assenti, percorsi mancanti, contenuti diversi o hash incoerenti interrompono la build prima di scrivere output. In clone shallow occorre rendere disponibile il commit, senza fallback al semplice controllo del formato. Per questo lotto i riferimenti sono immutati dalla #432. La disponibilità corrente online non è attestata dal controllo locale; distribuire solo riferimenti già verificati su GitHub. `release.mjs` contiene il manifest fissato dalla build, non accettato dalla domanda o dalla URL; SHA256 verifica integrità rispetto a quel riferimento fidato, non autenticità di un hosting compromesso.

I file generati costituiscono una cartella portabile di preview: index, CSS, modulo UI, lettore originale, release fissata, bundle derivato e answers.md. Non entrano nella build pubblica né nel catalogo canonico. Servire via HTTP locale o HTTPS: i moduli e WebCrypto non costituiscono una promessa di funzionamento con il doppio clic file://. Nessuna credenziale, dipendenza CDN o richiesta a servizi esterni. I link GitHub si aprono soltanto su azione del lettore; non sono acquisizioni live o verifica di disponibilità corrente delle fonti.

## Verifiche e limiti

Il gate A7 esistente esegue anche la preview reale, domande scritte normalizzate, chiarimenti senza numeri per richieste ambigue/causali/fuori scope, nuova selezione e consenso, reset del download dopo modifica, ed esportazione JSON riconciliata con le risposte A6 originali: sei piani in due viewport, identità dei fatti e dei limiti, consenso/annullamento/cambio selezione, dettagli originali, link congelati, assenza di overflow, errori browser, richieste esterne e memorizzazione delle domande. Fixture isolate verificano commit inesistenti o estranei, hash di programma/snapshot incoerenti, dossier mancanti, blocco su bundle alterato e resa di testo simile a HTML senza esecuzione. Nessun dato o sorgente del candidato viene alterato per queste prove. I report e screenshot sono output QA, non nuovi golden.

Il browser verifica etichette, tastiera e focus dei controlli nativi; questo non certifica una revisione completa con tecnologie assistive. Le soglie Lighthouse e i 40 golden pubblici restano invariati. La preview non aggiunge una famiglia al contratto delle route perché non viene pubblicata; una futura integrazione deve dichiararla esplicitamente e preservare shell, ricerca, Stato dati e regole tematiche.

Prima dell'integrazione pubblica il proprietario valuta leggibilità, pertinenza delle sei domande e chiarezza dei dati parziali. L'architettura definitiva e l'eventuale interpretazione libera restano aperte. Questa preview non conclude A7.5 o la Definition of Done di A7.
