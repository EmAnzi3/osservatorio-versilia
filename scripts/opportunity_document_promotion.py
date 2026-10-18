#!/usr/bin/env python3
"""Promote complete institutional notices, never editorial previews.

The supported contract is the ministerial notice with articles 1/2/3, universal
local-authority applicants and an explicit application window; CEPELL calls
require the full qualification list and evaluation annex. Other layouts remain
in discovery. There are no notice IDs, annual dates or amounts here.
"""
from __future__ import annotations

import hashlib
import io
import re
import urllib.request
from datetime import date
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from bs4 import BeautifulSoup

import opportunity_pdf_evidence as pdf
import run_opportunity_radar_v04 as core

VERSION = "1.2"
HOSTS = {"anci.lombardia.it", "www.anciabruzzo.it", "anciabruzzo.it",
         "cultura.gov.it", "www.cultura.gov.it", "centroperillibro.cultura.gov.it",
         "www.anci.it", "anci.it", "www.mim.gov.it", "mim.gov.it",
         "www.istruzione.it", "istruzione.it"}
MONTHS = {name: i for i, name in enumerate(
    "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split(), 1)}
MAX_LEADS = 12


def trusted(url: str, hosts=None) -> bool:
    p = urlsplit(url)
    return p.scheme == "https" and p.hostname in (HOSTS if hosts is None else hosts) and not p.username and p.port in (None, 443)


def notice_reference(url):
    """Protocol plus issue date, not a topic/title guess, links ministry copies."""
    name = unquote(urlsplit(url).path.rsplit("/", 1)[-1])
    original = re.search(r"\.0*(\d{5,7})\.(\d{2})-(\d{2})-(\d{4})", name)
    copy = re.search(r"n[. -]*0*(\d{5,7})[ -]+del[ -]+(\d{1,2})[ -]+(\w+)[ -]+(\d{4})", name, re.I)
    try:
        if original:
            protocol, day, month, year = map(int, original.groups())
        elif copy and copy[3].lower() in MONTHS:
            protocol, day, month, year = int(copy[1]), int(copy[2]), MONTHS[copy[3].lower()], int(copy[4])
        else:
            return None
        return protocol, date(year, month, day).isoformat()
    except ValueError:
        return None


def supporting_faq(receipt, item):
    """An authenticated ministry FAQ is supporting evidence, never a new call."""
    if (not receipt.get("document") or receipt.get("transport") != "direct_https"
            or not trusted(receipt.get("resolvedUrl", ""))
            or not re.fullmatch(r"[0-9a-f]{64}", receipt.get("sha256", ""))):
        return False
    raw=re.sub(r"\s+"," ",receipt.get("text","")).strip()
    return bool(item.get("coverage_id","").startswith("mim-document-otto-per-mille-")
                and re.match(r"Ministero dell.istruzione e del merito",raw,re.I)
                and "OTTO PER MILLE" in raw[:1800].upper()
                and re.search(r"\bFAQ\b.*QUESITO\s+N\.?\s*1\b.*RISPOSTA",raw,re.I)
                and "IL DIRIGENTE" in raw
                and not re.search(r"riapertura|proroga|nuova finestra",raw,re.I))



def verified_deadline_extension(receipt: dict, original: dict) -> dict | None:
    """Accept only a signed, directly acquired MIM note tied to a verified call.

    A matching institutional amendment updates the existing card identity;
    it never creates a new funding opportunity or widens admissibility.
    """
    if (not str(original.get("coverage_id") or "").startswith("mim-document-")
            or not receipt.get("document") or receipt.get("transport") != "direct_https"
            or not trusted(receipt.get("resolvedUrl", ""))
            or not re.fullmatch(r"[0-9a-f]{64}", receipt.get("sha256", ""))):
        return None
    raw = re.sub(r"\s+", " ", receipt.get("text") or "").strip()
    if not (re.match(r"Ministero dell[’']istruzione e del merito", raw, re.I)
            and "IL DIRETTORE GENERALE" in raw
            and re.search(r"Oggetto:\s*Proroga del termine di presentazione delle candidature", raw, re.I)
            and re.search(r"Restano ferme tutte le ulteriori disposizioni", raw, re.I)):
        return None
    cited = re.search(r"Avviso pubblico prot\.\s*n\.\s*(\d{5,7})\s+del\s+(\d{1,2})\s+(\w+)\s+(\d{4})", raw, re.I)
    reference = notice_reference(original.get("url", ""))
    if not cited or not reference or cited[3].lower() not in MONTHS:
        return None
    source_protocol = (int(cited[1]), date(int(cited[4]), MONTHS[cited[3].lower()], int(cited[2])).isoformat())
    if source_protocol != reference:
        return None
    origin = re.search(r"originariamente fissato alle ore\s+(\d{1,2})[:.](\d{2})\s+del\s+(\d{1,2})\s+(\w+)\s+(\d{4})", raw, re.I)
    later = re.search(r"(?:è|e[’'])\s+prorogato alle ore\s+(\d{1,2})[:.](\d{2})\s+del\s+(\d{1,2})\s+(\w+)\s+(\d{4})", raw, re.I)
    if not origin or not later:
        return None
    def endpoint(groups):
        hour, minute, day, month, year = groups
        if month.lower() not in MONTHS or not (0 <= int(hour) < 24 and 0 <= int(minute) < 60):
            raise ValueError("Data/orario di proroga non validi")
        return date(int(year), MONTHS[month.lower()], int(day)).isoformat(), f"{int(hour):02}:{int(minute):02}"
    old_date, old_time = endpoint(origin.groups())
    new_date, new_time = endpoint(later.groups())
    if (old_date, old_time) >= (new_date, new_time):
        raise ValueError("La nota non posticipa il termine")
    if (original.get("deadline_at"), original.get("deadline_time")) != (old_date, old_time):
        # A repeated note is idempotent only when its exact signed PDF is known.
        existing = original.get("amendment_evidence") or {}
        if (original.get("deadline_at"), original.get("deadline_time")) == (new_date, new_time) and existing.get("sha256") == receipt["sha256"]:
            return dict(original)
        return None
    item = dict(original)
    item.update(deadline_at=new_date, deadline_time=new_time,
                amendment_evidence={k: v for k, v in receipt.items() if k != "text"})
    item["description"] = re.sub(r"entro il\s+\d{4}-\d{2}-\d{2}\s+alle\s+\d{2}:\d{2}",
                                 f"entro il {new_date} alle {new_time}", item.get("description") or "")
    return item


class _Redirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts=None):
        super().__init__()
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not trusted(newurl, self.hosts):
            raise ValueError("Redirect fuori dalle fonti istituzionali consentite")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_receipt(url: str, *, document: bool, timeout: int = 15, allowed_hosts=None) -> dict:
    """Executed in the shared budget's isolated worker; TLS stays enabled."""
    if not trusted(url, allowed_hosts):
        raise ValueError("Fonte documentale non consentita")
    p = urlsplit(url)
    encoded = urlunsplit((p.scheme, p.netloc, quote(unquote(p.path), safe="/"), p.query, ""))
    request = urllib.request.Request(encoded, headers={"User-Agent": pdf.UA, "Accept": "application/pdf" if document else "text/html"})
    with urllib.request.build_opener(_Redirect(allowed_hosts)).open(request, timeout=timeout) as response:
        resolved = response.geturl()
        if not trusted(resolved, allowed_hosts):
            raise ValueError("Fonte finale non consentita")
        data = response.read(8_000_001 if document else 2_000_001)
        if len(data) > (8_000_000 if document else 2_000_000):
            raise ValueError("Documento oltre il limite di acquisizione")
        # ANCI Lombardia sends charset=utf-8,text/html on some detail pages.
        charset = (response.headers.get_content_charset() or "utf-8").split(",", 1)[0]
    page_metadata = {}
    if document:
        if not data.startswith(b"%PDF-"):
            raise ValueError("La risposta non è un PDF")
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        if not 1 <= len(reader.pages) <= 80:
            raise ValueError("PDF incompleto o oltre il limite di pagine")
        texts = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(texts)
        page_metadata = {"pages":len(texts), "pagesWithoutText":[i+1 for i,t in enumerate(texts) if len(re.sub(r"\s+", "", t)) < 20]}
        if len(re.sub(r"\s+", "", text)) < 200:
            raise ValueError("PDF scansionato o testo non estraibile: lettura del documento richiesta")
        if len(text) > 400_000:
            raise ValueError("Testo oltre il limite; nessuna promozione parziale")
    else:
        text = data.decode(charset, errors="replace")
    return {"text": text, "sha256": hashlib.sha256(data).hexdigest(), **page_metadata,
            "resolvedUrl": resolved, "document": document, "transport": "direct_https"}


def _plain(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    # PDF headers repeat on every page; they are not participation conditions.
    return re.sub(r"Ministero dell[’']Istruzione e del Merito Dipartimento per le risorse, l’organizzazione e l’innovazione digitale Direzione generale per l’edilizia scolastica, le risorse e il supporto alle istituzioni scolastiche", "", text, flags=re.I)


class NoticeWindowClosed(ValueError):
    def __init__(self, deadline):
        super().__init__(f"Finestra ministeriale di candidatura conclusa il {deadline}")
        self.deadline = deadline


def parse_notice(receipt: dict, url: str, today: date) -> dict:
    if not trusted(url) or not trusted(receipt.get("resolvedUrl", "")) or receipt.get("transport") != "direct_https" or not receipt.get("document"):
        raise ValueError("Manca una ricevuta PDF diretta su fonte istituzionale")
    if not re.fullmatch(r"[0-9a-f]{64}", receipt.get("sha256", "")):
        raise ValueError("Manca l'impronta del documento")
    raw = re.sub(r"\s+", " ", receipt["text"]).strip()
    if not re.match(r"Ministero dell[’']Istruzione e del Merito", raw, re.I) or "IL DIRETTORE GENERALE" not in raw:
        raise ValueError("Autore o chiusura del documento ministeriale non verificati")
    text = _plain(raw)
    # Match headings at line starts, not references such as articolo 46-bis.
    sections = re.split(r"^\s*(?:ART\.?|ARTICOLO)\s*(\d+)\s*[–—:\-]\s*", receipt["text"], flags=re.I | re.M)
    sections = [_plain(s) if i % 2 == 0 else s for i, s in enumerate(sections)]
    numbers = [int(sections[i]) for i in range(1, len(sections)-1, 2)]
    if len(numbers) != len(set(numbers)):
        raise ValueError("Articoli ripetuti o documento composto: verifica degli allegati richiesta")
    articles = {int(sections[i]): sections[i + 1] for i in range(1, len(sections)-1, 2)}
    if not all(n in articles for n in (1, 2, 3)):
        raise ValueError("Struttura dell'avviso non supportata")
    pattern = (r"dalle ore\s+([\d\s]{1,4})[.:]([\d\s]{2,3})\s+del\s+(?:giorno\s+)?(\d{1,2})\s+(\w+)\s+(\d{4})"
               r"\s+(?:e\s+)?fino alle ore\s+([\d\s]{1,4})[.:]([\d\s]{2,3})\s+del\s+(?:giorno\s+)?(\d{1,2})\s+(\w+)\s+(\d{4})")
    windows = list(dict.fromkeys(re.findall(pattern, articles[3], re.I)))
    if len(windows) != 1:
        raise ValueError("Finestra di candidatura assente o ambigua")
    values = windows[0]
    def endpoint(offset):
        hour, minute, day, month, year = values[offset:offset+5]
        hour, minute = int(hour.replace(" ", "")), int(minute.replace(" ", ""))
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError("Orario non valido")
        return date(int(year), MONTHS[month.lower()], int(day)), f"{hour:02}:{minute:02}"
    opens, opens_time = endpoint(0)
    closes, closes_time = endpoint(5)
    if closes < opens:
        raise ValueError("Finestra di candidatura non valida")
    if closes < today:
        raise NoticeWindowClosed(closes.isoformat())
    audience = articles[2]
    if re.search(r"\b(?:Abruzzo|Basilicata|Calabria|Campania|Emilia.Romagna|Friuli|Lazio|Liguria|Lombardia|Marche|Molise|Piemonte|Puglia|Sardegna|Sicilia|Toscana|Trentino|Umbria|Valle d.Aosta|Veneto)\b", audience, re.I):
        raise ValueError("Requisiti territoriali specifici da verificare")
    if not re.search(r"Tutti gli Enti locali possono presentare richiesta di finanziamento", audience, re.I):
        raise ValueError("Ammissibilità nazionale degli enti locali non dimostrata")
    if not re.search(r"edifici pubblici ad uso scolastico di propria competenza", audience, re.I):
        raise ValueError("Ruolo comunale e destinazione scolastica non dimostrati")
    # Reject territorial restrictions, even when the universal phrase remains.
    if re.search(r"(?:esclusivamente|soltanto|solo|limitat[oaie])\s+(?:a[il]*\s+)?(?:comuni|enti|territori|region[ei])|residenti|ubicati in|situati in", text, re.I):
        raise ValueError("Limitazione territoriale da verificare")
    header = sections[0].strip()
    if "OTTO PER MILLE" in header.upper():
        family = "otto-per-mille"
        title = "MIM · Otto per mille — interventi urgenti sugli edifici scolastici"
        if "Toscana" not in articles[1] or not all(x in audience.casefold() for x in ("urgenza", "doppio", "nulla osta", "approvat")) or not re.search(r"D\.?I\.?P\.?", audience):
            raise ValueError("Geografia o requisiti dell'otto per mille incompleti")
        conditions = "Edifici pubblici scolastici di competenza dell’ente; nulla osta del proprietario se diverso; progetto almeno a livello DIP approvato; urgenza e indifferibilità motivate; divieto di doppio finanziamento. Verificare tipologie, limiti economici, cofinanziamento e documentazione nell’avviso ministeriale."
    elif "VULNERABILITÀ SISMICA" in header.upper():
        family = "vulnerabilita-sismica"
        title = "MIM · Verifiche di vulnerabilità sismica degli edifici scolastici"
        if not all(x in audience.casefold() for x in ("non sia stata ancora effettuata", "nulla osta", "non deve essere destinataria di altro finanziamento")):
            raise ValueError("Requisiti delle verifiche sismiche incompleti")
        if "postacert.istruzione.it" not in articles[3] or "Sistema Nazionale" not in audience:
            raise ValueError("Canale PEC o requisito anagrafe non dimostrati")
        conditions = "Edifici pubblici scolastici di competenza dell’ente non ancora sottoposti a verifica sismica; nulla osta del proprietario se diverso; edifici censiti nell’anagrafe scolastica; esclusione delle unità già verificate o già migliorate/adeguate; divieto di doppio finanziamento. Verificare numero massimo di edifici, costi parametrici e allegati nell’avviso ministeriale; candidatura tramite PEC."
    else:
        raise ValueError("Famiglia documentale non ancora supportata")
    # Stable across institutional copies; a new window produces a new call.
    identity = hashlib.sha256(f"{header.casefold()}|{opens}|{closes}".encode()).hexdigest()[:16]
    requirements = re.sub(r"^SOGGETTI AMMESSI.*?PARTECIPAZIONE\s*", "", audience, flags=re.I).strip()
    description = f"Enti locali candidabili per edifici pubblici scolastici di propria competenza. Domande dal {opens.isoformat()} alle {opens_time}, entro il {closes.isoformat()} alle {closes_time} (ora italiana). Ammissibilità subordinata ai requisiti dell'avviso allegato; il finanziamento non è garantito."
    entry = {"coverage_id": f"mim-document-{family}-{identity}", "source_id": "mim-enti-locali",
             "source_label": "MIM · Avviso ministeriale", "publisher": "Ministero dell’Istruzione e del Merito",
             "title": title, "url": receipt["resolvedUrl"], "opens_at": opens.isoformat(),
             "deadline_at": closes.isoformat(), "deadline_time": closes_time,
             "lifecycle_stage": "announced_upcoming" if today < opens else "application_open",
             "description": description, "category": "istruzione", "municipality_role": "direct_applicant",
             "applicant_type": "local_authority", "final_beneficiaries": "Comunità scolastica",
             "geographic_scope": "Italia", "project_requirements": conditions,
             "condition_label": "Edificio scolastico di competenza e requisiti dell’avviso",
             "municipality_status_overrides": {town: {"status": "conditional", "reason": description} for town in core.TOWNS}}
    item = core.build_seed_item(entry, today, "live_document_verified")
    item["id"] = entry["coverage_id"]
    item.update(municipal_relevance_class="direct_conditional", document_promotion_version=VERSION,
                document_evidence={k: v for k, v in receipt.items() if k != "text"},
                participation_evidence=requirements, application_instructions=articles[3].strip(), opens_time=opens_time)
    return item


def parse_reading_notice(receipt, url, qualification, criteria, today):
    """CEPELL call plus its complete mandatory annexes; never a news preview."""
    for evidence in (receipt, qualification, criteria):
        if (not evidence.get("document") or evidence.get("transport") != "direct_https"
                or urlsplit(evidence.get("resolvedUrl", "")).hostname != "centroperillibro.cultura.gov.it"
                or not re.fullmatch(r"[0-9a-f]{64}", evidence.get("sha256", ""))):
            raise ValueError("Manca una ricevuta integrale CEPELL per bando e allegati")
    body = "\n".join(line for line in receipt["text"].splitlines() if not re.search(r"\.{3,}", line))
    parts = re.split(r"^\s*Art\.\s*(\d+)\s*[-–—]\s*", body, flags=re.I | re.M)
    numbers = [int(parts[i]) for i in range(1, len(parts)-1, 2)]
    if len(numbers) != len(set(numbers)):
        raise ValueError("Articoli ripetuti o documento composto")
    articles = {int(parts[i]): re.sub(r"\s+", " ", parts[i+1]).strip() for i in range(1,len(parts)-1,2)}
    if not all(n in articles for n in (1,3,4,5,7,8,9,11,14,20)):
        raise ValueError("Struttura del bando CEPELL incompleta")
    headline = re.sub(r"\s+", " ", parts[0])
    edition = re.search(r"BANDO .CITTÀ CHE LEGGE.\s+(\d+)[ªa]?\s+Edizione", headline, re.I)
    audience = re.sub(r"(?<=\d)\s+(?=\d)", "", articles[4])
    cycle = re.search(r"qualifica di .Città che legge.\s*((?:20\d{2}-){2}20\d{2})", audience, re.I)
    if (not edition or not cycle or "IL DIRETTORE" not in receipt["text"]
            or "Allegato B" not in articles[20] or "Allegato A" not in articles[20]
            or "non aver ottenuto finanziamenti" not in audience
            or not re.search(r"Comune non può essere pa\s*rtner", articles[5], re.I)
            or "in corso" not in audience or "costi reali" not in articles[5]):
        raise ValueError("Requisiti e ruolo dei Comuni nel bando CEPELL non dimostrati")
    if ("tutto il territorio nazionale" not in articles[1]
            or "almeno il 51%" not in articles[5]
            or "richiesta di finanziamento inferiore al 50%" not in articles[7]
            or "è volontario" not in articles[7] or "non è volontario" in articles[7]
            or re.search(r"(?:esclusivamente|soltanto|solo|limitati)\s+(?:ai?\s+)?Comuni\s+(?:di|del|della)\b",audience,re.I)):
        raise ValueError("Requisiti territoriali o finanziari del bando CEPELL non supportati")
    windows = re.findall(r"entro e non oltre le ore (\d{1,2}):(\d{2}) del giorno (\d{2})/(\d{2})/(\d{4})", articles[8])
    if len(set(windows)) != 1:
        raise ValueError("Finestra di candidatura assente o ambigua")
    hour, minute, day, month, year = map(int, windows[0])
    if not 0 <= hour < 24 or not 0 <= minute < 60:
        raise ValueError("Orario di candidatura non valido")
    closes = date(year, month, day)
    if closes < today:
        raise NoticeWindowClosed(closes.isoformat())
    qualified = re.sub(r"\s+", " ", qualification["text"])
    if cycle[1] not in qualified or "Elenco definitivo Comuni Qualificati" not in qualified:
        raise ValueError("Elenco dei Comuni qualificati assente o riferito ad altro triennio")
    if qualification.get("pagesWithoutText") != []:
        raise ValueError("PDF scansionato nell’elenco dei Comuni qualificati: pagine senza testo verificabile")
    admitted_body = re.split(r"Elenco Comuni Non Ammessi", qualification["text"], flags=re.I)[0]
    numbered_rows = re.findall(r"(?m)^\s*(\d+)\s+\d{4}\s*-QCL\s*-\d+\s+([^\n]+)", admitted_body)
    rows = [name for number,name in numbered_rows]
    names = {re.sub(r"\s+", " ", n).strip().casefold() for n in rows}
    if not rows or len(rows) != len(names) or [int(n) for n,name in numbered_rows] != list(range(1,len(rows)+1)):
        raise ValueError("Elenco dei Comuni qualificati incompleto o ambiguo")
    if not any(t.casefold() in names for t in core.TOWNS):
        raise ValueError("Nessun Comune della Versilia presente nell’allegato B")
    if not re.search(r"criteri\s+di\s+valutazione", criteria["text"], re.I) or not re.search(r"60\s*\(\s*sessanta\s*\)\s*punti", articles[11]):
        raise ValueError("Criteri e soglia di valutazione non dimostrati")
    conditions = (f"Qualifica Città che legge {cycle[1]} nell’allegato B; nessun finanziamento nell’edizione precedente e nessun altro progetto, convenzione o contributo CEPELL in corso. "
                  "Una sola domanda, singolarmente o in rete di Comuni qualificati; Comune capofila o componente della rete, mai partner. "
                  "Sezione e massimale dipendono dalla popolazione del Comune o dalla somma degli abitanti della rete. "
                  "Richiesta almeno pari al 50% del massimale, almeno 51% del finanziamento al capofila; cofinanziamento volontario. "
                  "Progetto di promozione della lettura, documentazione e registrazione in piattaforma; almeno 60 punti, finanziamento non garantito.")
    identity = f"cepell-citta-che-legge-{edition[1]}-{closes.isoformat()}"
    entry = dict(coverage_id=identity,source_id="mic-generale",source_label="MiC · Centro per il libro e la lettura",
                 publisher="Centro per il libro e la lettura",title=f"Città che legge · {edition[1]}ª edizione — progetti comunali di promozione della lettura",
                 url=receipt["resolvedUrl"],deadline_at=closes.isoformat(),deadline_time=f"{hour:02}:{minute:02}",
                 lifecycle_stage="application_open",category="cultura",municipality_role="direct_applicant",
                 applicant_type="local_authority",final_beneficiaries="Comunità locale e lettori",geographic_scope="Italia",
                 condition_label="Comune qualificato e assenza di finanziamenti CEPELL incompatibili",project_requirements=conditions,
                 description=f"Domanda tramite bandi.cepell.it entro il {closes.isoformat()} alle {hour:02}:{minute:02} (ora italiana). {conditions}",
                 municipality_status_overrides={t:{"status":"conditional" if t.casefold() in names else "not_eligible",
                   "reason":conditions if t.casefold() in names else f"Comune non presente nell’allegato B per la qualifica {cycle[1]}."} for t in core.TOWNS})
    item = core.build_seed_item(entry,today,"live_document_verified")
    item.update(id=identity,municipal_relevance_class="direct_conditional",document_promotion_version=VERSION,
                document_evidence={k:v for k,v in receipt.items() if k!="text"},
                qualification_evidence={k:v for k,v in qualification.items() if k!="text"},
                criteria_evidence={k:v for k,v in criteria.items() if k!="text"},
                participation_evidence=audience,application_instructions=articles[8])
    return item


def apply_promotions(result: dict, today: date, *, previous: dict | None = None, loader=None, live=True) -> dict:
    """Run before final continuity/new-item annotation and ordinary public gates."""
    diagnostic = {"version": VERSION, "added": 0, "revalidated": 0, "archived": 0, "checks": []}
    result["documentPromotion"] = diagnostic
    if not live and loader is None:
        return result
    if loader is None:
        import opportunity_discovery_resilient as discovery
        budget = discovery.LIVE_BUDGET
        if budget is None:
            from opportunity_transport_budget import TransportBudget
            budget = TransportBudget({}, scan_seconds=120)
        def loader(url, document):
            receipt, trace = budget.fetch(url, kind="promotion_document" if document else "promotion_page", timeout=60 if document else 15, attempts=1)
            if receipt is None:
                raise ValueError("; ".join(trace.get("errors") or ["Acquisizione fallita"]))
            return receipt
    old = [x for x in (previous or {}).get("opportunities", []) if x.get("document_promotion_version")]
    leads = [x for x in result.get("discoveryQueue", []) if trusted(x.get("url", ""))
             and re.search(r"mim|edilizia scolastica|vulnerabilit[àa].*sismic|citt[àa] che legge", x.get("title", ""), re.I)]
    items = result.setdefault("opportunities", [])
    seen = {x.get("coverage_id") for x in items}
    existing_urls = {x.get("url") for x in items}
    promoted_urls = set()
    cache = {}
    def load(url, document):
        key = (url, document)
        if key not in cache:
            cache[key] = loader(url, document)
        return cache[key]
    copies = [x["url"] for x in [*items, *old]
              if x.get("document_promotion_version") and trusted(x.get("url", ""))
              and urlsplit(x["url"]).hostname in {"anci.lombardia.it", "www.anciabruzzo.it", "anciabruzzo.it"}]
    def load_document(url):
        alternatives = [u for u in copies if u != url and notice_reference(u) is not None
                        and notice_reference(u) == notice_reference(url)]
        if urlsplit(url).hostname not in {"anci.it", "www.anci.it"}:
            alternatives = []
        errors = []
        for candidate in [*alternatives, url]:
            try:
                receipt = load(candidate, True)
                if candidate != url:
                    # A fresh, complete institutional copy must still pass the
                    # same notice parser. No cached card bypasses verification.
                    parse_notice(receipt, candidate, today)
                return receipt
            except Exception as exc:
                errors.append(str(exc))
        raise ValueError("; ".join(errors))
    unique_leads = list({x["url"]: x for x in leads}.values())
    previous_checks = {c.get("url"): c for c in ((previous or {}).get("documentPromotion") or {}).get("checks") or []}
    previous_links = {x.get("url"):x for x in (previous or {}).get("reviewDocumentLookup") or []}
    # Give deferred and previously unseen notices their turn before retries.
    unique_leads.sort(key=lambda x: 0 if x["url"] not in previous_checks or previous_checks[x["url"]].get("status") == "deferred" else 1)
    for lead in [*old, *unique_leads[:MAX_LEADS]]:
        url = lead["url"]
        check = {"url": url, "title": lead.get("title", ""), "status": "review", "errors": [], "documents": []}
        diagnostic["checks"].append(check)
        if lead in old and date.fromisoformat(lead["deadline_at"]) < today:
            core._append_archive(result, lead)
            diagnostic["archived"] += 1
            check["status"] = "expired"
            continue
        try:
            direct_pdf = bool(re.search(r"\.pdf(?:$|[?#])", url, re.I))
            cached_urls = []
            page = ""
            if not lead.get("document_promotion_version") and not direct_pdf:
                try:
                    page = load(url, False)["text"]
                except Exception as exc:
                    reference = (previous or {}).get("referenceDate")
                    fresh = bool(reference and 0 <= (today-date.fromisoformat(reference)).days <= 1)
                    prior = previous_checks.get(url) or previous_links.get(url) or {}
                    cached_urls = [d["url"] for d in prior.get("documents") or [] if trusted(d.get("url", ""))]
                    if not fresh or not cached_urls:
                        raise
                    check.update(sourcePageFallback="recent_attachment_references",sourcePageError=str(exc))
            urls = [url] if lead.get("document_promotion_version") or direct_pdf else cached_urls or pdf.pdf_links(page, url, limit=8)
            # Qualification/criteria annexes support the call; they are not
            # standalone notices, even when a listing orders them first.
            urls.sort(key=lambda u: bool(urlsplit(u).hostname == "centroperillibro.cultura.gov.it"
                                        and re.search(r"allegato-[ab]-", u, re.I)))
            check["documents"] = [{"url": u, "status": "not_checked" if trusted(u) else "untrusted_host"} for u in urls]
            from opportunity_review_actions import is_administrative_update, assessed_source, reviewed_source
            assessment = (assessed_source(page, url, today.isoformat()) or reviewed_source(page, url)) if page else None
            if assessment and assessment["status"] in {"expired","monitor"}:
                check.update(status="expired" if assessment["status"] == "expired" else "administrative_update",
                             pageAssessment=assessment, deadline=assessment.get("deadline"))
                continue
            if page and is_administrative_update(page):
                check["status"] = "administrative_update"
                continue
            urls = [u for u in urls if trusted(u)]
            if not urls:
                check["errors"].append("Nessun PDF ministeriale su host consentito")
            for document_url in urls:
                document_check = next(x for x in check["documents"] if x["url"] == document_url)
                try:
                    receipt = load_document(document_url)
                    document_check.update(resolvedUrl=receipt.get("resolvedUrl"), sha256=receipt.get("sha256"))
                    # Amendments have no Articles 1–3. Verify the original
                    # protocol, old window, new window and direct signed PDF.
                    amendment = None
                    # The original notice may already be archived. Keep its
                    # stable id and old deadline, so a signed note can close
                    # an existing archival record without manufacturing a new
                    # public call or treating an expired window as reopened.
                    archival_candidates = []
                    for archived in [*(result.get("archive") or []),
                                     *((previous or {}).get("archive") or [])]:
                        identity = str(archived.get("coverage_id") or archived.get("id") or "")
                        if (identity.startswith("mim-document-") and
                                archived.get("source_id") == "mim-enti-locali"):
                            archival_candidates.append(dict(archived, coverage_id=identity))
                    for candidate in [*items, *old, *archival_candidates]:
                        amendment = verified_deadline_extension(receipt, candidate)
                        if amendment is not None:
                            break
                    if amendment is not None:
                        identity = amendment["coverage_id"]
                        current = next((x for x in items if x.get("coverage_id") == identity), None)
                        if current is not None:
                            current.update(amendment)
                        elif amendment["deadline_at"] >= today.isoformat():
                            items.append(amendment)
                            seen.add(identity)
                        else:
                            core._append_archive(result, amendment)
                        archived = next((x for x in result.get("archive") or []
                                         if x.get("coverage_id") == identity), None)
                        if archived is not None:
                            if amendment["deadline_at"] >= today.isoformat():
                                result["archive"] = [x for x in result["archive"]
                                                     if x.get("coverage_id") != identity]
                            else:
                                archived.update(deadline_at=amendment["deadline_at"],
                                                deadline_time=amendment["deadline_time"])
                        check.update(status="published_candidate" if amendment["deadline_at"] >= today.isoformat() else "expired",
                                     coverage_id=identity, deadline=amendment["deadline_at"])
                        document_check.update(status="verified_extension" if amendment["deadline_at"] >= today.isoformat() else "expired",
                                              coverage_id=identity, deadline=amendment["deadline_at"])
                        promoted_urls.add(url)
                        break
                    existing = next((x for x in items if x.get("coverage_id") == check.get("coverage_id")), None)
                    if existing and supporting_faq(receipt,existing):
                        document_check.update(status="verified_support")
                        supplements=existing.setdefault("supplementary_documents",[])
                        if not any(d.get("sha256")==receipt["sha256"] and d.get("resolvedUrl")==receipt["resolvedUrl"] for d in supplements):
                            supplements.append({k:v for k,v in receipt.items() if k!="text"})
                        continue
                    if urlsplit(receipt.get("resolvedUrl", "")).hostname == "centroperillibro.cultura.gov.it":
                        qualification_url = (lead.get("qualification_evidence") or {}).get("resolvedUrl") or next((u for u in urls if re.search(r"allegato-b-", u, re.I)), None)
                        criteria_url = (lead.get("criteria_evidence") or {}).get("resolvedUrl") or next((u for u in urls if re.search(r"allegato-a-", u, re.I)), None)
                        if not qualification_url or not criteria_url:
                            raise ValueError("Allegati obbligatori del bando CEPELL non individuati")
                        qualification = load(qualification_url, True)
                        if qualification.get("pagesWithoutText"):
                            for support in check["documents"]:
                                if support["url"] == qualification_url:
                                    support.update(status="review",error="PDF scansionato: pagine senza testo nell’elenco dei Comuni qualificati")
                        item = parse_reading_notice(receipt, document_url, qualification, load(criteria_url, True), today)
                        for support_url,evidence in ((qualification_url,item["qualification_evidence"]),(criteria_url,item["criteria_evidence"])):
                            support_check=next(d for d in check["documents"] if d["url"] == support_url) if not lead.get("document_promotion_version") else None
                            if support_check is not None:
                                support_check.update(status="verified_support",resolvedUrl=evidence["resolvedUrl"],sha256=evidence["sha256"])
                    else:
                        item = parse_notice(receipt, document_url, today)
                    if receipt.get("resolvedUrl") != document_url:
                        document_check.update(originalUrl=document_url, url=receipt["resolvedUrl"])
                    if date.fromisoformat(item["deadline_at"]) < today:
                        document_check.update(status="expired", deadline=item["deadline_at"])
                        continue
                    if item["coverage_id"] not in seen and item["url"] not in existing_urls:
                        item["discovery_url"] = lead.get("discovery_url") or url
                        items.append(item)
                        seen.add(item["coverage_id"])
                        existing_urls.add(item["url"])
                        diagnostic["revalidated" if lead.get("document_promotion_version") else "added"] += 1
                    check.update(status="published_candidate", coverage_id=item["coverage_id"])
                    document_check.update(status="verified", coverage_id=item["coverage_id"], deadline=item["deadline_at"])
                    promoted_urls.add(url)
                    # CEPELL's required annexes were already completely read.
                    if item.get("qualification_evidence"):
                        break
                except NoticeWindowClosed as exc:
                    document_check.update(status="expired", deadline=exc.deadline)
                except Exception as exc:
                    document_check.update(status="review", error=str(exc))
                    check["errors"].append(str(exc))
            if check["documents"] and all(x["status"] == "expired" for x in check["documents"]):
                check["status"] = "expired"
            if check["errors"] and check.get("status") == "published_candidate":
                check["status"] = "review"
                promoted_urls.discard(url)
        except Exception as exc:
            check["errors"].append(str(exc))
    for lead in unique_leads[MAX_LEADS:]:
        diagnostic["checks"].append({"url": lead["url"], "title": lead.get("title", ""), "status": "deferred",
                                     "errors": ["Limite documentale del run raggiunto"], "documents": []})
    result["discoveryQueue"] = [x for x in result.get("discoveryQueue", []) if x.get("url") not in promoted_urls]
    core._recompute_v04_counts(result)
    result.setdefault("counts", {})["discoveryReview"] = len(result["discoveryQueue"])
    result.setdefault("counts", {})["documentAutomaticallyAdded"] = diagnostic["added"]
    return result
