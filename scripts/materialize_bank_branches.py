#!/usr/bin/env python3
"""Aggiunge al catalogo effettivo, in build, l'indicatore degli sportelli bancari.

Come gli altri indicatori nati dopo il catalogo canonico (RSA accreditate,
atlante delle attività…), `bankBranchesPer1000` non sta in `data/site-data.json`:
lo costruisce questo passo dell'overlay di build dall'ultimo snapshot
`data/source-snapshots/bdi-sportelli-bancari-AAAA.json`, scritto e riconciliato
da `update_source_data.py bdi-branches --year AAAA`. Registra anche il profilo
della fonte nel registro dell'overlay, così il controllo mensile la riconosce.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import bank_branches as bb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
PROFILE = "bdi-giava-continuous"
PROFILE_SPEC = {
    "publisher": "Banca d'Italia", "frequency": "annual",
    "frequencyLabel": "Annuale (fotografia al 31 dicembre da elenco aggiornato di continuo)",
    "expectedRelease": "Elenco delle succursali aggiornato di continuo; la fotografia dell'anno si chiude al 31 dicembre",
    "acquisitionMethod": ("Download dell'open data GIAVA «Lista succursali banche» e «Lista località geografiche»; conteggio "
                          "delle sedi operative al 31 dicembre (chiave banca + sede, esclusi uffici di rappresentanza) "
                          "riconciliato con la serie Istat 2022."),
    "licenseName": "CC BY 4.0", "licenseUrl": "https://www.bancaditalia.it/footer/note-legali/index.html",
}
SECTION = {"key": "credito", "label": "Banche e credito",
           "description": "Sportelli bancari aperti nei Comuni secondo l'elenco delle succursali della Banca d'Italia."}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_snapshot(root: Path | None = None) -> str:
    found = ((root or ROOT) / "data" / "source-snapshots").glob("bdi-sportelli-bancari-*.json")
    years = sorted((int(m.group(1)), p.name) for p in found if (m := re.fullmatch(r"bdi-sportelli-bancari-(20\d\d)\.json", p.name)))
    if not years:
        raise RuntimeError("Sportelli bancari: nessuno snapshot")
    return f"data/source-snapshots/{years[-1][1]}"


def validate(snapshot: dict, population_rows: list[dict]) -> None:
    if snapshot.get("qualityGate", {}).get("status") != "PASS" or snapshot["qualityGate"].get("istat2022") != bb.ISTAT_2022:
        raise RuntimeError("Sportelli bancari: snapshot senza riconciliazione Istat 2022")
    if set(snapshot["branches"]) != set(bb.TOWNS) or {r["code"] for r in population_rows} != set(bb.TOWNS):
        raise RuntimeError("Sportelli bancari: perimetro dei sette Comuni inatteso")
    years = snapshot["years"]
    for row in population_rows:
        series = dict(zip(row["series"]["years"], row["series"]["values"]))
        expected = [series.get(y + 1) for y in years]
        if expected != snapshot["population"]["towns"][row["code"]]:
            raise RuntimeError(f"Sportelli bancari: denominatori diversi dalla popolazione del catalogo ({row['town']})")
        if len(snapshot["branches"][row["code"]]) != len(years):
            raise RuntimeError(f"Sportelli bancari: serie incompleta ({row['town']})")


def apply(data: dict, registry: dict) -> dict:
    if bb.METRIC in data["metrics"]:
        raise RuntimeError(f"Metrica già presente: {bb.METRIC}")
    path = latest_snapshot()
    snapshot = load(ROOT / path)
    population_rows = data["metrics"]["population"]["rows"]
    validate(snapshot, population_rows)
    metric = bb.build_metric(snapshot, population_rows, path)
    data["metrics"][bb.METRIC] = metric
    theme = data["themes"]["economia"]
    anchor = "innovationBusinessShare"
    keys = theme["metrics"]
    keys.insert(keys.index(anchor) + 1 if anchor in keys else len(keys), bb.METRIC)
    sections = theme.setdefault("sections", [])
    at = next((i + 1 for i, s in enumerate(sections) if s["key"] == "imprenditorialita"), len(sections))
    sections.insert(at, {**SECTION, "metrics": [bb.METRIC]})
    registry.setdefault("sourceProfiles", {})[PROFILE] = PROFILE_SPEC
    for url in (bb.PAGE, bb.URL):
        registry.setdefault("sourceProfileByUrl", {})[url] = PROFILE
        registry.setdefault("sourceUrlProfiles", {})[url] = PROFILE
    registry.setdefault("metricOverrides", {})[bb.METRIC] = {"profile": PROFILE}
    registry["expectedMetricCount"] = len(data["metrics"])
    registry["expectedExternalMetricCount"] = int(registry.get("expectedExternalMetricCount", 4))
    registry["expectedInlineMetricCount"] = registry["expectedMetricCount"] - registry["expectedExternalMetricCount"]
    return metric


def main() -> None:
    data, registry = load(DATA), load(REGISTRY)
    apply(data, registry)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Sportelli bancari materializzati: {len(data['metrics'])} indicatori nel workspace")


if __name__ == "__main__":
    main()
