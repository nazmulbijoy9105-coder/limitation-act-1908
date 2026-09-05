window.Admin=(function(){
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
