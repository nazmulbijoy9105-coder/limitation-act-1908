#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""upgrade_production.py — final production build for limitation-act-1908/.
Fixes: wireUI crash, silent init failures, BN-optional-chaining, security
headers, cache strategy, robots, social meta, cache-busting, CRLF."""
import json
from pathlib import Path

V = "2"  # cache-bust version

# ============================================================ app.js
FILES = {}
FILES["app.js"] = r'''/* ============================================================
   Limitation Act 1908 — PRODUCTION client engine v2
   BM25 search · s.12 calculator · EN/BN · hardened init
   ============================================================ */
let KB=null, BN=null, LANG='en', IDX=null, DOCS=[];
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const BN_DIGITS='০১২৩৪৫৬৭৮৯';
const bn2en=s=>String(s??'').replace(/[০-৯]/g,d=>String(BN_DIGITS.indexOf(d)));
const en2bn=s=>String(s??'').replace(/\d/g,d=>BN_DIGITS[+d]);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const short=(s,n=90)=>{s=String(s??'');return s.length>n?s.slice(0,n)+'…':s;};

const RX_ART=/(?:article|অনুচ্ছেদ)\s*([0-9০-৯]{1,3})\s*([abc])?\b/i;
const RX_SEC=/(?:section|ধারা)\s*([0-9০-৯]{1,2})\b/i;
const RX_DATE=/(\d{1,2})[\/.\-](\d{1,2}|jan\w*|feb\w*|mar\w*|apr\w*|may|jun\w*|jul\w*|aug\w*|sep\w*|oct\w*|nov\w*|dec\w*)[\/.\-](\d{4})/i;
const RX_DEF=/\b(define|definition|meaning)\b|সংজ্ঞা|মানে|অর্থ/i;
const MONTHS={jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,oct:10,nov:11,dec:12};

const I18N={
en:{title:'Limitation Act, 1908',subtitle:'Bangladesh · Bilingual Knowledge Engine',
 tab_search:'Search',tab_calc:'Deadline Calculator',tab_browse:'Browse Schedule',tab_faq:'FAQ',
 btn_search:'Search',calc_h:'Deadline Calculator',
 calc_p:'Pick the provision, enter the date the period began. Section 12 excludes the first day, so the last day = start + full period.',
 calc_prov:'Provision',calc_date:'Period begins on',calc_btn:'Compute last day',
 matched:'Matched',period:'Period',start:'Start',last:'Last day',
 expired:'EXPIRED — the computed last day is already in the past (extensions under ss.4–25 may still save the claim).',
 urgent:d=>`URGENT — only ${d} day(s) remain before the computed last day.`,
 nomatch:'No match found. Try naming the article or section, e.g. "article 142".',
 nodate:'Please enter a date.',
 disc:'⚖ DISCLAIMER — General information from the Limitation Act, 1908 (Bangladesh) KB. NOT legal advice. Time may be excluded or extended under sections 4–25 (court closure s.4; sufficient cause s.5; disability ss.6–8; defendant abroad s.13; wrong forum s.14; injunctions s.15; fraud s.18; written acknowledgement s.19; part payment s.20). A qualified advocate must verify before filing.'},
bn:{title:'সীমাবদ্ধন (তামাদি) আইন, ১৯০৮',subtitle:'বাংলাদেশ · দ্বিভাষিক নলেজ ইঞ্জিন',
 tab_search:'অনুসন্ধান',tab_calc:'মেয়াদ গণনা',tab_browse:'তফসিল ব্রাউজ',tab_faq:'প্রশ্নোত্তর',
 btn_search:'খুঁজুন',calc_h:'মেয়াদ গণনা',
 calc_p:'বিধান নির্বাচন করুন, মেয়াদ শুরুর তারিখ দিন। ধারা ১২ অনুযায়ী প্রথম দিন বাদ যায় — শেষ দিন = শুরু + পূর্ণ মেয়াদ।',
 calc_prov:'বিধান',calc_date:'মেয়াদ শুরু',calc_btn:'শেষ দিন গণনা করুন',
 matched:'মিলে যাওয়া বিধান',period:'তামাদির মেয়াদ',start:'শুরু',last:'শেষ দিন',
 expired:'বলীয়ান — গণনাকৃত শেষ দিন ইতিমধ্যে অতিবাহিত (ধারা ৪–২৫ অনুযায়ী সময় বৃদ্ধি সম্ভব)।',
 urgent:d=>`সতর্কতা — মাত্র ${en2bn(d)} দিন বাকি!`,
 nomatch:'কোনো মিল পাওয়া যায়নি। অনুচ্ছেদ/ধারার নম্বর দিয়ে চেষ্টা করুন।',
 nodate:'তারিখ দিন।',
 disc:'⚖ দাবিত্যাগ — সীমাবদ্ধন আইন ১৯০৮ নলেজ-বেস থেকে প্রাপ্ত সাধারণ তথ্য; আইনি পরামর্শ নয়। ধারা ৪–২৫ অনুযায়ী সময় বাদ/বৃদ্ধি পেতে পারে (আদালত বন্ধ — ধারা ৪; পর্যাপ্ত কারণ — ধারা ৫; অক্ষমতা — ধারা ৬–৮; প্রতিবাদীর অনুপস্থিতি — ধারা ১৩; ভুল আদালত — ধারা ১৪; নিষেধাজ্ঞা — ধারা ১৫; প্রতারণা — ধারা ১৮; লিখিত স্বীকৃতি — ধারা ১৯; আংশিক পরিশোধ — ধারা ২০)। দায়েরের পূর্বে অবশ্যই আইনজীবী দ্বারা যাচাই করুন।'}};
const t=k=>I18N[LANG][k];

/* ---------- boot: hardened ---------- */
(async function init(){
  try{
    const [kbRes,bnRes]=await Promise.all([
      fetch('data/kb.json?v='+V),
      fetch('data/bn.json?v='+V).catch(()=>null)]);
    if(!kbRes.ok) throw new Error('kb.json HTTP '+kbRes.status+' — data/ missing in deployment?');
    KB=await kbRes.json();
    BN=(bnRes&&bnRes.ok)?await bnRes.json():{};
    const probs=validateKB(KB);
    if(probs.length)console.warn('[KB warnings]',probs);
    DOCS=buildDocs();
    const withPeriod=DOCS.filter(d=>d.type==='article'&&d.period).length;
    if(withPeriod<50)throw new Error('Only '+withPeriod+' parsable articles — KB schema mismatch.');
    IDX=buildIndex(DOCS);
    wireUI();               // ✅ defined below — crash fixed
    fillCalcSelect();
    renderBrowse('');
    renderFAQ();
    $('#footDisc').textContent=t('disc');
    if(probs.length)banner('⚠ Loaded with warnings: '+probs.slice(0,3).join(' | '),'warnline urgent');
    console.log('[init] OK —',DOCS.length,'docs,',withPeriod,'calculable articles');
  }catch(err){
    console.error('[init]',err);
    banner('❌ Init failed: '+err.message+' — see F12 Console');
  }
})();

function validateKB(kb){
  const p=[];
  if(!kb)return['KB null'];
  if(!Array.isArray(kb.sections))p.push('sections missing');
  if(!Array.isArray(kb.faq))p.push('faq missing');
  if(!Array.isArray(kb.definitions))p.push('definitions missing');
  if(!kb.schedule)return p.concat('schedule missing');
  for(const[div,arts]of Object.entries(kb.schedule)){
    if(!Array.isArray(arts)){p.push(div+':not array');continue;}
    arts.forEach(a=>{if(!a||!a.a)p.push(div+':bad entry');
      else if(!a.omitted&&(!a.p||!a.d))p.push('A'+a.a+':missing '+(a.p?'':'p ')+(a.d?'':'d'));});
  }
  return p;
}
function banner(msg,cls){
  const el=document.createElement('div');
  el.className='disc '+(cls||'');el.style.borderColor='#e74c3c';el.textContent=msg;
  document.querySelector('main .wrap')?.prepend(el);
}

/* ---------- docs ---------- */
function buildDocs(){
  const D=[];const PB=BN.periods_bn||{};
  (KB.definitions||[]).forEach(d=>{const b=(BN.definitions_bn||{})[d.term];
    D.push({id:'D:'+d.term,type:'definition',cite:'D:'+d.term,
      title:'Definition of "'+d.term+'" (s.'+d.section+')',en:d.definition,
      bn:b?('সংজ্ঞা: '+d.term+' — '+b):null,
      raw:'definition '+d.term+' '+d.section+' '+d.definition+' '+(b||'')});});
  (KB.sections||[]).forEach(s=>{const b=(BN.sections_bn||{})[s.id];
    D.push({id:'S'+s.id,type:'section',cite:'S'+s.id,
      title:'Section '+s.id+' — '+s.title+' ['+s.part+']',
      en:s.gist+(s.key_points&&s.key_points.length?'\n• '+s.key_points.join('\n• '):''),
      bn:b?('ধারা '+en2bn(s.id)+' — '+b.t+'।\n'+b.g):null,
      raw:'section '+s.id+' '+s.title+' '+s.part+' '+s.gist+' '+((s.key_points||[]).join(' '))+' '+(b?b.t+' '+b.g:'')});});
  for(const[div,arts]of Object.entries(KB.schedule||{}))
    (arts||[]).forEach(a=>{
      if(a.omitted){D.push({id:'A'+a.a,type:'article',cite:'A'+a.a,div,
        title:'Article '+a.a+' — [omitted]',en:a.omitted,bn:null,raw:'article '+a.a+' omitted'});return;}
      const b=(BN.articles_bn||{})[a.a];
      D.push({id:'A'+a.a,type:'article',cite:'A'+a.a,div,
        title:'Article '+a.a+' — '+a.d,
        en:a.d+'\nBegins to run: '+a.s+(a.note?'\nNote: '+a.note:''),
        bn:b?('অনুচ্ছেদ '+en2bn(a.a)+' — '+b+'।\nতামাদির মেয়াদ: '+(PB[a.p]||a.p)+'।'):null,
        period:a.p,begin:a.s,note:a.note||'',
        raw:'article '+a.a+' '+a.d+' period '+a.p+' begins '+a.s+' '+(a.note||'')+' '+(b||'')+' '+(PB[a.p]||'')});});
  (KB.faq||[]).forEach((f,i)=>{const b=(BN.faq_bn||{})[String(i)];
    D.push({id:'FAQ'+i,type:'faq',cite:'FAQ'+i,title:f.q,en:f.a,
      bn:b?('প্রশ্ন: '+b.q+'\nউত্তর: '+b.a):null,
      raw:'faq '+f.q+' '+f.a+' '+(b?b.q+' '+b.a:'')});});
  return D;
}

/* ---------- BM25 ---------- */
const tok=s=>bn2en(String(s??'')).toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').split(' ').filter(Boolean);
function buildIndex(docs){
  const toks=docs.map(d=>tok(d.raw));const df={};
  toks.forEach(ts=>new Set(ts).forEach(w=>df[w]=(df[w]||0)+1));
  const avgdl=toks.reduce((a,x)=>a+x.length,0)/(docs.length||1)||1;
  return{N:docs.length,df,avgdl,toks};
}
function glossaryExpand(q){
  const ql=q.toLowerCase();const extra=[];
  (BN.glossary||[]).forEach(g=>{
    if(ql.includes(g.en.toLowerCase())&&!q.includes(g.bn))extra.push(g.bn);
    else if(q.includes(g.bn)&&!ql.includes(g.en.toLowerCase()))extra.push(g.en);});
  return q+' '+extra.slice(0,6).join(' ');
}
function search(q,k=6){
  const qt=tok(glossaryExpand(q));if(!qt.length)return[];
  return DOCS.map((d,i)=>{let s=0;const ts=IDX.toks[i];
    for(const w of qt){let tf=0;for(const x of ts)if(x===w)tf++;
      if(!tf)continue;const f=IDX.df[w]||0;
      s+=Math.log(1+(IDX.N-f+.5)/(f+.5))*tf*2.2/(tf+1.2*(.25+.75*ts.length/IDX.avgdl));}
    return[d,s];}).filter(x=>x[1]>0).sort((a,b)=>b[1]-a[1]).slice(0,k);
}

/* ---------- parsers ---------- */
function getArt(q){const m=RX_ART.exec(bn2en(q));if(!m)return null;
  const id=m[1]+(m[2]?m[2].toLowerCase():'');
  return DOCS.find(d=>d.type==='article'&&d.cite==='A'+id)||null;}
function getSec(q){const m=RX_SEC.exec(bn2en(q));if(!m)return null;
  return DOCS.find(d=>d.type==='section'&&d.cite==='S'+m[1])||null;}
function parseDate(q){const m=RX_DATE.exec(bn2en(q));if(!m)return null;
  const d=+m[1],mon=m[2],y=+m[3];
  const mo=/^\d+$/.test(mon)?+mon:MONTHS[mon.slice(0,3).toLowerCase()];
  if(!mo)return null;const dt=new Date(Date.UTC(y,mo-1,d));return isNaN(dt)?null:dt;}
function parsePeriod(p){const m=/(\d+)\s*(day|month|year)/i.exec(p||'');
  return m?{n:+m[1],u:m[2][0].toLowerCase()}:null;}
const dim=(y,m)=>new Date(Date.UTC(y,m+1,0)).getUTCDate();
function addPeriod(dt,pv,pu){const d=new Date(dt);
  if(pu==='d')d.setUTCDate(d.getUTCDate()+pv);
  else if(pu==='m'){const tot=d.getUTCMonth()+pv,y=d.getUTCFullYear()+Math.floor(tot/12),m=tot%12;
    d.setUTCFullYear(y);d.setUTCMonth(m,Math.min(d.getUTCDate(),dim(y,m)));}
  else{const y=d.getUTCFullYear()+pv;d.setUTCFullYear(y);
    d.setUTCDate(Math.min(d.getUTCDate(),dim(y,d.getUTCMonth())));}
  return d;}

/* ---------- query pipeline ---------- */
function runQuery(qRaw){
  try{
    const q=(qRaw||'').trim();if(!q)return;
    const art=getArt(q),sec=getSec(q),dt=parseDate(q);
    if(dt){
      let hit=art;
      if(!hit){const top=search(q,1)[0];if(top&&top[0].type==='article'&&top[0].period)hit=top[0];}
      const pp=hit?parsePeriod(hit.period):null;
      if(hit&&pp){
        const end=addPeriod(dt,pp.n,pp.u);
        const today=new Date();today.setUTCHours(0,0,0,0);
        const days=Math.round((end-today)/864e5);
        let warn='';
        if(days<0)warn='<div class="warnline expired">⚠ '+esc(t('expired'))+'</div>';
        else if(days<=30)warn='<div class="warnline urgent">⚠ '+esc(t('urgent')(days))+'</div>';
        $('#results').innerHTML=
          card(hit,'<div class="calcbox"><div>'+esc(t('matched'))+': <b>'+esc(hit.cite)+'</b> — '+esc(short(hit.title))+
            '</div><div>'+esc(t('period'))+': <b>'+esc(hit.period)+'</b></div><div>'+esc(t('start'))+': <b>'+fmtDate(dt)+'</b></div>'+
            '<div class="big">'+esc(t('last'))+': '+fmtDate(end)+'</div>'+warn+
            '<div class="ensnip">s.12 excludes the first day; further exclusions under ss.4, 13–16, 19–20 may apply.</div></div>')+
          results(search(q,4).filter(x=>x[0]!==hit))+discBlock();
        return;
      }
    }
    if(art){$('#results').innerHTML=card(art)+discBlock();return;}
    if(sec){$('#results').innerHTML=card(sec)+discBlock();return;}
    if(RX_DEF.test(q)){const res=search(q,4);
      if(res[0]&&res[0][0].type==='definition'){
        $('#results').innerHTML=res.slice(0,2).map(([d])=>card(d)).join('')+discBlock();return;}}
    const res=search(q,6);
    $('#results').innerHTML=res.length?results(res)+discBlock()
      :'<div class="card">'+esc(t('nomatch'))+'</div>';
  }catch(err){console.error('[query]',err);
    $('#results').innerHTML='<div class="disc">❌ '+esc(err.message)+'</div>';}
}

/* ---------- renderers ---------- */
function pill(p){if(!p)return'';const cls=/day/i.test(p)?'p-days':/month/i.test(p)?'p-months':
  (/(12|30|60)\s*year/i.test(p)?'p-big':'p-years');
  const label=LANG==='bn'?((BN.periods_bn||{})[p]||p):p;
  return'<span class="pill '+cls+'">'+esc(label)+'</span>';}
function card(d,extra=''){
  const cls=d.type==='section'?'sec':d.type==='definition'?'def':d.type==='faq'?'faq':'';
  let body='';
  if(LANG==='bn'&&d.bn){body=esc(d.bn)+'<div class="ensnip">EN: '+esc(short(d.en,200))+'</div>';}
  else{body=esc(d.en);if(d.bn)body+='<div class="bnsnip">'+esc(short(d.bn,160))+'</div>';}
  return'<div class="card"><p class="rtitle"><span class="cite '+cls+'">'+esc(d.cite)+'</span>'+
    esc(d.title)+'</p>'+(d.period?pill(d.period):'')+'<div class="rbody">'+body+'</div>'+(extra||'')+'</div>';}
const results=res=>res.map(([d])=>card(d)).join('');
const discBlock=()=>'<div class="disc">'+esc(t('disc'))+'</div>';
function fmtDate(d){const s=d.toISOString().slice(0,10);return LANG==='bn'?en2bn(s):s;}

/* ---------- calculator ---------- */
function fillCalcSelect(){
  const sel=$('#calcArt');if(!sel){console.error('#calcArt missing');return;}
  sel.innerHTML='';let n=0;
  for(const[div,arts]of Object.entries(KB.schedule||{}))
    (arts||[]).filter(a=>a&&a.p).forEach(a=>{
      const o=document.createElement('option');o.value=a.a;
      o.textContent='Art '+a.a+' — '+short(a.d,55)+' ('+a.p+')';sel.appendChild(o);n++;});
  if(!n){sel.innerHTML='<option value="">— no provisions loaded —</option>';
    banner('⚠ Calculator: 0 provisions parsed — see Console [KB warnings]');}
  else{const o57=[...sel.options].find(o=>o.value==='57');if(o57)sel.value='57';}
  console.log('[calc] '+n+' provisions in dropdown');
}
function runCalc(){
  const out=$('#calcOut'),aid=$('#calcArt').value,dval=$('#calcDate').value;
  if(!aid){out.innerHTML='<div class="disc">⚠ '+esc(t('nomatch'))+'</div>';return;}
  if(!dval){out.innerHTML='<div class="disc">'+esc(t('nodate'))+'</div>';return;}
  const doc=DOCS.find(d=>d.cite==='A'+aid);const pp=doc&&parsePeriod(doc.period);
  if(!doc||!pp){out.innerHTML='<div class="disc">⚠ Cannot compute for Art '+esc(aid)+'</div>';return;}
  const start=new Date(dval+'T00:00:00Z'),end=addPeriod(start,pp.n,pp.u);
  const today=new Date();today.setUTCHours(0,0,0,0);
  const days=Math.round((end-today)/864e5);
  let warn='';
  if(days<0)warn='<div class="warnline expired">⚠ '+esc(t('expired'))+'</div>';
  else if(days<=30)warn='<div class="warnline urgent">⚠ '+esc(t('urgent')(days))+'</div>';
  out.innerHTML=card(doc,'<div class="calcbox"><div>'+esc(t('start'))+': <b>'+fmtDate(start)+
    '</b></div><div class="big">'+esc(t('last'))+': '+fmtDate(end)+'</div>'+warn+
    '<div class="ensnip">s.12 excludes the first day · ss.4–25 exclusions may apply.</div></div>')+discBlock();
}

/* ---------- browse ---------- */
const DIV_NAMES={division_1_suits:['First Division — Suits','প্রথম বিভাগ — মামলা'],
 division_2_appeals:['Second Division — Appeals','দ্বিতীয় বিভাগ — আপিল'],
 division_3_applications:['Third Division — Applications','তৃতীয় বিভাগ — আবেদন']};
function renderBrowse(filter){
  const f=(filter||'').toLowerCase();let html='';
  for(const[div,arts]of Object.entries(KB.schedule||{})){
    const rows=(arts||[]).filter(a=>{if(!f)return true;
      return(a.a+' '+(a.d||'')+' '+((BN.articles_bn||{})[a.a]||'')+' '+(a.p||''))
        .toLowerCase().includes(f)||bn2en(a.a+' '+(a.d||'')).toLowerCase().includes(bn2en(f));});
    if(!rows.length)continue;
    const nm=DIV_NAMES[div]||[div,div];
    html+='<h3 class="divh">'+esc(LANG==='bn'?nm[1]:nm[0])+'</h3><table><tr><th>Art</th><th>Description</th><th>Period</th></tr>';
    rows.forEach(a=>{const label=LANG==='bn'?((BN.articles_bn||{})[a.a]||a.d||'—'):(a.d||'[omitted]');
      html+='<tr class="row" data-cite="A'+esc(a.a)+'"><td><b>'+esc(a.a)+'</b></td><td>'+
        esc(short(label,110))+'</td><td class="per">'+(a.p?pill(a.p):'<span class="muted">—</span>')+'</td></tr>';});
    html+='</table>';}
  $('#browse').innerHTML=html||'<div class="card muted">No results.</div>';
}

/* ---------- faq ---------- */
function renderFAQ(){
  $('#faqList').innerHTML=(KB.faq||[]).map((f,i)=>{
    const b=(BN.faq_bn||{})[String(i)];
    const qq=(LANG==='bn'&&b)?b.q:f.q,aa=(LANG==='bn'&&b)?b.a:f.a;
    return'<div class="faq-q">'+esc(qq)+'</div><div class="faq-a">'+esc(aa)+'</div>';}).join('');
}

/* ---------- events (single source of truth) ---------- */
function showTab(name){
  $$('.tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));
  $$('.panel').forEach(p=>p.classList.toggle('active',p.id==='tab-'+name));}
function wireUI(){
  $('#go').onclick=()=>runQuery($('#q').value);
  $('#q').addEventListener('keydown',e=>{if(e.key==='Enter')runQuery($('#q').value);});
  $$('.chip').forEach(c=>c.onclick=()=>{$('#q').value=c.dataset.q;runQuery(c.dataset.q);});
  $$('.tab').forEach(b=>b.onclick=()=>showTab(b.dataset.tab));
  $('#browseFilter').addEventListener('input',e=>renderBrowse(e.target.value));
  $('#faqList').addEventListener('click',e=>{
    if(e.target.classList.contains('faq-q'))e.target.classList.toggle('open');});
  $('#browse').addEventListener('click',e=>{
    const tr=e.target.closest('tr.row');if(!tr)return;
    const doc=DOCS.find(d=>d.cite===tr.dataset.cite);
    if(doc){showTab('search');$('#q').value=doc.cite.replace('A','Article ');
      $('#results').innerHTML=card(doc)+discBlock();
      window.scrollTo({top:0,behavior:'smooth'});}});
  $('#calcGo').onclick=runCalc;
  $('#langBtn').onclick=()=>{
    LANG=LANG==='en'?'bn':'en';
    document.body.classList.toggle('bn',LANG==='bn');
    $('#langBtn').textContent=LANG==='bn'?'English':'বাংলা';
    $$('[data-i18n]').forEach(el=>{const k=el.dataset.i18n;if(I18N[LANG][k])el.textContent=I18N[LANG][k];});
    $('#footDisc').textContent=t('disc');
    renderBrowse($('#browseFilter').value);renderFAQ();
    if($('#results').innerHTML.trim())runQuery($('#q').value||'article 3');};
}
'''

# ============================================================ index.html (production meta)
FILES["index.html"] = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Limitation Act 1908 (Bangladesh) — Bilingual Legal KB</title>
<meta name="description" content="Searchable bilingual (English/বাংলা) knowledge engine for the Limitation Act, 1908 of Bangladesh — limitation periods, deadline calculator, appeals and applications. General information only; not legal advice.">
<meta name="theme-color" content="#0f1420">
<meta name="robots" content="index,follow">
<!-- Open Graph / Twitter (og:url set dynamically) -->
<meta property="og:type" content="website">
<meta property="og:title" content="Limitation Act 1908 (Bangladesh) — Bilingual Legal KB">
<meta property="og:description" content="All 183 schedule articles · deadline calculator · English + বাংলা. Not legal advice.">
<meta property="og:url" content="">
<meta name="twitter:card" content="summary">
<link rel="canonical" href="">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Serif+Bengali:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css?v=2">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚖️</text></svg>">
</head>
<body>
<header class="topbar">
  <div class="wrap bar-inner">
    <div class="brand">
      <span class="logo">⚖️</span>
      <div>
        <h1 data-i18n="title">Limitation Act, 1908</h1>
        <p class="sub" data-i18n="subtitle">Bangladesh · Bilingual Knowledge Engine</p>
      </div>
    </div>
    <button id="langBtn" class="lang-btn" title="Switch language">বাংলা</button>
  </div>
</header>

<nav class="tabs wrap" aria-label="Sections">
  <button class="tab active" data-tab="search">🔍 <span data-i18n="tab_search">Search</span></button>
  <button class="tab" data-tab="calc">📅 <span data-i18n="tab_calc">Deadline Calculator</span></button>
  <button class="tab" data-tab="browse">📚 <span data-i18n="tab_browse">Browse Schedule</span></button>
  <button class="tab" data-tab="faq">❓ <span data-i18n="tab_faq">FAQ</span></button>
</nav>

<main class="wrap">
  <section id="tab-search" class="panel active">
    <div class="searchbox">
      <input id="q" type="text" autocomplete="off" aria-label="Search"
        placeholder='Try: "article 113" · "money lent 15/03/2022" · "স্থাবর সম্পত্তির দখল" · "section 19"'>
      <button id="go" class="btn primary" data-i18n="btn_search">Search</button>
    </div>
    <div class="chips">
      <span class="chip" data-q="article 113">Article 113</span>
      <span class="chip" data-q="recover possession of immovable property">Possession 12y</span>
      <span class="chip" data-q="money lent 3 years deadline">Money lent</span>
      <span class="chip" data-q="appeal to High Court Division">Appeal to HCD</span>
      <span class="chip" data-q="ধার ফেরতের মামলার মেয়াদ">ধার (BN)</span>
      <span class="chip" data-q="written acknowledgement of debt">Acknowledgement s.19</span>
    </div>
    <div id="results"></div>
  </section>

  <section id="tab-calc" class="panel">
    <div class="card pad">
      <h2 data-i18n="calc_h">Deadline Calculator</h2>
      <p class="muted" data-i18n="calc_p">Pick the provision, enter the date the period began. Section 12 excludes the first day, so the last day = start + full period.</p>
      <div class="grid2">
        <label><span data-i18n="calc_prov">Provision</span>
          <select id="calcArt" aria-label="Provision"></select></label>
        <label><span data-i18n="calc_date">Period begins on</span>
          <input id="calcDate" type="date" aria-label="Start date"></label>
      </div>
      <button id="calcGo" class="btn primary" data-i18n="calc_btn">Compute last day</button>
      <div id="calcOut"></div>
    </div>
  </section>

  <section id="tab-browse" class="panel">
    <input id="browseFilter" class="filter" placeholder="Filter… / ফিল্টার" aria-label="Filter schedule">
    <div id="browse"></div>
  </section>

  <section id="tab-faq" class="panel">
    <div id="faqList"></div>
  </section>
</main>

<footer class="foot">
  <div class="wrap">
    <p id="footDisc"></p>
    <p class="muted small">Source: The Limitation Act, 1908 (Act No. IX of 1908) · Laws of Bangladesh ·
    Deployed on Vercel · <a href="/api/search?q=article%20113">JSON API</a></p>
  </div>
</footer>
<noscript><div class="disc">This app requires JavaScript. Data API: /api/search?q=…</div></noscript>
<script>
/* set absolute og:url + canonical to current deployment */
document.querySelectorAll('meta[property="og:url"],link[rel="canonical"]')
  .forEach(el=>{el.content||(el.content=location.href);el.href&&(el.href=location.href);});
</script>
<script src="app.js?v=2"></script>
</body>
</html>
'''

# ============================================================ vercel.json (security + cache)
FILES["vercel.json"] = r'''{
  "framework": null,
  "cleanUrls": true,
  "trailingSlash": false,
  "functions": {
    "api/*.js": { "includeFiles": "data/kb.json" }
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "SAMEORIGIN" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" }
      ]
    },
    {
      "source": "/data/(.*)",
      "headers": [{ "key": "Cache-Control", "value": "public, max-age=3600" }]
    },
    {
      "source": "/api/(.*)",
      "headers": [{ "key": "Cache-Control", "value": "no-store" }]
    }
  ]
}
'''

FILES["robots.txt"] = "User-agent: *\nAllow: /\nDisallow: /api/\n"

FILES[".gitattributes"] = "* text=auto eol=lf\n*.png binary\n*.ico binary\n"

FILES[".gitignore"] = ".vercel\nnode_modules/\n.DS_Store\n*.log\n__pycache__/\n"


def main():
    for rel, content in FILES.items():
        p = Path(rel); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8", newline="\n")
        print(f"  [ok] {rel}")
    # sanity-check the KB that ships
    kb = json.loads(Path("data/kb.json").read_text(encoding="utf-8"))
    arts = [a for div in kb["schedule"].values() for a in div if a.get("p")]
    print(f"\n[data check] sections={len(kb['sections'])} articles={len(arts)} "
          f"faq={len(kb['faq'])} definitions={len(kb['definitions'])}")
    print("sample dropdown item → Art", arts[0]["a"], "|", arts[0]["p"])
    bad = [a["a"] for a in arts if not a.get("d") or not a.get("s")]
    print("schema problems:", bad if bad else "none ✅")
    print("\nNEXT → git add -A && git commit -m 'production hardening v2' && git push")

if __name__ == "__main__":
    main()