# A7 — valori fuori scala fra i sette Comuni

Incremento di A7.5.3 (altre operazioni ammesse). A6 resta DONE e A7 IN_PROGRESS.
Espone in «Chiedi» l’operazione `anomaly` già validata da A6, con l’etichetta
pubblica «Valori fuori scala fra i sette Comuni». Nessun adapter, dato, metodo
numerico o script con impronta nelle evidenze A6 viene modificato.

## Cosa vede chi consulta

Per una vista ammessa la pagina indica quali Comuni hanno un valore molto sopra o
molto sotto gli altri, oppure che nessun Comune è fuori scala. Mostra soglia
inferiore, valore mediano e soglia superiore, la classificazione di ciascun
Comune e, a richiesta, quartili, scarto interquartile e soglie con la precisione
originale. Grafico e tabella restano quelli dei confronti fra Comuni.

La parola «anomalia» non compare nella presentazione: con sette Comuni la regola
è una lettura descrittiva e non indica errori nel dato, qualità amministrativa o
priorità. Lo dichiarano il testo della pagina e le avvertenze originali A6
(`anomaly_is_not_data_error_or_policy_priority`,
`small_peer_group_no_inferential_claim`, `reference_selection_changes_fences`).

## Richiesta trasportata

Profilo `outliers`: una sola richiesta A6 per vista, su tutti e sette i Comuni,
con campi dichiarati dal builder e pubblicati nel manifest (`outlierSelection`):

- `rule`: `tukey_1_5_iqr`;
- `reference`: `selected_municipalities`;
- `purpose`: motivo editoriale fisso in italiano, uguale per tutte le viste.

L’interfaccia legge questi campi dal manifest verificato e non li riscrive. Un
sottoinsieme di Comuni, un’altra regola o riferimento, un motivo diverso o il
consenso parziale restituiscono `not_materialized`. Il browser non calcola
quartili, soglie o classificazioni: valida il risultato nativo e lo presenta.

Rifiuti tradotti per la lettura, con il motivo originale nelle evidenze:
scarto interquartile nullo (`anomaly_zero_interquartile_range`) e meno di quattro
valori disponibili. La copertura incompleta segue il consenso già esistente.

## Misura

Sul catalogo effettivo del 26 ottobre 2026: 515 viste di 130 indicatori
ammettono l’operazione; 503 producono un risultato, 8 hanno scarto
interquartile nullo e 4 richiedono il consenso per copertura incompleta.

## Versioni e confini

- Interfaccia pubblica v8 (v6 → v8); l’anteprima isolata degli incroci passa
  da v7 a v9 e resta vietata nella build pubblica.
- L’audit di accessibilità considera presentate le viste `anomaly` soltanto con
  interfaccia ≥ 8 e verifica che nessuna associazione risulti presentata.
- Gli incroci (A7.5.4) sono esclusi dalla prima versione guidata per decisione
  del proprietario: vedi `A7_ASSOCIATION_PERIMETER.md`.

## Verifiche

`test_a7_query_runtime.py` (ricetta, manifest, parità nativa, riscritture rifiutate
nel browser), `test_a7_explorer_preview.py` (verdetto, classificazioni, soglie
arrotondate e originali, assenza della parola «anomalia», selettore del Comune
nascosto, rifiuti), `test_a7_accessibility.py` (perimetro presentato).
