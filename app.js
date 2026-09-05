/* ============================================================
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
      fetch('data/kb.json?v=2'),
      fetch('data/bn.json?v=2').catch(()=>null)]);
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
