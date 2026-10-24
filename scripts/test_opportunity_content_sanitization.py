#!/usr/bin/env python3
from __future__ import annotations

import html
import re

from opportunity_daily_refresh import _contamination_offset, _sanitize_public_content
import build_opportunity_preview as preview

# Ruoli osservati nello snapshot Radar pubblicato il 24 ottobre 2026: slug liberi
# degli overlay audit/matrice, prima esposti come testo inglese nelle schede.
OBSERVED_ROLE_SLUGS = {
    "direct_local_authority_applicant_singly_or_jointly": "Candidatura diretta, singola o associata",
    "beneficiary_local_authority_preparing_a_support_request_routed_via_the_Italian_National_Coordinating_Authority": "Richiesta di assistenza tecnica",
    "conditional_site_proponent_or_managing_authority_for_an_eligible_site": "Partner con sito o bene dimostrativo (a condizioni)",
    "local_authority_delegate_in_long_term_cities_regions_network": "Rappresentante dell’ente",
    "direct_waterfront_local_authority_member_receiving_structured_capacity_building_and_peer_support": "Adesione a rete o comunità",
    "direct_local_authority_borrower_subject_to_project_and_credit_appraisal": "Ente mutuatario",
    "direct_local_authority_technical_assistance_applicant": "Richiesta di assistenza tecnica",
    "conditional_public_procurer_in_ppi_buyer_group": "Acquirente pubblico in gruppo d’acquisto (a condizioni)",
    "municipal_civil_protection_authority_can_serve_as_required_practitioner_beneficiary_when_proposal_focus_matches": "Autorità di protezione civile partecipante",
    "public_space_planning_procurement_or_demo_neighbourhood_partner": "Partner con sito o bene dimostrativo",
    "public_legal_entity_project_promoter_seeking_investor_visibility_and_financing_matchmaking": "Promotore di progetto in cerca di finanziamento",
    "direct_municipality_requester_for_free_state_asset_transfer": "Richiesta di trasferimento di beni",
    "conditional_partner_or_lead": "Partecipazione come partner (a condizioni)",
    "direct_city_or_city_consortium": "Candidatura diretta",
    "public_body_scope_review": "Ruolo da verificare nella fonte ufficiale",
}
_ENGLISH = re.compile(r"\b(local|authority|applicant|beneficiary|direct|support|request|network|member|the|and|or)\b", re.I)


def _role_labels_are_italian() -> None:
    for role, expected in OBSERVED_ROLE_SLUGS.items():
        item = {"title": "Scheda", "municipality_role": role, "applicant_type": role.replace("_", " ")}
        card = html.unescape(preview.card_markup(item))
        shown_role = re.search(r"<dt>Ruolo del Comune</dt><dd>(.*?)</dd>", card).group(1)
        shown_applicant = re.search(r"<dt>Chi presenta domanda</dt><dd>(.*?)</dd>", card).group(1)
        assert shown_role == expected, (role, shown_role)
        for text in (shown_role, shown_applicant):
            assert "_" not in text and not _ENGLISH.search(text), (role, text)
    # Un testo libero italiano del proponente resta quello della fonte verificata.
    kept = {"municipality_role": "partner", "applicant_type": "Pro Loco iscritte al Registro regionale 2026"}
    assert "Pro Loco iscritte al Registro regionale 2026" in preview.card_markup(kept)
    assert "Comune o ente locale" in preview.card_markup({"municipality_role": "direct_applicant", "applicant_type": "local_authority"})
    # Un ruolo nuovo e non classificabile non espone lo slug: rinvia alla fonte.
    unknown = html.unescape(preview.card_markup({"municipality_role": "zz_unmapped_role", "applicant_type": "zz unmapped role"}))
    assert "zz" not in unknown.split('<h3>', 1)[1].split('Comuni della Versilia', 1)[0].replace('data-', '')


def _item(summary: str, beneficiary: str = "I Comuni toscani possono presentare domanda.") -> dict:
    return {
        "id": "opp-parcheggi",
        "coverage_id": "rt-parcheggi-2026",
        "title": "Bando parcheggi 2026",
        "summary": summary,
        "beneficiary_text": beneficiary,
    }


def main() -> int:
    clean_summary = "Contributi regionali per parcheggi pubblici."
    previous = {"opportunities": [_item(clean_summary)]}
    noise = (
        ' function proxyOpenDialog(event, dataId, button) { document.getElementById("x"); } '
        "60 Elementi Per pagina"
    )
    current = {
        "opportunities": [
            _item(clean_summary + noise, "I Comuni toscani possono presentare domanda." + noise),
            {
                "id": "opp-nuovo",
                "title": "Nuova opportunita",
                "summary": "Testo valido prima del codice" + noise,
                "beneficiary_text": "Enti locali",
            },
        ],
        "counts": {},
    }

    repaired = _sanitize_public_content(current, previous)
    assert len(repaired) == 2, repaired
    assert current["opportunities"][0]["summary"] == clean_summary
    assert current["opportunities"][0]["beneficiary_text"] == "I Comuni toscani possono presentare domanda."
    assert current["opportunities"][1]["summary"] == "Testo valido prima del codice"
    assert current["contentSanitization"]["repairedCount"] == 2
    assert current["counts"]["contentSanitized"] == 2
    for item in current["opportunities"]:
        assert _contamination_offset(item.get("summary")) is None
        assert _contamination_offset(item.get("beneficiary_text")) is None

    assert _contamination_offset("Testo istituzionale pulito") is None
    assert _contamination_offset("document.getElementById('x')") == 0
    _role_labels_are_italian()
    print("Sanificazione contenuti Radar: PASS (incluse etichette italiane dei ruoli)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
