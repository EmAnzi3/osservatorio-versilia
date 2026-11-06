#!/usr/bin/env python3
"""Contratto: ogni indicatore ha (o avrà, in un lotto dichiarato) una verifica mensile del periodo."""
from __future__ import annotations

import copy
import io
import json
import zipfile
from pathlib import Path

import monthly_data_check_status as status
import release_period_probes as probes

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data" / "source-monitor-state.json"
TOWNS = probes.TOWN_CODES
HEADER = "id_indicatore,anno,codice_geografia,geografia,den,num,misura_grezza,misura_standardizzata,liminf,limsup,sesso,strato1,strato2"


def coverage_contract() -> None:
    contract = probes.load_coverage()
    metrics = contract["metrics"]
    state_keys = set(json.loads(STATE.read_text(encoding="utf-8"))["metrics"])
    assert set(metrics) == state_keys, f"indicatori senza voce di copertura: {sorted(state_keys ^ set(metrics))[:10]}"
    pending = [k for k, v in metrics.items() if "pendingLot" in v]
    assert len(pending) <= contract["maxPending"], "la copertura non può peggiorare"
    assert len(pending) == contract["maxPending"], "aggiornare maxPending al nuovo valore più basso"
    for key, spec in metrics.items():
        assert ("probe" in spec) != ("pendingLot" in spec), key
        if "pendingLot" in spec:
            assert isinstance(spec["pendingLot"], int) and 2 <= spec["pendingLot"] <= 6, key
            continue
        assert spec["probe"] in probes.PROBES, key
        if spec["probe"] == "ars_export":
            assert isinstance(spec["indicatorId"], int), key
            assert spec["measurement"] in {"raw", "standardized"}, key
            assert spec["strato1"] and all(isinstance(s, str) for s in spec["strato1"]), key
        if spec["probe"] == "demo_istat":
            assert spec["measure"] in probes.DEMO_DATASET, key
        if spec["probe"] == "rgs_conto_annuale":
            assert spec["measure"] in probes.RGS_FILES_BY_MEASURE, key
        if spec["probe"] == "openbdap_rendiconto":
            assert spec["family"] in {"v139", "v160", "mission03", "debt_d1"}, key


def payload(values: dict[str, dict[str, float]], indicator: int = 9999) -> bytes:
    lines = [HEADER]
    for period, by_geo in values.items():
        for code, value in by_geo.items():
            text = f"{value}".replace(".", ",")
            lines.append(f'{indicator},{period},{code.lstrip("0")},x,1,1,"{text}","{text}",0,0,totale,,')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("dati.csv", "\n".join(lines) + "\n")
    return buffer.getvalue()


def metric(period: str, current: float, history: dict[str, float]) -> dict:
    years = list(history)
    return {
        "meta": {"year": period},
        "rows": [{"code": c, "value": current, "series": {"years": years, "values": [history[y] for y in years]}} for c in TOWNS],
        "aggregate": {"value": current},
    }


def probe_cases() -> None:
    spec = {"probe": "ars_export", "indicatorId": 9999, "strato1": ["", "totale"], "measurement": "standardized"}
    geos = list(TOWNS) + [probes.VERSILIA_ARS]
    base = {"2023": {g: 10.0 for g in geos}, "2024": {g: 11.004 for g in geos}}
    published = metric("2024", 11.0, {"2023": 10.0, "2024": 11.0})

    def run(values, m=published):
        return probes.probe_metric("demo", m, spec, fetch=lambda url: payload(values))

    same = run(base)
    assert same["status"] == "current" and same["reason"] == "match", same
    newer = run({**base, "2025": {g: 12.0 for g in geos}})
    assert newer["status"] == "release_detected" and newer["observedLatestPeriod"] == "2025", newer
    changed = copy.deepcopy(base)
    changed["2024"]["046018"] = 11.5
    differ = run(changed)
    assert differ["status"] == "verification_required" and differ["reason"] == "same_period_values_differ", differ
    revised = copy.deepcopy(base)
    revised["2023"]["046030"] = 10.7
    history = run(revised)
    assert history["status"] == "verification_required" and history["reason"] == "history_revised", history
    assert history["historyRevisions"][0] == {"geography": "046030", "period": "2023", "published": 10.0, "observed": 10.7}
    missing = copy.deepcopy(base)
    del missing["2024"]["046005"]
    del missing["2023"]["046005"]
    broken = run(missing)
    assert broken["reason"] == "structure_changed" and broken["manualAction"]["steps"], broken
    window = metric("2013–2022", 11.0, {"2013-2022": 11.0})
    rolled = probes.probe_metric("demo", window, spec, fetch=lambda url: payload({"2013-2022": {g: 11.0 for g in geos}, "2014-2023": {g: 12.0 for g in geos}}))
    assert rolled["status"] == "release_detected" and rolled["observedLatestPeriod"] == "2014-2023", rolled

    def offline(url):
        raise probes.ProbeError("source_unreachable", "timeout")

    down = probes.probe_metric("demo", published, spec, fetch=offline)
    action = down["manualAction"]
    assert down["status"] == "verification_required" and down["publishedPeriod"] == "2024"
    assert action["url"].endswith("indicatore=9999") and any("--file" in step for step in action["steps"]), action

    # Lo stato operativo riflette il probe, non la sola raggiungibilità.
    metrics = {"a": {"status": "source_checked", "releaseEvidence": {"old": 1}}, "b": {"status": "source_checked"}, "c": {"status": "source_checked"}}
    status.apply_release_probe_results(metrics, {"a": same, "b": newer, "c": down}, "2026-12-05T00:00:00+00:00")
    assert metrics["a"]["status"] == "current" and "releaseEvidence" not in metrics["a"]
    assert metrics["b"]["status"] == "release_detected" and metrics["b"]["releaseEvidence"]["verdict"] == "new_period"
    assert metrics["c"]["status"] == "verification_required" and metrics["c"]["manualAction"]["metric"] == "demo"
    local = probes.local_fetcher([])
    assert local(probes.openbdap_url(2026, "schemi")) == b"", "rendiconto successivo non allegato = non pubblicato"
    try:
        local(probes.ARS_EXPORT.format(id=1))
        raise AssertionError("file ARS mancante non segnalato")
    except probes.ProbeError as error:
        assert error.reason == "source_unreachable"
    lines = "\n".join(probes.report_lines({"demo": down}, probes.load_coverage()))
    assert "### Azioni manuali" in lines and "--file" in lines


def main() -> None:
    coverage_contract()
    probe_cases()
    contract = probes.load_coverage()
    covered = sum(1 for v in contract["metrics"].values() if "probe" in v)
    print(f"Verifica mensile dei periodi: {covered}/{len(contract['metrics'])} indicatori coperti, {contract['maxPending']} nei lotti successivi; casi current/new/differ/revised/structure/unreachable PASS")


if __name__ == "__main__":
    main()
