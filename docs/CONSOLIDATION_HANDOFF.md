# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline verificata il 19 ottobre 2026

- Main `fed2a7c73f3ba480a153eea4748e7b874b2e8c28`: #448 integrata e pubblicata. Deploy `39171231146` e live `39172500248` attestano quella baseline, non la #451.
- #451 ancora OPEN/Ready/mergiabile; head `fd196e6681a75be3d4620d5155618a9f8568ebb4`, base uguale a main, tree `8d30ba9dff733f38e1cde7a97901a47a5e819574`. Quick→Full effettivo `39178021176` e A3 `39178021175` SUCCESS; build/deploy skipped. Attestazione locale completa nella PR e nel pacchetto `A7_PR451_fd196e6_evidenze.zip`. Nessuna ripetizione automatica dei gate su quel candidato.
- #443 editoriale lavoro/redditi ancora OPEN/Ready, head `89127cac42bfc1a0877695fff60e0b9103e01e86`, con conflitti; resta separata e richiede revisione del proprietario. Radar e social fuori perimetro.
- A6 DONE: 225/225 adapter, 3.727 casi indipendenti PASS, 35 letture e due riepiloghi; Atlante 20.325 unità locali native, 40 golden e Camaiore congelata. Nessuna riapertura o modifica di dati/adapter/golden.
- Dossier #430 conservati: 17 ambiti, 45 sotto-dossier, 51 piani, sei specifiche e due dimostrazioni; non 51 dossier completi. Piloti pubblici ed esploratore generale restano distinti.

## Incremento corrente — A7 IN_PROGRESS

PR #453, branch `feature/a7-accessibility-audit`, derivato dalla head verificata #451;
nessuna modifica alla #451. Dipende da quella PR, non ne implica il merge.

`audit_a7_accessibility.py` deriva acquisizione A3 strict e tutte le dichiarazioni
vista/operazione A6, esegue le aspettative originali via workbench e, con
`--runtime`, verifica artefatti effettivi e parità di ogni risposta con A6.
Senza runtime dichiara `not_inspected`. Percorsi A3 locali e puntatori osservati
forniscono prove limitate: **companion/route/formule e copertura completa delle
nove dimensioni non sono ancora collegati**. `acquired_access_not_proven` non è
fonte assente né prova di accesso completo. Metodo `docs/A7_ACCESSIBILITY_AUDIT.md`.

Incremento di trasporto: profilo `ranking` soltanto su richiesta esplicita del
builder, sette Comuni/riferimento nativo, risposte `rank` originali. I tre profili
predefiniti rimangono. Nessuna nuova UI, voce menu, modello, backend o acquisizione.
Contratto del rollout atomico/ancora/errori definito nel metodo; publisher pubblico
ancora non implementato. Nessuno step A7 dichiarato DONE.

## Gate e prossima azione

Il nuovo candidato richiede Quick locale ordinario → Full locale ordinario e
CI Quick→Full/A3 sulla stessa head/albero. I verdi #451 non attestano le modifiche
correnti. P2 #453 riprodotto: mutazione del piano durante un fetch può separare
risposta e piano/digest. Correzione: snapshot privato prima del primo `await`,
validato e usato per selezione, output e hash; regressione con fetch sospeso.
Il Quick del primo candidato non attesta la correzione; il suo Full è stato
interrotto per non certificare una head superata. Anche il controllo dei puntatori
è corretto dopo un test negativo: normalizza solo la riga comunale, conservando
indici di categoria e chiavi degli anni. I gate intermedi non attestano il nuovo
albero. Test pertinenti e misura/audit
effettivo da completare prima del nuovo push;
registrare ricevute e limiti nella nuova PR. Nessun merge o deploy autorizzato.

Seguono: collegamento semantico riproducibile degli acquisiti A3 non provati,
periodi/selezioni oltre i profili nativi, ulteriori operazioni soltanto motivate
dalla matrice; poi integrazione guidata, grafici, citazioni/export e dossier/PDF.
Non allargare la navigazione pubblica fino a prodotto sufficientemente sviluppato.
