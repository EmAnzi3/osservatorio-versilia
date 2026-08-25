#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data/site-data.json"
INPUT = ROOT / "review/mobilita-v6-preview-input.json"
PREVIEW_JS = ROOT / "assets/mobilita-v6-preview.js"
METRIC_KEY = "scheduledTplTripsPer1000"
SOURCE_URL = "https://dati.toscana.it/dataset/rt-oraritb"


def main() -> None:
    data = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    audit = json.loads(INPUT.read_text(encoding="utf-8"))
    theme = data["themes"]["mobilita"]
    combined = audit["gtfs"]["combined"]

    # Usa una metrica esistente come anagrafica canonica per codice e slug.
    template_rows = data["metrics"]["outsideMunicipality"]["rows"]
    identity = {row["town"]: {"code": row["code"], "slug": row["slug"]} for row in template_rows}

    rows = []
    for town, tpl in combined.items():
        ident = identity[town]
        value = tpl["tripsPer1000"] if tpl["status"] == "ok" else None
        rows.append({
            "town": town,
            "code": ident["code"],
            "slug": ident["slug"],
            "value": value,
            "formatted": None,
            "series": None,
            "normalized": None,
            "benchmarkValue": value,
            "tplOffer": tpl,
        })

        detail = data.setdefault("details", {}).setdefault(ident["code"], {})
        mobility = detail.setdefault("mobility", {})
        mobility["tplOffer"] = {
            **tpl,
            "serviceDate": audit["serviceDate"],
            "source": "Regione Toscana — GTFS Autolinee Toscane e Trenitalia",
        }

    # Mantiene l'ordine comunale già usato dal catalogo Mobilità.
    town_order = [row["town"] for row in template_rows]
    rows.sort(key=lambda row: town_order.index(row["town"]))
    valid = [row["value"] for row in rows if row["value"] is not None]
    aggregate = sum(valid) / len(valid) if valid else None

    data["metrics"][METRIC_KEY] = {
        "meta": {
            "key": METRIC_KEY,
            "theme": "mobilita",
            "label": "Corse TPL programmate ogni 1.000 residenti",
            "shortLabel": "Offerta TPL programmata",
            "description": "Corse di autobus e ferrovia programmate nel giorno di riferimento che servono almeno un punto di fermata utilizzabile dai passeggeri nel Comune, rapportate ai residenti.",
            "unit": "per1000",
            "year": "26 agosto 2026 · feriale estivo",
            "source": "Regione Toscana — GTFS programmato",
            "polarity": "neutral",
            "searchTerms": ["tpl", "trasporto pubblico", "autobus", "bus", "treno", "ferrovia", "corse", "fermate"],
        },
        "sourceUrl": SOURCE_URL,
        "rows": rows,
        "aggregate": {
            "value": aggregate,
            "label": "Media semplice dei 7 Comuni",
            "note": "Ogni Comune pesa allo stesso modo. Non equivale al numero di corse uniche della Versilia: una stessa corsa può servire più Comuni.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione GTFS Osservatorio Versilia",
            "formula": "Per il giorno di riferimento si selezionano i service_id attivi da calendar/calendar_dates. Una trip_id è contata una sola volta per Comune se serve almeno uno stop_id geolocalizzato nel territorio comunale in cui sia consentita salita o discesa. Si sommano autobus e ferrovia e si divide per i residenti × 1.000.",
            "caveat": "Fotografia del servizio programmato per mercoledì 26 agosto 2026: non misura puntualità, corse effettivamente svolte, capacità o passeggeri. I punti di fermata GTFS possono rappresentare separatamente direzioni o piattaforme. Gli orari oltre le 24:00 appartengono alla prosecuzione del giorno di servizio.",
            "coverage": "7/7",
        },
    }

    if METRIC_KEY not in theme["metrics"]:
        # Inserisce il TPL dopo i flussi di pendolarismo, prima dei mezzi privati.
        insert_at = theme["metrics"].index("motorization") if "motorization" in theme["metrics"] else len(theme["metrics"])
        theme["metrics"].insert(insert_at, METRIC_KEY)

    tpl_section = {
        "key": "trasporto-pubblico",
        "label": "Trasporto pubblico",
        "description": "Offerta programmata di autobus e ferrovia misurata su GTFS ufficiali, con dettaglio su corse, punti di fermata e ampiezza oraria.",
        "metrics": [METRIC_KEY],
    }
    theme["sections"] = [section for section in theme.get("sections", []) if section.get("key") != "trasporto-pubblico"]
    pend_idx = next((i for i, section in enumerate(theme["sections"]) if section.get("key") == "pendolarismo"), -1)
    theme["sections"].insert(pend_idx + 1, tpl_section)
    theme["description"] = "Pendolarismo, trasporto pubblico, parco veicolare, ricarica elettrica, connettività digitale e mobilità lenta."

    # Aggiorna solo i metadata della pagina Mobilità per coerenza con il tema corrente.
    mobility_page = ROOT / "confronta/mobilita/index.html"
    html = mobility_page.read_text(encoding="utf-8")
    html = html.replace("Mobilità e sicurezza · Confronto dei comuni della Versilia", "Mobilità e infrastrutture · Confronto dei comuni della Versilia")
    html = html.replace("Pendolarismo, parco veicolare, incidenti stradali e contesto provinciale della criminalità.", "Pendolarismo, trasporto pubblico, parco veicolare, ricarica elettrica, connettività digitale e mobilità lenta.")
    if "mobilita-v6-preview.js" not in html:
        html = html.replace("</body>", '  <script src="../../assets/mobilita-v6-preview.js" defer></script>\n</body>')
    mobility_page.write_text(html, encoding="utf-8")

    # La scheda comunale usa la UI corrente; il piccolo modulo aggiunge soltanto il dettaglio TPL al deep dive esistente.
    for town_page in (ROOT / "comuni").glob("*/index.html"):
        html = town_page.read_text(encoding="utf-8")
        if "mobilita-v6-preview.js" not in html:
            html = html.replace("</body>", '  <script src="../../assets/mobilita-v6-preview.js" defer></script>\n</body>')
            town_page.write_text(html, encoding="utf-8")

    SITE_DATA.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    PREVIEW_JS.write_text(preview_js(), encoding="utf-8")

    manifest = {
        "metricKey": METRIC_KEY,
        "themeMetricCountBefore": len(theme["metrics"]) - 1,
        "themeMetricCountPreview": len(theme["metrics"]),
        "canonicalMetricCountBefore": 146,
        "canonicalMetricCountIfPromoted": 147,
        "serviceDate": audit["serviceDate"],
        "coverage": "7/7",
        "populationInsistence": audit["istatPopulationInsistence"],
        "notes": [
            "Preview costruita sul renderer reale del sito, non su un HTML autonomo.",
            "Un solo candidato TPL è aggiunto al catalogo; fermate, bus/ferrovia e ampiezza oraria restano dettagli.",
            "La popolazione insistente Istat resta sospesa e non viene inserita nella preview.",
        ],
    }
    (ROOT / "review/mobilita-v6-preview-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def preview_js() -> str:
    return r'''(() => {
  'use strict';
  const script = document.currentScript;
  const inputUrl = new URL('../review/mobilita-v6-preview-input.json', script.src);
  const metricKey = 'scheduledTplTripsPer1000';
  const slugToTown = {
    'massarosa': 'Massarosa', 'viareggio': 'Viareggio', 'camaiore': 'Camaiore',
    'pietrasanta': 'Pietrasanta', 'seravezza': 'Seravezza',
    'forte-dei-marmi': 'Forte dei Marmi', 'stazzema': 'Stazzema'
  };

  const fmt0 = value => new Intl.NumberFormat('it-IT', { maximumFractionDigits: 0 }).format(value);
  const fmt1 = value => new Intl.NumberFormat('it-IT', { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(value);
  function clock(value) {
    if (!value) return 'n.d.';
    const [rawHour, minute] = value.split(':').map(Number);
    if (rawHour < 24) return `${String(rawHour).padStart(2,'0')}:${String(minute).padStart(2,'0')}`;
    const day = Math.floor(rawHour / 24);
    const hour = rawHour % 24;
    return `${String(hour).padStart(2,'0')}:${String(minute).padStart(2,'0')} (+${day} giorno${day > 1 ? 'i' : ''})`;
  }

  function detailMarkup(row) {
    const railZero = row.railTrips === 0;
    return `<details class="detail-disclosure tpl-offer-detail">
      <summary><span>Mostra il dettaglio dell’offerta TPL</span><small>Feriale estivo · 26 agosto 2026</small></summary>
      <div class="deep-columns">
        <div><h4>Corse programmate</h4><ul class="deep-list deep-list--flows">
          <li><span>Totale bus + ferrovia</span><span class="deep-list-value"><strong>${fmt0(row.trips)}</strong><small>corse</small></span></li>
          <li><span>Autobus</span><span class="deep-list-value"><strong>${fmt0(row.busTrips)}</strong><small>corse</small></span></li>
          <li><span>Ferrovia</span><span class="deep-list-value"><strong>${fmt0(row.railTrips)}</strong><small>corse</small></span></li>
        </ul></div>
        <div><h4>Accesso e finestra oraria</h4><ul class="deep-list deep-list--flows">
          <li><span>Punti di fermata GTFS attivi</span><span class="deep-list-value"><strong>${fmt0(row.activeAccessPoints)}</strong><small>stop_id serviti</small></span></li>
          <li><span>Prima corsa utile</span><span class="deep-list-value"><strong>${clock(row.first)}</strong><small>giorno di servizio</small></span></li>
          <li><span>Ultima corsa utile</span><span class="deep-list-value"><strong>${clock(row.last)}</strong><small>giorno di servizio</small></span></li>
          <li><span>Intervallo prima–ultima</span><span class="deep-list-value"><strong>${fmt1(row.serviceSpanHours)} h</strong><small>non misura la frequenza</small></span></li>
        </ul></div>
      </div>
      <p class="aggregate-note">Una corsa è contata una sola volta nel Comune anche se effettua più fermate. Il dato descrive il servizio programmato, non puntualità o utilizzo.${railZero ? ' Il valore ferroviario 0 è effettivo nel perimetro comunale del feed e non è un dato mancante.' : ''}</p>
    </details>`;
  }

  fetch(inputUrl, { cache: 'no-store' }).then(r => r.json()).then(audit => {
    const apply = () => {
      const params = new URLSearchParams(location.search);
      if (params.get('indicatore') !== metricKey || document.body.dataset.page !== 'town') return;
      const town = slugToTown[document.body.dataset.town];
      const row = audit.gtfs.combined[town];
      if (!row || document.querySelector('.tpl-offer-detail')) return;
      const deep = document.querySelector('.topic-deep-dive');
      if (!deep) return;
      const heading = deep.querySelector('.deep-heading h3');
      const desc = deep.querySelector('.deep-heading p');
      if (heading) heading.textContent = 'Flussi e trasporto pubblico';
      if (desc) desc.textContent = 'Pendolarismo rilevato dal censimento e offerta TPL programmata. Le due letture descrivono fenomeni diversi e non vanno confuse con domanda o qualità del servizio.';
      deep.insertAdjacentHTML('beforeend', detailMarkup(row));
    };
    apply();
    new MutationObserver(apply).observe(document.getElementById('app'), { childList: true, subtree: true });
  }).catch(console.error);
})();
'''


if __name__ == "__main__":
    main()
