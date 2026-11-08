#!/usr/bin/env python3
"""Contratto: ogni indicatore ha una verifica mensile del periodo alla fonte."""
from __future__ import annotations

import copy
import datetime
import re
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
        if spec["probe"] == "source_period":
            assert spec["checks"] and all(name in contract["sourceChecks"] for name in spec["checks"]), key
    used = {name for spec in metrics.values() for name in spec.get("checks", [])}
    assert used == set(contract["sourceChecks"]), f"regole non usate: {sorted(set(contract['sourceChecks']) - used)}"
    for name, check in contract["sourceChecks"].items():
        mode = check.get("mode", "latest")
        assert mode in {"latest", "next", "absent", "snapshot"}, name
        assert check["url"].split(" ")[-1].startswith("https://") and check.get("hint"), name
        assert check.get("kind", "year") in {"year", "month", "semester", "date"}, name
        if mode in {"latest", "absent"}:
            assert re.compile(check["pattern"]).groups >= 1, name
        if mode == "next":
            assert "{next}" in check["url"] and all("{next}" in u for u in check.get("alternatives", [])), name
        if mode == "snapshot":
            assert check["expect"] and 0 < int(check["maxAgeDays"]) <= 92, name
        if check.get("kind") == "date" and mode == "latest":
            assert 0 <= int(check.get("graceDays", 0)) <= 92, name


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


def period_cases() -> None:
    """Verifica del solo periodo: pagine, edizioni successive, istantanee di fonti continue."""
    probes.SOURCE_CHECKS.clear()
    probes.SOURCE_CHECKS.update({
        "page": {"url": "https://x.test/p", "pattern": r"Periodo di riferimento: Anno (20\d\d)", "hint": "h"},
        "next": {"mode": "next", "url": "https://x.test/anno-{next}/", "confirm": True, "html": True, "hint": "h"},
        "feed": {"mode": "snapshot", "url": "https://x.test/api", "expect": "cod_istat", "maxAgeDays": 60, "hint": "h"},
        "daily": {"url": "https://x.test/d", "kind": "date", "graceDays": 30, "pattern": r"Elenco del (\d\d/\d\d/20\d\d)", "hint": "h"},
        "semester": {"url": "https://x.test/s", "kind": "semester", "pattern": r"(\d\d/\d\d/20\d\d)", "hint": "h"},
        "absent": {"mode": "absent", "url": "https://x.test/sdmx?startPeriod={next}", "pattern": r'TIME_PERIOD="(20\d\d)', "text": "raw", "hint": "h"},
    })

    def site(pages):
        def fetch(url):
            url = url.replace("PEEK ", "")
            if url not in pages:
                raise probes.ProbeError("not_found", url)
            if isinstance(pages[url], Exception):
                raise pages[url]
            return pages[url]
        return fetch

    def run(check, year, pages):
        return probes.probe_metric("m", {"meta": {"year": year}}, {"probe": "source_period", "checks": [check]}, fetch=site(pages))

    page = lambda text: f"<html><body><p>{text}</p></body></html>".encode()
    assert run("page", "2024", {"https://x.test/p": page("Periodo di riferimento: Anno 2024")})["status"] == "current"
    new = run("page", "2024", {"https://x.test/p": page("Periodo di riferimento: Anno 2025 · Anno 2024")})
    assert new["status"] == "release_detected" and new["observedLatestPeriod"] == "2025" and new["scope"] == "period", new
    assert run("page", "2024", {"https://x.test/p": page("Periodo di riferimento: Anno 2023")})["reason"] == "source_period_older"
    moved = run("page", "2024", {"https://x.test/p": page("pagina rifatta")})
    assert moved["reason"] == "structure_changed" and moved["manualAction"]["urls"] == ["https://x.test/p"], moved
    assert not any("--file" in step for step in moved["manualAction"]["steps"]), "nessun file da allegare per una verifica di periodo"
    down = run("page", "2024", {"https://x.test/p": probes.ProbeError("source_unreachable", "timeout")})
    assert down["status"] == "verification_required" and down["reason"] == "source_unreachable"
    edition = {"https://x.test/anno-2022/": page("edizione 2022")}
    assert run("next", "2022", edition)["status"] == "current"
    assert run("next", "2022", {**edition, "https://x.test/anno-2023/": page("edizione 2023")})["status"] == "release_detected"
    assert run("next", "2022", {})["reason"] == "structure_changed", "edizione pubblicata sparita = indirizzo da rivedere"
    probes.TODAY = lambda: datetime.date(2026, 11, 8)
    feed = {"https://x.test/api": b'{"data":[{"cod_istat":"046033"}]}'}
    assert run("feed", "5 novembre 2026", feed)["status"] == "current"
    assert run("feed", "2026-08-01", feed)["status"] == "release_detected"
    assert run("feed", "5 novembre 2026", {"https://x.test/api": b"{}"})["reason"] == "structure_changed"
    assert run("daily", "2026-10-11", {"https://x.test/d": page("Elenco del 08/11/2026")})["status"] == "current", "entro la tolleranza"
    assert run("daily", "2026-09-01", {"https://x.test/d": page("Elenco del 08/11/2026")})["status"] == "release_detected"
    assert run("semester", "2° semestre 2025", {"https://x.test/s": page("prelievo del 12/12/2025")})["status"] == "current"
    assert run("semester", "2° semestre 2025", {"https://x.test/s": page("prelievo del 03/02/2026")})["status"] == "release_detected"
    assert run("absent", "2018", {})["status"] == "current", "nessun dato dopo il periodo pubblicato"
    assert run("absent", "2018", {"https://x.test/sdmx?startPeriod=2019": b'<Obs TIME_PERIOD="2020"/>'})["status"] == "release_detected"
    probes.SOURCE_CHECKS.clear()
    assert probes.parse_period("settembre 8, 2026", "date") == (2026, 9, 8)
    assert probes.parse_period("agosto 2026", "month") == (2026, 8)
    assert probes.parse_period("a.s. 2024/25", "year") == (2024,)


