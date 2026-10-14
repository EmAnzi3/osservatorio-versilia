import {loadPilot} from './reader.mjs';
import release from './release.mjs';
const $ = id => document.getElementById(id);
const labels = {lavoro:'Lavoro e trasformazioni economiche',infanzia:'Infanzia e scuola'};
const node = (tag, text, className) => {const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;};
const list = items => {const ul=node('ul');for(const text of items)ul.append(node('li',text));return ul;};
const detail = (title, value) => {const d=node('details');d.append(node('summary',title),node('pre',JSON.stringify(value,null,2)));return d;};
// Snapshot links stay on a pinned, reviewed repository commit. Never accept URLs
// from questions or source strings; only canonical repository-relative paths.
const repositoryPath = path => typeof path==='string' && /^(docs|data)\/[A-Za-z0-9_./-]+$/u.test(path) && !path.split('/').includes('..');
const repoLink = (path,text,directory=false) => {if(!repositoryPath(path))return node('span',text);const a=node('a',text);a.href=`https://github.com/EmAnzi3/osservatorio-versilia/${directory?'tree':'blob'}/${release.repositoryCommit}/${path}`;return a;};
let pilot, choices, pending;
function reset(){pending=null;$('consenso').hidden=true;$('risposta').hidden=true;$('risposta').replaceChildren();}
function questions(){reset();$('domanda').replaceChildren();for(const q of choices.filter(q=>q.dossierId===$('dossier').value)){const o=node('option',q.question);o.value=q.questionId;$('domanda').append(o);}$('stato').textContent='Scegli una domanda e apri le sue evidenze.';}
function present(answer){
  const out=$('risposta');out.replaceChildren();out.hidden=false;
  const q=answer.questionPlan;
  out.append(node('h2',q.question),node('p','Risposta parzialmente supportata','badge'),node('p',q.answerBoundary));
  out.append(node('h3','Cosa non possiamo concludere'),node('p',q.interpretationLimit));
  out.append(node('h3','Dati che mancano per decidere'),list(q.missingData));
  out.append(node('h3','Evidenze disponibili'));
  for(const c of answer.components){
    const section=node('section',undefined,'component');section.setAttribute('aria-label','Componente '+c.caseId);
    section.append(node('h4',c.response.status==='computed'?'Calcolo verificato':'Operazione non calcolabile'));
    if(c.response.coverage)section.append(node('p',`Copertura: ${c.response.coverage.usable} osservazioni utilizzabili su ${c.response.coverage.requested} richieste.`));
    if(c.response.status!=='computed')section.append(node('p','Il motore ha rifiutato questa operazione. Il consenso non modifica il rifiuto.'));
    const ul=node('ul',undefined,'facts');
    for(const f of c.facts){const li=node('li');li.append(node('p',f.text));if(f.kind==='result')li.append(node('p','Perimetro del risultato (codici ISTAT): '+f.geographies.join(', ')+'.','meta'));
      const dl=node('dl');for(const [key,value] of [['Periodo',f.period],['Universo',f.population],['Definizione',f.definition],['Metodo',f.method],['Fonte',f.source]])if(value!==undefined){dl.append(node('dt',key),node('dd',typeof value==='string'?value:JSON.stringify(value)));}const provenance=node('details');provenance.append(node('summary','Fonte, universo e metodo'),dl);li.append(provenance);
      for(const e of f.evidence){if(e.path&&repositoryPath(e.path)){const p=node('p',undefined,'meta');p.append(repoLink(e.path,'Snapshot della fonte',e.encoding==='concatenate_ascii_base64_gzip_json'),node('span',` · SHA256 ${e.sha256||'non presente'} · puntatore ${e.recordPointer||e.valuePointer||e.jsonPointer||'vedi evidenza completa'}`));provenance.append(p);}}
      li.append(node('p',`Riferimento verificabile: ${c.caseId}${f.responsePointer}`,'meta'));ul.append(li);
    }section.append(ul);
    // Original codes stay visible, accompanied by the complete original response.
    if(c.response.warnings.length||c.response.reasons.length)section.append(detail('Avvertenze e motivi del motore (originali)',{warnings:c.response.warnings,reasons:c.response.reasons}));
    section.append(detail('Richiesta, risposta e provenienza originali',c));out.append(section);
  }
  out.append(node('h3','Approfondisci'),repoLink(q.dossierPath,'Leggi il dossier completo'),detail('Versione delle evidenze e richiesta selezionata',{release:answer.release,questionId:q.id,approvedPartial:pending?.approvedPartial===true,cacheKey:answer.cacheKey}));
  $('stato').textContent='Risposta disponibile. Controlla periodi, fonti e limiti di ciascuna componente.';out.focus();
}
function resolve(request){reset();pending=request;const answer=pilot.resolve(request);if(answer.resolution==='needs_confirmation'){$('consenso').hidden=false;$('stato').textContent='È necessario il consenso per esaminare le componenti parziali.';$('accetta').focus();return;}if(answer.resolution!=='resolved'){$('stato').textContent='Domanda non disponibile: scegli una domanda verificata.';return;}present(answer);}
$('selezione').addEventListener('submit',event=>{event.preventDefault();if(pilot)resolve({questionId:$('domanda').value,dossierId:$('dossier').value});});
$('dossier').addEventListener('change',questions);
$('domanda').addEventListener('change',()=>{reset();$('stato').textContent='Domanda cambiata: apri le nuove evidenze.';});
$('accetta').addEventListener('click',()=>{if(pending)resolve({...pending,approvedPartial:true});});
$('annulla').addEventListener('click',()=>{reset();$('stato').textContent='Componenti parziali non mostrate.';$('domanda').focus();});
try{
  if(!/^[a-f0-9]{40}$/u.test(release.repositoryCommit))throw new Error('invalid_repository_release');
  const response=await fetch('./bundle.json',{cache:'no-store',credentials:'omit'});if(!response.ok)throw new Error('bundle_unavailable');
  pilot=await loadPilot(await response.text(),release);choices=pilot.describe().choices;
  for(const id of [...new Set(choices.map(q=>q.dossierId))]){const o=node('option',labels[id]||id);o.value=id;$('dossier').append(o);}
  questions();for(const id of ['dossier','domanda','mostra'])$(id).disabled=false;
}catch(error){reset();$('stato').textContent='Evidenze non disponibili o non verificabili. Nessun risultato mostrato. Ricarica la preview della stessa build.';console.error('Preview unavailable:',error.message);}
