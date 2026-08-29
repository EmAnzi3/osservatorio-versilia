#!/usr/bin/env python3
"""Primitive semantiche usate dal monitor delle fonti.

Il monitor deve distinguere un vero cambio informativo dal semplice cambio dei
byte di trasporto. Questo modulo non pubblica dati e non interroga la rete.
"""
from __future__ import annotations

import hashlib
import io
import math
import zipfile
from typing import Any


def semantic_content_hash(payload: bytes) -> tuple[str, str]:
    """Hash stabile del contenuto; per ZIP ignora timestamp/metadati del contenitore."""
    raw_hash = hashlib.sha256(payload).hexdigest()
    if not payload.startswith(b"PK"):
        return raw_hash, "raw"
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            members = [item for item in archive.infolist() if not item.is_dir()]
            if not members:
                return raw_hash, "raw"
            digest = hashlib.sha256()
            for item in sorted(members, key=lambda value: (value.filename, value.CRC, value.file_size)):
                digest.update(item.filename.encode("utf-8", errors="surrogatepass"))
                digest.update(b"\0")
                digest.update(archive.read(item))
                digest.update(b"\0")
            return digest.hexdigest(), "zip-members"
    except (OSError, RuntimeError, zipfile.BadZipFile):
        return raw_hash, "raw"


def source_change_policy(url: str, registry: dict[str, Any]) -> dict[str, str]:
    policies = registry.get("sourceChangePolicies")
    if not isinstance(policies, dict):
        return {}
    item = policies.get(url)
    if not isinstance(item, dict):
        return {}
    return {
        "contentChange": str(item.get("contentChange") or "").strip(),
        "reason": str(item.get("reason") or "").strip(),
    }


def _same_number(left: Any, right: Any, *, tolerance: float = 5e-7) -> bool:
    if left is None or right is None:
        return left is None and right is None
    try:
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)
    except (TypeError, ValueError):
        return False


def fuel_metric_matches(metric: dict[str, Any], live: dict[str, Any]) -> bool:
    """Verifica i valori comunali MIMIT già pubblicati contro una fotografia live."""
    rows = {
        str(row.get("town") or ""): row
        for row in metric.get("rows", [])
        if isinstance(row, dict)
    }
    live_towns = live.get("towns")
    if not isinstance(live_towns, dict) or set(live_towns) != set(rows):
        return False

    for town, current in live_towns.items():
        if not isinstance(current, dict):
            return False
        row = rows.get(town)
        if not isinstance(row, dict):
            return False
        parts = {
            str(part.get("label") or "").strip().lower(): part.get("value")
            for part in row.get("parts", [])
            if isinstance(part, dict)
        }
        benzina = next((value for label, value in parts.items() if label.startswith("benzina")), None)
        gasolio = next((value for label, value in parts.items() if label.startswith("gasolio")), None)
        if not _same_number(benzina, current.get("benzina")):
            return False
        if not _same_number(gasolio, current.get("gasolio")):
            return False
        try:
            if int(row.get("stationCount") or 0) != int(current.get("stations") or 0):
                return False
        except (TypeError, ValueError):
            return False
    return True
