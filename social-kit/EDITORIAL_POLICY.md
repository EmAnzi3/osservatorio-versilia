# Carta editoriale social

## Scopo

Il Social Kit trasforma i dati pubblicati su Osservatorio Versilia in contenuti leggibili e verificabili. Non attribuisce meriti, colpe o cause che i dati non dimostrano e non produce comunicazione politica di parte.

La formula editoriale è:

> Un dato. La fonte. Il confronto. La tua opinione.

## Regole non negoziabili

1. Ogni contenuto riporta indicatore, unità di misura, anno o periodo, perimetro territoriale e fonte.
2. I numeri sono letti da `data/site-data.json`: non vengono ricopiati nel manifest editoriale.
3. I Comuni sono mostrati in ordine alfabetico, salvo che il contenuto dichiari esplicitamente un diverso ordinamento necessario alla lettura.
4. Una differenza numerica non diventa automaticamente un giudizio di qualità.
5. Non si inferiscono relazioni causali da una correlazione o da un semplice confronto territoriale.
6. I confronti con Toscana e Italia sono ammessi solo quando anno, unità e definizione sono compatibili e il benchmark è documentato nel dataset.
7. Il testo distingue dato ufficiale, elaborazione dell’Osservatorio e stima.
8. Ogni post chiude con una domanda aperta e non orientata.
9. Ogni grafica dispone di testo alternativo e file di provenienza leggibile da una macchina.
10. Una correzione aggiorna grafica, didascalia e provenienza, mantenendo traccia della versione dei dati.
11. Chiavi tecniche, slug e numerazioni interne restano nella provenienza e non compaiono nella grafica.
12. La domanda ai lettori è un elemento editoriale visibile, non una nota a piè di pagina.

## Lessico

Preferire formulazioni descrittive:

- “il valore è superiore/inferiore di…”;
- “tra il 2019 e il 2026 il dato passa da… a…”;
- “il dato misura…, non consente da solo di stabilire…”;
- “quali fattori pensi siano rilevanti?”

Evitare parole che trasformano il dato in una pagella o in un titolo allarmistico:

- record, boom, crollo, allarme;
- virtuoso, peggiore, maglia nera;
- successo, fallimento, promozione, bocciatura.

Questi termini possono comparire solo in una citazione attribuita e necessaria, mai nella voce dell’Osservatorio.

## Confronti e grafici

- Le barre partono da zero.
- Le serie storiche mostrano tutto l’intervallo disponibile usato nel titolo.
- Le scale troncate sono vietate nei confronti a barre.
- Colore e dimensione non devono suggerire un giudizio assente nei dati.
- Il colore identifica il tema; non identifica “buono” o “cattivo”.
- Se un indicatore descrive accesso, presenza o utilizzo di un servizio, il testo non lo presenta come esito o qualità del servizio.

## Struttura della didascalia

1. **Dato:** una frase descrittiva.
2. **Come leggerlo:** definizione o limite essenziale.
3. **Fonte:** ente, dataset, anno e collegamento alla scheda dell’indicatore.
4. **Domanda:** invito aperto a commentare, senza suggerire una risposta.

## Cadenza editoriale

1. Il budget editoriale ordinario è di **massimo due post a settimana**, normalmente organizzati sugli slot del martedì e del venerdì.
2. In una settimana senza ricorrenze o blackout, i due slot sono entrambi ordinari e appartengono a **temi diversi**.
3. La rotazione assegna un tema a ogni slot ordinario di calendario.
4. Una ricorrenza `anchor` realmente pertinente **occupa uno dei due posti settimanali** e sostituisce lo slot ordinario più vicino alla propria data di pubblicazione.
5. Una ricorrenza `conditional` entra nel piano soltanto dopo promozione editoriale esplicita; se promossa, sostituisce uno slot con la stessa regola delle `anchor`.
6. Lo slot ordinario sostituito non viene recuperato automaticamente: il tema previsto per quello slot cede il posto alla ricorrenza. Questo evita di comprimere tre o quattro contenuti nella stessa settimana e calibra la rotazione sulle occasioni editoriali reali.
7. Le date registrate come `blackout` non producono un post ordinario e non vengono recuperate automaticamente.
8. Il planner non può superare il budget di due contenuti. Se le ricorrenze selezionate sono più di due nella stessa settimana, si ferma e richiede una decisione editoriale esplicita.

## Ricorrenze nazionali e internazionali

Il calendario delle ricorrenze non serve a produrre post celebrativi generici: serve a intercettare momenti in cui un dato dell’Osservatorio può essere particolarmente utile.

1. Una ricorrenza classificata `anchor` entra nel piano salvo indisponibilità o inadeguatezza del dato e può uscire nel giorno esatto quando questo rende il contenuto più pertinente.
2. Una ricorrenza `conditional` diventa un post soltanto se esiste un indicatore realmente pertinente, con definizione e granularità adeguate, e dopo una decisione editoriale esplicita.
3. La ricorrenza non cambia il significato dell’indicatore: un gap occupazionale non diventa un pay gap, una fascia di reddito non diventa una misura di povertà, un dato comunale non diventa un dato di frazione, lago o area naturale.
4. Se il collegamento è indiretto ma utile, il limite deve essere dichiarato esplicitamente nella grafica o nella didascalia.
5. Se più ricorrenze competono nella stessa settimana, il totale resta due contenuti. Non si forza un terzo post e non si forza un contenuto debole.
6. Prima della produzione si ricontrollano data, denominazione, eventuale tema annuale e fonte ufficiale della ricorrenza.
7. Il contenuto mantiene sempre la struttura editoriale dell’Osservatorio: dato, fonte, confronto, limite di lettura e domanda aperta.
8. La cadenza è definita in `config/editorial-cadence.json`; le ricorrenze in `config/editorial-observances-2026-2027.json`; la rotazione ordinaria in `config/editorial-rotation.json`.
9. Il calendario operativo mantiene volutamente settimane con una sola uscita quando uno slot cade in un blackout editoriale, come Natale o Capodanno.

## Controllo prima della pubblicazione

- [ ] La cifra nella grafica coincide con il dataset corrente.
- [ ] Anno, unità, fonte e perimetro sono visibili.
- [ ] La domanda finale è neutrale.
- [ ] La descrizione non introduce cause non dimostrate.
- [ ] Il testo alternativo descrive contenuto e valori principali.
- [ ] Il link punta alla pagina dell’indicatore o del tema.
- [ ] Il carosello 1080×1350 è leggibile su smartphone e nessun testo esce dai box.
- [ ] I colori del contenuto corrispondono al tema canonico del sito.
- [ ] Se il post nasce da una ricorrenza, data e fonte ufficiale sono state ricontrollate e il collegamento con l’indicatore è esplicito.
- [ ] Il totale della settimana non supera due uscite.
