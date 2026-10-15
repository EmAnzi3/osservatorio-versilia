// Public wording and layout only. The original reader, answer and export stay intact.
import {loadEducation,presentEducation} from './education.mjs';
let sourceCommit, education;
const node=(tag,text,className)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;};
const list=items=>{const ul=node('ul');for(const item of items)ul.append(node('li',item));return ul;};
const fold=(title,child,technical=false)=>{const el=node('details');if(technical)el.dataset.a7Technical='true';el.append(node('summary',title),child);return el;};
const introductions={
 'lavoro-centrale':'Vivere e lavorare a Massarosa: due prospettive per leggere il cambiamento. Il confronto con Viareggio affianca l’occupazione dei residenti, le attività economiche e gli addetti presenti sul territorio.',
 'lavoro-1':'Che cosa cambia tra Massarosa e Viareggio? Guardiamo quante persone lavorano fra i residenti e come sono cambiate le unità locali: ogni confronto mantiene il proprio periodo di riferimento.',
 'lavoro-2':'Industria e servizi raccontano due volti dell’economia di Massarosa. I grafici affiancano valore aggiunto e retribuzioni nell’industria e mostrano i due anni disponibili per i servizi.',
 'infanzia-centrale':'Dai primi anni di vita alla scuola: come si presenta la rete dei servizi? Partiamo dalla capacità dei servizi educativi, dagli alunni e dalle classi per mettere a fuoco la situazione di Massarosa.',
 'infanzia-1':'Quale capacità offrono i servizi per la prima infanzia rispetto ai bambini residenti? Il confronto fra i Comuni aiuta a leggere differenze e dotazioni potenziali.',
 'infanzia-2':'Una scuola è fatta di alunni, tempo, spazi e opportunità. Affianchiamo dimensione delle classi, tempo pieno e caratteristiche degli edifici; i risultati educativi restano una prospettiva distinta.'
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
 out.classList.remove('edu-answer');
 document.getElementById('a7-guided').classList.toggle('education-reading',q.id==='infanzia-centrale');
 if(q.id==='infanzia-centrale'){presentEducation(out,answer,education);return;}
 out.append(node('p','La tua domanda','eyebrow'),node('h2',q.question));
 out.append(node('p',introductions[q.id]||q.interpretationLimit,'a7-answer-intro'),node('h3',q.id.startsWith('lavoro')?'Lavoro e attività: le due facce del territorio':'Bambini, servizi e scuole: il territorio a confronto'));
 for(const c of answer.components){
  const section=node('section',undefined,'component');section.setAttribute('aria-label','Dati della lettura');
  const first=c.facts[0];const title=first?first.text.split(' — ')[0]:'Un confronto che non possiamo calcolare';
  section.append(node('h4',title,'a7-indicator-title'));
  if(c.response.coverage && c.response.coverage.usable<c.response.coverage.requested)section.append(node('p',`Dati disponibili per ${c.response.coverage.usable} delle ${c.response.coverage.requested} osservazioni richieste. I mancanti restano esclusi.`, 'a7-coverage'));
  if(c.response.status!=='computed')section.append(node('p','I dati disponibili non permettono questo calcolo. Il consenso a leggere risultati parziali non cambia questo limite.'));
  // Plot only comparable observations already returned by the certified reader.
  // Results/pooled totals remain text: never mix them into territorial bars.
  const observations=c.facts.filter(f=>f.kind==='observation');
  const base=observations[0];
  const comparable=base&&observations.length>1&&observations.every(f=>
   f.unit===base.unit&&f.definition===base.definition&&f.dimension===base.dimension&&f.population===base.population&&f.method===base.method&&(f.source===base.source||(f.geography===base.geography&&new URL(f.source).origin===new URL(base.source).origin)))&&
   (observations.every(f=>f.period===base.period)||observations.every(f=>f.geography===base.geography));
  const numeric=observations.filter(f=>typeof f.value==='number'&&Number.isFinite(f.value));
  const plot=comparable&&numeric.length>0&&numeric.every(f=>f.value>=0);
  const maximum=plot?(base.unit==='percent'&&numeric.every(f=>f.value<=100)&&!base.definition.includes('cumulative')?100:Math.max(...numeric.map(f=>f.value))||1):1;
  if(plot){section.dataset.a7Chart='bars';section.append(node('p',`Confronto visivo · ${base.unit==='percent'?'scala percentuale':base.unit==='millionCurrency'?'milioni di euro':base.unit==='currency'?'euro':base.unit==='studentsPerClass'?'alunni per classe':'persone'} · da 0 a ${new Intl.NumberFormat('it-IT',{maximumFractionDigits:2}).format(maximum)}. ${observations.every(f=>f.period===base.period)?'Periodo: '+base.period:'Anni osservati: '+observations.map(f=>f.period).join(' e ')+'. Importi nominali; non è un andamento annuale.'}`,'meta'));}
  const ul=node('ul',undefined,'facts');
  for(const f of c.facts){
   const li=node('li');
   // The measure is named once in the component heading. Keep canonical
   // wording, periods and precision in export; shorten only matching labels.
   const prefix=title+' — ';
   const label=f.text.startsWith(prefix)?f.text.slice(prefix.length):f.text;
   li.append(node('p',label.replace('persone/addetti secondo definizione.','persone.'),'a7-fact'));
   if(plot&&f.kind==='observation'){
    if(typeof f.value==='number'&&Number.isFinite(f.value)){
     const track=node('div',undefined,'a7-bar-track');track.setAttribute('aria-hidden','true');
     const bar=node('span',undefined,'a7-bar');bar.style.width=(100*f.value/maximum)+'%';
     bar.dataset.value=String(f.value);bar.dataset.maximum=String(maximum);bar.dataset.geography=f.geography;bar.dataset.period=f.period;
     if(f.geography==='046018')bar.classList.add('a7-bar-focus');track.append(bar);li.append(track);
    }else li.append(node('p','Dato non disponibile: nessuna barra e nessun valore zero attribuito.','meta'));
   }
   if(f.period!==undefined)li.append(node('p','Periodo: '+f.period,'meta'));
   if(f.population!==undefined)li.append(node('p',populations[f.population]||'Il perimetro di questo dato è descritto nei dettagli di verifica.','a7-scope'));
   li.append(source(f.source));ul.append(li);
  }
  section.append(ul);
  if(c.response.warnings.length)section.append(fold('Come leggere questo dato',list([...new Set(c.response.warnings.map(w=>warnings[w]||'Sono presenti ulteriori limiti metodologici, conservati nei dettagli di verifica.'))])));
  out.append(section);
 }
 out.append(node('h3','Per interpretare i confronti'),node('p',q.answerBoundary,'a7-answer-boundary'));
 out.append(node('h3','Che cosa ci racconta questo confronto'),node('p',q.interpretationLimit));
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
new MutationObserver(()=>{if(document.getElementById('risposta').hidden)document.getElementById('a7-guided').classList.remove('education-reading');}).observe(document.getElementById('risposta'),{attributes:true,attributeFilter:['hidden']});
document.getElementById('a7-guided').addEventListener('focusin',event=>{
 const target=event.target;if(!['risposta','titolo-chiarimento'].includes(target.id))return;
 requestAnimationFrame(()=>{if(document.activeElement===target&&!target.closest('[hidden]'))target.scrollIntoView({block:'start',behavior:'instant'});});
});
try{
 const {default:release}=await import('./release.mjs');sourceCommit=release.repositoryCommit;
 education=await loadEducation(release);
 const ui=await import('./preview.mjs');
 ui.setAnswerPresentation(presentPublic);
 const choice=document.getElementById('domanda');const description=node('p',undefined,'a7-selected-question');description.id='a7-selected-question';choice.after(description);choice.setAttribute('aria-describedby',description.id);
 for(const id of ['domanda','dossier'])document.getElementById(id).addEventListener('change',selectedQuestion);selectedQuestion();
 if(new URLSearchParams(location.search).get('lettura')==='educazione'){
  document.getElementById('dossier').value='infanzia';document.getElementById('dossier').dispatchEvent(new Event('change'));
  document.getElementById('domanda').value='infanzia-centrale';selectedQuestion();document.getElementById('mostra').click();
 }
}catch(error){
 document.getElementById('stato').textContent='Evidenze non disponibili o non verificabili. Nessun risultato mostrato. Ricarica la pagina.';
 for(const id of ['dossier','domanda','mostra','domanda-testo','verifica-testo'])document.getElementById(id).disabled=true;
 document.getElementById('risposta').hidden=true;document.getElementById('risposta').replaceChildren();
}
