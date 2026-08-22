#!/usr/bin/env python3
"""Scarica i favicon direttamente dalle pagine ufficiali usate dal Radar.

La preview non dipende da placeholder grafici: per ogni fonte pubblicata prova la
pagina dell'opportunità e poi la landing configurata, legge i <link rel=icon> e
materializza localmente l'asset scelto. Se la pagina non espone un link icon,
prova /favicon.ico sullo stesso origin. Un errore di rete lascia il fallback
letterale già previsto dalla UI.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATHS = (
    ROOT / "data" / "opportunity-sources-v03.json",
    ROOT / "data" / "opportunity-discovery-v04.json",
    ROOT / "data" / "opportunity-discovery-v04-extra.json",
    ROOT / "data" / "opportunity-discovery-v042.json",
    ROOT / "data" / "opportunity-discovery-v043.json",
)
UA = "Mozilla/5.0 (compatible; OsservatorioVersiliaRadar/0.4.3; +https://osservatorioversilia.it/)"


class IconParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.icons: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        row = {str(k).lower(): str(v or "") for k, v in attrs}
        rel = row.get("rel", "").lower()
        if "icon" in rel and row.get("href"):
            self.icons.append(row)


def _json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def configured_pages() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for path in CONFIG_PATHS:
        data = _json(path)
        for row in data.get("sources") or []:
            source_id = str(row.get("id") or "")
            url = str(row.get("url") or "")
            if source_id and url.startswith("http"):
                out.setdefault(source_id, []).append(url)
        for row in data.get("discoverySources") or []:
            source_id = str(row.get("id") or "")
            for url in row.get("urls") or []:
                if source_id and str(url).startswith("http"):
                    out.setdefault(source_id, []).append(str(url))
    return out


def _fetch(url: str, *, max_bytes: int = 1_500_000) -> tuple[bytes, str, str]:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,image/*,*/*;q=0.8"})
    with urlopen(req, timeout=14) as response:
        content_type = str(response.headers.get("Content-Type") or "").split(";", 1)[0].lower()
        final_url = response.geturl()
        payload = response.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise ValueError("asset troppo grande")
    return payload, content_type, final_url


def _rank_icon(row: dict[str, str]) -> tuple[int, int, int]:
    href = row.get("href", "").lower()
    mime = row.get("type", "").lower()
    sizes = row.get("sizes", "")
    nums = [int(x) for x in re.findall(r"\b(\d{2,4})x\d{2,4}\b", sizes)]
    size = max(nums) if nums else 0
    scalable = 1 if ("svg" in mime or ".svg" in href) else 0
    apple = 1 if "apple-touch-icon" in row.get("rel", "").lower() else 0
    return scalable, size, apple


def _page_icon_urls(page_url: str) -> list[str]:
    parsed = urlparse(page_url)
    if parsed.path.lower().endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")):
        return []
    try:
        payload, content_type, final_url = _fetch(page_url)
    except Exception:
        return []
    if "html" not in content_type and b"<html" not in payload[:1000].lower():
        return []
    parser = IconParser()
    try:
        parser.feed(payload.decode("utf-8", errors="ignore"))
    except Exception:
        return []
    rows = sorted(parser.icons, key=_rank_icon, reverse=True)
    urls = [urljoin(final_url, row.get("href", "")) for row in rows if row.get("href")]
    origin = f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}/favicon.ico"
    if origin not in urls:
        urls.append(origin)
    return urls


def _extension(url: str, content_type: str) -> str:
    if "svg" in content_type:
        return ".svg"
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    if "icon" in content_type or "ico" in content_type:
        return ".ico"
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".svg", ".png", ".webp", ".jpg", ".jpeg", ".ico"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    guessed = mimetypes.guess_extension(content_type) if content_type else None
    return guessed if guessed in {".svg", ".png", ".webp", ".jpg", ".ico"} else ".ico"


def _save_data_uri(uri: str, target_stem: Path) -> Path | None:
    match = re.match(r"data:(image/[^;,]+)(;base64)?,(.*)$", uri, flags=re.I | re.S)
    if not match:
        return None
    mime, is_b64, body = match.groups()
    raw = base64.b64decode(body) if is_b64 else body.encode("utf-8")
    ext = _extension("", mime.lower())
    target = target_stem.with_suffix(ext)
    target.write_bytes(raw)
    return target


def materialize(payload: dict[str, Any], dist: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    landing = configured_pages()
    asset_dir = dist / "assets" / "source-favicons"
    asset_dir.mkdir(parents=True, exist_ok=True)
    by_source: dict[str, str] = {}
    provenance: dict[str, Any] = {}

    opportunities = list(payload.get("opportunities") or [])
    for item in opportunities:
        source_id = str(item.get("source_id") or "")
        if not source_id or source_id in by_source:
            continue
        pages: list[str] = []
        official = str(item.get("url") or "")
        if official.startswith("http"):
            pages.append(official)
        pages.extend(landing.get(source_id, []))
        seen: set[str] = set()
        resolved = None
        for page in pages:
            if page in seen:
                continue
            seen.add(page)
            for icon_url in _page_icon_urls(page):
                try:
                    stem = asset_dir / re.sub(r"[^a-z0-9-]+", "-", source_id.lower()).strip("-")
                    if icon_url.startswith("data:image/"):
                        target = _save_data_uri(icon_url, stem)
                        if target is None:
                            continue
                        final_icon_url = icon_url
                    else:
                        raw, content_type, final_icon_url = _fetch(icon_url)
                        if not raw:
                            continue
                        target = stem.with_suffix(_extension(final_icon_url, content_type))
                        target.write_bytes(raw)
                    resolved = "../assets/source-favicons/" + target.name
                    provenance[source_id] = {"page": page, "icon": final_icon_url, "local": resolved}
                    break
                except Exception:
                    continue
            if resolved:
                break
        if resolved:
            by_source[source_id] = resolved

    for item in opportunities:
        source_id = str(item.get("source_id") or "")
        if source_id in by_source:
            item.setdefault("presentation", {})["source_favicon"] = by_source[source_id]
    for item in payload.get("archive") or []:
        source_id = str(item.get("source_id") or "")
        if source_id in by_source:
            item["source_favicon"] = by_source[source_id]

    (asset_dir / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload, provenance
