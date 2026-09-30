#!/usr/bin/env python3
"""Audit whether A3-acquired histories and Toscana/Italia benchmarks reach public renderers."""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

PRIORITY_DIMENSIONS = ("serie_storica", "benchmark_toscana_italia")
PUBLIC_STATUSES = {"PUBLIC_RENDERED", "SPECIAL_ROUTE_RENDERED"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _valid_series(series: Any) -> tuple[list[str], list[float]] | None:
    if not isinstance(series, dict):
        return None
    years = series.get("years")
    values = series.get("values")
    if not isinstance(years, list) or not isinstance(values, list) or len(years) < 2 or len(years) != len(values):
        return None
    pairs = [(str(year), float(value)) for year, value in zip(years, values, strict=True) if _finite(value)]
    if len(pairs) < 2:
        return None
    if len({year for year, _value in pairs}) != len(pairs):
        return None
    return [year for year, _value in pairs], [value for _year, value in pairs]


def _generic_history(metric: dict[str, Any]) -> bool:
    rows = [row for row in metric.get("rows", []) if isinstance(row, dict) and not row.get("notApplicable")]
    if not rows:
        return False
    maps: list[dict[str, float]] = []
    for row in rows:
        valid = _valid_series(row.get("series"))
        if valid is None:
            return False
        years, values = valid
        maps.append(dict(zip(years, values, strict=True)))
    common = set(maps[0])
    for mapping in maps[1:]:
        common &= set(mapping)
    return len(common) >= 2


def _any_row_series(metric: dict[str, Any]) -> bool:
    return any(
        isinstance(row, dict) and _valid_series(row.get("series")) is not None
        for row in metric.get("rows", [])
    )


def _runtime_corpus(dist: Path) -> str:
    chunks: list[str] = []
    assets = dist / "assets"
    if assets.is_dir():
        for path in sorted(assets.glob("*.js")):
            try:
                chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                pass
    return "\n".join(chunks)


def _route_index(dist: Path, metric: dict[str, Any]) -> Path | None:
    storage = metric.get("dataStorage")
    storage = storage if isinstance(storage, dict) else {}
    meta = metric.get("meta")
    meta = meta if isinstance(meta, dict) else {}
    route = storage.get("detailRoute") or meta.get("detailRoute")
    if not isinstance(route, str) or not route.strip():
        return None
    return dist / route.strip("/") / "index.html"


def _history_status(metric_id: str, metric: dict[str, Any], evidence: str, dist: Path, runtime: str) -> tuple[str, str]:
    if any(isinstance(row, dict) and isinstance(row.get("a3History"), dict) for row in metric.get("rows", [])):
        return "PUBLIC_PAYLOAD_NOT_RENDERED", "a3History Ã¨ nel payload ma il renderer/export standard consuma row.series.years/values"
    if _generic_history(metric):
        return "PUBLIC_RENDERED", "serie allineata nel contratto pubblico row.series.years/values"

    route = _route_index(dist, metric)
    if route is not None and route.is_file():
        text = route.read_text(encoding="utf-8", errors="ignore").lower()
        if "storico" in text or "andamento" in text:
            return "SPECIAL_ROUTE_RENDERED", f"storico pubblicato dalla route specialistica {route.relative_to(dist)}"

    meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
    if meta.get("compositeType") == "invalsiProfile" and meta.get("allowPartialHistory") is True and _any_row_series(metric):
        return "SPECIAL_ROUTE_RENDERED", "profilo INVALSI con storico parziale governato dal renderer specialistico"

    if _any_row_series(metric) and metric_id in runtime:
        return "SPECIAL_ROUTE_RENDERED", "renderer specialistico esplicito per serie parziali/non omogenee"

    structural_tokens = [
        token for token in re.findall(r"[A-Za-z][A-Za-z0-9_]+", evidence)
        if token not in {"structured", "rows", "series", "values", "years", "storage", "data"}
    ]
    if metric_id in runtime and any(token in runtime for token in structural_tokens):
        return "SPECIAL_ROUTE_RENDERED", "struttura storica specialistica consumata dal runtime pubblico"

    return "NOT_PUBLIC_DESPITE_ACQUIRED", "A3 rileva uno storico ma non esiste un contratto pubblico consumabile dal renderer"


def _valid_meta_benchmark(metric: dict[str, Any]) -> bool:
    meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
    benchmark = meta.get("benchmark")
    if not isinstance(benchmark, dict):
        return False
    tuscany = benchmark.get("tuscany")
    italy = benchmark.get("italy")
    if not _finite(tuscany):
        return False
    if italy is not None and not _finite(italy):
        return False
    return all(str(benchmark.get(key) or "").strip() for key in ("year", "source", "url"))


def _benchmark_status(metric_id: str, metric: dict[str, Any], evidence: str, dist: Path, runtime: str) -> tuple[str, str]:
    if _valid_meta_benchmark(metric):
        return "PUBLIC_RENDERED", "meta.benchmark espone Toscana e, quando disponibile, Italia con anno/fonte/link"

    aggregate = metric.get("aggregate")
    national = metric.get("nationalBenchmark")
    if isinstance(aggregate, dict) and isinstance(national, dict):
        if _finite(aggregate.get("value")) and _finite(national.get("value")):
            labels = f"{aggregate.get('label','')} {national.get('label','')}".lower()
            if "toscana" in labels and "italia" in labels and metric_id in runtime:
                return "SPECIAL_ROUTE_RENDERED", "benchmark INVALSI Toscana/Italia consumato dal renderer specialistico"

    route = _route_index(dist, metric)
    if route is not None and route.is_file():
        text = route.read_text(encoding="utf-8", errors="ignore").lower()
        if "toscana" in text or "regionale" in text:
            return "SPECIAL_ROUTE_RENDERED", f"benchmark regionale pubblicato dalla route specialistica {route.relative_to(dist)}"

    if evidence.endswith("method.reference") or evidence.endswith("method.riferimento"):
        return "DETECTOR_FALSE_POSITIVE", "un riferimento bibliografico/geografico non Ã¨ un benchmark numerico Toscana/Italia"
    return "NOT_PUBLIC_DESPITE_ACQUIRED", "A3 rileva un benchmark ma il payload pubblico non espone un confronto regionale/nazionale renderizzabile"


def build_report(data: dict[str, Any], matrix: dict[str, Any], dist: Path) -> dict[str, Any]:
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Effective Public Catalog senza metrics")
    runtime = _runtime_corpus(dist)
    entries: list[dict[str, Any]] = []
    for row in matrix.get("rows", []):
        if not isinstance(row, dict) or row.get("dimension") not in PRIORITY_DIMENSIONS or row.get("state") != "ACQUIRED":
            continue
        metric_id = str(row.get("metricId") or "")
        metric = metrics.get(metric_id)
        if not isinstance(metric, dict):
            raise RuntimeError(f"Metrica ACQUIRED assente dal catalogo effettivo: {metric_id}")
        meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
        dimension = str(row["dimension"])
        evidence = str(row.get("evidence") or "")
        if dimension == "serie_storica":
            status, reason = _history_stattÊY]šX×ÚYY]šXË]šY[˜ÙK\İ[[YJBˆ[ÙN‚ˆİ]\Ë™X\ÛÛˆHØ™[˜ÚX\š×Üİ]2†ÖWG&–5ö–BÂÖWG&–2ÂWf–FVæ6RÂF—7BÂ'VçF–ÖR¢VçG&–W2æVæB‡°¢&ÖWG&–4–B#¢ÖWG&–5ö–BÀ¢&F–ÖVç6–öâ#¢F–ÖVç6–öâÀ¢'V&Æ–6F–öå7FGW2#¢7FGW2À¢&Wf–FVæ6R#¢Wf–FVæ6RÀ¢'&V6öâ#¢&V6öâÀ¢'6÷W&6R#¢7G"†ÖWFævWB‚'6÷W&6R"’÷"""’À¢'W&–öB#¢7G"†ÖWFævWB‚'–V""’÷"""’À¢'Væ—B#¢7G"†ÖWFævWB‚'Væ—B"’÷"""’À¢'6÷W&6UW&Â#¢7G"†ÖWG&–2ævWB‚'6÷W&6UW&Â"’÷"""’À¢Ò ¢7VÖÖ'“¢F–7E·7G"Âç•ÒÒ·Ğ¢f÷"F–ÖVç6–öâ–â$”õ$•E•ôD”ÔTå4”ôå3 ¢F–ÕöVçG&–W2Ò¶VçG'’f÷"VçG'’–âVçG&–W2–bVçG'•²&F–ÖVç6–öâ%ÒÓÒF–ÖVç6–öåĞ¢6÷VçG2Ò6÷VçFW"†VçG'•²'V&Æ–6F–öå7FGW2%Òf÷"VçG'’–âF–ÕöVçG&–W2¢7VÖÖ'•¶F–ÖVç6–öåÒÒ°¢&7V—&VB#¢ÆVâ†F–ÕöVçG&–W2’À¢'V&Æ–2#¢7VÒ†6÷VçG5·7FFUÒf÷"7FFR–âT$Ä”5õ5DEU4U2’À¢&æ÷EV&Æ–2#¢ÆVâ†F–ÕöVçG&–W2’Ò7VÒ†6÷VçG5·7FFUÒf÷"7FFR–âT$Ä”5õ5DEU4U2’À¢'7FGW6W2#¢F–7B‡6÷'FVB†6÷VçG2æ—FV×2‚’’’À¢Ğ¢&WGW&â°¢'66†VÖfW'6–öâ#¢À¢&VffV7F—fUV&Æ–4ÖWG&–46÷VçB#¢ÆVâ†ÖWG&–72’À¢&ÖG&—…7VÖÖ'’#¢ÖG&—‚ævWB‚'7VÖÖ'’"Â·Ò’À¢'7VÖÖ'’#¢7VÖÖ'’À¢&VçG&–W2#¢6÷'FVB†VçG&–W2Â¶W“ÖÆÖ&F—FVÓ¢†—FVÕ²&F–ÖVç6–öâ%ÒÂ—FVÕ²&ÖWG&–4–B%Ò’’À¢Ğ  ¦FVbfÆ–FFU÷&W÷'B‡&W÷'C¢F–7E·7G"Âç•Ò’ÓâæöæS ¢&ö&ÆV×2Ò¶VçG'’f÷"VçG'’–â&W÷'E²&VçG&–W2%Ò–bVçG'•²'V&Æ–6F–öå7FGW2%Òæ÷B–âT$Ä”5õ5DEU4U5Ğ¢ÖWFFFöÖ—76–ærÒ°¢VçG'’f÷"VçG'’–â&W÷'E²&VçG&–W2%Ğ¢–bæ÷BVçG'•²'6÷W&6R%Ò÷"æ÷BVçG'•²'W&–öB%Ò÷"æ÷BVçG'•²'Væ—B%Ò÷"æ÷BVçG'•²'6÷W&6UW&Â%Ğ¢Ğ¢–bÖWFFFöÖ—76–æs ¢FWF–ÂÒ"Â"æ¦ö–â†b'¶VçG'•²vÖWG&–4–Bu×Ò÷¶VçG'•²vF–ÖVç6–öâu×Ò"f÷"VçG'’–âÖWFFFöÖ—76–æu³£Ò¢&—6R'VçF–ÖTW'&÷"†b$2V&Æ–6F–öâ6öçG&7C¢föçFR÷W&–öFò÷Væ—L:öÆ–æ²Öæ6çF“¢¶FWF–ÇÒ"¢–b&ö&ÆV×3 ¢FWF–ÂÒ"Â"æ¦ö–â€¢b'¶VçG'•²vÖWG&–4–Bu×Ò÷¶VçG'•²vF–ÖVç6–öâu×Ó×¶VçG'•²wV&Æ–6F–öå7FGW2u×Ò ¢f÷"VçG'’–â&ö&ÆV×5³£#Ğ¢¢&—6R'VçF–ÖTW'&÷"†b$2V&Æ–6F–öâ6öçG&7Bæöâ6†—W6ó¢¶FWF–ÇÒ"  ¦FVbÖ&¶F÷vâ‡&W÷'C¢F–7E·7G"Âç•Ò’Óâ7G# ¢F—FÆRÒ"22(	BV&Æ–6F–öâvVF—B ¢Æ–æW2Ò·F—FÆRÂ""Âb$VffV7F—fRV&Æ–26FÆös¢¢§·&W÷'E²vVffV7F—fUV&Æ–4ÖWG&–46÷VçBu×Ò–æF–6F÷&’¢¢â"Â""Â"226–çFW6’"Â""Â'ÂF–ÖVç6–öæRÂ5T•$TBÂV&&Æ–6’ÂæöâV&&Æ–6’Â"Â'ÂÒÒ×ÂÒÒÓ§ÂÒÒÓ§ÂÒÒÓ§Â%Ğ¢Æ&VÇ2Ò²'6W&–U÷7F÷&–6#¢%6W&–R7F÷&–6†R"Â&&Væ6†Ö&µ÷F÷66æö—FÆ–#¢$&Væ6†Ö&²F÷66æò—FÆ–'Ğ¢f÷"F–ÖVç6–öâ–â$”õ$•E•ôD”ÔTå4”ôå3 ¢—FVÒÒ&W÷'E²'7VÖÖ'’%Õ¶F–ÖVç6–öåĞ¢Æ–æW2æVæB†b'Â¶Æ&VÇ5¶F–ÖVç6–öå×ÒÂ¶—FVÕ²v7V—&VBu×ÒÂ¶—FVÕ²wV&Æ–2u×ÒÂ¶—FVÕ²væ÷EV&Æ–2u×ÒÂ"¢Æ–æW2³Ò²""Â"226÷–R5T•$TB"Â""Â'Â–æF–6F÷&RÂF–ÖVç6–öæRÂ7FFòV&&Æ–6¦–öæRÂWf–FVç¦Â"Â'ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×Â%Ğ¢f÷"VçG'’–â&W÷'E²&VçG&–W2%Ó ¢Æ–æW2æVæB†b'Â¶VçG'•²vÖWG&–4–Bu×ÖÂ¶VçG'•²vF–ÖVç6–öâu×ÖÂ¶VçG'•²wV&Æ–6F–öå7FGW2u×ÖÂ¶VçG'•²w&V6öâuÒç&WÆ6R‚wÂrÂròr—ÒÂ"¢&WGW&â%Æâ"æ¦ö–â†Æ–æW2’²%Æâ   ¦FVbÖ–â‚’ÓâæöæS ¢'6W"Ò&w'6Rä&wVÖVçE'6W"‚¢'6W"æFEö&wVÖVçB‚"ÒÖFF"ÂG—SÕF‚Â&WV—&VCÕG'VR¢'6W"æFEö&wVÖVçB‚"ÒÖÖG&—‚"ÂG—SÕF‚Â&WV—&VCÕG'VR¢'6W"æFEö&wVÖVçB‚"ÒÖF—7B"ÂG—SÕF‚ÂFVfVÇCÕF‚‚&F—7B"’¢'6W"æFEö&wVÖVçB‚"ÒÖ§6öâÖ÷WGWB"ÂG—SÕF‚¢'6W"æFEö&wVÖVçB‚"ÒÖÖ&¶F÷vâÖ÷WGWB"ÂG—SÕF‚¢'6W"æFEö&wVÖVçB‚"Ò×7G&–7B"Â7F–öãÒ'7F÷&U÷G'VR"¢&w2Ò'6W"ç'6Uö&w2‚¢&W÷'BÒ'V–ÆE÷&W÷'B†ÆöB†&w2æFF’ÂÆöB†&w2æÖG&—‚’Â&w2æF—7B¢–b&w2æ§6öåö÷WGWC ¢&w2æ§6öåö÷WGWBç&VçBæÖ¶F—"‡&VçG3ÕG'VRÂW†—7Eöö³ÕG'VR¢&w2æ§6öåö÷WGWBçw&—FU÷FW‡B†§6öâæGV×2‡&W÷'BÂVç7W&Uö66–“ÔfÇ6RÂ–æFVçCÓ"’²%Æâ"ÂVæ6öF–æsÒ'WFbÓ‚"¢–b&w2æÖ&¶F÷våö÷WGWC ¢&w2æÖ&¶F÷våö÷WGWBç&VçBæÖ¶F—"‡&VçG3ÕG'VRÂW†—7Eöö³ÕG'VR¢&w2æÖ&¶F÷våö÷WGWBçw&—FU÷FW‡B†Ö&¶F÷vâ‡&W÷'B’ÂVæ6öF–æsÒ'WFbÓ‚"¢f÷"F–ÖVç6–öâÂ—FVÒ–â&W÷'E²'7VÖÖ'’%Òæ—FV×2‚“ ¢&–çB†b$2V&Æ–6F–öâ¶F–ÖVç6–öçÓ¢¶—FVÕ²wV&Æ–2u×Ò÷¶—FVÕ²v7V—&VBu×ÒV&&Æ–6“²¶—FVÕ²væ÷EV&Æ–2u×Òvâ"¢–b&w2ç7G&–7C ¢fÆ–FFU÷&W÷'B‡&W÷'B  ¦–bõöæÖUõòÓÒ%õöÖ–åõò# ¢Ö–â‚ 