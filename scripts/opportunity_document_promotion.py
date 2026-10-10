#!/usr/bin/env python3
"""Promote complete MIM school notices, never editorial previews.

The supported contract is the ministerial notice with articles 1/2/3, universal
local-authority applicants and an explicit application window. Other layouts
remain in discovery. There are no notice IDs, annual dates or amounts here.
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

VERSION = "1.1"
HOSTS = {"anci.lombardia.it", "www.anciabruzzo.it", "anciabruzzo.it",
         "www.anci.it", "anci.it", "www.mim.gov.it", "mim.gov.it",
         "www.istruzione.it", "istruzione.it"}
MONTHS = {name: i for i, name in enumerate(
    "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split(), 1)}
MAX_LEADS = 12


def trusted(url: str, hosts=None) -> bool:
    p = urlsplit(url)
    return p.scheme == "https" and p.hostname in (HOSTS if hosts is None else hosts) and not p.username and p.port in (None, 443)


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
    if document:
        if not data.startswith(b"%PDF-"):
            raise ValueError("La risposta non è un PDF")
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        if not 1 <= len(reader.pages) <= 18:
            raise ValueError("PDF incompleto o oltre il limite di pagine")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if len(re.sub(r"\s+", "", text)) < 200:
            raise ValueError("PDF scansionato o testo non estraibile: lettura del documento richiesta")
        if len(text) > 100_000:
            raise ValueError("Testo oltre il limite; nessuna promozione parziale")
    else:
        text = data.decode(charset, errors="replace")
    return {"text": text, "sha256": hashlib.sha256(data).hexdigest(),
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
            receipt, trace = budget.fetch(url, kind="promotion_document" if document else "promotion_page", timeout=15, attempts=1)
            if receipt is None:
                raise ValueError("; ".join(trace.get("errors") or ["Acquisizione fallita"]))
            return receipt
    old = [x for x in (previous or {}).get("opportunities", []) if x.get("document_promotion_version")]
    leads = [x for x in result.get("discoveryQueue", []) if trusted(x.get("url", ""))
             and re.search(r"mim|edilizia scolastica|vulnerabilit[àa].*sismic", x.get("title", ""), re.I)]
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
    unique_leads = list({x["url"]: x for x in leads}.values())
    previous_checks = {c.get("url"): c for c in ((previous or {}).get("documentPromotion") or {}).get("checks") or []}
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
            page = "" if lead.get("document_promotion_version") or direct_pdf else load(url, False)["text"]
            urls = [url] if lead.get("document_promotion_version") or direct_pdf else pdf.pdf_links(page, url, limit=8)
            check["documents"] = [{"url": u, "status": "not_checked" if trusted(u) else "untrusted_host"} for u in urls]
            from opportunity_review_actions import is_administrative_update
            if page and is_administrative_update(page):
                check["status"] = "administrative_update"
                continue
            urls = [u for u in urls if trusted(u)]
            if not urls:
                check["errors"].append("Nessun PDF ministeriale su host consentito")
            for document_url in urls:
                document_check = next(x for x in check["documents"] if x["url"] == document_url)
                try:
                    receipt = load(document_url, True)
                    document_check.update(resolvedUrl=receipt.get("resolvedUrl"), sha256=receipt.get("sha256"))
                    item = parse_notice(receipt, document_url, today)
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
                    break
                except NoticeWindowClosed as exc:
                    document_check.update(status="expired", deadline=exc.deadline)
                except Exception as exc:
                    document_check.update(status="review", error=str(exc))
                    check["errors"].append(str(exc))
            if check["documents"] and all(x["status"] == "expired" for x in check["documents"]):
                check["status"] = "expired"
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
