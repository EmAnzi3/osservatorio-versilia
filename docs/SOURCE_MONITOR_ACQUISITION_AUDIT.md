# Aggiornamenti e percorsi fonte — 4 ottobre 2026

## Stato recuperato

Main iniziale `311f71e2e09b50700e6a10496e943c4471c55f6d` include la #326 (`5a862fb`). Nessuna PR/branch successiva recuperata per questo lotto; carburanti ancora al 28 agosto, PNRR al CSV 11 agosto. L'handoff precedente descriveva ancora #326 come non mergiata. Nuovo branch isolato `fix/source-monitor-acquisition-routes`; nessun merge o deploy autorizzato.

## Acquisizioni validate

- MIMIT: CSV prezzi del 3 ottobre 2026 + anagrafica ufficiale; mediana self per Comune e carburante, 6/7 (Stazzema senza impianti), 63 impianti nella fotografia. Riutilizzati updater e history esistenti; vecchi punti preservati, nessuna interpolazione.
- PNRR: CSV Regione Toscana elaborato il 25 settembre, 45.364 record esaminati, 101 progetti comunali deduplicati. SHA-256 `bee81f4fd82272700bf8a9caec36e4481fd0b08a9f7cb7fddf873e059a5b512f`. Finanziamenti invariati (€36.683.107,64); macrofase ReGiS 5 da 74 a 78 (77,2277%). Camaiore 11/16, Forte dei Marmi 10/15, Massarosa 10/11, Pietrasanta 10/12, Seravezza 9/12, Stazzema 10/11, Viareggio 18/24. Le 22 opere conservano CUP e importi; stati di dettaglio ora 18 collaudi completati, 3 avviati, 1 lavori in esecuzione. I test ricalcolano l'audit dal pannello nativo minimo congelato, separando la macrofase dal collaudo.

## Matrice dei percorsi

Gli URL censiti e le alternative complete sono in `data/source-registry.json:sourceProbePolicies`, insieme al metodo di verifica e all'acquisizione. Questo documento spiega il percorso senza introdurre un secondo catalogo di indicatori.

| Fonte | URL censito / percorso | Acquisizione effettiva | Dato pubblicato | Verifica nuovo rilascio |
|---|---|---|---|---|
| SISBON | Vecchio export APEX ARPAT; nuovo servizio `https://sisbon.regione.toscana.it/` | `materialize_ambiente_acqua_v124.py:fetch_sisbon` legge **solo** `ambiente-acqua-v124-sisbon.json.gz.b64`, 152 procedimenti; non usa un harvester live | riferimento dichiarato 29 agosto 2026 | Vecchio servizio ritirato secondo ARPAT; trovare l'export pubblico 2.0 e confrontare codici e stato iter. La data dichiarata dello snapshot non prova un'acquisizione live in quella data |
| RUNTS | Ricerca enti; `https://servizi.lavoro.gov.it/runts/it-it/Lista-enti` | Snapshot manuale in `site-data.json:thirdSector`; raw/harvester non rinvenuto nel repository | 2025 | Il deep legge le date delle righe **Enti iscritti**; scaricare l'elenco ufficiale con il controllo della pagina e riconciliare sedi comunali e denominatore |
| INVALSI dispersione/eccellenza | Pagina dedicata + CSV ufficiale `download/1024/.../14204/report_generale_unito_dispersione_e_eccellenti_agg_2025.csv` | CSV originario → snapshot gzip/base64 `invalsi-v138-b64` → materializzatore; hash sorgente congelato `d6e18894…` | a.s. 2024/2025, pagina aggiornata 3 dicembre 2025 | Deep legge i nomi delle risorse CSV del dataset; un nuovo nome genera un candidato da validare; il confronto SHA avviene durante l’acquisizione, non verde automatico |
| ACI (2 indicatori) | Pagina Autoritratto; ZIP ufficiale `https://aci.gov.it/app/uploads/2025/06/Autoritratto-2024-Parco-Veicolare.zip` | Workbook e pannello nativo versionati in `a3-aci-vehicle-benchmark-2024.json`; validatore ACI riconcilia 7/7 | parco 2024; denominatore demografico dichiarato nei metadati | Catalogo annualità + download. Un vecchio ZIP raggiungibile non prova che sia l'ultima annualità |
| Affluenza | `https://elezionistorico.interno.gov.it/eligendo/opendata.php` | Archivio ufficiale versionato `data/affluenza/archive-v2-*.b64` e materializzatore dedicato | consultazioni fino al riferimento 2026 | Catalogo per consultazione e download pertinente; conservare 403 e tentativi del client come diagnostica, non dichiarare sito offline |
| Aree naturali protette | Nuova pagina `https://www.regione.toscana.it/sistema-aree-naturali-protette` | WFS Regione → snapshot GIS `territorio-v137-official.json` tramite `generate_territorio_v137_snapshot.py` | snapshot v1.37 verificato 12 settembre 2026 | Confronto layer WFS e hash; la pagina informativa non certifica l'aggiornamento delle geometrie. Nessuna rielaborazione GIS in questo lotto |
| PRC | `https://www.regione.toscana.it/piano-regionale-cave` | Geometrie ufficiali e clipping congelati in `attivita-estrattive-v128.json` | PRC vigente · variante 2025 | Confrontare atto/variante, download e geometrie; non sostituire il riferimento normativo con un mese generico |
| RTCave | `https://cave.regione.toscana.it/api/v1/cave_public` | Snapshot endpoint anonimo `attivita-estrattive-v128.json` | 2 settembre 2026 | Confrontare ID/contenuto dei record; mese generico non confrontabile con data snapshot |
| Reticolo | Pagina regionale; ZIP `https://www.regione.toscana.it/documents/d/guest/infrastruttura_rev25-zip` | Snapshot GIS versionato e confini Istat; build offline | DCRT 24/2025 · confini 1 gennaio 2026 | Confrontare atto/layer, mantenendo distinta la data dei confini; niente confronto artificiale tra anno e riferimento composto |

