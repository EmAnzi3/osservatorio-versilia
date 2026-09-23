# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A5 — Design System 2.0
- **Step attivo:** A5.4 — pagina pilota
- **Stato:** IN_PROGRESS — pilot visuale implementato, in attesa di CI e verifica manuale desktop/mobile
- **Main verificato:** `b99a19a55ab34fd842f7fa20f417c407097e92c5` (merge #272)
- **A4:** DONE
- **A5.1–A5.3:** mergiati
- **Pagina pilota:** `confronta/demografia/`
- **Branch corrente:** `feat/a5-design-system-pilot`
- **PR corrente:** #273 — `A5: pilot Design System 2.0 on Demografia` — Draft
- **Modifiche visive al prodotto:** sì, limitate alla pagina confronto Demografia

## A5.4 — pilot DS2

Il pilot applica in modo isolato i ruoli definiti in A5.2–A5.3:
- canvas neutro;
- surface primaria bianca;
- surface secondaria chiara;
- testo primary/secondary/tertiary con contrasto maggiore;
- bordi ed elevazione semplificati;
- accento tematico Demografia coerente;
- tab, metadati, note e controlli con dimensioni minime più leggibili.

Il CSS introduce anche token `--ds-theme-*` per tutti gli 11 temi. Fuori dal pilot questi token non vengono ancora consumati e non producono modifiche visive.

## Vincoli

1. Dati, contenuti, ordine, tooltip, unità e interazioni devono restare invariati.
2. Le baseline A4 non vanno aggiornate prima della verifica visiva.
3. Il mismatch visuale atteso deve essere limitato alle superfici intenzionalmente modificate.
4. La PR resta Draft fino ad approvazione desktop/mobile.
5. Nessuna estensione A5.5 prima della chiusura del pilot.

## Verifica visiva richiesta

Desktop:
- separazione chiara fra canvas e pannelli;
- gerarchia hero → selettori → dato → metadati;
- leggibilità di sezioni, tab, note e fonti;
- uso dell'accento terracotta senza dominare il grafico;
- nessuna variazione nei dati o nell'ordine delle righe.

Mobile:
- nessun overflow della pagina;
- navigazione temi confinata al proprio scroll orizzontale;
- tab con target adeguati e testo leggibile;
- pannello dati e definizione senza testi a ridosso dei bordi;
- link ai Comuni in colonna singola.

## Prossima azione esatta

1. Aprire PR Draft per A5.4.
2. Richiedere Quick e Full sul final head.
3. Verificare che eventuali failure Full siano esclusivamente visual-regression intenzionali.
4. Scaricare l'artifact visuale e verificare desktop/mobile.
5. Solo dopo approvazione esplicita aggiornare le baseline A4 e portare la PR Ready.
6. Merge solo dopo ulteriore approvazione esplicita del proprietario.

## A5.4 — revisione visuale warm editorial

La prima skin CSS-only è stata respinta in review perché troppo distante dal riferimento scelto. Il pilot corrente modifica anche la composizione della sola route `confronta/demografia/`, mantenendo invariati gli hook funzionali e i dati.

Direzione corrente:
- hero fotografico editoriale con asset canonico Versilia e testo sovrapposto;
- ribbon temi compatta subito sotto;
- testata Demografia a tre colonne;
- workspace 270px + area grafico dominante;
- solo il gruppo indicatore attivo è visivamente espanso;
- `#compare-definition` spostato sotto il grafico accanto al richiamo metodologia;
- schede comuni in griglia con stemmi reali;
- footer navy con markup e link reali;
- nessun cambio a dataset, tooltip, download, serie storiche o destinazioni link.

Il riferimento approvato è lo screenshot warm-editorial fornito dal proprietario nella review di A5.4. La PR resta Draft e le baseline A4 non vanno aggiornate finché il nuovo draft navigabile non viene approvato.
