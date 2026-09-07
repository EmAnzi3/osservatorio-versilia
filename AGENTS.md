# Osservatorio Versilia — regole operative per agenti

Queste regole valgono per qualunque agente o sessione che modifica il repository.

## Flusso obbligatorio

1. Non fare push diretto su `main`. Lavora sempre su un branch dedicato e passa da pull request.
2. Per modifiche tecniche **non visibili nell'interfaccia** (CI, test, manutenzione) la PR può essere aperta direttamente **Ready**: il flusso canonico deve eseguire `quick` e poi `full` nello stesso run. Per modifiche UI, rendering o interazioni mantieni invece la PR in **draft** finché preview e verifiche browser locali non sono concluse.
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

- `data/site-data.json` resta la fonte canonica del catalogo: indicatori, appartenenza ai temi e `detailRoute` si derivano da lì e non vanno ricopiati in manifest paralleli.
- `ci/content-contract.json` dichiara le **regole** dell'architettura pubblica: famiglie di pagine, storage ammessi, eccezioni di shell e risoluzione delle visualizzazioni. Una nuova famiglia strutturale richiede l'aggiornamento esplicito del contratto, non una scorciatoia nel builder.
- `ci/workflow-contract.json` è l'inventario canonico dei workflow Actions e dei check di ingresso. Un nuovo workflow, un workflow ritirato o una modifica ai check `quick`/`full` deve aggiornare il contratto nello stesso commit.
- `ci/build-materialization-contract.json` dichiara l'unico perimetro di sorgenti che la build pubblica può modificare temporaneamente. Il wrapper di build deve ripristinare byte per byte il checkout e rimuovere eventuali flag Git `assume-unchanged`; una nuova mutazione richiede un aggiornamento esplicito del contratto.
- `scripts/test_site_consistency.py` applica i contratti dichiarativi prima delle verifiche di shell, metadata, route e link. Non aggirarlo o indebolirlo per far passare una modifica.
- Le modifiche UI devono mantenere header/footer, ricerca, Stato dati, colori tematici, tooltip e selettori coerenti con il resto del sito.
- Testi e controlli non devono uscire dai rispettivi contenitori, né su desktop né su mobile.
- Le modifiche funzionali devono essere verificate nel browser locale quando interessano interazioni o rendering.

## Preflight

- `--quick`: contratto architetturale e sorgente, catalogo/dati, sintassi, build, materializzazione delle pagine speciali e coerenza strutturale. Non esegue la regressione browser completa, ma la build prerender richiede Chromium.
- `--full`: esegue `quick` e aggiunge regressioni statiche estese e browser.
- `--full --skip-quick`: riservato alla CI quando il job `quick` è già verde e il job `full` prepara un `dist/` coerente per i controlli full-only.

Non introdurre nuovi test o workflow release-specifici se lo stesso contratto può essere espresso nel preflight generale o in un gate con `paths` strettamente pertinenti. Non duplicare inventari di indicatori o route che possono essere derivati dalle fonti canoniche.
