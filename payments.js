/* Neum Lex Counsel — plans, bKash/Nagad TrxID submission, account panel */
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
