#!/usr/bin/env python3
"""Sonda generica di pagine e file di una fonte, eseguita sui runner GitHub.

`update_source_data.py source-probe --name NOME --url URL [--follow REGEX]`
scarica la pagina o il file e scrive in `data/source-probes/NOME.json` cosa
contiene: per una pagina HTML i collegamenti (e, con `--follow`, la stessa
analisi dei collegamenti che corrispondono); per un foglio Excel i fogli, le
prime righe e le righe dei sette Comuni, della Toscana e dell'Italia; per un
archivio zip l'elenco dei file e l'analisi dei fogli contenuti. Non modifica il
catalogo: serve a scrivere poi l'aggiornatore sul formato reale della fonte.
"""
from __future__ import annotations

import hashlib
import html as htmllib
import io
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "Mozilla/5.0 (compatible; OsservatorioVersilia-data-audit/1.0)"}
CODES = ("046005", "046013", "046018", "046024", "046028", "046030", "046033")
NAMES = ("CAMAIORE", "FORTE DEI MARMI", "MASSAROSA", "PIETRASANTA", "SERAVEZZA", "STAZZEMA", "VIAREGGIO", "TOSCANA", "ITALIA", "LUCCA")
MAX_FOLLOW = 8
HEAD_ROWS = 6
MAX_HITS = 80


def fetch(url: str, tries: int = 3) -> tuple[bytes, str]:
    error: Exception | None = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
                return r.read(), r.headers.get("Content-Type", "")
        except Exception as exc:  # noqa: BLE001 - la sonda registra ogni errore
            error = exc
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"{type(error).__name__}: {error}")


def cell(v: Any) -> Any:
    return v if v is None or isinstance(v, (int, float, bool)) else str(v)[:120]


def hit(row: list[Any]) -> bool:
    text = " ".join(str(v) for v in row if v is not None).upper()
    return any(c in text for c in CODES) or any(re.search(rf"\b{n}\b", text) for n in NAMES)


def workbook(data: bytes) -> dict[str, Any]:
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    sheets = []
    for ws in wb.worksheets:
        head, hits, count = [], [], 0
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            count += 1
            values = [cell(v) for v in row]
            while values and values[-1] is None:
                values.pop()
            if i < HEAD_ROWS:
                head.append(values)
            elif len(hits) < MAX_HITS and hit(values):
                hits.append([i + 1, values])
        sheets.append({"name": ws.title, "rows": count, "head": head, "hits": hits})
    return {"sheets": sheets}


def links(page: str, url: str) -> list[dict[str, str]]:
    out, seen = [], set()
    for m in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", page, flags=re.I | re.S):
        href = urllib.parse.urljoin(url, htmllib.unescape(m.group(1)))
        if href in seen or href.startswith(("javascript:", "mailto:")):
            continue
        seen.add(href)
        out.append({"url": href, "text": re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip()[:200]})
    return out


def forms(page: str, url: str) -> list[dict[str, Any]]:
    out = []
    for m in re.finditer(r"<form\b([^>]*)>(.*?)</form>", page, flags=re.I | re.S):
        attrs, body = m.group(1), m.group(2)
        def attr(name: str, text: str) -> str:
            found = re.search(rf"\b{name}\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))", text, re.I)
            return next((g for g in found.groups() if g is not None), "") if found else ""
        fields = []
        for f in re.finditer(r"<(input|select|textarea)\b([^>]*)>(.*?)(?=<(?:input|select|textarea)\b|</form>|$)", body, flags=re.I | re.S):
            options = [[attr("value", o.group(1)), re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", o.group(2))).strip()[:60]]
                       for o in re.finditer(r"<option\b([^>]*)>([^<]*)", f.group(3), flags=re.I)][:40]
            fields.append({"tag": f.group(1).lower(), "name": attr("name", f.group(2)), "type": attr("type", f.group(2)),
                           "value": attr("value", f.group(2))[:120], "options": options})
        out.append({"action": urllib.parse.urljoin(url, attr("action", attrs)), "method": attr("method", attrs) or "get", "fields": fields[:40]})
    return out[:10]


def analyse(url: str, follow: str | None, depth: int = 0) -> dict[str, Any]:
    item: dict[str, Any] = {"url": url}
    try:
        data, ctype = fetch(url)
    except RuntimeError as exc:
        item["error"] = str(exc)
        return item
    item.update(contentType=ctype, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    try:
        if data[:2] == b"PK" and b"xl/" in data[:4000]:
            item["workbook"] = workbook(data)
        elif data[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                item["members"] = [{"name": i.filename, "bytes": i.file_size} for i in z.infolist()]
                item["memberWorkbooks"] = {n: workbook(z.read(n)) for n in z.namelist() if n.lower().endswith((".xlsx", ".xlsm"))}
        else:
            page = data.decode("utf-8", errors="replace")
            ls = links(page, url)
            item["forms"] = forms(page, url)
            item["scripts"] = [urllib.parse.urljoin(url, s) for s in re.findall(r"<script\b[^>]*src=[\"']([^\"']+)", page, flags=re.I)][:20]
            item["inlineScript"] = "\n".join(re.findall(r"<script\b[^>]*>(.*?)</script>", page, flags=re.I | re.S))[:6000]
            item["links"] = [l for l in ls if re.search(r"\.(xlsx?|zip|csv|ods|pdf)\b", l["url"], re.I) or (follow and re.search(follow, l["url"] + " " + l["text"], re.I))]
            if follow and depth == 0:
                targets = [l["url"] for l in ls if re.search(follow, l["url"] + " " + l["text"], re.I)][:MAX_FOLLOW]
                item["followed"] = [analyse(t, follow, depth + 1) for t in targets]
    except Exception as exc:  # noqa: BLE001
        item["parseError"] = f"{type(exc).__name__}: {exc}"
    return item


def run(name: str, url: str, follow: str | None = None) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", name):
        raise RuntimeError("Nome della sonda non valido: minuscole, cifre e trattini")
    path = ROOT / "data" / "source-probes" / f"{name}.json"
    probe = {"schemaVersion": 1, "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "note": "Sonda: struttura della fonte consultata; non è un dato pubblicato.", "follow": follow,
             "result": analyse(url, follow)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(probe, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Sonda {name} scritta in {path.relative_to(ROOT)}")
    return path
