#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"marker non trovato in {path}: {old[:100]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    replace_once(
        "scripts/monthly_data_check.py",
        "import urllib.request\nfrom datetime import datetime, timezone\n",
        "import urllib.request\nfrom datetime import datetime, timezone\n\nimport monitor_semantic_checks as semantics\n",
    )
    replace_once(
        "scripts/monthly_data_check.py",
        '        "contentSha256": "",\n        "hashTruncated": False,\n        "error": "",\n',
        '        "contentSha256": "",\n        "contentHashMode": "raw",\n        "contentChangePolicy": "",\n        "contentChangeReason": "",\n        "hashTruncated": False,\n        "error": "",\n',
    )
    replace_once(
        "scripts/monthly_data_check.py",
        '''    if result["ok"] and should_hash(result["finalUrl"], result["contentType"], registry):
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
''',
        '''    if result["ok"] and should_hash(result["finalUrl"], result["contentType"], registry):
        try:
            with open_request(url, "GET", timeout) as content_response:
                payload = bytearray()
                total = 0
                while total <= max_bytes:
                    chunk = content_response.read(min(65_536, max_bytes + 1 - total))
                    if not chunk:
                        break
                    payload.extend(chunk)
                    total += len(chunk)
                result["hashTruncated"] = total > max_bytes
                if result["hashTruncated"]:
                    result["contentSha256"] = hashlib.sha256(bytes(payload)).hexdigest()
                    result["contentHashMode"] = "raw"
                else:
                    digest, mode = semantics.semantic_content_hash(bytes(payload))
                    result["contentSha256"] = digest
                    result["contentHashMode"] = mode
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            result["error"] = f"Metadati raggiungibili, hash non disponibile: {exc}"
''',
    )
    replace_once(
        "scripts/monthly_data_check.py",
        '        "contentSha256": "",\n        "hashTruncated": False,\n        "error": "",\n    }\n\n\ndef compare_states',
        '        "contentSha256": "",\n        "contentHashMode": "raw",\n        "contentChangePolicy": "",\n        "contentChangeReason": "",\n        "hashTruncated": False,\n        "error": "",\n    }\n\n\ndef compare_states',
    )
    replace_once(
        "scripts/monthly_data_check.py",
        '        "content": [],\n        "redirect": [],\n',
        '        "content": [],\n        "informationalContent": [],\n        "redirect": [],\n',
    )
    replace_once(
        "scripts/monthly_data_check.py",
        '''        if old.get("contentSha256") and item.get("contentSha256") and old["contentSha256"] != item["contentSha256"]:
            changes["content"].append({"url": url})
''',
        '''        old_mode = str(old.get("contentHashMode") or "raw")
        new_mode = str(item.get("contentHashMode") or "raw")
        if (
            old.get("contentSha256")
            and item.get("contentSha256")
            and old_mode == new_mode
            and old["contentSha256"] != item["contentSha256"]
        ):
            content_item = {"url": url}
            reason = str(item.get("contentChangeReason") or "")
            if reason:
                content_item["reason"] = reason
            if str(item.get("contentChangePolicy") or "") == "informational":
                changes["informationalContent"].append(content_item)
            else:
                changes["content"].append(content_item)
''',
    )
    replace_once(
        "scripts/monthly_data_check.py",
        '''    if changes["metadata"]:
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
''',
        '''    if changes["metadata"] or changes.get("informationalContent"):
        lines.extend(["### Segnali informativi", ""])
        if changes.get("informationalContent"):
            lines.extend(
                [
                    "Il contenuto di alcune fonti operative continue è cambiato, ma la politica della fonte classifica il cambio come informativo: gli indicatori pubblicati usano una fotografia datata e versionata.",
                    "",
                    url_list(changes["informationalContent"]),
                    "",
                ]
            )
        if changes["metadata"]:
            lines.extend(
                [
                    "Sono cambiati ETag o Last-Modified di alcune pagine. Il segnale non modifica automaticamente alcun dato.",
                    "",
                    url_list(changes["metadata"]),
                    "",
                ]
            )
''',
    )
    replace_once(
        "scripts/monthly_data_check.py",
        '''        probe["frequencies"] = sorted(source.get("frequencies", []))
        probes[url] = probe
''',
        '''        probe["frequencies"] = sorted(source.get("frequencies", []))
        source_policy = semantics.source_change_policy(url, registry)
        if source_policy:
            probe["contentChangePolicy"] = source_policy.get("contentChange", "")
            probe["contentChangeReason"] = source_policy.get("reason", "")
        probes[url] = probe
''',
    )

    replace_once(
        "scripts/monthly_data_check_status.py",
        'import monthly_data_check_coverage as coverage  # noqa: E402\nimport pnrr_toscana_audit  # noqa: E402\n',
        'import monthly_data_check_coverage as coverage  # noqa: E402\nimport monitor_semantic_checks as semantics  # noqa: E402\nimport pnrr_toscana_audit  # noqa: E402\nimport update_fuel_prices_mimit as fuel_mimit  # noqa: E402\n',
    )
    replace_once(
        "scripts/monthly_data_check_status.py",
        'PNRR_METRICS = ("pnrrFunding", "pnrrConcluded")\n',
        'PNRR_METRICS = ("pnrrFunding", "pnrrConcluded")\nFUEL_METRIC = "fuelPrices"\n',
    )
    anchor = 'def verification_evidence(audit_result: dict[str, Any], metric_key: str) -> dict[str, Any]:\n'
    fuel_code = '''def apply_fuel_verification_result(
    metric: dict[str, Any],
    item: dict[str, Any],
    live: dict[str, Any],
    checked_at: str,
) -> dict[str, Any]:
    published = str(item.get("publishedPeriod") or "")
    observed = str(live.get("referenceDate") or "")
    values_match = semantics.fuel_metric_matches(metric, live)
    evidence = {
        "provider": "Ministero delle Imprese e del Made in Italy",
        "url": str(live.get("sourceUrls", {}).get("prezzi") or fuel_mimit.audit.PRICES),
        "referenceDate": observed,
        "coverage": str(live.get("coverage") or ""),
        "valuesMatchPublished": values_match,
        "towns": live.get("towns", {}),
    }
    item["checkedAt"] = checked_at or str(item.get("checkedAt") or "")
    item["observedLatestPeriod"] = observed
    item["verificationEvidence"] = evidence
    if observed and published and observed > published:
        item["status"] = "release_detected"
        evidence["verdict"] = "new_period"
        item["releaseEvidence"] = evidence
    elif observed == published and values_match:
        item["status"] = "current"
        evidence["verdict"] = "match"
        item.pop("releaseEvidence", None)
    elif observed == published:
        item["status"] = "verification_required"
        evidence["verdict"] = "same_period_values_differ"
        item["releaseEvidence"] = evidence
    else:
        item["status"] = "verification_required"
        evidence["verdict"] = "period_not_comparable"
        item["releaseEvidence"] = evidence
    return evidence


def run_fuel_verification(
    data: dict[str, Any],
    metrics: dict[str, dict[str, Any]],
    report: dict[str, Any],
    checked_at: str,
) -> tuple[dict[str, Any] | None, str]:
    metric = data.get("metrics", {}).get(FUEL_METRIC)
    item = metrics.get(FUEL_METRIC)
    if not isinstance(metric, dict) or not isinstance(item, dict):
        return None, ""
    source_key = canonical_url(str(metric.get("sourceUrl") or ""))
    needs_semantic_check = source_key in changed_urls(report) or str(item.get("status") or "") in {
        "verification_required",
        "release_detected",
    }
    if not needs_semantic_check:
        return None, ""
    try:
        live = fuel_mimit.collect()
    except Exception as exc:
        item["status"] = "verification_required"
        return None, f"{type(exc).__name__}: {exc}"
    return apply_fuel_verification_result(metric, item, live, checked_at), ""


def append_fuel_report_section(
    report_md: Path,
    result: dict[str, Any] | None,
    error: str = "",
) -> None:
    if result is None and not error:
        return
    lines = ["", "### Verifica carburanti MIMIT", ""]
    if result is not None:
        lines.extend(
            [
                f"- Fotografia: `{result.get('referenceDate') or 'n.d.'}`",
                f"- Copertura: `{result.get('coverage') or 'n.d.'}`",
                f"- Esito semantico: `{result.get('verdict') or 'n.d.'}`",
                f"- Valori pubblicati coincidenti: `{'sì' if result.get('valuesMatchPublished') else 'no'}`",
                "- Il cambio quotidiano del CSV non viene più interpretato da solo come anomalia: il periodo e i valori vengono verificati semanticamente.",
            ]
        )
    else:
        lines.append(f"Controllo semantico non completato: `{error}`. Nessun valore viene modificato automaticamente.")
    with report_md.open("a", encoding="utf-8") as handle:
        handle.write("\\n".join(lines) + "\\n")


'''
    replace_once("scripts/monthly_data_check_status.py", anchor, fuel_code + anchor)
    replace_once(
        "scripts/monthly_data_check_status.py",
        '''    pnrr_result = None
    pnrr_error = ""
    if args.mode == "live":
        pnrr_result, pnrr_error = run_pnrr_verification(
''',
        '''    fuel_result = None
    fuel_error = ""
    pnrr_result = None
    pnrr_error = ""
    if args.mode == "live":
        fuel_result, fuel_error = run_fuel_verification(
            data,
            metrics,
            report,
            str(next_state.get("checkedAt") or ""),
        )
        if fuel_result is not None:
            report["fuelMimitVerification"] = fuel_result
        elif fuel_error:
            report["fuelMimitVerificationError"] = fuel_error
        pnrr_result, pnrr_error = run_pnrr_verification(
''',
    )
    replace_once(
        "scripts/monthly_data_check_status.py",
        '    append_report_section(args.report_md, next_state, pnrr_result, pnrr_error)\n    return 0\n',
        '    append_report_section(args.report_md, next_state, pnrr_result, pnrr_error)\n    append_fuel_report_section(args.report_md, fuel_result, fuel_error)\n    return 0\n',
    )

    registry_path = Path("data/source-registry.json")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["sourceChangePolicies"] = {
        "https://regionetoscana.smartregion.toscana.it/mobility/artifacts/gtfs": {
            "contentChange": "informational",
            "reason": "Feed GTFS operativo continuo; gli indicatori TPL usano una fotografia di servizio datata e versionata.",
        },
        "https://dati.toscana.it/dataset/8bb8f8fe-fe7d-41d0-90dc-49f2456180d1/resource/4f85393b-357d-443d-8378-65de4198505f/download/trenitalia.gtfs": {
            "contentChange": "informational",
            "reason": "Feed GTFS ferroviario operativo continuo; gli indicatori TPL usano una fotografia di servizio datata e versionata.",
        },
    }
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    replace_once(
        "scripts/test_monthly_data_check.py",
        'import json\nimport subprocess\n',
        'import io\nimport json\nimport subprocess\nimport zipfile\n',
    )
    replace_once(
        "scripts/test_monthly_data_check.py",
        'import monthly_data_check as checker\n',
        'import monthly_data_check as checker\nimport monitor_semantic_checks as semantics\n',
    )
    test_anchor = '    # L\'ingresso di una URL nella nuova baseline del monitor non è un\'anomalia\n'
    tests = '''    # Due ZIP con gli stessi membri ma timestamp differenti devono produrre lo
    # stesso hash semantico: ARS rigenera il contenitore senza cambiare il CSV.
    def zip_payload(year: int) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            info = zipfile.ZipInfo("data.csv", date_time=(year, 1, 1, 0, 0, 0))
            archive.writestr(info, "anno,valore\\n2022,1.0\\n")
        return buffer.getvalue()

    zip_hash_a, zip_mode_a = semantics.semantic_content_hash(zip_payload(2025))
    zip_hash_b, zip_mode_b = semantics.semantic_content_hash(zip_payload(2026))
    assert zip_mode_a == zip_mode_b == "zip-members"
    assert zip_hash_a == zip_hash_b

    volatile_url = "https://example.org/live.gtfs"
    volatile_changes = checker.compare_states(
        {"sources": {volatile_url: {"ok": True, "finalUrl": volatile_url, "contentSha256": "old", "contentHashMode": "raw"}}},
        {volatile_url: {"ok": True, "finalUrl": volatile_url, "contentSha256": "new", "contentHashMode": "raw", "contentChangePolicy": "informational", "contentChangeReason": "feed continuo"}},
    )
    assert not volatile_changes["content"]
    assert volatile_changes["informationalContent"] == [{"url": volatile_url, "reason": "feed continuo"}]

    zip_migration = checker.compare_states(
        {"sources": {volatile_url: {"ok": True, "finalUrl": volatile_url, "contentSha256": "legacy"}}},
        {volatile_url: {"ok": True, "finalUrl": volatile_url, "contentSha256": zip_hash_a, "contentHashMode": "zip-members"}},
    )
    assert not zip_migration["content"]

    fuel_metric = {
        "rows": [
            {"town": "A", "stationCount": 1, "parts": [{"label": "Benzina self", "value": 1.8}, {"label": "Gasolio self", "value": 1.7}]},
            {"town": "B", "stationCount": 0, "parts": [{"label": "Benzina self", "value": None}, {"label": "Gasolio self", "value": None}]},
        ]
    }
    fuel_live = {"referenceDate": "2026-08-28", "coverage": "1/2", "sourceUrls": {"prezzi": "https://example.org/fuel.csv"}, "towns": {"A": {"benzina": 1.8, "gasolio": 1.7, "stations": 1}, "B": {"benzina": None, "gasolio": None, "stations": 0}}}
    assert semantics.fuel_metric_matches(fuel_metric, fuel_live)
    fuel_state = {"publishedPeriod": "2026-08-28", "status": "verification_required"}
    evidence = status_model.apply_fuel_verification_result(fuel_metric, fuel_state, fuel_live, "2026-08-29T00:00:00+00:00")
    assert fuel_state["status"] == "current"
    assert evidence["verdict"] == "match"
    newer_state = {"publishedPeriod": "2026-08-27", "status": "current"}
    evidence = status_model.apply_fuel_verification_result(fuel_metric, newer_state, fuel_live, "2026-08-29T00:00:00+00:00")
    assert newer_state["status"] == "release_detected"
    assert evidence["verdict"] == "new_period"

'''
    replace_once("scripts/test_monthly_data_check.py", test_anchor, tests + test_anchor)


if __name__ == "__main__":
    main()
