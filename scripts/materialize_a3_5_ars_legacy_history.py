#!/usr/bin/env python3
"""A3.5 lotto 7: serie storiche ARS legacy da snapshot ufficiale versionato."""
from __future__ import annotations
import json, math
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
SITE_PATH=ROOT/"data"/"site-data.json"
SNAPSHOT_PATH=ROOT/"data"/"source-snapshots"/"ars-a3-5-legacy-history.json"
SOURCE_SNAPSHOT="data/source-snapshots/ars-a3-5-legacy-history.json"
TARGET_METRICS=("chronicTotal","dementia","diabetes","elderlyHomeCare","emergencyAccess","hospitalizedAll","mortalityAll")

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise RuntimeError(f"JSON non-oggetto: {path}")
    return value

def save(path:Path,value:dict[str,Any])->None:
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def _norm_period(value:Any)->str:
    return str(value or "").strip().replace("–","-").replace("—","-")

def _rows_by_town(metric:dict[str,Any],metric_id:str)->dict[str,dict[str,Any]]:
    rows=metric.get("rows")
    if not isinstance(rows,list): raise RuntimeError(f"{metric_id}: rows mancanti")
    result={str(row["town"]):row for row in rows if isinstance(row,dict) and row.get("town")}
    if len(result)!=7: raise RuntimeError(f"{metric_id}: perimetro comunale atteso 7/7")
    return result

def _assert_close(actual:Any,expected:Any,label:str)->None:
    if not math.isclose(float(actual),float(expected),rel_tol=0.0,abs_tol=0.055):
        raise RuntimeError(f"{label}: {actual} != {expected}")

def apply_enrichment(site:dict[str,Any],snapshot:dict[str,Any])->dict[str,int]:
    metrics=site.get("metrics"); indicators=snapshot.get("indicators")
    if not isinstance(metrics,dict) or not isinstance(indicators,dict):
        raise RuntimeError("Catalogo o snapshot ARS non valido")
    missing=sorted(set(TARGET_METRICS)-set(metrics))
    if missing: raise RuntimeError(f"Metriche ARS lotto 7 mancanti: {missing}")
    rows_enriched=0
    for metric_id in TARGET_METRICS:
        metric=metrics[metric_id]; source=indicators.get(metric_id)
        if not isinstance(source,dict): raise RuntimeError(f"{metric_id}: snapshot ARS mancante")
        periods=source.get("periods"); values=source.get("values")
        if not isinstance(periods,list) or len(periods)<2 or not isinstance(values,dict):
            raise RuntimeError(f"{metric_id}: storico ARS non valido")
        if len(set(periods))!=len(periods): raise RuntimeError(f"{metric_id}: periodi ARS duplicati")
        meta=metric.get("meta") if isinstance(metric.get("meta"),dict) else {}
        expected_period=_norm_period(meta.get("year"))
        if _norm_period(periods[-1])!=expected_period:
            raise RuntimeError(f"{metric_id}: ultimo periodo snapshot {periods[-1]} != catalogo {expected_period}")
        rows=_rows_by_town(metric,metric_id)
        if set(rows)!=set(values)-{"Versilia"}: raise RuntimeError(f"{metric_id}: perimetro snapshot ARS non allineato")
        for town,row in rows.items():
            series_values=values.get(town)
            if not isinstance(series_values,list) or len(series_values)!=len(periods):
                raise RuntimeError(f"{metric_id}/{town}: valori storici non allineati")
            if not all(isinstance(value,(int,float)) and not isinstance(value,bool) for value in series_values):
                raise RuntimeError(f"{metric_id}/{town}: storico non numerico")
            _assert_close(row.get("value"),series_values[-1],f"{metric_id}/{town}")
            row["a3History"]={
                "source":"ARS Toscana","sourceUrl":source.get("exportUrl"),"sourceSnapshot":SOURCE_SNAPSHOT,
                "periods":list(periods),"values":list(series_values),
                "note":"Serie ufficiale ARS congelata fino al periodo del valore pubblico corrente; eventuali periodi ARS successivi restano materia del normale refresh della fonte.",
            }
            rows_enriched+=1
        aggregate=metric.get("aggregate"); versilia=values.get("Versilia")
        if not isinstance(aggregate,dict) or aggregate.get("value") is None: raise RuntimeError(f"{metric_id}: aggregato Versilia mancante")
        if not isinstance(versilia,list) or len(versilia)!=len(periods): raise RuntimeError(f"{metric_id}: storico Versilia non allineato")
        _assert_close(aggregate.get("value"),versilia[-1],f"{metric_id}/Versilia")
    return {"metricsEnriched":len(TARGET_METRICS),"rowsEnriched":rows_enriched,"pairsAcquired":len(TARGET_METRICS)}

def main()->None:
    site=load(SITE_PATH); summary=apply_enrichment(site,load(SNAPSHOT_PATH)); save(SITE_PATH,site)
    print(f"A3.5 ARS legacy history: {summary['metricsEnriched']} metriche · {summary['rowsEnriched']} righe · {summary['pairsAcquired']} coppie AVAILABLE_MISSING integrate.")

if __name__=="__main__": main()
