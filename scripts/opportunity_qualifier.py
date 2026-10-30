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
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable
from urllib.parse import urlsplit

VERSION = "1.0"
LABEL = "Requisiti da confermare"
VERIFICATION_STATUS = "auto_qualified"
MAX_CANDIDATES = 40
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
    r"\b(graduatori[ae]|esit[oi]|vincitor[ie]|ammess[ie] a finanziamento|elenco (?:dei |degli )?(?:beneficiari|ammessi)|"
    r"approvazione (?:della |delle )?graduatori|chiariment[oi]|faq|orari|video|convegno|webinar|seminario|"
    r"seduta di gara|appalto|affidamento|rendicontazion[ei]|erogazion[ei]|liquidazion[ei]|riparto|ripartizion[ei]|"
    r"decreto di assegnazione|comunicato stampa|intervista|news in evidenza|"
    r"assunzion[ei]|concorso pubblico|selezione di personale|incarico|nomina|protocollo d.intesa|tasso annuo|"
    r"capitalizzazione|front office|description|who can apply|get support|work with us|come to our)\b", re.I)
APPLICANT_HEAD = re.compile(
    r"(soggetti\s+(?:beneficiari|ammessi|ammissibili|destinatari|proponenti|richiedenti|candidabili)|"
    r"beneficiari|destinatari|possono\s+(?:presentare|partecipare|candidarsi|accedere)|"
    r"chi\s+pu[oò]\s+(?:partecipare|presentare|candidarsi)|requisiti\s+di\s+(?:ammissibilit|partecipazione)|"
    r"sono\s+ammess[ie]|who\s+can\s+apply|eligible\s+(?:applicants|participants|entities|organisations|organizations)|"
    r"eligibility(?:\s+criteria)?|admissibility)", re.I)
MUNICIPAL = re.compile(
    r"\b(comun[ei]|enti\s+locali|ente\s+locale|amministrazion[ei]\s+comunal[ei]|unioni?\s+(?:dei|di)\s+comuni|"
    r"citt[àa]\s+metropolitan[ae]|local\s+(?:and\s+regional\s+)?authorit(?:y|ies)|municipalit(?:y|ies)|"
    r"public\s+(?:bodies|authorit(?:y|ies))|local\s+governments?|towns?|cities)\b", re.I)
# Per i programmi UE «public bodies» comprende anche università e agenzie: serve
# una menzione esplicita di autorità locali, Comuni o città.
MUNICIPAL_STRICT = re.compile(
    r"\b(local\s+(?:and\s+regional\s+)?authorit(?:y|ies)|municipalit(?:y|ies)|local\s+governments?|"
    r"cities|towns?|comun[ei]|enti\s+locali)\b", re.I)
# Il Comune come luogo, non come soggetto: «con sede nel Comune di», «residenti nel comune».
MUNICIPAL_AS_PLACE = re.compile(
    r"(sede(?:\s+legale|\s+operativa)?\s+(?:nel|in\s+un|in)\s+comune|residen\w*\s+(?:nel|in)\s+(?:un\s+)?comune|"
    r"ubicat\w+\s+(?:nel|in)\s+(?:un\s+)?comune|nel\s+territorio\s+(?:del|di\s+un)\s+comune)", re.I)
ONLY_OTHERS = re.compile(
    r"\b(esclusivamente|solo|soltanto|unicamente)\s+(?:a(?:lle|gli|i)?\s+)?(imprese|associazioni|cittadini|persone\s+fisiche|"
    r"studenti|scuole|universit|enti\s+del\s+terzo\s+settore|organizzazioni)", re.I)
PARTNER = re.compile(r"\b(partner|partenariato|in\s+collaborazione\s+con|capofila|consorzi[oa]|associated\s+partner)\b", re.I)
DEADLINE_CUE = re.compile(
    r"(scadenz[ae]|scade|entro\s+(?:e\s+non\s+oltre\s+)?(?:il|le\s+ore)?|termine|fino\s+al|chiusura|"
    r"presentazione\s+delle\s+(?:domande|candidature|proposte)|prorogat\w*|deadline|closing\s+date|until)", re.I)
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
        root = soup.select_one("main, article, #main, .main-content, #content, .content") or soup.body or soup
        text = root.get_text(" ", strip=True)
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
            deadlines.append((value, _sentence(text, position, position + 12)))
        elif OPEN_CUE.search(window[-60:]):
            openings.append(value)
    rolling = bool(ROLLING.search(text))
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
    for head in APPLICANT_HEAD.finditer(cleaned):
        window = cleaned[head.start():head.start() + 700]
        match = pattern.search(window)
        if not match:
            continue
        absolute = head.start() + match.start()
        sentence = _sentence(cleaned, absolute, absolute + len(match.group(0)))
        if ONLY_OTHERS.search(sentence) and not MUNICIPAL.search(ONLY_OTHERS.split(sentence, 1)[-1][:120]):
            continue
        role = "partner" if PARTNER.search(sentence) and not re.search(r"\b(capofila|proponente|soggetto\s+richiedente)\b.*\b(comun|ente locale)", sentence, re.I) else "direct_applicant"
        return sentence, role
    return "", "direct_applicant"


