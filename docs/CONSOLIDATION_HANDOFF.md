# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 4 ottobre 2026

- Main iniziale `311f71e`: #322 e #326 già mergiate/pubblicate. A3 conclusa: 123 storici, 137 confronti, 225 indicatori; le 76 opportunità costose restano escluse. #144 usa il vecchio catalogo e non va mergiata alla cieca.
- Lavoro autorizzato corrente: `fix/source-monitor-acquisition-routes`. MIMIT acquisito 3 ottobre (6/7); PNRR CSV 25 settembre validato: 78/101 conclusioni, finanziamenti invariati, 22 opere con stati ReGiS riallineati. Pannello nativo minimo e SHA-256 versionati; nessuna ricostruzione.
- Monitor: percorsi ufficiali e ruoli, diagnostica di tutti i tentativi, alternative limitate, fingerprint dei cataloghi RUNTS/INVALSI/ACI, rete separata da rilascio/acquisizione. Vecchio SISBON ritirato; build legge snapshot e non prova il live. URL aree protette corretto alla fonte. Errori non cancellano valori o ultime evidenze valide.
- Audit completo: `docs/SOURCE_MONITOR_ACQUISITION_AUDIT.md`; esiti e URL esatti: `reports/data-checks/source-routes-2026-10-04.{json,md}`. Deep live 225/138, zero errori strutturali, MIMIT/PNRR coincidenti con il candidato. INVALSI CSV HTTP 200/hash esatto. ACI 503, Eligendo 403; SISBON 2.0 landing disponibile/export non verificato; RUNTS catalogo disponibile/estrazione comunale non acquisita. Ulteriori timeout ARS e accesso negato ARPAT restano documentati, senza estendere l'acquisizione.
- Mensile automatico il 5 del mese, prossimo 5 ottobre; ultimo schedule settembre SUCCESS e PR #144 effettivamente creata. Quotidiano 4 ottobre SUCCESS; artifact, registro e selezione Stato dati verificati. PR non cancella più il run light programmato. Nessuna pubblicazione automatica di nuovi numeri.
- Evidenze operatore: ZIP ACI 2024 e CSV ARS 255 identici agli snapshot; schermate ACI/Eligendo/ARPAT disponibili. Validatore locale read-only e report SHA versionati. ACI 2025 è un candidato separato non acquisito; nuovo nome riconosciuto dal catalogo.
- UI/CSS/renderer/golden preservati: Camaiore `5aaf159870912eb49bffbd044963549bfb920150`, homepage e secondarie #313–315. Cambiano solo i dati autorizzati e i testi con date e valori PNRR collegati.
- Verifiche mirate PASS; Quick/Full e certificazione GitHub devono essere riportati nella PR con il loro esito reale. Non dichiarare la PR pronta al merge prima della conclusione dei gate. Nessun merge/deploy autorizzato.

## Lavori sospesi

- #301 A6.1 resta sospesa/Draft; nessuna chiusura o merge automatico di #302/#303/#304 e #318–#321. Questo lotto non riguarda Radar o altri interventi aperti.
