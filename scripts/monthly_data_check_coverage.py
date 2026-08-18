#!/usr/bin/env python3
"""Estensione del monitor che valida coperture dichiarate 6/7 o 7/7."""
from __future__ import annotations

import copy
import re
import shutil
import subprocess
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import monthly_data_check as base  # noqa: E402

ORIGINAL_VALIDATE = base.validate_dataset
ORIGINAL_CANONICAL_URL = base.canonical_url
ORIGINAL_COMPARE_STATES = base.compare_states
ORIGINAL_PROBE_SOURCE = base.probe_source
COVERAGE_RE = re.compile(r"^(\d+)\s*/\s*(\d+)$")
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0 Safari/537.36 "
    "OsservatorioVersiliaDataMonitor/1.0"
)

# Alcuni portali istituzionali respingono il landing URL ai client automatici
# pur esponendo endpoint ufficiali stabili e pubblici dello stesso servizio.
# Il fallback serve solo al controllo di raggiungibilità: la fonte pubblicata
# nell'indicatore resta invariata e nessun fallback certifica un nuovo periodo.
OFFICIAL_PROBE_FALLBACKS = {
    "https://www.italiadomani.gov.it/content/sogei-ng/it/it/catalogo-open-data.html": (
        "https://www.strutturapnrr.gov.it/it/documenti/catalogo-open-data/"
    ),
    "https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/": (
        "https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/"
        "fiscalitalocale/nuova_addcomirpef/download/tabella.htm"
    ),
    "https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_at/": (
        "https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/"
        "fiscalitalocale/nuova_at/dati/download.htm?anno={year}"
    ),
    "https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_imu/": (
        "https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/"
        "fiscalitalocale/nuova_imu/dati/download.htm?anno={year}"
    ),
}

# Il portale del Dipartimento delle Finanze aggiunge a ogni accesso un parametro
# `t` variabile alla stessa pagina. Non rappresenta un cambio di fonte e non deve
# quindi generare una segnalazione mensile di redirect.
VOLATILE_REDIRECT_QUERY_PARAMS = {
    ("www1.finanze.gov.it", "/finanze/analisi_stat/public/index.php"): {"t"},
}


def canonical_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value.strip())
    ignored = VOLATILE_REDIRECT_QUERY_PARAMS.get(
        (parsed.netloc.lower(), parsed.path or "/"),
        set(),
    )
    if ignored:
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        filtered_query = urllib.parse.urlencode(
            [(key, item) for key, item in query_pairs if key.lower() not in ignored]
        )
        value = urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, filtered_query, parsed.fragment)
        )
    return ORIGINAL_CANONICAL_URL(value)


