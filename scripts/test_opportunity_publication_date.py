#!/usr/bin/env python3
"""Data ufficiale di pubblicazione: estrazione dalla pagina, date curate e riga sulla scheda."""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_opportunity_preview_v044 as ui
import opportunity_publication_date as pd

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 11, 22)


def test_metadata_wins() -> None:
    raw = ('<script type="application/ld+json">{"@type":"NewsArticle","datePublished":"2026-11-11T09:30:00+01:00"}</script>'
           '<meta property="article:published_time" content="2026-11-12T10:00:00Z">')
    assert pd.publication_date(raw, "Pubblicato il 13 novembre 2026", TODAY) == ("2026-11-11", "metadati della pagina (datePublished)")
    raw = '<meta property="article:published_time" content="2026-11-12T10:00:00Z">'
    assert pd.publication_date(raw, "", TODAY)[0] == "2026-11-12"
    raw = '<meta name="DC.date.issued" content="2026-10-03">'
    assert pd.publication_date(raw, "", TODAY)[0] == "2026-10-03"


def test_text_labels() -> None:
    for text, expected in (("Data di pubblicazione: 12/11/2026 Ultimo aggiornamento 20/11/2026", "2026-11-12"),
                           ("Pubblicato il 3 giugno 2026 alle 10:00", "2026-06-03"),
                           ("Data pubblicazione 05.10.2026", "2026-10-05"),
                           ("Pubblicato il: martedì 11 novembre 2026", "2026-11-11")):
        assert pd.publication_date("", text, TODAY)[0] == expected, text


def test_no_date_rather_than_a_wrong_one() -> None:
    # Data futura, troppo vecchia, solo «aggiornato», o diciture discordanti: nessuna data.
    assert pd.publication_date("", "Pubblicato il 30 novembre 2026", TODAY) == (None, "")
    assert pd.publication_date("", "Pubblicato il 3 giugno 2023", TODAY) == (None, "")
    assert pd.publication_date("", "Ultimo aggiornamento 20/11/2026", TODAY) == (None, "")
    assert pd.publication_date("", "Pubblicato il 12/11/2026. Allegato pubblicato il 15/11/2026", TODAY) == (None, "")
    assert pd.publication_date('<meta property="article:published_time" content="2027-01-01">', "", TODAY) == (None, "")


def test_overlay_fills_only_missing_dates() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "data").mkdir()
        (Path(tmp) / pd.OVERLAY).write_text(json.dumps({"entries": [
            {"coverage_id": "a", "published_at": "2026-08-13", "evidence": "Avviso del 13/08", "evidence_url": "https://x"},
            {"coverage_id": "b", "published_at": "2026-01-01", "evidence": "x", "evidence_url": "https://x"}]}), encoding="utf-8")
        result = {"opportunities": [{"coverage_id": "a"}, {"coverage_id": "b", "published_at": "2026-02-02"}, {"coverage_id": "c"}]}
        assert pd.apply_overlay(result, tmp) == 1
        a, b, c = result["opportunities"]
        assert a["published_at"] == "2026-08-13" and "13/08" in a["published_at_evidence"]
        assert b["published_at"] == "2026-02-02" and "published_at" not in c


def test_overlay_file_is_consistent() -> None:
    doc = json.loads((ROOT / pd.OVERLAY).read_text(encoding="utf-8"))
    ids = [e["coverage_id"] for e in doc["entries"]]
    assert len(ids) == len(set(ids))
    for e in doc["entries"]:
        assert date.fromisoformat(e["published_at"]) <= date.fromisoformat(doc["verifiedAt"]), e
        assert e["evidence_url"].startswith("https://") and e["evidence"], e


def test_card_line() -> None:
    line = ui.publication_line({"published_at": "2026-11-12", "first_seen_at": "2026-11-13", "published_at_evidence": "Testo «x»"})
    assert ">Pubblicato il 12/11/2026 · nel Radar dal 13/11/2026<" in line and 'title="Testo «x»"' in line
    assert ">Data di pubblicazione non indicata dalla fonte · nel Radar dal 13/11/2026<" in ui.publication_line({"first_seen_at": "2026-11-13"})
    assert ">Data di pubblicazione non indicata dalla fonte<" in ui.publication_line({})


def main() -> int:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("Data di pubblicazione Radar: 6 test PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
