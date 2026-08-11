#!/usr/bin/env python3
"""Compatibility runner for LaMMA annual history.

The CKAN package for historical daily minimum temperatures exposes several
resource URLs with the filename prefix `Tmix_` even though the downloadable
archive uses `Tmin_`. Patch only that catalogue typo at runtime, keeping the
main processing script source-oriented and auditable.
"""
from __future__ import annotations

import lamma_annual_history as history

_original_resources_for = history.resources_for


def resources_for(package: str) -> dict[int, str]:
    resources = _original_resources_for(package)
    if package == history.PACKAGES["tmin"]:
        resources = {
            year: url.replace("/Tmix_giornaliero_", "/Tmin_giornaliero_")
            for year, url in resources.items()
        }
    return resources


history.resources_for = resources_for

if __name__ == "__main__":
    raise SystemExit(history.main())
