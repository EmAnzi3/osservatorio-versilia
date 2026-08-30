#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, value: str) -> None:
    (ROOT / path).write_text(value, encoding="utf-8")


def replace_once(value: str, old: str, new: str, label: str) -> str:
    count = value.count(old)
    if count != 1:
        raise SystemExit(f"{label}: attesa 1 occorrenza, trovate {count}")
    return value.replace(old, new, 1)


# 1) Canonicalizzazione delle chiavi della baseline e redirect informativi.
path = "scripts/monthly_data_check.py"
value = text(path)
old = '        "contentChangeReason": "",\n        "hashTruncated": False,'
new = '        "contentChangeReason": "",\n        "redirectChangePolicy": "",\n        "redirectChangeReason": "",\n        "hashTruncated": False,'
count = value.count(old)
if count != 2:
    raise SystemExit(f"campi probe/offline redirect: attese 2 occorrenze, trovate {count}")
value = value.replace(old, new)
value = replace_once(
    value,
    '        if source_policy:\n            probe["contentChangePolicy"] = source_policy.get("contentChange", "")\n            probe["contentChangeReason"] = source_policy.get("reason", "")\n        probes[url] = probe',
    '        if source_policy:\n            probe["contentChangePolicy"] = source_policy.get("contentChange", "")\n            probe["contentChangeReason"] = source_policy.get("reason", "")\n            probe["redirectChangePolicy"] = source_policy.get("redirectChange", "")\n            probe["redirectChangeReason"] = source_policy.get("reason", "")\n        probes[url] = probe',
    "applicazione policy redirect",
)
new_compare = '''def compare_states(previous: dict[str, Any], current: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    previous_sources = previous.get("sources")
    if not isinstance(previous_sources, dict):
        previous_sources = {}

    # Le baseline storiche possono contenere la stessa URL in una forma non
    # canonicalizzata (es. ':' letterali vs %3A nella query). Normalizziamo
    # entrambe le parti prima di cercare fonti aggiunte/rimosse.
    normalized_previous: dict[str, dict[str, Any]] = {}
    for raw_url, raw_item in previous_sources.items():
        if not isinstance(raw_item, dict):
            continue
        try:
            normalized_url = canonical_url(str(raw_url))
        except Exception:
            normalized_url = str(raw_url)
        item = dict(raw_item)
        item["url"] = normalized_url
        if item.get("finalUrl"):
            try:
                item["finalUrl"] = canonical_url(str(item["finalUrl"]))
            except Exception:
                pass
        normalized_previous.setdefault(normalized_url, item)
    previous_sources = normalized_previous

    normalized_current: dict[str, dict[str, Any]] = {}
    for raw_url, raw_item in current.items():
        try:
            normalized_url = canonical_url(str(raw_url))
        except Exception:
            normalized_url = str(raw_url)
        item = dict(raw_item)
        item["url"] = normalized_url
        if item.get("finalUrl"):
            try:
                item["finalUrl"] = canonical_url(str(item["finalUrl"]))
            except Exception:
                pass
        normalized_current[normalized_url] = item
    current = normalized_current

    changes: dict[str, list[dict[str, Any]]] = {
        "added": [],
        "removed": [],
        "content": [],
        "informationalContent": [],
        "redirect": [],
        "informationalRedirect": [],
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
        old_mode = str(old.get("contentHashMode") or "raw")
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
        old_final = str(old.get("finalUrl") or "")
        new_final = str(item.get("finalUrl") or "")
        if old_final and new_final and old_final != new_final:
            redirect_item = {"url": url, "before": old_final, "after": new_final}
            reason = str(item.get("redirectChangeReason") or "")
            if reason:
                redirect_item["reason"] = reason
            if str(item.get("redirectChangePolicy") or "") == "informational":
                changes["informationalRedirect"].append(redirect_item)
            else:
                changes["redirect"].append(redirect_item)
        old_meta = (str(old.get("etag") or ""), str(old.get("lastModified") or ""))
        new_meta = (str(item.get("etag") or ""), str(item.get("lastModified") or ""))
        if old_meta != new_meta and any(old_meta) and any(new_meta):
            changes["metadata"].append({"url": url})
    return changes

'''
value, count = re.subn(
    r'def compare_states\(previous: dict\[str, Any\], current: dict\[str, dict\[str, Any\]\]\) -> dict\[str, list\[dict\[str, Any\]\]\]:\n.*?(?=def url_list)',
    new_compare,
    value,
    flags=re.S,
)
if count != 1:
    raise SystemExit(f"compare_states: attesa 1 sostituzione, trovate {count}")
