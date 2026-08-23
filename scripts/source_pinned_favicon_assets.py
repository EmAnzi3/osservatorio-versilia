#!/usr/bin/env python3
"""Materializza favicon istituzionali pinned e validate dal repository.

I pin sono file binari versionati sotto assets/institutional-favicons/. La rete
non viene interrogata per queste sorgenti: metadati, provenienza e SHA-256 sono
registrati in data/source-favicon-pins-v1.json.
"""
from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PIN_FILE = ROOT / "data" / "source-favicon-pins-v1.json"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _load() -> dict[str, Any]:
    data = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Registro favicon pin non valido")
    return data


def _valid_png(raw: bytes) -> bool:
    if len(raw) < 45 or not raw.startswith(PNG_SIGNATURE):
        return False
    pos = len(PNG_SIGNATURE)
    saw_ihdr = False
    saw_iend = False
    while pos + 12 <= len(raw):
        length = struct.unpack(">I", raw[pos : pos + 4])[0]
        chunk_type = raw[pos + 4 : pos + 8]
        data_start = pos + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(raw):
            return False
        expected_crc = struct.unpack(">I", raw[data_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type)
        actual_crc = zlib.crc32(raw[data_start:data_end], actual_crc) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            return False
        if chunk_type == b"IHDR":
            if saw_ihdr or length != 13:
                return False
            width, height = struct.unpack(">II", raw[data_start : data_start + 8])
            if width <= 0 or height <= 0:
                return False
            saw_ihdr = True
        elif chunk_type == b"IEND":
            if length != 0:
                return False
            saw_iend = True
            return saw_ihdr and crc_end == len(raw)
        pos = crc_end
    return saw_ihdr and saw_iend


def _asset_path(meta: dict[str, Any]) -> Path:
    relative = Path(str(meta.get("asset") or ""))
    if not relative.parts or relative.is_absolute() or ".." in relative.parts:
        raise SystemExit(f"Percorso asset pinned non valido: {relative}")
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise SystemExit(f"Asset pinned fuori repository: {relative}") from exc
    return path


def validate_asset(source_id: str, path: Path, meta: dict[str, Any]) -> tuple[bytes, str]:
    if not path.exists() or not path.is_file():
        raise SystemExit(f"Asset pinned mancante per {source_id}: {path}")
    raw = path.read_bytes()
    if not raw:
        raise SystemExit(f"Asset pinned vuoto per {source_id}: {path}")
    expected_bytes = int(meta.get("bytes") or 0)
    if expected_bytes and len(raw) != expected_bytes:
        raise SystemExit(f"Dimensione asset pinned errata per {source_id}: {len(raw)}/{expected_bytes}")
    content_type = str(meta.get("contentType") or "")
    if content_type != "image/png" or not _valid_png(raw):
        raise SystemExit(f"Asset pinned non è un PNG valido per {source_id}")
    expected_sha = str(meta.get("sha256") or "")
    actual_sha = hashlib.sha256(raw).hexdigest()
    if not expected_sha or actual_sha != expected_sha:
        raise SystemExit(f"SHA-256 asset pinned errato per {source_id}: {actual_sha}/{expected_sha}")
    return raw, actual_sha


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
        source_path = _asset_path(meta)
        raw, actual_sha = validate_asset(source_id, source_path, meta)
        target = asset_dir / f"{source_id}.png"
        target.write_bytes(raw)
        resolved = "../assets/source-favicons/" + target.name
        provenance[source_id] = {
            "entity": meta.get("entity"),
            "page": meta.get("page"),
            "icon": meta.get("icon"),
            "local": resolved,
            "repositoryAsset": meta.get("asset"),
            "method": "pinned-official-asset-from-green-run",
            "acquisitionMethod": meta.get("acquisitionMethod"),
            "contentType": meta.get("contentType") or "image/png",
            "bytes": str(len(raw)),
            "sha256": actual_sha,
            "acquiredFromRun": meta.get("acquiredFromRun"),
            "artifactName": meta.get("artifactName"),
            "artifactId": meta.get("artifactId"),
            "sourceCommit": meta.get("sourceCommit"),
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
