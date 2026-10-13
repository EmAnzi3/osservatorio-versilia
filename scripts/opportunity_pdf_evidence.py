#!/usr/bin/env python3
"""Estrazione mirata di evidenza da PDF allegati ai bandi ufficiali."""
from __future__ import annotations

import io
import re
import urllib.request
from html import unescape
from html.parser import HTMLParser
from typing import Callable
from urllib.parse import urljoin, urlsplit, parse_qs
from opportunity_discovery_noise import content_html, unrelated_document

UA = "OsservatorioVersilia-OpportunityRadar/0.2.4 (+https://osservatorioversilia.it/)"
LINK_EXTRACTOR_VERSION = 3
KEYS = (
    "soggetti beneficiari",
    "destinatari / beneficiari",
    "destinatari/beneficiari",
    "soggetti ammissibili",
    "chi può presentare domanda",
    "chi puo presentare domanda",
    "beneficiari",
    "destinatari",
)
RELEVANT_LINK = re.compile(r"\b(bando|avviso|allegat\w*|decreto|disciplinare|linee guida)\b", re.I)


def verified_document_links(item):
    """The document links displayed in a public card, with no receipt metadata."""
    rows = [("Avviso PDF",item.get("document_evidence")),
            ("Elenco dei Comuni qualificati",item.get("qualification_evidence")),
            ("Criteri di valutazione",item.get("criteria_evidence"))]
    rows += [("FAQ ufficiali",x) for x in item.get("supplementary_documents") or []]
    links,seen=[],set()
    for label,evidence in rows:
        url=(evidence or {}).get("resolvedUrl", "")
        try: parsed=urlsplit(url)
        except ValueError: continue
        if (parsed.scheme!="https" or not parsed.hostname or parsed.username or url in seen
                or (evidence or {}).get("transport")!="direct_https"):
            continue
        seen.add(url);links.append((label,url))
    return links if len(links)>1 else []


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.href: str | None = None
        self.buf: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "a":
            self.href = dict(attrs).get("href")
            self.buf = []

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.buf.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.href is not None:
            self.links.append((self.href, " ".join(self.buf).strip()))
            self.href = None
            self.buf = []


def pdf_links(payload: str, page_url: str, limit: int = 2) -> list[str]:
    parser = Links()
    parser.feed(content_html(payload))
    parser.close()
    ranked: list[tuple[int, str]] = []
    seen: set[str] = set()
    for href, label in parser.links:
        absolute = urljoin(page_url, unescape(href))
        if unrelated_document(absolute):
            continue
        probe = f"{href} {label}"
        is_pdf = bool(re.search(r"\.pdf(?:$|[/?#])", href, re.I))
        document_like = "/documents/" in href.lower() or "download" in href.lower()
        # The Tuscan acts bank serves PDF bytes through Contenuto.xml.
        # Recognise this exact official attachment route, retaining its query.
        parsed = urlsplit(absolute)
        query = parse_qs(parsed.query)
        regional_attachment = (parsed.scheme == "https"
                               and parsed.hostname == "www301.regione.toscana.it"
                               and parsed.path == "/bancadati/atti/Contenuto.xml"
                               and bool(query.get("id")) and bool(query.get("nomeFile")))
        document_like = document_like or regional_attachment
        if not is_pdf and not (document_like and RELEVANT_LINK.search(probe)):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        score = 2 if RELEVANT_LINK.search(probe) else 1
        if re.search(r"\b(bando|avviso)\b", probe, re.I):
            score += 2
        ranked.append((score, absolute))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [url for _, url in ranked[:limit]]


def fetch_pdf_text(url: str, max_pages: int = 18, max_chars: int = 60000) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/pdf,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = response.read()
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    chunks: list[str] = []
    size = 0
    for page in reader.pages[:max_pages]:
        text = page.extract_text() or ""
        chunks.append(text)
        size += len(text)
        if size >= max_chars:
            break
    return "\n".join(chunks)[:max_chars]


def document_audience(text: str, window: int = 3200) -> str:
    # Preserve section boundaries and discard table-of-contents entries before
    # selecting beneficiaries. An index window can contain unrelated audiences.
    lines = [line.strip() for line in str(text or "").splitlines()
             if not re.search(r"\.{3,}|…{2,}", line)]
    body = "\n".join(lines)
    for match in re.finditer(r"(?m)^([^\n]{1,100})$", body):
        heading = match.group(1).casefold().replace("’", "'")
        if any(key in heading for key in KEYS) and re.fullmatch(
            r"(?:\d+(?:\.\d+)*[.)]?\s*)?(?:richiedenti\s*/\s*)?"
            r"(?:soggetti beneficiari|destinatari\s*/\s*beneficiari|"
            r"soggetti ammissibili|chi pu[oò] presentare domanda|beneficiari|destinatari)"
            r"\s*:?", heading
        ):
            return re.sub(r"\s+", " ", body[match.start():]).strip()[:window]
    plain = re.sub(r"\s+", " ", body).strip()
    folded = plain.casefold().replace("’", "'")
    starts = [folded.find(key) for key in KEYS if folded.find(key) >= 0]
    if not starts:
        return ""
    return plain[min(starts):min(starts) + window].strip()


def attached_pdf_audience(
    detail_html: str,
    page_url: str,
    text_loader: Callable[[str], str] | None = None,
) -> tuple[str, str | None]:
    loader = text_loader or fetch_pdf_text
    for url in pdf_links(detail_html, page_url):
        try:
            text = loader(url)
        except Exception:
            continue
        audience = document_audience(text)
        if audience:
            return audience, url
    return "", None
