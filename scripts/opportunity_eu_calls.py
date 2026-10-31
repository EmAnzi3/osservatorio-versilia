#!/usr/bin/env python3
"""Bandi UE dall'interfaccia di ricerca ufficiale del portale Funding & Tenders.

La pagina «topic-search» del portale si riempie solo con JavaScript: scaricata
come HTML è vuota, e per mesi il Radar l'ha segnata «ok» con zero bandi (così
sono sfuggiti per esempio i due inviti CERV-DAPHNE aperti a luglio 2026). Qui si
usa invece l'interfaccia di ricerca che alimenta il portale stesso
(api.tech.ec.europa.eu, chiave pubblica «SEDIA»), che restituisce in forma
strutturata tutti i topic aperti o in arrivo di CERV, LIFE, Horizon, Erasmus+,
CEF, Digital Europe e degli altri programmi a gestione diretta.

Per ogni topic si legge la scheda pubblica in JSON (topicDetails) con
descrizione e condizioni: il testo passa alla qualificazione automatica, che
pubblica solo i topic in cui le autorità locali o pubbliche sono fra i
richiedenti ammessi.
"""
from __future__ import annotations

import json
import re
import ssl
import urllib.request
import uuid
from datetime import date
from typing import Any, Callable

SEARCH_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
DETAILS_URL = "https://ec.europa.eu/info/funding-tenders/opportunities/data/topicDetails/{}.json"
TOPIC_URL = "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/{}"
STATUS_FORTHCOMING = "31094501"
STATUS_OPEN = "31094502"
# Programmi in cui Comuni ed enti locali possono essere richiedenti o partner.
# Ricerca di base, difesa, aiuti esterni e Euratom restano fuori: i loro topic
# citano le città come oggetto di studio, non come richiedenti.
PROGRAMME_PREFIXES = ("CERV", "LIFE", "ERASMUS", "CREA", "EU4H", "AMIF", "ISF", "ESF", "SOCPL", "CEF", "DIGITAL",
                      "SMP", "I3", "HORIZON-MISS", "EUCF", "EUI", "INTERREG", "URBACT", "JUST", "BMVI", "EMFAF")
MAX_PAGES = 20
USER_AGENT = "OsservatorioVersilia-Radar/1.0 (+https://osservatorioversilia.it/opportunita/)"
PAGE_SIZE = 100


def _post_multipart(url: str, fields: dict[str, str], timeout: int) -> bytes:
    boundary = uuid.uuid4().hex
    body = b"".join(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\nContent-Type: application/json\r\n\r\n{value}\r\n".encode()
        for name, value in fields.items()) + f"--{boundary}--\r\n".encode()
    request = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": USER_AGENT,
        "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
        return response.read(20_000_001)


