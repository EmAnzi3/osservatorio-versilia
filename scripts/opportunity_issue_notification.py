#!/usr/bin/env python3
"""Prepara una notifica GitHub Issue per le nuove identità del Radar.

Il modulo non chiama GitHub direttamente: confronta lo snapshot precedente con
quello corrente, produce un payload macchina e un corpo Markdown. Il workflow
usa poi il fingerprint per evitare Issue duplicate e crea la Issue soltanto se
esistono nuove opportunità pubblicabili.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

RADAR_URL = "https://osservatorioversilia.it/opportunita/"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON non valido: {path}")
    return payload


def _fold(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _normalized_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = urlsplit(text)
    path = re.sub(r"/+", "/", parsed.path).rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))


def _aliases(item: dict[str, Any]) -> set[str]:
    aliases: set[str] = set()
    coverage_id = str(item.get("coverage_id") or "").strip()
    if coverage_id:
        aliases.add("coverage:" + coverage_id)
    normalized = _normalized_url(item.get("url"))
    if normalized:
        aliases.add("url:" + normalized)
    item_id = str(item.get("id") or "").strip()
    if item_id:
        aliases.add("id:" + item_id)
    title = _fold(item.get("title"))
    deadline = str(item.get("deadline_at") or "").strip()
    if title:
        aliases.add(f"title:{title}|deadline:{deadline}")
    return aliases


def _preferred_identity(item: dict[str, Any]) -> str:
    coverage_id = str(item.get("coverage_id") or "").strip()
    if coverage_id:
        return "coverage:" + coverage_id
    normalized = _normalized_url(item.get("url"))
    if normalized:
        return "url:" + normalized
    item_id = str(item.get("id") or "").strip()
    if item_id:
        return "id:" + item_id
    return "title:" + _fold(item.get("title")) + "|deadline:" + str(item.get("deadline_at") or "")


def new_items(previous: dict[str, Any], current: dict[str, Any]) -> list[dict[str, Any]]:
    previous_aliases: set[str] = set()
    for item in previous.get("opportunities") or []:
        previous_aliases.update(_aliases(item))

    found: list[dict[str, Any]] = []
    for item in current.get("opportunities") or []:
        aliases = _aliases(item)
        if aliases and aliases.isdisjoint(previous_aliases):
            found.append(item)
    found.sort(key=lambda item: (str(item.get("deadline_at") or "9999-99-99"), str(item.get("title") or "")))
    return found


def _format_date(value: Any) -> str:
    text = str(value or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text or "non rilevata"
    year, month, day = text.split("-")
    return f"{day}/{month}/{year}"


def _municipalities(item: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    matrix = item.get("municipality_eligibility") or {}
    for town, entry in matrix.items():
        status = str((entry or {}).get("status") or "")
        if status in {"eligible", "conditional"}:
            rows.append({"name": str(town), "status": status})
    rows.sort(key=lambda row: row["name"])
    return rows


def _access_label(item: dict[str, Any]) -> str:
    mode = str(item.get("access_mode") or "").strip()
    labels = {
        "direct": "accesso diretto",
        "specific_requirement": "accesso diretto con requisito specifico",
        "direct_or_partner": "accesso diretto o come partner",
        "partnership": "partenariato",
        "partner": "partecipazione come partner",
        "indirect": "accesso indiretto",
    }
    if mode in labels:
        return labels[mode]
    role = str(item.get("municipality_role") or "").strip()
    role_labels = {
        "direct_applicant": "accesso diretto",
        "direct_or_partner": "accesso diretto o come partner",
        "partner": "partecipazione come partner",
        "system_member": "tramite sistema/ente capofila",
        "implementing_body": "come soggetto attuatore",
    }
    return role_labels.get(role, mode or role or "da verificare nella scheda")


def build_payload(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    items = new_items(previous, current)
    reference = str(current.get("referenceDate") or date.today().isoformat())
    identities = sorted(_preferred_identity(item) for item in items)
    fingerprint = hashlib.sha256("\n".join(identities).encode("utf-8")).hexdigest()[:16] if identities else None
    issue_title = f"Nuove opportunità Radar · {_format_date(reference)}" if items else None
    marker = f"<!-- radar-new:{fingerprint} -->" if fingerprint else None

    compact = []
    for item in items:
        compact.append(
            {
                "identity": _preferred_identity(item),
                "title": str(item.get("title") or "Senza titolo"),
                "deadline_at": item.get("deadline_at"),
                "municipalities": _municipalities(item),
                "access_mode": str(item.get("access_mode") or ""),
                "access_label": _access_label(item),
                "source_name": str(
                    item.get("source_name")
                    or (item.get("presentation") or {}).get("source_label")
                    or item.get("publisher")
                    or "Fonte ufficiale"
                ),
                "url": str(item.get("url") or ""),
            }
        )

    return {
        "schemaVersion": 1,
        "referenceDate": reference,
        "count": len(compact),
        "fingerprint": fingerprint,
        "marker": marker,
        "issueTitle": issue_title,
        "items": compact,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    if not payload.get("count"):
        return ""
    lines = [
        str(payload.get("marker") or ""),
        "# Nuove opportunità rilevate",
        "",
        (
            f"Il refresh automatico del Radar del **{_format_date(payload.get('referenceDate'))}** "
            f"ha rilevato **{payload.get('count')}** nuove opportunità pubblicabili."
        ),
        "",
    ]
    status_labels = {"eligible": "ammissibile", "conditional": "condizionale"}
    for item in payload.get("items") or []:
        towns = item.get("municipalities") or []
        town_text = ", ".join(
            f"{row['name']} ({status_labels.get(row['status'], row['status'])})"
            for row in towns
        ) or "nessun Comune indicato"
        lines.extend(
            [
                f"## {item.get('title')}",
                "",
                f"- **Scadenza:** {_format_date(item.get('deadline_at'))}",
                f"- **Comuni interessati:** {town_text}",
                f"- **Modalità di accesso:** {item.get('access_label') or 'da verificare'}",
                f"- **Fonte:** [{item.get('source_name') or 'Fonte ufficiale'}]({item.get('url')})" if item.get("url") else f"- **Fonte:** {item.get('source_name') or 'Fonte ufficiale'}",
                "",
            ]
        )
    lines.extend(
        [
            f"[Apri il Radar Opportunità]({RADAR_URL})",
            "",
            "_Issue generata automaticamente dal refresh giornaliero del Radar Opportunità._",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--body-out", type=Path, required=True)
    args = parser.parse_args()

    payload = build_payload(_load(args.previous), _load(args.current))
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.body_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.body_out.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"count": payload["count"], "fingerprint": payload["fingerprint"], "issueTitle": payload["issueTitle"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
