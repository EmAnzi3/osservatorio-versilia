# A7 — ordine numerico descrittivo dei sette Comuni

Incremento A7.5.3 dopo #466: il profilo opzionale `ranking`, già verificato nel
trasporto sperimentale, viene scelto esplicitamente dalla build pubblica.
La matrice del candidato precedente identifica 3.336 coppie vista/operazione
`rank` dichiarate ma non materializzate nel prodotto generale: è il divario
affrontato, non un inventario manuale di indicatori o domande. A6 resta DONE;
A7 resta IN_PROGRESS. Nessun cambiamento a dati, adapter, golden o navigazione.

## Selezione e significato

Tema, indicatore, vista e operazioni vengono dalle dichiarazioni canoniche.
`rank` seleziona tutti e sette i Comuni al riferimento predefinito nativo della
vista. Non seleziona categorie ATECO fra loro, anni arbitrari o sottoinsiemi;
non aggiunge `allowPartial`. I tre profili predefiniti del builder restano
invariati. Il costo dell'aggiunta si misura sul catalogo completo, separatamente
dalle 3.727 prove numeriche indipendenti A6.

Prima dell'esecuzione il controllo spiega ambito e direzione: dal valore maggiore
al minore. Il selettore del singolo Comune è nascosto e disabilitato per questa
operazione. La direzione non viene invertita secondo una polarità editoriale.
Un valore più alto non implica una criticità, merito amministrativo o un effetto
causale; non vengono prodotti punteggi, classifiche politiche o raccomandazioni.

## Presentazione originale

Ordine e posizioni provengono da `result.ranking`, senza ordinamento o calcolo
dei ranghi nel browser. Le posizioni a pari merito sono conservate: per esempio
1, 1, 3. I pari merito dipendono dalla precisione originale, non da valori
arrotondati per la grafica. Ogni riga conserva valore, unità, periodo, fonte e
definizione della corrispondente osservazione. Il payload originale resta
immutato e ispezionabile.

Il grafico, quando consentito dalle guardie esistenti di omogeneità e valori
non negativi, segue l'ordine originale con colore neutro e scala da zero.
Valori negativi restano nella tabella senza grafico sostitutivo. La tabella
scorre orizzontalmente su mobile senza allargare la pagina.

Un rifiuto originale non produce posizioni o grafici, nemmeno dopo il consenso
alla lettura delle osservazioni conservate. Dati mancanti e non applicabili
restano distinti da zero. Copertura incompleta, selezioni vietate e limiti di
materializzazione conservano i rispettivi messaggi. Modificare la selezione
revoca risultati e consenso; una risposta tardiva non ripristina il vecchio ordine.

La UI verifica corrispondenza fra righe di risultato e osservazioni prima di
mostrarle. La catena d'integrità, i budget, la cache per release, il confezionamento
atomico e il blocco senza fallback restano quelli già approvati.

## Verifiche

Il gate generale del trasporto comprende richieste/risposte identiche al motore,
ordine di righe e barre, posizioni native, periodi, pari merito e rifiuti in due
viewport. Verifica anche il cambio di operazione durante un caricamento e le
guardie precedenti di consenso, guasti, recupero e worker offline.
La matrice deriva il perimetro dai blocchi della medesima build, con ambito
`all_seven_towns_native_descriptive_order`; la ricevuta UI è versione 5.

Prima della revisione: misura completa, matrice, preview e browser desktop/mobile,
Quick e Full locali ordinari, CI Quick→Full effettivo e A3 sullo stesso albero.
Le attestazioni finali e i log sono nella PR; nessuna pubblicazione è implicita.
Ulteriori dimensioni/operazioni, associazioni, riuso ed esportazioni rimangono
passi successivi. Dossier editoriali e Radar restano separati.
