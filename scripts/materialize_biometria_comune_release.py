#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from biometria_comune_config import (
    SOURCE_PATH, OUTPUT_PATH, MUNICIPALITY_ORDER, BAND_IDS, BAND_SUM_TOLERANCE
)

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate(source):
    errors = []
    municipalities = source.get("municipalities", {})
    if list(municipalities) != MUNICIPALITY_ORDER:
        errors.append("Municipality order/scope does not match canonical seven towns.")
    for name in MUNICIPALITY_ORDER:
        row = municipalities.get(name)
        if not row:
            errors.append(f"{name}: missing")
            continue
        area = row.get("surfaceKm2")
        if not isinstance(area, (int, float)) or area <= 0:
            errors.append(f"{name}: invalid surfaceKm2")
        pcts = row.get("altitudeBandsPct", {})
        if list(pcts) != BAND_IDS:
            errors.append(f"{name}: band ids/order mismatch")
            continue
        values = list(pcts.values())
        if any((not isinstance(v, (int, float)) or v < 0 or v > 100) for v in values):
            errors.append(f"{name}: band value outside 0..100")
        if abs(sum(values) - 100.0) > BAND_SUM_TOLERANCE + 1e-9:
            errors.append(f"{name}: band total {sum(values):.1f} outside tolerance")
        if round(sum(values[:2]), 1) != row.get("below600Pct"):
            errors.append(f"{name}: below600Pct mismatch")
        if round(sum(values[1:]), 1) != row.get("from300Pct"):
            errors.append(f"{name}: from300Pct mismatch")
        alt = [row.get("altitudeMinM"), row.get("altitudeMeanM"), row.get("altitudeMaxM")]
        if any(v is not None for v in alt) and not (all(isinstance(v,(int,float)) for v in alt) and alt[0] <= alt[1] <= alt[2]):
            errors.append(f"{name}: altitude min/mean/max inconsistent")
    if errors:
        raise ValueError("\n".join(errors))

def materialize(source, population=None):
    validate(source)
    out = json.loads(json.dumps(source))
    if population:
        for name, row in out["municipalities"].items():
            pop = population.get(name)
            if isinstance(pop, (int, float)) and pop >= 0:
                row["densityPerKm2"] = round(pop / row["surfaceKm2"], 1)
                row["densityStatus"] = "derived-from-canonical-population"
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=str(SOURCE_PATH))
    ap.add_argument("--output", default=str(OUTPUT_PATH))
    ap.add_argument("--population-json", help="Optional JSON object {municipality: residents}")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    source = load(args.source)
    population = load(args.population_json) if args.population_json else None
    result = materialize(source, population)
    if not args.check:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(path)
    else:
        print("OK: biometria source validated")

if __name__ == "__main__":
    main()
