/* Neum Lex Counsel — site configuration. EDIT THIS FILE ONLY. */
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
