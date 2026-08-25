#!/usr/bin/env python3
"""Riconcilia i continuity hold dopo tutte le iniezioni v0.4/v0.4.4.

La continuità base viene calcolata dal motore v0.3 prima che le opportunità
coverage-first vengano reiniettate. Questo passaggio finale rimuove soltanto i
hold la cui identità è nuovamente presente nell'output corrente o nell'archivio.
Non usa similarità fuzzy e non nasconde vere scomparse.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any
from urllib.parse import urlsplit, urlunsplit


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
    identity_key = str(item.get("identity_key") or "").strip()
    if identity_key:
        aliases.add(identity_key)

    coverage_id = str(item.get("coverage_id") or "").strip()
    if coverage_id:
        aliases.add("coverage:" + coverage_id)
        aliases.add("rule:coverage:" + coverage_id)

    rule_id = str(item.get("rule_id") or "").strip()
    if rule_id:
        aliases.add("rule:" + rule_id)

    item_id = str(item.get("id") or "").strip()
    if item_id:
        aliases.add("id:" + item_id)

    url = _normalized_url(item.get("url"))
    if url:
        aliases.add("url:" + url)

    title = _fold(item.get("title"))
    deadline = str(item.get("deadline_at") or "").strip()
    if title and deadline:
        aliases.add(f"title:{title}|deadline:{deadline}")
    return aliases


def reconcile_final_continuity(result: dict[str, Any]) -> dict[str, Any]:
    """Rimuove solo hold già rappresentati a fine pipeline.

    Un hold è riconciliato se condivide almeno un'identità deterministica con
    una opportunità corrente oppure con una voce d'archivio. Gli hold realmente
    irrisolti restano invariati e continuano a bloccare la pubblicazione.
    """
    holds = list(result.get("continuityHold") or [])
    represented: set[str] = set()
    for field in ("opportunities", "archive"):
        for item in result.get(field) or []:
            represented.update(_aliases(item))

    remaining: list[dict[str, Any]] = []
    reconciled: list[dict[str, Any]] = []
    for hold in holds:
        aliases = _aliases(hold)
        if aliases and not aliases.isdisjoint(represented):
            reconciled.append(hold)
        else:
            remaining.append(hold)

    result["continuityHold"] = remaining
    result.setdefault("counts", {})["continuityHold"] = len(remaining)
    result["continuityReconciliation"] = {
        "before": len(holds),
        "reconciled": len(reconciled),
        "remaining": len(remaining),
    }
    return result
