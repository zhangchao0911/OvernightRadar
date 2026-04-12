(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const n of document.querySelectorAll('link[rel="modulepreload"]'))a(n);new MutationObserver(n=>{for(const l of n)if(l.type==="childList")for(const i of l.addedNodes)i.tagName==="LINK"&&i.rel==="modulepreload"&&a(i)}).observe(document,{childList:!0,subtree:!0});function s(n){const l={};return n.integrity&&(l.integrity=n.integrity),n.referrerPolicy&&(l.referrerPolicy=n.referrerPolicy),n.crossOrigin==="use-credentials"?l.credentials="include":n.crossOrigin==="anonymous"?l.credentials="omit":l.credentials="same-origin",l}function a(n){if(n.ep)return;n.ep=!0;const l=s(n);fetch(n.href,l)}})();function x(e,t){e.querySelectorAll(".tab-item").forEach(s=>{s.addEventListener("click",()=>{const a=s.dataset.view;t(a)})})}function A(e){const t=document.getElementById("tab-nav");t&&t.querySelectorAll(".tab-item").forEach(s=>{s.classList.toggle("active",s.dataset.view===e)})}const C="/OvernightRadar/data/";async function I(e,t=7){const s=[],a=new Date;for(let n=0;n<t;n++){const l=new Date(a);l.setDate(l.getDate()-n),s.push(B(l))}for(const n of s)try{const l=await fetch(`${C}${e}/${n}.json`);if(l.ok)return await l.json()}catch{}return null}function B(e){const t=e.getFullYear(),s=String(e.getMonth()+1).padStart(2,"0"),a=String(e.getDate()).padStart(2,"0");return`${t}-${s}-${a}`}function F(){return I("watchlist")}function N(){return I("results")}const k={4:{label:"🔴 强烈看多",cssClass:"sentiment-label-4"},3:{label:"🔴 偏多",cssClass:"sentiment-label-3"},2:{label:"⚪ 中性",cssClass:"sentiment-label-2"},1:{label:"🟢 偏空",cssClass:"sentiment-label-1"},0:{label:"🟢 强烈看空",cssClass:"sentiment-label-0"}};function E(e){return e==null?"—":`${e>=0?"+":""}${e.toFixed(2)}%`}function R(e){const t=e.us_change_pct>=0?"up":"down",s=k[e.sentiment_level]||k[2],a=e.relative_strength>=0?"跑赢大盘":"跑输大盘",n=e.relative_strength>=0?"+":"",l=e.volatility.is_abnormal?`异常波动 ${e.volatility.vol_multiple}σ`:"正常波动";let i="平盘";e.trend.direction==="up"&&e.trend.consecutive_days>0?i=`连涨${e.trend.consecutive_days}天+${e.trend.cumulative_pct}%`:e.trend.direction==="down"&&e.trend.consecutive_days>0&&(i=`连跌${e.trend.consecutive_days}天${e.trend.cumulative_pct}%`);const o=e.supply_chain.map(c=>{const d=c.change_pct!==null&&c.change_pct!==void 0?c.change_pct>=0?"up":"down":"na";return`<div class="stock-item">
      <span class="stock-name">${c.name}(${c.code})</span>
      <span class="stock-change ${d}">${E(c.change_pct)}</span>
    </div>`}).join("");let r="";return e.cn_etf_code&&(r=`<span class="card-cn-etf">${e.cn_etf_name}(${e.cn_etf_code})</span>`),`
    <div class="card sentiment-${e.sentiment_level}">
      <div class="card-sentiment ${s.cssClass}">${s.label}</div>
      <div class="card-header">
        <span class="card-us">${e.us_etf} ${e.us_name}</span>
        <span class="card-change ${t}">${E(e.us_change_pct)}</span>
      </div>
      <div class="card-detail">
        <span class="card-rs">${a}${n}${e.relative_strength.toFixed(1)}%</span>
      </div>
      <div class="card-detail">${l} · ${i}</div>
      <div class="card-cn">→ A股${e.cn_name} ${r}</div>
      <div class="card-stocks">${o}</div>
    </div>
  `}function D(e){return e==null?"—":`${e>=0?"+":""}${e.toFixed(2)}%`}async function O(e,t){const s=await N();if(!s){e.innerHTML='<p class="empty-state">暂无雷达数据</p>',t.innerHTML=`
      <h1 class="title">隔夜雷达</h1>
      <p class="slogan">昨夜美股异动，今日A股看点</p>
    `;return}const a={sp500:"标普",nasdaq:"纳指",dow:"道指"};let n="";for(const[i,o]of Object.entries(a))if(s.market_indices&&s.market_indices[i]){const r=s.market_indices[i].change_pct,c=r>=0?"up":"down";n+=`<span class="index-item">${o}<span class="${c}">${D(r)}</span></span>`}t.innerHTML=`
    <h1 class="title">隔夜雷达</h1>
    <p class="slogan">昨夜美股异动，今日A股看点</p>
    <div class="market-indices">${n}</div>
    <p class="date">${s.market_summary} · ${s.date} ${s.weekday}</p>
  `;const l=`
    <div class="disclaimer wl-top-disclaimer">
      <p>仅供数据参考，不构成投资建议。数据来源：Yahoo Finance、AKShare、公开市场数据。</p>
    </div>
  `;!s.sectors||s.sectors.length===0?e.innerHTML=l+'<p class="empty-state">暂无板块数据</p>':e.innerHTML=l+s.sectors.map(R).join("")}function V(e){return e==null||isNaN(e)?"#e8e8e8":e>=5?"#1b7a1b":e>=2?"#3ba53b":e>=.5?"#81c784":e>0?"#c8e6c9":e===0?"#e8e8e8":e>-.5?"#ffcdd2":e>-2?"#e57373":e>-5?"#d32f2f":"#b71c1c"}function q(e,t){return t==="change_pct"?e.change_pct:e.rel&&t in e.rel?e.rel[t]:null}function j(e){return e==null||isNaN(e)?"—":`${e>=0?"+":""}${e.toFixed(2)}%`}function W(e,t){const s=q(e,t),a=V(s),n=j(s),l=e.has_cn_mapping?'<span class="wl-cn-badge" title="有A股映射">A</span>':"";return`
    <div class="wl-block" data-ticker="${e.ticker}" style="background-color: ${a}">
      <span class="wl-block-ticker">${e.ticker}</span>
      <span class="wl-block-name">${e.name||""}</span>
      <span class="wl-block-value">${n}</span>
      ${l}
    </div>
  `}function P(e,t){for(const s of Object.values(e)){if(!s.etfs)continue;const a=s.etfs.find(n=>n.ticker===t);if(a)return a}return null}function U(e,t,s,a){let n=s;const l=t.find(r=>r.key===s),i=l?l.desc:"",o=t.map(r=>`<button class="wl-tab${r.key===s?" active":""}" data-key="${r.key}">${r.label}</button>`).join("");e.innerHTML=`
    <div class="wl-tabs-row">${o}</div>
    <p class="wl-indicator-desc">${i}</p>
  `,e.querySelectorAll(".wl-tab").forEach(r=>{r.addEventListener("click",()=>{const c=r.dataset.key;if(c===n)return;n=c,e.querySelectorAll(".wl-tab").forEach(u=>u.classList.remove("active")),r.classList.add("active");const d=t.find(u=>u.key===c),h=e.querySelector(".wl-indicator-desc");h&&d&&(h.textContent=d.desc),a(c)})})}function Y(e,t,s={}){if(!t||t.length<2)return;const a=e.getContext("2d"),n=s.width||e.width||300,l=s.height||e.height||80;e.width=n,e.height=l;const i=Math.min(...t),r=Math.max(...t)-i||1,c=2,d=n-c*2,h=l-c*2,u=t[0],$=t[t.length-1],S=$>=u?"#2e7d32":"#c62828";a.clearRect(0,0,n,l),a.beginPath(),a.strokeStyle=S,a.lineWidth=1.5,a.lineJoin="round";for(let f=0;f<t.length;f++){const b=c+f/(t.length-1)*d,_=c+h-(t[f]-i)/r*h;f===0?a.moveTo(b,_):a.lineTo(b,_)}a.stroke();const y=a.createLinearGradient(0,0,0,l);y.addColorStop(0,$>=u?"rgba(46,125,50,0.15)":"rgba(198,40,40,0.15)"),y.addColorStop(1,"rgba(255,255,255,0)"),a.lineTo(c+d,l),a.lineTo(c,l),a.closePath(),a.fillStyle=y,a.fill()}let g=null;function m(e){return e==null||isNaN(e)?"—":`${e>=0?"+":""}${e.toFixed(2)}%`}function M(e,t){if(!t)return;if(!e){t.style.display="none",g=null;return}if(g===e.ticker){t.style.display="none",g=null;return}g=e.ticker;const s=e.rel?`
      <div class="wl-rel-grid">
        <div class="wl-rel-item"><span class="wl-rel-label">REL5</span><span class="wl-rel-value">${m(e.rel.rel_5)}</span></div>
        <div class="wl-rel-item"><span class="wl-rel-label">REL20</span><span class="wl-rel-value">${m(e.rel.rel_20)}</span></div>
        <div class="wl-rel-item"><span class="wl-rel-label">REL60</span><span class="wl-rel-value">${m(e.rel.rel_60)}</span></div>
        <div class="wl-rel-item"><span class="wl-rel-label">REL120</span><span class="wl-rel-value">${m(e.rel.rel_120)}</span></div>
      </div>
    `:"",a=e.has_cn_mapping?`
      <div class="wl-cn-mapping">
        <span class="wl-cn-badge-detail">有 A 股映射</span>
        <span class="wl-cn-hint">数据来源：隔夜雷达</span>
      </div>
    `:"";t.innerHTML=`
    <div class="wl-detail-header">
      <h3 class="wl-detail-title">${e.ticker} · ${e.name}</h3>
      <button class="wl-detail-close" id="wl-detail-close">✕</button>
    </div>
    <div class="wl-detail-price">
      <span class="wl-detail-price-value">$${e.price.toFixed(2)}</span>
      <span class="wl-detail-change">${m(e.change_pct)}</span>
      <span class="wl-detail-ytd">YTD: ${m(e.ytd)}</span>
    </div>
    <canvas id="sparkline-canvas" width="300" height="80"></canvas>
    ${s}
    ${a}
  `,t.style.display="block",document.getElementById("wl-detail-close").addEventListener("click",()=>{t.style.display="none",g=null});const n=document.getElementById("sparkline-canvas");n&&e.history&&e.history.length>=2&&Y(n,e.history,{width:n.parentElement.clientWidth-32}),t.scrollIntoView({behavior:"smooth",block:"nearest"})}const G=[{key:"change_pct",label:"日涨跌",desc:"当日涨跌幅 (%)"},{key:"rel_5",label:"5日强弱",desc:"近5日相对标普500的超额收益"},{key:"rel_20",label:"20日强弱",desc:"近20日(约1月)相对标普500的超额收益"},{key:"rel_60",label:"60日强弱",desc:"近60日(约1季)相对标普500的超额收益"},{key:"rel_120",label:"120日强弱",desc:"近120日(约半年)相对标普500的超额收益"}],z=["broad","equal_weighted","market_cap_weighted","factors","growth","thematic","ark"];let w="change_pct",p=null;async function J(e,t){if(p||(p=await F()),!p){t.innerHTML=`
      <h1 class="title">市场观察表</h1>
      <p class="slogan">Market Watchlist · 美股 ETF 相对强度热力图</p>
    `,e.innerHTML='<p class="empty-state">暂无热力图数据</p>';return}t.innerHTML=`
    <h1 class="title">市场观察表</h1>
    <p class="slogan">Market Watchlist · 美股 ETF 相对强度热力图</p>
    <p class="date">更新时间: ${p.updated_at||p.date}</p>
  `;const s=`
    <div class="disclaimer wl-top-disclaimer">
      <p>仅供数据参考，不构成投资建议。数据来源：TheMarketMemo、Yahoo Finance。</p>
      <p>REL (相对强度) = ETF 涨跌幅 - 标普500 涨跌幅，正值表示跑赢大盘。</p>
    </div>
  `,a='<nav class="wl-indicators" id="wl-indicators"></nav>',n='<div id="wl-heatmap"></div>',l='<section id="wl-detail" class="wl-detail" style="display:none"></section>';e.innerHTML=s+a+n+l,U(document.getElementById("wl-indicators"),G,w,i=>{w=i,L(document.getElementById("wl-heatmap"),p.groups,w)}),L(document.getElementById("wl-heatmap"),p.groups,w),M(null,null)}function L(e,t,s){if(!t){e.innerHTML='<p class="empty-state">暂无数据</p>';return}let a="";for(const n of z){const l=t[n];!l||!l.etfs||l.etfs.length===0||(a+=`
      <div class="wl-group">
        <h2 class="wl-group-title">${l.display_name}</h2>
        <div class="wl-blocks">
          ${l.etfs.map(i=>W(i,s)).join("")}
        </div>
      </div>
    `)}e.innerHTML=a,e.querySelectorAll(".wl-block").forEach(n=>{n.addEventListener("click",()=>{const l=n.dataset.ticker,i=P(t,l);if(i){const o=document.getElementById("wl-detail");M(i,o)}})})}const T={heatmap:J,radar:O},v="heatmap";async function K(){const e=document.getElementById("app"),t=document.getElementById("loading"),s=document.getElementById("error"),a=document.getElementById("tab-nav");try{x(a,n=>{window.location.hash=`#/${n}`}),window.addEventListener("hashchange",()=>H()),await H(),t.style.display="none",e.style.display="block",a.style.display="flex"}catch(n){console.error("Failed to initialize app:",n),t.style.display="none",s.style.display="block"}}async function H(){const t=(window.location.hash||"").replace("#/","")||v;if(!T[t]){console.warn(`Unknown view: ${t}, falling back to ${v}`),window.location.hash=`#/${v}`;return}const s=document.getElementById("view-container"),a=document.getElementById("app-header");A(t),await T[t](s,a)}K();
