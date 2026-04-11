(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const o of document.querySelectorAll('link[rel="modulepreload"]'))n(o);new MutationObserver(o=>{for(const c of o)if(c.type==="childList")for(const a of c.addedNodes)a.tagName==="LINK"&&a.rel==="modulepreload"&&n(a)}).observe(document,{childList:!0,subtree:!0});function s(o){const c={};return o.integrity&&(c.integrity=o.integrity),o.referrerPolicy&&(c.referrerPolicy=o.referrerPolicy),o.crossOrigin==="use-credentials"?c.credentials="include":o.crossOrigin==="anonymous"?c.credentials="omit":c.credentials="same-origin",c}function n(o){if(o.ep)return;o.ep=!0;const c=s(o);fetch(o.href,c)}})();const r="/data/results/";async function l(){const e=document.getElementById("app"),t=document.getElementById("loading"),s=document.getElementById("error");try{const n=await d();if(!n){t.style.display="none",s.style.display="block";return}u(n),t.style.display="none",e.style.display="block"}catch(n){console.error("Failed to load report:",n),t.style.display="none",s.style.display="block"}}async function d(){const e=[],t=new Date;for(let s=0;s<7;s++){const n=new Date(t);n.setDate(n.getDate()-s),e.push(p(n))}for(const s of e)try{const n=await fetch(`${r}${s}.json`);if(n.ok)return await n.json()}catch{}return null}function p(e){const t=e.getFullYear(),s=String(e.getMonth()+1).padStart(2,"0"),n=String(e.getDate()).padStart(2,"0");return`${t}-${s}-${n}`}function u(e){document.getElementById("report-date").textContent=`${e.date} ${e.weekday}`;const t=document.getElementById("cards-container");e.cards.length===0?t.innerHTML='<p class="empty-msg">今日美股无板块涨跌幅超过 2%</p>':t.innerHTML=e.cards.map(f).join("");const s=document.getElementById("quiet-section");e.quiet_sectors.length>0&&(s.style.display="block",document.getElementById("quiet-list").innerHTML=e.quiet_sectors.map(g).join(""))}function f(e){const t=e.us_change_pct>=0,s=t?"up":"down",o=`${t?"+":""}${e.us_change_pct.toFixed(2)}%`;let c="";if(e.prob_high_open!==null&&e.prob_high_open!==void 0){const a=(e.prob_high_open*100).toFixed(0),i=`${e.avg_impact>=0?"+":""}${e.avg_impact.toFixed(2)}%`;c=`
      <div class="card-prob">${a}% <span>概率高开</span></div>
      <div class="card-impact">平均幅度 ${i}</div>
    `}else c='<div class="card-prob" style="font-size:14px;color:#aaa">样本不足</div>';return`
    <div class="card">
      <div class="card-header">
        <span class="card-us">${e.us_etf} ${e.us_name}</span>
        <span class="card-change ${s}">${o}</span>
      </div>
      <div class="card-arrow">↓</div>
      <div class="card-cn">→ A股 ${e.cn_name}</div>
      ${c}
      <span class="card-etf">${e.cn_etf_name}(${e.cn_etf_code})</span>
      ${e.sample_count>0?`<div class="card-meta">(${e.window_days}日 · ${e.sample_count}次样本)</div>`:""}
    </div>
  `}function g(e){const t=e.us_change_pct>=0,s=t?"up":"down",n=t?"+":"";return`
    <div class="quiet-item">
      <span>${e.us_name} (${e.us_etf})</span>
      <span class="quiet-change ${s}">${n}${e.us_change_pct.toFixed(2)}%</span>
    </div>
  `}l();
