#!/usr/bin/env python3
"""Completa il replay pubblico usando la matrice municipale finale v1.

Il replay generico ricava automaticamente i finding semplici dalle Wave. Questa
coda deterministica applica la decisione finale della matrice 2026-09-08 ai casi
che il formato storico delle Wave non consente di materializzare correttamente:
matrici multi-topic, record senza URL ereditato e riclassificazioni finali.
"""
from __future__ import annotations

import hashlib
from datetime import date
from typing import Any
from urllib.parse import urlsplit

import opportunity_audit_corpus_promotions as base
import opportunity_municipal_relevance as relevance

PROMOTION_VERSION = "municipal-matrix-v1-20260908"
MATRIX_CURRENT_TARGET = 89  # 52 municipali + 37 partnership, tutte nuove vs snapshot 7/9.
MUNICIPALITIES = list(base.MUNICIPALITIES)

# Questi record erano contenitori o controlli, non schede pubbliche atomiche.
_SUPPRESS_IDS = {
    "horizon-miss-2026-04-cit-matrix",
    "horizon-neb-facility-2026-matrix",
    "horizon-cl3-2026-01-drs-04",
}

# Decisioni finali della matrice su schede già materializzate dal replay generico.
_RECLASSIFY = {
    "life-2026-clima-sap-cca": relevance.DIRECT_CONDITIONAL,
    "life-2026-sap-clima-gov": relevance.DIRECT_CONDITIONAL,
    "life-2026-sap-env-environment": relevance.DIRECT_CONDITIONAL,
    "eit-urban-mobility-ris-education-2027": relevance.DIRECT_CONDITIONAL,
    "mic-european-heritage-label-2027": relevance.DIRECT_CONDITIONAL,
}

_PATCHES: dict[str, dict[str, Any]] = {
    "eit-urban-mobility-ris-education-2027": {
        "deadline_at": "2026-09-16",
        "audit_class": "current_conditional_beneficiary_false_negative",
    },
    "mic-fondo-carnevali-storici-2026": {
        "municipality_eligibility": {
            "Camaiore": {"status": "ineligible", "reason": "Non è stato documentato il requisito di organizzatore qualificato del Carnevale storico per la candidatura comunale 2026."},
            "Forte dei Marmi": {"status": "ineligible", "reason": "Non è stato documentato il requisito di organizzatore qualificato del Carnevale storico per la candidatura comunale 2026."},
            "Massarosa": {"status": "ineligible", "reason": "Non è stato documentato il requisito di organizzatore qualificato del Carnevale storico per la candidatura comunale 2026."},
            "Pietrasanta": {"status": "conditional", "reason": "Comune di Pietrasanta è un controllo positivo documentato dal ciclo 2025; verificare il mantenimento dei requisiti organizzativi nella domanda 2026."},
            "Seravezza": {"status": "ineligible", "reason": "Non è stato documentato il requisito di organizzatore qualificato del Carnevale storico per la candidatura comunale 2026."},
            "Stazzema": {"status": "ineligible", "reason": "Non è stato documentato il requisito di organizzatore qualificato del Carnevale storico per la candidatura comunale 2026."},
            "Viareggio": {"status": "ineligible", "reason": "Nel controllo 2025 il soggetto richiedente/beneficiario era Fondazione Carnevale di Viareggio, non il Comune."},
        }
    },
}


def _spec(
    coverage_id: str,
    title: str,
    relevance_class: str,
    url: str,
    *,
    deadline: str | None = None,
    opens: str | None = None,
    role: str,
    reason: str,
    funding: str | None = None,
    lifecycle: str | None = None,
) -> dict[str, Any]:
    return {
        "coverage_id": coverage_id,
        "title": title,
        "municipal_relevance_class": relevance_class,
        "url": url,
        "deadline_at": deadline,
        "opens_at": opens,
        "municipality_role": role,
        "reason": reason,
        "funding": funding,
        "lifecycle": lifecycle,
    }


