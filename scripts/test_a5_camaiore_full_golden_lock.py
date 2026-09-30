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
EXPECTED_TOWN_ORDER = (
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
)


def town_nav_order(page) -> list[str]:
    return page.evaluate("""() => [
      ...document.querySelectorAll('.town-context-nav .context-nav-row:first-child .context-nav-links > a')
    ].map(el => (el.textContent || '').trim())""")


def normalize_baseline_town_order(page) -> None:
    result = page.evaluate("""expected => {
      const host = document.querySelector('.town-context-nav .context-nav-row:first-child .context-nav-links');
      if (!host) return {ok:false, reason:'host-missing'};
      const links = [...host.querySelectorAll(':scope > a')];
      const byName = new Map(links.map(link => [(link.textContent || '').trim(), link]));
      const missing = expected.filter(name => !byName.has(name));
      if (missing.length) return {ok:false, reason:'links-missing', missing};
      expected.forEach(name => host.append(byName.get(name)));
      return {ok:true};
    }""", list(EXPECTED_TOWN_ORDER))
    if not result.get("ok"):
        raise AssertionError(f"Camaiore baseline town-nav normalization failed: {result}")


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
    """Normalize browser sentinels and the rollout implementation marker only."""
    if isinstance(value, float) and not math.isfinite(value):
        return "__NONFINITE__"
    if isinstance(value, dict):
        normalized = {key: canonical_state(item) for key, item in value.items()}
        if isinstance(normalized.get("classes"), list):
            normalized["classes"] = [
                name for name in normalized["classes"]
                if name != "a5-municipal-rollout"
            ]
        return normalized
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


def public_history_state(page) -> dict:
    return page.evaluate(
        """() => {
          const shell=document.querySelector('#town-topic > .history-panel.a5-shared-chart .ux-view-shell');
          const button=shell?.querySelector('[data-view-mode="history"]');
          const pane=shell?.querySelector('[data-view-pane="history"]');
          const text=(pane?.textContent || '').trim();
          return {
            buttonExists:Boolean(button),
            paneExists:Boolean(pane),
            disabled:Boolean(button?.disabled),
            chartCount:pane?.querySelectorAll('.ux-history-chart, .ux-two-point-chart, .trend-chart, .history-chart, [data-history-chart], svg, canvas').length || 0,
            unavailable:Boolean(
              pane?.querySelector('.ux-history-unavailable')
              || /serie storica non disponibile/i.test(text)
            ),
            contentLength:text.length,
          };
        }"""
    )


def verified_history_upgrade(baseline_state: dict, current_state: dict, base_page, cur_page) -> tuple[bool, dict]:
    baseline_shell = baseline_state.get("semantic", {}).get("financialShell", {})
    current_shell = current_state.get("semantic", {}).get("financialShell", {})
    if baseline_shell.get("historyChart") is not False or current_shell.get("historyChart") is not True:
        return False, {}

    normalized_current = json.loads(json.dumps(current_state))
    normalized_current["semantic"]["financialShell"]["historyChart"] = False
    if baseline_state != normalized_current:
        return False, {}

    baseline_dom = public_history_state(base_page)
    current_dom = public_history_state(cur_page)
    allowed = bool(
        baseline_dom["buttonExists"]
        and baseline_dom["paneExists"]
        and baseline_dom["disabled"]
        and current_dom["buttonExists"]
        and current_dom["paneExists"]
        and not current_dom["disabled"]
        and current_dom["chartCount"] >= 1
        and not current_dom["unavailable"]
        and current_dom["contentLength"] > 0
    )
    return allowed, {"baseline": baseline_dom, "current": current_dom}


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
    allowed_history_upgrades: list[dict] = []

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
                normalize_baseline_town_order(base_page)

                expected_town_order = list(EXPECTED_TOWN_ORDER)
                baseline_town_order = town_nav_order(base_page)
                current_town_order = town_nav_order(cur_page)
                if baseline_town_order != expected_town_order:
                    failures.append({
                        "key": f"{viewport}:{theme}:baseline-town-order",
                        "kind": "camaiore-baseline-town-order-normalization",
                        "value": baseline_town_order,
                        "expected": expected_town_order,
                    })
                if current_town_order != expected_town_order:
                    failures.append({
                        "key": f"{viewport}:{theme}:current-town-order",
                        "kind": "camaiore-current-town-order",
                        "value": current_town_order,
                        "expected": expected_town_order,
                    })

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
                    baseline_raw = state(base_page)
                    current_raw = state(cur_page)
                    if "a5-municipal-rollout" not in current_raw.get("classes", []):
                        failures.append({
                            "key": key,
                            "kind": "camaiore-rollout-marker-missing",
                            "classes": current_raw.get("classes", []),
                        })
                    baseline_state = canonical_state(baseline_raw)
                    current_state = canonical_state(current_raw)
                    checked += 1

                    if baseline_state != current_state:
                        allowed_upgrade, history_detail = verified_history_upgrade(
                            baseline_state,
                            current_state,
                            base_page,
                            cur_page,
                        )
                        if allowed_upgrade:
                            allowed_history_upgrades.append({
                                "key": key,
                                **history_detail,
                            })
                        else:
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
        "allowed_history_upgrades": allowed_history_upgrades,
        "failure_count": len(failures),
        "failures": failures,
    }
    (folder / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folder / "summary.txt").write_text(
        "A5 Camaiore full golden lock\n"
        f"approved_commit={APPROVED_COMMIT}\n"
        f"checked_states={checked}\n"
        f"allowed_history_upgrades={len(allowed_history_upgrades)}\n"
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
