#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""premium_upgrade.py — Neum Lex Counsel Premium Edition v3.
Writes complete site: premium UI, Firebase auth, 3-free-test gate,
Tk plans, TrxID payments, admin panel, fixed desktop calculator."""
from pathlib import Path

F = {}

# ================================================================ config.js
F["config.js"] = r'''/* Neum Lex Counsel — site configuration. EDIT THIS FILE ONLY. */
const APP_CONFIG = {
  brand: {
    firm: "Neum Lex Counsel",
    developer: "Md Nazmul Islam",          // ← edit spelling here if needed
    designation: "Advocate",
    court: "Supreme Court of Bangladesh",
    credit: function(){
      return "Developed by " + this.developer + ", " + this.designation +
             ", " + this.court + " · " + this.firm;
    }
  },
  /* Your Google account(s) that may open /admin */
  adminEmails: ["YOUR_ADMIN_GMAIL@gmail.com"],   // ← EDIT

  /* Firebase — paste your web app config (see SETUP.md) */
  firebase: {
    apiKey: "PASTE_API_KEY",
    authDomain: "PASTE_PROJECT.firebaseapp.com",
    projectId: "PASTE_PROJECT_ID",
    storageBucket: "PASTE_PROJECT.appspot.com",
    messagingSenderId: "PASTE",
    appId: "PASTE_APP_ID"
  },

  freeTests: 3,

  plans: [
    { id:"p1",  months:1,  bdt:100, label:"1 Month",   note:"Starter" },
    { id:"p3",  months:3,  bdt:200, label:"3 Months",  note:"Save 33%" },
    { id:"p6",  months:6,  bdt:400, label:"6 Months",  note:"Save 33%" },
    { id:"p12", months:12, bdt:550, label:"12 Months", note:"Save 54% · Best Value" }
  ],

  payment: {
    bkash: "01XXXXXXXXX",        // ← EDIT: your bKash (Merchant preferred)
    nagad: "01XXXXXXXXX",        // ← EDIT: your Nagad
    refPrefix: "NLX",            // reference format: NLX + last 4 of mobile
    note: "Send the exact amount using bKash/Nagad ‘Send Money’, then submit your TrxID below. Activation usually completes within a few hours after verification."
  }
};
'''

# ================================================================ auth.js
F["auth.js"] = r'''/* Neum Lex Counsel — auth, test-gate, profile badge (Firebase compat) */
window.NLC = (function(){
  let auth=null, db=null, fbReady=false, user=null, profile=null;
  const cfg = APP_CONFIG;

  function synthEmail(mobile){ return normMobile(mobile) + "@mobile.neumlex.app"; }
  function normMobile(m){
    let d = String(m||"").replace(/\D/g,"");
    if (d.startsWith("880")) d = d.slice(3);
    if (!d.startsWith("1")) d = d.replace(/^0+/,"");
    d = "01" + (d.startsWith("1")?d.slice(1):d);
    if (!/^01[3-9]\d{8}$/.test(d)) throw new Error("Invalid Bangladeshi mobile number (e.g. 01712345678)");
    return "880" + d.slice(1);
  }
  function configured(){ return cfg.firebase && !cfg.firebase.apiKey.startsWith("PASTE"); }

  function init(){
    if (!configured()){
      console.warn("[NLC] Firebase not configured — auth disabled (demo mode). See SETUP.md");
      document.getElementById("authBtn").textContent = "Sign in (setup)";
      return;
    }
    firebase.initializeApp(cfg.firebase);
    auth = firebase.auth(); db = firebase.firestore();
    fbReady = true;
    auth.onAuthStateChanged(async u=>{
      user = u;
      if (u){ profile = await loadProfile(u); await refreshBadge(); }
      else  { profile = null; refreshBadge(); }
      if (location.pathname.endsWith("/admin")) window.Admin && Admin.onAuth(u);
    });
  }

  async function loadProfile(u){
    try{
      const ref = db.collection("users").doc(u.uid);
      const snap = await ref.get();
      if (snap.exists) return snap.data();
      const fresh = { email:u.email||null, mobile:null, displayName:u.displayName||"",
                      testsUsed:0, planExpiry:null, createdAt:new Date() };
      await ref.set(fresh); return fresh;
    }catch(e){ console.error("[NLC] profile load", e); return {testsUsed:0, planExpiry:null}; }
  }

  function premiumUntil(){ return profile && profile.planExpiry ? profile.planExpiry.toDate() : null; }
  function isPremium(){ const d = premiumUntil(); return !!(d && d > new Date()); }
  function testsLeft(){ if(isPremium()) return Infinity;
    return Math.max(0, cfg.freeTests - ((profile && profile.testsUsed)||0)); }

  async function signupMobile(name, mobile, pass){
    requireFB();
    const cred = await auth.createUserWithEmailAndPassword(synthEmail(mobile), pass);
    if (name) await cred.user.updateProfile({displayName:name});
    await db.collection("users").doc(cred.user.uid).set({
      email:null, mobile:normMobile(mobile), displayName:name||"",
      testsUsed:0, planExpiry:null, createdAt:new Date()
    });
    profile = await loadProfile(cred.user); refreshBadge();
    return cred.user;
  }
  async function loginMobile(mobile, pass){
    requireFB();
    const cred = await auth.signInWithEmailAndPassword(synthEmail(mobile), pass);
    return cred.user;
  }
  async function signInGoogle(){
    requireFB();
    const provider = new firebase.auth.GoogleAuthProvider();
    provider.setCustomParameters({ prompt: "select_account" });
    return auth.signInWithPopup(provider);
  }
  async function logout(){ if(fbReady) await auth.signOut(); }

  function requireFB(){
    if(!fbReady) throw new Error("Authentication is not configured yet. The site owner must complete SETUP.md steps 1–6.");
  }

  /* ---------- THE GATE ---------- */
  async function gate(feature){
    if (!fbReady) return true;                    // demo mode: allow
    if (!user){ openAuth(feature); return false; }
    if (isPremium()) return true;
    if (testsLeft() > 0){
      try{
        await db.collection("users").doc(user.uid)
          .update({ testsUsed: firebase.firestore.FieldValue.increment(1) });
        profile.testsUsed = (profile.testsUsed||0) + 1;
        await refreshBadge();
        toast(`Free analysis used — ${testsLeft()} remaining`);
        return true;
      }catch(e){ console.error(e); return true; } // fail-open on infra error
    }
    openPaywall(); return false;
  }

  /* ---------- UI: badge, modals, toasts ---------- */
  function refreshBadge(){
    const b = document.getElementById("authBtn");
    const chip = document.getElementById("planChip");
    if (!b) return;
    if (!fbReady){ b.textContent="Sign in (setup)"; if(chip) chip.hidden=true; return; }
    if (!user){ b.innerHTML="🔐 Sign in / Sign up"; if(chip){chip.hidden=true;} return; }
    if (isPremium()){
      b.innerHTML = "👑 " + esc(short(user.displayName || (profile&&profile.mobile) || user.email, 18));
      if (chip){ chip.hidden=false;
        chip.textContent = "Premium until " + fmtShort(premiumUntil()); }
    } else {
      b.innerHTML = "👤 " + esc(short(user.displayName || (profile&&profile.mobile) || user.email, 14))
                  + " · " + testsLeft() + " free left";
      if (chip) chip.hidden=true;
    }
  }
  const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const short=(s,n)=>s.length>n?s.slice(0,n)+"…":s;
  const MO=["January","February","March","April","May","June","July","August","September","October","November","December"];
  function fmtShort(d){ return d.getDate()+" "+MO[d.getMonth()]+" "+d.getFullYear(); }

  function toast(msg){
    let t=document.getElementById("nlcToast");
    if(!t){ t=document.createElement("div"); t.id="nlcToast"; document.body.appendChild(t); }
    t.textContent=msg; t.classList.add("show");
    clearTimeout(t._h); t._h=setTimeout(()=>t.classList.remove("show"),2600);
  }

  function openAuth(feature){ window.__nlcAfterAuth = feature||null;
    document.getElementById("authModal").classList.add("open"); }
  function openPaywall(){ if(window.Payments) Payments.open(); }
  function openAccount(){ if(window.Payments) Payments.openAccount(); }

  function wire(){
    const $=s=>document.querySelector(s);
    $("#authBtn").onclick = ()=>{ if(!fbReady){alert("Auth not configured — see SETUP.md");return;}
      user ? openAccount() : openAuth(); };
    document.querySelectorAll("[data-close]").forEach(x=>x.onclick=e=>
      e.target.closest(".modal").classList.remove("open"));
    document.querySelectorAll(".modal").forEach(m=>m.addEventListener("click",e=>{
      if(e.target===m) m.classList.remove("open"); }));
    // auth modal tabs
    document.querySelectorAll("#authModal .mtab").forEach(tb=>tb.onclick=()=>{
      document.querySelectorAll("#authModal .mtab").forEach(x=>x.classList.remove("active"));
      document.querySelectorAll("#authModal .mpane").forEach(x=>x.classList.remove("active"));
      tb.classList.add("active");
      document.getElementById(tb.dataset.pane).classList.add("active"); });
    const err=(m)=>{ const e=$("#authErr"); e.textContent=m; e.hidden=false; };
    $("#doLogin").onclick = async ()=>{
      $("#authErr").hidden=true;
      try{ await loginMobile($("#liMobile").value, $("#liPass").value);
           $("#authModal").classList.remove("open"); toast("Welcome back");
      }catch(e){ err(prettyErr(e)); } };
    $("#doSignup").onclick = async ()=>{
      $("#authErr").hidden=true;
      try{
        if(($("#suPass").value||"").length<6) throw new Error("Password must be at least 6 characters.");
        await signupMobile($("#suName").value, $("#suMobile").value, $("#suPass").value);
        $("#authModal").classList.remove("open");
        toast("Account created — "+cfg.freeTests+" free analyses unlocked");
      }catch(e){ err(prettyErr(e)); } };
    $("#doGoogle").onclick = async ()=>{
      $("#authErr").hidden=true;
      try{ await signInGoogle(); $("#authModal").classList.remove("open"); toast("Signed in with Google");
      }catch(e){ err(prettyErr(e)); } };
  }
  function prettyErr(e){
    const c=e&&e.code||"";
    if(c.includes("email-already-in-use")) return "This mobile number is already registered — please Sign in.";
    if(c.includes("wrong-password")||c.includes("user-not-found")||c.includes("invalid-credential"))
      return "Mobile number or password is incorrect.";
    if(c.includes("weak-password")) return "Password must be at least 6 characters.";
    if(c.includes("popup-closed")) return "Google sign-in was cancelled.";
    if(c.includes("unauthorized-domain")) return "This domain isn't authorized in Firebase (Authentication → Settings → Authorized domains).";
    return e.message||"Something went wrong.";
  }

  document.addEventListener("DOMContentLoaded", ()=>{ init(); wire(); });
  return { gate, logout, openPaywall, openAccount, openAuth,
           get user(){return user}, get profile(){return profile},
           isPremium, testsLeft, premiumUntil, toast, cfg };
})();
'''

# ================================================================ payments.js
F["payments.js"] = r'''/* Neum Lex Counsel — plans, bKash/Nagad TrxID submission, account panel */
window.Payments = (function(){
  const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
  const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let selected=null;

  function plansHTML(){
    return NLC.cfg.plans.map(p=>`
      <div class="plan ${p.id==='p12'?'best':''}" data-plan="${p.id}">
        ${p.id==='p12'?'<div class="best-ribbon">BEST VALUE</div>':''}
        <div class="plan-name">${esc(p.label)}</div>
        <div class="plan-price"><span class="tk">৳</span>${p.bdt}</div>
        <div class="plan-note">${esc(p.note)}</div>
        <div class="plan-per">≈ ৳${Math.round(p.bdt/p.months)}/month</div>
      </div>`).join("");
  }

  function open(){
    if(!NLC.user){ NLC.openAuth(); return; }
    $("#payBody").innerHTML = `
      <h3 class="pay-title">Choose Your Plan</h3>
      <p class="pay-sub">Unlock unlimited searches, the deadline calculator and premium guidance.</p>
      <div class="plans">${plansHTML()}</div>`;
    $("#payModal").classList.add("open");
    $$("#payBody .plan").forEach(el=>el.onclick=()=>choose(el.dataset.plan));
  }

  function choose(planId){
    selected = NLC.cfg.plans.find(p=>p.id===planId);
    const pay = NLC.cfg.payment;
    const refCode = pay.refPrefix + "-" + String(NLC.profile&&(NLC.profile.mobile||"")).slice(-4);
    $("#payBody").innerHTML = `
      <button class="backlink" id="backPlans">← All plans</button>
      <h3 class="pay-title">${esc(selected.label)} — <span class="gold">৳${selected.bdt}</span></h3>
      <div class="paybox">
        <div class="payline"><span>bKash (Send Money)</span><b class="copyable" data-copy="${esc(pay.bkash)}">${esc(pay.bkash)}</b></div>
        <div class="payline"><span>Nagad (Send Money)</span><b class="copyable" data-copy="${esc(pay.nagad)}">${esc(pay.nagad)}</b></div>
        <div class="payline"><span>Amount</span><b>৳${selected.bdt} exactly</b></div>
        <div class="payline"><span>Reference</span><b>${esc(refCode)}</b></div>
      </div>
      <p class="pay-note">${esc(pay.note)}</p>
      <div class="grid2">
        <label>TrxID (from confirmation SMS)
          <input id="trx" maxlength="12" placeholder="e.g. 9HX7A2K1LM" autocomplete="off"></label>
        <label>Your bKash/Nagad number
          <input id="payerNo" placeholder="01XXXXXXXXX" autocomplete="off"></label>
      </div>
      <button id="submitTrx" class="btn goldbtn">Submit for Verification</button>
      <div id="payErr" class="formerr" hidden></div>`;
    $("#backPlans").onclick = open;
    $$(".copyable").forEach(c=>c.onclick=()=>{ navigator.clipboard&&navigator.clipboard.writeText(c.dataset.copy); Payments.toastMsg("Copied"); });
    $("#submitTrx").onclick = submit;
  }

  async function submit(){
    const trx=$("#trx").value.trim().toUpperCase();
    const pno=$("#payerNo").value.trim();
    const errBox=$("#payErr"); errBox.hidden=true;
    if(!/^[A-Z0-9]{6,12}$/.test(trx)){ errBox.textContent="Enter a valid TrxID (6–12 letters/digits)."; errBox.hidden=false; return; }
    if(!/^01[3-9]\d{8}$/.test(pno)){ errBox.textContent="Enter the sending number (01XXXXXXXXX)."; errBox.hidden=false; return; }
    const btn=$("#submitTrx"); btn.disabled=true; btn.textContent="Submitting…";
    try{
      await firebase.firestore().collection("payments").add({
        uid: NLC.user.uid,
        email: NLC.user.email||null,
        mobile: (NLC.profile&&NLC.profile.mobile)||null,
        displayName: NLC.user.displayName||"",
        planId: selected.id, months: selected.months, amount: selected.bdt,
        trxId: trx, payerNumber: pno, status:"pending", createdAt:new Date()
      });
      $("#payBody").innerHTML = `
        <div class="paid-ok">✓</div>
        <h3 class="pay-title">Submitted for Verification</h3>
        <p class="pay-sub">TrxID <b>${esc(trx)}</b> · ৳${selected.bdt} · ${esc(selected.label)}</p>
        <p class="pay-note">Our team verifies payments promptly. You'll see “Premium” in the header once activated. Keep your confirmation SMS until then.</p>
        <button class="btn goldbtn" onclick="document.getElementById('payModal').classList.remove('open')">Done</button>`;
    }catch(e){
      errBox.textContent = e.message; errBox.hidden=false;
      btn.disabled=false; btn.textContent="Submit for Verification";
    }
  }

  async function openAccount(){
    if(!NLC.user) return;
    const u=NLC.user, p=NLC.profile||{};
    let pays=[];
    try{
      const q=await firebase.firestore().collection("payments")
        .where("uid","==",u.uid).orderBy("createdAt","desc").limit(5).get();
      pays=q.docs.map(d=>d.data());
    }catch(e){ console.warn(e); }
    const premium = NLC.isPremium();
    const until = premium ? NLC.premiumUntil().toDateString() : null;
    $("#payBody").innerHTML = `
      <h3 class="pay-title">My Account</h3>
      <div class="acct">
        <div><span>Signed in as</span><b>${esc(u.displayName||u.email||(p.mobile||""))}</b></div>
        ${p.mobile?`<div><span>Mobile</span><b>+${esc(p.mobile)}</b></div>`:""}
        <div><span>Status</span><b class="${premium?'ok':'warn'}">${premium?"👑 Premium until "+until:(NLC.testsLeft()+" free analyses remaining")}</b></div>
        ${p.pendingTrx?`<div><span>Pending</span><b>TrxID ${esc(p.pendingTrx)} under review</b></div>`:""}
      </div>
      ${pays.length?`<h4 class="mini-h">Recent payments</h4>`+
        pays.map(x=>`<div class="payrow"><span>${esc(x.trxId)}</span><b>৳${x.amount}</b>
        <i class="st st-${x.status}">${esc(x.status)}</i></div>`).join(""):""}
      <div class="acct-actions">
        ${premium?"":'<button class="btn goldbtn" id="upNow">Upgrade / Subscribe</button>'}
        <button class="btn ghost" id="signOutBtn">Sign out</button>
      </div>`;
    $("#payModal").classList.add("open");
    const up=$("#upNow"); if(up) up.onclick=open;
    $("#signOutBtn").onclick=async()=>{ await NLC.logout(); $("#payModal").classList.remove("open"); };
  }

  function toastMsg(m){ NLC.toast(m); }

  document.addEventListener("DOMContentLoaded", ()=>{
    const pm=$("#payModal");
    pm.addEventListener("click",e=>{ if(e.target===pm) pm.classList.remove("open"); });
    document.querySelectorAll("#payModal [data-close]").forEach(x=>x.onclick=()=>pm.classList.remove("open"));
  });
  return { open, openAccount };
})();
'''

# ================================================================ app.js  (v3 premium engine)
F["app.js"] = r'''const APP_V='3';
/* ============================================================
   Neum Lex Counsel · Limitation Act 1908 Engine v3 (premium)
   BM25 search · s.12 calculator (desktop verdict card) · EN/BN
   Gated by NLC (auth) — 3 free analyses then subscription
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
en:{tab_search:'Search',tab_calc:'Deadline Calculator',tab_browse:'Schedule',tab_faq:'FAQ',tab_guide:'Guidelines',
 btn_search:'Analyze',matched:'Matched',period:'Statutory period',start:'Period begins',last:'Last day to institute',
 expired:d=>`EXPIRED — ${d} day(s) past the last day (extensions under ss.4–25 may still save the claim).`,
 urgent:d=>`URGENT — only ${d} day(s) remain. Do not delay.`,
 alive:d=>`Time remaining — ${d} day(s).`,
 nomatch:'No provision matched. Try an article/section number, e.g. “article 142”.',
 nodate:'Please choose or type a start date.',
 s12:'Section 12 excludes the day from which the period is reckoned; the last day therefore equals start + full period. Exclusions/extensions may apply under ss.4–25.',
 disc:'⚖ DISCLAIMER — This platform provides general legal information compiled from the Limitation Act, 1908 (Bangladesh). Nothing herein constitutes legal advice, nor creates an advocate–client relationship. Statutory periods may be extended, excluded or saved under sections 4–25 and by special laws (s.29). Before instituting any suit, appeal or application, verify computation with a qualified advocate. Neum Lex Counsel and the developer accept no liability for reliance placed on this tool.'},
bn:{tab_search:'অনুসন্ধান',tab_calc:'মেয়াদ গণনা',tab_browse:'তফসিল',tab_faq:'প্রশ্নোত্তর',tab_guide:'নির্দেশিকা',
 btn_search:'বিশ্লেষণ',matched:'মিলে যাওয়া বিধান',period:'তামাদির মেয়াদ',start:'মেয়াদ শুরু',last:'দায়েরের শেষ দিন',
 expired:d=>`বলীয়ান — শেষ দিন অতিক্রান্ত হয়েছে ${en2bn(d)} দিন (ধারা ৪–২৫ অনুযায়ী সময় বৃদ্ধি সম্ভব)।`,
 urgent:d=>`সতর্কতা — মাত্র ${en2bn(d)} দিন বাকি!`,
 alive:d=>`অবশিষ্ট সময় — ${en2bn(d)} দিন।`,
 nomatch:'কোনো বিধান মেলেনি। অনুচ্ছেদ/ধারার নম্বর দিন, যেমন “অনুচ্ছেদ ১৪২”।',
 nodate:'শুরুর তারিখ দিন।',
 s12:'ধারা ১২ অনুযায়ী যে দিন থেকে মেয়াদ গণনা শুরু হয় সেই দিন বাদ যায়; ফলে শেষ দিন = শুরু + পূর্ণ মেয়াদ। ধারা ৪–২৫ অনুযায়ী সময় বাদ/বৃদ্ধি হতে পারে।',
 disc:'⚖ দাবিত্যাগ — এই প্ল্যাটফর্ম সীমাবদ্ধন আইন, ১৯০৮ (বাংলাদেশ) থেকে সংকলিত সাধারণ আইনি তথ্য প্রদান করে; এটি আইনি পরামর্শ নয় এবং আইনজীবী–ক্লায়েন্ট সম্পর্ক সৃষ্টি করে না। ধারা ৪–২৫ ও বিশেষ আইনের (ধারা ২৯) অধীনে মেয়াদ বাদ/বৃদ্ধি/রক্ষা পেতে পারে। মামলা দায়েরের পূর্বে অবশ্যই যোগ্য আইনজীবী দ্বারা গণনা যাচাই করুন।'}};
const t=k=>I18N[LANG][k];
const WD={en:['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
          bn:['রবিবার','সোমবার','মঙ্গলবার','বুধবার','বৃহস্পতিবার','শুক্রবার','শনিবার']};
const MON={en:['January','February','March','April','May','June','July','August','September','October','November','December'],
           bn:['জানুয়ারি','ফেব্রুয়ারি','মার্চ','এপ্রিল','মে','জুন','জুলাই','আগস্ট','সেপ্টেম্বর','অক্টোবর','নভেম্বর','ডিসেম্বর']};

/* ---------- boot ---------- */
(async function init(){
  try{
    const [kbRes,bnRes]=await Promise.all([
      fetch('data/kb.json?v='+APP_V),
      fetch('data/bn.json?v='+APP_V).catch(()=>null)]);
    if(!kbRes.ok) throw new Error('kb.json HTTP '+kbRes.status);
    KB=await kbRes.json();
    BN=(bnRes&&bnRes.ok)?await bnRes.json():{};
    DOCS=buildDocs();
    const calc=DOCS.filter(d=>d.type==='article'&&d.period).length;
    if(calc<50) throw new Error('Only '+calc+' calculable articles — check data/kb.json');
    IDX=buildIndex(DOCS);
    wireUI(); fillCalcSelect(); renderBrowse(''); renderFAQ();
    $('#footDisc').textContent=t('disc');
    $('#creditLine').textContent=NLC.cfg.brand.credit();
    console.log('[init] OK —',DOCS.length,'docs ·',calc,'calculable · v'+APP_V);
  }catch(err){ console.error('[init]',err); banner('❌ '+err.message); }
})();
function banner(m){const el=document.createElement('div');el.className='disc';el.style.borderColor='#e74c3c';
  el.textContent=m;document.querySelector('main .wrap')?.prepend(el);}

/* ---------- docs / index / search (as v2) ---------- */
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
const tok=s=>bn2en(String(s??'')).toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').split(' ').filter(Boolean);
function buildIndex(docs){const toks=docs.map(d=>tok(d.raw));const df={};
  toks.forEach(ts=>new Set(ts).forEach(w=>df[w]=(df[w]||0)+1));
  const avgdl=toks.reduce((a,x)=>a+x.length,0)/(docs.length||1)||1;
  return{N:docs.length,df,avgdl,toks};}
function glossaryExpand(q){const ql=q.toLowerCase();const extra=[];
  (BN.glossary||[]).forEach(g=>{
    if(ql.includes(g.en.toLowerCase())&&!q.includes(g.bn))extra.push(g.bn);
    else if(q.includes(g.bn)&&!ql.includes(g.en.toLowerCase()))extra.push(g.en);});
  return q+' '+extra.slice(0,6).join(' ');}
function search(q,k=6){const qt=tok(glossaryExpand(q));if(!qt.length)return[];
  return DOCS.map((d,i)=>{let s=0;const ts=IDX.toks[i];
    for(const w of qt){let tf=0;for(const x of ts)if(x===w)tf++;
      if(!tf)continue;const f=IDX.df[w]||0;
      s+=Math.log(1+(IDX.N-f+.5)/(f+.5))*tf*2.2/(tf+1.2*(.25+.75*ts.length/IDX.avgdl));}
    return[d,s];}).filter(x=>x[1]>0).sort((a,b)=>b[1]-a[1]).slice(0,k);}

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

/* ---------- premium date formatting (desktop verdict card) ---------- */
function fmtFull(d){
  const dt=new Date(d),L=LANG;
  const wd=WD[L][dt.getUTCDay()],mo=MON[L][dt.getUTCMonth()];
  const dd=(L==='bn')?en2bn(dt.getUTCDate()):dt.getUTCDate();
  const yy=(L==='bn')?en2bn(dt.getUTCFullYear()):dt.getUTCFullYear();
  return wd+', '+dd+' '+mo+' '+yy;
}
function verdictHTML(hit,start,end,days){
  let chip,cls;
  if(days<0){chip=t('expired')(Math.abs(days));cls='expired';}
  else if(days<=30){chip=t('urgent')(days);cls='urgent';}
  else{chip=t('alive')(days);cls='ok';}
  return `<div class="verdict ${cls}">
    <div class="v-badge">${esc(hit.cite)}</div>
    <div class="v-title">${esc(hit.title)}</div>
    <div class="v-grid">
      <div class="v-col"><span>${esc(t('start'))}</span><b>${esc(fmtFull(start))}</b></div>
      <div class="v-arrow">⟶</div>
      <div class="v-col last"><span>${esc(t('last'))}</span><b class="goldtxt">${esc(fmtFull(end))}</b></div>
    </div>
    <div class="v-meta"><span>${esc(t('period'))}:</span> <b>${esc(LANG==='bn'?((BN.periods_bn||{})[hit.period]||hit.period):hit.period)}</b>
      · <span>${esc((hit.begin||'').slice(0,90))}</span></div>
    <div class="v-chip ${cls}">${esc(chip)}</div>
    <div class="ensnip">${esc(t('s12'))}</div>
  </div>`;
}

/* ---------- gated query pipeline ---------- */
async function runQuery(qRaw){
  if(!(await NLC.gate('search'))) return;
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
        $('#results').innerHTML=
          card(hit,verdictHTML(hit,dt,end,days))+
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

/* ---------- calculator tab ---------- */
function fillCalcSelect(){
  const sel=$('#calcArt');if(!sel)return;
  sel.innerHTML='';let n=0;
  for(const[div,arts]of Object.entries(KB.schedule||{}))
    (arts||[]).filter(a=>a&&a.p).forEach(a=>{
      const o=document.createElement('option');o.value=a.a;
      o.textContent='Art '+a.a+' — '+short(a.d,52)+' ('+a.p+')';sel.appendChild(o);n++;});
  const o57=[...sel.options].find(o=>o.value==='57');if(o57)sel.value='57';
  $('#calcCount').textContent=n+' provisions loaded';
}
async function runCalc(){
  if(!(await NLC.gate('calc'))) return;
  const out=$('#calcOut'),aid=$('#calcArt').value,dval=$('#calcDate').value;
  if(!dval){out.innerHTML='<div class="disc">'+esc(t('nodate'))+'</div>';return;}
  const doc=DOCS.find(d=>d.cite==='A'+aid);const pp=doc&&parsePeriod(doc.period);
  if(!doc||!pp){out.innerHTML='<div class="disc">⚠ Cannot compute for Art '+esc(aid)+'</div>';return;}
  const start=new Date(dval+'T00:00:00Z'),end=addPeriod(start,pp.n,pp.u);
  const today=new Date();today.setUTCHours(0,0,0,0);
  const days=Math.round((end-today)/864e5);
  out.innerHTML=card(doc,verdictHTML(doc,start,end,days))+discBlock();
}

/* ---------- browse / faq ---------- */
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
function renderFAQ(){
  $('#faqList').innerHTML=(KB.faq||[]).map((f,i)=>{
    const b=(BN.faq_bn||{})[String(i)];
    const qq=(LANG==='bn'&&b)?b.q:f.q,aa=(LANG==='bn'&&b)?b.a:f.a;
    return'<div class="faq-q">'+esc(qq)+'</div><div class="faq-a">'+esc(aa)+'</div>';}).join('');
}

/* ---------- events ---------- */
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
      runQuery($('#q').value);window.scrollTo({top:0,behavior:'smooth'});}});
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

# ================================================================ index.html (premium)
F["index.html"] = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Neum Lex Counsel · Limitation Act 1908 Bangladesh — Premium Legal Engine</title>
<meta name="description" content="Premium bilingual (English/বাংলা) limitation-law engine by Neum Lex Counsel — Md Nazmul Islam, Advocate, Supreme Court of Bangladesh. 183 schedule articles, deadline calculator, expert guidance.">
<meta name="theme-color" content="#0b1120">
<meta property="og:title" content="Neum Lex Counsel · Limitation Act 1908 Engine">
<meta property="og:description" content="Premium bilingual limitation-law intelligence. Advocate-crafted. Not legal advice.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;800&family=Noto+Serif+Bengali:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css?v=3">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚖️</text></svg>">
</head>
<body>
<header class="topbar">
  <div class="wrap bar-inner">
    <div class="brand">
      <div class="crest">⚖</div>
      <div>
        <h1>NEUM LEX COUNSEL</h1>
        <p class="sub">Limitation Act, 1908 · Bangladesh · Premium Legal Intelligence</p>
        <p class="credit" id="creditLine"></p>
      </div>
    </div>
    <div class="bar-actions">
      <span id="planChip" class="plan-chip" hidden></span>
      <button id="langBtn" class="lang-btn">বাংলা</button>
      <button id="authBtn" class="btn gold-outline">🔐 Sign in</button>
    </div>
  </div>
</header>

<nav class="tabs wrap" aria-label="Sections">
  <button class="tab active" data-tab="search">🔍 <span data-i18n="tab_search">Search</span></button>
  <button class="tab" data-tab="calc">📅 <span data-i18n="tab_calc">Deadline Calculator</span></button>
  <button class="tab" data-tab="browse">📚 <span data-i18n="tab_browse">Schedule</span></button>
  <button class="tab" data-tab="faq">❓ <span data-i18n="tab_faq">FAQ</span></button>
  <button class="tab" data-tab="guide">📜 <span data-i18n="tab_guide">Guidelines</span></button>
</nav>

<main class="wrap">
  <!-- SEARCH -->
  <section id="tab-search" class="panel active">
    <div class="hero-strip">
      <p>Expert computation of limitation periods · Compiled from Act No. IX of 1908 · English &amp; বাংলা</p>
    </div>
    <div class="searchbox">
      <input id="q" type="text" autocomplete="off"
        placeholder='Try: "article 113" · "money lent 15/03/2022" · "স্থাবর সম্পত্তির দখল" · "section 19"'>
      <button id="go" class="btn goldbtn" data-i18n="btn_search">Analyze</button>
    </div>
    <div class="chips">
      <span class="chip" data-q="article 113">Art 113 · 1 year</span>
      <span class="chip" data-q="recover possession of immovable property">Possession · 12 yrs</span>
      <span class="chip" data-q="money lent 15/03/2022">Deadline demo</span>
      <span class="chip" data-q="appeal to High Court Division">Appeal · 90 days</span>
      <span class="chip" data-q="ধার ফেরতের মামলার মেয়াদ">ধার · ৩ বছর</span>
      <span class="chip" data-q="written acknowledgement of debt">s.19 Acknowledgement</span>
    </div>
    <div id="results"></div>
  </section>

  <!-- CALCULATOR -->
  <section id="tab-calc" class="panel">
    <div class="calc-layout">
      <div class="card pad">
        <h2 class="serif">Deadline Calculator</h2>
        <p class="muted" data-i18n="calc_p">Select the statutory provision and the date the period began. Under section 12, the first day is excluded — the last day equals start + full period.</p>
        <label class="field"><span data-i18n="calc_prov">Provision</span>
          <select id="calcArt"></select>
          <small id="calcCount" class="muted"></small></label>
        <label class="field"><span data-i18n="calc_date">Period begins on</span>
          <input id="calcDate" type="date"></label>
        <button id="calcGo" class="btn goldbtn wide" data-i18n="calc_btn">Compute last day</button>
      </div>
      <div>
        <div id="calcOut" class="calc-out">
          <div class="card pad empty-hint">
            <div class="empty-ico">🗓️</div>
            <p class="muted">Your verdict card will appear here — with the exact last day, weekday, and a live countdown.</p>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- BROWSE -->
  <section id="tab-browse" class="panel">
    <input id="browseFilter" class="filter" placeholder="Filter… / ফিল্টার">
    <div id="browse"></div>
  </section>

  <!-- FAQ -->
  <section id="tab-faq" class="panel">
    <div id="faqList"></div>
  </section>

  <!-- GUIDELINES -->
  <section id="tab-guide" class="panel">
    <div class="card pad guide">
      <h2 class="serif">User Guidelines &amp; Terms</h2>

      <h3>1. Purpose</h3>
      <p>Neum Lex Counsel provides a curated, bilingual reference to the Limitation Act, 1908 (Act No. IX of 1908) — including every article of the First Schedule (Suits, Appeals, Applications), governing sections, and a computation utility reflecting section 12. It is designed for advocates, law students, litigants-in-person and researchers.</p>

      <h3>2. How to Use</h3>
      <ul>
        <li><b>Search</b> — describe your cause in plain English or বাংলা, or cite an article/section number directly.</li>
        <li><b>Deadline Calculator</b> — choose the provision and the date the period began; the verdict card shows the last day with weekday and countdown. Remember: the first day is excluded (s.12).</li>
        <li><b>Schedule</b> — browse all 183 articles across the three Divisions.</li>
        <li><b>Free access</b> — Schedule, FAQ and Guidelines are free. Search and Calculator: <b>3 complimentary analyses</b> per registered account, thereafter a subscription is required.</li>
      </ul>

      <h3>3. Interpretation Caution</h3>
      <p>Limitation is a subtle branch of law. Sections 4–25 permit exclusions and extensions (court closure, sufficient cause, legal disability, absence of the defendant, fraud, written acknowledgement, part payment, injunctions, prior proceedings). Special statutes may prescribe different periods (s.29). The calculator reflects the bare Act only; it cannot weigh your facts.</p>

      <h3>4. Subscription Terms</h3>
      <ul>
        <li>Plans: 1 month ৳100 · 3 months ৳200 · 6 months ৳400 · 12 months ৳550.</li>
        <li>Payment via bKash/Nagad ‘Send Money’ to the numbers shown at checkout, followed by TrxID submission.</li>
        <li>Activation follows manual verification — ordinarily within a few hours.</li>
        <li>A plan extends from the current expiry (stackable) once approved.</li>
      </ul>

      <h3>5. Refund Policy</h3>
      <p>Subscription access is a digital service. Where a verified payment has not been activated within 72 hours, contact counsel@neumlex — we will activate promptly or refund in full. No refunds after activation, save for demonstrated duplication of payment.</p>

      <h3>6. Acceptable Use</h3>
      <p>One account per person. Automated scraping, credential sharing or resale of access is prohibited and may result in termination without refund.</p>

      <h3>7. Legal Disclaimer</h3>
      <p class="emph">This platform offers general legal information — it is not legal advice and does not create an advocate–client relationship. Statutes are amended and case law evolves; the bare Act is presented as published in the Laws of Bangladesh. Before instituting any suit, appeal or application, verify computation and strategy with a qualified advocate.</p>

      <div class="guide-credit" id="guideCredit"></div>
    </div>
  </section>
</main>

<!-- AUTH MODAL -->
<div id="authModal" class="modal">
  <div class="sheet">
    <button class="x" data-close>✕</button>
    <div class="crest big">⚖</div>
    <h3 class="serif center">Welcome to Neum Lex Counsel</h3>
    <p class="muted center">Sign in to use your 3 complimentary analyses.</p>
    <div class="mtabs">
      <button class="mtab active" data-pane="paneMobile">📱 Mobile</button>
      <button class="mtab" data-pane="paneGoogle">📧 Gmail</button>
    </div>
    <div id="paneMobile" class="mpane active">
      <div class="minitabs">
        <button class="minitab active" data-form="login">Sign in</button>
        <button class="minitab" data-form="signup">Create account</button>
      </div>
      <div id="formLogin">
        <label>Mobile number<input id="liMobile" placeholder="01712345678" autocomplete="username"></label>
        <label>Password<input id="liPass" type="password" autocomplete="current-password"></label>
        <button id="doLogin" class="btn goldbtn wide">Sign in</button>
      </div>
      <div id="formSignup" hidden>
        <label>Full name<input id="suName" placeholder="e.g. Abdul Karim"></label>
        <label>Mobile number<input id="suMobile" placeholder="01712345678"></label>
        <label>Create password (min 6 chars)<input id="suPass" type="password"></label>
        <button id="doSignup" class="btn goldbtn wide">Create account — 3 free analyses</button>
      </div>
    </div>
    <div id="paneGoogle" class="mpane">
      <p class="muted center">One click with your Google account.</p>
      <button id="doGoogle" class="btn gbtn wide">Continue with Gmail</button>
    </div>
    <div id="authErr" class="formerr" hidden></div>
  </div>
</div>

<!-- PAY / ACCOUNT MODAL -->
<div id="payModal" class="modal">
  <div class="sheet wide-sheet">
    <button class="x" data-close>✕</button>
    <div id="payBody"></div>
  </div>
</div>

<footer class="foot">
  <div class="wrap">
    <div class="foot-brand">
      <div class="crest small">⚖</div>
      <div>
        <b>NEUM LEX COUNSEL</b>
        <p id="creditLine2" class="credit"></p>
      </div>
    </div>
    <p id="footDisc"></p>
    <p class="muted small">Source: The Limitation Act, 1908 (Act No. IX of 1908) · Laws of Bangladesh ·
    <a href="/api/search?q=article%20113">Public JSON API</a></p>
  </div>
</footer>
<noscript><div class="disc">JavaScript is required. Data API: /api/search?q=…</div></noscript>

<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore-compat.js"></script>
<script src="config.js?v=3"></script>
<script src="auth.js?v=3"></script>
<script src="payments.js?v=3"></script>
<script src="app.js?v=3"></script>
<script>
document.getElementById('creditLine2').textContent=document.getElementById('creditLine').textContent;
document.getElementById('guideCredit').textContent=document.getElementById('creditLine').textContent;
</script>
</body>
</html>
'''

# ================================================================ styles.css (premium)
F["styles.css"] = r''':root{
  --bg:#0b1120;--bg2:#0e1526;--panel:#121b31;--panel2:#182342;--line:#26324f;
  --txt:#eef2fb;--mut:#9aa8c7;--gold:#c9a227;--gold2:#e6c766;--ivory:#f5ecd7;
  --acc:#4f8cff;--good:#2ecc71;--warn:#f39c12;--bad:#e74c3c;
}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1200px 500px at 50% -10%,#152039 0%,var(--bg) 55%);
  color:var(--txt);font-family:'Inter','Noto Serif Bengali',system-ui,sans-serif;line-height:1.6}
body.bn{font-family:'Noto Serif Bengali','Inter',sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:0 18px}
.serif,h1,h2,.divh,.pay-title,.sheet h3{font-family:'Cormorant Garamond','Noto Serif Bengali',serif}

.topbar{background:linear-gradient(180deg,#0d1526,#0b1120);border-bottom:1px solid var(--line)}
.bar-inner{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:18px}
.brand{display:flex;gap:14px;align-items:center}
.crest{width:52px;height:52px;border-radius:50%;display:grid;place-items:center;font-size:26px;
  background:linear-gradient(145deg,#1b2745,#0e1526);border:1px solid var(--gold);
  box-shadow:0 0 0 3px rgba(201,162,39,.12), inset 0 0 18px rgba(201,162,39,.15);color:var(--gold2)}
.crest.big{width:64px;height:64px;margin:0 auto 10px}
.crest.small{width:40px;height:40px;font-size:20px}
h1{margin:0;font-size:24px;letter-spacing:3px;color:var(--ivory);font-weight:700}
.sub{margin:2px 0 0;color:var(--gold2);font-size:12.5px;letter-spacing:.6px}
.credit{margin:3px 0 0;color:var(--mut);font-size:12px;font-style:italic}
.bar-actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:flex-end}
.lang-btn,.btn{border-radius:9px;padding:10px 18px;font-size:14px;cursor:pointer;font-family:inherit}
.lang-btn{background:var(--panel2);color:var(--txt);border:1px solid var(--line)}
.lang-btn:hover{border-color:var(--gold)}
.btn{border:none;font-weight:600}
.goldbtn{background:linear-gradient(135deg,var(--gold),#b08d1e);color:#141003}
.goldbtn:hover{filter:brightness(1.1)}
.gold-outline{background:transparent;border:1px solid var(--gold);color:var(--gold2)}
.gold-outline:hover{background:rgba(201,162,39,.1)}
.ghost{background:var(--panel2);border:1px solid var(--line);color:var(--txt)}
.gbtn{background:#fff;color:#222}
.wide{width:100%;padding:13px}
.plan-chip{background:linear-gradient(135deg,#2a2140,#1b2745);border:1px solid var(--gold);
  color:var(--gold2);border-radius:999px;padding:6px 14px;font-size:12.5px;font-weight:700}

.tabs{display:flex;gap:6px;padding:14px 18px;flex-wrap:wrap}
.tab{background:none;border:1px solid transparent;color:var(--mut);padding:9px 15px;
  border-radius:9px;cursor:pointer;font-size:14px;font-family:inherit}
.tab.active{background:var(--panel2);color:var(--gold2);border-color:var(--gold)}
.panel{display:none}.panel.active{display:block;animation:fade .25s}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1}}

.hero-strip{border:1px solid var(--line);border-left:3px solid var(--gold);border-radius:10px;
  background:var(--panel);padding:12px 16px;margin-bottom:16px}
.hero-strip p{margin:0;color:var(--mut);font-size:13.5px;font-style:italic}

.searchbox{display:flex;gap:10px}
#q{flex:1;background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:15px 17px;color:var(--txt);font-size:16px;font-family:inherit}
#q:focus{outline:none;border-color:var(--gold)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 22px}
.chip{background:var(--panel);border:1px solid var(--line);color:var(--mut);
  border-radius:999px;padding:6px 14px;font-size:13px;cursor:pointer}
.chip:hover{color:var(--gold2);border-color:var(--gold)}

.card{background:var(--panel);border:1px solid var(--line);border-top:2px solid rgba(201,162,39,.5);
  border-radius:13px;padding:18px;margin-bottom:14px;box-shadow:0 8px 24px rgba(0,0,0,.25)}
.card.pad{padding:26px}
.cite{display:inline-block;background:var(--gold);color:#141003;border-radius:6px;
  padding:2px 9px;font-size:12px;font-weight:800;margin-right:8px}
.cite.sec{background:#d8c690}.cite.def{background:#9b6bff;color:#fff}.cite.faq{background:#2aa198;color:#fff}
.rtitle{font-weight:600;font-size:15.5px;margin:0 0 8px}
.rbody{color:#ccd7ee;font-size:14.5px;white-space:pre-wrap}
.bnsnip{color:var(--gold2);font-size:13.5px;margin-top:8px;border-top:1px dashed var(--line);padding-top:8px}
.ensnip{color:var(--mut);font-size:12.5px;margin-top:10px}

.pill{display:inline-block;border-radius:999px;padding:3px 12px;font-size:12.5px;font-weight:700;margin:4px 0}
.p-days{background:#3d1f24;color:#ff8a8a}.p-months{background:#3a2c17;color:#ffc46b}
.p-years{background:#153425;color:#6fe3a5}.p-big{background:#2a2140;color:#c9a6ff}

/* --- Verdict card (desktop-calculator fix) --- */
.calc-layout{display:grid;grid-template-columns:380px 1fr;gap:18px;align-items:start}
.field{display:flex;flex-direction:column;gap:6px;margin:16px 0;font-size:13.5px;color:var(--mut)}
select,input[type=date],input[type=text],input[type=password],.sheet input{
  background:var(--bg2);border:1px solid var(--line);border-radius:9px;
  padding:12px 13px;color:var(--txt);font-family:inherit;font-size:15px;width:100%}
input[type=date]{min-height:48px;font-size:16px}
select:focus,input:focus{outline:none;border-color:var(--gold)}
.verdict{background:linear-gradient(160deg,#182342,#101a30);border:1px solid var(--gold);
  border-radius:14px;padding:22px;box-shadow:0 10px 30px rgba(0,0,0,.35)}
.v-badge{display:inline-block;background:var(--gold);color:#141003;border-radius:6px;
  padding:2px 10px;font-size:12px;font-weight:800;letter-spacing:.5px}
.v-title{font-family:'Cormorant Garamond',serif;font-size:19px;font-weight:700;margin:10px 0 14px;color:var(--ivory)}
.v-grid{display:grid;grid-template-columns:1fr 44px 1.2fr;align-items:center;gap:6px}
.v-col span{display:block;color:var(--mut);font-size:11.5px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}
.v-col b{font-size:16.5px;font-weight:700}
.v-arrow{color:var(--gold);font-size:20px;text-align:center}
.goldtxt{color:var(--gold2)}
.v-meta{margin-top:14px;color:var(--mut);font-size:13px}
.v-meta b{color:var(--txt)}
.v-chip{display:inline-block;margin-top:14px;border-radius:999px;padding:7px 16px;font-weight:800;font-size:13.5px}
.v-chip.ok{background:#153425;color:#6fe3a5;border:1px solid #2ecc71}
.v-chip.urgent{background:#3a2c17;color:#ffc46b;border:1px solid var(--warn)}
.v-chip.expired{background:#3d1f24;color:#ff8a8a;border:1px solid var(--bad)}
.calc-out:empty::before{content:''}
.empty-hint{text-align:center}.empty-ico{font-size:44px;margin-bottom:6px}
#calcCount{margin-top:4px}

table{width:100%;border-collapse:collapse;font-size:13.5px}
th{color:var(--gold2);text-align:left;font-size:11.5px;text-transform:uppercase;letter-spacing:1px;
  padding:8px 10px;border-bottom:1px solid var(--line)}
td{padding:9px 10px;border-bottom:1px solid #1c2640;vertical-align:top}
tr.row{cursor:pointer}tr.row:hover{background:var(--panel2)}
td.per{white-space:nowrap;font-weight:700}
.divh{margin:22px 0 10px;font-size:18px;color:var(--gold2);border-bottom:1px solid var(--line);padding-bottom:6px}
.filter{width:100%;background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:12px 14px;color:var(--txt);font-size:15px;margin-bottom:16px;font-family:inherit}

.faq-q{background:var(--panel);border:1px solid var(--line);border-radius:11px;
  padding:14px 16px;cursor:pointer;margin-bottom:10px;font-weight:600;font-size:14.5px}
.faq-a{display:none;padding:0 16px 14px;color:#ccd7ee;font-size:14px;white-space:pre-wrap}
.faq-q.open+.faq-a{display:block}.faq-q.open{border-color:var(--gold)}

.disc{margin:18px 0;background:#231a2e;border:1px solid #7d4bd6;border-left:4px solid var(--gold);
  border-radius:11px;padding:14px 16px;font-size:13px;color:#e8ddff;white-space:pre-wrap}

/* --- Modals --- */
.modal{display:none;position:fixed;inset:0;background:rgba(5,8,16,.72);backdrop-filter:blur(4px);
  z-index:50;place-items:center;padding:18px}
.modal.open{display:grid}
.sheet{background:linear-gradient(170deg,#141d33,#0e1526);border:1px solid var(--gold);
  border-radius:16px;padding:26px;width:100%;max-width:430px;position:relative;
  box-shadow:0 24px 60px rgba(0,0,0,.5);max-height:90vh;overflow:auto}
.wide-sheet{max-width:560px}
.x{position:absolute;top:10px;right:12px;background:none;border:none;color:var(--mut);
  font-size:18px;cursor:pointer}
.center{text-align:center}
.mtabs{display:flex;gap:8px;margin:16px 0}
.mtab{flex:1;background:var(--panel2);border:1px solid var(--line);color:var(--mut);
  border-radius:9px;padding:10px;cursor:pointer;font-family:inherit}
.mtab.active{color:var(--gold2);border-color:var(--gold)}
.mpane{display:none}.mpane.active{display:block}
.minitabs{display:flex;gap:6px;margin-bottom:14px}
.minitab{flex:1;background:none;border:none;color:var(--mut);padding:8px;cursor:pointer;
  border-bottom:2px solid var(--line);font-family:inherit}
.minitab.active{color:var(--gold2);border-bottom-color:var(--gold)}
label{display:block;margin:10px 0;font-size:13px;color:var(--mut)}
label input{margin-top:5px}
.formerr{background:#3d1f24;border:1px solid var(--bad);color:#ffb3b3;border-radius:9px;
  padding:10px 12px;font-size:13px;margin-top:12px}

/* --- Payments --- */
.pay-title{margin:4px 0 6px;font-size:24px;color:var(--ivory)}
.pay-sub{color:var(--mut);font-size:14px;margin:0 0 16px}
.plans{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.plan{position:relative;background:var(--panel2);border:1px solid var(--line);border-radius:13px;
  padding:16px 12px;text-align:center;cursor:pointer;transition:.15s}
.plan:hover{border-color:var(--gold);transform:translateY(-2px)}
.plan.best{border-color:var(--gold)}
.best-ribbon{position:absolute;top:-9px;left:50%;transform:translateX(-50%);
  background:var(--gold);color:#141003;font-size:9.5px;font-weight:800;letter-spacing:1px;
  border-radius:999px;padding:2px 10px}
.plan-name{font-size:13px;color:var(--mut);font-weight:600}
.plan-price{font-family:'Cormorant Garamond',serif;font-size:30px;font-weight:700;color:var(--gold2)}
.plan-price .tk{font-size:17px;margin-right:2px}
.plan-note{font-size:11.5px;color:#8fd7ab}
.plan-per{font-size:11px;color:var(--mut);margin-top:3px}
.backlink{background:none;border:none;color:var(--gold2);cursor:pointer;font-family:inherit;
  font-size:13px;margin-bottom:8px;padding:0}
.paybox{background:var(--bg2);border:1px solid var(--line);border-radius:11px;padding:6px 14px;margin:12px 0}
.payline{display:flex;justify-content:space-between;gap:12px;padding:10px 0;
  border-bottom:1px dashed var(--line);font-size:14px}
.payline:last-child{border-bottom:none}
.payline span{color:var(--mut)}
.copyable{cursor:pointer;text-decoration:underline dotted var(--gold)}
.pay-note{color:var(--mut);font-size:12.5px;margin:10px 0 16px}
.paid-ok{width:64px;height:64px;border-radius:50%;background:#153425;color:#6fe3a5;
  display:grid;place-items:center;font-size:30px;margin:6px auto 14px;border:1px solid #2ecc71}
.acct div{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px dashed var(--line);font-size:14px}
.acct span{color:var(--mut)}.acct .ok{color:#6fe3a5}.acct .warn{color:#ffc46b}
.acct-actions{display:flex;gap:10px;margin-top:18px}
.mini-h{margin:16px 0 6px;color:var(--gold2)}
.payrow{display:flex;gap:10px;align-items:center;padding:7px 0;font-size:13.5px;border-bottom:1px dashed var(--line)}
.payrow span{flex:1}
.st{font-style:normal;font-size:11px;border-radius:999px;padding:2px 9px;font-weight:700}
.st-pending{background:#3a2c17;color:#ffc46b}.st-approved{background:#153425;color:#6fe3a5}
.st-rejected{background:#3d1f24;color:#ff8a8a}

/* --- Guidelines / footer / toast --- */
.guide h3{color:var(--gold2);margin:22px 0 6px;font-size:16px}
.guide p,.guide li{color:#ccd7ee;font-size:14.5px}
.guide ul{padding-left:22px}
.emph{border:1px solid var(--gold);border-radius:10px;padding:14px;background:rgba(201,162,39,.06)}
.guide-credit{margin-top:20px;color:var(--mut);font-style:italic;font-size:13px;border-top:1px solid var(--line);padding-top:12px}
.foot{margin-top:44px;border-top:1px solid var(--line);padding:26px 0 46px;background:#080d18}
.foot-brand{display:flex;gap:12px;align-items:center;margin-bottom:12px}
.foot p{margin:5px 0;font-size:13.5px;color:var(--mut);white-space:pre-wrap}
.small{font-size:12px}.muted{color:var(--mut)}
a{color:var(--gold2)}
#nlcToast{position:fixed;bottom:22px;left:50%;transform:translateX(-50%) translateY(20px);
  background:var(--panel2);border:1px solid var(--gold);color:var(--gold2);border-radius:999px;
  padding:10px 22px;font-size:13.5px;opacity:0;transition:.3s;pointer-events:none;z-index:99}
#nlcToast.show{opacity:1;transform:translateX(-50%) translateY(0)}

@media(max-width:860px){
  .calc-layout{grid-template-columns:1fr}
  .plans{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:640px){
  .bar-inner{flex-direction:column;align-items:flex-start}
  .v-grid{grid-template-columns:1fr;gap:10px}
  .v-arrow{display:none}
}
'''

# ================================================================ admin.html + admin.js
F["admin.html"] = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Neum Lex Counsel — Admin</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css?v=3"></head>
<body>
<header class="topbar"><div class="wrap bar-inner">
  <div class="brand"><div class="crest">⚖</div><div><h1 style="font-size:20px">ADMIN · VERIFICATION DESK</h1>
  <p class="sub">Neum Lex Counsel</p></div></div>
  <button id="authBtn" class="btn gold-outline">Sign in</button>
</div></header>
<main class="wrap" style="padding-top:22px">
  <div id="gate" class="disc">Sign in with an authorised administrator account.</div>
  <div id="desk" hidden>
    <h2 class="divh">Pending payments</h2>
    <div id="pending"></div>
    <h2 class="divh">Recent decisions</h2>
    <div id="recent"></div>
  </div>
</main>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore-compat.js"></script>
<script src="config.js?v=3"></script>
<script src="admin.js?v=3"></script>
</body></html>
'''

F["admin.js"] = r'''window.Admin=(function(){
  const $=s=>document.querySelector(s);
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let db=null,user=null;

  function isAdmin(u){ return u&&u.email&&APP_CONFIG.adminEmails.includes(u.email); }

  function init(){
    if(APP_CONFIG.firebase.apiKey.startsWith("PASTE")){
      $("#gate").textContent="Firebase not configured — edit config.js first (SETUP.md).";return;}
    firebase.initializeApp(APP_CONFIG.firebase);
    db=firebase.firestore();
    firebase.auth().onAuthStateChanged(onAuth);
    $("#authBtn").onclick=()=>firebase.auth().signInWithPopup(
      new firebase.auth.GoogleAuthProvider());
  }

  function onAuth(u){
    user=u;
    const b=$("#authBtn");
    if(!u){ b.textContent="Sign in"; $("#gate").hidden=false; $("#desk").hidden=true; return; }
    b.textContent=u.email;
    if(!isAdmin(u)){ $("#gate").hidden=false;
      $("#gate").textContent="⛔ "+u.email+" is not an authorised admin. Add this email to adminEmails in config.js.";
      $("#desk").hidden=true; return; }
    $("#gate").hidden=true; $("#desk").hidden=false; load();
  }

  async function load(){
    const pend=await db.collection("payments").where("status","==","pending")
      .orderBy("createdAt","desc").limit(100).get();
    $("#pending").innerHTML=pend.empty?'<p class="muted">No pending payments. 🎉</p>':
      pend.docs.map(d=>row(d,true)).join("");
    const rec=await db.collection("payments").orderBy("createdAt","desc").limit(20).get();
    $("#recent").innerHTML=rec.docs.filter(d=>d.data().status!=="pending")
      .map(d=>row(d,false)).join("")||'<p class="muted">—</p>';
    wire(pend);
  }

  function row(d,actions){
    const p=d.data();
    return `<div class="card"><p class="rtitle"><span class="cite">${esc(p.trxId)}</span>
      ৳${p.amount} · ${esc(p.planId)} · ${esc(p.payerNumber)}</p>
      <div class="rbody">User: ${esc(p.displayName||p.email||p.mobile||p.uid)}<br>
      ${p.createdAt?new Date(p.createdAt.toDate()).toLocaleString():""}</div>
      ${actions?`<div class="acct-actions">
        <button class="btn goldbtn" data-ok="${d.id}">✓ Approve</button>
        <button class="btn ghost" data-no="${d.id}">✕ Reject</button></div>`
        :`<div class="payrow"><i class="st st-${esc(p.status)}">${esc(p.status)}</i>
          ${p.approvedBy?'<span class="muted">by '+esc(p.approvedBy)+'</span>':''}</div>`}
    </div>`;
  }

  function wire(pend){
    pend.docs.forEach(d=>{
      const p=d.data();
      const okB=document.querySelector(`[data-ok="${d.id}"]`);
      const noB=document.querySelector(`[data-no="${d.id}"]`);
      if(okB) okB.onclick=()=>approve(d,p);
      if(noB) noB.onclick=async()=>{
        if(!confirm("Reject TrxID "+p.trxId+"?"))return;
        await d.ref.update({status:"rejected",approvedBy:user.email,decidedAt:new Date()});
        load();};
    });
  }

  async function approve(d,p){
    if(!confirm("Approve TrxID "+p.trxId+" — grant "+p.months+" month(s)?"))return;
    const uref=db.collection("users").doc(p.uid);
    const snap=await uref.get();
    const cur=(snap.exists&&snap.data().planExpiry)?snap.data().planExpiry.toDate():new Date(0);
    const base=cur>new Date()?cur:new Date();
    const end=new Date(base);end.setUTCMonth(end.getUTCMonth()+p.months);
    const batch=db.batch();
    batch.update(uref,{planExpiry:end});
    batch.update(d.ref,{status:"approved",approvedBy:user.email,approvedAt:new Date(),
      planExpiry:end});
    try{
      await batch.commit();
      alert("✓ Approved\nUser plan valid until "+end.toDateString());
      load();
    }catch(e){
      alert("Firestore write failed: "+e.message+"\n\nCheck: admin email listed in rules (firebase-rules.txt) and published in Firebase console.");
    }
  }
  document.addEventListener("DOMContentLoaded",init);
  return{onAuth};
})();
'''

# ================================================================ rules + setup + vercel + gitignore
F["firebase-rules.txt"] = r'''rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    function isAdmin() {
      return request.auth != null &&
             request.auth.token.email in ['YOUR_ADMIN_GMAIL@gmail.com'];  // ← EDIT
    }

    match /users/{uid} {
      allow read: if request.auth != null &&
                     (request.auth.uid == uid || isAdmin());
      allow create: if request.auth != null && request.auth.uid == uid;
      allow update: if isAdmin();   // only admin extends plans / resets counters
    }

    match /payments/{id} {
      allow create: if request.auth != null &&
                       request.resource.data.uid == request.auth.uid;
      allow read: if isAdmin() ||
                     (request.auth != null && resource.data.uid == request.auth.uid);
      allow update, delete: if isAdmin();
    }
  }
}
'''

F["SETUP.md"] = r'''# 🛠️ Neum Lex Counsel — Production Setup (15 minutes)

## 1. Firebase project (auth + database) — free tier
1. Open https://console.firebase.google.com → **Add project** (name: `neum-lex`) → disable Analytics → Create.
2. Left menu → **Build → Authentication → Get started**.
   - Sign-in method → enable **Google** (one toggle; support email = yours) → Save.
   - Sign-in method → enable **Email/Password** → Save.
   - (Skip **Phone** for now — SMS costs money. Mobile login here uses number + password.)
3. **Authentication → Settings → Authorized domains** → Add your Vercel domain
   (e.g. `limitation-act-1908-knc4.vercel.app`) and `localhost`.
4. ⚙️ **Project settings → General → Your apps → Web (</>)** → register app → copy the
   `firebaseConfig` object.
5. **Build → Firestore Database → Create database** → Production mode → location `asia-south1`.
6. Firestore → **Rules** tab → paste `firebase-rules.txt` → **replace `YOUR_ADMIN_GMAIL@gmail.com`**
   with your real Gmail (in BOTH places: rules file & step 7) → **Publish**.

## 2. Configure the site
Edit **config.js**:
- paste `firebaseConfig` values,
- `adminEmails: ["your-real-gmail@gmail.com"]`,
- `payment.bkash` / `payment.nagad` → your real numbers,
- check the developer name spelling in `brand.developer`.

## 3. Deploy
    git add -A && git commit -m "premium v3: auth, subscriptions, admin, fixed calculator" && git push
Vercel redeploys automatically.

## 4. Daily operations (you, the Advocate)
- **Approve payments:** open `https://YOUR-SITE.vercel.app/admin` → sign in with the
  admin Gmail → each pending TrxID shows **✓ Approve / ✕ Reject** → Approve instantly
  extends that user's plan (stacks on remaining time).
- **Password reset (mobile accounts):** Firebase console → Authentication → Users →
  find the user (email looks like `8801XXXXXXXXX@mobile.neumlex.app`) → ⋮ → Reset password →
  share the temp password with the client.
- **Check revenue:** Firestore → `payments` collection (approved = revenue).

## 5. Verify the full funnel (5 min)
1. Open site → Search anything → **login modal appears** (gated).
2. Create account with mobile `01712345678` / password → search 3 times →
   on the 4th, the **subscription wall** appears with all 4 Tk plans.
3. Pick 3 Months ৳200 → payment sheet shows bKash/Nagad → submit any TrxID
   (e.g. `TEST123456`) → "Submitted for verification".
4. Open `/admin` in another tab → Approve → back on the main site, header shows
   **👑 Premium until …** → unlimited searches work.

## Notes
- Google/Gmail accounts also get the 3-free-tests gate (same rules).
- Real bKash **OTP phone auth** or the bKash Payment Gateway API can be layered on
  later without changing the UI (Phase-2).
- The public JSON API `/api/search` remains open (marketing/lead-gen). To meter it
  later, move it behind Firebase App Check.
'''

F["vercel.json"] = r'''{
  "framework": null,
  "cleanUrls": true,
  "trailingSlash": false,
  "functions": { "api/*.js": { "includeFiles": "data/kb.json" } },
  "headers": [
    { "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "SAMEORIGIN" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" }
      ]},
    { "source": "/data/(.*)",
      "headers": [{ "key": "Cache-Control", "value": "public, max-age=3600" }]},
    { "source": "/api/(.*)",
      "headers": [{ "key": "Cache-Control", "value": "no-store" }]}
  ]
}
'''

F[".gitignore"] = "premium_upgrade.py\nupgrade_production.py\ngen_web.py\nmake_site.py\n.vercel\nnode_modules/\n.DS_Store\n*.log\n__pycache__/\n"

# admin.html uses api/search.js? no — untouched. Keep existing api/.


def main():
    for rel, content in F.items():
        p = Path(rel); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8", newline="\n")
        print(f"  [ok] {rel}")
    if not Path("api/search.js").exists():
        print("  [!] api/search.js missing — keep your existing one (bonus API).")
    if not Path("data/kb.json").exists():
        print("  [!] data/kb.json missing — run earlier setup first!")
    print("""
============================================================
 PREMIUM v3 WRITTEN.
 NEXT (see SETUP.md):
 1) Firebase: create project → enable Google + Email/Password
    → authorized domains → Firestore → paste firebase-rules.txt
 2) Edit config.js  (keys, admin Gmail, bKash/Nagad numbers,
    developer name spelling)
 3) git add -A && git commit -m "premium v3" && git push
============================================================""")

if __name__ == "__main__":
    main()