# Osservatorio Versilia — regole operative per agenti

Queste regole valgono per qualunque agente o sessione che modifica il repository.

## Flusso obbligatorio

1. Non fare push diretto su `main`. Lavora sempre su un branch dedicato e passa da pull request.
2. Durante lo sviluppo mantieni la PR in **draft**. Il check remoto `quick` deve restare verde; non usarlo per provare ipotesi.
3. Prima di qualunque push esegui localmente:

   ```bash
   python scripts/preflight.py --quick
   ```

4. Prima di considerare una PR pronta al merge esegui localmente:

   ```bash
   python scripts/preflight.py --full
   ```

5. GitHub Actions è un verificatore, non un debugger. Se una CI fallisce: leggi il log completo, riproduci localmente la causa, correggi la causa radice, riesegui il preflight pertinente e solo allora fai un nuovo push.
6. Non fare merge e non pubblicare senza approvazione esplicita del proprietario del repository.

## Contratti da preservare

- `data/site-data.json` è la fonte canonica per catalogo e `detailRoute` delle pagine speciali: non duplicare inventari di route se il dato può essere derivato da lì.
- Non aggirare o indebolire `scripts/test_site_consistency.py`, i gate di shell/route o i test browser per far passare una modifica.
- Le modifiche UI devono mantenere header/footer, ricerca, Stato dati, colori tematici, tooltip e selettori coerenti con il resto del sito.
- Testi e controlli non devono uscire dai rispettivi contenitori, né su desktop né su mobile.
- Le modifiche funzionali devono essere verificate nel browser locale quando interessano interazioni o rendering.

## Preflight

- `--quick`: contratto sorgente, catalogo/dati, sintassi, build, materializzazione delle pagine speciali e coerenza strutturale. Non esegue la regressione browser completa, ma la build prerender richiede Chromium.
- `--full`: esegue `quick` e aggiunge regressioni statiche estese e browser.
- `--full --skip-quick`: riservato alla CI quando il job `quick` è già verde e `dist/` viene ripristinato dal relativo artifact.

Non introdurre nuovi test o workflow release-specifici se lo stesso contratto può essere espresso nel preflight generale o in un gate con `paths` strettamente pertinenti.
