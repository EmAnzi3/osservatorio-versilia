#!/usr/bin/env python3
"""Fallback visuale per fonti che non espongono un favicon scaricabile ai runner CI.

Apre esclusivamente pagine ufficiali usate dal Radar. Se favicon/manifest non
sono materializzabili, cattura con Chromium il logo/brand mark realmente
renderizzato nella pagina. Per i portali istituzionali che espongono l'identità
come testo/CSS anziché come immagine, cattura direttamente il blocco identitario
renderizzato dalla pagina ufficiale. Nessun placeholder inventato.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import source_favicon_assets

UA = source_favicon_assets.UA

# Questi URL sono landing ufficiali degli stessi enti. Servono soltanto come
# ultima pagina di prova quando la pagina del singolo bando non espone il brand
# in un elemento grafico autonomo.
OFFICIAL_IDENTITY_FALLBACKS: dict[str, dict[str, Any]] = {
    "mic-dgcc": {
        "pages": [
            "https://creativitacontemporanea.cultura.gov.it/strutturadelladirezionegenerale/",
            "https://creativitacontemporanea.cultura.gov.it/",
        ],
        "labels": [
            "Direzione Generale Creatività Contemporanea",
            "DIREZIONE GENERALE CREATIVITÀ CONTEMPORANEA",
        ],
    },
    "pcm-pari-opportunita": {
        "pages": ["https://www.pariopportunita.gov.it/it/"],
        "labels": [
            "Dipartimento per le Pari Opportunità",
            "DIPARTIMENTO PER LE PARI OPPORTUNITÀ",
        ],
    },
    "pcm-politiche-mare": {
        "pages": ["https://www.dipartimentopolitichemare.gov.it/it/"],
        "labels": [
            "Dipartimento per le politiche del mare",
            "DIPARTIMENTO PER LE POLITICHE DEL MARE",
        ],
    },
}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")


def _pages_for(source_id: str, opportunities: list[dict[str, Any]]) -> list[str]:
    pages: list[str] = []
    for item in opportunities:
        if str(item.get("source_id") or "") != source_id:
            continue
        url = str(item.get("url") or "")
        if url.startswith("http"):
            pages.append(url)
    pages.extend(source_favicon_assets.configured_pages().get(source_id, []))
    pages.extend((OFFICIAL_IDENTITY_FALLBACKS.get(source_id) or {}).get("pages") or [])
    return list(dict.fromkeys(url for url in pages if str(url).startswith("http")))


def _rank(row: dict[str, Any]) -> tuple[int, float, float]:
    text = " ".join(str(row.get(k) or "") for k in ("alt", "src", "className", "ariaLabel")).lower()
    keyword = 0
    for token, weight in (
        ("logo", 80), ("brand", 45), ("minister", 35), ("dipart", 35),
        ("direzione", 30), ("presidenza", 25), ("mit", 20), ("cultura", 20),
    ):
        if token in text:
            keyword += weight
    width = float(row.get("width") or 0)
    height = float(row.get("height") or 0)
    if width < 18 or height < 18:
        keyword -= 1000
    ratio = width / height if height else 99
    ratio_score = -abs(min(ratio, 8.0) - 2.2)
    area_score = min(width * height, 250000) / 250000
    return keyword, ratio_score, area_score


def _save_locator_screenshot(locator: Any, target: Path) -> bool:
    try:
        box = locator.bounding_box()
        if not box or box["width"] < 18 or box["height"] < 14:
            return False
        if box["width"] > 900 or box["height"] > 300:
            return False
        locator.screenshot(path=str(target), type="png", animations="disabled")
        if not target.exists() or target.stat().st_size < 150:
            target.unlink(missing_ok=True)
            return False
        return True
    except Exception:
        target.unlink(missing_ok=True)
        return False


def _rendered_identity_text(
    page: Any,
    source_id: str,
    asset_dir: Path,
) -> tuple[str, dict[str, str]] | None:
    """Cattura il marchio testuale così come è renderizzato dalla pagina ufficiale.

    Alcuni portali della PCM e del MiC compongono l'identità istituzionale con
    testo/CSS e non con un <img> autonomo. In quel caso un favicon obbligatorio
    non deve trasformarsi in un falso errore di copertura: usiamo il blocco
    identitario realmente presente nella pagina, mai un testo generato da noi.
    """
    cfg = OFFICIAL_IDENTITY_FALLBACKS.get(source_id) or {}
    labels = [str(x) for x in cfg.get("labels") or [] if str(x).strip()]
    if not labels:
        return None

    target = asset_dir / f"{_slug(source_id)}-brand.png"
    for label in labels:
        try:
            matches = page.get_by_text(label, exact=False)
            count = min(matches.count(), 12)
        except Exception:
            continue
        for index in range(count):
            try:
                node = matches.nth(index)
                if not node.is_visible():
                    continue
                box = node.bounding_box()
                if not box or box["width"] < 40 or box["height"] < 14:
                    continue
                # Preferiamo un contenitore stretto che includa anche un eventuale
                # stemma/SVG adiacente, senza catturare l'intero header della pagina.
                chosen = node
                current = node
                for _ in range(3):
                    parent = current.locator("xpath=..")
                    pbox = parent.bounding_box()
                    if not pbox:
                        break
                    if pbox["width"] > 620 or pbox["height"] > 190:
                        break
                    try:
                        has_mark = parent.locator("img, svg").count() > 0
                        cls = (parent.get_attribute("class") or "").lower()
                    except Exception:
                        has_mark = False
                        cls = ""
                    if has_mark or any(token in cls for token in ("logo", "brand", "header", "identity", "masthead")):
                        chosen = parent
                    current = parent
                if not _save_locator_screenshot(chosen, target):
                    # Il testo stesso è comunque un'identità presa dalla pagina.
                    if not _save_locator_screenshot(node, target):
                        continue
                resolved = "../assets/source-favicons/" + target.name
                return resolved, {
                    "page": page.url,
                    "icon": "rendered-official-identity",
                    "local": resolved,
                    "method": "official-page-rendered-identity",
                    "label": label,
                    "bytes": str(target.stat().st_size),
                }
            except Exception:
                continue
    return None


def materialize_missing(
    payload: dict[str, Any],
    dist: Path,
    provenance: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    opportunities = list(payload.get("opportunities") or [])
    public_sources = {
        str(item.get("source_id") or "")
        for item in opportunities
        if item.get("source_id")
    }
    missing = sorted(public_sources - set(provenance))
    if not missing:
        return payload, provenance

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return payload, provenance

    asset_dir = dist / "assets" / "source-favicons"
    asset_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=UA,
            locale="it-IT",
            ignore_https_errors=True,
            viewport={"width": 1440, "height": 1000},
        )
        page = context.new_page()
        try:
            for source_id in missing:
                resolved = None
                for official_page in _pages_for(source_id, opportunities):
                    try:
                        response = page.goto(official_page, wait_until="domcontentloaded", timeout=30_000)
                        if response is None:
                            continue
                        page.wait_for_timeout(1800)
                        rows = page.eval_on_selector_all(
                            "img, header svg, [class*='logo' i] svg, [class*='brand' i] svg",
                            """els => els.map((el, i) => {
                                const r = el.getBoundingClientRect();
                                return {
                                  index: i,
                                  tag: el.tagName.toLowerCase(),
                                  alt: el.getAttribute('alt') || '',
                                  src: el.currentSrc || el.getAttribute('src') || '',
                                  className: typeof el.className === 'string' ? el.className : (el.className?.baseVal || ''),
                                  ariaLabel: el.getAttribute('aria-label') || '',
                                  width: r.width,
                                  height: r.height,
                                  visible: r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden'
                                };
                            }).filter(x => x.visible && x.width >= 18 && x.height >= 18)""",
                        )
                        ranked = sorted(rows or [], key=_rank, reverse=True)
                        for candidate in ranked[:12]:
                            if _rank(candidate)[0] <= 0:
                                continue
                            selector = "img, header svg, [class*='logo' i] svg, [class*='brand' i] svg"
                            locator = page.locator(selector).nth(int(candidate["index"]))
                            target = asset_dir / f"{_slug(source_id)}-brand.png"
                            if not _save_locator_screenshot(locator, target):
                                continue
                            resolved = "../assets/source-favicons/" + target.name
                            provenance[source_id] = {
                                "page": page.url,
                                "icon": candidate.get("src") or "rendered-logo-element",
                                "local": resolved,
                                "method": "official-page-brandmark-screenshot",
                                "selector": selector,
                                "alt": candidate.get("alt") or candidate.get("ariaLabel") or "",
                                "bytes": str(target.stat().st_size),
                            }
                            break

                        if not resolved:
                            rendered = _rendered_identity_text(page, source_id, asset_dir)
                            if rendered:
                                resolved, meta = rendered
                                provenance[source_id] = meta
                        if resolved:
                            break
                    except Exception:
                        continue

                if resolved:
                    for item in opportunities:
                        if str(item.get("source_id") or "") == source_id:
                            item.setdefault("presentation", {})["source_favicon"] = resolved
                    for item in payload.get("archive") or []:
                        if str(item.get("source_id") or "") == source_id:
                            item["source_favicon"] = resolved
        finally:
            context.close()
            browser.close()

    (asset_dir / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload, provenance
