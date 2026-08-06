# Aggiornamento mensile dei dati

## Obiettivo

Il controllo viene eseguito una volta al mese e può essere avviato anche manualmente. La procedura è prudenziale: verifica dati e fonti, ma non pubblica valori senza controllo umano.

## Calendario

Il workflow `Controllo mensile dati` è programmato per il giorno 5 di ogni mese alle 05:17 UTC. L'orario non tondo riduce la probabilità di attese nelle code dei runner GitHub.

## Cosa controlla

- presenza dei 98 indicatori attesi;
- copertura completa dei sette Comuni e codici Istat corretti;
- presenza di anno, unità, fonte, metodo e formula;
- coerenza fra annualità e valori delle serie storiche;
- raggiungibilità delle fonti ufficiali;
- modifica dei file ufficiali direttamente scaricabili;
- cambiamenti di URL, reindirizzamenti ed eventuali segnali HTTP.

## Cosa non fa

- non stima dati mancanti;
- non interpola annualità;
- non sostituisce valori pubblicati;
- non effettua merge;
- non pubblica direttamente su GitHub Pages.

## Notifiche

Per ogni esecuzione programmata o manuale il workflow:

1. crea, se necessario, l'issue `Registro controlli dati <anno>`;
2. aggiunge un commento con il rapporto mensile;
3. menziona `@EmAnzi3`, generando una notifica GitHub;
4. conserva il rapporto completo come artifact per 90 giorni.

Se il workflow si interrompe prima della notifica, resta disponibile la notifica di errore standard di GitHub Actions.

## Esiti possibili

- `no_changes`: nessuna variazione sostanziale; nessuna PR;
- `baseline_required`: prima fotografia delle fonti; PR in bozza;
- `changes_detected`: una fonte è stata aggiunta, rimossa, reindirizzata o un file ufficiale è cambiato; PR in bozza;
- `attention_required`: il dataset non supera i controlli strutturali; workflow fallito e pubblicazione impedita.

Le fonti non raggiungibili sono segnalate nel rapporto ma, nella fase iniziale, non cancellano dati e non sono automaticamente considerate un errore strutturale: alcuni portali istituzionali bloccano i controlli automatici.

## Prima esecuzione

Dopo il merge della funzionalità, la prima esecuzione live apre una PR in bozza per registrare la baseline delle fonti. La baseline diventa effettiva soltanto dopo verifica e merge.

## Esecuzione manuale

Aprire:

`Actions → Controllo mensile dati → Run workflow`

Lasciare attivo `Controlla anche le fonti online` per un controllo reale. Disattivarlo soltanto per verificare struttura e copertura senza traffico verso le fonti.

## Pubblicazione di nuovi dati

Quando il controllo rileva una variazione, la PR automatica è soltanto un avviso documentato. L'aggiornamento dei valori deve:

1. acquisire il nuovo dato dalla fonte originale;
2. conservare lo snapshot leggibile;
3. aggiornare anno, valori, serie, formula e fonte in modo coerente;
4. superare build e test;
5. essere verificato manualmente prima del merge.