_SPECS: list[dict[str, Any]] = [
    # DIRECT_CONDITIONAL mancanti dal replay generico.
    _spec(
        "eu-natura2000-award-2027-edition",
        "European Natura 2000 Award · Towns & cities",
        relevance.DIRECT_CONDITIONAL,
        "https://environment.ec.europa.eu/topics/nature-and-biodiversity/natura-2000-award/application-process_en",
        deadline="2026-10-16",
        role="conditional_direct_applicant",
        reason="Enti pubblici ammissibili; la categoria Towns & cities richiede un'iniziativa pertinente in siti Natura 2000 urbani o periurbani.",
    ),
    _spec(
        "life-2026-sap-env-gov",
        "LIFE 2026 · Environmental Governance",
        relevance.DIRECT_CONDITIONAL,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/standard-action-projects-saps-environmental-governance-0_en",
        deadline="2026-09-22",
        role="conditional_direct_or_partner_public_body",
        reason="Un Comune è una persona giuridica pubblica ammissibile; serve un progetto coerente con governance e attuazione della normativa ambientale.",
    ),
    _spec(
        "life-2026-sap-nat-nature",
        "LIFE 2026 · Nature and Biodiversity",
        relevance.DIRECT_CONDITIONAL,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/standard-action-projects-saps-nature-and-biodiversity-nature-1_en",
        deadline="2026-09-22",
        role="conditional_direct_or_partner_public_body",
        reason="Comune ammissibile se dispone di un progetto pertinente su natura, biodiversità, restoration o Natura 2000 e di un ruolo operativo documentabile.",
    ),
    _spec(
        "life-2026-sap-nat-gov",
        "LIFE 2026 · Nature Governance and Information",
        relevance.DIRECT_CONDITIONAL,
        "https://cinea.ec.europa.eu/life-calls-proposals-2026_en",
        deadline="2026-09-22",
        role="conditional_direct_or_partner_public_body",
        reason="Comune ammissibile come ente pubblico quando il progetto riguarda governance, compliance, informazione o capacity building in materia di natura e biodiversità.",
    ),
    _spec(
        "life-2026-ta-pp-clima-sip",
        "LIFE 2026 · Technical Assistance for preparation of SIPs · Climate",
        relevance.DIRECT_CONDITIONAL,
        "https://cinea.ec.europa.eu/life-calls-proposals-2026_en",
        deadline="2026-09-22",
        role="conditional_public_body_applicant_for_strategic_integrated_project_preparation",
        reason="La TA è accessibile a enti pubblici, ma richiede una strategia e una scala coerenti con la preparazione di uno Strategic Integrated Project climatico.",
    ),
    _spec(
        "erasmus-2026-ka210-vet-round2",
        "Erasmus+ KA210 VET · Small-scale partnerships · second round 2026",
        relevance.DIRECT_CONDITIONAL,
        "https://erasmus-plus.ec.europa.eu/programme-guide/part-b/key-action-2/small-scale-partnerships",
        deadline="2026-10-01",
        role="conditional_direct_applicant_or_partner_public_body",
        reason="Gli enti pubblici possono partecipare; servono almeno due organizzazioni di due Paesi e un progetto pertinente al settore VET.",
        funding="Lump sum EUR 30.000 o EUR 60.000 secondo la proposta.",
    ),
    _spec(
        "life-2026-cet-oss",
        "LIFE 2026 CET · Integrated home renovation services / One-Stop-Shops",
        relevance.DIRECT_CONDITIONAL,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/one-stop-shops-integrated-services-clean-energy-transition-private-buildings_en",
        deadline="2026-09-16",
        role="territorial_one_stop_shop_partner_or_direct_applicant_where_project_structure_supports_it",
        reason="È possibile anche una route single-applicant; il Comune deve poter sviluppare o gestire un servizio territoriale integrato per la riqualificazione energetica.",
    ),
    _spec(
        "agenzia-demanio-free-transfer-15bis-2026",
        "Agenzia del Demanio · Trasferimento gratuito immobili dello Stato · art. 15-bis",
        relevance.DIRECT_CONDITIONAL,
        "https://www.agenziademanio.it/it/in-evidenza/trasferimentoimmobiliEETT/",
        deadline="2026-12-31",
        role="direct_municipality_requester_for_free_state_asset_transfer",
        reason="Tutti i Comuni possono richiedere il trasferimento; serve un immobile statale ammissibile e un progetto istituzionale/sociale finanziato o candidato su PNRR, PNC o PNIEC.",
        funding="Trasferimento gratuito dell'immobile ammissibile, non contributo in denaro.",
    ),
    _spec(
        "co-waters-blue-climathons-2026",
        "CO-WATERS · Blue Climathons 2026",
        relevance.DIRECT_CONDITIONAL,
        "https://co-waters.eu/",
        deadline="2026-09-27",
        role="direct_coalition_member_city_region_island_or_port_applicant",
        reason="Candidatura per membri della Coalition con una sfida locale legata all'acqua; fit più immediato per i Comuni costieri/waterfront della Versilia.",
        funding="Supporto gratuito per fino a 20 Blue Climathons: definizione sfida, facilitazione, mobilitazione, comunicazione e fundraising.",
    ),

    # SUPPORT_FINANCE mancanti.
    _spec(
        "eib-elena-rolling",
        "ELENA · European Local ENergy Assistance",
        relevance.SUPPORT_FINANCE,
        "https://www.eib.org/en/products/advisory-services/elena/index.htm",
        role="direct_local_authority_technical_assistance_applicant",
        reason="Autorità locali e municipali possono richiedere assistenza tecnica per preparare programmi d'investimento in energia, edilizia e trasporto sostenibile.",
        funding="Assistenza tecnica fino al 90% dei costi di preparazione, soggetta alle condizioni ELENA.",
        lifecycle="rolling_open",
    ),
    _spec(
        "sinfi-supporto-comuni-2026",
        "SINFI 2026 · Supporto gratuito ai Comuni fino a 50.000 abitanti",
        relevance.SUPPORT_FINANCE,
        "https://www.infratelitalia.it/archivio-news/notizie/progetto-sinfi-2026-i-comuni-fino-50000-abitanti-infratel-italia-apre",
        role="direct_request_for_free_technical_support",
        reason="I Comuni fino a 50.000 abitanti possono richiedere rilievo, mappatura, digitalizzazione e caricamento dati SINFI tramite il servizio dedicato.",
        funding="Servizio tecnico gratuito, FIFO fino a esaurimento risorse.",
        lifecycle="rolling_open",
    ),
    _spec(
        "icsc-cultura-missione-comune-2026",
        "Cultura Missione Comune 2026",
        relevance.SUPPORT_FINANCE,
        "https://www.creditosportivo.it/cliente-enti-territoriali/",
        deadline="2026-09-30",
        role="direct_local_authority_borrower",
        reason="Strumento rivolto agli enti locali per investimenti sul patrimonio culturale pubblico e interventi connessi.",
        funding="EUR 50 milioni di mutui a tasso fisso con totale abbattimento degli interessi; limiti per fascia demografica.",
    ),
    _spec(
        "eit-cc-delegate-cities-regions-network",
        "EIT Culture & Creativity · Delegate Cities & Regions Network",
        relevance.SUPPORT_FINANCE,
        "https://eit-culture-creativity.eu/your-opportunities/expression-interest/delegate-cities-regions-network",
        deadline="2026-12-31",
        role="local_authority_delegate_in_long_term_cities_regions_network",
        reason="Aperta a rappresentanti dei livelli di governo locale e regionale; offre peer learning, collaborazione e implementazione di innovazione/policy per i settori culturali e creativi.",
        funding="Partecipazione non-grant e capacity building.",
    ),
    _spec(
        "eeef-direct-financing-rolling",
        "European Energy Efficiency Fund · direct financing",
        relevance.SUPPORT_FINANCE,
        "https://www.eeef.lu/eligible-investments.html",
        role="direct_municipal_project_promoter_and_final_beneficiary",
        reason="Autorità municipali, locali e regionali sono beneficiari finali per investimenti ammissibili in efficienza, rinnovabili di piccola scala e trasporto urbano pulito.",
        funding="Finanziamento rolling, normalmente EUR 5-25 milioni, soggetto a due diligence e bancabilità.",
        lifecycle="rolling_open",
    ),
    _spec(
        "eeef-ta-facility-rolling",
        "European Energy Efficiency Fund · Technical Assistance Facility",
        relevance.SUPPORT_FINANCE,
        "https://www.eeef.lu/eeef-ta-facility.html",
        role="direct_city_council_or_public_entity_applicant",
        reason="City Councils e altri enti pubblici UE possono richiedere servizi di sviluppo progetto per programmi di investimento ammissibili.",
        funding="Servizi di consulenza/project development; call senza scadenza, first-come-first-served.",
        lifecycle="rolling_open",
    ),

    # PARTNER: matrici e topic atomici mancanti.
    _spec(
        "interreg-euro-med-call-7-mmm-2026",
        "Interreg Euro-MED Call 7 · Mediterranean Multiprogramme Mechanism",
        relevance.PARTNER,
        "https://interreg-euro-med.eu/en/call-7-mediterranean-multiprogramme-mechanism-coordinated-call/",
        deadline="2026-09-30",
        role="conditional_partner_or_lead",
        reason="Toscana è nell'area di cooperazione e le autorità locali possono partecipare; serve un partenariato MMM e output già sviluppati in un altro programma.",
    ),
    _spec(
        "life-2026-plp-ener-gov",
        "LIFE 2026 · Multilevel climate and energy dialogue",
        relevance.PARTNER,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/multilevel-climate-and-energy-dialogue-deliver-governance-regulation-and-post-2030-energy-and_en",
        deadline="2026-09-22",
        role="conditional_partner_or_participant_local_authority",
        reason="Le autorità locali sono parte esplicita del dialogo multilivello; è una call di scala consortile, non un grant comunale standalone.",
    ),
    _spec(
        "HORIZON-MISS-2026-04-CIT-01",
        "HORIZON-MISS-2026-04-CIT-01 · Cities Mission 2026",
        relevance.PARTNER,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/horizon-europe-eur-855-million-available-under-climate-neutral-and-smart-cities-eu-mission_en",
        deadline="2026-10-08",
        role="city_beneficiary_in_topic_specific_consortium",
        reason="Topic Cities Mission con ruolo operativo di città/autorità urbana nel consorzio; verificare il fit progettuale e la composizione richiesta.",
    ),
    _spec(
        "HORIZON-MISS-2026-04-CIT-02",
        "HORIZON-MISS-2026-04-CIT-02 · Cities Mission 2026",
        relevance.PARTNER,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/horizon-europe-eur-855-million-available-under-climate-neutral-and-smart-cities-eu-mission_en",
        deadline="2026-10-08",
        role="city_beneficiary_in_topic_specific_consortium",
        reason="Topic Cities Mission con ruolo operativo di città/autorità urbana nel consorzio; verificare il fit progettuale e la composizione richiesta.",
    ),
    _spec(
        "HORIZON-MISS-2026-04-CIT-NEB-B4P-CCRI-03",
        "HORIZON-MISS-2026-04-CIT-NEB-B4P-CCRI-03 · Cities Mission / NEB / Built4People / CCRI",
        relevance.PARTNER,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/horizon-europe-eur-855-million-available-under-climate-neutral-and-smart-cities-eu-mission_en",
        deadline="2026-10-08",
        role="required_city_beneficiary_demo_consortium",
        reason="La Wave 3 documenta dimostrazioni in almeno tre città di Paesi diversi, con le città come beneficiari e almeno una Mission City.",
    ),
    _spec(
        "HORIZON-NEB-2026-01-PARTICIPATION-01",
        "HORIZON-NEB-2026-01-PARTICIPATION-01 · Housing-led approaches to homelessness",
        relevance.PARTNER,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/horizon-europe-eur-1011-million-under-new-european-bauhaus-facility_en",
        deadline="2026-12-01",
        role="housing_social_service_policy_or_demo_neighbourhood_partner",
        reason="Il Comune può essere beneficiario/partner quando esercita funzioni su casa, homelessness, welfare o quartieri dimostrativi; il ruolo municipale non è obbligatorio in ogni consorzio.",
    ),
    _spec(
        "HORIZON-NEB-2026-01-PARTICIPATION-02",
        "HORIZON-NEB-2026-01-PARTICIPATION-02 · Spatial design of neighbourhoods",
        relevance.PARTNER,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/horizon-europe-eur-1011-million-under-new-european-bauhaus-facility_en",
        deadline="2026-12-01",
        role="public_space_planning_procurement_or_demo_neighbourhood_partner",
        reason="Ruolo concreto quando il Comune controlla spazi pubblici, pianificazione, servizi o procurement nel quartiere dimostrativo.",
    ),
    _spec(
        "HORIZON-NEB-2026-01-REGEN-01",
        "HORIZON-NEB-2026-01-REGEN-01 · Thermal comfort in buildings",
        relevance.PARTNER,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/horizon-europe-eur-1011-million-under-new-european-bauhaus-facility_en",
        deadline="2026-12-01",
        role="municipal_building_or_cultural_heritage_asset_owner_demo_partner",
        reason="Il Comune può entrare come proprietario/gestore di edificio pubblico o storico e partner di dimostrazione.",
    ),
    _spec(
        "HORIZON-NEB-2026-01-REGEN-02",
        "HORIZON-NEB-2026-01-REGEN-02 · Sustainable maintenance and repair of existing buildings",
        relevance.PARTNER,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/horizon-europe-eur-1011-million-under-new-european-bauhaus-facility_en",
        deadline="2026-12-01",
        role="public_heritage_or_social_housing_asset_owner_demo_partner",
        reason="Dimostrazioni su edifici, incluso patrimonio e housing sociale/affordable: ruolo comunale concreto come asset owner/manager o partner di sito.",
    ),
    _spec(
        "HORIZON-NEB-2026-01-BUSINESS-01",
        "HORIZON-NEB-2026-01-BUSINESS-01 · Social infrastructure and services against homelessness",
        relevance.PARTNER,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/horizon-europe-eur-1011-million-under-new-european-bauhaus-facility_en",
        deadline="2026-12-01",
        role="local_social_infrastructure_service_coordinator_or_demo_partner",
        reason="Il Comune può avere un ruolo operativo su welfare e infrastrutture sociali nei quartieri dimostrativi.",
    ),
    _spec(
        "HORIZON-NEB-2026-01-BUSINESS-03",
        "HORIZON-NEB-2026-01-BUSINESS-03 · Reuse of vacant, obsolete or underutilised spaces",
        relevance.PARTNER,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/horizon-europe-eur-1011-million-under-new-european-bauhaus-facility_en",
        deadline="2026-12-01",
        role="local_authority_inventory_regulatory_asset_reuse_and_demo_partner",
        reason="L'outcome cita esplicitamente le autorità locali nella sistematica identificazione e riuso di spazi vuoti/sottoutilizzati; ruolo consortile operativo documentato.",
    ),
    _spec(
        "life-2026-cet-enerpov",
        "LIFE 2026 CET · Energy Poverty (ENERPOV)",
        relevance.PARTNER,
        "https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/alleviating-household-energy-poverty-europe-1_en",
        deadline="2026-09-16",
        role="local_public_authority_policy_governance_or_delivery_partner",
        reason="Le autorità locali rientrano esplicitamente nella governance/delivery; non è stabilito un Comune beneficiario obbligatorio in ogni proposta.",
    ),
    _spec(
        "horizon-cl6-2026-01-zeropollution-03",
        "HORIZON-CL6-2026-01-ZEROPOLLUTION-03 · Managed aquifer recharge / water resilience",
        relevance.PARTNER,
        "https://cordis.europa.eu/programme/id/HORIZON_HORIZON-CL6-2026-01-ZEROPOLLUTION-03",
        deadline="2026-09-17",
        role="relevant_local_authority_stakeholder_or_partner",
        reason="Il multi-actor approach richiede adeguato coinvolgimento degli stakeholder, incluse autorità locali; il Comune non è beneficiario obbligatorio.",
    ),
    _spec(
        "horizon-cl5-2026-10-d6-07",
        "HORIZON-CL5-2026-10-D6-07 · CIVITAS ecosystem",
        relevance.PARTNER,
        "https://cordis.europa.eu/programme/id/HORIZON_HORIZON-CL5-2026-10-D6-07",
        deadline="2026-10-08",
        role="city_local_or_regional_authority_capacity_replication_partner",
        reason="La CSA CIVITAS è esplicitamente orientata a città e autorità locali/regionali per capacity building e replication.",
    ),
    _spec(
        "horizon-miss-2026-04-pcp-cit-01",
        "HORIZON-MISS-2026-04-PCP-CIT-01 · PCP for climate-neutral cities",
        relevance.PARTNER,
        "https://cordis.europa.eu/programme/id/HORIZON_HORIZON-MISS-2026-04-PCP-CIT-01",
        deadline="2026-10-08",
        role="public_procurer_or_follower_city",
        reason="Serve un buyer group con lead procurer Mission City e almeno tre Mission Cities; altre città possono partecipare come follower/partner.",
    ),
    _spec(
        "horizon-cl3-2026-01-ssri-03",
        "HORIZON-CL3-2026-01-SSRI-03 · Public procurement of innovation for security",
        relevance.PARTNER,
        "https://cordis.europa.eu/programme/id/HORIZON_HORIZON-CL3-2026-01-SSRI-03",
        deadline="2026-11-05",
        role="conditional_public_procurer_in_ppi_buyer_group",
        reason="Richiede almeno tre practitioner e tre public procurer di tre Paesi; un Comune può partecipare se possiede la pertinente funzione di procurement/security.",
    ),
    _spec(
        "horizon-cl3-2026-01-drs-01",
        "HORIZON-CL3-2026-01-DRS-01 · Risk awareness and disaster preparedness",
        relevance.PARTNER,
        "https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/wp-call/2026-2027/wp-6-civil-security-for-society_horizon-2026-2027_en.pdf",
        deadline="2026-11-05",
        role="required_local_or_regional_authority_representative",
        reason="Il consorzio richiede almeno un'organizzazione rappresentativa delle autorità locali/regionali insieme agli attori di disaster risk e società civile.",
    ),
    _spec(
        "horizon-cl3-2026-01-drs-02",
        "HORIZON-CL3-2026-01-DRS-02 · Multi-hazard and cascading impacts",
        relevance.PARTNER,
        "https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/wp-call/2026-2027/wp-6-civil-security-for-society_horizon-2026-2027_en.pdf",
        deadline="2026-11-05",
        role="required_local_or_regional_disaster_response_authority",
        reason="Richiesti rappresentanti di autorità locali/regionali responsabili della risposta ai disastri in un consorzio multinazionale.",
    ),
    _spec(
        "horizon-cl3-2026-01-drs-05",
        "HORIZON-CL3-2026-01-DRS-05 · Climate security and civil preparedness",
        relevance.PARTNER,
        "https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/wp-call/2026-2027/wp-6-civil-security-for-society_horizon-2026-2027_en.pdf",
        deadline="2026-11-05",
        role="conditional_local_or_regional_risk_management_partner",
        reason="Il topic dà priorità al lavoro locale/regionale su risk management e adattamento; il ruolo comunale resta consortile e condizionato.",
    ),
    _spec(
        "i3-2026-inv1",
        "I3-2026-INV1 · Interregional Innovation Investments Strand 1",
        relevance.PARTNER,
        "https://eismea.ec.europa.eu/funding-opportunities/calls-proposals_en",
        deadline="2026-11-12",
        role="public_authority_partner_in_interregional_s3_investment_ecosystem",
        reason="Le autorità pubbliche sono organizzazioni target; serve un consorzio interregionale e coerenza con priorità S3 complementari.",
    ),
    _spec(
        "i3-2026-inv2a",
        "I3-2026-INV2a · Interregional Innovation Investments Strand 2a",
        relevance.PARTNER,
        "https://eismea.ec.europa.eu/funding-opportunities/calls-proposals/interregional-innovation-investments-strand-2a-i3-2026-inv2a_en",
        deadline="2026-11-12",
        role="public_authority_partner_in_interregional_s3_investment_ecosystem",
        reason="Le autorità pubbliche possono partecipare nel partenariato interregionale; fit subordinato a ecosistema di investimento e priorità S3.",
    ),
    _spec(
        "life-2026-cet-betterreno",
        "LIFE 2026 CET · BETTERRENO",
        relevance.PARTNER,
        "https://cinea.ec.europa.eu/life-calls-proposals-2026_en",
        deadline="2026-09-16",
        role="renovation_market_policy_or_demo_partner",
        reason="Ruolo comunale come partner di policy, mercato della riqualificazione o sito/asset dimostrativo; non grant comunale standalone.",
    ),
    _spec(
        "horizon-cl3-2026-01-ssri-02",
        "HORIZON-CL3-2026-01-SSRI-02 · Demand-led innovation in security",
        relevance.PARTNER,
        "https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/wp-call/2026-2027/wp-6-civil-security-for-society_horizon-2026-2027_en.pdf",
        deadline="2026-11-05",
        role="public_procurer_or_civil_security_practitioner_in_pcp_buyer_group",
        reason="Il consorzio richiede practitioner e procurer pubblici; un Comune può entrare se esercita una pertinente funzione di sicurezza/procurement.",
    ),
    _spec(
        "eit-cc-neb-academy-skills-infrastructure-2026",
        "EIT Culture & Creativity · NEB Academy | Skills Infrastructure",
        relevance.PARTNER,
        "https://eit-culture-creativity.eu/your-opportunities/calls-funding/neb-academy-skills-infrastructure",
        deadline="2026-09-11",
        role="required_public_authority_or_municipality_beneficiary_in_multi_country_consortium",
        reason="Il consorzio deve includere almeno un'autorità pubblica/municipalità insieme a education provider e organizzazione privata del lived environment.",
        funding="Fino a EUR 600.000 per progetto; budget indicativo EUR 3,5 milioni.",
    ),

    # Upcoming già pubblicati come avvisi ma non ancora candidabili l'8 settembre.
    _spec(
        "sai-2026-ordinary-2402",
        "Ministero dell'Interno · SAI 2026 · 2.402 posti ordinari",
        relevance.DIRECT_CONDITIONAL,
        "https://fnasilo.dlci.interno.it/sprar/",
        opens="2026-09-15",
        deadline="2026-11-10",
        role="direct_local_authority_applicant_singly_or_jointly",
        reason="Gli enti locali possono presentare progetti singolarmente o in forma associata; candidature dal 15 settembre 2026.",
        funding="FAMI-backed funding per nuova capacità di accoglienza SAI ordinaria.",
    ),
    _spec(
        "sai-2026-msna-500",
        "Ministero dell'Interno · SAI 2026 · 500 posti MSNA",
        relevance.DIRECT_CONDITIONAL,
        "https://fnasilo.dlci.interno.it/sprar/secure/notiziaVisualizza/65",
        opens="2026-09-15",
        deadline="2026-11-10",
        role="direct_local_authority_applicant_singly_or_jointly",
        reason="Enti locali candidabili per progetti SAI destinati a minori stranieri non accompagnati; apertura 15 settembre.",
        funding="FAMI 2021-2027; fino a 500 posti, durata fino al 31 dicembre 2028 secondo l'avviso.",
    ),
    _spec(
        "sai-2026-disagio-300",
        "Ministero dell'Interno · SAI 2026 · 300 posti disagio mentale/sanitario",
        relevance.DIRECT_CONDITIONAL,
        "https://fnasilo.dlci.interno.it/sprar/secure/notiziaVisualizza/64",
        opens="2026-09-15",
        deadline="2026-11-10",
        role="direct_local_authority_applicant_singly_or_jointly",
        reason="Enti locali candidabili per posti SAI dedicati a persone con esigenze di salute, disabilità o disagio mentale; apertura 15 settembre.",
        funding="FAMI 2021-2027; fino a 300 posti specializzati, durata fino al 31 dicembre 2028 secondo l'avviso.",
    ),
    _spec(
        "mic-festival-cori-bande-2026",
        "MiC · Festival, Cori e Bande 2026",
        relevance.PARTNER,
        "https://spettacolo.cultura.gov.it/bando-festival-cori-e-bande-anno-2026-d-m-4-aprile-2025-n-110-recante-criteri-e-modalita-di-accesso-al-fondo-di-cui-allarticolo-1-comma-605-della-legge-30-dicembre-2024/",
        opens="2026-09-15",
        deadline="2026-10-15",
        role="temporary_grouping_of_at_least_four_local_public_authorities",
        reason="Sono ammessi raggruppamenti temporanei già costituiti di almeno quattro enti pubblici territoriali; il singolo Comune non può presentarsi da solo.",
    ),
]