## Automazione e persistenza

- Mensile: `.github/workflows/monthly-data-refresh.yml`, cron `17 5 5 * *` (UTC); prossimo previsto 5 ottobre 2026. Ultimo **schedule** `33957168433`, 5 settembre, SUCCESS. I run PR sono offline e non certificano la rete. La #326 ha validato il catalogo effettivo 225/138; la versione corrente entra nel prossimo schedule dopo il merge.
- Quotidiano: `.github/workflows/source-monitor-light.yml`, cron `41 5 * * *`; schedule `37198147708`, 4 ottobre, SUCCESS. La separazione dei gruppi di concorrenza impedisce a una PR di cancellare un run programmato.
- Deep: artifact JSON/Markdown/next-state, retention 90 giorni; registro annuale delle esecuzioni programmate; PR diagnostica solo per cambiamenti sostanziali/baseline. Light: artifact 30 giorni. Gli esiti manuali persistono negli artifact, senza scrivere il registro.
- Pages/Radar riusano il selettore introdotto nella #326: soli artifact live riusciti su main, catalogo/digest/periodi compatibili. Nessuna importazione di valori o codice. Run falliti, offline, PR o riferiti a un catalogo vecchio non rimpiazzano lo stato pubblico valido. Deploy main `37211885670` SUCCESS dopo #326.
- Timeout, accesso negato, errore server, path assente e path ritirato sono distinti nel report. Ogni tentativo registra URL, metodo HTTP/client, status, redirect ed errore. Un solo client alternativo per endpoint; massimo due alternative ufficiali. Il deep legge marcatori pertinenti del catalogo entro 1 MiB; la raggiungibilità resta separata da rilascio e acquisizione. Hash troncati non certificano contenuti completi.
- Il monitor non scrive valori. Mantiene ultimo successo e fingerprint completi per confronti successivi, senza attribuire successo corrente a uno snapshot o a un vecchio hash. Una landing alternativa non viene confrontata byte per byte con il vecchio export.

## Verifiche manuali residue