def compare_states(
    previous: dict[str, Any], current: dict[str, dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Normalizza anche la baseline precedente prima di confrontare i redirect."""
    prepared_previous = copy.deepcopy(previous)
    previous_sources = prepared_previous.get("sources")
    if isinstance(previous_sources, dict):
        for item in previous_sources.values():
            if isinstance(item, dict) and item.get("finalUrl"):
                item["finalUrl"] = canonical_url(str(item["finalUrl"]))

    prepared_current = copy.deepcopy(current)
    for item in prepared_current.values():
        if isinstance(item, dict) and item.get("finalUrl"):
            item["finalUrl"] = canonical_url(str(item["finalUrl"]))

    return ORIGINAL_COMPARE_STATES(prepared_previous, prepared_current)


def _curl_probe(url: str, registry: dict[str, Any]) -> dict[str, Any] | None:
    """Secondo tentativo con curl per fonti che rifiutano urllib/HEAD.

    Alcuni portali pubblici applicano filtri TLS o anti-bot diversi a seconda del
    client. Il fallback usa una GET limitata a un byte e non interpreta mai il
    contenuto come un nuovo rilascio: serve esclusivamente a stabilire se la fonte
    è raggiungibile.
    """
    curl = shutil.which("curl")
    if not curl:
        return None
    timeout = max(1, int(float(registry.get("requestTimeoutSeconds", 20))))
    marker = "__OV_CURL_META__"
    command = [
        curl,
        "--location",
        "--silent",
        "--show-error",
        "--max-time",
        str(timeout),
        "--connect-timeout",
        str(min(timeout, 10)),
        "--user-agent",
        BROWSER_USER_AGENT,
        "--header",
        "Accept: */*",
        "--range",
        "0-0",
        "--output",
        "/dev/null",
        "--write-out",
        f"{marker}%{{http_code}}\n%{{url_effective}}\n%{{content_type}}\n%{{size_download}}",
        url,
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout + 5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    stdout = completed.stdout or ""
    if marker not in stdout:
        return None
    meta = stdout.split(marker, 1)[1].splitlines()
    if len(meta) < 3:
        return None
    try:
        status = int(meta[0].strip() or "0")
    except ValueError:
        status = 0
    final_url = meta[1].strip() or url
    content_type = meta[2].strip().split(";", 1)[0]
    error = (completed.stderr or "").strip()
    ok = 200 <= status < 400
    return {
        "url": url,
        "ok": ok,
        "status": status or None,
        "finalUrl": canonical_url(final_url),
        "contentType": content_type,
        "contentLength": None,
        "etag": "",
        "lastModified": "",
        "contentSha256": "",
        "hashTruncated": False,
        "error": "" if ok else (error or f"HTTP {status}"),
        "probeMethod": "curl-range",
    }


def _attempt_probe(url: str, registry: dict[str, Any]) -> dict[str, Any]:
    result = ORIGINAL_PROBE_SOURCE(url, registry)
    if result.get("ok"):
        return result
    fallback = _curl_probe(url, registry)
    if fallback is not None and fallback.get("ok"):
        return fallback
    return result


def _as_official_fallback(
    source_url: str,
    fallback_url: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Mantiene l'identità della fonte pur registrando l'endpoint di controllo."""
    prepared = dict(result)
    prepared["probeUrl"] = fallback_url
    prepared["probeFinalUrl"] = str(result.get("finalUrl") or fallback_url)
    prepared["url"] = source_url
    # Il cambio del solo endpoint tecnico non deve apparire come redirect della fonte.
    prepared["finalUrl"] = canonical_url(source_url)
    method = str(result.get("probeMethod") or "urllib")
    prepared["probeMethod"] = f"official-fallback:{method}"
    return prepared


def probe_source(url: str, registry: dict[str, Any]) -> dict[str, Any]:
    """Prova la fonte, poi client alternativo e infine un endpoint ufficiale gemello."""
    result = _attempt_probe(url, registry)
    if result.get("ok"):
        return result

    template = OFFICIAL_PROBE_FALLBACKS.get(canonical_url(url))
    if not template:
        return result
    year = datetime.now(timezone.utc).year
    fallback_url = template.format(year=year)
    fallback_result = _attempt_probe(fallback_url, registry)
    if fallback_result.get("ok"):
        return _as_official_fallback(url, fallback_url, fallback_result)
    return result


def _strip_partial_series_nulls(row: dict[str, Any]) -> None:
    """Rimuove solo dalla copia di validazione gli anni dichiaratamente non disponibili.

    Una serie di un indicatore con copertura parziale può legittimamente contenere
    `null` per un Comune/anno non osservato. Il monitor base vieta i null in assoluto,
    quindi qui li escludiamo dalla copia temporanea senza alterare il dataset reale.
    """
    series = row.get("series")
    if not isinstance(series, dict):
        return
    years = series.get("years")
    values = series.get("values")
    if not isinstance(years, list) or not isinstance(values, list) or len(years) != len(values):
        return
    pairs = [(year, value) for year, value in zip(years, values) if value is not None]
    series["years"] = [year for year, _ in pairs]
    series["values"] = [value for _, value in pairs]


def validate_dataset(data: dict[str, Any], registry: dict[str, Any]):
    prepared = copy.deepcopy(data)
    findings = []
    expected_total = len(registry.get("expectedTowns", []))

    metrics = prepared.get("metrics")
    if isinstance(metrics, dict):
        for metric_key, metric in metrics.items():
            if not isinstance(metric, dict):
                continue
            rows = metric.get("rows")
            method = metric.get("method")
            if not isinstance(rows, list) or not isinstance(method, dict):
                continue

            coverage_text = str(method.get("coverage", "")).strip()
            match = COVERAGE_RE.fullmatch(coverage_text)
            if not match:
                continue
            declared_available, declared_total = map(int, match.groups())
            partial_coverage = declared_available < declared_total
            if expected_total and declared_total != expected_total:
                findings.append(
                    base.finding(
                        "error",
                        "coverage_denominator",
                        f"Copertura dichiarata {coverage_text}, ma i Comuni attesi sono {expected_total}.",
                        metric_key,
                    )
                )

            missing_rows = [
                row for row in rows
                if isinstance(row, dict) and row.get("value") is None
            ]
            available = len([
                row for row in rows
                if isinstance(row, dict) and row.get("value") is not None
            ])
            if available != declared_available:
                findings.append(
                    base.finding(
                        "error",
                        "coverage_value_mismatch",
                        f"Copertura dichiarata {coverage_text}, ma i valori disponibili sono {available}/{declared_total}.",
                        metric_key,
                    )
                )

            if partial_coverage:
                for row in rows:
                    if isinstance(row, dict):
                        _strip_partial_series_nulls(row)

            for row in missing_rows:
                # Il frontend formatta i valori null come n.d.; il campo `formatted`
                # non è obbligatorio per una riga dichiaratamente fuori copertura.
                if not partial_coverage and row.get("formatted") != "n.d.":
                    findings.append(
                        base.finding(
                            "error",
                            "missing_value_label",
                            f"Il valore mancante per {row.get('town', row.get('code', '?'))} deve essere mostrato come n.d.",
                            metric_key,
                        )
                    )
                # Lo zero è usato soltanto nella copia temporanea di validazione
                # richiesta dal controllore base e non viene mai scritto nei dati.
                row["value"] = 0

    base_findings, source_map, stats = ORIGINAL_VALIDATE(prepared, registry)
    return findings + base_findings, source_map, stats


def main(argv: list[str] | None = None) -> int:
    base.canonical_url = canonical_url
    base.compare_states = compare_states
    base.validate_dataset = validate_dataset
    base.probe_source = probe_source
    if argv is None:
        return base.main()

    original_argv = sys.argv
    try:
        sys.argv = [original_argv[0], *argv]
        return base.main()
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    raise SystemExit(main())