def _build_item(spec: dict[str, Any], today: date) -> dict[str, Any]:
    deadline = spec.get("deadline_at")
    opens = spec.get("opens_at")
    if opens and date.fromisoformat(str(opens)) > today:
        lifecycle = "announced_upcoming"
    elif spec.get("lifecycle") == "rolling_open" or deadline is None:
        lifecycle = "rolling_open"
    else:
        lifecycle = "application_open"

    title = str(spec["title"])
    coverage_id = str(spec["coverage_id"])
    relevance_class = str(spec["municipal_relevance_class"])
    reason = str(spec["reason"])
    url = str(spec["url"])
    publisher = urlsplit(url).netloc.removeprefix("www.") or "Fonte ufficiale"
    digest = hashlib.sha1(coverage_id.encode("utf-8")).hexdigest()[:14]
    status_map = {name: {"status": "conditional", "reason": reason} for name in MUNICIPALITIES}

    return {
        "id": f"opp-matrix-{digest}",
        "coverage_id": coverage_id,
        "source_id": "municipal-matrix-v1",
        "source_name": publisher,
        "publisher": publisher,
        "title": title,
        "url": url,
        "summary": " ".join(x for x in (str(spec.get("funding") or "").strip(), reason) if x),
        "status": "upcoming" if lifecycle == "announced_upcoming" else "open",
        "opens_at": opens,
        "deadline_at": deadline,
        "published_at": None,
        "beneficiary_text": reason,
        "municipalities": list(MUNICIPALITIES),
        "eligibility": "conditional",
        "eligibility_reason": reason,
        "municipality_eligibility": status_map,
        "applicant_eligibility": "conditional",
        "applicant_type": str(spec["municipality_role"]).replace("_", " "),
        "municipality_role": spec["municipality_role"],
        "municipal_relevance_class": relevance_class,
        "final_beneficiaries": "Comuni e comunità locali interessati dal progetto, servizio o investimento",
        "partnership_required": relevance_class == relevance.PARTNER,
        "project_requirements": reason,
        "geographic_scope": "Italia / Unione europea secondo la call",
        "geographic_eligibility": "conditional",
        "territorial_relevance": "partner" if relevance_class == relevance.PARTNER else "direct",
        "actionable_for_municipality": True,
        "decision_class": "matrix_verified_partner" if relevance_class == relevance.PARTNER else "matrix_verified_municipal",
        "themes": [base._category(title)],
        "verified_direct": relevance_class != relevance.PARTNER,
        "verified_at": today.isoformat(),
        "audit_class": "matrix_v1_verified_public",
        "audit_promotion_version": PROMOTION_VERSION,
        "presentation": {
            "source_label": publisher,
            "source_mark": "UE" if ".eu" in urlsplit(url).netloc or "europa.eu" in url else publisher[:12],
            "source_class": "eu" if ".eu" in urlsplit(url).netloc or "europa.eu" in url else "istituzionale",
            "category": base._category(title),
            "description": reason[:320],
            "condition_label": "Partnership / consorzio" if relevance_class == relevance.PARTNER else (
                "Supporto / finanza" if relevance_class == relevance.SUPPORT_FINANCE else "Verificare i requisiti specifici"
            ),
        },
        "access_mode": "support_route" if relevance_class in {relevance.SUPPORT_FINANCE, relevance.ROUTED} else "specific_requirement",
        "quality_gate": {"status": "pass", "missing": [], "reasons": []},
        "lifecycle_stage": lifecycle,
        "is_new": True,
        "first_seen_at": today.isoformat(),
    }