1. **ACI**: https://aci.gov.it/attivita-e-progetti/studi-e-ricerche/autoritratto/ — HTTP 503 con urllib e curl. Anche lo ZIP 2024 alternativo è 503 nel runtime. Verificare la pagina annualità e fornire un eventuale nuovo download ufficiale.
2. **Eligendo**: https://elezionistorico.interno.gov.it/eligendo/opendata.php — HTTP 403 con HEAD, GET limitata e curl. Accesso negato a questi client; la causa anti-bot non è certificata dal solo codice HTTP.
3. **SISBON 2.0**: https://sisbon.regione.toscana.it/ — landing HTTP 200, **export e acquisizione non verificati**. ARPAT conferma il ritiro di 1.0: https://www.arpat.toscana.it/banca-dati/banca-dati-dei-siti-interessati-da-processo-di-bonifica/. Servono percorso pubblico del download e controllo del tracciato; nessuna ricostruzione GIS.
4. **RUNTS**: https://servizi.lavoro.gov.it/runts/it-it/Lista-enti — HTTP 200 e rilascio Enti iscritti 4 ottobre 2026. La pagina utilizza controlli di download: l'estrazione comunale non è acquisita in questo lotto. Fonte disponibile, dato pubblicato conservato.

Il vecchio URL `https://www.regione.toscana.it/-/il-sistema-delle-aree-naturali-protette` era 404; il nuovo percorso è 200. Non resta un link da riparare nel generatore. PRC/reticolo/WFS richiedono confronto dei riferimenti sorgente prima di dichiarare nuovi dati: nessun valore è cambiato per aver raggiunto una pagina.

## Accesso operatore e importazione controllata

Il 4 ottobre il proprietario ha fornito schermate ACI/Eligendo/ARPAT e ZIP ACI 2024/ARS 255. Entrambi i file coincidono con le sorgenti già acquisite (SHA archivio/workbook ACI e CSV ARS); non sono nuovi valori. Gli errori del monitor restano veri per quel tentativo, senza equipararli alla disponibilità generale. La pagina ACI espone inoltre il candidato 2025, non acquisito, con nome `Autoritratto2025_Parco_veicolare.zip`; regex e fallback ufficiali sono stati aggiornati.

`scripts/verify_manual_source_download.py` accetta un archivio ricevuto dall’operatore e produce soltanto un JSON di riconciliazione: URL atteso, metodo, dimensioni, SHA, indicatore/periodo e confronto allo snapshot. Non modifica catalogo, baseline o esiti live. Rifiuta indicatore ARS errato, schemi inattesi, CRC non validi, archivi ambigui e dimensioni eccessive. Un contenuto diverso resta candidato da validare; una coincidenza non certifica che il rilascio sia l’ultimo.

Il monitor resta a 20 secondi per evitare scansioni bloccanti; gli harvester ARS già prevedono 120 secondi per generare/scaricare il ZIP. Va mantenuto questo doppio controllo: disponibilità rapida e acquisizione separata, con prova persistente del file. Preferire download ufficiali precisi ai titoli delle pagine e mantenere l’importazione operatore come fallback verificabile quando la rete CI non riesce. Le evidenze di questa sessione sono in `reports/data-checks/operator-evidence-2026-10-04.json`.

ARS 255: prova live aggiuntiva con il GET del harvester (timeout 120 s) riuscita in 33,52 secondi, CSV di 4.769.433 byte con SHA identico allo snapshot. Il monitor deep usa ora 90 secondi solo sui sette export ARS osservati; light mantiene 20 secondi. Questo corregge la verifica, senza sostituire valori e senza generalizzare il successo del 255 agli altri sei export. Il report deep iniziale conserva i timeout realmente riscontrati prima della correzione.

Conferma sul monitor corretto: probe deep ARS 255 HTTP 200, timeout configurato 90 s, hash completo `zip-members`, nessun troncamento. Esito salvato nella baseline; gli altri sei timeout ARS restano da riverificare dal deep mensile. Il controllo light non cancella la prova deep acquisita. Nessun valore aggiornato per ARS, poiché il CSV coincide con la sorgente pubblicata.
