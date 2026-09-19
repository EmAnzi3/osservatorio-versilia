# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A3 — Enrichment Audit globale
- **Step attivo:** A3.5 — integrazione nuove dimensioni in lotti controllati
- **Stato:** IN_PROGRESS — lotti 1–5 mergiati; lotto 6 historical + MEF companions sul branch dedicato
- **Main verificato:** 8da1ff52f7489e33e0c16c5d4dbd62a1e48ceb37 (merge #264)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2:** 2.025 coppie; 2.025 classificate, 0 residue
- **Backlog A3.4 post-#264:** 787 AVAILABLE_MISSING · 262 pacchetti · 63 source profile
- **Branch corrente:** feat/a3-5-enrichment-lot-6
- **Autorizzazione operativa corrente:** proseguire sui lotti non-visivi; fermarsi quando serve verifica visiva del proprietario

## A3.5 — acquisizioni

- **Lotto 1 / #260:** 3 coppie sesso.
- **Lotto 2 / #261:** 16 coppie OpenBDAP numeratore/denominatore.
- **Lotto 3 / #262:** 20 coppie Frame SBS.
- **Lotto 4 / #263:** 12 coppie Istat Census.
- **Lotto 5 / #264:** 34 coppie source-backed; backlog confermato a 787.

### Lotto 6 — branch corrente

Usa esclusivamente snapshot già versionati e non modifica il payload pubblico consumato dalla UI.

Acquisizioni attese:
- 6 × serie storica: due quote industriali Frame SBS, due variazioni ASIA, popolazione 2019–2026, rigidità della spesa OpenBDAP;
- 2 × categorie specifiche industria/servizi per le due quote Frame SBS;
- 4 × MEF numeratore/denominatore + assoluto/normalizzato per profilo fonti di reddito e peso dei redditi da pensione;
- 1 × assoluto/normalizzato per addizionale comunale IRPEF sullo scenario standard 20.000 €.

Totale: 13 coppie. Effetto atteso:

AVAILABLE_MISSING: 787 → 774

Restano esclusi gli storici non riconciliabili 7/7 con gli snapshot disponibili. A3.5 resta IN_PROGRESS; A3.6 non parte.

## Decisioni vincolanti

1. data/site-data.json resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale.
3. A3.2 resta strict a unclassifiedPairCount = 0.
4. ACQUIRED deriva solo da struttura/formula verificabile, mai da override manuale.
5. Nessuna retro-derivazione di componenti mancanti dai valori pubblicati.
6. Nessuna modifica UI/rendering nei lotti enrichment puramente strutturali.

## Prossima azione esatta

1. Aprire la PR Ready del lotto 6.
2. Verificare A3 + Quick + Full sullo stesso final head.
3. Confermare 774 AVAILABLE_MISSING e 0 residue.
4. Correggere solo regressioni reali senza indebolire detector o contratti.
5. Se i gate sono verdi, merge secondo l'autorizzazione corrente e ripartenza dal backlog LIVE.
