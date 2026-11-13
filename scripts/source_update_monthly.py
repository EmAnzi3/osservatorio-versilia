#!/usr/bin/env python3
"""Giro mensile degli aggiornatori di `scripts/update_source_data.py`.

Esegue ogni aggiornatore disponibile (tutti gli indicatori ARS legacy; ASIA-UL e
mobilità Istat P2 per l'anno pubblicato e per quello successivo; ultima edizione
AGCOM FTTH; anno successivo di capacità ricettiva Istat, parco ACI e consumo di
suolo ISPRA; semestre successivo delle quotazioni OMI), uno alla volta, e scrive
un rapporto Markdown con l'esito di ciascuno: aggiornato, invariato o rifiutato
con il motivo e cosa fare. Ogni aggiornatore scrive solo se il file della fonte è
completo, quindi i riusciti restano anche se un altro viene rifiutato.

Il workflow «Aggiorna dati dalla fonte» lo lancia ogni mese su main: se i dati
cambiano apre una PR in bozza, la fusione resta manuale.

    python scripts/source_update_monthly.py --report reports/runtime/source-update.md
    python scripts/source_update_monthly.py --plan        # solo l'elenco dei comandi
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "data" / "site-data.json"
ARS_LEGACY = ROOT / "data" / "source-snapshots" / "ars-a3-5-legacy-history.json"
MOBILITY_KEY = "internalResidentialMobility"
# Aggiornatori di un'edizione annuale nuova: comando e indicatore che ne porta l'anno pubblicato.
NEXT_YEAR = [("istat-tourism", "tourismBeds"), ("aci-vehicles", "motorization"), ("ispra-soil", "landUse"), ("mim-schools", "schoolSites"), ("erp-arrears", "erpArrears")]
NEW_PERIOD = {"istat-tourism", "aci-vehicles", "ispra-soil", "omi-residential", "mim-schools", "gaia-water", "erp-arrears"}


def plan(site: dict, ars: dict) -> list[list[str]]:
    commands = [["ars-legacy", "--metric", key] for key in sorted(ars["indicators"])]
    asia = int(site["metrics"]["localUnits"]["meta"]["year"])
    commands += [["istat-asia", "--year", str(asia)], ["istat-asia", "--year", str(asia + 1)]]
    year = int(site["metrics"][MOBILITY_KEY]["meta"]["year"])
    commands += [["istat-mobility", "--year", str(year)], ["istat-mobility", "--year", str(year + 1)]]
    commands.append(["agcom-ftth"])
    commands += [[name, "--year", str(int(site["metrics"][key]["meta"]["year"]) + 1)]
                 for name, key in NEXT_YEAR]
    commands.append(["omi-residential", "--semester", next_semester(site["metrics"]["omiResidential"]["meta"]["year"])])
    commands.append(["gaia-water", "--period", next_semester(site["metrics"]["drinkingWaterQuality"]["meta"]["year"])])
    return commands


def next_semester(label: str) -> str:
    """«2° semestre 2025» → «2026-S1»; «1° semestre 2026» → «2026-S2»."""
    half, year = label.split("° semestre ")
    return f"{int(year) + 1}-S1" if half.strip() == "2" else f"{year.strip()}-S2"


def advice(args: list[str], message: str) -> str:
    """Cosa fare dopo un rifiuto, in base al motivo riportato dall'aggiornatore."""
    text = message.casefold()
    if "la fonte pubblica" in text:
        return "Periodo nuovo alla fonte: va pubblicato con una PR dedicata (etichette, domande verificate, test)."
    if args[0] == "istat-asia" and "anni assenti" in text:
        return "Anno non ancora pubblicato da Istat per tutti i Comuni: nessuna azione, si riprova il mese prossimo."
    if args[0] == "istat-mobility" and any(k in text for k in ("404", "not found", "non è uno zip")):
        return "Anno non ancora pubblicato da Istat: nessuna azione, si riprova il mese prossimo."
    if args[0] in NEW_PERIOD and any(k in text for k in ("non trovat", "non presente", "404", "not found")):
        return "Periodo non ancora pubblicato dalla fonte: nessuna azione, si riprova il mese prossimo."
    if any(k in text for k in ("tentativi", "timeout", "timed out", "connection", "http", "ssl", "urlopen")):
        return "Fonte non raggiungibile da GitHub: rilanciare il workflow a mano; se persiste, scaricare il file e usare `--file`."
    return "Forma del file cambiata o controllo non superato: verificare il file della fonte e l'aggiornatore prima di pubblicare."


def data_changed() -> list[str]:
    out = subprocess.run(["git", "status", "--porcelain", "--", "data"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [line[3:] for line in out.stdout.splitlines() if line.strip()]


def fingerprint() -> str:
    """Stato di `data/` rispetto al commit: cambia se un aggiornatore scrive qualcosa."""
    diff = subprocess.run(["git", "diff", "--binary", "--", "data"], cwd=ROOT, capture_output=True, check=True).stdout
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "--", "data"], cwd=ROOT, capture_output=True, check=True).stdout
    blobs = b"".join((ROOT / name).read_bytes() for name in untracked.decode().split())
    return hashlib.sha256(diff + untracked + blobs).hexdigest()


def run(commands: list[list[str]]) -> list[dict]:
    results = []
    for args in commands:
        before = fingerprint()
        proc = subprocess.run([sys.executable, "scripts/update_source_data.py", *args], cwd=ROOT, capture_output=True, text=True)
        print("::group::" + " ".join(args))
        print(proc.stdout + proc.stderr)
        print("::endgroup::")
        after = fingerprint()
        if proc.returncode != 0:
            lines = [l for l in (proc.stderr or proc.stdout).splitlines() if l.strip()]
            message = lines[-1] if lines else f"uscita {proc.returncode}"
            results.append({"args": args, "outcome": "rifiutato", "message": message, "advice": advice(args, message)})
        elif after != before:
            results.append({"args": args, "outcome": "aggiornato", "message": proc.stdout.strip()})
        else:
            results.append({"args": args, "outcome": "invariato", "message": ""})
    return results


def report(results: list[dict], files: list[str]) -> str:
    counts = {k: sum(r["outcome"] == k for r in results) for k in ("aggiornato", "invariato", "rifiutato")}
    lines = [
        "## Aggiornatori dalla fonte",
        "",
        f"{counts['aggiornato']} aggiornati · {counts['invariato']} invariati · {counts['rifiutato']} rifiutati",
        "",
        "| Aggiornatore | Esito | Dettaglio |",
        "|---|---|---|",
    ]
    for r in results:
        detail = r.get("advice", "") if r["outcome"] == "rifiutato" else ""
        if r["outcome"] == "rifiutato":
            detail = f"{r['message']}<br>**Cosa fare:** {detail}"
        lines.append(f"| `{' '.join(r['args'])}` | {r['outcome']} | {detail.replace('|', '/')} |")
    for r in results:
        if r["outcome"] == "aggiornato":
            lines += ["", f"### `{' '.join(r['args'])}`", "", "```", r["message"], "```"]
    if files:
        lines += ["", "File cambiati:", "", *[f"- `{f}`" for f in files]]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--report", type=Path)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    commands = plan(json.loads(SITE.read_text(encoding="utf-8")), json.loads(ARS_LEGACY.read_text(encoding="utf-8")))
    if args.plan:
        print("\n".join(" ".join(c) for c in commands))
        return 0
    results = run(commands)
    files = data_changed()
    text = report(results, files)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
            out.write(f"changed={'true' if files else 'false'}\n")
            out.write(f"refused={sum(r['outcome'] == 'rifiutato' for r in results)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
