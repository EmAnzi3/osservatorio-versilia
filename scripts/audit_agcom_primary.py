#!/usr/bin/env python3
"""Verifica i conteggi assoluti FTTH sul dataset comunale primario AGCOM.

Il controllo scopre la distribuzione comunale corrente solo da endpoint
ufficiali AGCOM, valida strettamente il CSV prima di usarlo e non ricostruisce
mai conteggi assoluti dalle percentuali.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_agid_indicators as base  # noqa: E402

PUBLIC_MAP_URL = "https://maps.agcom.it/"
# Alias pubblico/canonico usato dai materializzatori e dal source registry.
AI_READY_PAGE = PUBLIC_MAP_URL
LEGACY_CSV_URL = (
    "https://geo.agcom.it/arcgis/sharing/rest/content/items/"
    "25830559c5784c1eb5eb1cf748889f4c/data"
)
PORTAL_SEARCH_URL = "https://geo.agcom.it/arcgis/sharing/rest/search"
DISCOVERY_ENTRY_URLS = (
    PUBLIC_MAP_URL,
    "https://geo.agcom.it/",
    "https://geo.agcom.it/reportistica/",
    "https://geo.agcom.it/reportistica/index.html",
    "https://geo.agcom.it/reportistica/ai/ai_251231_260210_comuni.html",
)
AGCOM_HOSTS = {"geo.agcom.it", "maps.agcom.it"}
PORTAL_SEARCH_TERMS = (
    "reportistica comuni",
    "BBmap comuni",
    "FTTH comuni",
)
FETCH_ATTEMPTS = 3
FETCH_RETRY_SECONDS = 2
MAX_DISCOVERY_PAGES = 12
MAX_DISCOVERY_DEPTH = 2
MIN_PRIMARY_ROWS = 7000
MAX_PORTAL_ITEM_AGE_DAYS = 400


def fetch_bytes(url: str, accept: str = "*/*", timeout: int = 120) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": base.USER_AGENT, "Accept": accept},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _is_official_agcom_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return False
    return parsed.scheme == "https" and (parsed.hostname or "").lower() in AGCOM_HOSTS


def _is_csv_candidate(url: str) -> bool:
    if not _is_official_agcom_url(url):
        return False
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()
    if re.search(
        r"/arcgis/sharing/rest/content/items/[a-f0-9]{32}/data$",
        path,
        flags=re.IGNORECASE,
    ):
        return True
    return path.endswith(".csv")


def _is_discovery_page(url: str) -> bool:
    if not _is_official_agcom_url(url):
        return False
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()
    if "/reportistica" not in path:
        return False
    if any(path.endswith(suffix) for suffix in (".pdf", ".csv", ".zip", ".xlsx", ".xls")):
        return False
    return True


def _extract_official_links(page_url: str, html: str) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()

    for raw in re.findall(r"""href\s*=\s*["']([^"']+)["']""", html, flags=re.IGNORECASE):
        candidate = urllib.parse.urljoin(page_url, raw.strip())
        if _is_official_agcom_url(candidate) and candidate not in seen:
            seen.add(candidate)
            links.append(candidate)

    for raw in re.findall(
        r"https://(?:geo|maps)\.agcom\.it/arcgis/sharing/rest/content/items/[a-f0-9]{32}/data",
        html,
        flags=re.IGNORECASE,
    ):
        if raw not in seen:
            seen.add(raw)
            links.append(raw)

    return links


def _portal_candidates() -> list[tuple[str, str]]:
    """Cerca item comunali recenti nel portale ArcGIS ufficiale AGCOM."""
    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()
    min_modified_ms = int((time.time() - MAX_PORTAL_ITEM_AGE_DAYS * 86400) * 1000)

    for term in PORTAL_SEARCH_TERMS:
        query = urllib.parse.urlencode(
            {
                "f": "json",
                "num": 100,
                "sortField": "modified",
                "sortOrder": "desc",
                "q": term,
            }
        )
        url = f"{PORTAL_SEARCH_URL}?{query}"
        try:
            payload = json.loads(
                fetch_bytes(url, "application/json,*/*", timeout=45).decode(
                    "utf-8", errors="replace"
                )
            )
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            json.JSONDecodeError,
        ):
            continue

        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            continue

        for item in results:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id") or "").strip().lower()
            if not re.fullmatch(r"[a-f0-9]{32}", item_id):
                continue
            title = str(item.get("title") or "")
            item_type = str(item.get("type") or "")
            tags = item.get("tags")
            tag_text = " ".join(str(tag) for tag in tags) if isinstance(tags, list) else ""
            haystack = f"{title} {item_type} {tag_text}".lower()
            if "comun" not in haystack:
                continue
            if not any(token in haystack for token in ("report", "bbmap", "broadband", "ftth")):
                continue
            modified = item.get("modified")
            if isinstance(modified, (int, float)) and modified < min_modified_ms:
                continue
            candidate = (
                "https://geo.agcom.it/arcgis/sharing/rest/content/items/"
                f"{item_id}/data"
            )
            if candidate in seen:
                continue
            seen.add(candidate)
            candidates.append(
                (candidate, f"arcgis_portal_search:{term}:{title or item_id}")
            )
    return candidates


def _html_candidates() -> list[tuple[str, str]]:
    """Segue un numero limitato di sole pagine reportistica AGCOM ufficiali."""
    candidates: list[tuple[str, str]] = []
    seen_candidates: set[str] = set()
    visited: set[str] = set()
    queue = deque((url, 0) for url in DISCOVERY_ENTRY_URLS)

    while queue and len(visited) < MAX_DISCOVERY_PAGES:
        page_url, depth = queue.popleft()
        if page_url in visited or not _is_official_agcom_url(page_url):
            continue
        visited.add(page_url)
        try:
            html = fetch_bytes(page_url, "text/html,*/*", timeout=45).decode(
                "utf-8", errors="replace"
            )
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            continue

        for link in _extract_official_links(page_url, html):
            if _is_csv_candidate(link):
                if link not in seen_candidates:
                    seen_candidates.add(link)
                    candidates.append((link, f"official_html:{page_url}"))
                continue
            if depth < MAX_DISCOVERY_DEPTH and _is_discovery_page(link) and link not in visited:
                queue.append((link, depth + 1))

    return candidates


def discover_csv_candidates() -> list[tuple[str, str]]:
    """Restituisce candidati ufficiali, recenti e deduplicati; il legacy è ultimo."""
    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()

    for url, discovery in [*_portal_candidates(), *_html_candidates()]:
        if url in seen:
            continue
        seen.add(url)
        candidates.append((url, discovery))

    if LEGACY_CSV_URL not in seen:
        candidates.append((LEGACY_CSV_URL, "legacy_known_item_last_resort"))
    return candidates


def parse_int(value: str) -> int | None:
    raw = (value or "").strip()
    if not raw:
        return None
    raw = raw.replace(".", "").replace(",", "")
    try:
        return int(float(raw))
    except ValueError:
        return None


def parse_pct(value: str) -> float | None:
    raw = (value or "").strip().rstrip("%").replace(",", ".")
    if not raw:
        return None
    try:
        result = float(raw)
        return result if math.isfinite(result) else None
    except ValueError:
        return None


def parse_csv(body: bytes) -> dict[str, dict[str, Any]]:
    text = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = body.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise base.DataError("CSV AGCOM: encoding non riconosciuto")

    reader = csv.reader(io.StringIO(text), delimiter=";")
    header = next((row for row in reader if any(str(cell).strip() for cell in row)), None)
    if header is None:
        raise base.DataError("CSV AGCOM vuoto")

    normalized_header = [str(cell).replace("\ufeff", "").strip().lower() for cell in header]
    if len(normalized_header) < 19:
        raise base.DataError(f"CSV AGCOM: colonne inattese ({len(normalized_header)})")
    if normalized_header[3] != "pro_com":
        raise base.DataError(
            f"CSV AGCOM: schema inatteso, colonna 4={normalized_header[3]!r}"
        )

    result: dict[str, dict[str, Any]] = {}
    for raw in reader:
        if not any(str(cell).strip() for cell in raw):
            continue
        if len(raw) < 19:
            raw += [""] * (19 - len(raw))
        code = raw[3].strip().zfill(6)
        if not code.strip("0"):
            continue
        result[code] = {
            "comune": raw[2].strip(),
            "famiglie_residenti": parse_int(raw[13]),
            "famiglie_ftth": parse_int(raw[14]),
            "famiglie_ftth_20m": parse_int(raw[15]),
            "copertura_ftth_desi_pct": parse_pct(raw[16]),
            "copertura_ftth_20m_pct": parse_pct(raw[18]),
            "raw": {
                "famiglie_residenti": raw[13],
                "famiglie_ftth": raw[14],
                "famiglie_ftth_20m": raw[15],
                "copertura_ftth_desi_pct": raw[16],
                "copertura_ftth_20m_pct": raw[18],
            },
        }
    if not result:
        raise base.DataError("CSV AGCOM: nessuna riga comunale valida")
    return result


def fetch_primary_rows(url: str, attempts: int = FETCH_ATTEMPTS) -> dict[str, dict[str, Any]]:
    """Acquisisce e valida sintatticamente un candidato CSV primario."""
    failures: list[str] = []
    for attempt in range(1, attempts + 1):
        body = b""
        try:
            body = fetch_bytes(url, "text/csv,application/octet-stream,*/*")
            return parse_csv(body)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, base.DataError) as exc:
            failures.append(f"tentativo {attempt}/{attempts}: {exc}; bytes={len(body)}")
            if attempt < attempts:
                time.sleep(FETCH_RETRY_SECONDS * attempt)
    raise base.DataError(
        f"candidato non acquisibile dopo {attempts} tentativi: "
        + " | ".join(failures)
    )


def validate_primary_rows(
    rows: dict[str, dict[str, Any]],
    required_codes: set[str],
    *,
    min_rows: int = MIN_PRIMARY_ROWS,
) -> None:
    if len(rows) < min_rows:
        raise base.DataError(
            f"CSV AGCOM: copertura nazionale inattesa ({len(rows)} righe; minimo {min_rows})"
        )
    missing_codes = sorted(required_codes - set(rows))
    if missing_codes:
        raise base.DataError(
            "CSV AGCOM: Comuni Versilia mancanti: " + ", ".join(missing_codes)
        )
    for code in sorted(required_codes):
        row = rows[code]
        resident = row.get("famiglie_residenti")
        desi = row.get("copertura_ftth_desi_pct")
        within_20m = row.get("copertura_ftth_20m_pct")
        if not isinstance(resident, int) or resident <= 0:
            raise base.DataError(f"CSV AGCOM {code}: famiglie residenti non valide")
        if not isinstance(desi, (int, float)) or not 0 <= float(desi) <= 100:
            raise base.DataError(f"CSV AGCOM {code}: copertura DESI non valida")
        if not isinstance(within_20m, (int, float)) or not 0 <= float(within_20m) <= 100:
            raise base.DataError(f"CSV AGCOM {code}: copertura 20 m non valida")


def acquire_primary_rows(
    required_codes: set[str],
    *,
    attempts: int = FETCH_ATTEMPTS,
    min_rows: int = MIN_PRIMARY_ROWS,
) -> tuple[dict[str, dict[str, Any]], str, str]:
    failures: list[str] = []
    candidates = discover_csv_candidates()
    if not candidates:
        raise base.DataError("AGCOM: nessun candidato ufficiale scoperto")

    for url, discovery in candidates:
        try:
            rows = fetch_primary_rows(url, attempts=attempts)
            validate_primary_rows(rows, required_codes, min_rows=min_rows)
            return rows, url, discovery
        except base.DataError as exc:
            failures.append(f"{discovery} -> {url}: {exc}")

    raise base.DataError(
        "Nessuna distribuzione comunale AGCOM ufficiale ha superato la validazione: "
        + " || ".join(failures)
    )


def population_by_code(data: dict[str, Any]) -> dict[str, float]:
    metric = data.get("metrics", {}).get("population", {})
    result = {}
    for row in metric.get("rows", []):
        value = row.get("value")
        if isinstance(value, (int, float)) and not isinstance(value, bool) and float(value) > 0:
            result[str(row.get("code"))] = float(value)
    return result


def plausibility(population: float | None, households: int | None, reached: int | None) -> tuple[bool, str]:
    if households is None or households <= 0:
        return False, "famiglie residenti assenti o non positive"
    if reached is None:
        return False, "famiglie FTTH mancanti"
    if reached < 0 or reached > households:
        return False, "famiglie FTTH fuori intervallo rispetto alle famiglie residenti"
    if population and population > 0:
        implied = population / households
        if implied > 5:
            return False, f"{implied:.1f} residenti per famiglia impliciti (>5)"
        return True, f"{implied:.2f} residenti per famiglia impliciti"
    return True, "conteggi internamente coerenti; controllo demografico non disponibile"


def audit(data: dict[str, Any], snapshot: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
    town_names = {str(t.get("code")): t.get("name") for t in data.get("towns", [])}
    required_codes = set(town_names)
    rows, csv_url, discovery = acquire_primary_rows(required_codes)

    population = population_by_code(data)
    invalid: list[str] = []
    report_rows: list[dict[str, Any]] = []
    snapshot_by_code = {str(t.get("code")): t for t in snapshot.get("towns", [])}

    for code, town_name in town_names.items():
        source = rows.get(code)
        if source is None:
            invalid.append(code)
            report_rows.append({"code": code, "town": town_name, "valid": False, "reason": "Comune assente nel CSV primario", "official": None})
            continue
        valid, reason = plausibility(population.get(code), source["famiglie_residenti"], source["famiglie_ftth"])
        if not valid:
            invalid.append(code)
        target = snapshot_by_code.get(code)
        if target is not None:
            agcom = target.setdefault("agcom", {})
            agcom["primaryOfficialCsv"] = source
            agcom["absoluteCountsValid"] = valid
            agcom["absoluteCountsValidation"] = reason
            if valid:
                agcom["residentHouseholds"] = source["famiglie_residenti"]
                agcom["ftthHouseholds"] = source["famiglie_ftth"]
                agcom["ftthHouseholdsWithin20m"] = source["famiglie_ftth_20m"]
            else:
                agcom["ftthHouseholds"] = None
        report_rows.append({"code": code, "town": town_name, "valid": valid, "reason": reason, "official": source})

    snapshot["agcomAudit"] = {
        "sourceType": "primary_official_csv",
        "publicMapUrl": PUBLIC_MAP_URL,
        "officialCsvUrl": csv_url,
        "discovery": discovery,
        "rowCount": len(rows),
        "invalidAbsoluteTownCodes": sorted(invalid),
        "invalidAbsoluteTowns": [town_names[code] for code in sorted(invalid)],
        "rows": report_rows,
        "rule": (
            "Nessun conteggio assoluto viene ricostruito dalle percentuali. "
            "La distribuzione comunale è scoperta da endpoint ufficiali AGCOM e "
            "accettata solo dopo validazione di schema, copertura nazionale e sette Comuni."
        ),
    }
    return snapshot, csv_url, discovery


def write_report(snapshot: dict[str, Any], path: Path) -> None:
    audit = snapshot["agcomAudit"]
    lines = [
        "# Audit primario AGCOM — conteggi FTTH",
        "",
        f"- Mappa pubblica: {audit['publicMapUrl']}",
        f"- Dataset acquisito: {audit['officialCsvUrl']}",
        f"- Discovery: `{audit['discovery']}`",
        f"- Righe CSV: **{audit['rowCount']}**",
        f"- Comuni non validati: **{', '.join(audit['invalidAbsoluteTowns']) or 'nessuno'}**",
        "",
        "| Comune | Famiglie residenti | Famiglie FTTH | FTTH 20 m | Copertura DESI | Esito | Motivo |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for item in audit["rows"]:
        source = item.get("official") or {}
        lines.append(
            f"| {item['town']} | {source.get('famiglie_residenti', 'n.d.')} | {source.get('famiglie_ftth', 'n.d.')} | "
            f"{source.get('famiglie_ftth_20m', 'n.d.')} | {source.get('copertura_ftth_desi_pct', 'n.d.')}% | "
            f"{'OK' if item['valid'] else 'NON VALIDATO'} | {item['reason']} |"
        )
    lines.extend(["", "> I valori non validati restano `n.d.`. Nessuna stima viene effettuata.", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-data", type=Path, default=base.SITE_DATA)
    parser.add_argument("--snapshot", type=Path, default=base.SNAPSHOT)
    parser.add_argument("--report-md", type=Path, default=base.ROOT / "reports" / "previews" / "imprese-banda-larga" / "agcom-primary-audit.md")
    args = parser.parse_args(argv)
    data = base._json_load(args.site_data)
    snapshot = base._json_load(args.snapshot)
    snapshot, csv_url, discovery = audit(data, snapshot)
    base._json_write(args.snapshot, snapshot)
    write_report(snapshot, args.report_md)
    print(json.dumps({
        "status": "ok",
        "officialCsvUrl": csv_url,
        "publicMapUrl": PUBLIC_MAP_URL,
        "discovery": discovery,
        "invalidTowns": snapshot["agcomAudit"]["invalidAbsoluteTowns"],
        "report": str(args.report_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except base.DataError as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        raise SystemExit(2)