value = replace_once(
    value,
    '    if changes["metadata"] or changes.get("informationalContent"):\n',
    '    if changes["metadata"] or changes.get("informationalContent") or changes.get("informationalRedirect"):\n',
    "condizione segnali informativi",
)
needle = '''        if changes.get("informationalContent"):
            lines.extend(
                [
                    "Il contenuto di alcune fonti operative continue è cambiato, ma la politica della fonte classifica il cambio come informativo: gli indicatori pubblicati usano una fotografia datata e versionata.",
                    "",
                    url_list(changes["informationalContent"]),
                    "",
                ]
            )
'''
replacement = needle + '''        if changes.get("informationalRedirect"):
            lines.extend(
                [
                    "Sono cambiati reindirizzamenti tecnici di landing page esplicitamente classificate come informative; il segnale non equivale a un nuovo rilascio dati.",
                    "",
                    url_list(changes["informationalRedirect"]),
                    "",
                ]
            )
'''
value = replace_once(value, needle, replacement, "report redirect informativi")
write(path, value)


# 2) Policy semantiche: anche il redirect può essere informativo.
path = "scripts/monitor_semantic_checks.py"
value = text(path)
value = replace_once(
    value,
    '    return {\n        "contentChange": str(item.get("contentChange") or "").strip(),\n        "reason": str(item.get("reason") or "").strip(),\n    }',
    '    return {\n        "contentChange": str(item.get("contentChange") or "").strip(),\n        "redirectChange": str(item.get("redirectChange") or "").strip(),\n        "reason": str(item.get("reason") or "").strip(),\n    }',
    "source_change_policy redirect",
)
write(path, value)


# 3) MIMIT giornaliero informativo; redirect ISTAT informativo.
path = ROOT / "data/source-registry.json"
registry = json.loads(path.read_text(encoding="utf-8"))
policies = registry.setdefault("sourceChangePolicies", {})
policies["https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"] = {
    "contentChange": "informational",
    "reason": "Feed prezzi carburanti aggiornato ogni giorno; l'avanzamento ordinario viene verificato semanticamente e diventa rilascio da revisionare solo nel controllo mensile programmato.",
}
policies["https://esploradati.istat.it/"] = {
    "redirectChange": "informational",
    "reason": "Landing page Istat: un cambio di redirect tecnico non dimostra la disponibilità di una nuova annualità dell'indicatore.",
}
path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# 4) Verifica MIMIT: i run ad hoc non inseguono il giorno successivo.
path = "scripts/monthly_data_check_status.py"
value = text(path)
value = replace_once(value, "import json\nimport sys\n", "import json\nimport os\nimport sys\n", "import os")
old = '''    source_key = canonical_url(str(metric.get("sourceUrl") or ""))
    needs_semantic_check = source_key in changed_urls(report) or str(item.get("status") or "") in {
        "verification_required",
        "release_detected",
    }
'''
new = '''    source_key = canonical_url(str(metric.get("sourceUrl") or ""))
    run_trigger = str(os.environ.get("MONITOR_RUN_TRIGGER") or "").strip()
    needs_semantic_check = run_trigger == "schedule" or source_key in changed_urls(report) or str(item.get("status") or "") in {
        "verification_required",
        "release_detected",
    }
'''
value = replace_once(value, old, new, "gate MIMIT per trigger")
old = '''        if fuel_result is not None:
            report["fuelMimitVerification"] = fuel_result
        elif fuel_error:
            report["fuelMimitVerificationError"] = fuel_error
        pnrr_result, pnrr_error = run_pnrr_verification(
'''
new = '''        if fuel_result is not None:
            report["fuelMimitVerification"] = fuel_result
        elif fuel_error:
            report["fuelMimitVerificationError"] = fuel_error

        # Il feed MIMIT è giornaliero: solo il run schedulato mensile deve
        # trasformare l'avanzamento ordinario in una PR di revisione.
        if (
            str(os.environ.get("MONITOR_RUN_TRIGGER") or "").strip() == "schedule"
            and isinstance(fuel_result, dict)
            and fuel_result.get("verdict") == "new_period"
            and report.get("status") == "no_changes"
        ):
            report["status"] = "changes_detected"
            current_md = args.report_md.read_text(encoding="utf-8")
            current_md = current_md.replace(
                "**Esito:** `no_changes`",
                "**Esito:** `changes_detected`",
                1,
            )
            args.report_md.write_text(current_md, encoding="utf-8")
            output_path = os.environ.get("GITHUB_OUTPUT")
            if output_path:
                with open(output_path, "a", encoding="utf-8") as output:
                    output.write("status=changes_detected\\n")

        pnrr_result, pnrr_error = run_pnrr_verification(
'''
value = replace_once(value, old, new, "promozione MIMIT mensile")
write(path, value)