def apply_complete_promotions(result: dict[str, Any], today: date) -> dict[str, Any]:
    before_ids = {str(x.get("coverage_id") or x.get("rule_id") or x.get("id") or "") for x in result.get("opportunities") or []}
    before_titles = {base._normalized_title(x.get("title")) for x in result.get("opportunities") or []}

    base.apply_audit_corpus_promotions(result, today)
    opportunities = list(result.get("opportunities") or [])
    opportunities = [x for x in opportunities if str(x.get("coverage_id") or "") not in _SUPPRESS_IDS]

    for item in opportunities:
        coverage_id = str(item.get("coverage_id") or "")
        if coverage_id in _RECLASSIFY:
            item["municipal_relevance_class"] = _RECLASSIFY[coverage_id]
            item["municipal_relevance_label"] = relevance.LABELS[_RECLASSIFY[coverage_id]]
            item["municipal_headline"] = _RECLASSIFY[coverage_id] in relevance.HEADLINE_CLASSES
        for key, value in _PATCHES.get(coverage_id, {}).items():
            item[key] = value

    existing_ids = {str(x.get("coverage_id") or "") for x in opportunities}
    existing_titles = {base._normalized_title(x.get("title")) for x in opportunities}
    for spec in _SPECS:
        item = _build_item(spec, today)
        coverage_id = str(item["coverage_id"])
        title_key = base._normalized_title(item["title"])
        if coverage_id in existing_ids or title_key in existing_titles:
            continue
        opportunities.append(item)
        existing_ids.add(coverage_id)
        existing_titles.add(title_key)

    order = {"application_open": 0, "rolling_open": 1, "announced_upcoming": 2}
    opportunities.sort(key=lambda x: (
        order.get(str(x.get("lifecycle_stage") or "application_open"), 9),
        str(x.get("deadline_at") or "9999-99-99"),
        str(x.get("title") or ""),
    ))
    result["opportunities"] = opportunities

    added = [
        x for x in opportunities
        if str(x.get("coverage_id") or x.get("id") or "") not in before_ids
        and base._normalized_title(x.get("title")) not in before_titles
    ]
    added_summary = relevance.summarize(added)
    current_added = added_summary["headlineCurrentOrRolling"] + added_summary["partnershipCurrentOrRolling"]
    result["auditCorpusPromotionVersion"] = PROMOTION_VERSION
    result["auditCorpusPromotion"] = {
        "discovered": len(added),
        "added": len(added),
        "currentOrRollingAdded": current_added,
        "matrixCurrentTarget": MATRIX_CURRENT_TARGET,
        "municipalCurrentOrRollingAdded": added_summary["headlineCurrentOrRolling"],
        "municipalUpcomingAdded": added_summary["headlineUpcoming"],
        "partnershipCurrentOrRollingAdded": added_summary["partnershipCurrentOrRolling"],
        "partnershipUpcomingAdded": added_summary["partnershipUpcoming"],
    }
    result.setdefault("counts", {})["auditPromotionsAdded"] = len(added)
    return result
