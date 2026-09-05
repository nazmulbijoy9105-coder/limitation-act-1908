/* Neum Lex Counsel — auth, test-gate, profile badge (Firebase compat) */
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
