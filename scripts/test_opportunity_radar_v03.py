#!/usr/bin/env python3
from __future__ import annotations
import unittest
import json
from datetime import date
import opportunity_radar_v03 as radar
import run_opportunity_radar_v03  # noqa: F401 - attiva gli shim del runtime live


class RadarV03Test(unittest.TestCase):
    def test_specialized_regional_sources_reuse_regione_rules(self):
        rules,_,aliases=radar.load_rules();original=radar.v021.matching_rule
        def alias_match(item,selected_rules=None):
            working=dict(item);sid=str(working.get('source_id') or '')
            if sid in aliases: working['source_id']=aliases[sid]
            return original(working,selected_rules)
        radar.v021.matching_rule=alias_match
        try: rule=radar.v021.matching_rule({'source_id':'regione-toscana-fse','title':'Anno educativo e scolastico 2026-2027, contributi ai Comuni per percorsi formativi per la qualità del "Sistema integrato 0-6 anni"'},rules)
        finally: radar.v021.matching_rule=original
        self.assertIsNotNone(rule);self.assertEqual(rule['id'],'rt-sistema-integrato-0-6-2026')

    def test_backtest_v03_passes_and_tests_source_aliases(self):
        rules,_,aliases=radar.load_rules();original=radar.v021.matching_rule
        def alias_match(item,selected_rules=None):
            working=dict(item);sid=str(working.get('source_id') or '')
            if sid in aliases: working['source_id']=aliases[sid]
            return original(working,selected_rules)
        radar.v021.matching_rule=alias_match
        try: report=radar.v025.run_backtest(radar.DEFAULT_BACKTEST,rules)
        finally: radar.v021.matching_rule=original
        self.assertTrue(report['passed']);self.assertEqual(next(x for x in report['rows'] if x['id']=='p14')['prediction'],'operational');self.assertEqual(next(x for x in report['rows'] if x['id']=='n12')['prediction'],'non_operational')

    def test_recovered_municipal_rules_are_documented(self):
        rules,_,_=radar.load_rules()
        cases=(
            ('sviluppo-toscana','Avviso Mercati Rionali','st-mercati-rionali-2026','2026-10-15'),
            ('mic-spettacolo','Bando per la PROMOZIONE DELLA MUSICA JAZZ / 2027 – Avviso pubblico e apertura dei termini di presentazione delle domande','mic-jazz-2027','2026-09-10'),
            ('ministero-interno-prefetture','Videosorveglianza - D.M. 2026','mi-videosorveglianza-2026','2026-08-24'),
            ('regione-toscana','Bando Nidi gratis 2026-2027 per i servizi educativi rivolto ai Comuni','rt-nidi-gratis-comuni-reopening-2026-2027','2026-10-06'),
            ('regione-toscana','Finanziamenti per studi di Microzonazione Sismica di livello 2 e 3','rt-microzonazione-sismica-2026','2026-10-17'),
            ('regione-toscana','Studi di microzonazione sismica e analisi delle Condizioni limite per l’emergenza: avviso ai Comuni','rt-microzonazione-sismica-2026','2026-10-17'),
        )
        for source,title,rule_id,deadline in cases:
            with self.subTest(rule=rule_id):
                rule=radar.v021.matching_rule({'source_id':source,'title':title},rules)
                self.assertIsNotNone(rule)
                self.assertEqual(rule['id'],rule_id)
                self.assertTrue(rule['actionable'])
                self.assertEqual(rule['municipality_role'],'direct_applicant')
                self.assertEqual(rule['deadline_override'],deadline)
                self.assertTrue(rule['evidence_url'].startswith('https://'))

    def test_mercati_rionali_has_live_detail_fallback(self):
        payload=json.loads(run_opportunity_radar_v03._VERIFIED.read_text(encoding='utf-8'))
        entry=next(x for x in payload['entries'] if x['rule_id']=='st-mercati-rionali-2026')
        self.assertEqual(entry['deadline_at'],'2026-10-15')
        self.assertTrue(entry['canonical'])
        self.assertIn('15 Ottobre 2026',entry['required_terms'])
        self.assertIn('Comuni della Regione Toscana',entry['required_terms'])

        result={
            'municipalities':['Camaiore'],
            'sources':[{'sourceId':'sviluppo-toscana','status':'ok','freshness':{'status':'current'}}],
            'opportunities':[],
            'qualityHold':[],
            'counts':{},
        }
        run_opportunity_radar_v03.post.inject_verified_details(
            radar,
            result,
            radar.DEFAULT_CONFIG,
            date(2026,9,21),
            radar.DEFAULT_PRESENTATION,
            run_opportunity_radar_v03._VERIFIED,
            detail_payloads={
                entry['url']:(
                    '<p>Possono presentare domanda i Comuni della Regione Toscana. '
                    'Scadenza prorogata alle ore 12:00 del 15 Ottobre 2026. '
                    'Contributo fino all 80%.</p>'
                )
            },
            live=False,
        )
        item=next(x for x in result['opportunities'] if x['rule_id']=='st-mercati-rionali-2026')
        self.assertEqual(item['deadline_at'],'2026-10-15')
        self.assertEqual(item['deadline_time'],'12:00')
        self.assertEqual(item['quality_gate']['status'],'pass')

    def test_fami_language_courses_are_documented_non_municipal(self):
        rules,_,_=radar.load_rules()
        rule=radar.v021.matching_rule({
            'source_id':'regione-toscana',
            'title':'Erogazione di corsi di lingua e cultura italiana per cittadini di Paesi terzi: bando rivolto agli Enti del terzo settore',
        },rules)
        self.assertIsNotNone(rule)
        self.assertEqual(rule['id'],'rt-fami-corsi-ets-2026')
        self.assertEqual(rule['municipality_role'],'none')
        self.assertFalse(rule['actionable'])

    def test_deadline_parser_prefers_operational_extension(self):
        text=(
            'Data di pubblicazione bando su Burt: 25.06.2026. '
            'Data di scadenza presentazione domande: 15.09.2026 12:00. '
            'Scadenza del bando prorogata fino alle ore 12 del 15 ottobre 2026. '
            'La domanda può essere presentata fino alle ore 12:00 del 15 ottobre 2026 '
            '(scadenza iniziale 15 settembre 2026).'
        )
        _opens,deadline,published=radar.base.dates(text)
        self.assertEqual(deadline,'2026-10-15')
        self.assertEqual(published,'2026-06-25')

    def test_microzonazione_uses_recent_burt_and_operational_deadline(self):
        text=(
            'Pubblicato il 04.02.2026. Pubblicato su BURT il 16.09.2026. '
            'Data di scadenza presentazione domande: 07.10.2026 12:00. '
            'Le Amministrazioni comunali possono presentare la manifestazione di interesse '
            'fino alle ore 12:00 di sabato 17 ottobre 2026.'
        )
        _opens,deadline,published=radar.base.dates(text)
        self.assertEqual(deadline,'2026-10-17')
        self.assertEqual(published,'2026-09-16')

    def test_nidi_gratis_comuni_is_distinct_from_family_measure(self):
        rules,_,_=radar.load_rules()
        municipal=radar.v021.matching_rule({
            'source_id':'regione-toscana',
            'title':'Bando Nidi gratis 2026-2027 per i servizi educativi rivolto ai Comuni',
        },rules)
        family=radar.v021.matching_rule({
            'source_id':'regione-toscana',
            'title':'Bando Nidi gratis 2026-2027 per i servizi educativi rivolto alle famiglie',
        },rules)
        self.assertIsNotNone(municipal)
        self.assertEqual(municipal['id'],'rt-nidi-gratis-comuni-reopening-2026-2027')
        self.assertIsNone(family)

    def test_discovery_candidates_are_internal_only(self):
        source={'id':'anci-toscana','label':'ANCI Toscana','publisher':'ANCI Toscana','territory':'Toscana','includeTerms':['bando','contribut'],'municipalTerms':['comun','edifici pubblici']}
        html='<h3><a href="/bando-test/">Bando edifici pubblici per i Comuni</a></h3><p>Contributi per interventi di riqualificazione.</p><h3><a href="/notizia/">Convegno regionale</a></h3><p>Una giornata di studio.</p>'
        rows=radar.discovery_candidates(source,html,'https://ancitoscana.it/');self.assertEqual(len(rows),1);self.assertTrue(rows[0]['discovery_only']);self.assertEqual(rows[0]['status'],'internal_review')

    def test_coverage_counts_discovery_without_publication(self):
        registry={'sources':{'regione-toscana':{'label':'Regione Toscana','monitoringStatus':'active','role':'primary'},'gse':{'label':'GSE','monitoringStatus':'active','role':'discovery','favicon':'https://www.gse.it/favicon.ico'}},'plannedSources':[]}
        result={'sources':[{'sourceId':'regione-toscana','status':'ok','freshness':{'status':'current','observedDate':'2026-08-22'}}]}
        coverage=radar.build_coverage(result,registry,[{'sourceId':'gse','status':'ok','freshness':{'status':'discovery'}}]);self.assertEqual(coverage['summary']['active'],2);self.assertEqual(coverage['summary']['healthyActive'],2);self.assertEqual(coverage['summary']['discovery'],1)

    def test_source_visuals_attach_favicon(self):
        result={'opportunities':[{'source_id':'regione-toscana-fesr','presentation':{'source_label':'Regione Toscana'}},{'source_id':'fondazione-cr-lucca','presentation':{'source_label':'Fondazione'}}], 'archive':[]};radar.attach_source_visuals(result,radar.DEFAULT_PRESENTATION)
        self.assertIn('favicon.ico',result['opportunities'][0]['presentation']['source_favicon'])
        self.assertEqual(result['opportunities'][1]['presentation']['source_favicon'],'/assets/source-icons/fondazione-cr-lucca.svg')

    def test_runtime_coverage_uses_local_icons_for_fragile_sources(self):
        registry={'sources':{'fondazione-cr-lucca':{'label':'Fondazione Cassa di Risparmio di Lucca','monitoringStatus':'active','role':'primary'},'anci-toscana':{'label':'ANCI Toscana','monitoringStatus':'active','role':'discovery'},'ministero-interno':{'label':'Ministero dell Interno','monitoringStatus':'active','role':'discovery'}},'plannedSources':[]}
        result={'sources':[{'sourceId':'fondazione-cr-lucca','status':'ok','freshness':{'status':'current'}}]}
        discovery=[{'sourceId':'anci-toscana','status':'ok','freshness':{'status':'discovery'}},{'sourceId':'ministero-interno','status':'ok','freshness':{'status':'discovery'}}]
        coverage=radar.build_coverage(result,registry,discovery)
        expected={
            'fondazione-cr-lucca':'/assets/source-icons/fondazione-cr-lucca.svg',
            'anci-toscana':'/assets/source-icons/anci-toscana.svg',
            'ministero-interno':'/assets/source-icons/ministero-interno.svg',
        }
        for row in coverage['rows']:
            self.assertEqual(row.get('favicon'),expected[row['source_id']],row['source_id'])

    def test_final_continuity_drops_recovered_verified_item(self):
        result={
            'opportunities':[{'rule_id':'mic-jazz-2027','title':'Bando per la promozione della musica Jazz 2027'}],
            'continuityHold':[{'identity_key':'rule:mic-jazz-2027','title':'Bando per la promozione della musica Jazz 2027'}],
            'counts':{'continuityHold':1},
        }
        run_opportunity_radar_v03._reconcile_final_continuity(result)
        self.assertEqual(result['continuityHold'],[])
        self.assertEqual(result['counts']['continuityHold'],0)


if __name__=='__main__': unittest.main()
