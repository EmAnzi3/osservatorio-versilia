#!/usr/bin/env python3
"""Genera il rapporto leggibile e machine-readable di ogni run del Radar.

Il confronto usa solo identita deterministiche e separa i cambiamenti operativi
dai campi volatili del refresh (timestamp di verifica, badge ``is_new`` ecc.).
Il comando e volutamente robusto: deve riuscire a produrre una diagnosi anche
quando scan, validazione o build non sono arrivati a conclusione.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREVIOUS = Path("/tmp/opportunity-daily-previous.json")
DEFAULT_CURRENT = ROOT / "data" / "opportunity-daily-public.json"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "runtime"

PHASE_LABELS = {
    "scan": "Scansione e riconciliazione",
    "validation": "Validazione snapshot",
    "build": "Build e controllo browser",
}

FIELD_LABELS = {
    "title": "Titolo",
    "deadline_at": "Scadenza",
    "deadline_time": "Ora scadenza",
    "opens_at": "Apertura",
    "status": "Stato",
    "lifecycle_stage": "Ciclo di vita",
    "eligibility": "Ammissibilita",
    "access_mode": "Modalita di accesso",
    "municipality_role": "Ruolo del Comune",
    "partnership_required": "Partenariato richiesto",
    "source_id": "Fonte",
    "source_name": "Nome fonte",
    "publisher": "Ente pubblicatore",
    "url": "URL ufficiale",
    "summary": "Sintesi",
    "beneficiary_text": "Beneficiari",
    "themes": "Temi",
    "municipality_eligibility": "Comuni interessati",
}


def incomplete_run_stages(statuses: dict[str, str | None]) -> dict[str, str | None]:
    """Restituisce ogni stadio non concluso con successo, senza short-circuit."""
    return {name: status for name, status in statuses.items() if status != "success"}


def _load_optional(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, f"File assente: {path}"
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"File non leggibile: {path} ({exc})"
    if not isinstance(payload, dict):
        return {}, f"Contenuto JSON non valido: {path}"
    return payload, None


def _fold(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(
        char for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _normalized_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = urlsplit(text)
    path = re.sub(r"/+", "/", parsed.path).rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))


def _identity(item: dict[str, Any]) -> str:
    for field, prefix in (("coverage_id", "coverage"), ("rule_id", "rule")):
        value = str(item.get(field) or "").strip()
        if value:
            return f"{prefix}:{value}"
    value = _normalized_url(item.get("url"))
    if value:
        return "url:" + value
    value = str(item.get("id") or "").strip()
    if value:
        return "id:" + value
    return "title:" + _fold(item.get("title"))


def _match_items(
    previous: list[dict[str, Any]],
    current: list[dict[str, Any]],
) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Abbina record solo con chiavi esatte e non ambigue.

    I passaggi sono ordinati dalla chiave piu forte al fallback sul titolo
    normalizzato. Il fallback si applica soltanto se il titolo e unico in
    entrambi gli snapshot: nessun fuzzy matching e nessuna scelta arbitraria.
    """
    prev_left = set(range(len(previous)))
    curr_left = set(range(len(current)))
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    key_functions: list[Callable[[dict[str, Any]], str]] = [
        lambda item: str(item.get("coverage_id") or "").strip(),
        lambda item: str(item.get("rule_id") or "").strip(),
        lambda item: str(item.get("id") or "").strip(),
        lambda item: _normalized_url(item.get("url")),
        lambda item: _fold(item.get("title")),
    ]

    for key_function in key_functions:
        prev_index: dict[str, list[int]] = {}
        curr_index: dict[str, list[int]] = {}
        for index in prev_left:
            key = key_function(previous[index])
            if key:
                prev_index.setdefault(key, []).append(index)
        for index in curr_left:
            key = key_function(current[index])
            if key:
                curr_index.setdefault(key, []).append(index)
        for key in sorted(set(prev_index) & set(curr_index)):
            if len(prev_index[key]) != 1 or len(curr_index[key]) != 1:
                continue
            old_index = prev_index[key][0]
            new_index = curr_index[key][0]
            pairs.append((previous[old_index], current[new_index]))
            prev_left.remove(old_index)
            curr_left.remove(new_index)

    return (
        pairs,
        [current[index] for index in sorted(curr_left)],
        [previous[index] for index in sorted(prev_left)],
    )


