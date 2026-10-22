# A7 — variazioni fra estremi della serie nativa

Incremento A7.5.3; A6 DONE, A7 IN_PROGRESS. Nessun adapter, dato, golden o
politica di calcolabilità modificati. Nessun nuovo modello o servizio.

## Perimetro derivato e selezione temporale

Il profilo opzionale `changes` deriva `absolute_change`, `relative_change` e
`percentage_points` dalle dichiarazioni delle viste del catalogo canonico.
Per ogni Comune legge la serie originale A6 e conserva il primo e l’ultimo
periodo nell’ordine restituito, senza dedurre date dalle etichette. Non salta
estremi null/non disponibili, non cerca la coppia più favorevole e non inventa
continuità metodologica. I periodi espliciti vengono passati al motore originale:
una serie consultabile non autorizza automaticamente la variazione.

Quando non emergono due periodi distinti, la richiesta conserva il riferimento
nativo senza periodi inventati e ne presenta il rifiuto. Le richieste sono
finite: un Comune, una vista e una coppia per operazione dichiarata. Periodi
arbitrari, inversioni, sottoinsiemi geografici e `allowPartial` non sono
materializzati e non vengono riscritti. I tre profili predefiniti restano
invariati; la build pubblica sceglie esplicitamente anche `changes`.

L’interfaccia mostra la coppia prima dell’esecuzione e la aggiorna al cambio
Comune. Il risultato espone valore iniziale, finale e differenza originale,
con unità, fonti, formula e periodi. Differenza in punti percentuali e variazione
percentuale relativa restano distinte. Non si annualizza, non si calcola nel
browser e il segno non è un giudizio di miglioramento né un effetto di politica.
I rifiuti conservano motivi e osservazioni senza differenze sostitutive.

## Integrità, misura e verifiche

`changePeriodsByTown` è un campo derivato del dettaglio, non un inventario
canonico. Il verificatore del pacchetto lo confronta con nuove richieste al
motore sulla stessa versione/catalogo; le ricette vincolano esattamente gli
shard alle coppie. Il lettore cerca solo richieste identiche. La ricevuta
interfaccia versione 4 distingue trasporto e controlli preparati nella matrice.
Confezionamento atomico e ancora indipendente restano quelli di
`A7_ATOMIC_RUNTIME_PACKAGE.md`; nessuna nuova visibilità nella navigazione.

La matrice si rigenera con `audit_a7_accessibility.py --runtime ... --site ...`.
Le misure di richieste/byte non sono nuove aspettative numeriche indipendenti.
La suite A6 originale resta separata e invariata. I gate esistenti verificano
parità, due build byte-identiche, estremi null conservati, periodi fuori perimetro,
consenso, risposte tardive e riepiloghi desktop/mobile con payload nativo.
Quick e Full locali ordinari e CI Quick→Full/A3 sullo stesso candidato sono
obbligatori; evidenze finali nella PR, senza trasferire verdi della #464.

## Ricognizione sul catalogo congelato

Il profilo deriva 3.780 richieste: 1.836 computed e 1.944 rifiuti originali.
Variazioni assolute: 213 viste / 87 indicatori, 850 computed su 1.491;
relative: 211 / 85, 813 su 1.477; punti percentuali: 116 / 23, 173 su 812.
I rifiuti includono dimensioni storiche non esposte, discontinuità censuarie,
perimetro OSL Massarosa non attestato e 23 basi iniziali zero per le relative.
Sono richieste di trasporto, non nuove prove numeriche indipendenti.

La misura combinata preliminare comprende 45.773 richieste (26.750 computed /
19.023 rifiuti), 225 indicatori / 3.359 viste, 105.527.018 byte gzip:
+1.292.741 rispetto alla #464. Massimo shard invariato a 68.838 byte gzip /
2.338.129 byte decompressi. Da riconfermare nei gate del candidato definitivo.
