#!/usr/bin/env python3
"""Test offline del giro mensile degli aggiornatori (piano, consigli, rapporto)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_update_monthly as m  # noqa: E402

site = json.loads(m.SITE.read_text(encoding="utf-8"))
ars = json.loads(m.ARS_LEGACY.read_text(encoding="utf-8"))
commands = m.plan(site, ars)
year = int(site["metrics"][m.MOBILITY_KEY]["meta"]["year"])
assert [c for c in commands if c[0] == "ars-legacy"] == [["ars-legacy", "--metric", k] for k in sorted(ars["indicators"])]
n = len(m.NEXT_YEAR)
assert commands[-(n + 5):-(n + 2)] == [["istat-mobility", "--year", str(year)], ["istat-mobility", "--year", str(year + 1)], ["agcom-ftth"]]
assert commands[-(n + 2):-2] == [[n, "--year", str(int(site["metrics"][k]["meta"]["year"]) + 1)] for n, k in m.NEXT_YEAR]
assert commands[-2][:2] == ["omi-residential", "--semester"]
assert commands[-1] == ["gaia-water", "--period", m.next_semester(site["metrics"]["drinkingWaterQuality"]["meta"]["year"])]
assert "non ancora pubblicato" in m.advice(["gaia-water", "--period", "2027-S1"], "GAIA Camaiore · Casoli: 1° semestre 2027 non presente (la pagina riporta '2° Semestre 2026')")
assert m.next_semester("2° semestre 2025") == "2026-S1" and m.next_semester("1° semestre 2026") == "2026-S2"
assert "non ancora pubblicato" in m.advice(["ispra-soil", "--year", "2026"], "Consumo di suolo: edizione 2027 non trovata nella libreria ISPRA")
assert "non ancora pubblicato" in m.advice(["omi-residential"], "OMI: semestre 2026-S2 o 2026-S1 non presente nella consultazione")
assert "non ancora pubblicato" in m.advice(["mim-schools", "--year", "2027"], "Anagrafe scuole: file statale dell'a.s. 2027/28 non presente nel catalogo MIM")
assert "hospitalizedAll" in ars["indicators"]
asia = int(site["metrics"]["localUnits"]["meta"]["year"])
assert [c for c in commands if c[0] == "istat-asia"] == [["istat-asia", "--year", str(asia)], ["istat-asia", "--year", str(asia + 1)]]
assert "non ancora pubblicato" in m.advice(["istat-asia", "--year", str(asia + 1)], "ASIA-UL 046005: anni assenti ['lu 2026']")

mob = ["istat-mobility", "--year", str(year + 1)]
assert "PR dedicata" in m.advice(["ars-legacy"], "hospitalizedAll: la fonte pubblica 2026 (pubblicato 2025); …")
assert "non ancora pubblicato" in m.advice(mob, "Aggiornamento rifiutato: https://demo.istat.it/x.zip: HTTP 404")
assert "non raggiungibile" in m.advice(["ars-legacy"], "x: 3 tentativi da 60 secondi falliti; timed out")
assert "non raggiungibile" in m.advice(mob, "x: 3 tentativi da 60 secondi falliti; timed out")
assert "Forma del file" in m.advice(["ars-legacy"], "ARS 1332: serie assenti per ['Massarosa']")

text = m.report(
    [
        {"args": ["ars-legacy", "--metric", "dementia"], "outcome": "invariato", "message": ""},
        {"args": ["ars-legacy", "--metric", "hospitalizedAll"], "outcome": "aggiornato", "message": "Massarosa 63,28 → 63,40"},
        {"args": mob, "outcome": "rifiutato", "message": "HTTP 404 | x", "advice": m.advice(mob, "HTTP 404")},
    ],
    ["data/site-data.json"],
)
assert "1 aggiornati · 1 invariati · 1 rifiutati" in text
assert "HTTP 404 / x<br>**Cosa fare:** Anno non ancora pubblicato" in text
assert "Massarosa 63,28 → 63,40" in text and "- `data/site-data.json`" in text
print("Giro mensile aggiornatori: piano 7 ARS + ASIA-UL + mobilità", year, "e", year + 1, "· consigli e rapporto PASS")
