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
 if(model.schemaVersion!==2||Object.keys(model.townReadings||{}).length!==7||JSON.stringify(Object.keys(model.townReadings).sort())!==JSON.stringify(Object.keys(release.educationPdfs||{}).sort()))throw new Error('education_territories_mismatch');
 for(const [code,view] of Object.entries(model.townReadings))if(view.focusCode!==code||view.repositoryCommit!==model.repositoryCommit||view.bundleSha256!==model.bundleSha256||!/^education(?:-[0-9]{6})?\.pdf$/.test(release.educationPdfs[code].file)||!/^[a-f0-9]{64}$/.test(release.educationPdfs[code].sha256))throw new Error('education_territory_mismatch');
 model.pdfs=release.educationPdfs;
 model.pdfSha256=release.educationPdfSha256;
 return model;
}
export function presentEducation(out,answer,source,preservedExport=[]){
 out.replaceChildren();
 const status=document.getElementById('stato');delete status.dataset.educationError;status.textContent='';
 const code=new URL(location.href).searchParams.get('comune')||source.focusCode;
 const backlink=document.querySelector('[data-a7-town-link]');
 const setBacklink=view=>{if(backlink){backlink.hidden=!view;if(view){backlink.href=view.townRoute;backlink.textContent='scheda di '+view.territory;}}};
 const selector=make('div',null,'edu-town-selector');
 const label=make('label','Di quale Comune vuoi conoscere l’offerta educativa?');label.htmlFor='comune-educazione';
 const select=make('select');select.id='comune-educazione';
 const placeholder=make('option','Scegli un Comune');placeholder.value='';placeholder.disabled=true;select.append(placeholder);
 for(const [key,view] of Object.entries(source.townReadings).sort((a,b)=>a[1].territory.localeCompare(b[1].territory,'it'))){const option=make('option',view.territory);option.value=key;select.append(option);}
 select.value=Object.hasOwn(source.townReadings,code)?code:'';
 select.addEventListener('change',()=>{const button=out.querySelector('#esporta-risposta');const exportNodes=button?[button,button.nextElementSibling].filter(Boolean):preservedExport;const url=new URL(location.href);url.searchParams.set('lettura','educazione');if(select.value===source.focusCode)url.searchParams.delete('comune');else url.searchParams.set('comune',select.value);history.replaceState(null,'',url);presentEducation(out,answer,source,exportNodes);const heading=out.querySelector('h2');if(heading){heading.tabIndex=-1;heading.focus();}});
 selector.append(label,select);out.append(selector);
 if(!Object.hasOwn(source.townReadings,code)){setBacklink(null);out.append(make('p','Questo Comune non è disponibile nella lettura. Scegli uno dei sette Comuni della Versilia.'));return;}
 const model={...source,...source.townReadings[code],pdfSha256:source.pdfs[code].sha256};
 setBacklink(model);
 const chapterUrl=id=>{const url=new URL(location.href);url.search='';url.searchParams.set('lettura','educazione');if(code!==source.focusCode)url.searchParams.set('comune',code);url.hash=id;return url.pathname+url.search+url.hash;};
 const q=answer.questionPlan;
 if(q.id!==model.questionId||JSON.stringify([...q.requiredCaseRefs,...q.contextCaseRefs])!==JSON.stringify(model.requiredCaseRefs))throw new Error('education_question_mismatch');
 out.classList.add('edu-answer');delete document.getElementById('stato').dataset.educationError;
 out.append(make('p',model.territory.toUpperCase()+' · OFFERTA EDUCATIVA · '+model.period,'edu-kicker'),make('h2',q.question));
 const tools=make('div',null,'edu-tools');
 const pdf=make('a','Scarica il rapporto PDF','edu-download');pdf.href=new URL('./'+source.pdfs[code].file,import.meta.url).href;pdf.download=model.territory+'-offerta-educativa.pdf';pdf.dataset.educationPdf='true';pdf.addEventListener('click',async event=>{
  event.preventDefault();if(pdf.dataset.loading==='true')return;pdf.dataset.loading='true';
  try{
   const response=await fetch(pdf.href,{cache:'no-store',credentials:'omit'});if(!response.ok)throw new Error('pdf_unavailable');
   const bytes=await response.arrayBuffer();
   const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
   if(digest!==model.pdfSha256)throw new Error('pdf_integrity_mismatch');
   if(!pdf.isConnected)return;
   const url=URL.createObjectURL(new Blob([bytes],{type:'application/pdf'}));const a=make('a');a.href=url;a.download=pdf.download;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
   const status=document.getElementById('stato');delete status.dataset.educationError;status.textContent='';
  }catch{if(pdf.isConnected){document.getElementById('stato').dataset.educationError='true';document.getElementById('stato').textContent='Rapporto PDF non disponibile o non verificabile. Riprova: la lettura resta consultabile.';}}
  finally{delete pdf.dataset.loading;}
 });tools.append(pdf);
 const back=make('button','Cambia domanda');back.type='button';back.className='edu-change';back.addEventListener('click',()=>{setBacklink(source);history.replaceState(null,'',location.pathname);document.getElementById('dossier').dispatchEvent(new Event('change'));document.getElementById('a7-guided').classList.remove('education-reading');document.getElementById('domanda').focus();});tools.append(back);
 const dossier=make('a','Approfondisci il dossier');dossier.href=chapterUrl('nidi');dossier.dataset.educationDossier='true';tools.append(dossier);out.append(tools);
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
  const link=make('a',c.title);link.href=chapterUrl(c.id);link.dataset.chapter=c.id;
  link.addEventListener('click',event=>{event.preventDefault();history.replaceState(null,'',link.href);show(c.id,true);});nav.append(link);
  const panel=make('section',null,'edu-panel');panel.id='educazione-'+c.id;panel.setAttribute('aria-labelledby',panel.id+'-title');
  const title=make('h3',c.id==='sintesi'?'Famiglie e scuola: il profilo di '+model.territory:c.title);title.id=panel.id+'-title';title.tabIndex=-1;panel.append(title);
  // Build-produced markup, checked against the release hash above. No user HTML.
  const content=make('div');content.innerHTML=c.html;panel.append(content);body.append(panel);panels.push(panel);
 }
 dossier.addEventListener('click',event=>{event.preventDefault();history.replaceState(null,'',dossier.href);show('nidi',true);});
 out.append(nav,body);
 const boundary=make('details',null,'edu-boundary');boundary.append(make('summary','Fonti, perimetro e limiti della risposta'),make('p',model.answerBoundaryPublic,'a7-answer-boundary'),make('p',q.interpretationLimit));out.append(boundary);
 const verification=make('details');verification.dataset.a7Technical='true';verification.append(make('summary','Dati del pilota originale di Massarosa'),make('pre',JSON.stringify(answer,null,2)));out.append(verification);
 for(const element of preservedExport)verification.append(element);
 const territorialVerification=make('details');territorialVerification.dataset.educationTechnical='true';territorialVerification.append(make('summary','Verifica dei confronti sui sette Comuni'),make('p','Richieste e risposte del medesimo motore, conservate integralmente.'),make('pre',JSON.stringify(model.territorialCases,null,2)));out.append(territorialVerification);
 show(location.search.includes('lettura=educazione')?location.hash.slice(1):'sintesi');
}
