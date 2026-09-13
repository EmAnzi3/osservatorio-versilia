# INVALSI v1.38.0 — gate di review

Questa tranche resta in Draft fino a verifica dei workflow e approvazione esplicita.

## Contratto dati

- 203 → 207 indicatori.
- Comune = `Comune plesso`, aggregazione `Totale`.
- Benchmark ufficiali: Toscana e Italia.
- Nessuna media Versilia.
- `888`, `999` e valori sorgente assenti → `n.d.`.
- Nessuna stima o interpolazione.
- Dettaglio dei singoli istituti escluso.

## Gate automatici

- ricostruzione snapshot con dimensione e SHA-256 attesi;
- validazione 16 viste risultati, 12 competenze, 2 dispersione, 2 eccellenza;
- controllo coperture correnti e gap pandemici;
- materializzazione 203 → 207 in file temporanei;
- canonical build;
- sintassi bundle JavaScript;
- browser QA desktop/mobile;
- benchmark Toscana/Italia e assenza di media Versilia;
- controllo overflow mobile e screenshot di review.
