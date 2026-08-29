#!/usr/bin/env python3
from pathlib import Path

materializer = Path("scripts/materialize_costa_mare_v123.py")
text = materializer.read_text(encoding="utf-8")
start = text.index("def apply_monitor_state(state: dict[str, Any]) -> None:\n")
end = text.index("\ndef patch_search_terms() -> None:\n", start)
new_block = '''def apply_monitor_state(state: dict[str, Any]) -> None:
    """Inizializza lo stato v1.23 senza degradare verifiche live più recenti.

    Il materializzatore della release può essere rilanciato in CI dopo che il
    monitor ha già registrato metadati, hash, evidenze e timestamp più recenti.
    Questi dati operativi non appartengono alla materializzazione e non devono
    essere riscritti. I valori qui sotto sono quindi solo default per una baseline
    che ancora non contiene le fonti o gli indicatori Costa e mare.
    """
    checked = "2026-08-28T18:00:00+00:00"
    source_config = {
        ARPAT_URL: ([KEYS[0], KEYS[1]], "arpat-bathing-annual", "annual"),
        BLUE_FLAG_URL: ([KEYS[2]], "fee-blue-flag-annual", "annual"),
        ISPRA_DYNAMICS_URL: ([KEYS[3]], "ispra-coast-irregular", "census_or_irregular"),
        ISPRA_PROTECTED_URL: ([KEYS[4]], "ispra-coast-irregular", "census_or_irregular"),
    }
    sources = state.setdefault("sources", {})
    for url, (metrics, profile, frequency) in source_config.items():
        defaults = {
            "url": url,
            "ok": True,
            "status": 200,
            "finalUrl": url,
            "contentType": "text/html",
            "contentLength": None,
            "etag": "",
            "lastModified": "",
            "contentSha256": "",
            "hashTruncated": False,
            "error": "",
            "metrics": metrics,
            "roles": ["primary"],
            "profileIds": [profile],
            "frequencies": [frequency],
        }
        current = sources.get(url)
        if not isinstance(current, dict):
            sources[url] = defaults
            continue
        for field, value in defaults.items():
            current.setdefault(field, value)

    periods = {
        KEYS[0]: "2025",
        KEYS[1]: "2025",
        KEYS[2]: "2026",
        KEYS[3]: "2006–2020",
        KEYS[4]: "2020",
    }
    metrics_state = state.setdefault("metrics", {})
    for key, period in periods.items():
        current = metrics_state.get(key)
        if not isinstance(current, dict):
            metrics_state[key] = {
                "publishedPeriod": period,
                "checkedAt": checked,
                "observedLatestPeriod": period,
                "status": "current",
            }
            continue
        current.setdefault("publishedPeriod", period)
        current.setdefault("checkedAt", checked)
        current.setdefault("observedLatestPeriod", period)
        current.setdefault("status", "current")
'''
materializer.write_text(text[:start] + new_block + text[end:], encoding="utf-8")

test = Path("scripts/test_costa_mare_v123.py")
text = test.read_text(encoding="utf-8")
if "import materialize_costa_mare_v123 as coast_materializer" not in text:
    text = text.replace(
        "import math\nfrom pathlib import Path\n",
        "import math\nfrom pathlib import Path\n\nimport materialize_costa_mare_v123 as coast_materializer\n",
        1,
    )
marker = "\ndef assert_registry_and_ui(data: dict) -> None:\n"
regression = '''\ndef assert_monitor_state_preservation() -> None:
    url = coast_materializer.ISPRA_PROTECTED_URL
    metric = coast_materializer.KEYS[4]
    state = {
        "sources": {
            url: {
                "url": url,
                "ok": True,
                "status": 200,
                "finalUrl": url,
                "contentType": "text/html",
                "contentLength": "70716",
                "etag": "live-etag",
                "lastModified": "Sat, 29 Aug 2026 12:00:00 GMT",
                "contentSha256": "live-hash",
                "contentHashMode": "raw",
                "contentChangePolicy": "",
                "contentChangeReason": "",
                "hashTruncated": False,
                "error": "",
                "metrics": [metric],
                "roles": ["primary"],
                "profileIds": ["ispra-coast-irregular"],
                "frequencies": ["census_or_irregular"],
                "probeMethod": "urllib",
            }
        },
        "metrics": {
            metric: {
                "publishedPeriod": "2020",
                "checkedAt": "2026-08-29T12:22:42+00:00",
                "observedLatestPeriod": "2020",
                "status": "current",
                "verificationEvidence": {"verdict": "match"},
            }
        },
    }
    before_source = dict(state["sources"][url])
    before_metric = dict(state["metrics"][metric])
    coast_materializer.apply_monitor_state(state)
    assert state["sources"][url] == before_source
    assert state["metrics"][metric] == before_metric

    empty = {"sources": {}, "metrics": {}}
    coast_materializer.apply_monitor_state(empty)
    for key in coast_materializer.KEYS:
        assert empty["metrics"][key]["status"] == "current"
        assert empty["metrics"][key]["checkedAt"] == "2026-08-28T18:00:00+00:00"
    assert empty["sources"][coast_materializer.ARPAT_URL]["metrics"] == [
        coast_materializer.KEYS[0], coast_materializer.KEYS[1]
    ]
'''
if "def assert_monitor_state_preservation()" not in text:
    text = text.replace(marker, regression + marker, 1)
call_marker = "    assert_registry_and_ui(data)\n"
if "    assert_monitor_state_preservation()\n" not in text:
    text = text.replace(call_marker, "    assert_monitor_state_preservation()\n" + call_marker, 1)
test.write_text(text, encoding="utf-8")
