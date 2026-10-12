#!/usr/bin/env python3
"""Conservative exclusions for discovery leads, never publication decisions."""
from __future__ import annotations

import re
from datetime import date
from urllib.parse import unquote, urlsplit

GENERIC = re.compile(
    r"^(?:aggiornamenti da .+|navigazione(?: principale)?|main navigation|footer\b.*|"
    r"menu bottom|briciole di pane|breadcrumb|cerca nel sito|sezione link utili|"
    r"seguici su|siti collegati|non hai trovato quello che cerchi\?|"
    r"identità e loghi|guide e risorse|notizie|latest news|related content|"
    r"bandi e avvisi(?: pubblici)?|avvisi e bandi|archivio bandi|calls? for proposals|"
    r"amministrazione trasparente|organizzazione|lista dei comunicati|"
    r"ultime comunicazioni|ultimi aggiornamenti per i comuni|big picture|"
    r"bonus e contributi attivi|prefetture - ministero dell.interno|"
    r"osservatorio sulla finanza e la contabilità degli enti locali|"
    r"strong interreg, strong regions, strong europe|"
    r"come mettersi in comunicazione con il ministero .+)$", re.I)
REOPENING = re.compile(r"prorog\w*|riapert\w*|nuova\s+finestra|"
                      r"(?:presentare|inviare)\s+(?:le\s+)?(?:domande|candidature)|"
                      r"(?:aperto|apertura)\s+(?:il\s+|del\s+)?bando", re.I)


def classify_signal(item, reference_date=None):
    title = re.sub(r"\s+", " ", str(item.get("title") or "")).strip()
    location = urlsplit(str(item.get("url") or ""))
    path = unquote(location.path).casefold().rstrip("/")
    context = title + " " + str(item.get("summary") or "")
    if title.casefold() == "call for proposals" and path not in {
        "/en/activities/digital-programme", "/en/activities/get-funding-digital"}:
        return None
    if GENERIC.fullmatch(title):
        return "catalog_or_navigation"
    # Never derive expiry from a decree year or a multi-year programme.
    # Only an explicitly archived route or matching annual archive heading
    # qualifies; a reopening or a still-current structured deadline wins.
    if REOPENING.search(context):
        return None
    reference = str(reference_date or date.today().isoformat())
    deadline = str(item.get("deadline_at") or "")
    current_window = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", deadline) and deadline >= reference)
    if current_window:
        return None
    edition = re.fullmatch(r"Avviso\s+(20\d{2})", title, re.I)
    outcome = re.search(r"chiusura\s+(?:dell[’']?\s*)?avviso|"
                        r"elenco\s+degli\s+eventi\s+ammessi\s+(?:al\s+|a\s+)?contributo", context, re.I)
    if not current_window and (
        (edition and outcome and location.hostname == "www.sport.governo.it"
         and int(edition[1]) < int(reference[:4]) and path.endswith("/avviso-" + edition[1]))
        or (location.hostname == "spettacolo.cultura.gov.it" and path in {
            "/tax-credit-musica-old", "/tax-credit-musica-old-old"})
    ):
        return "archive_page"
    if location.hostname == "prefettura.interno.gov.it":
        if "/amministrazione-trasparente/bandi-gara-e-contratti/" in path:
            return "procurement_notice"
        if re.search(r"\b(?:riunione|visita|firmati.*patti|sigla.*(?:patti|protocolli)|"
                     r"terminata.*istruttoria|graduatoria definitiva)\b", title, re.I):
            return "administrative_update"
    if (location.hostname == "www.interregeurope.eu" and "/news-events/events/" in path
            and re.search(r"\bstrong regions\b.*\bstrong europe\b", title, re.I)):
        return "informational_event"
    from opportunity_review_actions import is_administrative_update
    if is_administrative_update(title, str(item.get("url") or "")):
        return "administrative_update"
    return None


def content_html(payload):
    """Remove site chrome, retaining article headers and actual attachments."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(payload or "", "html.parser")
    for element in list(soup.select("nav, [role=navigation], [role=contentinfo], "
                                    ".site-header, .site-footer, "
                                    ".elementor-location-header, .elementor-location-footer")):
        if element.parent is not None:
            element.decompose()
    for element in list(soup.find_all(["header", "footer"])):
        if element.find_parent(["main", "article"]) is None:
            element.decompose()
    return str(soup)


def unrelated_document(url):
    name = unquote(urlsplit(str(url)).path.rsplit("/", 1)[-1]).casefold()
    if re.search(r"(?:bando|avviso|allegat|domanda)", name):
        return False
    return bool(re.search(r"statuto.*anci|anci.*statuto|privacy[-_ ]?policy|"
                          r"cookie[-_ ]?policy|dichiarazione[-_ ].*accessibilit", name))


def clean_review_queues(payload, reference_date):
    """Retain exclusions with reasons; remove them before document budgets."""
    discarded = { (x.get("url"), x.get("title"), x.get("reasonCode")): x
                  for x in payload.get("discoveryNoise") or [] }
    for field in ("discoveryQueue", "reviewQueue"):
        kept = []
        for item in payload.get(field) or []:
            reason = classify_signal(item, reference_date)
            if reason:
                row = {"url": item.get("url"), "title": item.get("title"),
                       "source_id": item.get("source_id"), "reasonCode": reason,
                       "summary": item.get("summary", ""), "deadline_at": item.get("deadline_at", "")}
                discarded[(row["url"], row["title"], reason)] = row
            else:
                kept.append(item)
        if field in payload:
            payload[field] = kept
    payload["discoveryNoise"] = list(discarded.values())
    payload.setdefault("counts", {})["discoveryReview"] = len(payload.get("discoveryQueue") or [])
    if "reviewQueue" in payload:
        payload["counts"]["reviewInternal"] = len(payload["reviewQueue"])
    payload["counts"]["discoveryNoiseDiscarded"] = len(discarded)
    return payload
