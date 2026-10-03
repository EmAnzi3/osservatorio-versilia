# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — integrazione A3, 3 ottobre 2026

- Branch `feat/a3-integration-approved-ui`: integra il lotto finale #321, il parent aggiornato #302 e `main` `ac5e14ecb37b00e8b734a9bce0acf61c2983e677`. Nessuna modifica a main, merge di PR o pubblicazione eseguita.
- Il proprietario chiede di passare all'implementazione preservando l'ultima UI. La raccolta è conclusa: nessun ulteriore storico o benchmark direttamente pronto nel perimetro concordato; ACI escluso dall'ultima estensione. Non riaprire ricerche, GIS, ricostruzioni o calcoli territoriali onerosi.
- A3 già implementata nel contratto pubblico: 123/123 indicatori con storico e 137/137 benchmark, zero gap. 119 storici nella lettura base e quattro aggiuntivi nelle componenti selezionabili. I 76 confronti residui restano opportunità documentate, non attività necessarie per chiudere questa fase.
- Certificazione #321 sul head `721582ceaba50145c89572fa66f0679661343f9b`: run `37149580997` Quick, Full, preview e contratti SUCCESS, log verificati. Pubblicazione 123/123 e 137/137, 40 baseline A4, Lavoro/Istruzione e Percorsi PASS. Questo run certifica il branch stacked, non la nuova combinazione con main.
- Cinque storici Istat: occupazione/disoccupazione/attività Totale 15+ (2019, 2021–2024); diploma/terziario Totale 25–49 (2018–2024); diploma Totale 25–64 (1991, 2001, 2011, 2024). Attività = 100 − inattività. Il 2024 corrente è preservato; fasce distinte, fonti native e discontinuità censuaria dichiarate, nessun aggregato storico da percentuali senza denominatori.

## UI da preservare

- #280 A5 è già mergiata, merge `a98b89995e01cd12f2ab8422a0a6ed6aa81b5578`; il precedente blocco documentale su quella PR era obsoleto.
- Ultima UI in main: #313, merge `741430fd751da7fb65129eafaa9cc7952fd70ec2`, e correzione Atlante #315, merge `ac5e14ecb37b00e8b734a9bce0acf61c2983e677`.
- Tutti gli asset visuali sono byte-identici a questo main; l'unico asset differente è `assets/ux-history.js`, con i collegamenti funzionali alle nuove serie già verificati nella #321. Nessun redesign, nessun cambio a CSS, hero, toolbar Atlante, palette, renderer A5 o golden/baseline.
- La build pubblica deve continuare a usare `scripts/build_public_site.py`, inclusa l'applicazione finale di `apply_secondary_pages_ui.py` alle sole sette route approvate. Non usare il solo prerender del preflight come prova della UI pubblicata.
- Schede comunali/tematiche e golden A5 restano protetti; route speciali Meteo/clima, Atlante e Affluenza mantengono le proprie eccezioni.

## Correzione integrazione monitor

La PR #322 integra la combinazione completa, primo head e4e9dd37469da8e7f56c836ff90452e2d98fb01c. I monitor light/deep hanno fallito sul replay turistico per import anticipato di requests; causa riprodotta localmente con Python -S. La dipendenza HTTP viene caricata soltanto nelle funzioni di acquisizione. Test di replay nativo delle quattro serie senza requests PASS; materializzazione completa del monitor con sola standard library PASS: 225 indicatori, 221 inline, 4 esterni, 69 profili. Nessun dato/UI cambiato. Verificare i nuovi run dopo la correzione; i verdi del primo head non certificano il nuovo head.

## Prossima azione esatta

1. Controlli locali conclusi: pubblicazione 123/123 e 137/137, browser nuove serie 44/44, baseline A4 40/40, 105 intestazioni su 25 pagine, coerenza 250 pagine, integrità del sito pubblico completo PASS. Confronto diretto con main delle sette UI finali: 14/14 banner desktop/mobile PASS, zero differenze pixel significative e stessa geometria/stile. Tutti i 225 indicatori, 1.547 valori comunali e aggregati correnti sono identici alla build main. Quick eseguito: primo output locale incompleto della finalizzazione brand/PWA, rimaterializzato prima dei controlli finali; rimane il limite Percorsi/Leaflet CDN. Quick completo e Full locale non dichiarati verdi; nessuna guardia aggirata.
2. Aprire una PR DRAFT d'integrazione verso main e verificare i gate sul suo head; i precedenti verdi non certificano automaticamente questo branch.
3. Prima di Ready/merge resta richiesto il Full locale di AGENTS.md. Il limite locale Leaflet CDN/Percorsi è documentato e non deve essere aggirato né dichiarato verde.
4. Le PR #302/#303/#304 e i lotti #318–#321 restano OPEN/DRAFT; nessun merge o deploy senza autorizzazione esplicita del proprietario. La #303 conserva opportunità non incluse nel lotto certificato e non va inglobata automaticamente.
5. Solo dopo integrazione approvata: riallineare la #301 A6.1 a main e rivalidare il catalogo effettivo dei 225 indicatori. La #301 resta sospesa/DRAFT; nessuna UI A6 avviata.
