#!/usr/bin/env python3
"""Read-only inspection of the generated SIOPE parser and one official OData page."""
from __future__ import annotations

import inspect
import json
from urllib.parse import quote

import build_siope_history as builder

BASE = "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3"
PACKAGE_ID = "7deb457c-3207-481f-bed0-ffd45be4ff59"


def main() -> None:
    print("=== FUNZIONI DEL COSTRUTTORE SIOPE ===")
    functions = {
        name: value
        for name, value in vars(builder).items()
        if inspect.isfunction(value) and value.__module__ == builder.__name__
    }
    print(sorted(functions))

    relevant_tokens = (
        "resource", "header", "dataset", "parse", "normal", "main", "amount", "month"
    )
    for name, function in functions.items():
        if any(token in name.casefold() for token in relevant_tokens):
            print(f"\n=== SOURCE {name} ===")
            try:
                print(inspect.getsource(function))
            except OSError as exc:
                print(f"SOURCE NON DISPONIBILE: {exc}")

    print("\n=== COSTANTI RILEVANTI ===")
    for name, value in vars(builder).items():
        if name.isupper() and any(
            token in name.casefold()
            for token in ("town", "year", "category", "code", "column", "indicator", "month")
        ):
            try:
                rendered = json.dumps(value, ensure_ascii=False, default=str)
            except TypeError:
                rendered = repr(value)
            print(f"{name} = {rendered[:12000]}")

    session = builder.requests.Session()
    session.headers.update({"User-Agent": "OsservatorioVersilia/1.0"})
    package_url = f"{BASE}/action/package_show?id={quote(PACKAGE_ID)}"
    package_response = session.get(package_url, timeout=30)
    package_response.raise_for_status()
    package = package_response.json()["result"]
    odata_resources = [
        resource for resource in package.get("resources", [])
        if str(resource.get("resource_type") or "").casefold() == "odata"
    ]
    if len(odata_resources) != 1:
        raise RuntimeError(f"Risorsa OData non univoca: {odata_resources}")
    resource = odata_resources[0]
    rows_url = str(resource["url"]).replace("http://", "https://", 1)
    response = session.get(
        rows_url,
        params={"$skip": "0", "$top": "3", "$format": "json"},
        headers={"Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("d", {}).get("results", [])
    print("\n=== RISORSA ODATA E PRIME RIGHE ===")
    print(json.dumps({
        "resource": resource,
        "requested_url": response.url,
        "row_count": len(rows),
        "field_names": [key for key in rows[0] if key != "__metadata"] if rows else [],
        "rows": rows,
    }, ensure_ascii=False, indent=2)[:30000])


if __name__ == "__main__":
    main()
