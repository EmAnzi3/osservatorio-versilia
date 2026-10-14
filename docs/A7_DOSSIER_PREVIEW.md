# A7 — preview navigabile dei dossier Massarosa

Primo passo di presentazione dopo il merge del proprietario della #432 (`ae1249784c6e3ba25a99da52cc35780049a88380`, tree `77d24913d6603c63461abd8f080442fa16beb55f`). A6 resta DONE e A7 IN_PROGRESS. È una preview isolata per revisione: nessuna route, shell, pagina pubblica, navigazione globale o golden master cambia.

## Esperienza da verificare

Il lettore sceglie lavoro oppure infanzia/scuola e una delle domande canoniche. La risposta mostra subito la classificazione parziale, il confine della risposta, ciò che non si può concludere e i dati mancanti per decidere. Seguono i fatti numerici già prodotti da A6, con periodi, universi, definizioni, metodi, fonti, snapshot e puntatori. Richiesta e risposta originali restano consultabili per componente. Il dossier completo è raggiungibile con un link al commit congelato.

La selezione usa gli ID restituiti dal lettore della #432: nessun nuovo repertorio, numero o indicatore è copiato nel codice UI. Non ci sono input liberi, interpretazione linguistica o raccomandazioni automatiche. Le sei domande restano parzialmente supportate. La vista non determina posti nido necessari, qualità complessiva dei servizi o trasformazioni congiunturali del 2026.

Il consenso precede l'esposizione di qualsiasi componente di un piano parziale. Annullare o cambiare domanda/ambito rimuove risultati e consenso: non si eredita l'autorizzazione della domanda precedente. Il lettore originale conserva i rifiuti anche dopo il consenso. Un bundle mancante, corrotto o non corrispondente alla release blocca la preview, senza mostrare numeri.

## Build e distribuzione di revisione

```bash
python scripts/build_a7_dossier_preview.py --catalog dist/data/site-data.json --output-dir /tmp/a7-preview --repository-commit ae1249784c6e3ba25a99da52cc35780049a88380
python -m http.server 8765 --directory /tmp/a7-preview
```

Aprire `http://localhost:8765/`. Il parametro commit deve identificare gli snapshot e dossier della build verificata; per questo lotto sono immutati dalla #432. Quando cambieranno i dati o i dossier, il riferimento dovrà essere aggiornato e verificato. `release.mjs` contiene il manifest fissato dalla build, non accettato dalla domanda o dalla URL; SHA256 verifica integrità rispetto a quel riferimento fidato, non autenticità di un hosting compromesso.

I file generati costituiscono una cartella portabile di preview: index, CSS, modulo UI, lettore originale, release fissata, bundle derivato e answers.md. Non entrano nella build pubblica né nel catalogo canonico. Servire via HTTP locale o HTTPS: i moduli e WebCrypto non costituiscono una promessa di funzionamento con il doppio clic file://. Nessuna credenziale, dipendenza CDN o richiesta a servizi esterni. I link GitHub si aprono soltanto su azione del lettore; non sono acquisizioni live o verifica di disponibilità corrente delle fonti.

## Verifiche e limiti

Il gate A7 esistente esegue anche la preview reale: sei piani in due viewport, identità dei fatti e dei limiti, consenso/annullamento/cambio selezione, dettagli originali, link congelati, assenza di overflow, errori browser, richieste esterne e memorizzazione delle domande. Fixture isolate verificano blocco su bundle alterato e resa di testo simile a HTML senza esecuzione. Nessun dato o sorgente del candidato viene alterato per queste prove. I report e screenshot sono output QA, non nuovi golden.

Il browser verifica etichette, tastiera e focus dei controlli nativi; questo non certifica una revisione completa con tecnologie assistive. Le soglie Lighthouse e i 40 golden pubblici restano invariati. La preview non aggiunge una famiglia al contratto delle route perché non viene pubblicata; una futura integrazione deve dichiararla esplicitamente e preservare shell, ricerca, Stato dati e regole tematiche.

Prima dell'integrazione pubblica il proprietario valuta leggibilità, pertinenza delle sei domande e chiarezza dei dati parziali. L'architettura definitiva e l'eventuale interpretazione libera restano aperte. Questa preview non conclude A7.5 o la Definition of Done di A7.
