# Metodo editoriale social

## Il contratto

L’Osservatorio pubblica **due contenuti a settimana**. Ogni contenuto è un unico carosello di **quattro immagini PNG 1080×1350**, identiche per Facebook, Instagram, LinkedIn e X.

Non si producono PDF, storie o formati paralleli. La settimana di avvio può essere incompleta; una settimana ordinaria non supera mai due uscite.

## I quattro passaggi

1. **Il dato attuale** — i sette Comuni in ordine alfabetico, barre da zero e un dato territoriale complessivo messo in evidenza.
2. **Lo storico** — andamento nel tempo, estremi leggibili e dichiarazione esplicita quando la scala non parte da zero.
3. **Il confronto temporale** — variazione dal periodo base per ciascun Comune. Lo zero resta visibile e il colore non esprime un giudizio.
4. **La conversazione** — due domande specifiche, invito a indicare il Comune nei commenti e invito a seguire la pagina.

Se una fonte affidabile non offre una serie storica, le tavole 2 e 3 diventano rispettivamente “Che cosa misura” e “Come leggerlo”. Non si inventano storici né stime.

## Cosa rimane sempre uguale

- formato, griglia e sfondo;
- posizione e dimensione del logo;
- margini e allineamento a sinistra;
- famiglia tipografica e gerarchie;
- pannello, testata, fonte e contatore 1–4;
- struttura delle tavole e delle didascalie;
- ordine alfabetico dei Comuni;
- posizione delle domande e dell’invito a partecipare.

Il tema cambia soltanto i colori `accent`, `soft` e `line`. Questi valori sono quelli del sito e sono centralizzati in `config/themes.json`.

La regola di impaginazione è assoluta: **nessun testo può uscire dal proprio box**. Il generatore riduce il corpo entro il minimo ammesso; se il testo non entra, interrompe la generazione.

## Calendario e ricorrenze

La priorità editoriale è:

1. ricorrenza ufficiale pertinente;
2. contesto attuale pertinente;
3. normale rotazione del calendario.

Una ricorrenza sostituisce uno dei due contenuti settimanali: non crea una terza uscita. Si usa soltanto quando:

- la ricorrenza è documentata da un ente ufficiale in `config/recurrences.json`;
- esiste nel repository un indicatore realmente pertinente;
- la fonte, l’anno, il perimetro e la copertura sono verificabili;
- il collegamento non richiede interpretazioni forzate.

Se manca anche una sola condizione, si segue il calendario ordinario.

Il controllo preventivo si esegue con:

```bash
python3 scripts/plan_social_week.py --date 2026-11-09
```

## Dati climatici

Un episodio di caldo può rendere attuale un contenuto sul clima, ma non può essere presentato come prova della tendenza climatica. I caroselli climatici usano soltanto anni completi e confronti pluriennali dichiarati; non includono il 2026 parziale.

## Generazione

Tutte le bozze configurate:

```bash
python3 -m pip install -r social-kit/requirements.txt
python3 scripts/generate_social_kit.py
python3 scripts/test_social_kit.py
```

Una sola voce:

```bash
python3 scripts/generate_social_kit.py \
  --post-id 2026-08-14-clima-temperature-massime
```

Le voci disponibili:

```bash
python3 scripts/generate_social_kit.py --list-posts
```

## Pacchetto prodotto

Per ogni contenuto:

- quattro PNG e quattro SVG 1080×1350;
- testi adattati per Facebook, Instagram, LinkedIn e X;
- testo master;
- testo alternativo per ogni tavola;
- provenienza completa con valori, calcoli, fonte e URL;
- manifest di controllo.

Tutto rimane in bozza. Il workflow GitHub produce un artefatto da scaricare e non pubblica sui social né modifica il sito.

## Revisione umana

Prima della pubblicazione si controllano le quattro PNG reali su smartphone, non soltanto gli SVG:

- nessun testo tagliato o fuori box;
- dato, unità e periodo comprensibili senza leggere la didascalia;
- assenza di classifiche implicite o cause non dimostrate;
- domande pertinenti e non generiche;
- corrispondenza tra grafica, testo, fonte e pagina del sito;
- opportunità dell’uscita nel contesto del momento.
