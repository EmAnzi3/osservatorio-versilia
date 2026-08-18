#!/usr/bin/env python3
"""Inventario forense read-only dei progetti PNRR selezionati per la Versilia.

Questo script non modifica il catalogo. Scarica il feed ufficiale Regione Toscana,
riusa esattamente il perimetro dell'audit PNRR e conserva abbastanza dettaglio
per verificare duplicazioni, CUP/ID, fasi ReGiS e provenienza dei conteggi.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pnrr_toscana_audit as audit


def clean_row(row: dict[str, Any]) -> dict[str, str]:
    """Conserva soltanto campi non vuoti, senza trasformare il contenuto fonte."""
    result: dict[str, str] = {}
    for key, value in row.items():
        text = str(value or "").strip()
        if text and audit.norm(text) not in {"NULL", "ND", "N D", "NON DISPONIBILE"}:
            result[str(key)] = text
    return result


def project_title(row: dict[str, Any]) -> str:
    preferred = (
        "titolo_progetto",
        "titolo",
        "descrizione_sintetica_cup",
        "descrizione_progetto",
        "denominazione_progetto",
        "nome_progetto",
        "oggetto_progetto",
        "descrizione",
    )
    for key in preferred:
        value = str(row.get(key) or "").strip()
        if value and audit.norm(value) not in {"NULL", "ND", "N D", "NON DISPONIBILE"}:
            return value
    for key, value in row.items():
        key_n = audit.norm(key)
        if "TITOLO" in key_n or "DENOMINAZIONE" in key_n:
            text = str(value or "").strip()
            if text and audit.norm(text) not in {"NULL", "ND", "N D", "NON DISPONIBILE"}:
                return text
    return ""


def build_forensic(data: dict[str, Any]) -> dict[str, Any]:
    published = audit.published_snapshot(data)
    records = list(audit.iter_csv_records())
    by_town, dates, scanned = audit.select_town_projects(records, published)

    selected_ids: set[str] = set()
    selected_subjects: dict[str, str] = {}
    inventory: list[dict[str, Any]] = []
    phase_distribution: dict[str, Counter[str]] = defaultdict(Counter)
    amount_missing: list[str] = []

    for code, projects in by_town.items():
        town = published[code]["town"]
        for project_id, row in projects.items():
            selected_ids.add(project_id)
            selected_subjects[project_id] = town
            phase = str(row.get(audit.CANONICAL_CONCLUSION_FIELD) or "").strip()
            phase_distribution[town][phase or "(vuoto)"] += 1
            if audit.parse_number(row.get("importo_finanziato_pnrr")) is None:
                amount_missing.append(project_id)
            inventory.append(
                {
                    "townCode": code,
                    "town": town,
                    "id_progetto": project_id,
                    "cup": str(row.get("cup") or "").strip(),
                    "title": project_title(row),
                    "fundingPnrr": audit.parse_number(row.get("importo_finanziato_pnrr")),
                    "canonicalPhase": phase,
                    "concluded": audit.concluded_from(row, audit.CANONICAL_CONCLUSION_FIELD),
                    "dataElaborazione": str(row.get("data_elaborazione") or "").strip(),
                    "raw": clean_row(row),
                }
            )

    # Conta quante righe sorgente corrispondono a ciascun ID selezionato: il
    # conteggio pubblico resta per progetto unico, non per localizzazione/riga.
    occurrences: Counter[str] = Counter()
    for row in records:
        project_id = str(row.get("id_progetto") or row.get("cup") or "").strip()
        if project_id in selected_ids:
            town = selected_subjects.get(project_id, "")
            if town and audit.town_subject_match(row.get("soggetto_attuatore"), town):
                occurrences[project_id] += 1

    cross_town: dict[str, list[str]] = defaultdict(list)
    for code, projects in by_town.items():
        for project_id in projects:
            cross_town[project_id].append(code)

    inventory.sort(key=lambda item: (item["town"].casefold(), item["id_progetto"]))
    field_names = sorted({key for item in inventory for key in item["raw"]})
    duplicate_source_rows = {
        project_id: count for project_id, count in sorted(occurrences.items()) if count > 1
    }
    cross_town_duplicates = {
        project_id: codes for project_id, codes in sorted(cross_town.items()) if len(codes) > 1
    }

    return {
        "dataset": audit.DATASET_URL,
        "resource": audit.MAIN_CSV_URL,
        "recordsScanned": scanned,
        "dataElaborationDates": sorted(dates),
        "selectedUniqueProjects": len(inventory),
        "uniqueProjectIds": len(selected_ids),
        "missingFundingProjectIds": sorted(amount_missing),
        "sourceRowOccurrencesGreaterThanOne": duplicate_source_rows,
        "crossTownDuplicateProjectIds": cross_town_duplicates,
        "availableFieldsOnSelectedProjects": field_names,
        "phaseDistribution": {
            town: dict(sorted(counter.items()))
            for town, counter in sorted(phase_distribution.items())
        },
        "projects": inventory,
    }


def markdown(result: dict[str, Any]) -> str:
    concluded = sum(1 for item in result["projects"] if item["concluded"])
    rows = [
        "# Verifica forense PNRR · Regione Toscana",
        "",
        f"- Fotografia: `{', '.join(result['dataElaborationDates']) or 'n.d.'}`",
        f"- Record sorgente scansionati: {result['recordsScanned']}",
        f"- Progetti unici selezionati: {result['selectedUniqueProjects']}",
        f"- Progetti conclusi (`{audit.CANONICAL_CONCLUSION_FIELD}`): {concluded}",
        f"- Progetti senza importo PNRR: {len(result['missingFundingProjectIds'])}",
        f"- ID presenti in più Comuni: {len(result['crossTownDuplicateProjectIds'])}",
        f"- ID con più righe sorgente: {len(result['sourceRowOccurrencesGreaterThanOne'])}",
        "",
        "## Distribuzione delle fasi ReGiS",
        "",
    ]
    for town, phases in result["phaseDistribution"].items():
        rows.append(f"### {town}")
        for phase, count in phases.items():
            rows.append(f"- `{phase}`: {count}")
        rows.append("")

    rows.extend(
        [
            "## Inventario sintetico",
            "",
            "| Comune | ID progetto | CUP | Fase ReGiS | Importo PNRR | Titolo |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for item in result["projects"]:
        title = str(item["title"] or "").replace("|", "\\|").replace("\n", " ")
        rows.append(
            f"| {item['town']} | {item['id_progetto']} | {item['cup'] or '—'} | "
            f"{item['canonicalPhase'] or '—'} | {item['fundingPnrr'] if item['fundingPnrr'] is not None else 'n.d.'} | {title or '—'} |"
        )
    rows.append("")
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/site-data.json"))
    parser.add_argument("--output-json", type=Path, default=Path("reports/pnrr-toscana-forensic.json"))
    parser.add_argument("--output-md", type=Path, default=Path("reports/pnrr-toscana-forensic.md"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    result = build_forensic(data)
    if result["selectedUniqueProjects"] <= 0:
        raise SystemExit("Nessun progetto PNRR selezionato: fotografia non valida")
    if result["selectedUniqueProjects"] != result["uniqueProjectIds"]:
        raise SystemExit("Conteggio progetti e ID unici non coerente")
    if result["crossTownDuplicateProjectIds"]:
        raise SystemExit("Uno o più ID progetto risultano attribuiti a più Comuni del perimetro")
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(result), encoding="utf-8")
    print(markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
