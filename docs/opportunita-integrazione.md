# Radar Opportunità · integrazione nel sito

## Stato di questa PR

Questa fase porta il motore v0.4.3 sulla build reale dell'Osservatorio per collaudare la route definitiva `/opportunita/` senza pubblicarla.

Vincoli intenzionali:

- route generata soltanto dal workflow `Radar Opportunità · integrazione nascosta`;
- `noindex,nofollow,noarchive`;
- nessuna voce `Opportunità` nell'header;
- nessun blocco o link in home;
- nessuna voce in sitemap;
- nessuna modifica al workflow pubblico `pages.yml`;
- nessun deploy automatico del Radar.

## Baseline funzionale

Il collector e il renderer derivano dalla v0.4.3 collaudata nella PR prototipale. La raccolta mantiene i gate di copertura, continuità, audit indipendente e holdout. Il primo run della nuova branch può usare l'ultimo artifact v0.4.3 del prototipo come bootstrap di continuità; i run successivi usano il precedente artifact della branch di integrazione.

## Uscita dalla fase nascosta

Solo dopo collaudo esplicito:

1. collegare la generazione di `/opportunita/` al normale workflow Pages;
2. aggiungere `Opportunità` alla navigazione canonica;
3. aggiungere il richiamo in home;
4. rimuovere `noindex` e registrare la route in sitemap;
5. rieseguire i controlli di coerenza globali prima del merge/pubblicazione.
