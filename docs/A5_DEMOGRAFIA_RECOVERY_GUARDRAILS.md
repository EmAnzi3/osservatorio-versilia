# A5 Demografia — Recovery guardrails

Baseline immutabile: `802ea5708a139ec60f7e62e991d1b3becb712386`.

## Scope autorizzato

Il recovery può modificare esclusivamente:

1. visibilità e resa del riferimento **Media Versilia**;
2. tonalità dei selettori compositi coerenti con la tematica;
3. presenza contestuale del box **Mobilità dei laureati italiani 25–39 anni**;
4. posizione e resa di **Scheda indicatore / CSV / PDF** nel grafico, mantenendo le icone file;
5. compattazione di **Metodo e comparabilità** e **Scala di lettura**;
6. titolo Demografia non coperto da elementi decorativi;
7. fisarmoniche dei gruppi indicatori: un solo controllo, funzionante;
8. grafico corrente non compresso;
9. rimozione dell'area morta nella colonna sinistra;
10. coerenza tra primo render e rerender;
11. card comunali con immagine + valore corrente, ordine alfabetico e spaziatura uniforme.

## Fuori scope / bloccato

Salvo autorizzazione esplicita del proprietario, non cambiare:

- hero e copy approvati;
- palette generale A5;
- header, navigazione temi e footer;
- font e gerarchia tipografica generale;
- struttura delle pagine non Demografia;
- dataset, metriche, benchmark o fonti;
- `assets/ux-history.js`;
- `assets/visual-grammar.js`;
- baseline A4;
- semantica, tooltip e logica dei grafici non direttamente necessaria ai punti sopra.

## File di lavoro

- `assets/a5-demografia-review.css` — unico layer visuale editabile per il recovery.
- `assets/a5-demografia-review.js` — unico adattatore comportamentale specifico per Demografia.
- `assets/fidelity.js` — può contenere soltanto il loader dei due file sopra.

Le modifiche specifiche del recovery non devono essere sparse in altri file.

## Regola sulle modifiche manuali del proprietario

Se il proprietario modifica direttamente `assets/a5-demografia-review.css` o `assets/a5-demografia-review.js`:

- quelle modifiche diventano immediatamente fonte di verità;
- prima di ogni nuovo intervento va riletto il branch LIVE;
- non sovrascrivere né riformattare modifiche manuali non richieste;
- eventuali conflitti vanno segnalati prima di scrivere altro codice.

## Regola di consegna

Prima di produrre un artifact:

1. Quick verde;
2. diff contro `802ea570...`;
3. nessun file fuori scope;
4. verifica visuale dei soli punti della review;
5. PR Draft; baseline A4 invariate.
