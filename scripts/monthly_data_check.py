#!/usr/bin/env python3
"""Controllo mensile prudenziale dei dati e delle fonti dell'Osservatorio.

La procedura non modifica mai i valori pubblicati. Valida il dataset, controlla
le URL ufficiali, confronta gli esiti con una baseline approvata e produce un
rapporto leggibile e uno JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

USER_AGENT = (
    "OsservatorioVersiliaDataMonitor/1.0 "
    "(https://github.com/EmAnzi3/osservatorio-versilia)"
)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"File non trovato: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"JSON non valido in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Il contenuto di {path} deve essere un oggetto JSON")
    return value


def canonical_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value.strip())
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = urllib.parse.urlencode(
        sorted(
            (key, item)
            for key, item in query_pairs
            if key.lower() not in {"v", "cache", "cachebust", "timestamp", "_"}
        )
    )
    return urllib.parse.urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", query, "")
    )


def finding(level: str, code: str, message: str, metric: str | None = None) -> dict[str, Any]:
    return {"level": level, "code": code, "message": message, "metric": metric}


def iter_metric_sources(metric: dict[str, Any]) -> Iterable[tuple[str, str]]:
    source_url = metric.get("sourceUrl")
    if isinstance(source_url, str) and source_url.strip():
        yield "primary", source_url.strip()
    benchmark = metric.get("meta", {}).get("benchmark")
    if isinstance(benchmark, dict):
        benchmark_url = benchmark.get("url")
        if isinstance(benchmark_url, str) and benchmark_url.strip():
            yield "benchmark", benchmark_url.strip()


def validate_dataset(
    data: dict[str, Any], registry: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, int]]:
    findings: list[dict[str, Any]] = []
    metrics = data.get("metrics")
    towns = data.get("towns")

    if not isinstance(metrics, dict):
        findings.append(finding("error", "metrics_missing", "La sezione metrics non è un oggetto."))
        metrics = {}
    if not isinstance(towns, list):
        findings.append(finding("error", "towns_missing", "La sezione towns non è un elenco."))
        towns = []

    expected_count = int(registry.get("expectedMetricCount", 0) or 0)
    if expected_count and len(metrics) != expected_count:
        findings.append(
            finding(
                "error",
                "metric_count",
                f"Attesi {expected_count} indicatori, trovati {len(metrics)}.",
            )
        )

    expected_towns = {
        str(item["code"]): str(item["name"])
        for item in registry.get("expectedTowns", [])
        if isinstance(item, dict) and item.get("code") and item.get("name")
    }
    actual_towns = {
        str(item.get("code")): str(item.get("name"))
        for item in towns
        if isinstance(item, dict) and item.get("code") and item.get("name")
    }
    if expected_towns and actual_towns != expected_towns:
        findings.append(
            finding(
                "error",
                "town_registry",
                "L'elenco dei sette Comuni o i codici Istat non coincide con il registro.",
            )
        )

    source_map: dict[str, dict[str, Any]] = {}
    metrics_with_series = 0
    rows_total = 0

    for metric_key, metric in metrics.items():
        if not isinstance(metric, dict):
            findings.append(finding("error", "metric_shape", "Indicatore non valido.", metric_key))
            continue

        meta = metric.get("meta")
        rows = metric.get("rows")
        method = metric.get("method")

        if not isinstance(meta, dict):
            findings.append(finding("error", "meta_missing", "Metadati assenti.", metric_key))
            meta = {}
        if str(meta.get("key", "")) != metric_key:
            findings.append(
                finding("error", "meta_key", "meta.key non coincide con la chiave.", metric_key)
            )
        for field in ("theme", "label", "unit", "year", "source"):
            if meta.get(field) in (None, ""):
                findings.append(
                    finding(
                        "error",
                        "meta_field",
                        f"Metadato obbligatorio mancante: {field}.",
                        metric_key,
                    )
                )

        if not isinstance(method, dict):
            findings.append(finding("error", "method_missing", "Metodo assente.", metric_key))
        else:
            for field in ("type", "formula", "coverage"):
                if method.get(field) in (None, ""):
                    findings.append(
                        finding(
                            "error",
                            "method_field",
                            f"Campo metodologico mancante: {field}.",
                            metric_key,
                        )
                    )

        if not isinstance(rows, list):
            findings.append(finding("error", "rows_missing", "Righe comunali assenti.", metric_key))
            rows = []

        row_codes = [str(row.get("code")) for row in rows if isinstance(row, dict)]
        if expected_towns and set(row_codes) != set(expected_towns):
            findings.append(
                finding(
                    "error",
                    "coverage",
                    f"Copertura comunale non completa: {len(set(row_codes))}/{len(expected_towns)}.",
                    metric_key,
                )
            )
        if len(row_codes) != len(set(row_codes)):
            findings.append(finding("error", "duplicate_town", "Codici comunali duplicati.", metric_key))

        has_series = False
        for row in rows:
            if not isinstance(row, dict):
                findings.append(finding("error", "row_shape", "Riga comunale non valida.", metric_key))
                continue
            rows_total += 1
            if row.get("value") is None:
                findings.append(
                    finding(
                        "error",
                        "value_missing",
                        f"Valore corrente assente per {row.get('town', row.get('code', '?'))}.",
                        metric_key,
                    )
                )
            series = row.get("series")
            if series is None:
                continue
            has_series = True
            if not isinstance(series, dict):
                findings.append(finding("error", "series_shape", "Serie non valida.", metric_key))
                continue
            years = series.get("years")
            values = series.get("values")
            if not isinstance(years, list) or not isinstance(values, list):
                findings.append(
                    finding("error", "series_arrays", "years e values devono essere elenchi.", metric_key)
                )
                continue
            if len(years) != len(values):
                findings.append(
                    finding(
                        "error",
                        "series_length",
                        f"Serie con {len(years)} anni e {len(values)} valori.",
                        metric_key,
                    )
                )
            if years != sorted(years) or len(years) != len(set(years)):
                findings.append(
                    finding("error", "series_years", "Annualità non ordinate o duplicate.", metric_key)
                )
            if any(value is None for value in values):
                findings.append(
                    finding("error", "series_null", "La serie contiene valori nulli.", metric_key)
                )

        if has_series:
            metrics_with_series += 1

        source_count = 0
        for role, raw_url in iter_metric_sources(metric):
            source_count += 1
            try:
                url = canonical_url(raw_url)
            except Exception:
                findings.append(
                    finding("error", "source_url", f"URL fonte non interpretabile: {raw_url}", metric_key)
                )
                continue
            parsed = urllib.parse.urlsplit(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                findings.append(
                    finding("error", "source_url", f"URL fonte non HTTP(S): {raw_url}", metric_key)
                )
                continue
            source = source_map.setdefault(url, {"url": url, "metrics": [], "roles": []})
            if metric_key not in source["metrics"]:
                source["metrics"].append(metric_key)
            if role not in source["roles"]:
                source["roles"].append(role)
        if not source_count:
            findings.append(finding("error", "source_missing", "URL della fonte assente.", metric_key))

    return findings, source_map, {
        "metricCount": len(metrics),
        "townCount": len(towns),
        "rowCount": rows_total,
        "metricsWithSeries": metrics_with_series,
        "uniqueSourceCount": len(source_map),
    }


def should_hash(url: str, content_type: str, registry: dict[str, Any]) -> bool:
    extension = Path(urllib.parse.urlsplit(url).path.lower()).suffix
    extensions = {str(item).lower() for item in registry.get("contentExtensions", [])}
    if extension in extensions:
        return True
    content_type = content_type.lower()
    return any(
        token in content_type
        for token in (
            "text/csv",
            "application/json",
            "application/zip",
            "application/pdf",
            "spreadsheet",
            "excel",
        )
    )


def open_request(url: str, method: str, timeout: float, headers: dict[str, str] | None = None):
    request_headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, method=method, headers=request_headers)
    return urllib.request.urlopen(request, timeout=timeout)


def probe_source(url: str, registry: dict[str, Any]) -> dict[str, Any]:
    timeout = float(registry.get("requestTimeoutSeconds", 20))
    max_bytes = int(registry.get("maxDownloadBytes", 4_194_304))
    result: dict[str, Any] = {
        "url": url,
        "ok": False,
        "status": None,
        "finalUrl": url,
        "contentType": "",
        "contentLength": None,
        "etag": "",
        "lastModified": "",
        "contentSha256": "",
        "hashTruncated": False,
        "error": "",
    }

    response = None
    try:
        response = open_request(url, "HEAD", timeout)
    except urllib.error.HTTPError as exc:
        if exc.code not in {403, 405, 501}:
            result["status"] = exc.code
            result["error"] = f"HTTP {exc.code}"
            return result
    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        result["error"] = str(exc)
        return result

    if response is None:
        try:
            response = open_request(url, "GET", timeout, {"Range": "bytes=0-0"})
        except urllib.error.HTTPError as exc:
            result["status"] = exc.code
            result["error"] = f"HTTP {exc.code}"
            return result
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            result["error"] = str(exc)
            return result

    try:
        result["status"] = getattr(response, "status", response.getcode())
        result["finalUrl"] = canonical_url(response.geturl())
        result["contentType"] = response.headers.get("Content-Type", "").split(";", 1)[0].strip()
        result["contentLength"] = response.headers.get("Content-Length")
        result["etag"] = response.headers.get("ETag", "").strip()
        result["lastModified"] = response.headers.get("Last-Modified", "").strip()
        result["ok"] = 200 <= int(result["status"]) < 400
    finally:
        response.close()

    if result["ok"] and should_hash(result["finalUrl"], result["contentType"], registry):
        try:
            with open_request(url, "GET", timeout) as content_response:
                digest = hashlib.sha256()
                total = 0
                while total <= max_bytes:
                    chunk = content_response.read(min(65_536, max_bytes + 1 - total))
                    if not chunk:
                        break
                    digest.update(chunk)
                    total += len(chunk)
                result["contentSha256"] = digest.hexdigest()
                result["hashTruncated"] = total > max_bytes
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            result["error"] = f"Metadati raggiungibili, hash non disponibile: {exc}"
    return result


def offline_source(url: str) -> dict[str, Any]:
    return {
        "url": url,
        "ok": True,
        "status": 200,
        "finalUrl": url,
        "contentType": "offline/validation",
        "contentLength": None,
        "etag": "",
        "lastModified": "",
        "contentSha256": "",
        "hashTruncated": False,
        "error": "",
    }


def compare_states(previous: dict[str, Any], current: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    previous_sources = previous.get("sources")
    if not isinstance(previous_sources, dict):
        previous_sources = {}
    changes: dict[str, list[dict[str, Any]]] = {
        "added": [],
        "removed": [],
        "content": [],
        "redirect": [],
        "metadata": [],
        "unreachable": [],
        "recovered": [],
    }
    for url in sorted(set(current) - set(previous_sources)):
        changes["added"].append({"url": url})
    for url in sorted(set(previous_sources) - set(current)):
        changes["removed"].append({"url": url})

    for url, item in sorted(current.items()):
        old = previous_sources.get(url)
        if not isinstance(old, dict):
            if not item.get("ok"):
                changes["unreachable"].append({"url": url, "error": item.get("error", "")})
            continue
        if old.get("ok") and not item.get("ok"):
            changes["unreachable"].append({"url": url, "error": item.get("error", "")})
        if not old.get("ok") and item.get("ok"):
            changes["recovered"].append({"url": url})
        if old.get("contentSha256") and item.get("contentSha256") and old["contentSha256"] != item["contentSha256"]:
            changes["content"].append({"url": url})
        if old.get("finalUrl") and item.get("finalUrl") and old["finalUrl"] != item["finalUrl"]:
            changes["redirect"].append(
                {"url": url, "before": old.get("finalUrl"), "after": item.get("finalUrl")}
            )
        old_meta = (str(old.get("etag") or ""), str(old.get("lastModified") or ""))
        new_meta = (str(item.get("etag") or ""), str(item.get("lastModified") or ""))
        if old_meta != new_meta and any(old_meta) and any(new_meta):
            changes["metadata"].append({"url": url})
    return changes


def url_list(items: list[dict[str, Any]]) -> str:
    if not items:
        return "Nessuno"
    return "\n".join(f"- `{item.get('url', '')}`" for item in items[:30])


def build_report(
    checked_at: str,
    mode: str,
    summary: dict[str, int],
    findings: list[dict[str, Any]],
    probes: dict[str, dict[str, Any]],
    changes: dict[str, list[dict[str, Any]]],
    status: str,
) -> str:
    errors = [item for item in findings if item["level"] == "error"]
    warnings = [item for item in findings if item["level"] == "warning"]
    unavailable = [item for item in probes.values() if not item.get("ok")]
    change_count = sum(len(changes[key]) for key in ("added", "removed", "content", "redirect"))
    lines = [
        "@EmAnzi3",
        "",
        f"## Controllo dati — {checked_at[:10]}",
        "",
        f"**Esito:** `{status}`  ",
        f"**Modalità:** `{mode}`",
        "",
        "| Controllo | Esito |",
        "|---|---:|",
        f"| Indicatori verificati | {summary['metricCount']} |",
        f"| Comuni verificati | {summary['townCount']} |",
        f"| Righe comunali | {summary['rowCount']} |",
        f"| Indicatori con serie storica | {summary['metricsWithSeries']} |",
        f"| Fonti uniche verificate | {summary['uniqueSourceCount']} |",
        f"| Fonti non raggiungibili | {len(unavailable)} |",
        f"| Errori strutturali | {len(errors)} |",
        f"| Avvisi strutturali | {len(warnings)} |",
        f"| Segnali di modifica sostanziale | {change_count} |",
        f"| Variazioni dei soli metadati HTTP | {len(changes['metadata'])} |",
        "",
    ]
    if errors:
        lines.extend(["### Errori bloccanti", ""])
        for item in errors[:50]:
            prefix = f"`{item['metric']}` — " if item.get("metric") else ""
            lines.append(f"- **{item['code']}**: {prefix}{item['message']}")
        lines.append("")
    if unavailable:
        lines.extend(["### Fonti non raggiungibili", ""])
        for item in unavailable[:50]:
            detail = item.get("error") or f"HTTP {item.get('status')}"
            lines.append(f"- `{item['url']}` — {detail}")
        lines.append("")
    if change_count:
        lines.extend(
            [
                "### Modifiche da verificare",
                "",
                "**Nuove fonti**",
                url_list(changes["added"]),
                "",
                "**Fonti rimosse**",
                url_list(changes["removed"]),
                "",
                "**Contenuto di file ufficiali modificato**",
                url_list(changes["content"]),
                "",
                "**Reindirizzamenti modificati**",
                url_list(changes["redirect"]),
                "",
            ]
        )
    if changes["metadata"]:
        lines.extend(
            [
                "### Segnali informativi",
                "",
                "Sono cambiati ETag o Last-Modified di alcune pagine. Il segnale non modifica automaticamente alcun dato.",
                "",
                url_list(changes["metadata"]),
                "",
            ]
        )
    lines.extend(
        [
            "### Regola di pubblicazione",
            "",
            "Il controllo non modifica i valori pubblicati e non effettua stime. Una modifica alle fonti genera al massimo una PR in bozza, da verificare prima del merge.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(values: dict[str, Any]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/site-data.json"))
    parser.add_argument("--registry", type=Path, default=Path("data/source-registry.json"))
    parser.add_argument("--state", type=Path, default=Path("data/source-monitor-state.json"))
    parser.add_argument("--report-md", type=Path, required=True)
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--next-state", type=Path, required=True)
    parser.add_argument("--mode", choices=("live", "offline"), default="live")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = load_json(args.data)
    registry = load_json(args.registry)
    previous = load_json(args.state)
    checked_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    findings, source_map, summary = validate_dataset(data, registry)
    probes: dict[str, dict[str, Any]] = {}
    for url, source in sorted(source_map.items()):
        probe = offline_source(url) if args.mode == "offline" else probe_source(url, registry)
        probe["metrics"] = sorted(source["metrics"])
        probe["roles"] = sorted(source["roles"])
        probes[url] = probe

    changes = compare_states(previous, probes)
    errors = [item for item in findings if item["level"] == "error"]
    substantial = any(changes[key] for key in ("added", "removed", "content", "redirect"))
    previous_sources = previous.get("sources")
    baseline_required = not isinstance(previous_sources, dict) or not previous_sources

    if errors:
        status = "attention_required"
    elif baseline_required:
        status = "baseline_required"
    elif substantial:
        status = "changes_detected"
    else:
        status = "no_changes"

    next_state = {
        "schemaVersion": 1,
        "checkedAt": checked_at,
        "mode": args.mode,
        "sources": probes,
    }
    report_payload = {
        "schemaVersion": 1,
        "checkedAt": checked_at,
        "mode": args.mode,
        "status": status,
        "summary": summary,
        "findings": findings,
        "changes": changes,
        "sources": probes,
    }
    report_md = build_report(checked_at, args.mode, summary, findings, probes, changes, status)

    for path in (args.report_md, args.report_json, args.next_state):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.report_md.write_text(report_md + "\n", encoding="utf-8")
    args.report_json.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.next_state.write_text(
        json.dumps(next_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    unavailable_count = sum(1 for item in probes.values() if not item.get("ok"))
    change_count = sum(len(changes[key]) for key in ("added", "removed", "content", "redirect"))
    write_outputs(
        {
            "status": status,
            "metric_count": summary["metricCount"],
            "source_count": summary["uniqueSourceCount"],
            "unavailable_count": unavailable_count,
            "error_count": len(errors),
            "change_count": change_count,
            "report_md": args.report_md,
            "report_json": args.report_json,
            "next_state": args.next_state,
        }
    )
    print(
        json.dumps(
            {
                "status": status,
                "metrics": summary["metricCount"],
                "sources": summary["uniqueSourceCount"],
                "errors": len(errors),
                "unavailable": unavailable_count,
                "changes": change_count,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
