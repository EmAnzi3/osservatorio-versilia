#!/usr/bin/env python3
"""Cattura schermate desktop e mobile della preview ASIA/AGCOM/ATECO."""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


PAGES = (
    (
        "economia",
        "/confronta/economia/?indicatore=localEmployees",
        "#ateco-compare-module",
    ),
    (
        "massarosa-ateco",
        "/comuni/massarosa/?tema=economia&indicatore=localEmployees",
        "#ateco-town-module",
    ),
    (
        "mobilita-infrastrutture",
        "/confronta/mobilita/?indicatore=ftthCoverageDesi",
        "#compare-bars",
    ),
)


async def capture(base_url: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            for profile, viewport in (
                ("desktop", {"width": 1440, "height": 1100}),
                ("mobile", {"width": 390, "height": 844}),
            ):
                context = await browser.new_context(
                    viewport=viewport,
                    device_scale_factor=1,
                    locale="it-IT",
                )
                page = await context.new_page()
                for name, path, selector in PAGES:
                    await page.goto(
                        f"{base_url.rstrip('/')}{path}",
                        wait_until="networkidle",
                        timeout=60_000,
                    )
                    await page.wait_for_selector(selector, timeout=30_000)
                    await page.screenshot(
                        path=output_dir / f"{name}-{profile}.png",
                        full_page=True,
                    )
                await context.close()
        finally:
            await browser.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/previews/imprese-banda-larga"),
    )
    args = parser.parse_args()
    asyncio.run(capture(args.base_url, args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
