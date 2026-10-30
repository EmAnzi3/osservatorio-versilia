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
DEFAULT_QUERIES = ("local authorities", "municipalities", "public authorities", "cities", "town twinning", "regions")
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


def search(text: str, *, timeout: int = 30, poster: Callable[..., bytes] = _post_multipart) -> list[dict[str, Any]]:
    query = {"bool": {"must": [
        {"terms": {"type": ["1", "2", "8"]}},
        {"terms": {"status": [STATUS_FORTHCOMING, STATUS_OPEN]}},
    ]}}
    url = f"{SEARCH_URL}?apiKey=SEDIA&text={urllib.request.quote(text)}&pageSize={PAGE_SIZE}&pageNumber=1"
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
    }


def details_text(identifier: str, *, timeout: int = 20, getter: Callable[..., bytes] = _get) -> str:
    """Descrizione e condizioni della scheda pubblica del topic, in testo semplice."""
    payload = json.loads(getter(DETAILS_URL.format(identifier.lower()), timeout))
    details = payload.get("TopicDetails") or payload
    parts = []
    for key in ("title", "description", "conditions", "furtherInformation", "topicConditions"):
        value = details.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, (list, dict)):
            parts.append(json.dumps(value, ensure_ascii=False))
    text = re.sub(r"<[^>]+>", " ", " ".join(parts))
    return re.sub(r"\s+", " ", text).strip()


def candidates(source: dict[str, Any], today: date, *, poster: Callable[..., bytes] = _post_multipart,
               getter: Callable[..., bytes] = _get) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Candidati strutturati e diagnostica. Una ricerca che fallisce è un errore, mai uno zero silenzioso."""
    queries = source.get("apiQueries") or DEFAULT_QUERIES
    found: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    raw_results = 0
    for text in queries:
        try:
            results = search(text, poster=poster, timeout=int(source.get("fetchTimeoutSeconds") or 30))
        except Exception as exc:
            errors.append(f"ricerca «{text}»: {exc}")
            continue
        raw_results += len(results)
        for result in results:
            item = topic(result)
            if not item or item["identifier"] in found:
                continue
            if item["deadline_at"] and item["deadline_at"] < today.isoformat():
                continue
            found[item["identifier"]] = item
    out = []
    for item in found.values():
        try:
            text = details_text(item["identifier"], getter=getter)
        except Exception as exc:
            errors.append(f"scheda {item['identifier']}: {exc}")
            text = item["summary"]
        out.append({
            "source_id": source["id"],
            "source_label": source.get("label") or source["id"],
            "publisher": source.get("publisher") or "Commissione europea",
            "territory": source.get("territory") or "Unione europea",
            "title": f"{item['identifier']} · {item['title']}",
            "url": TOPIC_URL.format(item["identifier"]),
            "summary": item["summary"],
            "deadline_at": item["deadline_at"],
            "opens_at": item["opens_at"],
            "structured_text": f"{item['title']}. {item.get('call') or ''}. {text}",
            "strict_municipal": True,
            "discovery_only": True,
            "status": "internal_review",
            "reason": "Topic UE aperto o in arrivo dall'interfaccia ufficiale del portale Funding & Tenders.",
        })
    if errors and not raw_results:
        raise RuntimeError("; ".join(errors))
    return out, {"status": "ok" if raw_results else "degraded", "rawResults": raw_results,
                 "topics": len(out), "errors": errors, "transport": "official_api", "payloadFormat": "json"}