def _municipalities(value: Any) -> list[str]:
    result: list[str] = []
    for town, entry in (value or {}).items():
        status = str((entry or {}).get("status") or "")
        if status in {"eligible", "conditional"}:
            result.append(f"{town} ({status})")
    return sorted(result)


def _canonical(field: str, value: Any) -> Any:
    if field == "url":
        return _normalized_url(value)
    if field == "themes":
        return sorted(str(item) for item in (value or []))
    if field == "municipality_eligibility":
        return _municipalities(value)
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    return value


def _display(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if value is True:
        return "Si"
    if value is False:
        return "No"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "—"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _changes(old: dict[str, Any], new: dict[str, Any]) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for field, label in FIELD_LABELS.items():
        before = _canonical(field, old.get(field))
        after = _canonical(field, new.get(field))
        if before == after:
            continue
        changes.append({
            "field": field,
            "label": label,
            "before": _display(before),
            "after": _display(after),
        })
    return changes


def _compact(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "identity": _identity(item),
        "title": str(item.get("title") or "Senza titolo"),
        "source": str(item.get("source_name") or item.get("publisher") or item.get("source_id") or "Fonte non indicata"),
        "sourceId": str(item.get("source_id") or ""),
        "deadline": item.get("deadline_at"),
        "url": str(item.get("url") or ""),
    }


def _archive_keys(item: dict[str, Any]) -> set[str]:
    keys = {_identity(item)}
    raw_identity = str(item.get("identity_key") or "").strip()
    if raw_identity:
        keys.add(raw_identity)
        if raw_identity.startswith("rule:coverage:"):
            keys.add(raw_identity[len("rule:"):])
    item_id = str(item.get("id") or "").strip()
    if item_id:
        keys.add("id:" + item_id)
    title = _fold(item.get("title"))
    if title:
        keys.add("title:" + title)
    return keys


def _is_archived(item: dict[str, Any], archive: list[dict[str, Any]]) -> bool:
    item_keys = _archive_keys(item)
    return any(not item_keys.isdisjoint(_archive_keys(row)) for row in archive)


def _gate_summary(
    current: dict[str, Any],
    diagnostic: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    if diagnostic and diagnostic.get("gateSummary"):
        summary = diagnostic.get("gateSummary") or {}
        return [
            {
                "name": "Continuita",
                "status": "pass" if int(summary.get("continuityHoldCount") or 0) == 0 else "fail",
                "detail": f"{int(summary.get('continuityHoldCount') or 0)} in hold",
            },
            {
                "name": "Copertura",
                "status": str(summary.get("coverageAuditStatus") or "unknown"),
                "detail": f"{int(summary.get('runtimeUncoveredFamilyCount') or 0)} famiglie runtime scoperte",
            },
            {
                "name": "Regione Toscana",
                "status": str(summary.get("regionalCompletenessStatus") or "unknown"),
                "detail": f"{len((diagnostic.get('regionalCompleteness') or {}).get('overdue') or [])} candidati oltre finestra",
            },
            {
                "name": "Backtest",
                "status": "pass" if summary.get("backtestPassed") is True else "fail",
                "detail": "stato acquisito dalla diagnostica del run",
            },
            {
                "name": "Verifiche dirette",
                "status": "pass" if int(summary.get("coverageHoldCount") or 0) == 0 else "fail",
                "detail": f"{int(summary.get('coverageHoldCount') or 0)} in hold",
            },
        ]
    continuity = current.get("continuityReconciliation") or {}
    coverage = current.get("coverageAudit") or {}
    regional = current.get("regionalCompleteness") or {}
    backtest = current.get("backtest") or {}
    gates = [
        {
            "name": "Continuita",
            "status": "pass" if not current.get("continuityHold") and int(continuity.get("remaining") or 0) == 0 else "fail",
            "detail": f"{continuity.get('reconciled', 0)} riconciliate; {continuity.get('remaining', 0)} irrisolte",
        },
        {
            "name": "Copertura",
            "status": str(coverage.get("status") or "unknown"),
            "detail": f"{len(coverage.get('runtimeUncoveredFamilies') or [])} famiglie runtime scoperte",
        },
        {
            "name": "Regione Toscana",
            "status": str(regional.get("status") or "unknown"),
            "detail": f"{len(regional.get('overdue') or [])} candidati oltre finestra",
        },
        {
            "name": "Backtest",
            "status": "pass" if backtest.get("passed") is True else "fail",
            "detail": f"recall {backtest.get('recall', 'n.d.')}",
        },
        {
            "name": "Verifiche dirette",
            "status": "pass" if not current.get("coverageHold") else "fail",
            "detail": f"{len(current.get('coverageHold') or [])} in hold",
        },
    ]
    return gates


def build_report(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    phase_statuses: dict[str, str],
    previous_error: str | None = None,
    current_error: str | None = None,
    diagnostic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    previous_items = list(previous.get("opportunities") or [])
    current_items = list(current.get("opportunities") or [])
    pairs, added_raw, removed_raw = _match_items(previous_items, current_items)

    modified = []
    for old, new in pairs:
        changes = _changes(old, new)
        if changes:
            modified.append({**_compact(new), "changes": changes})
    modified.sort(key=lambda item: (item["deadline"] or "9999-99-99", item["title"]))

    added = sorted(
        (_compact(item) for item in added_raw),
        key=lambda item: (item["deadline"] or "9999-99-99", item["title"]),
    )
    archive = list(current.get("archive") or [])
    archived = sorted(
        (_compact(item) for item in removed_raw if _is_archived(item, archive)),
        key=lambda item: (item["deadline"] or "9999-99-99", item["title"]),
    )
    removed = sorted(
        (_compact(item) for item in removed_raw if not _is_archived(item, archive)),
        key=lambda item: (item["deadline"] or "9999-99-99", item["title"]),
    )

    scan_succeeded = phase_statuses.get("scan") == "success"
    gates = _gate_summary(current, diagnostic if not scan_succeeded else None) if current or diagnostic else []
    transport_payload = diagnostic if diagnostic and not scan_succeeded else current
    transport = transport_payload.get("transportAudit") or {}
    transport_summary = transport.get("summary") or {}
    source_rows = []
    for source in transport.get("sources") or []:
        if source.get("effectiveStatus") == "ok" and not source.get("graceUsed") and not source.get("failureClasses"):
            continue
        source_rows.append({
            "sourceId": source.get("sourceId"),
            "runtimeStatus": source.get("runtimeStatus"),
            "effectiveStatus": source.get("effectiveStatus"),
            "graceUsed": bool(source.get("graceUsed")),
            "consecutiveFailures": int(source.get("consecutiveFailures") or 0),
            "failureClasses": list(source.get("failureClasses") or []),
        })

    phase_failed = bool(incomplete_run_stages(phase_statuses))
    gate_failed = any(gate["status"] == "fail" for gate in gates)
    load_errors = [error for error in (previous_error, current_error) if error]
    failure_reasons = list(load_errors)
    diagnostic_error = str((diagnostic or {}).get("error") or "").strip()
    if diagnostic_error:
        failure_reasons.append(diagnostic_error)
    if phase_failed or gate_failed or load_errors:
        overall = "fail"
    elif int(transport_summary.get("sourcesInGrace") or 0) or int(transport_summary.get("unhealthySources") or 0):
        overall = "pass_with_warnings"
    else:
        overall = "pass"

    identity_lines = [item["identity"] for item in added + archived + removed]
    identity_lines.extend(
        item["identity"] + ":" + ",".join(change["field"] for change in item["changes"])
        for item in modified
    )
    fingerprint = hashlib.sha256("\n".join(sorted(identity_lines)).encode("utf-8")).hexdigest()[:16]

    return {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "referenceDate": current.get("referenceDate") or previous.get("referenceDate"),
        "overallStatus": overall,
        "phases": [
            {"name": name, "label": PHASE_LABELS[name], "status": phase_statuses[name]}
            for name in PHASE_LABELS
        ],
        "counts": {
            "previous": len(previous_items),
            "current": len(current_items),
            "added": len(added),
            "modified": len(modified),
            "archived": len(archived),
            "removed": len(removed),
            "unchanged": len(pairs) - len(modified),
        },
        "comparisonAvailable": scan_succeeded and current_error is None,
        "fingerprint": fingerprint,
        "added": added,
        "modified": modified,
        "archived": archived,
        "removed": removed,
        "gates": gates,
        "sourceHealth": {
            "configuredSources": int(transport_summary.get("configuredSources") or 0),
            "configuredEndpoints": int(transport_summary.get("configuredEndpoints") or 0),
            "fallbackSuccesses": int(transport_summary.get("fallbackSuccesses") or 0),
            "endpointFailures": int(transport_summary.get("endpointFailures") or 0),
            "sourcesInGrace": int(transport_summary.get("sourcesInGrace") or 0),
            "unhealthySources": int(transport_summary.get("unhealthySources") or 0),
            "attention": sorted(source_rows, key=lambda row: str(row.get("sourceId") or "")),
        },
        "diagnostic": diagnostic or {},
        "errors": load_errors,
        "failureReasons": failure_reasons,
    }


def _status_label(value: str) -> str:
    return {
        "pass": "PASS",
        "pass_with_warnings": "PASS CON ANOMALIE GESTITE",
        "fail": "FAIL",
        "success": "PASS",
        "failure": "FAIL",
        "skipped": "NON ESEGUITO",
        "unknown": "SCONOSCIUTO",
        "degraded": "DEGRADATO",
    }.get(str(value), str(value).upper())


def _markdown_link(item: dict[str, Any]) -> str:
    title = str(item.get("title") or "Senza titolo").replace("|", "\\|")
    url = str(item.get("url") or "")
    return f"[{title}]({url})" if url else title


def render_markdown(report: dict[str, Any], *, detail_limit: int = 25) -> str:
    counts = report["counts"]
    health = report["sourceHealth"]
    lines = [
        "# Radar Opportunita · rapporto del run",
        "",
        f"**Esito: {_status_label(report['overallStatus'])}** · data dati **{report.get('referenceDate') or 'n.d.'}** · fingerprint `{report['fingerprint']}`",
        "",
        "| Nuove | Modificate | Archiviate | Rimosse | Correnti |",
        "|---:|---:|---:|---:|---:|",
        f"| **{counts['added']}** | **{counts['modified']}** | **{counts['archived']}** | **{counts['removed']}** | **{counts['current']}** |",
        "",
        f"Snapshot precedente: **{counts['previous']}** -> snapshot corrente: **{counts['current']}**; record invariati: **{counts['unchanged']}**.",
    ]
    if not report.get("comparisonAvailable"):
        lines.extend([
            "",
            "> Il confronto dei contenuti non e conclusivo: la scansione non ha prodotto uno snapshot validabile. I conteggi delle variazioni rappresentano il file rimasto nel workspace, non nuove decisioni del Radar.",
        ])
    if report.get("failureReasons"):
        lines.extend(["", "## Motivo del blocco", ""])
        lines.extend(f"- {reason}" for reason in report["failureReasons"])
    lines.extend(["", "## Fasi e gate", "", "| Controllo | Esito | Dettaglio |", "|---|---|---|"])
    for phase in report["phases"]:
        lines.append(f"| {phase['label']} | **{_status_label(phase['status'])}** | — |")
    for gate in report["gates"]:
        lines.append(f"| {gate['name']} | **{_status_label(gate['status'])}** | {gate['detail']} |")

    lines.extend([
        "",
        "## Salute fonti",
        "",
        (
            f"Fonti configurate **{health['configuredSources']}** · endpoint **{health['configuredEndpoints']}** · "
            f"fallback riusciti **{health['fallbackSuccesses']}** · failure endpoint **{health['endpointFailures']}** · "
            f"fonti in grace **{health['sourcesInGrace']}** · unhealthy **{health['unhealthySources']}**."
        ),
    ])
    if health["attention"]:
        lines.extend(["", "| Fonte | Runtime | Effettivo | Grace | Failure consecutivi | Classi errore |", "|---|---|---|---:|---:|---|"])
        for source in health["attention"]:
            lines.append(
                f"| `{source['sourceId']}` | {source['runtimeStatus']} | {source['effectiveStatus']} | "
                f"{'Si' if source['graceUsed'] else 'No'} | {source['consecutiveFailures']} | "
                f"{', '.join(source['failureClasses']) or '—'} |"
            )

    sections = (
        ("Nuove opportunita", "added"),
        ("Record modificati", "modified"),
        ("Opportunita archiviate", "archived"),
        ("Record rimossi senza archiviazione", "removed"),
    )
    for title, key in sections:
        items = report[key]
        lines.extend(["", f"## {title} ({len(items)})", ""])
        if not items:
            lines.append("Nessun record.")
            continue
        lines.extend(["| Fonte | Scadenza | Opportunita | Dettaglio |", "|---|---|---|---|"])
        for item in items[:detail_limit]:
            detail = "—"
            if key == "modified":
                detail = "<br>".join(
                    f"**{change['label']}:** {change['before']} -> {change['after']}"
                    for change in item["changes"]
                )
            lines.append(
                f"| {item['source']} | {item['deadline'] or '—'} | {_markdown_link(item)} | {detail} |"
            )
        if len(items) > detail_limit:
            lines.append(f"\n_Altri {len(items) - detail_limit} record sono disponibili nel report HTML/JSON._")

    if report["errors"]:
        lines.extend(["", "## Errori di acquisizione del report", ""])
        lines.extend(f"- {error}" for error in report["errors"])
    return "\n".join(lines).rstrip() + "\n"


def _html_table(title: str, items: list[dict[str, Any]], *, modified: bool = False) -> str:
    rows = []
    for item in items:
        link = html.escape(str(item.get("title") or "Senza titolo"))
        if item.get("url"):
            link = f'<a href="{html.escape(str(item["url"]), quote=True)}" target="_blank" rel="noopener noreferrer">{link}</a>'
        detail = "—"
        if modified:
            detail = "<ul>" + "".join(
                "<li><strong>" + html.escape(change["label"]) + ":</strong> "
                + html.escape(change["before"]) + " -> " + html.escape(change["after"]) + "</li>"
                for change in item.get("changes") or []
            ) + "</ul>"
        rows.append(
            "<tr><td>" + html.escape(str(item.get("source") or "—")) + "</td><td>"
            + html.escape(str(item.get("deadline") or "—")) + "</td><td>" + link
            + "</td><td>" + detail + "</td></tr>"
        )
    body = "".join(rows) if rows else '<tr><td colspan="4">Nessun record.</td></tr>'
    return (
        f"<section><h2>{html.escape(title)} ({len(items)})</h2>"
        "<table><thead><tr><th>Fonte</th><th>Scadenza</th><th>Opportunita</th><th>Dettaglio</th></tr></thead>"
        f"<tbody>{body}</tbody></table></section>"
    )


def render_html(report: dict[str, Any]) -> str:
    counts = report["counts"]
    health = report["sourceHealth"]
    phase_rows = "".join(
        f"<tr><td>{html.escape(row['label'])}</td><td><strong>{html.escape(_status_label(row['status']))}</strong></td><td>—</td></tr>"
        for row in report["phases"]
    )
    gate_rows = "".join(
        f"<tr><td>{html.escape(row['name'])}</td><td><strong>{html.escape(_status_label(row['status']))}</strong></td><td>{html.escape(row['detail'])}</td></tr>"
        for row in report["gates"]
    )
    source_rows = "".join(
        "<tr><td><code>" + html.escape(str(row.get("sourceId") or "")) + "</code></td><td>"
        + html.escape(str(row.get("runtimeStatus") or "")) + "</td><td>"
        + html.escape(str(row.get("effectiveStatus") or "")) + "</td><td>"
        + ("Si" if row.get("graceUsed") else "No") + "</td><td>"
        + html.escape(str(row.get("consecutiveFailures") or 0)) + "</td><td>"
        + html.escape(", ".join(row.get("failureClasses") or []) or "—") + "</td></tr>"
        for row in health["attention"]
    ) or '<tr><td colspan="6">Nessuna fonte richiede attenzione.</td></tr>'
    status_class = "ok" if report["overallStatus"] == "pass" else ("warn" if report["overallStatus"] == "pass_with_warnings" else "fail")
    generated = html.escape(str(report.get("generatedAt") or ""))
    comparison_warning = "" if report.get("comparisonAvailable") else (
        '<section><h2>Confronto non conclusivo</h2><p>La scansione non ha prodotto uno snapshot validabile. '
        'I conteggi delle variazioni rappresentano il file rimasto nel workspace.</p></section>'
    )
    failure_reasons = ""
    if report.get("failureReasons"):
        failure_reasons = "<section><h2>Motivo del blocco</h2><ul>" + "".join(
            "<li>" + html.escape(str(reason)) + "</li>" for reason in report["failureReasons"]
        ) + "</ul></section>"
    return f"""<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Radar Opportunita - rapporto del run</title>
<style>
body{{font-family:Arial,sans-serif;color:#111827;background:#f3f6f8;line-height:1.45;margin:0;padding:24px}}main{{max-width:1500px;margin:auto}}h1{{margin-bottom:4px}}.small{{color:#6b7280;font-size:13px}}.status{{display:inline-block;border-radius:999px;padding:7px 12px;font-weight:800}}.ok{{background:#dcfce7;color:#166534}}.warn{{background:#fef3c7;color:#92400e}}.fail{{background:#fee2e2;color:#991b1b}}.cards{{display:grid;grid-template-columns:repeat(5,minmax(140px,1fr));gap:12px;margin:18px 0 24px}}.card,section{{border:1px solid #d1d5db;border-radius:14px;background:white}}.card{{padding:14px}}.card strong{{display:block;font-size:28px}}section{{padding:18px;margin-bottom:20px;overflow-x:auto}}table{{border-collapse:collapse;width:100%;margin:12px 0 8px;font-size:13px}}th,td{{border-bottom:1px solid #e5e7eb;padding:8px;vertical-align:top}}th{{background:#f9fafb;text-align:left;position:sticky;top:0}}a{{color:#0f766e;font-weight:700;text-decoration:none}}ul{{margin:0;padding-left:18px}}@media(max-width:800px){{body{{padding:12px}}.cards{{grid-template-columns:repeat(2,minmax(130px,1fr))}}}}
</style></head><body><main>
<h1>Radar Opportunita - rapporto del run</h1><p class="small">Generato {generated} · dati {html.escape(str(report.get('referenceDate') or 'n.d.'))} · fingerprint {html.escape(report['fingerprint'])}</p>
<p><span class="status {status_class}">{html.escape(_status_label(report['overallStatus']))}</span></p>
<div class="cards"><div class="card"><strong>{counts['added']}</strong>Nuove</div><div class="card"><strong>{counts['modified']}</strong>Modificate</div><div class="card"><strong>{counts['archived']}</strong>Archiviate</div><div class="card"><strong>{counts['removed']}</strong>Rimosse</div><div class="card"><strong>{counts['current']}</strong>Correnti</div></div>
<section><h2>Riepilogo</h2><p>Record precedenti: <strong>{counts['previous']}</strong> -> record correnti: <strong>{counts['current']}</strong><br>Record invariati: <strong>{counts['unchanged']}</strong></p></section>
{comparison_warning}{failure_reasons}
<section><h2>Fasi e gate</h2><table><thead><tr><th>Controllo</th><th>Esito</th><th>Dettaglio</th></tr></thead><tbody>{phase_rows}{gate_rows}</tbody></table></section>
<section><h2>Salute fonti</h2><p>Fonti <strong>{health['configuredSources']}</strong> · endpoint <strong>{health['configuredEndpoints']}</strong> · fallback riusciti <strong>{health['fallbackSuccesses']}</strong> · failure endpoint <strong>{health['endpointFailures']}</strong> · in grace <strong>{health['sourcesInGrace']}</strong> · unhealthy <strong>{health['unhealthySources']}</strong>.</p><table><thead><tr><th>Fonte</th><th>Runtime</th><th>Effettivo</th><th>Grace</th><th>Failure consecutivi</th><th>Classi errore</th></tr></thead><tbody>{source_rows}</tbody></table></section>
{_html_table('Nuove opportunita', report['added'])}
{_html_table('Record modificati', report['modified'], modified=True)}
{_html_table('Opportunita archiviate', report['archived'])}
{_html_table('Record rimossi senza archiviazione', report['removed'])}
</main></body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", type=Path, default=DEFAULT_PREVIOUS)
    parser.add_argument("--current", type=Path, default=DEFAULT_CURRENT)
    parser.add_argument("--diagnostic", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scan-status", default="unknown")
    parser.add_argument("--validation-status", default="unknown")
    parser.add_argument("--build-status", default="unknown")
    args = parser.parse_args()

    previous, previous_error = _load_optional(args.previous)
    current, current_error = _load_optional(args.current)
    diagnostic: dict[str, Any] = {}
    if args.diagnostic:
        diagnostic, _ = _load_optional(args.diagnostic)
    report = build_report(
        previous,
        current,
        phase_statuses={
            "scan": args.scan_status,
            "validation": args.validation_status,
            "build": args.build_status,
        },
        previous_error=previous_error,
        current_error=current_error,
        diagnostic=diagnostic,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "opportunity-run-report.json"
    markdown_path = args.output_dir / "opportunity-run-report.md"
    html_path = args.output_dir / "opportunity-run-report.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    counts = report["counts"]
    print(
        f"Report Radar: {_status_label(report['overallStatus'])} · "
        f"+{counts['added']} nuove · {counts['modified']} modificate · "
        f"{counts['archived']} archiviate · {counts['removed']} rimosse · {counts['current']} correnti"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
