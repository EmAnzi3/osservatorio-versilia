# A6 — Pendolarismo per lavoro con basi temporali esplicite

Il lotto v11 abilita sette indicatori già pubblicati, senza acquisizioni o cambiamenti dei dati, delle pagine o dei golden. Il motore raggiunge 108/225 adapter effettivi e 75/181 sorgente; i conteggi vengono comunque derivati dall'audit. A6.4 resta parziale; A6.5–A6.6 aperte, A7 non avviata.

## Fonte e perimetro

Pagina ufficiale: https://www.istat.it/notizia/matrice-di-pendolarismo-per-lavoro/

Archivio censito: https://esploradati.istat.it/databrowser/DWL/PERMPOP/MATPEN/matrix_pendoLAVORO_2021.zip

Si riusa `data/source-snapshots/a3-istat-commuting-benchmark-2021.json`: 7.904 totali comunali, copertura di 273 comuni toscani, conservazione ingressi/uscite nazionali e 19.565.808 pendolari residenti della matrice. Lo snapshot registra l'estrazione da 523.949 coppie, **ma non conserva tutte le coppie origine-destinazione**. Non permette di ricostruire linee di desiderio, modi di trasporto, tempi, mezzi, capacità o flussi lordi attraverso il confine di un gruppo di comuni.

Universo: lavoro abituale, raggiunto almeno tre giorni a settimana con ritorno giornaliero. Non sono tutti gli occupati, tutti gli spostamenti quotidiani o il pendolarismo per studio. Il 2021 non viene presentato come fotografia corrente 2026; nessuna serie storica o variazione viene inventata.

| Indicatore | Componenti | Denominatore / precisione |
|---|---|---|
| Entrate / uscite | Totali della matrice con origine/destinazione diversa | Conteggi del 2021 |
| Saldo assoluto | Entrate meno uscite | Saldo firmato del 2021 |
| Tassi di entrata / uscita | Conteggi 2021 × 1.000 | Residenti POSAS al 1° gennaio **2026**, fonte etichettata come stima |
| Tasso di saldo | Saldo 2021 × 1.000 | Residenti censiti al 1° gennaio **2021**, P02 con maschi + femmine = totale |
| Autocontenimento | Flussi nel proprio comune / (interni + uscite) × 100 | Universo dei pendolari residenti della matrice 2021; rapporto esatto da componenti |

Il valore pubblico dell'autocontenimento è arrotondato a un decimale. Il motore conserva `publishedValue`, verifica lo scarto entro mezzo decimale e restituisce il rapporto esatto da componenti con avvertenza; nessun JSON pubblico viene riscritto. Gli altri carrier sono riconciliati alle componenti. Un valore mancante pubblicato resta mancante, anche quando esistono componenti.

I residenti 2026 dei sette comuni sono verificati nel POSAS congelato; i benchmark Toscana/Italia sono riconciliati con il relativo snapshot demografico e il suo hash. Residenti 2021 e flussi hanno identica copertura nazionale e componente comunale identificata. La provenienza conserva hash, percorsi, puntatori e archivi dei numeratori/denominatori. Queste sono evidenze dell'acquisizione congelata, non verifiche live di un nuovo rilascio.

## Aggregazioni e confronti

I rapporti del gruppo si ricavano dalla somma delle componenti, senza mediare percentuali o tassi. Le entrate e le uscite comunali sommate **includono movimenti tra comuni del gruppo**: non sono ingressi e uscite dal territorio selezionato. Il saldo netto somma invece entrate meno uscite e cancella i movimenti interni al gruppo; dai soli margini non si recuperano i due flussi lordi al confine.

L'autocontenimento ponderato del gruppo è la quota che lavora **nel proprio comune** tra i pendolari residenti dei comuni scelti. Non è la quota che lavora in qualsiasi comune della Versilia. Questo limite vale anche per i benchmark regionali/nazionali costruiti dagli stessi margini.

Gli scostamenti verso Toscana/Italia sono abilitati per i quattro rapporti sulle medesime definizioni e date. Il confronto tra il volume assoluto di un comune e l'intero volume regionale/nazionale è rifiutato. Le correlazioni sono descrittive, su coppie scelte con scopo esplicito; componenti condivise e dimensione demografica possono generare associazioni meccaniche. Tassi 2021/2026 e tasso di saldo 2021/2021 non vengono associati automaticamente come misure contemporanee omogenee.

`outsideMunicipality` resta senza adapter: la quota censuaria non è riconciliata all'universo della matrice per lavoro e non è il complemento di `selfContainment`. Non si deducono mobilità per studio, accesso alle scuole, qualità della rete, fabbisogno di corse o effetti delle politiche.

## Domande e controlli

Suite cumulativa: 148 domande, 94 calcoli e 54 rifiuti attesi; 18 casi aggiuntivi con numeri indipendenti e coefficienti Spearman verificati da ranghi trascritti (−17/28 e 9/14), denominatori, periodi, componenti condivise e rifiuti verificati. Regressione: 161 osservazioni native/benchmark, riferimenti comunali trascritti, somme del gruppo, valori mancanti, identità e formule alterate, conservazione dei flussi e periodi impropri. Nessuna soglia generale viene ridotta.

```bash
python scripts/test_semantic_commuting_adapters.py
python scripts/semantic_engine_audit.py --output-dir /tmp/a6-commuting
python scripts/semantic_question_suite.py --output-dir /tmp/a6-commuting
python scripts/semantic_engine_benchmark.py --output-dir /tmp/a6-commuting
python scripts/preflight.py --quick
python scripts/preflight.py --full
```

Audit, mappa dei collegamenti, domande e baseline sono riproducibili dal catalogo effettivo. La baseline misura carichi deterministici locali; non garantisce latenza in produzione, concorrenza, cache disco fredda o capacità di servizio. I gate finali e la modalità del browser locale vengono riportati nella PR prima della revisione per merge.
