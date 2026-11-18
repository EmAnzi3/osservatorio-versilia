#!/usr/bin/env python3
"""Aggiunge al catalogo effettivo, in build, i due indicatori dei fabbisogni standard.

`standardNeedsSpendingGap` e `standardNeedsServiceGap` non stanno in
`data/site-data.json`: li costruisce questo passo dell'overlay di build dall'ultimo
snapshot `data/source-snapshots/opencivitas-fabbisogni-AAAA.json`, scritto da
`update_source_data.py opencivitas-needs`. Registra anche il profilo della fonte nel
registro dell'overlay, così il controllo mensile la riconosce.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import opencivitas_needs as oc

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
PROFILE = "opencivitas-annual"
PROFILE_SPEC = {
    "publisher": "SOSE — Ministero dell'Economia e delle Finanze", "frequency": "annual",
    "frequencyLabel": "Annuale (annualità dei fabbisogni standard)",
    "expectedRelease": "Nuova annualità sul portale OpenCivitas dopo l'approvazione dei fabbisogni standard",
    "acquisitionMethod": ("Download dell'open data OpenCivitas «Indicatori — Totale funzioni» e dell'anagrafica enti; "
                          "lettura di spesa storica, spesa standard e scostamento dei servizi per i sette Comuni, "
                          "riconciliati con la sonda del file; aggregati Toscana e Italia sui Comuni valutabili."),
    "licenseName": "CC BY 4.0", "licenseUrl": "https://www.opencivitas.it/portale/note-legali",
}
SECTION = {"key": "fabbisogni-standard", "label": "Fabbisogni standard",
           "description": "Spesa e servizi dei Comuni rispetto al fabbisogno standard stimato da SOSE e MEF (OpenCivitas)."}


def _enrichment(metric: str) -> dict:
    ref = oc.PAGE
    spend = metric == oc.SPENDING
    return {
        "serie_storica": {"state": "SOURCE_UNAVAILABLE", "evidence": "L'elenco open data OpenCivitas (12 pagine lette il 18 novembre 2026) contiene solo l'annualità 2023 del file «Indicatori — Totale funzioni»: le annualità precedenti non sono scaricabili nello stesso formato. La serie si allungherà con le prossime annualità.", "sourceReference": ref},
        "sesso": {"state": "NOT_APPLICABLE", "evidence": "Spesa e servizi sono del Comune come ente: la disaggregazione per sesso non ha significato.", "sourceReference": ref},
        "eta": {"state": "NOT_APPLICABLE", "evidence": "Spesa e servizi sono del Comune come ente: la disaggregazione per età non ha significato.", "sourceReference": ref},
        "assoluto_normalizzato": {"state": "AVAILABLE_MISSING", "evidence": (
            "Lo snapshot contiene spesa storica e spesa standard in euro e per abitante (Massarosa 14,4 contro 15,5 milioni nel 2023); la metrica pubblica lo scostamento percentuale."
            if spend else "OpenCivitas pubblica anche il livello dei servizi su scala 0–10 (POSIZIONE_OUTPUT_PERC_TOT), nello snapshot ma non nella metrica."), "sourceReference": ref},
        "numeratore_denominatore": {"state": "AVAILABLE_MISSING", "evidence": (
            "Spesa storica (numeratore) e spesa standard (denominatore) sono nello snapshot e il motore delle domande le restituisce, ma non sono campi strutturati della metrica pubblicata."
            if spend else "Lo scostamento dei servizi è un dato pubblicato da OpenCivitas: i servizi svolti e quelli standard per singola funzione non sono nel file «Totale funzioni»."), "sourceReference": ref},
        "frequenza_infra_annuale": {"state": "NOT_APPLICABLE", "evidence": "I fabbisogni standard si stimano per annualità: non esiste una misura infra-annuale.", "sourceReference": ref},
        "categorie_specifiche": {"state": "AVAILABLE_MISSING", "evidence": "OpenCivitas pubblica file separati per funzione (polizia locale, istruzione, sociale e asili nido, rifiuti…); la metrica usa il totale delle funzioni.", "sourceReference": ref},
    }


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_snapshot(root: Path | None = None) -> str:
    found = ((root or ROOT) / "data" / "source-snapshots").glob("opencivitas-fabbisogni-*.json")
    years = sorted((int(m.group(1)), p.name) for p in found if (m := re.fullmatch(r"opencivitas-fabbisogni-(20\d\d)\.json", p.name)))
    if not years:
        raise RuntimeError("Fabbisogni standard: nessuno snapshot")
    return f"data/source-snapshots/{years[-1][1]}"


def validate(snapshot: dict, rows: list[dict]) -> None:
    if snapshot.get("qualityGate", {}).get("status") != "PASS":
        raise RuntimeError("Fabbisogni standard: snapshot senza controllo di qualità")
    if set(snapshot["towns"]) != set(oc.TOWNS) or {r["code"] for r in rows} != set(oc.TOWNS):
        raise RuntimeError("Fabbisogni standard: perimetro dei sette Comuni inatteso")
    for code, t in snapshot["towns"].items():
        if t["username"] != oc.TOWNS[code] or t["notEvaluable"] or not t["spesaStandard"] > 0 or not t["spesaStorica"] > 0:
            raise RuntimeError(f"Fabbisogni standard: record non valido per {code}")
    for scope in ("tuscany", "italy"):
        if not snapshot["scopes"][scope]["spesaStandard"] > 0:
            raise RuntimeError(f"Fabbisogni standard: aggregato {scope} vuoto")


def apply(data: dict, registry: dict) -> dict:
    for key in oc.METRICS:
        if key in data["metrics"]:
            raise RuntimeError(f"Metrica già presente: {key}")
    path = latest_snapshot()
    snapshot = load(ROOT / path)
    rows = data["metrics"]["population"]["rows"]
    validate(snapshot, rows)
    metrics = oc.build_metrics(snapshot, rows, path)
    data["metrics"].update(metrics)
    theme = data["themes"]["bilanci"]
    keys = theme["metrics"]
    anchor = "financialDebtProfile"
    at = keys.index(anchor) + 1 if anchor in keys else len(keys)
    keys[at:at] = list(oc.METRICS)
    sections = theme.setdefault("sections", [])
    pos = next((i + 1 for i, s in enumerate(sections) if s["key"] == "equilibri"), len(sections))
    sections.insert(pos, {**SECTION, "metrics": list(oc.METRICS)})
    registry.setdefault("sourceProfiles", {})[PROFILE] = PROFILE_SPEC
    for url in (oc.PAGE, snapshot["dataUrl"]):
        registry.setdefault("sourceProfileByUrl", {})[url] = PROFILE
        registry.setdefault("sourceUrlProfiles", {})[url] = PROFILE
    for key in oc.METRICS:
        registry.setdefault("metricOverrides", {})[key] = {"profile": PROFILE, "enrichmentDimensions": _enrichment(key)}
    registry["expectedMetricCount"] = len(data["metrics"])
    registry["expectedExternalMetricCount"] = int(registry.get("expectedExternalMetricCount", 4))
    registry["expectedInlineMetricCount"] = registry["expectedMetricCount"] - registry["expectedExternalMetricCount"]
    return metrics


def main() -> None:
    data, registry = load(DATA), load(REGISTRY)
    apply(data, registry)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fabbisogni standard materializzati: {len(data['metrics'])} indicatori nel workspace")


if __name__ == "__main__":
    main()
