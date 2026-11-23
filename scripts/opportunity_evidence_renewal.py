#!/usr/bin/env python3
"""Rinnovo delle prove di copertura dal run corrente (audit v0.4.3 e v0.4.4).

Una prova manuale (pagina ufficiale verificata a mano) scade dopo `maxEvidenceAgeDays`. Il run la rinnova da solo
in due casi, entrambi osservati oggi:
- `signals`: la fonte risponde (`ok`/`degraded`) e produce segnalazioni;
- `evidence_page`: la pagina ufficiale della prova è stata letta con successo in questo run (stesso URL o URL
  finale dopo il redirect). Vale per le fonti che sorvegliano una sola pagina e oggi non hanno novità (Erasmus+,
  CEF, Horizon), che altrimenti scadrebbero pur essendo raggiunte ogni giorno.
Una fonte in errore, o una pagina della prova non letta, non rinnova nulla.
"""
from __future__ import annotations

from typing import Any


def _norm(url: Any) -> str:
    return str(url or "").strip().rstrip("/").lower()


def _fetched_ok() -> set[str]:
    try:
        import opportunity_discovery_resilient as discovery
    except Exception:  # pragma: no cover - modulo di trasporto assente (test isolati)
        return set()
    urls: set[str] = set()
    for trace in discovery.FETCH_TRACE.values():
        if trace.get("status") == "ok":
            urls.update(_norm(u) for u in (trace.get("url"), trace.get("resolvedUrl")) if u)
    return urls


def renewal(runtime_row: dict[str, Any] | None, evidence_url: Any) -> str | None:
    """Motivo del rinnovo («signals» | «evidence_page») o None."""
    row = runtime_row or {}
    status = str(row.get("runtimeStatus") or "")
    if status in {"ok", "degraded"} and int(row.get("candidateCount") or 0) > 0:
        return "signals"
    if status in {"ok", "degraded"} and evidence_url and _norm(evidence_url) in _fetched_ok():
        return "evidence_page"
    return None
