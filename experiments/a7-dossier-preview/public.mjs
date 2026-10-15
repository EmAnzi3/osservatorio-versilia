// Public wording and layout only. The original reader, answer and export stay intact.
let sourceCommit;
const node=(tag,text,className)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;};
const list=items=>{const ul=node('ul');for(const item of items)ul.append(node('li',item));return ul;};
const fold=(title,child,technical=false)=>{const el=node('details');if(technical)el.dataset.a7Technical='true';el.append(node('summary',title),child);return el;};
const introductions={
 'lavoro-centrale':'Per capire il lavoro a Massarosa, guardiamo sia chi vive nel Comune sia le attività che vi operano. Sono prospettive diverse: più attività sul territorio non significa automaticamente più opportunità per ogni residente.',
 'lavoro-1':'Il confronto con Viareggio affianca l’occupazione dei residenti e l’andamento delle unità locali. I dati riguardano periodi diversi e non dimostrano che un fenomeno abbia causato l’altro.',
 'lavoro-2':'Produzione industriale, retribuzioni e servizi descrivono aspetti diversi dell’economia locale. Gli importi sono nominali: la loro variazione non misura da sola una crescita reale.',
 'infanzia-centrale':'Mettiamo a fianco la capacità potenziale dei servizi per la prima infanzia, gli alunni e l’organizzazione delle scuole. La dotazione disponibile non dice da sola quante famiglie riescano a usare i servizi.',
 'infanzia-1':'Il confronto mostra la capacità potenziale dichiarata rispetto ai bambini della fascia considerata. Non misura presenze o liste d’attesa: per decidere nuovi posti servono anche questi elementi.',
 'infanzia-2':'Alunni, classi, tempo pieno e accessibilità aiutano a descrivere la rete scolastica. I risultati educativi richiedono un approfondimento distinto e hanno una copertura territoriale incompleta.'
};
const populations={
 'resident population; 25–64 total residents':'Residenti tra 25 e 64 anni.',
 'ASIA active local units; annual average employment at workplace; ASIA total':'Unità locali attive e addetti localizzati nel territorio (ASIA). Gli addetti sono una media annua e possono risiedere altrove.',
 'Frame SBS local units of industry and services; industry':'Unità locali dell’industria rilevate da ISTAT (Frame SBS).',
 'Frame SBS local units of industry and services; services':'Unità locali dei servizi rilevate da ISTAT (Frame SBS).',
 'resident children aged 3–36 months':'Bambini residenti tra 3 e 36 mesi; la capacità è potenziale, non misura le presenze effettive.',
 'tested students by municipality of school location, official Totale aggregation':'Alunni che hanno svolto le prove, attribuiti al Comune della scuola, non a quello di residenza.',
 'unique MIM school buildings; accessibilita defined responses, or all responses for undefined share':'Edifici scolastici censiti dal Ministero: la quota di accessibilità considera le risposte definite, non quelle mancanti.',
 'pupils in state and private schools located in the municipality; not resident children':'Alunni nelle scuole statali e paritarie del Comune; possono risiedere in altri Comuni.'
};
const warnings={
 classes_not_buildings_or_sites:'Il dato riguarda le classi, non il numero di edifici o sedi scolastiche.',
 cross_boundary_use_waiting_lists_and_quality_not_measured:'Spostamenti tra Comuni, liste d’attesa e qualità del servizio non sono misurati.',
 cumulative_baseline_change_not_year_on_year:'La variazione riguarda l’intero intervallo indicato, non il solo ultimo anno.',
 declared_building_attributes_not_certification_quality_capacity_or_pupil_access:'Le caratteristiche dichiarate degli edifici non certificano qualità, capacità o accessibilità effettiva per ogni alunno.',
 disjoint_populations_must_be_attested:'Un totale è ammissibile soltanto per gruppi che non si sovrappongono.',
 frame_and_asia_universes_differ:'Frame SBS e ASIA hanno perimetri differenti: non vanno trattati come una fonte unica.',
 frame_value_added_not_municipal_gdp:'Il valore aggiunto delle unità locali non è il PIL del Comune.',
 frozen_derived_components_no_implicit_weighting:'Le componenti provengono dai dati conservati; non si ricostruiscono pesi mancanti.',
 full_time_classification_not_service_quality_or_parental_employment_effect:'Il tempo pieno non misura la qualità del servizio né il suo effetto sull’occupazione dei genitori.',
 invalsi_2019_20_tests_not_conducted_gap_preserved:'Le prove INVALSI non si sono svolte nell’anno scolastico 2019/20; quel vuoto non viene colmato.',
 invalsi_aggregation_totale_same_grade_subject_academic_year:'Il confronto INVALSI mantiene uguali grado, materia, anno scolastico e aggregazione ufficiale.',
 invalsi_comune_plesso_not_student_residence:'Il territorio è quello della scuola, non la residenza degli alunni.',
 invalsi_missing_or_suppressed_cells_not_zero_or_absence_of_schools:'I valori mancanti o non pubblicati non significano zero né assenza di scuole.',
 invalsi_numeric_rank_not_school_quality_or_policy_priority:'L’ordine dei valori non è una graduatoria della qualità delle scuole o delle priorità amministrative.',
 invalsi_participation_and_coverage_percentages_not_valid_student_denominators:'Le percentuali di partecipazione e copertura non consentono di ricostruire il numero degli alunni.',
 invalsi_published_precision_retained_no_versilia_mean:'Si conserva la precisione pubblicata, senza ricostruire una media della Versilia.',
 located_school_pupils_not_resident_children_or_service_coverage:'Gli iscritti nelle scuole del Comune non coincidono con i bambini residenti né misurano la copertura dei servizi.',
 nominal_economic_values_not_real_growth:'Gli importi sono nominali: la variazione non misura la crescita reale al netto dell’inflazione.',
 official_rounded_measure_preserved_no_implicit_weighting:'Si conserva il valore arrotondato pubblicato, senza ricostruire pesi non disponibili.',
 partial_coverage:'Non sono disponibili tutti i dati richiesti per il confronto.',
 potential_capacity_not_attendance_or_access:'La capacità potenziale non misura frequenza effettiva o accesso delle famiglie.',
 published_rounding_preserved_no_implicit_weighting:'Gli arrotondamenti pubblicati restano invariati; non si introducono pesi mancanti.',
 resident_employment_not_workplace_jobs:'Si misura l’occupazione dei residenti, non i posti di lavoro localizzati nel Comune.',
 response_denominator_varies_by_field:'La base di calcolo cambia secondo la caratteristica rilevata: va letta insieme al singolo dato.',
 school_year_not_calendar_year:'L’anno scolastico è distinto dall’anno solare.',
 undefined_responses_not_no_or_zero:'Una risposta non definita non equivale a un no o a uno zero.',
 workplace_activity_not_resident_employment:'L’attività economica localizzata non misura direttamente l’occupazione dei residenti.'
};
function source(source){
 const p=node('p',undefined,'a7-source');
 try{
  const url=new URL(source);const names={'esploradati.istat.it':'ISTAT','www.istat.it':'ISTAT','dati.toscana.it':'Regione Toscana','serviziostatistico.invalsi.it':'INVALSI','dati.istruzione.it':'Ministero dell’Istruzione e del Merito'};
  if(url.protocol==='https:'&&names[url.hostname]){const a=node('a',names[url.hostname]);a.href=url.href;p.append(node('span','Fonte: '),a);return p;}
 }catch{}
 p.textContent='Fonte e documentazione disponibili nei dettagli di verifica.';return p;
}
function selectedQuestion(){const el=document.getElementById('a7-selected-question');if(el)el.textContent=document.getElementById('domanda').selectedOptions[0]?.textContent||'';}
function presentPublic(out,answer){
 selectedQuestion();
 const q=answer.questionPlan;
 out.append(node('p','La tua domanda','eyebrow'),node('h2',q.question),node('p','Risposta parziale · scopri cosa sappiamo e cosa manca','badge'));
 out.append(node('p',introductions[q.id]||q.interpretationLimit,'a7-answer-intro'),node('h3','Partiamo dai dati'));
 for(const c of answer.components){
  const section=node('section',undefined,'component');section.setAttribute('aria-label','Dati della lettura');
  const first=c.facts[0];section.append(node('h4',first?first.text.split(' — ')[0]:'Un confronto che non possiamo calcolare'));
  if(c.response.coverage && c.response.coverage.usable<c.response.coverage.requested)section.append(node('p',`Dati disponibili per ${c.response.coverage.usable} delle ${c.response.coverage.requested} osservazioni richieste. I mancanti restano esclusi.`, 'a7-coverage'));
  if(c.response.status!=='computed')section.append(node('p','I dati disponibili non permettono questo calcolo. Il consenso a leggere risultati parziali non cambia questo limite.'));
  const ul=node('ul',undefined,'facts');
  for(const f of c.facts){
   const li=node('li');li.append(node('p',f.text.replace('persone/addetti secondo definizione.','persone.'),'a7-fact'));
   if(f.period!==undefined)li.append(node('p','Periodo: '+f.period,'meta'));
   if(f.population!==undefined)li.append(node('p',populations[f.population]||'Il perimetro di questo dato è descritto nei dettagli di verifica.','a7-scope'));
   li.append(source(f.source));ul.append(li);
  }
  section.append(ul);
  if(c.response.warnings.length)section.append(fold('Come leggere questo dato',list([...new Set(c.response.warnings.map(w=>warnings[w]||'Sono presenti ulteriori limiti metodologici, conservati nei dettagli di verifica.'))])));
  out.append(section);
 }
 out.append(node('h3','Fin dove possiamo arrivare'),node('p',q.interpretationLimit));
 out.append(fold('Quali dati mancano per decidere?',list(q.missingData)));
 const docs=node('p');const a=node('a','Approfondisci nel dossier');
 // The canonical source path and pinned commit are validated before publishing.
 const commit=sourceCommit;
 if(/^[a-f0-9]{40}$/u.test(commit||'')&&/^docs\/[A-Za-z0-9_./-]+$/u.test(q.dossierPath)&&!q.dossierPath.split('/').includes('..')){a.href=`https://github.com/EmAnzi3/osservatorio-versilia/blob/${commit}/${q.dossierPath}`;docs.append(a);out.append(docs);}
 const verification=node('div');const snapshots=node('ul');const seen=new Set();
 for(const c of answer.components)for(const f of c.facts)for(const e of f.evidence){
  if(!/^[a-f0-9]{40}$/u.test(sourceCommit||'')||!/^data\/[A-Za-z0-9_./-]+$/u.test(e.path||'')||e.path.split('/').includes('..')||seen.has(e.path))continue;
  seen.add(e.path);const li=node('li');const link=node('a','Apri i dati della fonte conservati');
  link.href=`https://github.com/EmAnzi3/osservatorio-versilia/${e.encoding==='concatenate_ascii_base64_gzip_json'?'tree':'blob'}/${sourceCommit}/${e.path}`;li.append(link);snapshots.append(li);
 }
 verification.append(snapshots,node('pre',JSON.stringify(answer,null,2)));
 out.append(fold('Dettagli tecnici per verificare la lettura',verification,true));
}
document.getElementById('a7-guided').addEventListener('focusin',event=>{
 const target=event.target;if(!['risposta','titolo-chiarimento'].includes(target.id))return;
 requestAnimationFrame(()=>{if(document.activeElement===target&&!target.closest('[hidden]'))target.scrollIntoView({block:'start',behavior:'instant'});});
});
try{
 const ui=await import('./preview.mjs');
 const {default:release}=await import('./release.mjs');sourceCommit=release.repositoryCommit;
 ui.setAnswerPresentation(presentPublic);
 const choice=document.getElementById('domanda');const description=node('p',undefined,'a7-selected-question');description.id='a7-selected-question';choice.after(description);choice.setAttribute('aria-describedby',description.id);
 for(const id of ['domanda','dossier'])document.getElementById(id).addEventListener('change',selectedQuestion);selectedQuestion();
}catch(error){
 document.getElementById('stato').textContent='Evidenze non disponibili o non verificabili. Nessun risultato mostrato. Ricarica la pagina.';
 for(const id of ['dossier','domanda','mostra','domanda-testo','verifica-testo'])document.getElementById(id).disabled=true;
 document.getElementById('risposta').hidden=true;document.getElementById('risposta').replaceChildren();
}
