# Audit frontend qualitativo · v1.13

Data: 16 agosto 2026

## Obiettivo

Questo audit nasce dal controllo della gerarchia del riferimento Versilia, della grammatica cromatica dei confronti e della crescita dei file CSS/JS. Non modifica dati, formule, fonti o conteggio degli indicatori.

## Riferimento Versilia

Il codice distingue correttamente fra:

- **riferimento/aggregato Versilia**, calcolato sui sette Comuni secondo la natura dell'indicatore;
- **benchmark esterno Toscana/Italia**, mostrato solo quando esiste una comparabilità metodologicamente omogenea.

Per gli indicatori compositi il riferimento Versilia non è soppresso: la UI usa logiche dedicate per distribuzioni, stock, mobilità, OMI e misure di sicurezza. L'assenza del pannello `benchmarkMarkup()` nei compositi riguarda il confronto esterno, non l'aggregato dei sette Comuni.

Intervento v1.13 qualitativo:

- nelle pagine tema il valore territoriale nell'`indicator-definition` viene promosso visivamente;
- nelle schede comunali lo scostamento resta la headline, ma il valore Versilia non è più una nota tipografica marginale;
- la linea di riferimento Versilia nei confronti è resa più leggibile senza trasformarla in un'ottava serie comunale.

## Grammatica cromatica

Nel foglio base storico esiste una regola `.bar-row:nth-child(-n+2) .bar-fill` che assegna il blu alle prime due righe. La grammatica corrente dei confronti, però, trasforma le barre in dot plot e rimuove la numerazione ordinale.

Per evitare sia un significato cromatico implicito sia stati intermedi incoerenti, `visual-grammar.css` neutralizza esplicitamente quella regola: le barre residue/fallback usano il colore del tema. La selezione viene comunicata da stato, hover/focus e dimensione del segno, non dalla posizione in elenco.

Il test browser copre anche `Sicurezza stradale`, indicatore composito, e verifica:

- assenza della numerazione ordinale;
- stesso colore semantico per i sette Comuni;
- riferimento Versilia visibile;
- valore Versilia con gerarchia tipografica adeguata.

## CSS: stato reale

Il numero dei fogli CSS non corrisponde automaticamente a fogli duplicati. La build ha responsabilità separate:

- base storica: `original.css`;
- shell/statico: `static.css`, `fidelity.css`;
- grammatica dei confronti: `visual-grammar.css`;
- pagine indicatore: `indicator-pages.css`;
- storico/accordion/export: `ux-experiment.css`, `mobile-accordion-fix.css`, `export-v161.css`;
- superfici dei grafici: `chart-surfaces.css`;
- brand/PWA: `brand.css`, `pwa.css`;
- pagina speciale Meteo e clima: `meteo-clima.css`;
- Percorsi usa un proprio perimetro CSS.

Quindi non è consigliabile fondere i file in modo indiscriminato. Il debito tecnico principale è la presenza di nomi e regole storiche che non descrivono più l'ownership corrente. Il consolidamento futuro dovrebbe ridurre le sovrapposizioni per responsabilità, non il numero di file come obiettivo autonomo.

## JavaScript climatico

Esito dell'audit delle due versioni segnalate:

- `climate-ux-v3.js` **è attivo**: `fidelity.js` lo carica dinamicamente quando la pagina principale è pronta, poi carica `climate-town-benchmark.js`;
- `climate-ux-v2.js` non risulta caricato da runtime, build o workflow ed è stato rimosso come residuo;
- il marker DOM `data-ov-climate-v2` e l'id stile `ov-climate-v2-style` restano per compatibilità con la pulizia del prerender. Il nome è storico, ma non implica l'esecuzione del file v2.

Non viene effettuata una rinomina cosmetica del marker in questa PR perché coinvolgerebbe contemporaneamente runtime climatico e normalizzazione del prerender senza beneficio funzionale.

## Tipografia

La famiglia corrente resta Geist + Geist Mono. Non viene introdotto un serif: l'eventuale uso di una seconda famiglia tipografica richiede una decisione di design system e non è una correzione tecnica.

## Documentazione

Il README era rimasto a v1.12.0 / 121 indicatori. Viene riallineato alla release canonica:

- v1.13.0;
- 127 indicatori complessivi;
- 123 incorporati;
- 4 climatici esterni.

## Perimetro escluso

Questa PR non:

- cambia dati o formule;
- aggiunge indicatori;
- cambia la struttura dei temi;
- pubblica Meteo e clima come sezione definitiva;
- introduce un nuovo font;
- riscrive integralmente la cascata CSS.

L'obiettivo è consolidare la grammatica esistente con interventi piccoli, verificabili e reversibili.
