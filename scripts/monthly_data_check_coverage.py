#!/usr/bin/env python3
"""Estensione del monitor per coperture parziali ed eccezioni pubbliche dichiarate."""
from __future__ import annotations

import copy
import hashlib
import os
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

# Italia Domani espone pubblicamente il catalogo ReGiS ma risponde 403 ai probe
# automatici anche attraverso il landing ufficiale della Struttura di missione.
# Un 401/403/429 viene quindi registrato come limitazione nota dell'automazione,
# non come indisponibilità della fonte. Errori di rete/TLS/5xx restano invece guasti.
AUTOMATION_LIMITED_SOURCES = {
    "https://www.italiadomani.gov.it/content/sogei-ng/it/it/catalogo-open-data.html": {
        "evidenceUrl": "https://www.strutturapnrr.gov.it/it/documenti/catalogo-open-data/",
        "reason": "Il portale ufficiale limita le richieste automatizzate; il catalogo resta soggetto a verifica manuale.",
    }
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


def _failure_kind(result: dict[str, Any]) -> str:
    if result.get("ok"):
        return "reachable"
    status = result.get("status")
    if status in {401, 403, 429}:
        return "access_denied"  # HTTP alone does not prove an anti-bot block.
    if status in {404, 410}:
        return "path_missing"
    if status and int(status) >= 500:
        return "server_error"
    error = str(result.get("error") or "").lower()
    if "timed out" in error or "timeout" in error:
        return "network_timeout"
    return "transport_error"


def _attempt_record(url: str, method: str, result: dict[str, Any]) -> dict[str, Any]:
    return {"url": url, "method": method, "httpStatus": result.get("status"),
            "finalUrl": result.get("finalUrl") or url, "ok": bool(result.get("ok")),
            "error": str(result.get("error") or ""), "result": _failure_kind(result)}


def _attempt_probe(url: str, registry: dict[str, Any]) -> dict[str, Any]:
    result = ORIGINAL_PROBE_SOURCE(url, registry)
    result.setdefault("probeMethod", "urllib")
    attempts = list(result.get("attempts") or [_attempt_record(url, "urllib", result)])
    # Exactly one alternative transport per endpoint; no retry storms.
    if not result.get("ok"):
        fallback = _curl_probe(url, registry)
        if fallback is not None:
            attempts.append(_attempt_record(url, "curl-range", fallback))
            if fallback.get("ok"):
                result = fallback
    result["attempts"] = attempts
    result["failureKind"] = _failure_kind(result)
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
    prepared["directReachable"] = False
    prepared["probeContentSha256"] = prepared.get("contentSha256", "")
    prepared["contentSha256"] = ""  # Different endpoint; not comparable to the primary route.
    return prepared


def _as_automation_limited(source_url: str, result: dict[str, Any]) -> dict[str, Any]:
    policy = AUTOMATION_LIMITED_SOURCES[canonical_url(source_url)]
    prepared = dict(result)
    # `ok` indica che il monitor ha classificato con successo lo stato operativo;
    # `directReachable` conserva separatamente il fatto che il landing respinge il bot.
    prepared["ok"] = True
    prepared["directReachable"] = False
    prepared["automationLimited"] = True
    prepared["url"] = source_url
    prepared["finalUrl"] = canonical_url(source_url)
    prepared["probeUrl"] = str(policy["evidenceUrl"])
    prepared["probeMethod"] = "automation-limited"
    prepared["error"] = str(policy["reason"])
    return prepared


def _catalogue_check(policy: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    """Read only the relevant release markers, never unrelated page dates."""
    url = str(policy.get("catalogueUrl") or "")
    pattern = str(policy.get("releasePattern") or "")
    if not url or not pattern:
        return {}
    result = {"url": url, "method": "GET-release-catalogue", "httpStatus": None, "ok": False, "error": ""}
    try:
        with base.open_request(url, "GET", float(registry.get("requestTimeoutSeconds", 20))) as response:
            result["httpStatus"] = getattr(response, "status", response.getcode())
            result["finalUrl"] = response.geturl()
            raw = response.read(1_048_577)
        if len(raw) > 1_048_576:
            raise RuntimeError("Catalogo oltre il limite di 1 MiB: verifica non conclusa")
        markers = sorted(set(re.findall(pattern, raw.decode("utf-8", errors="replace"), re.I)))
        if not markers:
            raise RuntimeError("Marcatori del rilascio assenti: possibile schema cambiato o pagina di blocco")
        result["ok"] = True
        result["markers"] = markers
        result["fingerprint"] = hashlib.sha256("\n".join(markers).encode()).hexdigest()
    except Exception as exc:
        if hasattr(exc, "code"):
            result["httpStatus"] = exc.code
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def probe_source(url: str, registry: dict[str, Any]) -> dict[str, Any]:
    """Bounded probes of registered official routes, separate from acquisition."""
    source_key = canonical_url(url)
    policies = registry.get("sourceProbePolicies", {})
    policy = next((v for k, v in policies.items() if canonical_url(k) == source_key), {})
    if policy.get("retired"):
        result = {"url": url, "finalUrl": url, "ok": False, "status": None,
                  "error": policy.get("reason", "Endpoint ritirato"),
                  "failureKind": "obsolete_path", "probeMethod": "retired-route",
                  "attempts": [{"url": url, "method": "not-requested-retired", "httpStatus": None,
                                "ok": False, "error": policy.get("reason", ""), "result": "obsolete_path"}]}
    else:
        probe_registry = registry
        if os.environ.get("MONITOR_CHECK_DEPTH") == "deep" and policy.get("deepRequestTimeoutSeconds"):
            probe_registry = dict(registry)
            probe_registry["requestTimeoutSeconds"] = min(120, max(20, float(policy["deepRequestTimeoutSeconds"])))
        result = _attempt_probe(url, probe_registry)
        result["requestTimeoutSeconds"] = probe_registry.get("requestTimeoutSeconds", 20)
    direct_ok = bool(result.get("ok"))
    attempts = list(result.get("attempts", []))
    routes = policy.get("alternatives", [])
    template = OFFICIAL_PROBE_FALLBACKS.get(source_key)
    if template:
        routes = [*routes, {"url": template.format(year=datetime.now(timezone.utc).year), "role": "information"}]
    if not result.get("ok"):
        for route in routes[:2]:
            fallback_url = str(route["url"])
            fallback_result = _attempt_probe(fallback_url, registry)
            attempts.extend(fallback_result.get("attempts", []))
            if fallback_result.get("ok"):
                result = _as_official_fallback(url, fallback_url, fallback_result)
                result["endpointRole"] = route.get("role", "information")
                break
    limited = AUTOMATION_LIMITED_SOURCES.get(source_key)
    if limited and result.get("status") in {401, 403, 429}:
        result = _as_automation_limited(url, result)
    result["attempts"] = attempts
    result["directReachable"] = direct_ok
    result.setdefault("endpointRole", policy.get("role", "unspecified"))
    result["failureKind"] = "obsolete_path" if policy.get("retired") else _failure_kind(result)
    if policy:
        result["acquisition"] = policy.get("acquisition", {})
        result["releaseCheck"] = policy.get("releaseCheck", "")
        result["releaseVerification"] = "not_performed"
        result["acquisitionVerified"] = False
        if policy.get("retired"):
            result["retiredSource"] = True
            result["error"] = str(policy.get("reason", ""))
    if policy and os.environ.get("MONITOR_CHECK_DEPTH") == "deep":
        catalogue = _catalogue_check(policy, registry)
        if catalogue:
            result["releaseCatalogue"] = catalogue
            result["attempts"].append({k: v for k, v in catalogue.items() if k not in {"markers", "fingerprint"}})
            result["releaseVerification"] = "catalogue_only" if catalogue.get("ok") else "not_performed"
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

            meta = metric.get("meta")
            allows_partial_history = (
                isinstance(meta, dict) and meta.get("allowPartialHistory") is True
            )
            coverage_text = str(method.get("coverage", "")).strip()
            match = COVERAGE_RE.fullmatch(coverage_text)
            if not match and not allows_partial_history:
                continue

            partial_coverage = allows_partial_history
            declared_available = None
            declared_total = None
            if match:
                declared_available, declared_total = map(int, match.groups())
                partial_coverage = partial_coverage or declared_available < declared_total
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
            if (
                declared_available is not None
                and declared_total is not None
                and available != declared_available
            ):
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
                # I dataset che dichiarano esplicitamente storia/coprertura parziale
                # possono avere n.d. ufficiali. La copia di validazione li neutralizza
                # senza alterare lo snapshot monitorato né inventare valori pubblici.
                if not partial_coverage and row.get("formatted") != "n.d.":
                    findings.append(
                        base.finding(
                            "error",
                            "missing_value_label",
                            f"Il valore mancante per {row.get('town', row.get('code', '?'))} deve essere mostrato come n.d.",
                            metric_key,
                        )
                    )
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