def _get(url: str, timeout: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
        return response.read(5_000_001)


def search(text: str, *, timeout: int = 30, poster: Callable[..., bytes] = _post_multipart,
           page: int = 1) -> list[dict[str, Any]]:
    query = {"bool": {"must": [
        {"terms": {"type": ["1", "2", "8"]}},
        {"terms": {"status": [STATUS_FORTHCOMING, STATUS_OPEN]}},
    ]}}
    url = f"{SEARCH_URL}?apiKey=SEDIA&text={urllib.request.quote(text)}&pageSize={PAGE_SIZE}&pageNumber={page}"
    payload = json.loads(poster(url, {"query": json.dumps(query), "languages": json.dumps(["en"]),
                                      "sort": json.dumps({"order": "DESC", "field": "startDate"})}, timeout))
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("Risposta della ricerca UE senza elenco dei risultati")
    return results


def _first(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    if isinstance(value, list):
        value = value[0] if value else None
    return str(value) if value not in (None, "") else None


def _date(value: str | None) -> str | None:
    if not value:
        return None
    match = re.match(r"(\d{4}-\d{2}-\d{2})", value)
    return match.group(1) if match else None


def topic(result: dict[str, Any]) -> dict[str, Any] | None:
    metadata = result.get("metadata") or {}
    identifier = _first(metadata, "identifier") or _first(metadata, "callccm2Id")
    if not identifier:
        return None
    deadlines = [d for d in (_date(x) for x in (metadata.get("deadlineDate") or [])) if d]
    return {
        "identifier": identifier,
        "title": _first(metadata, "title") or result.get("title") or identifier,
        "call": _first(metadata, "callTitle") or _first(metadata, "callIdentifier"),
        "status": _first(metadata, "status"),
        "opens_at": _date(_first(metadata, "startDate")),
        "deadline_at": max(deadlines) if deadlines else None,
        "summary": re.sub(r"<[^>]+>", " ", str(result.get("summary") or result.get("content") or ""))[:800],
        "url": str(result.get("url") or "") if "/portal/screen/" in str(result.get("url") or "") else None,
    }


def _plain(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def details(identifier: str, *, timeout: int = 20, getter: Callable[..., bytes] = _get) -> tuple[str, list[str]]:
    """Descrizione del topic e link ai documenti della call (la scheda JSON non riporta i richiedenti ammessi)."""
    payload = json.loads(getter(DETAILS_URL.format(identifier.lower()), timeout))
    data = payload.get("TopicDetails") or payload
    text = _plain(" ".join(str(data.get(k) or "") for k in ("title", "description")))
    blob = json.dumps(data, ensure_ascii=False)
    documents = sorted({u for u in re.findall(r"https://[^\"\\\s<>]+?\.pdf", blob)
                        if re.search(r"call-fiche|call-document|wp-call|call_document", u, re.I)})
    return text, documents


def pdf_text(url: str, *, timeout: int = 45, getter: Callable[..., bytes] = _get) -> str:
    import io
    from pypdf import PdfReader
    data = getter(url, timeout)
    if not data.startswith(b"%PDF-"):
        raise ValueError("Il documento della call non è un PDF")
    reader = PdfReader(io.BytesIO(data))
    return re.sub(r"\s+", " ", " ".join((page.extract_text() or "") for page in reader.pages[:120]))


def topic_section(document: str, identifier: str) -> str:
    """La parte del documento della call dedicata al topic (le call coprono più topic)."""
    marker = re.search(r"\[\s*Topic\s+" + re.escape(identifier) + r"\s*\]", document, re.I)
    if not marker:
        return ""
    following = re.search(r"\[\s*Topic\s+[A-Z0-9-]+\s*\]", document[marker.end():])
    end = marker.end() + following.start() if following else marker.end() + 8000
    # Il paragrafo che precede il marcatore apre la priorità: lo includiamo.
    return document[max(0, marker.start() - 1500):end]


def candidates(source: dict[str, Any], today: date, *, poster: Callable[..., bytes] = _post_multipart,
               getter: Callable[..., bytes] = _get) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Candidati strutturati e diagnostica. Una ricerca che fallisce è un errore, mai uno zero silenzioso."""
    # Tutti i topic aperti o in arrivo, pagina per pagina: nessuna ricerca per
    # parole chiave che tagli i risultati oltre il primo centinaio.
    found: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    raw_results = 0
    prefixes = tuple(source.get("programmePrefixes") or PROGRAMME_PREFIXES)
    for page in range(1, MAX_PAGES + 1):
        try:
            results = search("***", poster=poster, page=page, timeout=int(source.get("fetchTimeoutSeconds") or 30))
        except Exception as exc:
            errors.append(f"ricerca pagina {page}: {exc}")
            break
        raw_results += len(results)
        for result in results:
            item = topic(result)
            if not item or item["identifier"] in found:
                continue
            if not item["identifier"].upper().startswith(prefixes):
                continue
            if not item["deadline_at"] or item["deadline_at"] < today.isoformat():
                continue
            found[item["identifier"]] = item
        if len(results) < PAGE_SIZE:
            break
    out = []
    documents_cache: dict[str, str] = {}
    import threading
    from concurrent.futures import ThreadPoolExecutor
    lock = threading.Lock()

    def document(url: str) -> str:
        with lock:
            if url in documents_cache:
                return documents_cache[url]
        try:
            text = pdf_text(url, getter=getter)
        except Exception as exc:
            with lock:
                errors.append(f"documento {url}: {exc}")
            text = ""
        with lock:
            documents_cache[url] = text
        return text

    def enrich(item: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
        section = ""
        try:
            text, documents = details(item["identifier"], getter=getter)
            for url in documents[:2]:
                section = topic_section(document(url), item["identifier"]) or section
        except Exception as exc:
            with lock:
                errors.append(f"scheda {item['identifier']}: {exc}")
            text = item["summary"]
        return item, text, section

    with ThreadPoolExecutor(max_workers=8) as pool:
        enriched = list(pool.map(enrich, found.values()))
    for item, text, section in enriched:
        out.append({
            "source_id": source["id"],
            "source_label": source.get("label") or source["id"],
            "publisher": source.get("publisher") or "Commissione europea",
            "territory": source.get("territory") or "Unione europea",
            "title": f"{item['identifier']} · {item['title']}",
            "url": item["url"] or TOPIC_URL.format(item["identifier"]),
            "summary": item["summary"],
            "deadline_at": item["deadline_at"],
            "opens_at": item["opens_at"],
            "structured_text": f"{item['title']}. {item.get('call') or ''}. {text} {section}",
            "strict_municipal": True,
            "discovery_only": True,
            "status": "internal_review",
            "reason": "Topic UE aperto o in arrivo dall'interfaccia ufficiale del portale Funding & Tenders.",
        })
    if errors and not raw_results:
        raise RuntimeError("; ".join(errors))
    return out, {"status": "ok" if raw_results else "degraded", "rawResults": raw_results,
                 "topics": len(out), "errors": errors, "transport": "official_api", "payloadFormat": "json"}