def zipped(text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("dati.csv", text)
    return buffer.getvalue()


def demo_cases() -> None:
    metric = {"rows": [{"code": "046018", "surfaceKm2": 10.0}]}
    posas = "Popolazione residente al 1 gennaio\nCodice comune;Comune;Età;Totale maschi;Totale femmine;Totale\n"
    posas += "46018;Massarosa;5;3;2;5\n046018;Massarosa;40;10;10;20\n046018;Massarosa;70;4;6;10\n046018;Massarosa;999;17;18;35\n"
    assert probes.demo_values("population", zipped(posas), metric) == {"046018": 35}, "la riga 999 (totale) non va sommata alle età"
    assert probes.demo_values("old_age", zipped(posas), metric) == {"046018": 200.0}
    broken = posas.replace(";999;17;18;35", ";999;17;18;36")
    try:
        probes.demo_values("population", zipped(broken), metric)
        raise AssertionError("totale POSAS incoerente non segnalato")
    except probes.ProbeError as error:
        assert error.reason == "structure_changed"
    rcs = "Codice Istat;Comune;Codice stato di cittadinanza;Stato di cittadinanza;Maschi;Femmine;Totale\n"
    rcs += "046018;Massarosa;100;Italia;45;45;90\n046018;Massarosa;235;Romania;5;5;10\n046;Lucca;235;Romania;50;50;100\n"
    assert probes.demo_values("foreign_share", zipped(rcs), metric) == {"046018": 10.0}, "gli italiani non sono stranieri"


def main() -> None:
    coverage_contract()
    probe_cases()
    period_cases()
    demo_cases()
    contract = probes.load_coverage()
    covered = sum(1 for v in contract["metrics"].values() if "probe" in v)
    print(f"Verifica mensile dei periodi: {covered}/{len(contract['metrics'])} indicatori coperti, {contract['maxPending']} nei lotti successivi; casi current/new/differ/revised/structure/unreachable e verifiche di periodo PASS")


if __name__ == "__main__":
    main()
