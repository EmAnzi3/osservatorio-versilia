# A1.1 — audit della pipeline di Data Governance

Data audit: 2026-09-15
Baseline auditata: `2b7523050310f0615415ad813dacefbaaf028bc5`

Rivalidazione su `main` dopo il merge radar #189: `850fad77dc506d19f33351e092e926fa8fc3728a`. I file canonici `data/site-data.json` e `data/source-registry.json` risultano invariati, quindi evidenze e conclusioni dell'audit restano valide.

## Scopo

Questo audit descrive il percorso che porta dal catalogo sorgente alla release effettivamente pubblicata. I numeri riportati qui sono evidenze della baseline auditata, non contatori operativi da mantenere manualmente.

Il principio architetturale resta invariato: `data/site-data.json` è l'unica fonte canonica del catalogo sorgente. La build può arricchirlo in uno workspace transazionale, ma non deve introdurre un secondo inventario canonico.

## Tre livelli distinti

1. **Catalogo sorgente canonico** — `data/site-data.json` versionato nel repository.
2. **Effective Public Catalog** — `dist/data/site-data.json`, vista derivata e riproducibile prodotta dalla build dopo tutti i materializzatori pubblici.
3. **Stato operativo del monitor** — `data/source-monitor-state.json`, che registra i controlli realmente eseguiti sulle fonti.

Questi livelli hanno responsabilità diverse. Il catalogo pubblico non deve essere ricopiato nel sorgente solo per far coincidere i conteggi; lo stato operativo del monitor non deve essere interpretato come inventario del catalogo.

## Baseline verificata

Sulla baseline auditata:

- catalogo sorgente: **181** indicatori;
- catalogo effettivamente pubblicato: **225** indicatori;
- registry pubblico materializzato: **225** indicatori, di cui 221 incorporati e 4 climatici esterni;
- Stato dati pubblico: **225** ID, allineati al catalogo pubblicato;
- tutti i **225** indicatori pubblicati risolvono una policy fonte completa;
- 44 indicatori sono quindi aggiunti dalla catena di materializzazione rispetto alla sorgente canonica.

Il monitor periodico resta una dimensione separata: l'ultimo run auditato operava sul catalogo sorgente e non prova, da solo, l'avvenuto controllo recente di tutti i 225 indicatori pubblicati. La copertura temporale/operativa completa è oggetto di `A2`.

## Lineage osservata 181 → 225

La catena di release osservata porta il catalogo attraverso questi checkpoint:

| Passaggio | Indicatori |
| --- | ---: |
| Catalogo sorgente | 181 |
| Agricoltura II | 183 |
| Atlante economia | 184 |
| Affluenza | 185 |
| Fragilità | 189 |
| Economia prodotta | 195 |
| Biometria comunale | 198 |
| Territorio / UCS | 201 |
| Foreste | 202 |
| Rete viaria | 203 |
| INVALSI | 207 |
| Bilanci | 213 |
| Salute | 225 |

Questa tabella documenta la baseline auditata. La lineage eseguibile dovrà essere resa verificabile dal contratto di build in `A1.8`, senza trasformare la tabella in un secondo manifest da aggiornare a mano.

## Pipeline effettiva

Il flusso pubblico è:

`data/site-data.json`
→ workspace transazionale di build
→ materializzatori/overlay di release
→ `dist/data/site-data.json`
→ `build_data_status.py`
→ `dist/data/data-status.json` + `/stato-dati/`
→ controlli di consistenza
→ deploy Pages

`public_build_snapshot.py` è il punto già esistente che distingue correttamente sorgente canonica e snapshot pubblico. La build deve poter arricchire il catalogo senza lasciare mutazioni nei file canonici versionati.

## Divergenze trovate

### README

Il README della baseline pubblica era fermo a 213 indicatori / v1.39.0, mentre la release effettiva era 225 / v1.40.0. Questo dimostra che i blocchi di stato del README non devono dipendere da conteggi copiati manualmente. È il perimetro di `A1.4` e `A1.6`.

### Stato dati

La generazione di Stato dati è già build-aware: legge lo snapshot pubblico materializzato. Non va riscritta. Deve invece essere protetta da un'invariante per ID, non soltanto da conteggi.

### Monitor fonti

Il monitor periodico auditato parte dal catalogo sorgente e quindi può risultare verde pur non avendo ancora controllato gli indicatori aggiunti dagli overlay pubblici. `A1` deve garantire che ogni ID pubblicato sia almeno censito e dotato di policy fonte; `A2` deve garantire che venga anche controllato periodicamente secondo una strategia verificabile.

### Lineage dei materializzatori

`ci/build-materialization-contract.json` protegge il perimetro delle mutazioni transitorie, ma l'inventario `publicMaterializers` non rappresenta ancora in modo completo tutti i passaggi realmente invocati dalla build. La correzione è oggetto di `A1.8`: la lineage deve diventare verificabile, non restare implicita nella sequenza Python.

## Decisione A1.2

L'**Effective Public Catalog** è formalmente `dist/data/site-data.json`.

È una vista derivata e riproducibile della release, non una nuova fonte canonica. Deve essere usata dai controlli post-build che ragionano su ciò che gli utenti vedono realmente.

## Invariante A1.3

Dopo la materializzazione di Stato dati il gate generale deve verificare:

`ID catalogo pubblico = ID Stato dati = ID con policy fonte valida`

Il confronto è per identità degli ID, non per semplice uguaglianza dei conteggi. Il gate deve fallire indicando gli ID mancanti, extra o privi di policy.

L'ultimo controllo riuscito e la freschezza operativa di ciascun ID restano responsabilità del monitor e saranno chiusi in `A2`.

## Conseguenze per i prossimi step

- `A1.4`: generare i blocchi README dalla stessa verità derivata;
- `A1.5`: consolidare ciò che già esiste in Stato dati senza introdurre una seconda pipeline;
- `A1.6`: riconciliare versione, conteggi e date tra superfici pubbliche;
- `A1.7`: mantenere i gate nel preflight generale;
- `A1.8`: rendere verificabile la lineage dei materializzatori e documentare fonte → acquisizione → trasformazione → indicatore → visualizzazione.
