#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

from test_a5_camaiore_rollout import EXPECTED, VIEWPORTS, choose, discover, go, stable, state

APPROVED_COMMIT = "5aaf159870912eb49bffbd044963549bfb920150"
REVIEW_METRICS = {
    "population",
    "incomeDistribution",
    "employmentRate",
    "diplomaPlus",
    "lifeExpectancy",
    "outsideMunicipality",
    "roadSafety",
    "omiResidential",
    "landCoverProfile",
    "landslideExposure",
    "climateTemperatureTrend50y",
    "drinkingWaterQuality",
    "financialDebtProfile",
    "libraryLoansPerResident",
    "pnrrFunding",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_state(value):
    """Normalize browser non-finite geometry sentinels without hiding real diffs."""
    if isinstance(value, float) and not math.isfinite(value):
        return "__NONFINITE__"
    if isinstance(value, dict):
        return {key: canonical_state(item) for key, item in value.items()}
    if isinstance(value, list):
        return [canonical_state(item) for item in value]
    return value


def pixel_difference(baseline: bytes, current: bytes, threshold: int = 3) -> dict:
    first = Image.open(io.BytesIO(baseline)).convert("RGB")
    second = Image.open(io.BytesIO(current)).convert("RGB")
    if first.size != second.size:
        return {
            "same_size": False,
            "baseline_size": first.size,
            "current_size": second.size,
            "ratio": 1.0,
        }
    diff = ImageChops.difference(first, second)
    total = first.size[0] * first.size[1]
    changed = sum(1 for pixel in diff.getdata() if max(pixel) > threshold)
    return {
        "same_size": True,
        "baseline_size": first.size,
        "current_size": second.size,
        "changed": changed,
        "total": total,
        "ratio": changed / total if total else 0.0,
    }


def compare_screenshot(base_page, cur_page, selector: str, key: str, folder: Path, failures: list[dict]) -> None:
    base_loc = base_page.locator(selector)
    cur_loc = cur_page.locator(selector)
    if base_loc.count() != 1 or cur_loc.count() != 1:
        failures.append({
            "key": key,
            "kind": "golden-region-missing",
            "selector": selector,
            "baselineCount": base_loc.count(),
            "currentCount": cur_loc.count(),
        })
        return
    before = base_loc.screenshot(animations="disabled")
    after = cur_loc.screenshot(animations="disabled")
    diff = pixel_difference(before, after)
    if (not diff["same_size"]) or diff["ratio"] > 0.0005:
        bpath = folder / f"{key}-baseline.png"
        cpath = folder / f"{key}-current.png"
        bpath.write_bytes(before)
        cpath.write_bytes(after)
        failures.append({
            "key": key,
            "kind": "camaiore-visual-golden-diff",
            "selector": selector,
            "pixelDiff": diff,
            "baselineSha256": digest(before),
            "currentSha256": digest(after),
            "baselineImage": bpath.name,
            "currentImage": cpath.name,
        })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-base", required=True)
    parser.add_argument("--baseline-base", required=True)
    parser.add_argument("--report-dir", required=True)
    args = parser.parse_args()

    folder = Path(args.report_dir)
    folder.mkdir(parents=True, exist_ok=True)
    failures: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        probe_current = browser.new_page(viewport={"width": 1440, "height": 1100})
        probe_baseline = browser.new_page(viewport={"width": 1440, "height": 1100})
        current_contract = discover(probe_current, args.current_base)
        baseline_contract = discover(probe_baseline, args.baseline_base)
        probe_current.close()
        probe_baseline.close()

        total = sum(map(len, current_contract.values()))
        unique = len({metric for metrics in current_contract.values() for metric in metrics})
        if current_contract != baseline_contract:
            failures.append({
                "key": "catalog",
                "kind": "camaiore-contract-diff",
                "baseline": baseline_contract,
                "current": current_contract,
            })
        if total != EXPECTED or unique != EXPECTED:
            failures.append({
                "key": "catalog",
                "kind": "camaiore-golden-metric-count",
                "expected": EXPECTED,
                "total": total,
                "unique": unique,
            })

        checked = 0
        for viewport, width, height in VIEWPORTS:
            base_page = browser.new_page(viewport={"width": width, "height": height})
            cur_page = browser.new_page(viewport={"width": width, "height": height})
            baseline_errors: list[str] = []
            current_errors: list[str] = []
            base_page.on("pageerror", lambda error: baseline_errors.append(str(error)))
            cur_page.on("pageerror", lambda error: current_errors.append(str(error)))

            for theme, metrics in current_contract.items():
                go(base_page, args.baseline_base, theme, metrics[0])
                go(cur_page, args.current_base, theme, metrics[0])

                if theme == next(iter(current_contract)):
                    compare_screenshot(
                        base_page,
                        cur_page,
                        ".town-hero",
                        f"{viewport}-hero",
                        folder,
                        failures,
                    )

                for metric in metrics:
                    choose(base_page, metric)
                    choose(cur_page, metric)
                    key = f"{viewport}:{theme}:{metric}"
                    baseline_state = canonical_state(state(base_page))
                    current_state = canonical_state(state(cur_page))
                    checked += 1

                    if baseline_state != current_state:
                        failures.append({
                            "key": key,
                            "kind": "camaiore-computed-golden-diff",
                            "baseline": baseline_state,
                            "current": current_state,
                        })

                    if metric == metrics[0] or metric in REVIEW_METRICS:
                        compare_screenshot(
                            base_page,
                            cur_page,
                            "#town-topic",
                            f"{viewport}-{theme}-{metric}",
                            folder,
                            failures,
                        )

            if baseline_errors:
                failures.append({"key": viewport, "kind": "baseline-page-errors", "errors": baseline_errors})
            if current_errors:
                failures.append({"key": viewport, "kind": "current-page-errors", "errors": current_errors})
            base_page.close()
            cur_page.close()

        browser.close()

    report = {
        "approved_commit": APPROVED_COMMIT,
        "town": "camaiore",
        "checked_states": checked,
        "themes": list(current_contract),
        "metric_states_per_viewport": total,
        "unique_metric_count": unique,
        "viewports": [{"name": name, "width": width, "height": height} for name, width, height in VIEWPORTS],
        "failure_count": len(failures),
        "failures": failures,
    }
    (folder / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folder / "summary.txt").write_text(
        "A5 Camaiore full golden lock\n"
        f"approved_commit={APPROVED_COMMIT}\n"
        f"checked_states={checked}\n"
        f"failures={len(failures)}\n",
        encoding="utf-8",
    )
    if failures:
        raise SystemExit(
            f"A5 Camaiore full golden lock FAILED: {len(failures)} problemi\n"
            + json.dumps(failures[:10], ensure_ascii=False, indent=2)
        )
    print(
        f"A5 Camaiore full golden lock OK: {checked} stati "
        f"({total}/viewport) invariati rispetto a {APPROVED_COMMIT[:7]}."
    )


if __name__ == "__main__":
    main()
