# A7 — tendenza della serie nativa nell’esploratore

Incremento candidato A7.5.3 dopo #471; A6 DONE, A7 IN_PROGRESS. Il profilo
`trends`, già verificato separatamente, è una scelta esplicita della build
pubblica candidata. I tre default del generatore non cambiano. Nessun adapter,
dato, policy, golden o posizione nella navigazione viene modificato.

## Una selezione, una serie nativa

Tema, indicatore, vista e operazioni derivano dal catalogo e dalle dichiarazioni
A6. «Tendenza della serie» usa un solo Comune e l’intera serie nativa scelta dal
motore, senza periodi, metodo o consenso aggiunti alla richiesta. Nessuna finestra
arbitraria, eliminazione di null o selezione dei soli anni favorevoli. Una serie
consultabile non garantisce un trend ammissibile; il rifiuto resta consultabile
con i motivi e le eventuali osservazioni originali, senza pendenza sostitutiva.
Il consenso alla copertura incompleta non trasforma il rifiuto in risultato.
I motivi noti hanno anche una spiegazione italiana: storico non esposto nella
vista, osservazioni insufficienti o continuità ordinaria/OSL non attestata.
Le traduzioni sono etichette di presentazione, non nuove autorizzazioni; i
codici originali e il payload completo restano integri.

La sintesi mostra la pendenza originale A6, la sua unità per anno, gli estremi
osservati e il numero `n` di osservazioni utilizzate. Il dettaglio del metodo
conserva la precisione originale, tutti i valori dell’asse temporale effettivo
e la formula. OLS è spiegato come retta dei minimi quadrati: la pendenza non è
una variazione identica in ogni anno, un test di significatività o una previsione.
Gli intervalli mancanti restano tali; gli anni non sono sostituiti da posizioni
equidistanti nel calcolo. Nessuna regressione o estrapolazione nel browser.

Una misura percentuale produce punti percentuali per anno, distinti dalla
percentuale relativa. Le altre unità provengono dal risultato originale;
`decimal/year` è presentato come unità della misura per anno, con il nome e la
definizione della misura conservati. Il segno non è una valutazione di merito,
una prova causale o una raccomandazione. Nessun ordinamento delle pendenze.

Tabella e fonti restano quelle originali, paginate a venti osservazioni. Quando
le guardie già approvate consentono un grafico, le barre mostrano le osservazioni
con i rispettivi periodi, non una retta stimata o valori previsti. Valori negativi
restano nella tabella senza grafico sostitutivo. Cambiare selezione revoca
risultato e consenso; una risposta tardiva non ripristina la vecchia tendenza.

## Integrità e copertura

Ricevuta UI versione 6. La matrice riconosce le capacità preparate soltanto se
il grafo verificato contiene sia quel profilo sia questa versione di interfaccia.
Trasporto, controlli preparati e pubblicazione restano prove distinte. I riferimenti
del profilo opzionale restano `one_town_full_native_series_ols_no_forecast`.

La build prepara in staging l’intero grafo e lo verifica prima della sostituzione
atomica del sito generato. Pagina, descrittore, modulo con ancora indipendente e
blocchi restano nel medesimo artifact Pages. Artifact mancanti, incompatibili o
corrotti bloccano la consultazione; nessun fallback di release o numero sostitutivo.
Il recupero ritenta la stessa release. `A7_ATOMIC_RUNTIME_PACKAGE.md` e
`A7_PUBLIC_EXPLORER_INTEGRATION.md` conservano i contratti di pubblicazione.

## Verifiche richieste

Il gate esistente del trasporto include la resa UI del trend: parità completa di
richiesta/risposta, pendenze positive e negative, unità, n, asse temporale, periodi,
paginazione delle serie lunghe, rifiuti e risposta tardiva dopo cambio Comune.
Restano attivi i controlli precedenti di consenso, caricamento selettivo, assenza
di storage o servizi esterni, guasti e recupero, worker offline senza fallback,
controlli bianchi e assenza di overflow desktop/mobile.

Misura combinata completa e matrice derivata devono essere riconciliate con il
candidato finale. I conteggi di trasporto non sono nuove prove numeriche
indipendenti. Preview e browser prima della revisione; Quick e Full locali
ordinari, CI Quick→Full effettivo e A3 sullo stesso albero prima del merge.
Attestazioni finali nella PR. Nessun merge o deploy dell’assistente.

## Misura sul catalogo congelato

Il candidato combinato comprende 225 indicatori, 3.359 viste e 50.523 richieste:
28.422 computed e 22.101 rifiuti originali. Totale 127.146.205 byte gzip,
+2.273.349 rispetto al runtime pubblico #471; non caricati integralmente
all’apertura. Manifest 102.138 byte; massimo shard invariato a 68.838 byte gzip
/ 2.338.129 decompressi. Il pacchetto dedicato della #471 non era questo costo
incrementale: la misura combinata condivide i dettagli già necessari.

I 12.420 riferimenti a shard dei profili precedenti sono identici, così come i
202 shard trend attestati dalla #471. Le 1.414 selezioni trend conservano 724
computed e 690 rifiuti; tutte le risposte computed rispettano le guardie di
presentazione. Queste sono prove di trasporto e forma, non verifiche browser di
ogni selezione né nuove aspettative numeriche indipendenti. Il catalogo ha SHA256
`1416209ca86f27b4eaeede51e59a90edd0b24167f75c60e5157df4583678d710`.
Misure e produttori vanno riconciliati con la build finale attestata nella PR.
