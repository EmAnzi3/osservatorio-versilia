#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data"/"site-data.json"
SNAP=ROOT/"data"/"source-snapshots"/"a3-istat-demography-benchmark-2026.json"
SNAP_REF="data/source-snapshots/a3-istat-demography-benchmark-2026.json"
RCS_SNAP=ROOT/"data"/"source-snapshots"/"istat-rcs-demography-2025.json"

TARGETS={
    "population":{
        "year":"2026","unit":"number",
        "sourceUrl":"https://demo.istat.it/",
        "formula":"Valore pubblicato dalla fonte, senza trasformazione ulteriore.",
        "source":"Istat — popolazione residente",
        "note":"Toscana e Italia sono aggregati dal perimetro comunale Istat coerente con il dato corrente 2026.",
    },
    "populationChange":{
        "year":"2019–2026","unit":"percent",
        "sourceUrl":"https://demo.istat.it/",
        "formula":"((residenti anno finale - residenti 2019) / residenti 2019) × 100",
        "source":"Istat — popolazione residente",
        "note":"Variazione 2019–2026 ricalcolata sui residenti aggregati Toscana/Italia, non come media delle variazioni comunali.",
    },
    "ageDistribution":{
        "year":"2026","unit":"percent",
        "sourceUrl":"https://demo.istat.it/app/?a=2025&i=POS",
        "formula":"residenti della fascia / popolazione residente totale × 100; età media = somma(età × residenti alla singola età) / residenti totali",
        "source":"Istat — popolazione residente per età (POSAS)",
        "part":"20–34 anni",
        "note":"Benchmark riferito alla voce predefinita «20–34 anni». Le quote sono calcolate sui conteggi POSAS aggregati Toscana/Italia; Età=999 è solo controllo del totale.",
    },
    "dependencyIndices":{
        "year":"2026","unit":"per100",
        "sourceUrl":"https://demo.istat.it/",
        "formula":"dipendenza strutturale = (0–14 + 65+) / 15–64 × 100; dipendenza anziani = 65+ / 15–64 × 100. Il risultato si legge come persone nella fascia considerata ogni 100 persone di 15–64 anni.",
        "source":"Istat — popolazione residente per età e sesso (POSAS)",
        "part":"Indice di dipendenza strutturale",
        "note":"Benchmark riferito alla voce predefinita «Indice di dipendenza strutturale», ricalcolata sui conteggi aggregati per età.",
    },
    "naturalDemographicDynamics":{
        "year":"2025","unit":"per1000",
        "sourceUrl":"https://demo.istat.it/",
        "formula":"tasso = eventi dell’anno / media tra popolazione al 1° gennaio e popolazione al 31 dicembre × 1.000; saldo naturale = nati vivi − morti",
        "source":"Istat — bilancio demografico comunale (P02)",
        "part":"Saldo naturale",
        "note":"Benchmark riferito alla voce predefinita «Saldo naturale». Il tasso è ricalcolato su eventi e popolazione media aggregati Toscana/Italia.",
    },
    "foreignResidents":{
        "year":"2025","unit":"percent",
        "sourceUrl":"https://demo.istat.it/",
        "formula":"residenti di cittadinanza non italiana / popolazione residente totale × 100",
        "source":"Istat RCS — popolazione residente per cittadinanza",
        "note":"Quota di residenti con cittadinanza non italiana al 1° gennaio 2025. Toscana e Italia sono ricalcolate sui conteggi RCS aggregati; il benchmark è pubblicato solo dopo riconciliazione 7/7 con i dati comunali pubblici e controllo della popolazione RCS con P02.",
    },
}


def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def norm(value:Any)->str:
    return re.sub(r"\s+"," ",str(value or "").strip().lower())


def finite(value:Any)->bool:
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(float(value))


def reconcile_snapshot(snap:dict[str,Any])->None:
    if (snap.get("qualityGate") or {}).get("status")!="PASS":
        raise RuntimeError("Snapshot demografia senza qualityGate PASS")
    b=snap.get("benchmarks") or {}
    c=snap.get("components") or {}
    for scope in ("tuscany","italy"):
        pop=float((b["population"] or {})[scope])
        age=(c[scope] or {})["ageDistribution"]
        if not math.isclose(pop,float(age["population"]),rel_tol=0.0,abs_tol=0.1):
            raise RuntimeError(f"{scope}: popolazione non riconciliata con POSAS")
        if not math.isclose(sum(float(v) for v in age["bands"].values()),pop,rel_tol=0.0,abs_tol=0.1):
            raise RuntimeError(f"{scope}: classi POSAS non esaustive")
        ch=(c[scope] or {})["populationChange"]
        expected=(float(ch["end2026"])-float(ch["start2019"]))/float(ch["start2019"])*100.0
        if not math.isclose(expected,float(b["populationChange"][scope]),rel_tol=0.0,abs_tol=1e-12):
            raise RuntimeError(f"{scope}: populationChange non riconciliato")
        nat=(c[scope] or {})["naturalDemographicDynamics"]
        expected_nat=float(nat["naturalBalance"])/float(nat["meanPopulation"])*1000.0
        if not math.isclose(expected_nat,float(b["naturalDemographicDynamics"][scope]),rel_tol=0.0,abs_tol=1e-12):
            raise RuntimeError(f"{scope}: saldo naturale non riconciliato")
        dep=(float(age["age0_14"])+float(age["age65plus"]))/float(age["age15_64"])*100.0
        if not math.isclose(dep,float(b["dependencyIndices"][scope]),rel_tol=0.0,abs_tol=1e-12):
            raise RuntimeError(f"{scope}: dependencyIndices non riconciliato")
        age2034=float(age["bands"]["20-34"])/pop*100.0
        if not math.isclose(age2034,float(b["ageDistribution"][scope]),rel_tol=0.0,abs_tol=1e-12):
            raise RuntimeError(f"{scope}: ageDistribution non riconciliato")


