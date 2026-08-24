(() => {
  const root=document.querySelector('[data-opportunity-preview]');if(!root)return;
  root.querySelectorAll('.op-source-favicon').forEach(img=>img.addEventListener('error',()=>img.remove(),{once:true}));
  const select=root.querySelector('[data-op-source]');const quick=[...root.querySelectorAll('[data-op-source-quick]')];
  const sync=()=>quick.forEach(b=>{const on=Boolean(select?.value)&&b.dataset.opSourceQuick===select.value;b.classList.toggle('is-active',on);b.setAttribute('aria-pressed',on?'true':'false')});
  quick.forEach(b=>{b.setAttribute('aria-pressed','false');b.addEventListener('click',()=>{if(!select)return;select.value=select.value===b.dataset.opSourceQuick?'':b.dataset.opSourceQuick;select.dispatchEvent(new Event('change',{bubbles:true}));sync()})});
  select?.addEventListener('change',sync);root.querySelector('[data-op-reset]')?.addEventListener('click',()=>setTimeout(sync,0));sync();
})();
