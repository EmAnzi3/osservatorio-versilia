#!/usr/bin/env python3
"""Allinea il materializzatore al perimetro approvato: nessuna sottodimensione sotto 6/7."""
from pathlib import Path

path = Path(__file__).with_name("materialize_agricoltura_territorio_v120.py")
text = path.read_text(encoding="utf-8")

replacements = [
    ('    ("OLIVTTR", "Olive da tavola"),\n', ''),
    ('        minimum = 4 if crop == "OLIVTTR" else 6\n', '        minimum = 6\n'),
    ('    olive_table_missing = {code for code in expected if raw[code]["cropsHa"].get("OLIVTTR") is None}\n    if olive_table_missing != {"046013", "046030", "046033"}:\n        raise RuntimeError("Perimetro n.d. OLIVTTR diverso da quello verificato")\n', ''),
    ('            "formula": "ARU per TYPE_OF_CROP nel dataflow DF_DCAT_CENSAGRIC2020_UA_CROPS_2: ARLAND, OLIVOOILTR, OLIVTTR, VINEY, PGRAPM.",\n', '            "formula": "ARU per TYPE_OF_CROP nel dataflow DF_DCAT_CENSAGRIC2020_UA_CROPS_2: ARLAND, OLIVOOILTR, VINEY, PGRAPM.",\n'),
    ('            "caveat": "Una riga assente non è interpretata come zero. Vite: 6/7 (Forte dei Marmi n.d.). Olive da tavola: eccezione esplicitamente approvata 4/7 (Forte dei Marmi, Stazzema e Viareggio n.d.).",\n', '            "caveat": "Una riga assente non è interpretata come zero. Vite: 6/7 (Forte dei Marmi n.d.). Non sono pubblicate sottodimensioni con copertura inferiore a 6/7.",\n'),
    ('            "coverage": "7/7 seminativi, olivo da olio e prati/pascoli; 6/7 vite; 4/7 olive da tavola (eccezione approvata)",\n', '            "coverage": "7/7 seminativi, olivo da olio e prati/pascoli; 6/7 vite",\n'),
    ('    new_cov = old_cov + " Per sottodimensioni esplicitamente approvate prima della pubblicazione può essere ammessa una copertura inferiore: nel profilo colture 2020, *olive da tavola* è l\'eccezione documentata 4/7; le tre assenze restano `n.d.`."\n    if new_cov not in text:\n        text = text.replace(old_cov, new_cov)\n', '    # Nessuna eccezione sotto la soglia approvata 6/7.\n'),
    ('La copertura è 7/7 per aziende, SAU, dimensione media, irrigazione, seminativi, olivo da olio e prati/pascoli; 6/7 per la vite (Forte dei Marmi `n.d.`). Per la sola sottocategoria *olive da tavola* è stata approvata prima della pubblicazione un\'eccezione 4/7: Forte dei Marmi, Stazzema e Viareggio restano `n.d.`. Nessuna assenza viene trasformata in zero.', 'La copertura è 7/7 per aziende, SAU, dimensione media, irrigazione, seminativi, olivo da olio e prati/pascoli; 6/7 per la vite (Forte dei Marmi `n.d.`). Nessuna sottodimensione sotto 6/7 viene pubblicata e nessuna assenza viene trasformata in zero.'),
    ('    print("Agricoltura e territorio v1.20.0 materializzata: 5 indicatori canonici; OLIVTTR 4/7 esplicitamente documentato.")\n', '    print("Agricoltura e territorio v1.20.0 materializzata: 5 indicatori canonici; tutte le sottodimensioni pubblicate hanno copertura almeno 6/7.")\n'),
]

for old, new in replacements:
    if old in text:
        text = text.replace(old, new, 1)
    elif new and new in text:
        continue
    else:
        raise RuntimeError(f"Pattern non trovato nel materializzatore: {old[:120]}")

path.write_text(text, encoding="utf-8")
print("Perimetro agricoltura riallineato alla soglia minima 6/7.")
