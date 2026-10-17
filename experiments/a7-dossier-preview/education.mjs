// A curated public reading. Numbers and prose are generated together from A6.
// No question text or network response is interpolated into this HTML.
const make=(tag,text,cls)=>{const e=document.createElement(tag);if(text)e.textContent=text;if(cls)e.className=cls;return e;};
export async function loadEducation(release){
 const response=await fetch(new URL('./education.json',import.meta.url),{cache:'no-store',credentials:'omit'});
 if(!response.ok)throw new Error('education_unavailable');
 const text=await response.text();
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))),b=>b.toString(16).padStart(2,'0')).join('');
 if(digest!==release.educationSha256)throw new Error('education_integrity_mismatch');
 const model=JSON.parse(text);
 if(model.bundleSha256!==release.bundleSha256||model.repositoryCommit!==release.repositoryCommit||model.questionId!=='infanzia-centrale')throw new Error('education_release_mismatch');
 model.pdfSha256=release.educationPdfSha256;
 return model;
}
export function presentEducation(out,answer,model){
 const q=answer.questionPlan;
 if(q.id!==model.questionId||JSON.stringify([...q.requiredCaseRefs,...q.contextCaseRefs])!==JSON.stringify(model.requiredCaseRefs))throw new Error('education_question_mismatch');
 out.classList.add('edu-answer');delete document.getElementById('stato').dataset.educationError;
 out.append(make('p','MASSAROSA · OFFERTA EDUCATIVA · '+model.period,'edu-kicker'),make('h2',q.question));
 const tools=make('div',null,'edu-tools');
 const pdf=make('a','Scarica il rapporto PDF','edu-download');pdf.href=new URL('./education.pdf',import.meta.url).href;pdf.download='Massarosa-offerta-educativa.pdf';pdf.dataset.educationPdf='true';pdf.addEventListener('click',async event=>{
  event.preventDefault();if(pdf.dataset.loading==='true')return;pdf.dataset.loading='true';
  try{
   const response=await fetch(pdf.href,{cache:'no-store',credentials:'omit'});if(!response.ok)throw new Error('pdf_unavailable');
   const bytes=await response.arrayBuffer();
   const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
   if(digest!==model.pdfSha256)throw new Error('pdf_integrity_mismatch');
   const url=URL.createObjectURL(new Blob([bytes],{type:'application/pdf'}));const a=make('a');a.href=url;a.download=pdf.download;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
   const status=document.getElementById('stato');delete status.dataset.educationError;status.textContent='';
  }catch{document.getElementById('stato').dataset.educationError='true';document.getElementById('stato').textContent='Rapporto PDF non disponibile o non verificabile. Riprova: la lettura resta consultabile.';}
  finally{delete pdf.dataset.loading;}
 });tools.append(pdf);
 const back=make('button','Cambia domanda');back.type='button';back.className='edu-change';back.addEventListener('click',()=>{history.replaceState(null,'',location.pathname);document.getElementById('dossier').dispatchEvent(new Event('change'));document.getElementById('a7-guided').classList.remove('education-reading');document.getElementById('domanda').focus();});tools.append(back);
 const dossier=make('a','Approfondisci il dossier');dossier.href='?lettura=educazione#nidi';dossier.dataset.educationDossier='true';tools.append(dossier);out.append(tools);
 const nav=make('nav',null,'edu-navigation');nav.setAttribute('aria-label','Capitoli del dossier educativo');
 const body=make('div',null,'edu-body');const panels=[];
 const chapters=[{id:'sintesi',title:'In sintesi',html:model.overview},...model.chapters];
 const show=(id,focus=false)=>{
  if(!chapters.some(c=>c.id===id))id='sintesi';
  for(const panel of panels){panel.hidden=panel.id!=='educazione-'+id;}
  for(const link of nav.querySelectorAll('a')){if(link.dataset.chapter===id)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');}
  if(focus){const heading=body.querySelector('section:not([hidden]) h3');heading.focus();heading.scrollIntoView({block:'start',behavior:'instant'});}
 };
 for(const c of chapters){
  const link=make('a',c.title);link.href='?lettura=educazione#'+c.id;link.dataset.chapter=c.id;
  link.addEventListener('click',event=>{event.preventDefault();history.replaceState(null,'',link.href);show(c.id,true);});nav.append(link);
  const panel=make('section',null,'edu-panel');panel.id='educazione-'+c.id;panel.setAttribute('aria-labelledby',panel.id+'-title');
  const title=make('h3',c.id==='sintesi'?'Famiglie e scuola: la Versilia a confronto':c.title);title.id=panel.id+'-title';title.tabIndex=-1;panel.append(title);
  // Build-produced markup, checked against the release hash above. No user HTML.
  const content=make('div');content.innerHTML=c.html;panel.append(content);body.append(panel);panels.push(panel);
 }
 dossier.addEventListener('click',event=>{event.preventDefault();history.replaceState(null,'',dossier.href);show('nidi',true);});
 out.append(nav,body);
 const boundary=make('details',null,'edu-boundary');boundary.append(make('summary','Fonti, perimetro e limiti della risposta'),make('p',model.answerBoundaryPublic,'a7-answer-boundary'),make('p',q.interpretationLimit));out.append(boundary);
 const verification=make('details');verification.dataset.a7Technical='true';verification.append(make('summary','Dati originali e verifica tecnica'),make('pre',JSON.stringify(answer,null,2)));out.append(verification);
 const territorialVerification=make('details');territorialVerification.dataset.educationTechnical='true';territorialVerification.append(make('summary','Verifica dei confronti sui sette Comuni'),make('p','Richieste e risposte del medesimo motore, conservate integralmente.'),make('pre',JSON.stringify(model.territorialCases,null,2)));out.append(territorialVerification);
 show(location.search.includes('lettura=educazione')?location.hash.slice(1):'sintesi');
}
