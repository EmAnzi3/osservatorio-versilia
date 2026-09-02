#!/usr/bin/env python3
"""Contratto dati/metodo per Demanio marittimo v1.27.0 e release successive."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text(encoding="utf-8"))
def rowmap(metric): return {r["town"]:r for r in metric["rows"]}
def version_tuple(value):
    return tuple(int(part) for part in str(value).lstrip("v").split(".")[:3])

def main():
    site=load(Path("data/site-data.json"))
    snap=load(Path("data/source-snapshots/demanio-marittimo-v127.json"))
    reg=load(Path("data/source-registry.json"))
    assert version_tuple(site["version"]) >= (1,27,0)
    assert len(site["metrics"]) >= 177
    assert reg["expectedMetricCount"] >= 177 and reg["expectedInlineMetricCount"] >= 173 and reg["expectedExternalMetricCount"]==4
    keys=("maritimeConcessions","maritimeConcessionFeesDue")
    coast=next(s for s in site["themes"]["ambiente"]["sections"] if s["key"]=="costa-mare")
    assert coast["metrics"][-2:]==list(keys)
    for k in keys:
        m=site["metrics"][k]
        assert m["meta"]["theme"]=="ambiente"
        assert m["meta"]["detailGroup"]=="coast"
        assert m["meta"]["compositeType"]=="securityMeasures"
        assert m["meta"]["sourceMeta"]["snapshot"]=="data/source-snapshots/demanio-marittimo-v127.json"
        assert m["method"]["coverage"]=="4/4 Comuni costieri + 3 n.a."
        assert reg["metricOverrides"][k]["profile"]=="mit-sid-demanio-irregular"
    counts={"Camaiore":130,"Forte dei Marmi":187,"Pietrasanta":123,"Viareggio":359}
    fees={"Camaiore":852515.21,"Forte dei Marmi":1449307.39,"Pietrasanta":1552876.15,"Viareggio":2669422.99}
    tr={"Camaiore":124,"Forte dei Marmi":161,"Pietrasanta":116,"Viareggio":174}
    cr=rowmap(site["metrics"][keys[0]]); fr=rowmap(site["metrics"][keys[1]])
    for town,value in counts.items():
        assert cr[town]["value"]==value
        assert next(p for p in cr[town]["parts"] if p["key"]=="tourist")["value"]==tr[town]
        assert abs(fr[town]["value"]-fees[town])<0.001
    for town in ("Massarosa","Seravezza","Stazzema"):
        assert cr[town]["value"] is None and cr[town]["notApplicable"] is True and cr[town]["formatted"]=="n.a."
        assert fr[town]["value"] is None and fr[town]["notApplicable"] is True and fr[town]["formatted"]=="n.a."
    assert site["metrics"][keys[0]]["aggregate"]["value"]==799
    assert next(p for p in site["metrics"][keys[0]]["aggregate"]["parts"] if p["key"]=="tourist")["value"]==575
    assert abs(site["metrics"][keys[1]]["aggregate"]["value"]-6524121.74)<0.001
    assert abs(next(p for p in site["metrics"][keys[1]]["aggregate"]["parts"] if p["key"]=="tourist")["value"]-5469023.68)<0.001
    assert snap["quality"]["nationalCsvRows"]==29248 and snap["quality"]["nationalDistinctIdconc"]==29242
    assert snap["quality"]["perfectDuplicateRows"]==6 and snap["quality"]["allRowsStatus"]=="Vigente"
    assert snap["quality"]["polygonCoverage"]["localSharePercent"]["Forte dei Marmi"]==59.9
    assert snap["quality"]["territorialAssignment"]["publishedDistinctIdconc"]==799
    assert snap["quality"]["territorialAssignment"]["municipalAuthorityCounts"]=={"Camaiore":129,"Forte dei Marmi":185,"Pietrasanta":122,"Viareggio":181}
    assert snap["source"]["files"]["concessioni-epsg4326.csv"]["sha256"]=="66b492555b29147421693080555f7d29eb5f7469f2c3aa5bffe00aa5d27ad28d"
    assert "non un incasso" in site["metrics"][keys[1]]["meta"]["description"].lower()
    assert "stabilimento balneare" in site["metrics"][keys[0]]["method"]["caveat"].lower()
    assert not any(k in site["metrics"] for k in ("concessionedArea","concessionedCoastMetres","concessionedCoastShare","bathingEstablishments"))
    print("Demanio marittimo v1.27.0+: 2 card e gate metodologici verificati.")

if __name__=="__main__": main()
