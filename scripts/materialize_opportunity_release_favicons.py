#!/usr/bin/env python3
"""Materializza le icone fonte del Radar pubblico senza dipendenze di rete.

Le fonti già acquisite usano il favicon ufficiale versionato. Le opportunità
provenienti dal replay audit possono avere source_id tecnico generico: in quel
caso la famiglia grafica viene risolta dal dominio ufficiale. Per i domini
indipendenti che non hanno ancora un favicon binario versionato viene generato
un source-mark SVG locale, identificabile e stabile, evitando fallback testuali
nella release pubblica.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "opportunity-source-favicons"
EXPECTED_MIC_SHA256 = "fb5906ca71b08563282e4f48a9ada17a1f481031ada4071e85671499f84775fc"
EXPECTED_MIC_BYTES = 19912

# Alias verso favicon ufficiali già versionati nel repository.
_HOST_ALIASES = {
    "regione.toscana.it": "regione-toscana",
    "spettacolo.cultura.gov.it": "mic-spettacolo",
    "cinema.cultura.gov.it": "mic-dgcc",
    "cultura.gov.it": "mic-spettacolo",
    "fnasilo.dlci.interno.it": "ministero-interno-prefetture",
    "urban-initiative.eu": "eu-eui",
    "www.urban-initiative.eu": "eu-eui",
    "new-european-bauhaus.europa.eu": "eu-neb",
    "avvisibandi.sport.governo.it": "pcm-famiglia",
}

# Source-mark locali per domini indipendenti non ancora dotati di asset acquisito.
# Non sono loghi inventati: sono badge tipografici identificativi della fonte.
_GENERATED_HOST_MARKS = {
    "agenziagioventu.gov.it": "AG",
    "inpa.gov.it": "inPA",
    "creditosportivo.it": "ICSC",
    "eit-culture-creativity.eu": "EIT",
    "eiturbanmobility.eu": "EIT",
    "eib.org": "EIB",
    "advisory.eib.org": "EIB",
    "eeef.lu": "eeef",
    "co-waters.eu": "CO",
    "space4cities.eu": "S4C",
    "sundanseproject.eu": "SUN",
    "iriscc.eu": "IRIS",
    "agenziademanio.it": "DEM",
    "iucnsos.org": "IUCN",
    "coebank.org": "CEB",
    "infratelitalia.it": "INF",
    "interreg-euro-med.eu": "MED",
    "regione.sardegna.it": "RAS",
    "trunsport.eu": "TRU",
}


def _items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return list(payload.get("opportunities") or []) + list(payload.get("archive") or [])


def _host(item: dict[str, Any]) -> str:
    return urlsplit(str(item.get("url") or "")).netloc.lower().removeprefix("www.")


def _safe_host(host: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-")
    return value or "source"


def _generated_key(host: str) -> str:
    return f"generated:{host}"


def _resolve_icon_key(item: dict[str, Any], provenance: dict[str, dict[str, Any]]) -> str | None:
    sid = str(item.get("source_id") or "")
    if sid in provenance:
        return sid

    host = _host(item)
    if not host:
        return None
    if host in _HOST_ALIASES and _HOST_ALIASES[host] in provenance:
        return _HOST_ALIASES[host]
    if host in _GENERATED_HOST_MARKS:
        key = _generated_key(host)
        return key if key in provenance else None

    # La gran parte dei nuovi programmi CINEA/Horizon/Erasmus/EIT/InvestEU usa
    # l'identità web della Commissione europea: riusiamo il favicon EC ufficiale.
    if host == "europa.eu" or host.endswith(".europa.eu"):
        return "eu-neb" if "new-european-bauhaus" in host else "eu-cerv"
    return None


def _source_mark_svg(label: str) -> str:
    safe = html.escape(label, quote=False)
    size = 25 if len(label) <= 3 else 20 if len(label) <= 4 else 15
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img">\n'
        f'  <title>{safe}</title>\n'
        '  <rect x="2" y="2" width="60" height="60" rx="14" fill="#0F3654"/>\n'
        '  <rect x="5" y="5" width="54" height="54" rx="11" fill="none" stroke="#ffffff" stroke-opacity=".28"/>\n'
        f'  <text x="32" y="34" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="700" fill="#ffffff">{safe}</text>\n'
        '</svg>\n'
    )


def _materialize_generated(provenance: dict[str, dict[str, Any]], target: Path) -> None:
    for host, label in _GENERATED_HOST_MARKS.items():
        name = f"source-{_safe_host(host)}.svg"
        content = _source_mark_svg(label)
        path = target / name
        path.write_text(content, encoding="utf-8")
        provenance[_generated_key(host)] = {
            "page": f"https://{host}/",
            "icon": None,
            "local": f"../assets/source-favicons/{name}",
            "method": "local-source-mark",
            "contentType": "image/svg+xml",
            "bytes": len(content.encode("utf-8")),
        }


def materialize(payload: dict[str, Any], dist: Path) -> dict[str, dict[str, Any]]:
    provenance_path = SOURCE / "provenance.json"
    if not provenance_path.exists():
        raise RuntimeError("Provenienza favicon Radar versionata assente")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if not isinstance(provenance, dict):
        raise RuntimeError("Provenienza favicon Radar non valida")

    target = dist / "assets" / "source-favicons"
    target.mkdir(parents=True, exist_ok=True)
    copied: set[str] = set()
    for source_id, meta in list(provenance.items()):
        local = str((meta or {}).get("local") or "")
        name = Path(local).name
        if not name or name == "provenance.json" or Path(name).name != name:
            raise RuntimeError(f"Path favicon non valido per {source_id}: {local!r}")
        source = SOURCE / name
        if not source.is_file() or source.stat().st_size == 0:
            raise RuntimeError(f"Asset favicon mancante o vuoto per {source_id}: {name}")
        expected_bytes = int((meta or {}).get("bytes") or source.stat().st_size)
        if source.stat().st_size != expected_bytes:
            raise RuntimeError(
                f"Dimensione favicon incoerente per {source_id}: {source.stat().st_size}/{expected_bytes}"
            )
        shutil.copyfile(source, target / name)
        copied.add(name)

    _materialize_generated(provenance, target)

    mic = target / "mic-dgcc.png"
    if mic.stat().st_size != EXPECTED_MIC_BYTES:
        raise RuntimeError(f"Dimensione mic-dgcc inattesa: {mic.stat().st_size}")
    digest = hashlib.sha256(mic.read_bytes()).hexdigest()
    if digest != EXPECTED_MIC_SHA256:
        raise RuntimeError(f"Hash mic-dgcc inatteso: {digest}")

    public_items = _items(payload)
    unresolved = [item for item in public_items if not _resolve_icon_key(item, provenance)]
    covered = len(public_items) - len(unresolved)
    (target / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if unresolved:
        detail = ", ".join(
            f"{_host(item) or item.get('source_id')}::{item.get('title')}" for item in unresolved[:12]
        )
        raise RuntimeError(
            f"Icone fonte incomplete: {covered}/{len(public_items)} schede coperte; mancanti: {detail}"
        )
    print(
        f"Icone Radar locali: {covered}/{len(public_items)} schede coperte · "
        f"{len(copied)} asset ufficiali versionati + {len(_GENERATED_HOST_MARKS)} source-mark locali · "
        "mic-dgcc verificato."
    )
    return provenance


def apply_to_payload(payload: dict[str, Any], provenance: dict[str, dict[str, Any]]) -> dict[str, Any]:
    for item in payload.get("opportunities") or []:
        presentation = item.setdefault("presentation", {})
        key = _resolve_icon_key(item, provenance)
        meta = provenance.get(key or "") or {}
        presentation["source_favicon"] = str(meta.get("local") or "")
        presentation["source_favicon_family"] = key or ""
    for item in payload.get("archive") or []:
        key = _resolve_icon_key(item, provenance)
        meta = provenance.get(key or "") or {}
        item["source_favicon"] = str(meta.get("local") or "")
        item["source_favicon_family"] = key or ""
    return payload
