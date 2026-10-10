# A6 — Biblioteche pubbliche comunali

Tre carrier regionali già pubblicati diventano interrogabili: prestiti per residente, utenti attivi del prestito ogni 100 residenti e ore medie settimanali di apertura. Il motore restituisce gli indici comunali ufficiali arrotondati, con definizione, unità, periodo, fonte e puntatori agli snapshot. Nessuna nuova acquisizione o modifica dei valori pubblici.

## Perimetro e precisione

Il riferimento corrente è il 2024, con cinque Comuni numerici su sette. Massarosa ha una riga nel monitoraggio ma valori non alimentati; Stazzema è assente dal monitoraggio, non necessariamente priva di biblioteche. Entrambi restano n.d., mai zero o ultimo valore storico riportato in avanti. La doppia riga Viareggio è governata dalla selezione già congelata; nessuna somma fra reti o sedi.

I prestiti sono transazioni, non lettori unici. L’indice di impatto conserva l’unità ogni 100 residenti: non diventa percentuale di residenti deduplicati, né indice su 1.000. Gli utenti possono utilizzare più sedi e la loro residenza non è dedotta dalla localizzazione della biblioteca. Le ore sono la misura comunale ufficiale dell’orario settimanale; non indice di apertura, ore annue o somma degli orari delle sedi.

Gli indici pubblicati a due decimali restano distinti dai rapporti calcolabili dal dettaglio delle sedi. Pur contenendo prestiti/iscritti e popolazione per alcune sedi nel 2024, lo snapshot non certifica un rapporto territoriale o utenti unici tra Comuni. Nessuna ponderazione per residenti contemporanei o retro-derivazione dai valori arrotondati. Il riepilogo pubblico è una media aritmetica dei cinque valori disponibili, non un aggregato ufficiale Versilia.

## Serie, copertura e benchmark

Prestiti/utenti: osservazioni 1998–2024 con lacune. Ore: soltanto 2022–2024; il campo precedente non è semanticamente omogeneo e non viene sostituito con l’indice di apertura. Le query temporali conservano tutti gli anni congelati, inclusi null; i puntatori al catalogo descrivono esplicitamente l’assenza del periodo nella serie sparsa. Il puntatore allo snapshot identifica direttamente ciascuna cella, anche null. Le esclusioni richiedono `allowPartial=true`, secondo i gate esistenti. Una serie può mostrare un solo valore, senza certificare variazioni o trend; serie interamente mancanti restano non calcolabili. Il 2020 pandemico è un contesto esplicito, non una correzione automatica.

Ammessi confronto, ordinamento numerico, consultazione della serie e scostamento dal benchmark Toscana 2024 ufficiale. Il benchmark regionale è distinto dalla media dei cinque Comuni locali; Italia e benchmark storico non acquisiti. Lo scostamento per un Comune senza valore non diventa calcolabile accettando esclusioni parziali. Rifiutati pooling, variazioni, trend, punti percentuali, anomalie e coppie non congiuntamente revisionate, in entrambe le posizioni del selector. Nessuna classifica di qualità del servizio o conclusione causale.

## Evidenze e verifica

Snapshot `regione-toscana-cultura-biblioteche-2024.json` e `a3-regione-toscana-libraries-benchmark-2024.json` congelati: SHA dei byte e fingerprint degli input nella cache verificati ad ogni accesso. 21 celle correnti, tre benchmark e 57 celle storiche di Massarosa con trascrizioni fisse indipendenti; replay separato di 399 celle, incluse null, non una nuova acquisizione dei CSV. Mutazioni avversarie su identità, periodo, unità, componenti, riepilogo, benchmark, cache, imputazione e riporto storico.

Le 58 nuove domande si aggiungono al corpus governato; tre carichi descrittivi alla baseline prestazioni, senza soglie di latenza. Report derivati in `reports/a6-library/`. Audit sul catalogo materializzato: 184/225 adapter effettivi, 133/181 sorgente, 41 residui. Corpus 1.111/1.111 PASS (485 consultazioni/calcoli, 626 rifiuti attesi); 58 collegamenti tipizzati, 29 companion e 87 carichi descrittivi. Catalogo, storici e benchmark pubblici invariati. A6.4 parziale, A6.5–A6.6 aperte, A7 non avviata. Quick locale prima del push; Full locale canonico in clone freddo distinto e Quick→Full CI sul medesimo albero prima della prontezza al merge. Merge e pubblicazione restano manuali del proprietario.