def other_region(title: str, applicant: str) -> str | None:
    probe = f"{title} {applicant}"
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
    if not CALL.search(title) and not CALL.search(combined[:1500]):
        return Decision("rejected", "Nessun elemento di avviso o bando nella pagina.")
    if len(combined) < 400:
        return Decision("unreadable", "Pagina e documenti senza testo sufficiente da leggere.")
    applicant, role = find_applicant(combined, strict=bool(candidate.get("strict_municipal")))
    if not applicant:
        return Decision("rejected", "I soggetti ammessi non comprendono Comuni o enti locali, oppure non sono indicati.")
    region = other_region(title, applicant)
    if region:
        return Decision("rejected", f"Avviso riservato a enti di un'altra regione ({region}).")
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
                    documents=list(documents))


def identity(candidate: dict[str, Any], decision: Decision) -> str:
    key = f"{urlsplit(str(candidate.get('url') or '')).netloc}|{_fold(candidate.get('title'))}|{decision.deadline or 'sportello'}"
    return "auto-" + hashlib.sha256(key.encode()).hexdigest()[:16]


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
        "municipality_status_overrides": {town: {"status": "conditional", "reason": requirements} for town in towns},
    }


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
    lookup = {x.get("url"): x for x in (result.get("reviewDocumentLookup") or [])}
    published_urls: set[str] = set()

    # Le schede qualificate nei giorni precedenti restano fino alla scadenza:
    # una pagina momentaneamente irraggiungibile non le fa sparire.
    for old in (previous or {}).get("opportunities") or []:
        if old.get("verification_status") != VERIFICATION_STATUS or old.get("coverage_id") in known_ids:
            continue
        deadline = old.get("deadline_at")
        if deadline and str(deadline) < today.isoformat():
            continue
        items.append(dict(old, is_new=False))
        known_ids.add(old.get("coverage_id"))
        known_urls.add(_fold(old.get("url")))
        report["carried"] += 1

    candidates = []
    for candidate in queue:
        if _fold(candidate.get("url")) in known_urls or _fold(candidate.get("title")) in known_titles:
            continue
        if not candidate.get("url"):
            continue
        candidates.append(candidate)
    unique = list({_fold(c.get("url")): c for c in candidates}.values())
    for candidate in unique[:MAX_CANDIDATES]:
        url = str(candidate["url"])
        check: dict[str, Any] = {"url": url, "title": candidate.get("title"), "source_id": candidate.get("source_id")}
        report["checks"].append(check)
        report["checked"] += 1
        page_text, documents = "", {}
        if candidate.get("structured_text"):
            page_text = str(candidate["structured_text"])
        elif loader is not None:
            try:
                raw = loader(url, False)
                page_text = visible_text(raw)
                links = (document_links(raw, url) if document_links else [])
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
    report["deferred"] = max(0, len(unique) - MAX_CANDIDATES)
    result["discoveryQueue"] = [x for x in queue if x.get("url") not in published_urls]
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
    budget = discovery.LIVE_BUDGET
    if budget is None:
        from opportunity_transport_budget import TransportBudget
        budget = TransportBudget({}, scan_seconds=180)

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

    return apply(result, today, loader=loader, previous=previous, build_item=core.build_seed_item,
                 towns=core.TOWNS, document_links=links)


def track_silent_zero(result: dict[str, Any], previous: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Giorni consecutivi senza candidati per fonte; elenca quelle da riparare."""
    before = {s.get("sourceId"): s for s in (previous or {}).get("discoverySources") or []}
    broken = []
    for state in result.get("discoverySources") or []:
        if state.get("status") == "deferred":
            state["zeroStreak"] = (before.get(state.get("sourceId")) or {}).get("zeroStreak", 0)
            continue
        zero = bool(state.get("silentZero"))
        state["zeroStreak"] = (int((before.get(state.get("sourceId")) or {}).get("zeroStreak") or 0) + 1) if zero else 0
        empty_page = zero and 0 < int(state.get("listingChars") or 0) < 1500
        if state.get("status") == "error" or empty_page or state["zeroStreak"] >= 14:
            broken.append({"sourceId": state.get("sourceId"), "status": state.get("status"),
                           "zeroStreak": state["zeroStreak"], "listingChars": state.get("listingChars"),
                           "reason": ("fonte in errore" if state.get("status") == "error" else
                                      "pagina quasi vuota: probabilmente generata via JavaScript o cambiata" if empty_page
                                      else f"nessun candidato da {state['zeroStreak']} giorni")})
    result["sourcesToRepair"] = broken
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
