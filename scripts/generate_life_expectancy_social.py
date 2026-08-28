#!/usr/bin/env python3
"""Carosello lifeExpectancy basato solo sui dati canonici della repository."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import generate_social_kit as r

ROOT = Path(__file__).resolve().parents[1]
SEXES = ("totale", "maschi", "femmine")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fy(value, signed=False):
    prefix = "+" if signed and value > 0 else ""
    return f"{prefix}{r.fmt_it(float(value), 1)} anni"


def pmap(parts):
    return {part["key"]: part for part in parts}


def get_model():
    site = load(ROOT / "data" / "site-data.json")
    metric = site["metrics"]["lifeExpectancy"]
    if metric["meta"].get("compositeType") != "sexBreakdown" or len(metric["rows"]) != 7:
        raise ValueError("lifeExpectancy: contratto sexBreakdown/7 comuni non rispettato")
    aggregate_parts = pmap(metric["aggregate"]["parts"])
    if not all(key in aggregate_parts for key in SEXES):
        raise ValueError("lifeExpectancy: aggregato ARS senza Totale/Maschi/Femmine")
    rows = []
    for row in sorted(metric["rows"], key=lambda item: item["town"].casefold()):
        parts = pmap(row["parts"])
        if not all(key in parts for key in SEXES):
            raise ValueError(f"lifeExpectancy: parti per sesso mancanti in {row['town']}")
        rows.append({"town": row["town"], "value": float(parts["totale"]["value"]), "parts": parts})
    years = [int(x) for x in aggregate_parts["totale"]["series"]["years"]]
    if years != list(range(2008, 2023)):
        raise ValueError("lifeExpectancy: serie aggregata diversa da 2008–2022")
    meta = metric["meta"]
    return metric, {
        "dataset_path": "data/site-data.json",
        "dataset_version": site["version"],
        "dataset_updated": site.get("updated"),
        "dataset_status": "published",
        "metric": "lifeExpectancy",
        "theme": meta["theme"],
        "label": meta["label"],
        "short_label": meta.get("shortLabel") or meta["label"],
        "description": meta["description"],
        "unit": "years",
        "year": int(meta["year"]),
        "year_label": "2008–2022",
        "source": meta["source"],
        "source_url": metric["sourceUrl"],
        "method": metric.get("method", {}),
        "rows": rows,
        "aggregate": {"value": float(aggregate_parts["totale"]["value"]), "parts": aggregate_parts, "label": metric["aggregate"].get("label"), "note": metric["aggregate"].get("note")},
        "link": "https://osservatorioversilia.it/confronta/salute/?indicatore=lifeExpectancy",
    }


def current_slide(parts, box, model, theme):
    x, y, w, h = box["x"], box["y"], box["width"], box["height"]
    ref = model["aggregate"]["value"]
    rows = model["rows"]
    values = [row["value"] for row in rows] + [ref]
    spread = max(values) - min(values)
    lo, hi = min(values) - max(.35, spread * .1), max(values) + max(.35, spread * .1)
    hero = y + 28
    parts += [
        f'<rect x="{x+32}" y="{hero}" width="{w-64}" height="128" rx="24" fill="{theme["accent"]}"/>',
        f'<text x="{x+68}" y="{hero+37}" class="hero-label white">ZONA VERSILIA · AGGREGATO UFFICIALE ARS</text>',
        r.fitted_text(fy(ref), x+66, hero+101, 380, 58, "white", 56, 38, 1, "aggregate-current", "#FFFFFF"),
        r.fitted_text("speranza di vita · Totale", x+465, hero+91, 360, 42, "white", 19, 16, 2, "aggregate-description", "#FFFFFF"),
        f'<text x="{x+w-64}" y="{hero+39}" class="white" style="font-size:18px;font-weight:650" text-anchor="end">2022</text>',
        f'<text x="{x+36}" y="{y+195}" class="section" fill="{theme["accent"]}">I SETTE COMUNI · TOTALE 2022</text>',
    ]
    cx, cw, vx = x+355, 360, x+w-36
    start, step = y+222, 58
    rx = cx + cw * (ref-lo)/(hi-lo)
    parts += [
        f'<line x1="{rx:.1f}" x2="{rx:.1f}" y1="{start-8}" y2="{start+(len(rows)-1)*step+30}" stroke="{theme["accent"]}" stroke-width="3" stroke-dasharray="7 7" opacity=".55"/>',
        f'<text x="{rx:.1f}" y="{start-22}" class="axis" text-anchor="middle">Versilia {r.fmt_it(ref,1)}</text>',
    ]
    for i, row in enumerate(rows):
        cy = start + i*step
        px = cx + cw * (row["value"]-lo)/(hi-lo)
        parts += [
            f'<text x="{x+36}" y="{cy+21}" class="label">{r.esc(row["town"])}</text>',
            f'<line x1="{cx}" x2="{cx+cw}" y1="{cy+11}" y2="{cy+11}" stroke="#D8DFDC" stroke-width="3" stroke-linecap="round"/>',
            f'<circle cx="{px:.1f}" cy="{cy+11}" r="10" fill="{theme["accent"]}" stroke="#FFF9F2" stroke-width="4"/>',
            f'<text data-role="numeric-value" x="{vx}" y="{cy+22}" class="number" text-anchor="end">{fy(row["value"])}</text>',
        ]
    parts.append(f'<text x="{x+36}" y="{y+h-24}" class="small">Linea tratteggiata: Zona Versilia pubblicata direttamente da ARS.</text>')


def sex_slide(parts, box, model, theme):
    x, y, w, h = box["x"], box["y"], box["width"], box["height"]
    pm = model["aggregate"]["parts"]
    vals = [float(pm[key]["value"]) for key in SEXES]
    gap = float(pm["femmine"]["value"]) - float(pm["maschi"]["value"])
    lo, hi = min(vals)-.7, max(vals)+.7
    hero = y+28
    parts += [
        f'<rect x="{x+32}" y="{hero}" width="{w-64}" height="126" rx="24" fill="{theme["accent"]}"/>',
        f'<text x="{x+68}" y="{hero+37}" class="hero-label white">ZONA VERSILIA · 2022</text>',
        r.fitted_text(fy(gap), x+66, hero+96, 300, 48, "white", 42, 30, 1, "sex-gap", "#FFFFFF"),
        r.fitted_text("differenza tra valore femminile e maschile", x+385, hero+88, 445, 42, "white", 18, 15, 2, "sex-gap-label", "#FFFFFF"),
        f'<text x="{x+36}" y="{y+195}" class="section" fill="{theme["accent"]}">TOTALE · MASCHI · FEMMINE</text>',
    ]
    labels = {"totale":"Totale", "maschi":"Maschi", "femmine":"Femmine"}
    cx, cw, start, step = x+245, w-500, y+270, 112
    for i, key in enumerate(SEXES):
        value = float(pm[key]["value"])
        cy = start+i*step
        px = cx+cw*(value-lo)/(hi-lo)
        parts += [
            f'<text x="{x+54}" y="{cy+9}" class="label">{labels[key]}</text>',
            f'<line x1="{cx}" x2="{cx+cw}" y1="{cy}" y2="{cy}" stroke="#D8DFDC" stroke-width="5" stroke-linecap="round"/>',
            f'<circle cx="{px:.1f}" cy="{cy}" r="13" fill="{theme["accent"]}" stroke="#FFF9F2" stroke-width="4"/>',
            f'<text x="{x+w-54}" y="{cy+10}" class="number" text-anchor="end">{fy(value)}</text>',
        ]
    parts += [
        r.fitted_text("Totale, Maschi e Femmine sono disponibili nella repository per tutti i sette Comuni e per ogni anno dal 2008 al 2022.", x+54, y+610, w-108, 85, "body", 21, 17, 3, "sex-note"),
        f'<text x="{x+36}" y="{y+h-24}" class="small">Valori dell’aggregato ufficiale Zona Versilia ARS.</text>',
    ]


def platform_copy(model):
    pm = model["aggregate"]["parts"]
    total, male, female = [float(pm[key]["value"]) for key in SEXES]
    series = pm["totale"]["series"]
    start = float(series["values"][0])
    delta, gap = total-start, female-male
    fact = f"Zona Versilia ARS: speranza di vita {fy(total)} nel 2022."
    hist = f"Serie 2008–2022: da {fy(start)} a {fy(total)} ({fy(delta, True)})."
    sex = f"Nel 2022: Maschi {fy(male)}, Femmine {fy(female)}; differenza {fy(gap)}."
    method = "L’aggregato Versilia è pubblicato direttamente da ARS: non è una media calcolata sui sette Comuni."
    q = "Quanto ti sorprende la differenza tra uomini e donne? Quale Comune vorresti seguire lungo tutta la serie storica?"
    link = f"Dati, grafici, metodo e fonte: {model['link']}"
    source = f"Fonte: {model['source']} · 2008–2022 · dati {model['dataset_version']}"
    master = "\n\n".join([fact,hist,sex,method,q,link,source])
    fb = "\n\n".join([f"📊 {fact}",hist,sex,method,f"💬 {q}",link,source]) + "\n\n#OsservatorioVersilia #Versilia #Salute"
    ig = "\n\n".join(["Scorri il carosello →",fact,hist,sex,"I grafici usano esclusivamente i dati già pubblicati nell’Osservatorio.",f"💬 {q}",f"Approfondisci: {model['link']}",source]) + "\n\n#OsservatorioVersilia #Versilia #Salute #DatiPubblici"
    li = "\n\n".join(["La speranza di vita in Versilia ora può essere letta anche nel tempo e per sesso, mantenendo la stessa fonte ARS.",fact,hist,sex,method,"Il dato descrive le condizioni di mortalità osservate: non è una previsione individuale e non spiega da solo le differenze territoriali.",q,link,source]) + "\n\n#OsservatorioVersilia #DatiPubblici #Salute"
    xt = f"Zona Versilia ARS 2022: {r.fmt_it(total,1)} anni. Maschi {r.fmt_it(male,1)}, Femmine {r.fmt_it(female,1)}; 2008→2022: {r.fmt_it(start,1)}→{r.fmt_it(total,1)}. {model['link']} #Versilia"
    if len(xt) > 280:
        raise ValueError("Copy X lifeExpectancy oltre 280 caratteri")
    return {"master":master,"facebook":fb,"instagram":ig,"linkedin":li,"x":xt}


def generate_post(post, design, themes, destination):
    metric, model = get_model()
    if post.get("metric") != "lifeExpectancy" or post.get("theme") != "salute":
        raise ValueError("Renderer lifeExpectancy invocato su un post non coerente")
    theme = themes["themes"]["salute"]
    pm = model["aggregate"]["parts"]
    years = [int(x) for x in pm["totale"]["series"]["years"]]
    history = [float(x) for x in pm["totale"]["series"]["values"]]
    delta = history[-1]-history[0]
    comp = {"label":"Zona Versilia ARS · 2008–2022","delta":delta,"display":delta,"display_unit":"years"}
    titles = ["Speranza di vita","Andamento storico","Totale, maschi e femmine","Cosa vedi nel tuo Comune?"]
    subtitles = ["Sette Comuni e Zona Versilia ARS · Totale 2022","Zona Versilia ARS · Totale · 2008–2022","Zona Versilia ARS · 2022","I numeri aprono la conversazione. Il territorio la completa."]
    questions = ["Quanto ti sorprende la differenza tra uomini e donne nella speranza di vita?","Quale Comune vorresti seguire lungo tutta la serie 2008–2022?"]
    qpost = {**post,"questions":questions}
    specs = [
        ("01-dato-attuale",lambda p,b: current_slide(p,b,model,theme),"Speranza di vita alla nascita, Totale 2022. Zona Versilia ARS " + fy(model["aggregate"]["value"]) + ". Valori comunali: " + "; ".join(f"{row['town']} {fy(row['value'])}" for row in model["rows"]) + "."),
        ("02-andamento-storico",lambda p,b: r.history_slide(p,b,model,years,history,comp,theme),"Andamento storico Zona Versilia ARS, Totale, 2008–2022: " + "; ".join(f"{year} {fy(value)}" for year,value in zip(years,history)) + "."),
        ("03-genere",lambda p,b: sex_slide(p,b,model,theme),f"Zona Versilia ARS 2022 per sesso: Totale {fy(pm['totale']['value'])}; Maschi {fy(pm['maschi']['value'])}; Femmine {fy(pm['femmine']['value'])}. Serie per sesso disponibile 2008–2022 per tutti i sette Comuni."),
        ("04-partecipa",lambda p,b: r.questions_slide(p,design,qpost,theme),"Due domande aperte sulla differenza tra uomini e donne e sulla serie storica 2008–2022, con invito a commentare indicando il Comune."),
    ]
    cards=[]
    for i,(name,draw,alt) in enumerate(specs,1):
        svg=r.make_page(i,titles[i-1],subtitles[i-1],model,qpost,design,theme,draw)
        svg_path=destination/"cards"/f"{name}.svg"; png_path=destination/"cards"/f"{name}.png"
        r.write(svg_path,svg); r.render_png(svg_path,png_path,design["format"]["width"],design["format"]["height"]); r.write(destination/"alt"/f"{name}.txt",alt+"\n")
        cards.append({"slide":i,"filename":name,"title":titles[i-1],"alt":alt})
    for platform,text in platform_copy(model).items(): r.write(destination/"testi"/f"{platform}.txt",text+"\n")
    provenance={"status":"draft","post_id":post["id"],"date":post["date"],"priority":post["priority"],"design_system":design["version"],"theme":"salute","palette":{"accent":theme["accent"],"soft":theme["soft"]},"dataset":{"path":model["dataset_path"],"version":model["dataset_version"],"status":"published","updated":model["dataset_updated"]},"metric":"lifeExpectancy","source":model["source"],"source_url":model["source_url"],"method":model["method"],"current_year":model["year"],"current_values":{row["town"]:row["value"] for row in model["rows"]},"aggregate":{"type":"official-source","value":model["aggregate"]["value"],"note":model["aggregate"]["note"]},"history":{str(y):v for y,v in zip(years,history)},"sex_current":{key:float(pm[key]["value"]) for key in SEXES},"questions":questions,"generated_at":datetime.now(timezone.utc).isoformat(timespec="seconds")}
    r.write(destination/"provenienza.json",json.dumps(provenance,ensure_ascii=False,indent=2)+"\n")
    manifest={"status":"draft","method":"four-slide-carousel","design_system":design["version"],"post_id":post["id"],"date":post["date"],"format":"1080x1350","platforms":design["format"]["platforms"],"outputs":["png","svg"],"cards":cards}
    r.write(destination/"manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    return manifest
