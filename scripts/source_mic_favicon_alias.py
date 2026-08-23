#!/usr/bin/env python3
"""Fallback deterministico per sottositi del Ministero della Cultura.

Alcuni portali MiC possono non esporre in modo stabile favicon/logo ai runner
GitHub. Quando `mic-dgcc` non è risolvibile direttamente, riusiamo una favicon
ufficiale MiC già acquisita nello stesso build da un altro portale del Ministero.
La provenienza resta esplicita e l'asset non viene inventato.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import source_favicon_assets

TARGETS = {"mic-dgcc"}
DONORS = (
    "mic-spettacolo",
    "mic-cultura",
)
OFFICIAL_HOSTS = {
    "cultura.gov.it",
    "www.cultura.gov.it",
    "spettacolo.cultura.gov.it",
    "creativitacontemporanea.cultura.gov.it",
}


def _official_mic(meta: dict[str, Any]) -> bool:
    for field in ("page", "icon"):
        value = str(meta.get(field) or "")
        if not value.startswith("http"):
            continue
        host = (urlparse(value).hostname or "").lower()
        if host in OFFICIAL_HOSTS or host.endswith(".cultura.gov.it"):
            return True
    return False


def _asset_path(asset_dir: Path, local: str) -> Path | None:
    name = Path(str(local or "")).name
    if not name:
        return None
    path = asset_dir / name
    return path if path.is_file() and path.stat().st_size > 0 else None


def materialize(
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
    missing = sorted((public_sources & TARGETS) - set(provenance))
    if not missing:
        return payload, provenance

    asset_dir = dist / "assets" / "source-favicons"
    asset_dir.mkdir(parents=True, exist_ok=True)

    donor_id = None
    donor_meta: dict[str, Any] | None = None
    donor_asset: Path | None = None
    for candidate in DONORS:
        meta = provenance.get(candidate)
        if not isinstance(meta, dict) or not _official_mic(meta):
            continue
        asset = _asset_path(asset_dir, str(meta.get("local") or ""))
        if asset is None:
            continue
        donor_id = candidate
        donor_meta = meta
        donor_asset = asset
        break

    if donor_id is None or donor_meta is None or donor_asset is None:
        return payload, provenance

    configured = source_favicon_assets.configured_pages()
    for source_id in missing:
        suffix = donor_asset.suffix.lower() or ".ico"
        target = asset_dir / f"{source_id}-mic-official{suffix}"
        shutil.copy2(donor_asset, target)
        resolved = "../assets/source-favicons/" + target.name
        pages = configured.get(source_id, [])
        provenance[source_id] = {
            "page": pages[0] if pages else "",
            "icon": donor_meta.get("icon") or donor_meta.get("page") or "",
            "local": resolved,
            "method": "official-mic-shared-favicon",
            "inheritedFrom": donor_id,
            "institutionalOwner": "Ministero della Cultura",
            "reason": "Il sottosito DGCC non espone stabilmente l'asset ai runner GitHub; viene riusata una favicon ufficiale MiC già acquisita nello stesso build.",
            "bytes": str(target.stat().st_size),
        }
        for item in opportunities:
            if str(item.get("source_id") or "") == source_id:
                item.setdefault("presentation", {})["source_favicon"] = resolved
        for item in payload.get("archive") or []:
            if str(item.get("source_id") or "") == source_id:
                item["source_favicon"] = resolved

    (asset_dir / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload, provenance
