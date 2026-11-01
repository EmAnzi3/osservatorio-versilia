#!/usr/bin/env python3
"""DAPHNE 2026: evidenza composita live di due fonti UE primarie.

La call fiche documenta topic e ruolo comunale; il portale Funding & Tenders
documenta la scadenza aggiornata. Non sono ammessi proxy, reader, cache,
redirect cross-host o fallback su documenti storici. Fail closed.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from hashlib import sha256
from io import BytesIO
import re
import unicodedata
from urllib.parse import urlsplit

import requests
from pypdf import PdfReader

PDF_URL = (
    "https://ec.europa.eu/info/funding-tenders/opportunities/docs/"
    "2021-2027/cerv/wp-call/2026/call-fiche_cerv-2026-daphne_en.pdf"
)
TOPICS = {
    "CERV-2026-DAPHNE-CONVENTION-DIR": "convention",
    "CERV-2026-DAPHNE-CHILDREN": "children",
    # Priorità 2 e 3: consorzio con capofila non profit; l'autorità pubblica
    # è raccomandata (beneficiario, partner associato o lettera di supporto).
    "CERV-2026-DAPHNE-PROTECTION": "partner_recommended",
    "CERV-2026-DAPHNE-PREVENTION": "partner_recommended",
}
DEADLINE = date(2026, 11, 5)
MAX_PDF_BYTES = 12 * 1024 * 1024
PAGE_LIMIT = 80


class PrimaryEvidenceError(RuntimeError):
    """Nessuna promozione senza entrambe le prove primarie vive."""


def _official_url(url: str) -> None:
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise PrimaryEvidenceError("Porta URL non valida") from exc
    if (parsed.scheme != "https" or parsed.hostname != "ec.europa.eu"
            or port not in (None, 443) or parsed.username or parsed.password
            or parsed.fragment):
        raise PrimaryEvidenceError("HTTPS/host UE non verificato")


def _fold(value: str) -> str:
    plain = unicodedata.normalize("NFKC", str(value)).replace("\u00ad", "")
    plain = re.sub(r"-\s+", "-", plain)
    return re.sub(r"\s+", " ", plain).casefold().strip()


def validate_pdf_pages(pages: dict[int, str], topic: str) -> list[str]:
    """Le affermazioni sui beneficiari devono essere presenti nella call fiche."""
    if topic not in TOPICS:
        raise PrimaryEvidenceError("Topic DAPHNE non autorizzato")
    intro = _fold(pages.get(3, ""))
    eligibility = _fold(pages.get(31, ""))
    public_authority = _fold(pages.get(32, ""))
    scope = _fold(pages.get(14, ""))
    compact = re.sub(r"[^a-z0-9]", "", intro)
    if re.sub(r"[^a-z0-9]", "", topic.casefold()) not in compact:
        raise PrimaryEvidenceError("Call fiche: topic non attestato a pagina 4")
    if TOPICS[topic] == "convention":
        terms = (
            "for priority 4: lead applicants must be public authorities",
            "at national, regional or local level",
            "for priority 1 and 4, proposals can be submitted",
        )
        texts = (eligibility, eligibility, eligibility)
    elif TOPICS[topic] == "partner_recommended":
        terms = (
            "for priorities 2, 3, and 5, proposals must be submitted by a consortium of at least",
            "the beneficiaries must be public entities or private organisations",
            "for priorities 1, 2, 3 and 5: lead applicants must be non-profit making",
            "for priority 2 and 3: applicants are encouraged to involve a public authority",
        )
        texts = (eligibility, eligibility, eligibility, public_authority)
    else:
        terms = (
            "the participation of a public authority is mandatory under this priority",
            "for priorities 2, 3, and 5, proposals must be submitted by a consortium of at least",
            "for priorities 1, 2, 3 and 5: lead applicants must be non-profit making",
        )
        texts = (scope, eligibility, eligibility)
    missing = [term for term, content in zip(terms, texts) if _fold(term) not in content]
    if missing:
        raise PrimaryEvidenceError("Call fiche: requisiti comunali/consortili assenti: " + "; ".join(missing))
    return list(terms)


def validate_portal_text(body: str, topic: str, deadline: date) -> list[str]:
    """La scadenza deve essere associata alla scheda del topic, non a un altro."""
    if topic not in TOPICS or deadline != DEADLINE:
        raise PrimaryEvidenceError("Topic o scadenza non attesi")
    text = _fold(body)
    key = topic.casefold()
    offsets = [match.start() for match in re.finditer(re.escape(key), text)]
    if not offsets:
        raise PrimaryEvidenceError("Portale UE: topic non trovato")
    deadline_pattern = re.compile(r"deadline\s+date\s*:?\s*0?5\s+november\s+2026\b")
    for offset in offsets:
        nearby = text[offset:offset + 1800]
        if deadline_pattern.search(nearby) and "open for submission" in nearby:
            return [topic, "Deadline date 05 November 2026", "Open For Submission"]
    raise PrimaryEvidenceError("Portale UE: scadenza aggiornata o stato non attestati sul topic")


def fetch_pdf_live(url: str = PDF_URL) -> tuple[dict[int, str], dict]:
    """GET HTTPS originale, senza cookie/cache/proxy e senza seguire redirect."""
    _official_url(url)
    with requests.Session() as session:
        session.trust_env = False
        response = session.get(
            url, allow_redirects=False, stream=True, timeout=(4, 10),
            headers={"Accept": "application/pdf", "Cache-Control": "no-store", "Pragma": "no-cache"},
        )
        try:
            if response.status_code != 200 or response.history or response.url != url:
                raise PrimaryEvidenceError(f"PDF UE: HTTP {response.status_code} o redirect")
            if "pdf" not in str(response.headers.get("Content-Type", "")).casefold():
                raise PrimaryEvidenceError("PDF UE: content-type non documentale")
            chunks, length = [], 0
            for chunk in response.iter_content(chunk_size=65536):
                length += len(chunk)
                if length > MAX_PDF_BYTES:
                    raise PrimaryEvidenceError("PDF UE supera il limite di dimensione")
                chunks.append(chunk)
            data = b"".join(chunks)
        finally:
            response.close()
    if not data.startswith(b"%PDF-") or len(data) < 1000:
        raise PrimaryEvidenceError("PDF UE vuoto o non leggibile")
    try:
        reader = PdfReader(BytesIO(data), strict=False)
        if not 32 <= len(reader.pages) <= PAGE_LIMIT:
            raise PrimaryEvidenceError("PDF UE: numero pagine inatteso")
        pages = {index: reader.pages[index].extract_text() or "" for index in (3, 14, 31, 32)}
    except PrimaryEvidenceError:
        raise
    except Exception as exc:
        raise PrimaryEvidenceError("PDF UE: estrazione non riuscita") from exc
    if any(len(pages[index].strip()) < 200 for index in pages):
        raise PrimaryEvidenceError("PDF UE: testo delle sezioni non leggibile")
    return pages, {
        "url": url, "resolved_url": url, "transport": "direct_https_pdf",
        "proxy_used": False, "sha256": sha256(data).hexdigest(),
        "bytes": len(data), "role": "eligibility_and_topic",
    }


def fetch_portal_live(url: str, topic: str) -> tuple[str, dict]:
    """Chromium con TLS valido, contesto fresco e navigazione solo ec.europa.eu."""
    _official_url(url)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as engine:
        browser = engine.chromium.launch(headless=True, args=["--no-proxy-server", "--disk-cache-size=0"])
        context = browser.new_context(
            locale="en-GB", ignore_https_errors=False, service_workers="block",
            extra_http_headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
        )
        page = context.new_page()
        navigations: list[str] = []

        def watch_navigation(request) -> None:
            if request.is_navigation_request() and request.resource_type == "document":
                navigations.append(request.url)

        page.on("request", watch_navigation)
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=18000)
            if response is None or response.status != 200:
                raise PrimaryEvidenceError("Portale UE: risposta HTTP non verificata")
            _official_url(page.url)
            if any(urlsplit(nav).hostname != "ec.europa.eu" for nav in navigations):
                raise PrimaryEvidenceError("Portale UE: navigazione cross-host")
            try:
                page.wait_for_function(
                    "topic => document.body && document.body.innerText.includes(topic)",
                    arg=topic, timeout=12000,
                )
            except Exception as exc:
                raise PrimaryEvidenceError("Portale UE: topic non reso nel DOM live") from exc
            body = page.locator("body").inner_text(timeout=5000)
            final_url = page.url
            _official_url(final_url)
            if final_url != url:
                raise PrimaryEvidenceError("Portale UE: redirect inatteso")
        finally:
            context.close()
            browser.close()
    if not body or len(body) > 400_000:
        raise PrimaryEvidenceError("Portale UE: body vuoto o inatteso")
    return body, {
        "url": url, "resolved_url": final_url, "transport": "chromium_https",
        "proxy_used": False, "sha256": sha256(body.encode("utf-8")).hexdigest(),
        "role": "current_deadline_and_topic",
    }


def verify_live(entry: dict, today: date) -> dict:
    """Due riscontri obbligatori nello stesso run; nessun fallback persistente."""
    topic = str(entry.get("primary_composite_topic") or "")
    if topic not in TOPICS or entry.get("deadline_at") != DEADLINE.isoformat():
        raise PrimaryEvidenceError("Configurazione topic/scadenza composita non valida")
    if today > DEADLINE:
        raise PrimaryEvidenceError("Scadenza DAPHNE trascorsa")
    url = str(entry.get("url") or "")
    _official_url(url)
    if not url.endswith("/" + topic):
        raise PrimaryEvidenceError("URL del topic diverso dalla call ufficiale")
    pages, pdf_audit = fetch_pdf_live()
    pdf_terms = validate_pdf_pages(pages, topic)
    body, portal_audit = fetch_portal_live(url, topic)
    portal_terms = validate_portal_text(body, topic, DEADLINE)
    for audit, expected_url, expected_transport in (
        (pdf_audit, PDF_URL, "direct_https_pdf"),
        (portal_audit, url, "chromium_https"),
    ):
        if (audit.get("url") != expected_url or audit.get("resolved_url") != expected_url
                or audit.get("transport") != expected_transport
                or audit.get("proxy_used") is not False):
            raise PrimaryEvidenceError("Provenienza composita UE non verificata")
        _official_url(expected_url)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    pdf_audit["required_terms"] = pdf_terms
    portal_audit["required_terms"] = portal_terms
    for audit in (pdf_audit, portal_audit):
        audit["verified_at_utc"] = timestamp
    return {
        "type": "official_primary_composite",
        "method": "eu_daphne_pdf_and_funding_tenders_v1",
        "url": url,
        "resolved_url": portal_audit["resolved_url"],
        "transport": "direct_https_pdf+chromium_https",
        "proxy_used": False, "verified_at": today.isoformat(),
        "evidence_sources": [pdf_audit, portal_audit],
        "required_terms": pdf_terms + portal_terms,
    }
