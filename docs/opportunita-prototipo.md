# Radar Opportunità Versilia — prototipo

## Obiettivo

Verificare se un collettore automatico può individuare opportunità finanziarie realmente utilizzabili dai sette Comuni della Versilia senza introdurre rumore o false certezze.

Il prototipo è intenzionalmente separato dalla parte pubblica del sito: non crea route, non modifica `data/site-data.json`, non entra nella sitemap e non pubblica automaticamente opportunità.

## Perimetro v0.1

Comuni: Camaiore, Forte dei Marmi, Massarosa, Pietrasanta, Seravezza, Stazzema e Viareggio.

Prime fonti:

1. Regione Toscana — bandi aperti;
2. Fondazione Cassa di Risparmio di Lucca — bandi in corso;
3. PA digitale 2026 — dataset open data degli avvisi.

## Regola di sicurezza sull'ammissibilità

Il motore non usa inferenze generative per dichiarare ammissibile un Comune.

- `eligible`: la fonte cita esplicitamente Comuni, enti locali o amministrazioni pubbliche locali;
- `conditional`: sono ammessi soggetti pubblici ma esistono condizioni/partenariati da verificare;
- `review`: il testo disponibile non basta;
- `not_relevant`: i destinatari espliciti non sono amministrazioni comunali e l'elemento viene escluso dall'output operativo.

Una futura interfaccia dovrà mostrare la motivazione e la fonte, non soltanto l'etichetta.

## Output normalizzato

Ogni opportunità mantiene almeno: fonte, titolo, URL, sintesi, apertura, scadenza, destinatari, Comuni potenzialmente interessati, stato di ammissibilità, motivazione, temi, importi quando presenti, priorità provvisoria, timestamp di rilevamento e fingerprint.

La priorità in v0.1 è solo una triage operativa (`high`, `medium`, `low`), non una valutazione amministrativa.

## Esecuzione

```bash
python scripts/test_opportunity_radar.py
python scripts/opportunity_radar.py \
  --date 2026-08-21 \
  --output reports/runtime/opportunities.json \
  --report reports/runtime/opportunities.md
```

La seconda istruzione richiede accesso di rete e interroga le tre fonti configurate in `data/opportunity-sources.json`.

## Criteri per passare alla v0.2

Prima di costruire `/opportunita/` occorre misurare su un campione reale:

- quante opportunità vengono individuate;
- quante sono realmente pertinenti a un Comune;
- quanti falsi positivi genera il filtro;
- quante opportunità note vengono perse;
- quali fonti richiedono parser dedicati o feed machine-readable.

Solo dopo questa verifica si aggiungono altre fonti e un backtest 60–90 giorni.