def reconcile_foreign_residents(site:dict[str,Any],snap:dict[str,Any],rcs_detail:dict[str,Any])->None:
    metric=(site.get("metrics") or {}).get("foreignResidents")
    if not isinstance(metric,dict):
        raise RuntimeError("foreignResidents: metrica pubblica mancante")
    rows=metric.get("rows") or []
    towns=rcs_detail.get("towns") or {}
    if not isinstance(towns,dict) or len(towns)!=7:
        raise RuntimeError("foreignResidents: snapshot RCS non 7/7")
    public_by_town={str(row.get("town") or ""):row for row in rows if isinstance(row,dict)}
    if set(public_by_town)!=set(towns):
        raise RuntimeError("foreignResidents: perimetro comunale pubblico non riconciliato con RCS")
    for town,detail in towns.items():
        row=public_by_town[town]
        count=int(row.get("count"))
        population=float(row.get("population"))
        value=float(row.get("value"))
        if count!=int(detail.get("citizenshipTotal")):
            raise RuntimeError(f"{town}: residenti stranieri pubblici non riconciliati con RCS 2025")
        expected=count/population*100.0
        if not math.isclose(expected,value,rel_tol=0.0,abs_tol=1e-12):
            raise RuntimeError(f"{town}: quota residenti stranieri pubblica non riconciliata con conteggio/popolazione")
    gate=snap.get("rcs") or {}
    if gate.get("validation")!="7/7 public rows reconciled; population cross-check with P02 1/1/2025":
        raise RuntimeError("foreignResidents: snapshot benchmark senza gate RCS/P02")
    spec=(snap.get("benchmarks") or {}).get("foreignResidents") or {}
    for scope in ("tuscany","italy"):
        scope_data=(gate.get("scopes") or {}).get(scope) or {}
        foreign=float(scope_data.get("foreign"))
        population=float(scope_data.get("population"))
        expected=foreign/population*100.0
        if not math.isclose(expected,float(spec.get(scope)),rel_tol=0.0,abs_tol=1e-12):
            raise RuntimeError(f"foreignResidents {scope}: benchmark non riconciliato")


def main()->None:
    site=load(SITE)
    snap=load(SNAP)
    reconcile_snapshot(snap)
    rcs_detail=load(RCS_SNAP)
    reconcile_foreign_residents(site,snap,rcs_detail)
    metrics=site.get("metrics")
    if not isinstance(metrics,dict):
        raise RuntimeError("Catalogo senza metrics")
    benchmarks=snap.get("benchmarks") or {}
    updated=0

    for metric_id,cfg in TARGETS.items():
        metric=metrics.get(metric_id)
        if not isinstance(metric,dict):
            raise RuntimeError(f"{metric_id}: metrica mancante")
        meta=metric.get("meta")
        if not isinstance(meta,dict):
            raise RuntimeError(f"{metric_id}: meta mancante")
        if str(meta.get("year"))!=cfg["year"] or str(meta.get("unit"))!=cfg["unit"]:
            raise RuntimeError(
                f"{metric_id}: contratto inatteso anno={meta.get('year')} unità={meta.get('unit')}"
            )
        if str(metric.get("sourceUrl") or "")!=cfg["sourceUrl"]:
            raise RuntimeError(f"{metric_id}: sourceUrl inatteso {metric.get('sourceUrl')}")
        method=metric.get("method")
        if not isinstance(method,dict) or norm(method.get("formula"))!=norm(cfg["formula"]):
            raise RuntimeError(f"{metric_id}: formula pubblica non allineata")

        spec=benchmarks.get(metric_id)
        if not isinstance(spec,dict):
            raise RuntimeError(f"{metric_id}: benchmark assente dallo snapshot")
        if str(spec.get("year"))!=cfg["year"] or str(spec.get("unit"))!=cfg["unit"]:
            raise RuntimeError(f"{metric_id}: anno/unità snapshot non allineati")
        tuscany=spec.get("tuscany"); italy=spec.get("italy")
        if not finite(tuscany) or not finite(italy):
            raise RuntimeError(f"{metric_id}: Toscana/Italia non numerici")

        part=cfg.get("part")
        if part:
            parts=[str(p.get("label") or "") for p in ((metric.get("aggregate") or {}).get("parts") or []) if isinstance(p,dict)]
            if part not in parts:
                raise RuntimeError(f"{metric_id}: componente benchmark {part!r} non presente tra {parts}")

        meta["benchmark"]={
            "year":cfg["year"],
            "tuscany":tuscany,
            "italy":italy,
            "source":cfg["source"],
            "url":cfg["sourceUrl"],
            "sourceSnapshot":SNAP_REF,
            "note":cfg["note"],
        }
        updated+=1

    SITE.write_text(json.dumps(site,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"A3 benchmark demografia: {updated} metriche Toscana/Italia materializzate con contratto POSAS/P02 riconciliato.")


if __name__=="__main__":
    main()
