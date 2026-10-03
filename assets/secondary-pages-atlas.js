(() => {
  "use strict";
  const host = document.querySelector("ov-economy-atlas");
  if (!host) return;

  const CSS = `
    .hero{
      position:relative;width:100vw;min-height:365px;
      margin-left:calc(50% - 50vw);
      display:grid;grid-template-columns:80px minmax(0,1fr);
      align-content:center;gap:28px;
      padding:46px max(24px,calc((100vw - 1240px)/2));
      border:0;color:#fff;
      background:
        linear-gradient(90deg,rgba(6,31,49,.95) 0%,rgba(6,31,49,.84) 38%,rgba(6,31,49,.48) 69%,rgba(6,31,49,.18) 100%),
        url("https://upload.wikimedia.org/wikipedia/commons/4/40/11_Piacenza%2C_Italy_-_%E3%82%B7%E3%83%A7%E3%83%83%E3%83%94%E3%83%B3%E3%82%B0_%E3%82%A4%E3%82%A2.jpg") center 54%/cover no-repeat;
      overflow:hidden
    }
    .hero:before{
      content:"";position:absolute;
      left:max(24px,calc((100vw - 1240px)/2));top:0;
      width:72px;height:4px;background:#ffdb4d
    }
    .hero:after{
      content:"Attività commerciali · Wikimedia Commons";
      position:absolute;right:max(14px,calc((100vw - 1240px)/2));bottom:12px;
      padding:5px 8px;border-radius:6px;background:rgba(5,31,48,.62);
      color:rgba(255,255,255,.78);font-size:8px;font-weight:600
    }
    .hero>*{position:relative;z-index:2}
    .hero-symbol{
      width:68px;height:68px;border:1px solid rgba(255,255,255,.38);
      border-radius:20px 20px 20px 7px;background:rgba(255,255,255,.14);
      color:#ffdb4d;display:grid;place-items:center;
      font:800 18px var(--mono);backdrop-filter:blur(8px)
    }
    .hero .overline{color:#ffdb4d}
    .hero h1{color:#fff;text-shadow:0 3px 22px rgba(0,0,0,.24)}
    .hero p{max-width:780px;color:rgba(255,255,255,.91);font-size:15px;line-height:1.58;margin:0}
    .hero-meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}
    .meta-pill{
      background:rgba(5,31,48,.50);border:1px solid rgba(255,255,255,.24);
      border-radius:999px;padding:8px 11px;color:#fff;font-size:10px;
      font-weight:750;backdrop-filter:blur(8px)
    }
    .meta-pill strong{color:#ffdb4d}

    .atlas-export-actions{
      display:flex!important;flex-wrap:wrap;align-items:center;
      gap:6px!important;margin:0 0 18px!important
    }
    .atlas-export-actions button{
      min-height:30px!important;display:inline-flex!important;align-items:center!important;
      justify-content:center!important;border:1px solid #c9d3d1!important;
      border-radius:7px!important;background:#fbf7f0!important;color:#102f45!important;
      padding:5px 8px!important;font-size:7px!important;font-weight:760!important;
      line-height:1!important;white-space:nowrap!important
    }
    .atlas-export-actions button:hover,.atlas-export-actions button:focus-visible{
      border-color:#145b78!important;background:#e4eff2!important;outline:none
    }
    .atlas-export-actions [data-download]::before,
    .atlas-export-actions [data-print]::before{
      content:"";width:17px;height:17px;flex:0 0 17px;margin-right:5px;
      background:center/contain no-repeat
    }
    .atlas-export-actions [data-download]::before{
      background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23217346' d='M4 2h11l5 5v15H4z'/%3E%3Cpath fill='none' stroke='%23fff' stroke-width='1.4' d='M15 2v5h5'/%3E%3Cpath fill='%23fff' d='M7.1 10h2.1l1.3 2.2 1.3-2.2h2l-2.2 3.5 2.4 3.8h-2.1l-1.5-2.4-1.5 2.4H6.8l2.4-3.8z'/%3E%3C/svg%3E")
    }
    .atlas-export-actions [data-print]::before{
      background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23b84b34' d='M4 2h11l5 5v15H4z'/%3E%3Cpath fill='none' stroke='%23fff' stroke-width='1.4' d='M15 2v5h5'/%3E%3Ctext x='6.2' y='16.2' fill='%23fff' font-size='6.1' font-family='Arial,sans-serif' font-weight='700'%3EPDF%3C/text%3E%3C/svg%3E")
    }
    @media(max-width:680px){
      .hero{min-height:390px;grid-template-columns:44px minmax(0,1fr);align-content:end;gap:14px;padding:36px 20px 34px}
      .hero:before{left:20px;width:54px}
      .hero:after{right:9px;bottom:8px;font-size:7px}
      .hero-symbol{width:44px;height:44px;border-radius:13px 13px 13px 4px;font-size:13px}
      .hero h1{font-size:47px}
      .hero p{font-size:13px}
    }
  `;

  function apply() {
    const root = host.shadowRoot;
    if (!root) return false;
    if (root.querySelector("#secondary-pages-atlas-ui")) return true;
    const style = document.createElement("style");
    style.id = "secondary-pages-atlas-ui";
    style.textContent = CSS;
    root.appendChild(style);
    return true;
  }

  if (apply()) return;
  customElements.whenDefined("ov-economy-atlas").then(() => {
    let tries = 0;
    const timer = window.setInterval(() => {
      tries += 1;
      if (apply() || tries > 80) window.clearInterval(timer);
    }, 50);
  });
})();
