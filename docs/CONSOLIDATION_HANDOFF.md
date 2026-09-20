# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A5 — Design System 2.0
- **Step attivo:** A5.1–A5.3 — audit e fondazione non visuale
- **Stato:** IN_PROGRESS — fondazione preparata in branch, A5.4 sarà la prima modifica UI
- **Main verificato:** `df90fd9372c536cb4288488557cc863150e43791` (merge #271)
- **A4:** DONE — deploy Pages post-merge verde, `ov-pages-live` success
- **Catalogo effettivo:** 225 indicatori
- **Visual regression A4:** 40 campioni rappresentativi
- **Branch corrente:** `feat/a5-design-system-foundation`
- **Modifiche visive al prodotto:** nessuna

## A5.1 — audit

Il referto completo è in `docs/A5_DESIGN_SYSTEM_AUDIT.md`.

Baseline principali:
- 246 colori HEX distinti nei quattro CSS pubblici principali;
- 187 dichiarazioni background e 336 dichiarazioni di bordo;
- contrasto `paper/surface`: 1,11:1;
- contrasto `muted/paper`: 4,37:1;
- 177/288 dichiarazioni font-size in px <= 11 px;
- due sistemi tematici sovrapposti: `theme-color` e `theme-accent`;
- token tematici espliciti per 9 temi su 11: mancano `sicurezza` e `bilanci`.

## A5.2–A5.3

La fondazione DS2 separa:
- canvas neutro;
- surface primaria, secondaria ed editoriale;
- testo primary/secondary/tertiary;
- bordi e focus;
- elevazione;
- tema accent/soft/line;
- stati semantici.

Il vocabolario nuovo usa prefisso `--ds-`. Gli alias storici restano temporaneamente durante la migrazione; `--theme-color` e `--theme-accent` devono convergere.

## Prossima azione esatta

1. Portare la fondazione A5.1–A5.3 in PR Ready e richiedere Quick + Full verdi.
2. Merge solo dopo approvazione esplicita del proprietario.
3. Dopo il merge aprire A5.4 sulla pagina pilota `confronta/demografia/`.
4. A5.4 deve essere Draft perché modifica la UI.
5. Il primo mismatch A4 intenzionale deve produrre screenshot diagnostici: verificarli desktop/mobile prima di aggiornare le baseline.
6. Non modificare dati, contenuti, tooltip o semantica durante il pilot.
