#!/usr/bin/env python3
"""Radar Opportunità Versilia v0.2.4.

Strato di presentazione e lifecycle sopra il motore v0.2.2:
- metadati editoriali leggibili per la UI;
- orario di scadenza quando documentato;
- modalità di partecipazione separata dalla review interna;
- archivio minimale dei bandi scaduti, alimentato da un output precedente.

La review e il quality gate restano strumenti interni e non sono concetti UI.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opportunity_radar_v022 as v022

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "data" / "opportunity-sources.json"
DEFAULT_RULES = ROOT / "data" / "opportunity-rules-v022.json"
DEFAULT_PRESENTATION = ROOT / "data" / "opportunity-presentation-v024.json"

TIME_PATTERN = re.compile(
    r"(?:scadenza(?:\s+presentazione\s+domande)?|entro)"
    r"[^0-9]{0,30}(\d{1,2}[./]\d{1,2}[./]\d{4}|\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})"
    r"[^0-9]{0,20}(\d{1,2}:\d{2})",
    re.I,
)


def load_presentation(path: Path = DEFAULT_PRESENTATION) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Presentation registry v0.2.4 non valido.")
    return payload


def extract_deadline_time(item: dict[str, Any]) -> str | None:
    existing = str(item.get("deadline_time") or "").strip()
    if re.fullmatch(r"\d{2}:\d{2}", existing):
        return existing
    text = " ".join(
        str(item.get(key) or "") for key in ("summary", "beneficiary_text", "deadline_evidence")
    )
    deadline = str(item.get("deadline_at") or "")
    for match in TIME_PATTERN.finditer(text):
        parsed = v022.base.parse_date(match.group(1))
        if not parsed:
            continue
        if deadline and parsed.isoformat() != deadline:
            continue
        hhmm = match.group(2)
        hour, minute = map(int, hhmm.split(":"))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"
    return None


def _fallback_description(item: dict[str, Any]) -> str:
    text = v022.base.clean(item.get("summary") or "")
    if not text:
        return "Consulta la fonte ufficiale per oggetto, interventi finanziabili e modalità di partecipazione."
    cuts = [
        r"\s+Pubblicato il\b.*$",
        r"\s+Pubblicato su BURT\b.*$",
        r"\s+Categoria:\s*.*$",
        r"\s+Stato:\s*Aperto\b.*$",
        r"\s+Scadenza presentazione domande\b.*$",
    ]
    for pattern in cuts:
        text = re.sub(pattern, "", text, flags=re.I).strip(" .;-")
    if len(text) > 360:
        text = text[:357].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return text or "Consulta la fonte ufficiale per oggetto, interventi finanziabili e modalità di partecipazione."


def _presentation_for(item: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    source_id = str(item.get("source_id") or "")
    rule_id = str(item.get("rule_id") or (item.get("eligibility_evidence") or {}).get("rule_id") or "")
    source = dict((registry.get("sources") or {}).get(source_id) or {})
    rule = dict((registry.get("rules") or {}).get(rule_id) or {})
    return {"source": source, "rule": rule}


def enrich_item(item: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    meta = _presentation_for(out, registry)
    source_meta = meta["source"]
    rule_meta = meta["rule"]

    source_label = source_meta.get("label") or out.get("publisher") or out.get("source_name") or out.get("source_id")
    out["presentation"] = {
        "source_label": source_label,
        "source_mark": source_meta.get("mark") or "".join(
            part[0].upper() for part in str(source_label or "Fonte").split()[:3] if part
        ),
        "source_class": source_meta.get("class") or "other",
        "category": rule_meta.get("category") or ((out.get("themes") or ["generale"])[0]),
        "description": rule_meta.get("description") or _fallback_description(out),
        "condition_label": rule_meta.get("conditionLabel"),
    }
    out["deadline_time"] = extract_deadline_time(out)

    if out.get("eligibility") == "conditional":
        out["access_mode"] = "specific_requirement"
        if not out["presentation"]["condition_label"]:
            role = out.get("municipality_role")
            labels = {
                "partner": "Richiede partenariato",
                "system_member": "Partecipazione tramite sistema o aggregazione",
            }
            out["presentation"]["condition_label"] = labels.get(role) or "Richiede requisito specifico"
    else:
        out["access_mode"] = "direct"

    return out


def archive_entry(item: dict[str, Any], today: date) -> dict[str, Any]:
    presentation = item.get("presentation") or {}
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "source_id": item.get("source_id"),
        "source_label": presentation.get("source_label") or item.get("publisher") or item.get("source_name"),
        "source_mark": presentation.get("source_mark"),
        "source_class": presentation.get("source_class"),
        "url": item.get("url"),
        "deadline_at": item.get("deadline_at"),
        "deadline_time": item.get("deadline_time"),
        "closed_at": today.isoformat(),
    }


def load_previous(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def merge_archive(
    current: list[dict[str, Any]], previous: dict[str, Any], today: date
) -> list[dict[str, Any]]:
    active_ids = {item.get("id") for item in current if item.get("id")}
    archive: dict[str, dict[str, Any]] = {}

    for old in previous.get("archive") or []:
        key = str(old.get("id") or f"{old.get('source_id')}::{old.get('title')}")
        archive[key] = dict(old)

    for old in previous.get("opportunities") or []:
        old_id = old.get("id")
        deadline = v022.base.parse_date(old.get("deadline_at")) if old.get("deadline_at") else None
        if old_id in active_ids or not deadline or deadline >= today:
            continue
        enriched = old if old.get("presentation") else enrich_item(old, {"sources": {}, "rules": {}})
        entry = archive_entry(enriched, today)
        key = str(entry.get("id") or f"{entry.get('source_id')}::{entry.get('title')}")
        archive[key] = entry

    return sorted(
        archive.values(),
        key=lambda x: (str(x.get("deadline_at") or "0000-00-00"), str(x.get("title") or "")),
        reverse=True,
    )


def run(
    config_path: Path,
    today: date,
    *,
    payloads: dict[str, str] | None = None,
    detail_payloads: dict[str, str] | None = None,
    rules_path: Path = DEFAULT_RULES,
    presentation_path: Path = DEFAULT_PRESENTATION,
    previous_path: Path | None = None,
) -> dict[str, Any]:
    result = v022.run(
        config_path,
        today,
        payloads=payloads,
        detail_payloads=detail_payloads,
        rules_path=rules_path,
    )
    registry = load_presentation(presentation_path)
    result["schemaVersion"] = "2.4"
    result["opportunities"] = [enrich_item(item, registry) for item in result.get("opportunities") or []]
    previous = load_previous(previous_path)
    result["archive"] = merge_archive(result["opportunities"], previous, today)
    result["counts"]["archive"] = len(result["archive"])
    result["presentationVersion"] = "0.2.4"
    return result


def render_markdown(result: dict[str, Any]) -> str:
    counts = result["counts"]
    lines = [
        "# Radar Opportunità Versilia — v0.2.4",
        "",
        f"Data di riferimento: **{result['referenceDate']}**",
        "",
        (
            f"Opportunità correnti: **{len(result.get('opportunities') or [])}** · "
            f"archivio: **{counts.get('archive', 0)}** · "
            f"review interna: **{counts.get('reviewInternal', 0)}** · "
            f"quality hold interno: **{counts.get('qualityHeld', 0)}**."
        ),
        "",
        "## Opportunità correnti",
        "",
    ]
    for item in result.get("opportunities") or []:
        p = item.get("presentation") or {}
        deadline = item.get("deadline_at") or "non rilevata"
        if item.get("deadline_time"):
            deadline += f" ore {item['deadline_time']}"
        lines += [
            f"### {item['title']}",
            f"- Fonte: {p.get('source_label') or item.get('source_name')}",
            f"- Modalità: **{item.get('access_mode')}**",
            f"- Scadenza: **{deadline}**",
            f"- Descrizione: {p.get('description')}",
        ]
        if p.get("condition_label"):
            lines.append(f"- Requisito sintetico: **{p['condition_label']}**")
        lines.append("")
    lines += ["## Archivio", ""]
    if not result.get("archive"):
        lines.append("Nessun bando archiviato nello stato precedente fornito.")
    else:
        for item in result["archive"]:
            lines.append(
                f"- {item.get('title')} — {item.get('source_label')} — "
                f"{item.get('deadline_at') or 'scadenza non rilevata'} — {item.get('url')}"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--presentation", type=Path, default=DEFAULT_PRESENTATION)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)

    result = run(
        args.config,
        args.date,
        rules_path=args.rules,
        presentation_path=args.presentation,
        previous_path=args.previous,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = render_markdown(result)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
    elif not args.output:
        print(report, end="")
    return 1 if any(source["status"] == "error" for source in result["sources"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
