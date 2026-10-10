#!/usr/bin/env python3
"""Declarative entry point for the site-wide consistency gate."""
from __future__ import annotations

import json

import site_consistency_impl as _impl
from content_contract import configured_paths, expected_pages as _expected_pages, validate_content_contract
from ephemeral_build_workspace import validate_build_materialization_contract
from site_consistency_impl import *  # noqa: F401,F403
from workflow_contract import validate_workflow_contract
from visualization_content_contract import validate_visual_runtime_contract, validate_visualization_content_contract
from semantic_model_contract import validate_semantic_model_contract
from semantic_operations import coverage_matrix
from semantic_query_engine import QueryEngine
import semantic_query_coast_adapters as coast
import semantic_query_bathing_adapters as bathing
import semantic_query_maritime_adapters as maritime
import semantic_query_extractive_adapters as extractive
import semantic_query_library_adapters as library


_ORIGINAL_BUILD_ASSERTIONS = _impl.build_assertions


def _build_assertions_from_dist_catalog(dist) -> None:
    """Valida l'inventario HTML contro il catalogo realmente usato per produrre dist/."""
    catalog_path = dist / "data" / "site-data.json"
    assert catalog_path.exists(), f"Catalogo materializzato della build non trovato: {catalog_path}"
    build_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    validate_visualization_content_contract(catalog_path)
    effective_semantic = validate_semantic_model_contract(catalog_path, layer="effective")
    operation_matrix = coverage_matrix(json.loads(catalog_path.read_text(encoding="utf-8")))
    assert len(operation_matrix) == effective_semantic["metrics"]
    query_engine = QueryEngine(catalog_path, layer="effective")
    query_coverage = query_engine.coverage()
    assert len(query_coverage) == effective_semantic["metrics"]
    for item in query_coverage:
        if item["engine"]["status"] == "adapter_present_query_preconditions_apply":
            selector={"metric":item["metric"],"dimension":item["engine"]["dimensions"][0]}
            query = {"operation": "lookup" if item["metric"] == "drinkingWaterQuality" else "compare", "selectors": [selector]}
            coastal = item["metric"] in (*coast.KEYS,*bathing.KEYS,*maritime.KEYS)
            is_library = item["metric"] in library.KEYS
            if coastal or is_library or item["metric"]==extractive.KEYS[1]:
                refusal = query_engine.query(query)
                assert refusal["status"] == "not_computable" and "partial_coverage_requires_opt_in" in refusal["reasons"], refusal
                query["allowPartial"] = True
            result = query_engine.query(query)
            assert result["status"] == "computed", result
            if query["operation"] == "lookup":
                assert result["interpretationLevel"] == "source_lookup" and result["coverage"]["usable"] == 70, result
            if is_library:
                assert result["coverage"]["usable"] == 5 and {x["observation"]["geography"] for x in result["excluded"]} == {"046018", "046030"}, result
            if coastal:
                assert result["coverage"]["usable"] == 4 and {x["observation"]["geography"] for x in result["excluded"]} == set(coast.NA), result
            if 'weighted_ratio' in item['engine']['operations']:
                result = query_engine.query(dict(operation='weighted_ratio',selectors=[selector],**({'allowPartial':True} if coastal else {})))
                assert result['status']=='computed', result
                if coastal:assert result['coverage']['usable']==4 and len(result['excluded'])==3, result
            if 'benchmark_gap' in item['engine']['operations']:
                for scope in item['engine']['benchmarkScopes']:
                    result = query_engine.query({'operation':'benchmark_gap','benchmark':scope,
                        'selectors':[dict(selector,towns=[coast.COASTAL[0] if coastal else ('046005' if is_library else '046018')])]})
                    assert result['status']=='computed', result
    age_coverage=next(x for x in query_coverage if x['metric']=='ageDistribution')
    for dimension in age_coverage['engine']['dimensions']:
        result=query_engine.query({'operation':'weighted_ratio','selectors':[{'metric':'ageDistribution','dimension':dimension}]})
        assert result['status']=='computed',result
    result=query_engine.query({'operation':'anomaly','selectors':[{'metric':'income'}],
        'rule':'tukey_1_5_iqr','reference':'selected_municipalities','purpose':'Effective catalog descriptive regression'})
    assert result['status']=='computed',result
    from test_semantic_territorial_readings import regressions
    regressions(catalog_path)
    from test_semantic_ars_adapters import regressions as ars_regressions
    ars_regressions(catalog_path)
    from test_semantic_business_adapters import regressions as business_regressions
    business_regressions(catalog_path)
    from test_semantic_census_adapters import regressions as census_regressions
    census_regressions(catalog_path)
    from test_semantic_distinct_finance_adapters import regressions as distinct_finance_regressions
    from test_semantic_demography_school_adapters import regressions as demography_school_regressions
    demography_school_regressions(catalog_path)
    from test_semantic_commuting_adapters import regressions as commuting_regressions
    commuting_regressions(catalog_path)
    from test_semantic_agriculture_adapters import regressions as agriculture_regressions
    agriculture_regressions(catalog_path)
    from test_semantic_coast_adapters import regressions as coast_regressions
    coast_regressions(catalog_path)
    from test_semantic_bathing_adapters import regressions as bathing_regressions
    bathing_regressions(catalog_path)
    from test_semantic_maritime_adapters import regressions as maritime_regressions
    maritime_regressions(catalog_path)
    from test_semantic_extractive_adapters import regressions as extractive_regressions
    extractive_regressions(catalog_path)
    from test_semantic_remediation_adapters import regressions as remediation_regressions
    remediation_regressions(catalog_path)
    from test_semantic_pab_adapters import regressions as pab_regressions
    pab_regressions(catalog_path)
    from test_semantic_climate_adapters import regressions as climate_regressions
    climate_regressions(catalog_path)
    from test_semantic_classification_adapters import regressions as classification_regressions
    classification_regressions(catalog_path)
    from test_semantic_water_quality_adapters import regressions as water_quality_regressions
    water_quality_regressions(catalog_path)
    from test_semantic_library_adapters import regressions as library_regressions
    library_regressions(catalog_path)
    from test_semantic_regional_adapters import regressions as regional_regressions
    regional_regressions(catalog_path)
    from test_semantic_tourism_adapters import regressions as tourism_regressions
    tourism_regressions(catalog_path)
    from test_semantic_rgs_adapters import regressions as rgs_regressions
    rgs_regressions(catalog_path)
    from test_semantic_mef_adapters import regressions as mef_regressions
    mef_regressions(catalog_path)
    from test_semantic_agriculture_profile_adapters import regressions as profile_regressions
    profile_regressions(catalog_path)
    from test_semantic_fragility_adapters import regressions as fragility_regressions
    fragility_regressions(catalog_path)
    from test_semantic_hazard_adapters import regressions as hazard_regressions
    hazard_regressions(catalog_path)
    from test_semantic_territory_adapters import regressions as territory_regressions
    territory_regressions(catalog_path)
    from test_semantic_soil_adapters import regressions as soil_regressions
    soil_regressions(catalog_path)
    from test_semantic_geography_adapters import regressions as geography_regressions
    geography_regressions(catalog_path)
    from test_semantic_environment_adapters import regressions as environment_regressions
    environment_regressions(catalog_path)
    distinct_finance_regressions(catalog_path)
    from test_semantic_finance_adapters import regressions as finance_regressions
    finance_regressions(catalog_path)
    from test_semantic_engine_audit import regressions as engine_audit_regressions
    engine_audit_regressions(catalog_path)
    print(f"A6.4 effective query coverage: {len(query_coverage)} indicatori; adapter e limiti derivati.")
    print(
        "A6 semantic model effective catalog: "
        f"{effective_semantic['metrics']} indicatori pubblici · "
        f"{effective_semantic['sources']} fonti · {effective_semantic['periods']} periodi."
    )

    previous_expected_pages = _impl.expected_pages
    _impl.expected_pages = lambda: _expected_pages(build_catalog)
    try:
        _ORIGINAL_BUILD_ASSERTIONS(dist)
    finally:
        _impl.expected_pages = previous_expected_pages


def main() -> None:
    content = validate_content_contract()
    workflows = validate_workflow_contract()
    build_workspace = validate_build_materialization_contract()
    visualization = validate_visualization_content_contract()
    semantic_source = validate_semantic_model_contract(layer="source")
    runtime_visualization = validate_visual_runtime_contract()
    _impl.SPECIAL_PUBLIC_PAGES = configured_paths("builderTraceExceptions")
    _impl.NO_SHELL_PAGES = configured_paths("noShell")
    _impl.NO_FOOTER_PAGES = configured_paths("noFooter")
    _impl.expected_pages = _expected_pages
    _impl.build_assertions = _build_assertions_from_dist_catalog
    print(
        "Contratto architetturale verificato: "
        f"{content['metrics']} indicatori, {content['pages']} route, {workflows['workflows']} workflow, "
        f"{build_workspace['allowed_mutations']} mutazioni build transitorie dichiarate, "
        f"{visualization['unitCount']} unità visuali governate nel catalogo sorgente, "
        f"{semantic_source['metrics']} indicatori nel Source Catalog A6, "
        f"{len(runtime_visualization)} invarianti runtime visuali."
    )
    _impl.main()


if __name__ == "__main__":
    main()
