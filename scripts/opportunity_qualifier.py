#!/usr/bin/env python3
"""Qualificazione automatica delle segnalazioni del Radar.

Fino a ottobre 2026 una segnalazione emersa dal discovery restava in coda finché
qualcuno non scriveva una regola dedicata: il Radar trovava i bandi ma non li
pubblicava. Questo modulo legge pagina e documenti ufficiali di ogni
segnalazione e decide da solo, con regole generali (nessun identificativo di
bando, nessuna data fissa):

- è un avviso/bando e non una notizia, una graduatoria o una comunicazione;
- fra i soggetti ammessi ci sono Comuni o enti locali (frase citata);
- la scadenza è futura, oppure l'avviso è a sportello (frase citata);
- non è riservato a un'altra regione.

Le schede qualificate sono pubblicate subito con l'etichetta «Requisiti da
confermare» e con le frasi dei documenti che giustificano la decisione
(decisione del proprietario, 30/10/2026). Le segnalazioni scartate restano nel
rapporto con il motivo.
"""
from __future__ import annotations

import hashlib
import html as html_lib
import re
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Callable
from urllib.parse import urlsplit

VERSION = "1.1"
LABEL = "Requisiti da confermare"
VERIFICATION_STATUS = "auto_qualified"
MAX_CANDIDATES = 120
MAX_SECONDS = 420
RECHECK_DAYS = 7
MAX_DOCUMENTS = 3

