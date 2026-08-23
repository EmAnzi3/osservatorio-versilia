#!/usr/bin/env python3
"""Materializza favicon ufficiali già acquisite e verificate in un run verde.

Questi pin servono solo per sorgenti la cui rete/HTML è instabile sui runner.
Gli asset sono byte-per-byte quelli scaricati dalla pagina ufficiale, versionati
in Base64 con SHA-256 e dimensione attesi. Nessun accesso di rete è necessario.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PIN_FILE = ROOT / "data" / "source-favicon-pins-v1.json"


def _load() -> dict[str, Any]:
    data = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Registro favicon pin non valido")
    return data


def materialize(payload: dict[str, Any], dist: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    pins = (_load().get("pins") or {})
    public_sources = {
        str(item.get("source_id") or "")
        for item in payload.get("opportunities") or []
        if item.get("source_id")
    }
    selected = {sid: meta for sid, meta in pins.items() if sid in public_sources}
    if not selected:
        return payload, {}

    asset_dir = dist / "assets" / "source-favicons"
    asset_dir.mkdir(parents=True, exist_ok=True)
    provenance: dict[str, Any] = {}

    for source_id, meta in selected.items():
        raw = base64.b64decode(str(meta.get("dataBase64") or ""), validate=True)
        expected_bytes = int(meta.get("bytes") or 0)
        expected_sha = str(meta.get("sha256") or "")
        actual_sha = hashlib.sha256(raw).hexdigest()
        if len(raw) != expected_bytes or actual_sha != expected_sha:
            raise SystemExit(
                f"Pin favicon corrotto per {source_id}: bytes {len(raw)}/{expected_bytes}, sha {actual_sha}/{expected_sha}"
            )
        if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise SystemExit(f"Pin favicon non PNG per {source_id}")

        target = asset_dir / f"{source_id}.png"
        target.write_bytes(raw)
        resolved = "../assets/source-favicons/" + target.name
        provenance[source_id] = {
            "page": meta.get("page"),
            "icon": meta.get("icon"),
            "local": resolved,
            "method": "pinned-official-asset-from-green-run",
            "contentType": meta.get("contentType") or "image/png",
            "bytes": str(len(raw)),
            "sha256": actual_sha,
            "acquiredFromRun": meta.get("acquiredFromRun"),
            "artifactId": meta.get("artifactId"),
        }

        for item in payload.get("opportunities") or []:
            if str(item.get("source_id") or "") == source_id:
                item.setdefault("presentation", {})["source_favicon"] = resolved
        for item in payload.get("archive") or []:
            if str(item.get("source_id") or "") == source_id:
                item["source_favicon"] = resolved

    return payload, provenance


def pinned_source_ids(payload: dict[str, Any]) -> set[str]:
    pins = set(((_load().get("pins") or {}).keys()))
    public = {
        str(item.get("source_id") or "")
        for item in payload.get("opportunities") or []
        if item.get("source_id")
    }
    return pins & public
