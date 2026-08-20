#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from data_status_model import build_public_status  # noqa: E402

DATASET_URL = "https://dati.toscana.it/dataset/regione-toscana-pnrr"
SOCIAL_IMAGE = "https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg"
EXPECTED = {
    "046005": {"projects": 16, "concluded": 10, "funding": 3270511.41},
    "046013": {"projects": 15, "concluded": 10, "funding": 1337644.46},
    "046018": {"projects": 11, "concluded": 10, "funding": 5965208.14},
    "046024": {"projects": 12, "concluded": 9, "funding": 9478237.98},
    "046028": {"projects": 12, "concluded": 8, "funding": 2485485.63},
    "046030": {"projects": 11, "concluded": 9, "funding": 2055502.34},
    "046033": {"projects": 24, "concluded": 18, "funding": 12090517.68},
}
EXPECTED_WORK_STATUS = {
    "Collaudo completato": (7, 5830474.87),
    "Collaudo avviato": (12, 18593970.29),
    "Lavori in esecuzione": (1, 2500000.00),
    "Contratto stipulato": (1, 1440000.00),
    "Stipula in corso": (1, 495000.00),
}
SOCIAL_META_TOKENS = (
    'property="og:title"',
    'property="og:description"',
    'property="og:type"',
    'property="og:url"',
    'property="og:site_name"',
    'property="og:locale"',
    'property="og:image"',
    'property="og:image:alt"',
    'name="twitter:card"',
    'name="twitter:title"',
    'name="twitter:description"',
    'name="twitter:site"',
    'name="twitter:image"',
    'name="twitter:image:alt"',
)


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def rows(metric):
    return {str(row["code"]): row for row in metric["rows"]}


def count_summary_matches(node, expected):
    count = 0
    if isinstance(node, dict):
        required = {"pnrrProjects", "pnrrConcluded", "pnrrInProgress", "pnrrFunding"}
        if required.issubset(node):
            if (
                node["pnrrProjects"] == expected["projects"]
                and node["pnrrConcluded"] == expected["concluded"]
                and node["pnrrInProgress"] == expected["projects"] - expected["concluded"]
                and math.isclose(float(node["pnrrFunding"]), expected["funding"], abs_tol=0.01)
            ):
                count += 1
        for child in node.values():
            count += count_summary_matches(child, expected)
    elif isinstance(node, list):
        for child in node:
            count += count_summary_matches(child, expected)
    return count


def validate_deep_dive(data):
    deep = data["pnrrDeepDive"]
    totals = deep["totals"]
    works = deep["physicalWorks"]
    assert totals == {
        "projects": 101,
        "concluded": 74,
        "execution": 26,
        "contracting": 1,
        "funding": 36683107.64,
    }
    assert len(deep["towns"]) == 7
    assert works["count"] == 22
    assert math.isclose(float(works["funding"]), 28859445.16, abs_tol=0.01)
    assert math.isclose(float(works["fundingSharePercent"]), 78.672302, abs_tol=0.001)
    assert len(works["works"]) == 22
    assert len({item["cup"] for item in works["works"]}) == 22
    status = {item["status"]: (item["count"], item["funding"]) for item in works["statusSummary"]}
    for key, (count, funding) in EXPECTED_WORK_STATUS.items():
        assert status[key][0] == count
        assert math.isclose(float(status[key][1]), funding, abs_tol=0.01)
    text = json.dumps(deep, ensure_ascii=False).lower()
    assert "non equivale automaticamente" in text
    assert "percentuale di spesa" in text
    assert "realizzata" not in text