MONTHS = {name: i for i, name in enumerate(
    "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split(), 1)}
MONTHS.update({name: i for i, name in enumerate(
    "january february march april may june july august september october november december".split(), 1)})

REGIONS = ("Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna", "Emilia Romagna", "Friuli",
           "Lazio", "Liguria", "Lombardia", "Marche", "Molise", "Piemonte", "Puglia", "Sardegna", "Sicilia",
           "Trentino", "Alto Adige", "Umbria", "Valle d'Aosta", "Valle d’Aosta", "Veneto")
REGION_ADJECTIVES = ("lombard", "piemontes", "venet", "emilian", "ligur", "lazial", "campan", "pugliese",
                     "calabres", "sicilian", "sardi", "abruzzes", "marchigian", "umbr", "friulan", "trentin",
                     "lucan", "molisan", "valdostan")

CALL = re.compile(
    r"\b(avvis[oi]|bando|bandi|manifestazion[ei] di interesse|call for proposals|call\b|invito a presentare|"
    r"contribut[oi]|finanziament[oi]|fondo|sovvenzion[ei]|candidatur[ae]|grant|funding|topic)\b", re.I)
NOT_A_CALL = re.compile(
    r"\b((?<!formazione della )(?<!formazione delle )graduatori[ae]|esit[oi]|vincitor[ie]|ammess[ie] a finanziamento|elenco (?:dei |degli )?(?:beneficiari|ammessi)|"
    r"approvazione (?:della |delle )?graduatori|chiariment[oi]|faq|orari|video|convegno|webinar|seminario|"
    r"seduta di gara|appalto|affidamento|rendicontazion[ei]|erogazion[ei]|liquidazion[ei]|riparto|ripartizion[ei]|"
    r"decreto di assegnazione|comunicato stampa|intervista|news in evidenza|"
    r"assunzion[ei]|concorso pubblico|selezione di personale|incarico|nomina|protocollo d.intesa|tasso annuo|"
    r"capitalizzazione|front office|description|who can apply|get support|work with us|come to our|"
    # Sezioni per chi è già finanziato (varianti, progetti esecutivi), non nuovi avvisi.
    r"varianti\s*/\s*esecutivi)\b", re.I)
APPLICANT_HEAD = re.compile(
    r"(soggetti\s+(?:beneficiari|ammessi|ammissibili|destinatari|proponenti|richiedenti|candidabili)|"
    r"beneficiari|destinatari|possono\s+(?:presentare|partecipare|candidarsi|accedere)|"
    r"chi\s+pu[oò]\s+(?:partecipare|presentare|candidarsi)|requisiti\s+di\s+(?:ammissibilit|partecipazione)|"
    r"sono\s+ammess[ie]|who\s+can\s+apply|eligible\s+(?:applicants|participants|entities|organisations|organizations)|"
    r"eligibility(?:\s+criteria)?|admissibility|applicants?\b|coordinators?\b|participation\s+of\s+a\s+public\s+authority|"
    r"restricted\s+to\s+public\s+authorities|consortium)", re.I)
MUNICIPAL = re.compile(
    r"\b(comun[ei]|enti\s+locali|ente\s+locale|autonomie\s+territoriali|amministrazion[ei]\s+comunal[ei]|unioni?\s+(?:dei|di)\s+comuni|"
    r"citt[àa]\s+metropolitan[ae]|local\s+(?:and\s+regional\s+)?authorit(?:y|ies)|municipalit(?:y|ies)|"
    r"public\s+(?:bodies|authorit(?:y|ies))|local\s+governments?|towns?|cities)\b", re.I)
# Per i programmi UE «public bodies» comprende anche università e agenzie: serve
# una menzione esplicita di autorità locali, Comuni o città.
MUNICIPAL_STRICT = re.compile(
    r"\b(local\s+(?:and\s+regional\s+)?authorit(?:y|ies)|(?:regional\s+or|regional,?\s+and)\s+local\s+authorit\w*|"
    r"public\s+authorit\w+\s+at\s+local\s+level|authorities\s*\(local|municipalit(?:y|ies)|local\s+governments?|"
    r"cities|comun[ei]|enti\s+locali|"
    # «public authorities can be national, regional or local Ministries/agencies…»:
    # il livello locale è nominato espressamente (i PDF spezzano a volte le parole).
    r"regional\s+or\s+local\s+(?:mini\s?str\w*|agenc\w*|authorit\w*|bod\w*|public\s+\w+))\b", re.I)
# Nei programmi UE il Comune è richiedente solo se il testo lo dice: coordinatori o
# richiedenti che «devono/possono essere» autorità pubbliche/locali, o priorità
# riservata alle autorità pubbliche. Altrimenti partecipa come partner.
EU_LEAD = re.compile(
    r"((coordinator|applicant|lead)\w*[^.]{0,120}\b(must|shall|should|can|may)\s+be\b[^.]{0,160}"
    r"(local|regional\s+or\s+local|public)\s+authorit|restricted\s+to\s+public\s+authorities|"
    r"(eligible\s+applicants?|applicants?)[^.]{0,80}\b(local\s+authorit|municipalit))", re.I)
EU_PARTNER = re.compile(
    r"((consorti(?:um|a)|proposals?|projects?|applicants?|partnerships?)[^.]{0,80}\b(must|should|shall|are\s+(?:expected|required|encouraged)\s+to)\s+"
    r"(?:include|involve|have)[^.]{0,100}\b(local\s+(?:and\s+regional\s+)?(?:public\s+)?authorit|municipalit|city\s+authorit|local\s+governments?)|"
    r"(local\s+(?:and\s+regional\s+)?authorities|municipalities)[^.]{0,40}\b(are|is)\s+eligible|"
    r"(local\s+(?:and\s+regional\s+)?authorities|municipalities)[^.]{0,60}\b(must|should)\s+(?:be\s+)?(?:involved|participate|part\s+of)|"
    r"public\s+authorit\w*\s+in\s+the\s+consorti\w+[^.]{0,30}\bas\s+(?:a\s+)?beneficiar|"
    # «The participation of a public authority is mandatory under this priority»
    # (CERV-DAPHNE-CHILDREN): partecipazione obbligatoria, non capofila.
    r"(?:participation|involvement)\s+of\s+(?:a\s+)?public\s+authorit\w*[^.]{0,20}\b(?:is\s+)?(?:mandatory|compulsory|required))", re.I)
# Topic riservati a gruppi chiusi di città (per esempio le 112 della Missione
# città climaticamente neutre): un Comune qualsiasi non può partecipare.
EU_RESERVED = re.compile(r"(?:must|shall)\s+be\s+from\s+one\s+of\s+the\s+\d+\s+cities|cities\s+selected\s+for\s+the\s+EU\s+Mission", re.I)
# Il Comune come luogo, non come soggetto: «con sede nel Comune di», «residenti nel comune».
MUNICIPAL_AS_PLACE = re.compile(
    r"(sede(?:\s+legale|\s+operativa)?\s+(?:nel|in\s+un|in)\s+comune|residen\w*\s+(?:nel|in)\s+(?:un\s+)?comune|"
    r"ubicat\w+\s+(?:nel|in)\s+(?:un\s+)?comune|nel\s+territorio\s+(?:del|di\s+un)\s+comune|"
    # «beni comuni», «spazi comuni»: aggettivo, non l'ente.
    r"\b(?:ben[ei]|spaz[io]|aree?|part[ei]|obiettiv[oi]|interess[ei])\s+comun[ei]\b)", re.I)
SUBJECT_APPLIES = re.compile(
    r"\b(?:i\s+|gli\s+|le\s+)?(?:comuni|enti\s+locali|amministrazioni\s+comunali|unioni\s+di\s+comuni)\b"
    r"(?:\s+[\w’']+){0,6}?\s+(?:possono|potranno|potrà|può)\s+(?:presentare|inoltrare|trasmettere|candidarsi|"
    r"partecipare|richiedere|accedere|aderire)", re.I)
# Frasi che impongono un adempimento a chi ha già ricevuto un contributo:
# rendiconti, certificazioni, conclusione dei lavori. Non sono avvisi.
OBLIGATION = re.compile(r"\b(?:sono\s+tenut[ie]|è\s+tenut[oa]|devono\s+(?:concludere|rendicontare|trasmettere\s+il\s+rendiconto)|"
                        r"beneficiari\s+dei\s+contributi\s+(?:relativi|assegnati|concessi))", re.I)
# Un avviso a domanda dice come presentarla. Senza questa indicazione la pagina
# parla di un riparto, di un adempimento o di una notizia.
APPLY = re.compile(
    r"\b(?:presentare|presentano|inoltrare|trasmettere|inviare)\s+(?:la\s+|le\s+|una\s+|apposita\s+|propri[ae]\s+)?"
    r"(?:domand|candidatur|istanz|richiest[ae]\s+di\s+(?:contribut|finanziament|ammission|partecipazion)|propost|progett|manifestazion)|"
    r"presentazione\s+(?:delle|della|di)\s+(?:domand|candidatur|istanz|propost|progett|manifestazion|richiest)|"
    r"\b(?:domand[ae]|candidatur[ae]|istanz[ae])\s+(?:di\s+(?:contributo|finanziamento|partecipazione|ammissione)\s+)?"
    r"(?:dovranno|devono|possono|potranno)\s+essere\s+(?:presentat|inoltrat|trasmess|inviat)|"
    r"\bdomande\s+(?:fino\s+al|entro|esclusivamente|tramite|da\s+presentare)|"
    r"\bcandidature\b|manifestazioni?\s+di\s+interesse|sportello\s+(?:telematico|online)|"
    r"call\s+for\s+proposals|submission|apply\b|deadline", re.I)
# Topic UE che finanziano un unico consorzio incaricato di gestire uno
# strumento a cascata (per esempio la European City Facility): i Comuni ne
# beneficiano in una fase successiva, non possono presentare la proposta.
OPERATOR = re.compile(r"intends? to (?:select|fund) (?:only )?(?:one|a) single proposal|"
                      r"(?:select|fund) (?:only )?one proposal under (?:this )?topic", re.I)
ONLY_OTHERS = re.compile(
    r"\b(esclusivamente|solo|soltanto|unicamente)\s+(?:a(?:lle|gli|i)?\s+)?(imprese|associazioni|cittadini|persone\s+fisiche|"
    r"studenti|scuole|universit|enti\s+del\s+terzo\s+settore|organizzazioni)", re.I)
# «Riservata a soli soggetti privati»: il bando esclude gli enti pubblici, anche
# se più avanti cita il Comune come possibile finanziatore o partner.
PRIVATE_ONLY = re.compile(
    r"riservat[ao]\s+(?:a\s+)?(?:soli|sol[oe]|esclusivamente|unicamente|soltanto)\s+(?:a(?:i|gli|lle)?\s+)?"
    r"(?:soggetti|enti|organismi|organizzazioni)\s+privat", re.I)
# Voce dei destinatari: la scheda del bando, o l'articolo dell'avviso, dice chi
# può presentare domanda. È l'unica fonte della decisione su chi è ammesso.
BENEFICIARY_HEAD = re.compile(
    r"\b(?:soggetti\s+(?:beneficiari|ammessi|ammissibili|destinatari|proponenti|richiedenti|legittimati|candidabili)"
    r"(?:\s+(?:a\s+(?:presentare|partecipare)|alla\s+presentazione)[^.:;]{0,40})?|"
    r"destinatari\b(?:\s+(?:del\s+(?:bando|contributo|finanziamento)|dell[’']\s*avviso|dei\s+contributi))?|"
    r"beneficiari\b(?!\s+(?:finali|dei\s+contributi\s+(?:relativi|assegnati|concessi)|ammess))"
    r"(?:\s+(?:del\s+(?:bando|contributo|finanziamento)|dell[’']\s*avviso))?|"
    r"chi\s+pu[oò]\s+(?:partecipare|presentare(?:\s+domanda)?|candidarsi|fare\s+domanda|accedere)|"
    r"a\s+chi\s+(?:è|e['’])\s+rivolt[oa]|a\s+chi\s+si\s+rivolge|requisiti\s+soggettivi|"
    r"(?:pre)?requisiti\s+di\s+(?:ammissibilit[àa]|partecipazione|accesso)|domanda\s+(?:deve\s+essere\s+)?presentata\s+da|"
    r"(?:le\s+)?domande\s+possono\s+essere\s+presentate\s+da|"
    r"possono\s+(?:presentare\s+(?:domanda|candidatura|istanza|richiesta|progett\w+|propost\w+)|partecipare|candidarsi)"
    r"(?:\s+al(?:l[’'])?\s*(?:bando|avviso))?|"
    r"eligible\s+(?:applicants|participants|entities|organisations|organizations|beneficiaries)|who\s+can\s+apply|"
    r"eligibility\s+(?:criteria|conditions))"
    r"\s*[:.\-–—]?\s*", re.I)
# Dove finisce la voce: la voce successiva della scheda o dell'avviso.
SECTION_STOP = re.compile(
    r"\b(?:obiettiv[oi]|finalit[àa]|oggetto\s+(?:del|dell)|come\s+(?:fare|partecipare)|modalit[àa]\s+(?:di|e)\s|"
    r"scadenz[ae]|termin[ei]\s+(?:di|e|per)\s|dotazione|risorse\s+(?:disponibili|finanziarie)|entit[àa]\s+del|"
    r"spese\s+ammissibili|interventi\s+ammissibili|ambiti?\s+di\s+intervento|documentazione|contatti|allegati|"
    r"criteri\s+di|tempistic\w+|(?-i:Art(?:icolo|\.)\s*\d+)|requisiti\s+(?:dei|del)\s+progett\w+|importo|"
    r"come\s+presentare|presentazione\s+delle\s+domande|per\s+informazioni)\b", re.I)
PUBLIC_BODIES = re.compile(
    r"\b(?:soggetti\s+pubblici|enti\s+pubblici|enti\s+territoriali|pubbliche\s+amministrazioni|"
    r"amministrazioni\s+pubbliche|enti\s+locali\s+territoriali|enti\s+(?:di\s+)?diritto\s+pubblico|"
    r"di\s+diritto\s+pubblico|pubblic[ie]\s+(?:e|o|e/o)\s+privat[ie]|privat[ie]\s+(?:e|o|e/o)\s+pubblic[ie])\b|"
    # Etichetta «Destinatari: Enti» delle schede regionali (enti pubblici).
    r"^\s*enti\b(?!\s+(?:del\s+terzo|privat|non\s+profit|no[\s-]?profit|ecclesiastic|religios|gestori|di\s+formazione|accreditat))",
    re.I)
PUBLIC_EXCLUDED = re.compile(r"\b(?:esclus[ie]\b|non\s+(?:sono\s+ammess[ie]|possono))[^.;]{0,60}\b(?:enti\s+pubblici|soggetti\s+pubblici|comuni|enti\s+locali|pubbliche\s+amministrazioni)\b"
                             # «Non possono partecipare i Comuni che hanno già ottenuto…»: esclude
                             # una parte dei Comuni, non i Comuni come richiedenti.
                             r"(?!\s*,?\s+(?:che|i\s+quali|le\s+quali|gi[àa]|nei\s+quali|in\s+cui|con|aventi|privi|"
                             r"beneficiari|titolari|assegnatari|destinatari|finanziati|ammessi|sopra|sotto|oltre))", re.I)
# Richiedenti limitati agli enti in dissesto o in riequilibrio: non è un'opportunità per i sette Comuni.
DISTRESS_ONLY = re.compile(r"\b(?:in\s+(?:stato\s+di\s+)?dissesto|dissestat\w+|riequilibrio\s+finanziario|"
                           r"strutturalmente\s+deficitari|gestione\s+liquidatoria|organo\s+straordinario\s+di\s+liquidazione)\b", re.I)
# Limiti di popolazione dei Comuni ammessi, letti dalla voce sui destinatari.
_NUMBER = r"(\d{1,3}(?:[.\s’']\d{3})+|\d+)(?!\s*(?:anni|mesi|euro|%|per\s*cento))"
POPULATION_UPPER = re.compile(
    r"(?:popolazion\w*|abitanti)[^.;]{0,30}?(?:massim[ao]\s+(?:di\s+)?|non\s+superior\w+\s+a(?:i|lle)?\s*|"
    r"(?<!non )inferior\w+\s+a(?:i|lle)?\s*|pari\s+o\s+inferior\w+\s+a(?:i|lle)?\s*|fino\s+a(?:i|lle)?\s*|entro\s+i\s*|sotto\s+i\s*|"
    r"meno\s+di\s*|≤\s*|<\s*)" + _NUMBER + r"\s*(?:abitanti|residenti)?|"
    r"\b(?:fino\s+a|meno\s+di|non\s+oltre|sotto\s+i|(?<!non )inferiore\s+a)\s+" + _NUMBER + r"\s+(?:abitanti|residenti)", re.I)
POPULATION_LOWER = re.compile(
    r"(?:popolazion\w*|abitanti)[^.;]{0,30}?(?:(?<!non )superior\w+\s+a(?:i|lle)?\s*|pari\s+o\s+superior\w+\s+a(?:i|lle)?\s*|"
    r"non\s+inferior\w+\s+a(?:i|lle)?\s*|almeno\s*|oltre\s*|più\s+di\s*|≥\s*|>\s*)" + _NUMBER + r"\s*(?:abitanti|residenti)?|"
    r"\b(?:oltre|più\s+di|almeno|(?<!non )superiore\s+a|sopra\s+i)\s+" + _NUMBER + r"\s+(?:abitanti|residenti)", re.I)


def population_limits(text: str) -> tuple[int | None, int | None]:
    """(minimo, massimo) di abitanti richiesti ai Comuni, se la voce li indica."""
    def first(pattern: re.Pattern[str]) -> int | None:
        match = pattern.search(text or "")
        if not match:
            return None
        raw = next(g for g in match.groups() if g)
        value = int(re.sub(r"\D", "", raw))
        # Sotto i 500 non è una soglia demografica (anni, posti, percentuali).
        return value if value >= 500 else None
    return first(POPULATION_LOWER), first(POPULATION_UPPER)


_POPULATIONS: dict[str, int] | None = None


def town_populations() -> dict[str, int]:
    """Residenti dei sette Comuni dall'indicatore pubblicato dall'Osservatorio (Istat)."""
    global _POPULATIONS
    if _POPULATIONS is None:
        import json
        from pathlib import Path
        rows = json.loads((Path(__file__).resolve().parents[1] / "data" / "site-data.json")
                          .read_text(encoding="utf-8"))["metrics"]["population"]["rows"]
        _POPULATIONS = {str(row["town"]): int(row["value"]) for row in rows}
    return _POPULATIONS


def population_eligible(towns: tuple[str, ...], limits: tuple[int | None, int | None],
                        populations: dict[str, int]) -> dict[str, bool]:
    low, high = limits
    return {town: (low is None or populations.get(town, 0) >= low) and (high is None or populations.get(town, 0) <= high)
            for town in towns}
# Il Comune come finanziatore o come sede del progetto altrui: non è un richiedente.
MUNICIPAL_AS_FUNDER = re.compile(
    r"\b(?:finanziator\w*|cofinanzi\w*|patrocin\w*)\b[^.;]{0,100}?\bcomun[ei]\b", re.I)


def beneficiary_sections(text: str) -> list[tuple[str, bool]]:
    """Le voci «Destinatari», «Soggetti ammessi»… di un testo, nell'ordine: (testo, voce debole)."""
    sections = []
    for head in BENEFICIARY_HEAD.finditer(text):
        word = head.group(0)
        # Una voce è un'etichetta («Beneficiari», «Destinatari:») o una frase che
        # dice chi presenta («possono partecipare…»). «beneficiari» in mezzo a una
        # frase («i beneficiari di altri contributi») non è una voce.
        label = word[:1].isupper() or word.rstrip().endswith((":", "-", "–", "—"))
        statement = re.match(r"(?:possono|chi|a\s+chi|soggetti\s+\w+\s+(?:a|alla)\s|domand)", word, re.I)
        if not (label or statement):
            continue
        start = head.end()
        body = text[start:start + 1200]
        stop = next((m.start() for m in SECTION_STOP.finditer(body) if m.start() >= 15), len(body))
        body = body[:stop].strip(" .:;-–—")
        # Le righe dell'indice («Destinatari e partnership ..... 7») non sono voci.
        if re.search(r"(?:\.\s?){6,}|…{2,}", text[start:start + 160]):
            continue
        if len(body) < 8 or OBLIGATION.search(text[max(0, head.start() - 60):head.end()]):
            continue
        subject_after = re.match(r"\s*(?:le|i|gli|l['’]|tutt[ie]|esclusivamente|solo|soltanto|unicamente|anche)\b", body, re.I)
        if head.group(0).lower().startswith("possono") and subject_after:
            # «Possono presentare domanda le associazioni pro-loco…»: decide la frase
            # stessa; le frasi seguenti contano solo se fanno partecipare il Comune.
            end = body.find(". ")
            body = head.group(0) + (body[:end + 400] if end > 0 else body[:300])
        elif head.group(0).lower().startswith("possono"):
            # «I Comuni che intendono… possono presentare»: il soggetto precede il verbo.
            before = text[max(0, head.start() - 200):head.start()]
            cut = max(before.rfind(". "), before.rfind("; "), before.rfind(": "))
            subject = before[cut + 2:] if cut >= 0 else before
            body = subject + head.group(0) + body[:200]
        # «Destinatari» indica a volte il pubblico delle attività (cittadini,
        # scuole), non chi presenta domanda: vale per includere, non per escludere.
        weak = bool(re.match(r"(?:soggetti\s+)?destinatari|a\s+chi", word, re.I))
        sections.append((re.sub(r"\s+", " ", body).strip(), weak))
    return sections


# Regola del proprietario: basta che il Comune possa partecipare in qualche forma
# (richiedente, partner, collaborazione con accordo, adesione). Non partecipa se
# si limita a patrocinare, sostenere, autorizzare o dare un parere.
MUNICIPAL_AS_SUPPORTER = re.compile(
    r"\b(?:sostegno|parere|nulla\s*osta|autorizzazion\w*|patrocin\w*)\b[^.;]{0,60}?\b(?:comun[ei]|enti\s+locali|ente\s+locale|"
    r"amministrazion\w+\s+comunal\w+)\b"
    r"|\b(?:comun[ei]|enti\s+locali|ente\s+locale)\b[^.;]{0,40}?\b(?:pu[òo]|possono|potr\w+)\s+(?:sostener\w*|patrocinar\w*)",
    re.I)
# Il Comune partecipa come collaboratore o partner del progetto.
MUNICIPAL_AS_COLLABORATOR = re.compile(
    r"\b(?:collabor\w*|accord\w*|coinvolg\w*|d['’]\s*intesa|lettera\s+di\s+adesione|adesion\w*|partner\w*|partenariat\w*|"
    r"condivis\w*|co-?progett\w*)\b[^.;]{0,100}?\b(?:comun[ei]|enti\s+locali|ente\s+locale|amministrazion\w+\s+comunal\w+|"
    r"soggett\w+\s+pubblic\w+|enti\s+pubblici)\b"
    r"|\b(?:comun[ei]|enti\s+locali|ente\s+locale)\b[^.;]{0,40}?\b(?:pu[òo]|possono|potr\w+)\s+(?:collaborar\w*|aderir\w*|partecipar\w*)",
    re.I)
# Dopo la prima frase della voce, un Comune conta se il testo lo fa partecipare
# (ammesso, partner, partenariato, consorzio, ATS, collaborazione…).
LATER_ADMISSION = re.compile(
    r"\b(?:ammess\w*|ammissibil\w*|possono\s+(?:altresì\s+|anche\s+)?(?:partecipare|presentare|candidarsi|aggiungersi|"
    r"far\s+parte|essere\s+(?:partner|beneficiari|soggetti|capofila|proponenti))|partenariato|consorzi\w*|aggregazion\w*|"
    r"associazion[ei]\s+temporane\w*|partnership|soggett\w+\s+partner|raggruppament\w*|in\s+forma\s+associata|capofila|co-?beneficiar\w*|partner\s+beneficiar\w*)\b",
    re.I)
# Voce di elenco che inizia con un soggetto pubblico («Altri soggetti pubblici…»).
LIST_ITEM_PUBLIC = re.compile(
    r"\s*(?:[a-z0-9]\)\s*)?(?:altri\s+|altre\s+|gli\s+|i\s+|le\s+)?(?:comuni|unioni\s+(?:dei|di)\s+comuni|enti\s+locali|"
    r"enti\s+pubblici|soggetti\s+pubblici|amministrazioni\s+(?:pubbliche|comunali)|pubbliche\s+amministrazioni|"
    r"enti\s+(?:di\s+)?diritto\s+pubblico|enti\s+territoriali)\b", re.I)
SENTENCE_END = re.compile(r"(?<=[^\W\d]{2}[.!?])\s+(?=[A-ZÀ-Ý«\"(])")


def classify_section(section: str) -> tuple[str, str]:
    """(esito, ruolo) di una voce sui destinatari: municipal | other."""
    cleaned = MUNICIPAL_AS_FUNDER.sub(" ", MUNICIPAL_AS_PLACE.sub(" ", section))
    if PRIVATE_ONLY.search(cleaned) or PUBLIC_EXCLUDED.search(cleaned):
        return "other", ""
    cleaned = MUNICIPAL_AS_SUPPORTER.sub(" ", cleaned)
    # La prima frase è il contenuto della voce; le successive contano solo se
    # fanno partecipare i Comuni o gli enti pubblici (anche come partner).
    first, *rest = SENTENCE_END.split(cleaned.strip(), maxsplit=12) or [""]
    collaborator = False
    if not (MUNICIPAL.search(first) or PUBLIC_BODIES.search(first)):
        clauses = [c for r in rest for c in re.split(r";\s+|\s[-–•]\s", r)]
        kept = [c for c in clauses if LATER_ADMISSION.search(c) or LIST_ITEM_PUBLIC.match(c)]
        helped = [c for c in clauses if c not in kept and MUNICIPAL_AS_COLLABORATOR.search(c)]
        collaborator = bool(helped) and not any(MUNICIPAL.search(c) or PUBLIC_BODIES.search(c) for c in kept)
        cleaned = " ".join([first, *kept, *helped])
    if not (MUNICIPAL.search(cleaned) or PUBLIC_BODIES.search(cleaned)):
        return "other", ""
    if collaborator:
        return "municipal", "partner"
    lead = re.search(r"\b(capofila|proponente|soggetto\s+richiedente|soggetto\s+capofila)\b[^.;]{0,80}\b(comun|ente\s+locale|enti\s+locali|soggett\w+\s+pubblic)", cleaned, re.I)
    role = "partner" if PARTNER.search(cleaned) and not lead and not re.match(r"\s*(?:i\s+|gli\s+|le\s+)?(?:comuni|enti\s+locali|soggetti\s+pubblici)", cleaned, re.I) else "direct_applicant"
    return "municipal", role


def find_beneficiaries(page_text: str, documents: dict[str, str]) -> tuple[str, str, str]:
    """(voce citata, ruolo, esito) dalla scheda del bando o, se manca, dai documenti.

    esito: municipal (Comuni o enti pubblici fra i richiedenti), other (la voce
    esiste e non li comprende), missing (nessuna voce sui destinatari).
    """
    for text in [page_text, *documents.values()]:
        sections = beneficiary_sections(text or "")
        if not sections:
            # «Gli enti locali potranno presentare domanda…»: il testo dice
            # espressamente chi presenta, anche senza una voce dedicata.
            cleaned = MUNICIPAL_AS_PLACE.sub(" ", text or "")
            for match in SUBJECT_APPLIES.finditer(cleaned):
                sentence = _sentence(cleaned, match.start(), match.end())
                if not OBLIGATION.search(sentence):
                    return sentence, "direct_applicant", "municipal"
            continue
        verdicts = [(section, weak, *classify_section(section)) for section, weak in sections[:6]]
        # Una voce che riserva il bando ai privati, o esclude gli enti pubblici, prevale.
        for section, _, _, _ in verdicts:
            probe = MUNICIPAL_AS_PLACE.sub(" ", section)
            if PRIVATE_ONLY.search(probe) or PUBLIC_EXCLUDED.search(probe):
                return _quote(section), "", "other"
        # Decide la prima voce sui richiedenti (soggetti ammessi, beneficiari, chi può…).
        strong = [v for v in verdicts if not v[1]]
        if strong:
            section, _, verdict, role = strong[0]
            return _quote(section), role, verdict
        # Solo voci «Destinatari»: includono se nominano i Comuni, altrimenti non decidono.
        for section, _, verdict, role in verdicts:
            if verdict == "municipal":
                return _quote(section), role, "municipal"
    return "", "", "missing"


def _quote(section: str, limit: int = 320) -> str:
    text = section.strip(" .;:")
    if len(text) > limit:
        cut = max(text.rfind("; ", 0, limit), text.rfind(". ", 0, limit))
        text = text[:cut if cut > 80 else limit].rstrip(" ,;") + "…"
    return text + ("" if text.endswith(("…", ".")) else ".")


PARTNER = re.compile(r"\b(partner|partenariato|in\s+collaborazione\s+con|capofila|consorzi[oa]|associated\s+partner)\b", re.I)
DEADLINE_CUE = re.compile(
    r"(scadenz[ae]|scade|entro\s+(?:e\s+non\s+oltre\s+)?(?:il|le\s+ore)?|termine|fino\s+al|chiusura|"
    r"presentazione\s+delle\s+(?:domande|candidature|proposte)|prorogat\w*|deadline|closing\s+date|until|"
    r"\balle\s+ore\s+[\d.:]+\s+del(?:\s+giorno)?)", re.I)
# Termini che riguardano la domanda, distinti da quelli di esecuzione o di
# rendiconto (lavori, spese, relazioni) che seguono il finanziamento.
SUBMISSION_CUE = re.compile(r"(domand|candidatur|istanz|propost|presentazion|manifestazion|invio\s+delle|iscrizion|"
                            r"adesion|partecipazion|richiest[ae]\s+di|submission|applications?|deadline)", re.I)
EXECUTION_CUE = re.compile(r"(lavori|conclu[sd]|completat|eseguit|rendicont|relazione|impegn|restituir|aggiudicat|appaltat|spes[ae]\b|erogazion|"
                           r"liquidazion|realizzat|ultimat|collaud|certificazion|documentazione|utilizz)", re.I)
OPEN_CUE = re.compile(r"(a\s+partire\s+dal|dal(?:le\s+ore\s+[\d.:]+\s+del)?|apertura|opening\s+date|opens?\s+on)", re.I)
ROLLING = re.compile(r"\b(a\s+sportello|fino\s+ad?\s+esaurimento|senza\s+scadenza|sempre\s+aperto|open\s+until\s+further\s+notice)\b", re.I)
DATE_NUMERIC = re.compile(r"\b(\d{1,2})[/.\-](\d{1,2})[/.\-](20\d{2})\b")
DATE_TEXT = re.compile(r"\b(\d{1,2})(?:°|º|o)?\s+(" + "|".join(MONTHS) + r")\s+(20\d{2})\b", re.I)
DATE_ISO = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")
THEMES = (
    ("istruzione", r"scuol|edilizia scolastica|istruzione|nid[io]|infanzia|studenti|educativ"),
    ("sport", r"\bsport|impiant\w+ sportiv|palestr|piscin"),
    ("ambiente", r"ambient|energ|clima|rifiut|raccolta differenziata|amianto|forest|biodiversit|acqua"),
    ("cultura", r"cultur|bibliotec|lettura|teatr|musei|spettacol|patrimonio"),
    ("sociale", r"social|disabil|minori|famigli|anzian|inclusion|violenza|pari opportunit|povert"),
    ("mobilita", r"mobilit|trasport|ciclabil|parchegg|strad"),
    ("digitale", r"digital|dati|open data|innovazion|ict"),
    ("turismo", r"turism|commerc|centri commerciali naturali|attrattiv"),
    ("territorio", r"sismic|rigenerazion|urban|territori|edifici pubblici|riqualificazion"),
)


@dataclass
class Decision:
    status: str                      # qualified | rejected | expired | unreadable
    reason: str
    applicant: str = ""
    deadline: str | None = None
    deadline_evidence: str = ""
    opens_at: str | None = None
    rolling: bool = False
    role: str = "direct_applicant"
    documents: list[str] = field(default_factory=list)
    population: tuple[int | None, int | None] = (None, None)


def visible_text(payload: str) -> str:
    """Testo leggibile di una pagina HTML, senza menu, script e piè di pagina."""
    if not payload:
        return ""
    if "<" not in payload[:2000]:
        return re.sub(r"\s+", " ", payload).strip()
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(payload, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "form", "svg"]):
            tag.decompose()
        # Il contenitore più ricco, non il primo: molti temi WordPress hanno
        # piccoli <article> di anteprima prima del testo della pagina.
        texts = [node.get_text(" ", strip=True) for node in
                 soup.select("main, article, #main, .main-content, #content, .content, .entry-content")]
        text = max(texts, key=len, default="")
        if len(text) < 500:
            text = (soup.body or soup).get_text(" ", strip=True)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", payload)
    return re.sub(r"\s+", " ", html_lib.unescape(text)).strip()


def _sentence(text: str, start: int, end: int, limit: int = 320) -> str:
    left = max(text.rfind(". ", 0, start), text.rfind("; ", 0, start), start - limit // 2)
    right_candidates = [i for i in (text.find(". ", end), text.find("; ", end)) if i != -1]
    right = min(right_candidates + [end + limit // 2])
    return text[max(0, left + 1):right + 1].strip(" .;") + "."


def _dates(text: str) -> list[tuple[int, date]]:
    found = []
    for match in DATE_NUMERIC.finditer(text):
        day, month, year = map(int, match.groups())
        try:
            found.append((match.start(), date(year, month, day)))
        except ValueError:
            pass
    for match in DATE_TEXT.finditer(text):
        try:
            found.append((match.start(), date(int(match[3]), MONTHS[match[2].lower()], int(match[1]))))
        except ValueError:
            pass
    for match in DATE_ISO.finditer(text):
        try:
            found.append((match.start(), date(int(match[1]), int(match[2]), int(match[3]))))
        except ValueError:
            pass
    return sorted(found)


def find_deadline(text: str, today: date) -> tuple[date | None, str, date | None, bool]:
    """(scadenza, frase, apertura, a sportello). La scadenza è la data più tarda introdotta da una formula di termine."""
    deadlines: list[tuple[date, str]] = []
    openings: list[date] = []
    for position, value in _dates(text):
        window = text[max(0, position - 140):position]
        if DEADLINE_CUE.search(window):
            near = window[-110:]
            # Decide l'indicazione più vicina alla data.
            sub = max((m.end() for m in SUBMISSION_CUE.finditer(near)), default=-1)
            exe = max((m.end() for m in EXECUTION_CUE.finditer(near)), default=-1)
            kind = "generic" if sub == exe == -1 else ("submission" if sub > exe else "execution")
            deadlines.append((value, _sentence(text, position, position + 12), kind))
        elif OPEN_CUE.search(window[-60:]):
            openings.append(value)
    rolling = bool(ROLLING.search(text))
    if not deadlines:
        return None, "", (max(openings) if openings else None), rolling
    # Prima i termini della domanda; i termini di esecuzione non sono mai una scadenza dell'avviso.
    submission = [d for d in deadlines if d[2] == "submission"]
    deadlines = submission or [d for d in deadlines if d[2] == "generic"]
    if not deadlines:
        return None, "", (max(openings) if openings else None), rolling
    future = [d for d in deadlines if d[0] >= today]
    chosen = max(future or deadlines, key=lambda d: d[0])
    upcoming = [o for o in openings if o > today and o <= chosen[0]]
    return chosen[0], chosen[1], (min(upcoming) if upcoming else None), rolling


def find_applicant(text: str, strict: bool = False) -> tuple[str, str]:
    """(frase sui soggetti ammessi che nomina i Comuni, ruolo)."""
    cleaned = MUNICIPAL_AS_PLACE.sub(" ", text)
    pattern = MUNICIPAL_STRICT if strict else MUNICIPAL
    if not strict:
        # «Gli enti locali potranno presentare…»: il soggetto precede il verbo.
        for match in SUBJECT_APPLIES.finditer(cleaned):
            sentence = _sentence(cleaned, match.start(), match.end())
            if not OBLIGATION.search(sentence):
                return sentence, "direct_applicant"
    for head in APPLICANT_HEAD.finditer(cleaned):
        # Nei bandi UE le note a piè di pagina spezzano spesso la frase sui
        # soggetti ammessi; la conferma vera resta EU_LEAD/EU_PARTNER più sotto.
        window = cleaned[head.start():head.start() + (1200 if strict else 700)]
        match = pattern.search(window)
        if not match:
            continue
        absolute = head.start() + match.start()
        sentence = _sentence(cleaned, absolute, absolute + len(match.group(0)))
        if OBLIGATION.search(sentence):
            continue
        if ONLY_OTHERS.search(sentence) and not MUNICIPAL.search(ONLY_OTHERS.split(sentence, 1)[-1][:120]):
            continue
        if strict:
            # Nei topic UE una città citata come contesto non basta: serve che le
            # autorità locali guidino il progetto o vi partecipino espressamente.
            lead = EU_LEAD.search(cleaned)
            if not lead and not EU_PARTNER.search(cleaned):
                continue
            if EU_RESERVED.search(cleaned):
                continue
            role = "direct_applicant" if lead else "partner"
        else:
            role = "partner" if PARTNER.search(sentence) and not re.search(r"\b(capofila|proponente|soggetto\s+richiedente)\b.*\b(comun|ente locale)", sentence, re.I) else "direct_applicant"
        return sentence, role
    return "", "direct_applicant"


def other_region(title: str, applicant: str) -> str | None:
    # «ANCI Lombardia informa…»: è chi rilancia l'avviso, non il territorio ammesso.
    probe = re.sub(r"\bANCI\s+\w+", " ", f"{title} {applicant}")
    for region in REGIONS:
        if re.search(r"\b" + re.escape(region) + r"\b", probe, re.I) and not re.search(r"\btoscan", probe, re.I):
            return region
    if re.search(r"\bcomuni\s+(" + "|".join(REGION_ADJECTIVES) + r")\w*", probe, re.I):
        return "regione diversa dalla Toscana"
    return None


def theme(text: str) -> str:
    for name, pattern in THEMES:
        if re.search(pattern, text, re.I):
            return name
    return "generale"


def qualify(candidate: dict[str, Any], page_text: str, documents: dict[str, str], today: date) -> Decision:
    title = str(candidate.get("title") or "")
    combined = " ".join([page_text, *documents.values()])
    if NOT_A_CALL.search(title):
        return Decision("rejected", "Il titolo indica una notizia, un esito o una comunicazione, non un avviso aperto.")
    if len(combined) < 400:
        return Decision("unreadable", "Pagina e documenti senza testo sufficiente da leggere.")
    # I menu dei siti occupano spesso le prime migliaia di caratteri.
    if not CALL.search(title) and not CALL.search(combined[:6000]):
        return Decision("rejected", "Nessun elemento di avviso o bando nella pagina.")
    if not candidate.get("deadline_at") and not APPLY.search(combined):
        return Decision("rejected", "La pagina non indica come presentare domanda: riparto, adempimento o notizia.")
    if OPERATOR.search(combined):
        return Decision("rejected", "Bando per il gestore di uno strumento di sostegno: i Comuni ne sono destinatari, non richiedenti.")
    if candidate.get("strict_municipal"):
        applicant, role = find_applicant(combined, strict=True)
        if not applicant:
            return Decision("rejected", "I soggetti ammessi non comprendono Comuni o enti locali, oppure non sono indicati.")
    else:
        applicant, role, verdict = find_beneficiaries(page_text, documents)
        if verdict == "missing":
            return Decision("rejected", "Nessuna voce sui destinatari nella scheda né nei documenti: il caso resta in coda.")
        if verdict == "other":
            return Decision("rejected", f"I destinatari indicati dal bando non comprendono Comuni o enti pubblici: «{applicant}»",
                            applicant=applicant)
    region = other_region(title, applicant)
    if region:
        return Decision("rejected", f"Avviso riservato a enti di un'altra regione ({region}).")
    if DISTRESS_ONLY.search(applicant):
        return Decision("rejected", "Riservato a enti in dissesto o in riequilibrio finanziario.", applicant=applicant)
    population = population_limits(applicant)
    if population != (None, None):
        populations = candidate.get("town_populations") or town_populations()
        if not any(population_eligible(tuple(populations), population, populations).values()):
            low, high = population
            bound = " e ".join(x for x in (f"almeno {low}" if low else "", f"al massimo {high}" if high else "") if x)
            return Decision("rejected", f"Limite di popolazione ({bound} abitanti): nessuno dei sette Comuni rientra.",
                            applicant=applicant)
    structured_deadline = candidate.get("deadline_at")
    if structured_deadline:
        deadline, evidence, opens, rolling = date.fromisoformat(str(structured_deadline)[:10]), \
            f"Scadenza indicata dalla fonte ufficiale: {str(structured_deadline)[:10]}.", None, False
        if candidate.get("opens_at") and str(candidate["opens_at"])[:10] > today.isoformat():
            opens = date.fromisoformat(str(candidate["opens_at"])[:10])
    else:
        deadline, evidence, opens, rolling = find_deadline(combined, today)
    if deadline and deadline < today:
        return Decision("expired", f"Termine concluso il {deadline.isoformat()}.", applicant=applicant,
                        deadline=deadline.isoformat(), deadline_evidence=evidence)
    if not deadline and not rolling:
        return Decision("rejected", "Nessuna scadenza futura né modalità a sportello indicata.", applicant=applicant)
    return Decision("qualified", "Avviso aperto con Comuni o enti locali fra i soggetti ammessi.", applicant=applicant,
                    deadline=deadline.isoformat() if deadline else None, deadline_evidence=evidence,
                    opens_at=opens.isoformat() if opens else None, rolling=rolling and not deadline, role=role,
                    documents=list(documents), population=population)


def identity(candidate: dict[str, Any], decision: Decision) -> str:
    key = f"{urlsplit(str(candidate.get('url') or '')).netloc}|{_fold(candidate.get('title'))}|{decision.deadline or 'sportello'}"
    return "auto-" + hashlib.sha256(key.encode()).hexdigest()[:16]


def _years(candidate: dict[str, Any]) -> list[int]:
    probe = f"{candidate.get('title') or ''} {urlsplit(str(candidate.get('url') or '')).path}"
    return [int(y) for y in re.findall(r"(?<!\d)(20[0-3]\d)(?!\d)", probe)]


def _fold(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def build_entry(candidate: dict[str, Any], decision: Decision, today: date, towns: tuple[str, ...]) -> dict[str, Any]:
    title = re.sub(r"\s+", " ", str(candidate.get("title") or "")).strip()
    source_label = candidate.get("source_label") or candidate.get("publisher") or candidate.get("source_id")
    when = (f"scadenza {decision.deadline}" if decision.deadline else "a sportello")
    partner = decision.role == "partner"
    requirements = (
        f"{LABEL}: scheda qualificata automaticamente dal Radar leggendo la fonte ufficiale. "
        f"Soggetti ammessi, dal testo: «{decision.applicant.strip()}»"
        + (f" Termine, dal testo: «{decision.deadline_evidence.strip()}»" if decision.deadline_evidence else "")
        + " Prima di candidarsi verificare requisiti, importi e modalità nell’avviso."
    )
    description = (f"Segnalato da {source_label} ({when}). "
                   + ("Il Comune partecipa come partner. " if partner else "Possono candidarsi Comuni o enti locali. ")
                   + LABEL + ".")
    stage = "announced_upcoming" if decision.opens_at and decision.opens_at > today.isoformat() else (
        "rolling_open" if decision.rolling else "application_open")
    return {
        "coverage_id": identity(candidate, decision),
        "source_id": candidate.get("source_id"),
        "source_label": source_label,
        "publisher": candidate.get("publisher") or source_label,
        "title": title,
        "url": candidate.get("url"),
        "opens_at": decision.opens_at,
        "deadline_at": decision.deadline,
        "lifecycle_stage": stage,
        "description": description,
        "category": theme(f"{title} {decision.applicant}"),
        "municipality_role": "partner" if partner else "direct_applicant",
        "applicant_type": "Comuni o enti locali secondo l’avviso",
        "final_beneficiaries": "Da verificare nell’avviso",
        "geographic_scope": candidate.get("territory") or "Da verificare nell’avviso",
        "project_requirements": requirements,
        "condition_label": LABEL,
        "municipality_status_overrides": _town_statuses(towns, decision, requirements),
    }


def _town_statuses(towns: tuple[str, ...], decision: Decision, requirements: str) -> dict[str, dict[str, str]]:
    if decision.population == (None, None):
        return {town: {"status": "conditional", "reason": requirements} for town in towns}
    populations = town_populations()
    fits = population_eligible(towns, decision.population, populations)
    return {town: ({"status": "conditional", "reason": requirements} if fits[town] else
                   {"status": "not_eligible",
                    "reason": f"Fuori dal limite di popolazione dell’avviso: {populations.get(town, 0)} residenti (Istat)."})
            for town in towns}


# Fonti la cui coda interna contiene notizie di altri territori e non avvisi:
# hanno filtri dedicati e non passano dalla qualificazione automatica.
REVIEW_EXCLUDED_SOURCES = {"ministero-interno-prefetture"}
SOURCE_META_PATH = None  # sostituibile nei test


def _tokens(value: Any) -> set[str]:
    return {t for t in _fold(value).split() if len(t) >= 4 and not t.isdigit() and t not in {"bando", "avviso", "pubblico"}}


def review_candidates(result: dict[str, Any], items: list[dict[str, Any]],
                      source_meta: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Schede della coda interna da leggere come segnalazioni.

    Una scheda già pubblicata con un titolo diverso (curata a mano o da un
    altro corpus) non viene duplicata: se quasi tutte le parole significative
    del titolo in coda compaiono nel titolo pubblicato, si considera la stessa.
    """
    if source_meta is None:
        source_meta = _source_meta()
    published = [(_tokens(x.get("title")), x.get("source_id")) for x in items]
    out = []
    for row in result.get("reviewQueue") or []:
        if row.get("source_id") in REVIEW_EXCLUDED_SOURCES or not row.get("url"):
            continue
        words = _tokens(row.get("title"))
        if words and any(source == row.get("source_id") and len(words & other) / len(words) >= 0.8
                         for other, source in published):
            continue
        meta = source_meta.get(row.get("source_id")) or {}
        out.append({**row, "origin": "review_queue",
                    "source_label": meta.get("publisher") or row.get("source_id"),
                    "publisher": meta.get("publisher"), "territory": meta.get("territory")})
    return out


def _source_meta() -> dict[str, dict[str, Any]]:
    import json
    from pathlib import Path
    path = SOURCE_META_PATH or Path(__file__).resolve().parents[1] / "data" / "opportunity-sources.json"
    try:
        sources = json.loads(Path(path).read_text(encoding="utf-8")).get("sources") or []
    except (OSError, ValueError):
        return {}
    return {s["id"]: s for s in sources if isinstance(s, dict) and s.get("id")}


def apply(result: dict[str, Any], today: date, *, loader: Callable[[str, bool], str] | None,
          previous: dict[str, Any] | None = None, build_item: Callable[..., dict[str, Any]],
          towns: tuple[str, ...], document_links: Callable[[str, str], list[str]] | None = None) -> dict[str, Any]:
    """Qualifica le segnalazioni in coda e pubblica quelle che superano le regole."""
    report: dict[str, Any] = {"version": VERSION, "checked": 0, "qualified": 0, "carried": 0,
                              "rejected": 0, "expired": 0, "unreadable": 0, "deferred": 0, "checks": []}
    result["autoQualification"] = report
    items = result.setdefault("opportunities", [])
    known_urls = {_fold(x.get("url")) for x in items} | {_fold(x.get("discovery_url")) for x in items}
    known_titles = {_fold(x.get("title")) for x in items}
    known_ids = {x.get("coverage_id") for x in items}
    queue = list(result.get("discoveryQueue") or [])
    # Anche le schede delle fonti primarie rimaste in coda interna per mancanza
    # di una regola dedicata passano dalla stessa lettura dei documenti.
    review = review_candidates(result, items)
    queue_urls = {_fold(x.get("url")) for x in queue}
    queue += [x for x in review if _fold(x.get("url")) not in queue_urls]
    lookup = {x.get("url"): x for x in (result.get("reviewDocumentLookup") or [])}
    published_urls: set[str] = set()

    # Le schede qualificate nei giorni precedenti restano fino alla scadenza:
    # una pagina momentaneamente irraggiungibile non le fa sparire.
    # Quando le regole cambiano (VERSION) le schede qualificate con le regole
    # precedenti si rileggono: restano solo se superano le regole attuali. Se
    # la pagina non si legge in questo run, la scheda resta com'era.
    stale: dict[str, dict[str, Any]] = {}
    for old in (previous or {}).get("opportunities") or []:
        if old.get("verification_status") != VERIFICATION_STATUS or old.get("coverage_id") in known_ids:
            continue
        deadline = old.get("deadline_at")
        if deadline and str(deadline) < today.isoformat():
            continue
        source_url = old.get("discovery_url") or old.get("url")
        if old.get("auto_qualification_version") != VERSION and source_url:
            stale[_fold(source_url)] = old
            continue
        items.append(dict(old, is_new=False))
        known_ids.add(old.get("coverage_id"))
        known_urls.add(_fold(old.get("url")))
        report["carried"] += 1
    queue_urls = {_fold(x.get("url")) for x in queue}
    for key, old in stale.items():
        if key not in queue_urls:
            queue.append({"url": old.get("discovery_url") or old.get("url"), "title": old.get("title"),
                          "source_id": old.get("source_id"), "source_label": old.get("source_name"),
                          "deadline_at": old.get("deadline_at"), "origin": "requalify",
                          "discovery_first_seen_at": old.get("first_seen_at")})

    # Le schede verificate dello snapshot precedente (regole e corpora curati)
    # possono essere ricostruite più avanti nella catena: non vanno duplicate.
    for old in (previous or {}).get("opportunities") or []:
        if old.get("verification_status") != VERIFICATION_STATUS:
            known_urls.add(_fold(old.get("url")))
            known_titles.add(_fold(old.get("title")))

    candidates = []
    for candidate in queue:
        if _fold(candidate.get("url")) in known_urls or _fold(candidate.get("title")) in known_titles:
            continue
        if not candidate.get("url"):
            continue
        candidates.append(candidate)
    unique = list({_fold(c.get("url")): c for c in candidates}.values())
    # Decisioni negative recenti: non si rileggono ogni giorno, così la coda
    # avanza e le segnalazioni nuove vengono lette entro un giorno.
    horizon = (today - timedelta(days=RECHECK_DAYS)).isoformat()
    cache = {url: row for url, row in ((previous or {}).get("autoQualificationCache") or {}).items()
             if str(row.get("checkedAt") or "") >= horizon and row.get("reason")}
    result["autoQualificationCache"] = cache
    pending = []
    for candidate in unique:
        row = cache.get(str(candidate.get("url")))
        if row and row.get("status") in {"rejected", "expired"} and _fold(candidate.get("url")) not in stale:
            report["skippedRecent"] = report.get("skippedRecent", 0) + 1
            continue
        pending.append(candidate)
    unique = pending
    # Segnalazioni che citano solo anni ormai chiusi: scartate senza scaricarle.
    fresh = []
    for candidate in unique:
        years = _years(candidate)
        # Nei topic UE l'anno è parte del codice (I3-2024-INV1 può scadere nel
        # 2026): con una scadenza strutturata futura decide la scadenza.
        structured_open = str(candidate.get("deadline_at") or "")[:10] >= today.isoformat()
        if years and max(years) <= today.year - 2 and not structured_open:
            report["checks"].append({"url": candidate.get("url"), "title": candidate.get("title"),
                                     "source_id": candidate.get("source_id"), "status": "rejected",
                                     "reason": f"Avviso riferito al {max(years)}: non più aperto."})
            report["rejected"] += 1
            continue
        fresh.append(candidate)
    # Prima i dati strutturati (nessuno scaricamento), poi le segnalazioni più recenti.
    fresh.sort(key=lambda c: (_fold(c.get("url")) not in stale, not c.get("structured_text"),
                              -(max(_years(c)) if _years(c) else today.year)))
    # I dati strutturati non scaricano nulla: si decidono tutti e non tolgono
    # posto alle segnalazioni da leggere in rete (prima occupavano 97 posti su 120).
    structured = [c for c in fresh if c.get("structured_text")]
    networked = [c for c in fresh if not c.get("structured_text")]
    report["deferred"] = max(0, len(networked) - MAX_CANDIDATES)
    started = time.monotonic()
    selected = structured + networked[:MAX_CANDIDATES]
    for position, candidate in enumerate(selected):
        # Tempo massimo per run: il resto passa al run successivo, in ordine di priorità.
        if (loader is not None and not candidate.get("structured_text")
                and time.monotonic() - started > MAX_SECONDS):
            report["deferred"] += len(selected) - position
            break
        url = str(candidate["url"])
        check: dict[str, Any] = {"url": url, "title": candidate.get("title"), "source_id": candidate.get("source_id")}
        if candidate.get("origin"):
            check["origin"] = candidate["origin"]
        report["checks"].append(check)
        report["checked"] += 1
        page_text, documents = "", {}
        if candidate.get("structured_text"):
            page_text = str(candidate["structured_text"])
        elif loader is not None:
            try:
                # Alcuni segnali puntano direttamente al PDF dell'avviso.
                is_pdf = urlsplit(url).path.lower().endswith(".pdf")
                raw = loader(url, is_pdf)
                if not is_pdf and raw.lstrip().startswith("%PDF"):
                    is_pdf, raw = True, loader(url, True)
                page_text = re.sub(r"\s+", " ", raw) if is_pdf else visible_text(raw)
                links = (document_links(raw, url) if document_links and not is_pdf else [])
                cached = [d.get("url") for d in (lookup.get(url) or {}).get("documents") or [] if d.get("url")]
                for doc_url in list(dict.fromkeys([*links, *cached]))[:MAX_DOCUMENTS]:
                    try:
                        documents[doc_url] = re.sub(r"\s+", " ", loader(doc_url, True))
                    except Exception as exc:  # documento illeggibile: la pagina resta valida
                        check.setdefault("documentErrors", []).append(f"{doc_url}: {exc}")
            except Exception as exc:
                check.update(status="unreadable", reason=f"Pagina non raggiungibile: {exc}")
                report["unreadable"] += 1
                continue
        decision = qualify(candidate, page_text, documents, today)
        check.update(status=decision.status, reason=decision.reason, applicant=decision.applicant,
                     deadline=decision.deadline, documents=decision.documents)
        if not candidate.get("structured_text"):
            cache[url] = {"status": decision.status, "checkedAt": today.isoformat(),
                          "reason": str(decision.reason or "")[:200]}
        if decision.status != "qualified":
            report[decision.status] = report.get(decision.status, 0) + 1
            continue
        entry = build_entry(candidate, decision, today, towns)
        if entry["coverage_id"] in known_ids:
            check["status"] = "duplicate"
            continue
        report["qualified"] += 1
        item = build_item(entry, today, VERIFICATION_STATUS)
        item.update(
            id=entry["coverage_id"], discovery_url=url, auto_qualification_version=VERSION,
            municipal_relevance_class="partner" if entry["municipality_role"] == "partner" else "direct_conditional",
            auto_qualification={"applicant": decision.applicant, "deadline": decision.deadline_evidence,
                                "documents": decision.documents, "checked_at": today.isoformat()},
            first_seen_at=candidate.get("discovery_first_seen_at") or today.isoformat(),
        )
        items.append(item)
        known_ids.add(entry["coverage_id"])
        published_urls.add(url)
        check["coverage_id"] = entry["coverage_id"]
    # Schede da rileggere: senza una decisione in questo run restano com'erano;
    # respinte o scadute con le regole attuali escono dal Radar.
    decided = {_fold(c.get("url")): c.get("status") for c in report["checks"]}
    report["withdrawn"] = 0
    for key, old in stale.items():
        status = decided.get(key)
        if status in {"rejected", "expired"}:
            report["withdrawn"] += 1
            continue
        if status in {"qualified", "duplicate"} or old.get("coverage_id") in known_ids:
            continue
        items.append(dict(old, is_new=False))
        known_ids.add(old.get("coverage_id"))
        report["carried"] += 1
    result["discoveryQueue"] = [x for x in result.get("discoveryQueue") or [] if x.get("url") not in published_urls]
    if "reviewQueue" in result:
        result["reviewQueue"] = [x for x in result["reviewQueue"] if x.get("url") not in published_urls]
    report["fromReviewQueue"] = sum(1 for c in report["checks"] if c.get("origin") == "review_queue")
    counts = result.setdefault("counts", {})
    counts["autoQualified"] = report["qualified"] + report["carried"]
    counts["discoveryReview"] = len(result["discoveryQueue"])
    return result


OFFICIAL_SUFFIXES = (".gov.it", ".governo.it", ".europa.eu", "regione.toscana.it", "anci.it", "ancitoscana.it",
                     "anci.lombardia.it", "anciabruzzo.it", "anciliguria.it", "sviluppo.toscana.it",
                     "fondazionecarilucca.it", "invitalia.it", "gse.it", "cassaddpp.it", "italiadomani.gov.it",
                     "interregeurope.eu", "urbact.eu", "urban-initiative.eu", "interreg-maritime.eu")


def official_host(url: str, page_url: str | None = None) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    if not host or urlsplit(url).scheme != "https":
        return False
    if page_url and host == (urlsplit(page_url).hostname or "").lower():
        return True
    return any(host == s.lstrip(".") or host.endswith(s if s.startswith(".") else "." + s) or host == s
               for s in OFFICIAL_SUFFIXES)


def run_live(result: dict[str, Any], today: date, *, previous: dict[str, Any] | None) -> dict[str, Any]:
    """Collega la qualificazione al trasporto con budget del run giornaliero."""
    import opportunity_discovery_resilient as discovery
    import opportunity_pdf_evidence as pdf
    import run_opportunity_radar_v04 as core
    import tempfile
    from pathlib import Path

    from opportunity_transport_budget import TransportBudget
    main_budget = discovery.LIVE_BUDGET
    # Budget proprio: le letture della qualificazione non consumano la scadenza
    # unica della scansione; il tempo speso le viene restituito alla fine.
    budget = TransportBudget({}, scan_seconds=MAX_SECONDS + 60 if main_budget is not None else 180,
                             journal=(Path(__file__).resolve().parents[1] / "reports/runtime"
                                      if main_budget is not None else Path(tempfile.gettempdir()))
                             / "opportunity-qualifier-progress.jsonl")
    started = time.monotonic()

    def loader(url: str, document: bool) -> str:
        host = urlsplit(url).hostname or ""
        receipt, trace = budget.fetch(url, kind="qualifier_document" if document else "qualifier_page",
                                      timeout=45 if document else 15, attempts=1,
                                      options={"allowedHosts": [host]})
        if receipt is None:
            raise ValueError("; ".join(trace.get("errors") or ["Acquisizione fallita"]))
        return receipt["text"]

    def links(payload: str, page_url: str) -> list[str]:
        return [u for u in pdf.pdf_links(payload, page_url, limit=6) if official_host(u, page_url)]

    try:
        out = apply(result, today, loader=loader, previous=previous, build_item=core.build_seed_item,
                    towns=core.TOWNS, document_links=links)
    finally:
        if main_budget is not None:
            with main_budget.lock:
                main_budget.deadline += time.monotonic() - started
                main_budget.lock.notify_all()
    # Le decisioni lette in rete finiscono nel log del run: gli artefatti non
    # sono sempre scaricabili e i rifiuti vanno verificabili.
    for check in (result.get("autoQualification") or {}).get("checks") or []:
        if check.get("status") in {"qualified", "rejected", "expired", "unreadable"}:
            print(f"QUALIFICA: {check.get('status')} · {check.get('source_id')} · "
                  f"{str(check.get('title') or '')[:90]} · {str(check.get('reason') or '')[:140]}")
    return out


# Fonti che bloccano i server della CI (firewall) e i cui bandi per i Comuni
# arrivano comunque da altre fonti monitorate: il Ministero che emana i decreti
# e l'ANCI che li rilancia. Se il blocco è del sito e almeno una fonte di
# copertura risponde, la fonte non è «da riparare» ma «bloccata e coperta».
COVERED_WHEN_BLOCKED = {
    "gse": ("mase-bandi", "anci-toscana"),
}
BLOCK_CLASSES = {"http_401", "http_403", "http_403_waf", "http_429"}


def _blocked_by_site(state: dict[str, Any]) -> bool:
    classes = set(state.get("failureClasses") or [])
    for endpoint in state.get("endpointResults") or []:
        for key in ("failureClass", "initialFailureClass", "terminalFailureClass"):
            if endpoint.get(key):
                classes.add(endpoint[key])
    return bool(classes) and classes <= BLOCK_CLASSES


def track_silent_zero(result: dict[str, Any], previous: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Giorni consecutivi senza candidati per fonte; elenca quelle da riparare."""
    before = {s.get("sourceId"): s for s in (previous or {}).get("discoverySources") or []}
    status = {s.get("sourceId"): s.get("status") for s in result.get("discoverySources") or []}
    broken, covered = [], []
    for state in result.get("discoverySources") or []:
        if state.get("status") == "deferred":
            state["zeroStreak"] = (before.get(state.get("sourceId")) or {}).get("zeroStreak", 0)
            continue
        zero = bool(state.get("silentZero"))
        state["zeroStreak"] = (int((before.get(state.get("sourceId")) or {}).get("zeroStreak") or 0) + 1) if zero else 0
        empty_page = zero and 0 < int(state.get("listingChars") or 0) < 1500
        backups = [b for b in COVERED_WHEN_BLOCKED.get(state.get("sourceId"), ()) if status.get(b) == "ok"]
        if state.get("status") == "error" and backups and _blocked_by_site(state):
            covered.append({"sourceId": state.get("sourceId"), "coveredBy": backups,
                            "reason": "il sito blocca i server della CI; i suoi bandi per i Comuni arrivano da "
                                      + ", ".join(backups)})
            continue
        if state.get("status") == "error" or empty_page or state["zeroStreak"] >= 14:
            broken.append({"sourceId": state.get("sourceId"), "status": state.get("status"),
                           "zeroStreak": state["zeroStreak"], "listingChars": state.get("listingChars"),
                           "reason": ("fonte in errore" if state.get("status") == "error" else
                                      "pagina quasi vuota: probabilmente generata via JavaScript o cambiata" if empty_page
                                      else f"nessun candidato da {state['zeroStreak']} giorni")})
    result["sourcesToRepair"] = broken
    result["sourcesBlockedCovered"] = covered
    result.setdefault("counts", {})["sourcesToRepair"] = len(broken)
    return broken


def detection_lag(result: dict[str, Any], today: date, threshold_days: int = 7) -> dict[str, Any]:
    """Ritardo fra pubblicazione ufficiale e prima rilevazione del Radar."""
    rows = []
    for item in result.get("opportunities") or []:
        published, seen = item.get("published_at"), item.get("first_seen_at")
        if not published or not seen:
            continue
        try:
            lag = (date.fromisoformat(str(seen)[:10]) - date.fromisoformat(str(published)[:10])).days
        except ValueError:
            continue
        if lag >= 0:
            rows.append({"title": item.get("title"), "url": item.get("url"), "publishedAt": str(published)[:10],
                         "firstSeenAt": str(seen)[:10], "lagDays": lag})
    recent = [r for r in rows if r["firstSeenAt"] >= date.fromordinal(today.toordinal() - 30).isoformat()]
    lags = sorted(r["lagDays"] for r in recent)
    summary = {"thresholdDays": threshold_days, "sample": len(lags),
               "medianDays": (lags[len(lags) // 2] if lags else None),
               "late": [r for r in recent if r["lagDays"] > threshold_days]}
    result["detectionLag"] = summary
    return summary
