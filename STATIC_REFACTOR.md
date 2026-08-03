# Refactoring statico — area di lavoro non pubblicata

Questa branch costruisce una versione pre-renderizzata dell'Osservatorio senza
modificare o distribuire il sito pubblico attuale.

## Obiettivi

- HTML completo per home, 7 pagine comunali, 9 confronti e pagine editoriali;
- contenuti leggibili e indicizzabili anche senza JavaScript;
- un solo bundle JavaScript ordinario, senza concatenazione runtime dei file
  `00.txt`–`06.txt`, `Blob` o `import()` dinamico;
- immagini e font locali;
- canonical URL, JSON-LD e `sitemap.xml`;
- test automatici per contenuti senza JavaScript, grafici, ordinate, sticky
  header, immagini e collegamenti fondamentali.

## Comandi locali

```bash
python scripts/build_static_safe.py
python scripts/test_static.py
```

L'output viene scritto in `dist/`, che non viene pubblicato. Il workflow della
branch carica soltanto un artefatto privato di GitHub Actions e non contiene
alcun job `deploy-pages`.

## Strategia di migrazione

Durante questa prima fase l'applicazione esistente viene eseguita in un browser
headless **solo in fase di build**, così da preservare fedelmente il markup e la
grafica. Il risultato completo viene salvato nell'HTML. L'interattività resta
attiva tramite `assets/app-bundle.js`, creato in fase di build concatenando i
sette moduli sorgente in un unico file cacheabile.

Il passaggio successivo, sempre fuori produzione, sarà separare la sola logica
interattiva dal rendering e rimuovere progressivamente il re-rendering lato
client.
