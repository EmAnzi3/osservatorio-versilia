#!/usr/bin/env python3
"""Inventario diagnostico delle fonti ufficiali necessarie alla v1.37.

Non modifica data/site-data.json. Serve esclusivamente nella Action di acquisizione
per risolvere gli URL correnti dei cataloghi Regione Toscana e verificare gli input.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

OUT = Path("tmp/territorio-v137-source-inventory.json")
CKAN = "https://dati.toscana.it/api/3/action/package_show?id={}"
PACKAGES = {
    "roads": "grafo-civici",
    "protected": "arprot",
    "natura2000": "sir",
    "ramsar": "ramsar",
}
DIRECT = {
    "ispraSoil": "https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/suolo/il-consumo-di-suolo/consumo_di_suolo_estratto_dati_2025_anni_2006_2024.xlsx",
    "reticulumPage": "https://www.regione.toscana.it/-/reticolo-idrografico-e-di-gestione",
    "reticulumZip": "https://www.regione.toscana.it/documents/d/guest/infrastruttura_rev25-zip",
    "protectedPage": "https://www.regione.toscana.it/-/il-sistema-delle-aree-naturali-protette",
    "natura2000Page": "https://www.regione.toscana.it/-/rete-natura-2000-in-toscana-2",
    "ramsarPage": "https://www.regione.toscana.it/-/aree-ramsar",
    "roadsPage": "https://www.regione.toscana.it/-/reticolo-stradale-regionale",
}


def request_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia-v137-source-audit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def probe(url: str) -> dict:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "OsservatorioVersilia-v137-source-audit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return {
                "status": response.status,
                "finalUrl": response.geturl(),
                "contentType": response.headers.get("Content-Type"),
                "contentLength": response.headers.get("Content-Length"),
                "etag": response.headers.get("ETag"),
                "lastModified": response.headers.get("Last-Modified"),
            }
    except urllib.error.HTTPError as exc:
        # Alcuni endpoint disabilitano HEAD pur accettando GET: registriamo la risposta
        # senza trasformarla in un falso negativo dell'intero inventario.
        return {"status": exc.code, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - diagnostica: preservare il motivo
        return {"status": None, "error": repr(exc)}


def normalized_resource(resource: dict) -> dict:
    return {
        "id": resource.get("id"),
        "name": resource.get("name"),
        "format": resource.get("format"),
        "url": resource.get("url"),
        "size": resource.get("size"),
        "last_modified": resource.get("last_modified"),
        "created": resource.get("created"),
        "description": resource.get("description"),
    }


def main() -> None:
    output = {"packages": {}, "direct": {}}
    failures = []

    for key, package_id in PACKAGES.items():
        url = CKAN.format(package_id)
        try:
            payload = request_json(url)
            if not payload.get("success"):
                raise RuntimeError(f"CKAN success=false for {package_id}")
            result = payload["result"]
            resources = [normalized_resource(item) for item in result.get("resources", [])]
            output["packages"][key] = {
                "packageId": package_id,
                "title": result.get("title"),
                "metadataModified": result.get("metadata_modified"),
                "version": result.get("version"),
                "resources": resources,
            }
            if not resources:
                failures.append(f"{package_id}: nessuna risorsa")
        except Exception as exc:  # noqa: BLE001
            output["packages"][key] = {"packageId": package_id, "error": repr(exc)}
            failures.append(f"{package_id}: {exc!r}")

    for key, url in DIRECT.items():
        output["direct"][key] = {"url": url, "probe": probe(url)}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit("Inventario incompleto: " + "; ".join(failures))


if __name__ == "__main__":
    main()
