# 🛠️ Neum Lex Counsel — Production Setup (15 minutes)

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
