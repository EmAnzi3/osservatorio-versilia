#!/usr/bin/env python3
"""Regression A3.5 lotto 7: serie storiche ARS legacy."""
from __future__ import annotations
import copy,json,math
from pathlib import Path
import enrichment_audit_matrix_core as matrix_core
import enrichment_audit_matrix_structural_base as structural_base
import materialize_a3_5_ars_legacy_history as enrichment

ROOT=Path(__file__).resolve().parents[1]; SITE_PATH=ROOT/"data"/"site-data.json"
def load(path:Path)->dict: return json.loads(path.read_text(encoding="utf-8"))
def public_surface(metric:dict)->dict:
    value=copy.deepcopy(metric)
    for row in value.get("rows") or []:
        if isinstance(row,dict): row.pop("a3History",None)
    return value

def test_ars_legacy_history()->None:
    source_site=load(SITE_PATH); site=copy.deepcopy(source_site); snapshot=load(enrichment.SNAPSHOT_PATH)
    before={metric_id:public_surface(site["metrics"][metric_id]) for metric_id in enrichment.TARGET_METRICS}
    baseline={metric_id:{dimension:structural_base.acquired_evidence(site["metrics"][metric_id],dimension) for dimension in matrix_core.DIMENSIONS} for metric_id in enrichment.TARGET_METRICS}
    for metric_id in enrichment.TARGET_METRICS:
        assert baseline[metric_id]["serie_storica"] is None,(metric_id,baseline[metric_id]["serie_storica"])
    summary=enrichment.apply_enrichment(site,snapshot)
    assert summary=={"metricsEnriched":7,"rowsEnriched":49,"pairsAcquired":7}
    for metric_id in enrichment.TARGET_METRICS:
        metric=site["metrics"][metric_id]
        evidence=structural_base.acquired_evidence(metric,"serie_storica")
        assert evidence is not None and "a3History" in evidence,(metric_id,evidence)
        assert public_surface(metric)==before[metric_id],metric_id
        source=snapshot["indicators"][metric_id]; periods=source["periods"]
        assert len(periods)>=2 and source["sourceFile"]["sha256"] and int(source["sourceFile"]["bytes"])>0
        for row in metric["rows"]:
            history=row["a3History"]; values=source["values"][row["town"]]
            assert history["periods"]==periods and history["values"]==values
            assert history["sourceSnapshot"]==enrichment.SOURCE_SNAPSHOT
            assert math.isclose(float(row["value"]),float(values[-1]),rel_tol=0.0,abs_tol=0.055),(metric_id,row["town"])
        for dimension in matrix_core.DIMENSIONS:
            if dimension=="serie_storica": continue
            observed=structural_base.acquired_evidence(metric,dimension)
            assert observed==baseline[metric_id][dimension],(metric_id,dimension,baseline[metric_id][dimension],observed)

if __name__=="__main__":
    test_ars_legacy_history()
    print("A3.5 ARS legacy history regression passed: 7 serie storiche acquisite da snapshot ufficiali ARS versionati, senza modificare il payload pubblico consumato dalla UI.")
