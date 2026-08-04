#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUT = Path("v12-omi-results")
OUT.mkdir(exist_ok=True)
S = requests.Session()
S.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; OsservatorioVersiliaDataAudit/1.2; +https://github.com/EmAnzi3/osservatorio-versilia)",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.6",
})
SEARCH = "https://www1.agenziaentrate.gov.it/servizi/Consultazione/ricerca.htm"
RESULT = "https://www1.agenziaentrate.gov.it/servizi/Consultazione/risultato.php"
CODES = {
    "camaiore": "B455", "forte-dei-marmi": "D730", "massarosa": "F035",
    "pietrasanta": "G628", "seravezza": "I622", "stazzema": "I942", "viareggio": "L833",
}
records = []
for town, code in CODES.items():
    step2 = S.post(SEARCH, data={"level":"2","lingua":"IT","pr":"LU","anno_semestre":"20252","co":code}, timeout=(30,120), verify=False)
    soup2 = BeautifulSoup(step2.content, "html.parser")
    select = soup2.find("select", attrs={"name":"linkzonastrada"})
    if not select:
        records.append({"town":town,"error":"zone selector missing"})
        continue
    for index, option in enumerate(select.find_all("option"), start=1):
        zone = option.get("value")
        if not zone: continue
        step4 = S.post(SEARCH, data={"level":"4","lingua":"IT","pr":"LU","co":code,"anno_semestre":"20252","linkzonastrada":zone}, timeout=(30,120), verify=False)
        soup4 = BeautifulSoup(step4.content, "html.parser")
        form = soup4.find("form", action="risultato.php")
        if not form:
            records.append({"town":town,"zone":zone,"error":"result form missing"})
            continue
        payload = {el.get("name"): el.get("value", "") for el in form.find_all("input") if el.get("name")}
        payload.update({"utilizzo":"Residenziale", "bt1":"Mostra valori"})
        result = S.post(RESULT, data=payload, timeout=(30,120), verify=False)
        path = OUT / f"omi-residential-{town}-{index:02d}-{zone}.html"
        path.write_bytes(result.content)
        records.append({"town":town,"zone":zone,"zone_label":option.get_text(" ",strip=True),"status":result.status_code,"size":len(result.content),"path":str(path)})
        print(town, zone, result.status_code, len(result.content), flush=True)
(OUT/"summary.json").write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
