#!/usr/bin/env python3
"""Estrazione mirata di evidenza da PDF allegati ai bandi ufficiali."""
from __future__ import annotations

import io
import re
import urllib.request
from html import unescape
from html.parser import HTMLParser
from typing import Callable
from urllib.parse import urljoin

UA = "OsservatorioVersilia-OpportunityRadar/0.2.4 (+https://osservatorioversilia.it/)"
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
RELEVANT_LINK = re.compile(r"\b(bando|avviso|allegat|decreto|disciplinare|linee guida)\b", re.I)


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
    parser.feed(payload or "")
    parser.close()
    ranked: list[tuple[int, str]] = []
    seen: set[str] = set()
    for href, label in parser.links:
        absolute = urljoin(page_url, unescape(href))
        probe = f"{href} {label}"
        is_pdf = bool(re.search(r"\.pdf(?:$|[?#])", href, re.I))
        document_like = "/documents/" in href.lower() or "download" in href.lower()
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
    plain = re.sub(r"\s+", " ", str(text or "")).strip()
    folded = plain.casefold().replace("’", "'")
    starts = [folded.find(key) for key in KEYS if folded.find(key) >= 0]
    if not starts:
        return ""
    start = min(starts)
    return plain[start : start + window].strip()


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
