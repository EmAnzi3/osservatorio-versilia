#!/usr/bin/env python3
from __future__ import annotations
import unittest
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
            ('sviluppo-toscana','Avviso Mercati Rionali','st-mercati-rionali-2026','2026-09-15'),
            ('mic-spettacolo','Bando per la PROMOZIONE DELLA MUSICA JAZZ / 2027 – Avviso pubblico e apertura dei termini di presentazione delle domande','mic-jazz-2027','2026-09-10'),
            ('ministero-interno-prefetture','Videosorveglianza - D.M. 2026','mi-videosorveglianza-2026','2026-08-24'),
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
        self.assertTrue(result['opportunities'][1]['presentation']['source_favicon'].startswith('data:image/png;base64,'))

    def test_runtime_coverage_uses_embedded_icons_for_fragile_sources(self):
        registry={'sources':{'fondazione-cr-lucca':{'label':'Fondazione Cassa di Risparmio di Lucca','monitoringStatus':'active','role':'primary'},'anci-toscana':{'label':'ANCI Toscana','monitoringStatus':'active','role':'discovery'},'ministero-interno':{'label':'Ministero dell Interno','monitoringStatus':'active','role':'discovery'}},'plannedSources':[]}
        result={'sources':[{'sourceId':'fondazione-cr-lucca','status':'ok','freshness':{'status':'current'}}]}
        discovery=[{'sourceId':'anci-toscana','status':'ok','freshness':{'status':'discovery'}},{'sourceId':'ministero-interno','status':'ok','freshness':{'status':'discovery'}}]
        coverage=radar.build_coverage(result,registry,discovery)
        for row in coverage['rows']:
            self.assertTrue((row.get('favicon') or '').startswith('data:image/png;base64,'),row['source_id'])


if __name__=='__main__': unittest.main()
