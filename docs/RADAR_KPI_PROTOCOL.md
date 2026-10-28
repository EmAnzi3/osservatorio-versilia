# Radar Opportunità — protocollo KPI prospettici

## Perimetro e denominatore

Il **capture rate prospettico** misura, su un campione indipendente e raccolto
in avanti nel tempo, la quota di opportunità pertinenti trovate dal Radar.
Il denominatore comprende tutte le opportunità eleggibili del campione holdout,
anche quelle che il Radar non rileva: non si selezionano solo le schede già
pubblicate. La metrica compare **solo con almeno 20 casi prospettici**.
Sotto 20, `captureRate = null`, stato `pending_minimum_sample` e conteggi
visibili; nessuna percentuale provvisoria viene chiamata KPI.

Il campione retrospettivo del 22 agosto 2026 è intenzionalmente sbilanciato
verso i falsi negativi; non misura la copertura generale. I casi
`audit_review` e i controlli storici non entrano nel denominatore.

## Eventi temporali non intercambiabili

Per ogni caso prospettico si annotano date documentate (ISO 8601):

| Campo | Significato |
| --- | --- |
| `official_published_at` | Prima pubblicazione accertata dell'avviso sulla fonte istituzionale. |
| `radar_detected_at` | Prima acquisizione della segnalazione da parte del Radar, prima di qualsiasi qualificazione. |
| `radar_qualified_at` | Prima verifica completa di requisiti, ammissibilità territoriale e ruolo comunale. |
| `radar_published_at` | Prima comparsa effettiva della scheda nel Radar pubblico. |

I tre tempi di attraversamento, separati, sono:

- **Detection lag** = prima rilevazione Radar meno pubblicazione ufficiale;
- **Qualification lag** = qualificazione completa meno prima rilevazione;
- **Publication lag** = pubblicazione effettiva meno qualificazione.

La mediana di ogni tempo resta non misurabile fino a 20 coppie di date
coerenti per quello specifico passaggio. Un timestamp assente, incoerente o
precedente all'evento iniziale non viene riempito per deduzione.

Le date `audit_found_at` del controllo retrospettivo misurano **quando
l'auditor ha trovato il caso**, non quando il Radar avrebbe dovuto o potuto
rilevarlo. Il precedente campo `targetedDetectionLagDays` è mantenuto per
compatibilità ma disabilitato (mediana nulla); la vecchia durata è
esplicitamente `targetedAuditIdentificationDelayDays` e non è un KPI.

## Cosa non dimostrano queste metriche

Un test di replay verde non è una prova di capture rate prospettico.
La sola data `first_seen_at` sul record pubblicato non ricostruisce i tempi
di qualifica e pubblicazione. Occorrono log/receipt dei tre passaggi,
identificativi stabili e un campione holdout indipendente. Nessun dato mancante
è stimato e nessun servizio esterno a pagamento è richiesto.