def validate_built_preview(data):
    page = Path("dist/pnrr/index.html")
    if not page.exists():
        return
    text = page.read_text(encoding="utf-8")
    assert 'data-page="pnrr"' in text
    assert "Dentro il PNRR" in text
    assert "Regione Toscana — Open Data PNRR" in text
    assert text.count('data-pnrr-work="true"') == 22
    assert "Asilo nido Girotondo a Piano di Mommio" in text
    assert "Piscina comunale G. Frati" in text
    assert "Nuova piscina comunale" in text
    assert "Collaudo completato" in text
    assert "Collaudo avviato" in text
    assert "realizzata" not in text.lower()
    assert "ov-mark-svg" in text
    assert "assets/pnrr-deep-dive.css" in text
    for token in SOCIAL_META_TOKENS:
        assert text.count(token) == 1, f"Metadata social PNRR non canonico: {token}"
    assert SOCIAL_IMAGE in text
    assert 'name="twitter:card" content="summary_large_image"' in text
    assert 'name="twitter:site" content="@OssVersilia"' in text
    assert text.count('data-data-status-nav="header"') == 1
    assert text.count('data-data-status-nav="footer"') == 1

    sitemap = Path("dist/sitemap.xml").read_text(encoding="utf-8")
    assert sitemap.count("https://osservatorioversilia.it/pnrr/") == 1

    for key in ("pnrrFunding", "pnrrConcluded"):
        slug = slugify(data["metrics"][key]["meta"]["label"])
        indicator = Path("dist/indicatori") / slug / "index.html"
        assert indicator.exists(), indicator
        indicator_text = indicator.read_text(encoding="utf-8")
        assert 'data-pnrr-deep-dive-teaser="true"' in indicator_text
        assert 'href="../../pnrr/"' in indicator_text
        assert "assets/pnrr-deep-dive.css" in indicator_text

    bundle = Path("dist/assets/app-bundle.js").read_text(encoding="utf-8")
    assert (
        "pageType === 'pnrr'" in bundle
        or "['status', 'pnrr', 'special'].includes(pageType)" in bundle
    )


def main():
    data = json.loads(Path("data/site-data.json").read_text(encoding="utf-8"))
    registry = json.loads(Path("data/source-registry.json").read_text(encoding="utf-8"))
    state = json.loads(Path("data/source-monitor-state.json").read_text(encoding="utf-8"))
    metrics = data["metrics"]
    assert len(metrics) == 127
    pop = rows(metrics["population"])
    funding = rows(metrics["pnrrFunding"])
    concluded = rows(metrics["pnrrConcluded"])

    assert metrics["pnrrFunding"]["meta"]["source"] == "Regione Toscana — Open Data PNRR"
    assert metrics["pnrrConcluded"]["meta"]["source"] == "Regione Toscana — Open Data PNRR"
    assert metrics["pnrrFunding"]["sourceUrl"] == DATASET_URL
    assert metrics["pnrrConcluded"]["sourceUrl"] == DATASET_URL

    for code, expected in EXPECTED.items():
        population = float(pop[code]["value"])
        expected_per_resident = expected["funding"] / population
        expected_concluded = expected["concluded"] / expected["projects"] * 100
        assert math.isclose(float(funding[code]["value"]), expected_per_resident, rel_tol=0, abs_tol=1e-9)
        assert math.isclose(float(concluded[code]["value"]), expected_concluded, rel_tol=0, abs_tol=1e-9)
        assert count_summary_matches(data, expected) >= 1

    assert sum(v["projects"] for v in EXPECTED.values()) == 101
    assert sum(v["concluded"] for v in EXPECTED.values()) == 74
    assert math.isclose(sum(v["funding"] for v in EXPECTED.values()), 36683107.64, abs_tol=0.01)
    validate_deep_dive(data)

    profile = registry["sourceProfiles"]["regione-toscana-pnrr-monthly"]
    assert profile["publisher"] == "Regione Toscana"
    assert profile["frequency"] == "monthly"
    assert registry["sourceProfileByUrl"][DATASET_URL] == "regione-toscana-pnrr-monthly"
    assert registry["expectedMetricCount"] == 127
    assert registry["expectedInlineMetricCount"] == 123
    assert registry["expectedExternalMetricCount"] == 4

    public = build_public_status(data, registry, state)
    public_by_key = {item["key"]: item for item in public["metrics"]}
    for key in ("pnrrFunding", "pnrrConcluded"):
        item = public_by_key[key]
        assert item["status"] == "current"
        assert item["sourceAutomationLimited"] is False
        assert item["sourceReachable"] is True
        assert item["observedLatestPeriod"] == "2026"
        assert item["verificationSource"]["dataElaborationDate"] == "2026-08-11"
        assert item["verificationSource"]["match7of7"] is True

    validate_built_preview(data)
    print("OK: bozza PNRR Toscana + Dentro il PNRR coerenti, 127 indicatori invariati")


if __name__ == "__main__":
    main()