# 5) Test di regressione dedicati.
path = "scripts/test_monthly_data_check.py"
value = text(path)
anchor = '''    assert not redirect_changes["redirect"]

    # Due ZIP con gli stessi membri ma timestamp differenti devono produrre lo
'''
insert = '''    assert not redirect_changes["redirect"]

    # La stessa URL ARPAT, con ':' letterali o percent-encoded nella query,
    # deve restare la stessa fonte anche se la baseline è stata prodotta da
    # una versione precedente del canonicalizzatore.
    arpat_legacy = "https://sira.arpat.toscana.it/apex/f?p=SISBON:REPORT_PER_RT::CSV:IR_REPORT_GEOSCOPIO"
    arpat_canonical = checker.canonical_url(arpat_legacy)
    arpat_changes = checker.compare_states(
        {"sources": {arpat_legacy: {"ok": True, "finalUrl": arpat_legacy}}},
        {arpat_canonical: {"ok": True, "finalUrl": arpat_canonical}},
    )
    assert not arpat_changes["added"]
    assert not arpat_changes["removed"]
    assert not arpat_changes["redirect"]

    # I redirect di landing page esplicitamente governate possono essere
    # informativi senza mettere l'indicatore in verifica necessaria.
    istat_url = "https://esploradati.istat.it/"
    info_redirect = checker.compare_states(
        {"sources": {istat_url: {"ok": True, "finalUrl": "https://old.example/"}}},
        {istat_url: {"ok": True, "finalUrl": "https://new.example/", "redirectChangePolicy": "informational", "redirectChangeReason": "landing tecnica"}},
    )
    assert not info_redirect["redirect"]
    assert info_redirect["informationalRedirect"] == [
        {"url": istat_url, "before": "https://old.example/", "after": "https://new.example/", "reason": "landing tecnica"}
    ]

    # Due ZIP con gli stessi membri ma timestamp differenti devono produrre lo
'''
value = replace_once(value, anchor, insert, "test ARPAT/ISTAT")
write(path, value)


# 6) Workflow: passa il tipo di run e non apre PR per no_changes.
path = ".github/workflows/monthly-data-refresh.yml"
value = text(path)
value, count = re.subn(
    r'\n      # PR128_BOOTSTRAP_START\n.*?      # PR128_BOOTSTRAP_END\n',
    "\n",
    value,
    flags=re.S,
)
if count != 1:
    raise SystemExit(f"rimozione bootstrap workflow: attesa 1, trovate {count}")
value = replace_once(
    value,
    '      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}\n      PYTHONUNBUFFERED: "1"\n',
    '      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}\n      PYTHONUNBUFFERED: "1"\n      MONITOR_RUN_TRIGGER: ${{ github.event_name }}\n',
    "env trigger workflow",
)
value = replace_once(
    value,
    '''        if: >-
          github.event_name != 'pull_request' &&
          steps.prepare.outputs.mode == 'live' &&
          steps.monitor.outputs.status != 'attention_required'
''',
    '''        if: >-
          github.event_name != 'pull_request' &&
          steps.prepare.outputs.mode == 'live' &&
          (steps.monitor.outputs.status == 'changes_detected' ||
           steps.monitor.outputs.status == 'baseline_required')
''',
    "condizione apertura PR",
)
value = value.replace(
    "          - ogni esecuzione live registra metadata aggiornati in una PR in bozza;",
    "          - una PR in bozza viene aperta solo quando il controllo trova modifiche sostanziali o richiede una baseline;",
)
value = value.replace(
    "Questa PR registra la data effettiva del controllo, lo stato operativo delle fonti e degli indicatori e gli eventuali segnali da verificare. Anche quando non emergono variazioni sostanziali, la PR aggiorna i soli metadata di controllo: i valori di `data/site-data.json` restano invariati.",
    "Questa PR viene aperta solo quando il controllo rileva modifiche sostanziali o richiede una baseline. I run `no_changes` restano nel registro e negli artifact del workflow, senza generare una nuova PR.",
)
write(path, value)


# 7) Togliamo dalla PR lo stato rumoroso generato dal run del 30/08.
subprocess.run(
    [
        "git",
        "checkout",
        "origin/main",
        "--",
        "data/source-monitor-state.json",
        "reports/data-checks/2026-08.md",
    ],
    cwd=ROOT,
    check=True,
)

# Il bootstrap non deve restare nella PR.
Path(__file__).unlink()
print("PR128 monitor fix applied")
