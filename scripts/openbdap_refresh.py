#!/usr/bin/env python3
"""Controllo e aggiornamento dei rendiconti OpenBDAP già pubblicati (Comuni ritrasmessi).

Il controllo mensile verificava solo la raggiungibilità del portale OpenBDAP; un Comune che
ritrasmette il rendiconto cambia però l'archivio regionale senza cambiare la pagina. Questo modulo
riscarica gli archivi toscani «Schemi di bilancio» e «Piano degli indicatori» degli anni pubblicati,
ricalcola per i sette Comuni gli stessi campi dello snapshot `bilanci-v1.6.0.json` con la stessa
funzione (`build_bilanci_snapshot.build_year`) e confronta campo per campo.

Le differenze vengono applicate allo snapshot (campi grezzi e valori per indicatore) e al catalogo
(valore corrente, serie e aggregato Versilia degli indicatori che dipendono dal campo cambiato), con
le stesse formule della pubblicazione (`update_bilanci_v160`). Ogni modifica è registrata nello
snapshot (`refreshLog`) con il valore precedente, il nuovo valore e l'impronta dell'archivio.
"""
from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import date
from typing import Any, Callable

import build_bilanci_snapshot as base

SNAPSHOT = "data/source-snapshots/bilanci-v1.6.0.json"
FIRST, LAST = 2019, 2025
KINDS = {"schemi": "Schemi di bilancio", "indicatori": "Piano degli indicatori"}


class RefreshError(RuntimeError):
    pass


def archive_path(year: int, kind: str) -> str:
    return f"/Datasets_FET/Rendiconto/{year}/{year}_Rendiconto - {KINDS[kind]}_TOSCANA.zip"


def fetch_archives(fetch: Callable[[str], bytes]) -> tuple[dict[str, tuple[bytes, str]], dict[str, dict[str, Any]]]:
    archives, sources = {}, {}
    for year in range(FIRST, LAST + 1):
        for kind in KINDS:
            url = base.BASE + base.quote(archive_path(year, kind), safe="/:_-.")
            raw = fetch(url)
            if not raw.startswith(b"PK"):
                raise RefreshError(f"{year} {kind}: risposta non ZIP")
            zipfile.ZipFile(io.BytesIO(raw)).testzip()
            archives[f"{year}-{kind}"] = (raw, url)
            sources[f"{year}-{kind}"] = {"url": url, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    return archives, sources


def differences(snapshot: dict[str, Any], fresh: dict[int, dict[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    out = []
    for year, towns in fresh.items():
        for town, values in towns.items():
            old = snapshot["raw"][town]["years"][str(year)]
            for field, value in values.items():
                if field == "population_at_1_january":
                    continue  # popolazione dal catalogo, non dall'archivio
                if field == "mission_commitments":
                    for code in sorted(set(value) | set(old.get(field, {}))):
                        a, b = old.get(field, {}).get(code, 0.0), value.get(code, 0.0)
                        if abs(a - b) > 0.005:
                            out.append({"year": year, "town": town, "field": f"{field}.{code}", "old": a, "new": b})
                elif field in old and abs(float(old[field]) - float(value)) > 0.005:
                    out.append({"year": year, "town": town, "field": field, "old": old[field], "new": value})
    return out


def apply(snapshot: dict[str, Any], site: dict[str, Any], diffs: list[dict[str, Any]], sources: dict[str, Any]) -> list[str]:
    import update_bilanci_v160 as pub
    touched: set[tuple[int, str]] = set()
    for d in diffs:
        old = snapshot["raw"][d["town"]]["years"][str(d["year"])]
        if d["field"].startswith("mission_commitments."):
            old["mission_commitments"][d["field"].split(".", 1)[1]] = d["new"]
        else:
            old[d["field"]] = d["new"]
        touched.add((d["year"], d["town"]))
    changed_metrics: set[str] = set()
    for year, town in sorted(touched):
        values = base.compute_values(snapshot["raw"][town]["years"][str(year)])
        for key, value in values.items():
            entry = snapshot["metrics"].get(key)
            if not entry or str(year) not in entry["values"].get(town, {}):
                continue
            if abs(entry["values"][town][str(year)] - value) > 1e-12:
                entry["values"][town][str(year)] = value
                changed_metrics.add(key)
                metric = site["metrics"][key]
                row = next(r for r in metric["rows"] if r["town"] == town)
                years = [int(y) for y in row["series"]["years"]] if row.get("series") else []
                if year in years:
                    row["series"]["values"][years.index(year)] = value
                if str(year) == str(metric["meta"]["year"]):
                    row["value"] = value
                    if "benchmarkValue" in row:
                        row["benchmarkValue"] = value
                    row["formatted"] = pub.format_currency(value) if metric["meta"]["unit"] == "currency" else pub.format_percent(value)
    for key in sorted(changed_metrics):
        metric = site["metrics"][key]
        if str(metric["meta"]["year"]) == str(LAST):
            metric["aggregate"]["value"] = pub.aggregate(snapshot, key)
    snapshot.setdefault("refreshLog", []).append({"date": date.today().isoformat(), "differences": diffs, "metrics": sorted(changed_metrics),
                                                   "sources": sources})
    return sorted(changed_metrics)


def run(fetch: Callable[[str], bytes], snapshot: dict[str, Any], site: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    archives, sources = fetch_archives(fetch)
    populations = base.population_lookup(site)
    fresh = {}
    for year in range(FIRST, LAST + 1):
        raw, _ = base.build_year(year, populations, archives)
        missing = set(snapshot["raw"]) - set(raw)
        if missing:
            raise RefreshError(f"{year}: Comuni assenti dall'archivio {sorted(missing)}")
        fresh[year] = raw
    diffs = differences(snapshot, fresh)
    changed = apply(snapshot, site, diffs, sources) if diffs else []
    return diffs, changed, sources
