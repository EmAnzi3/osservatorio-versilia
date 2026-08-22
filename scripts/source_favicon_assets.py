#!/usr/bin/env python3
"""Scarica i favicon direttamente dalle pagine ufficiali usate dal Radar.

La preview non dipende da placeholder grafici: per ogni fonte pubblicata prova la
pagina dell'opportunità e poi la landing configurata, legge i <link rel=icon> e
materializza localmente l'asset scelto. Se il fetch HTTP standard non basta,
usa Chromium/Playwright sulla stessa pagina ufficiale e scarica l'icona nello
stesso contesto browser. Non vengono inventate icone sostitutive.
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
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151.0.0.0 Safari/537.36"
)


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


def _fetch(
    url: str,
    *,
    max_bytes: int = 1_500_000,
    referer: str | None = None,
) -> tuple[bytes, str, str]:
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.7",
        "Cache-Control": "no-cache",
    }
    if referer:
        headers["Referer"] = referer
    req = Request(url, headers=headers)
    with urlopen(req, timeout=18) as response:
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


def _page_icon_urls(page_url: str) -> list[tuple[str, str]]:
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
    urls = [(urljoin(final_url, row.get("href", "")), final_url) for row in rows if row.get("href")]
    origin = f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}/favicon.ico"
    if not any(url == origin for url, _ in urls):
        urls.append((origin, final_url))
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


def _looks_like_image(raw: bytes, content_type: str, url: str = "") -> bool:
    ctype = content_type.lower()
    if ctype.startswith("image/"):
        return True
    prefix = raw[:32].lstrip().lower()
    if raw.startswith(b"\x89PNG\r\n\x1a\n") or raw.startswith(b"\x00\x00\x01\x00"):
        return True
    if raw.startswith(b"\xff\xd8\xff") or raw[:4] in {b"RIFF"}:
        return True
    if prefix.startswith(b"<svg") or b"<svg" in raw[:500].lower():
        return True
    return Path(urlparse(url).path).suffix.lower() in {".svg", ".png", ".webp", ".jpg", ".jpeg", ".ico"} and bool(raw)


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


def _store_remote_icon(
    source_id: str,
    icon_url: str,
    page_url: str,
    asset_dir: Path,
) -> tuple[str, dict[str, str]] | None:
    stem = asset_dir / re.sub(r"[^a-z0-9-]+", "-", source_id.lower()).strip("-")
    if icon_url.startswith("data:image/"):
        target = _save_data_uri(icon_url, stem)
        if target is None:
            return None
        final_icon_url = icon_url
        content_type = "image/data"
        raw = target.read_bytes()
    else:
        raw, content_type, final_icon_url = _fetch(icon_url, referer=page_url)
        if not raw or not _looks_like_image(raw, content_type, final_icon_url):
            return None
        target = stem.with_suffix(_extension(final_icon_url, content_type))
        target.write_bytes(raw)
    resolved = "../assets/source-favicons/" + target.name
    return resolved, {
        "page": page_url,
        "icon": final_icon_url,
        "local": resolved,
        "method": "official-page-html",
        "contentType": content_type,
        "bytes": str(len(raw)),
    }


def _browser_resolve(
    source_id: str,
    pages: list[str],
    asset_dir: Path,
) -> tuple[str, dict[str, str]] | None:
    """Fallback reale: apre la pagina ufficiale in Chromium e usa i suoi link icon."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    stem = asset_dir / re.sub(r"[^a-z0-9-]+", "-", source_id.lower()).strip("-")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=UA, locale="it-IT")
            page = context.new_page()
            try:
                for requested_page in pages:
                    try:
                        response = page.goto(requested_page, wait_until="domcontentloaded", timeout=25_000)
                        if response is None:
                            continue
                        final_page = page.url
                        icons = page.eval_on_selector_all(
                            'link[rel*="icon" i]',
                            "els => els.map(el => ({href: el.href || el.getAttribute('href') || '', rel: el.rel || '', sizes: el.sizes ? el.sizes.value : '', type: el.type || ''})).filter(x => x.href)",
                        )
                        icons = sorted(icons, key=_rank_icon, reverse=True)
                        icon_urls = [str(row.get("href") or "") for row in icons]
                        origin = f"{urlparse(final_page).scheme}://{urlparse(final_page).netloc}/favicon.ico"
                        if origin not in icon_urls:
                            icon_urls.append(origin)
                        for icon_url in icon_urls:
                            try:
                                if icon_url.startswith("data:image/"):
                                    target = _save_data_uri(icon_url, stem)
                                    if target is None:
                                        continue
                                    raw = target.read_bytes()
                                    content_type = "image/data"
                                    final_icon = icon_url
                                else:
                                    icon_response = page.request.get(
                                        icon_url,
                                        headers={"Referer": final_page, "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"},
                                        timeout=20_000,
                                        fail_on_status_code=False,
                                    )
                                    if not icon_response.ok:
                                        continue
                                    raw = icon_response.body()
                                    content_type = str(icon_response.headers.get("content-type") or "").split(";", 1)[0].lower()
                                    final_icon = icon_response.url
                                    if not raw or not _looks_like_image(raw, content_type, final_icon):
                                        continue
                                    target = stem.with_suffix(_extension(final_icon, content_type))
                                    target.write_bytes(raw)
                                resolved = "../assets/source-favicons/" + target.name
                                return resolved, {
                                    "page": final_page,
                                    "icon": final_icon,
                                    "local": resolved,
                                    "method": "official-page-playwright",
                                    "contentType": content_type,
                                    "bytes": str(len(raw)),
                                }
                            except Exception:
                                continue
                    except Exception:
                        continue
            finally:
                context.close()
                browser.close()
    except Exception:
        return None
    return None


def materialize(payload: dict[str, Any], dist: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    landing = configured_pages()
    asset_dir = dist / "assets" / "source-favicons"
    asset_dir.mkdir(parents=True, exist_ok=True)
    by_source: dict[str, str] = {}
    provenance: dict[str, Any] = {}

    opportunities = list(payload.get("opportunities") or [])
    unresolved: dict[str, list[str]] = {}
    for item in opportunities:
        source_id = str(item.get("source_id") or "")
        if not source_id or source_id in by_source:
            continue
        pages: list[str] = []
        official = str(item.get("url") or "")
        if official.startswith("http"):
            pages.append(official)
        pages.extend(landing.get(source_id, []))
        pages = list(dict.fromkeys(page for page in pages if page.startswith("http")))
        resolved = None
        for page_url in pages:
            for icon_url, final_page in _page_icon_urls(page_url):
                try:
                    stored = _store_remote_icon(source_id, icon_url, final_page, asset_dir)
                except Exception:
                    stored = None
                if stored:
                    resolved, meta = stored
                    by_source[source_id] = resolved
                    provenance[source_id] = meta
                    break
            if resolved:
                break
        if not resolved:
            unresolved[source_id] = pages

    # Alcuni siti istituzionali accettano il browser ma non urllib o richiedono
    # cookie/redirect JS. Il fallback resta sulla pagina ufficiale originale.
    for source_id, pages in unresolved.items():
        stored = _browser_resolve(source_id, pages, asset_dir)
        if stored:
            resolved, meta = stored
            by_source[source_id] = resolved
            provenance[source_id] = meta

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
