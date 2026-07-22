# 🚀 Go-Live Playbook — Breakthrough OKC 2026

**Architecture (target):**
```
breakthroughokc.com / www   → Cloudways   → WEBSITE + landing page (static HTML)
registration.breakthroughokc.com → GHL    → checkout funnel (Step 2 → Check Out → payment)
sponsorship.breakthroughokc.com  → GHL    → sponsor funnel
lc.breakthroughokc.com           → Mailgun → EMAIL (never touched)
```
Do the phases in order. Phases 1–3 are additive (nothing live changes). Only Phase 4 flips the switch.

---

## PHASE 1 — GHL: move funnels onto their subdomains (no DNS change, no downtime)
- [ ] GHL → **Settings → Domains → + Connect** `registration.breakthroughokc.com` (CNAME already points to GHL → verifies fast + auto-SSL)
- [ ] **+ Connect** `sponsorship.breakthroughokc.com`
- [ ] Open your **event/checkout funnel** (Home → Step 2 → Check Out) → **Settings → Domain → `registration.breakthroughokc.com`**
- [ ] Open your **sponsors funnel** → **Settings → Domain → `sponsorship.breakthroughokc.com`**
- [ ] **TEST both live** — run a real/test payment on the checkout; confirm the Thank-You step + workflows fire
- [ ] **Copy the checkout entry URL** (the Step-2 / contact-info step on `registration.…`) and the **sponsor funnel URL** → send them to me → I lock every Register/Apply button to the exact URLs

## PHASE 2 — Meta Pixel
- [ ] Copy the Meta Pixel `<script>` from your GHL funnel's **head-tracking** box → send to me → I wire it into all 9 website pages + the landing page
      *(the A2P/LeadConnector chat widget is already on every page)*

## PHASE 3 — Cloudways: host the site (test before any DNS change)
- [ ] Create a Cloudways **server** (DigitalOcean/Vultr, smallest size is fine)
- [ ] Create a **Custom App (PHP stack)** — NOT WordPress
- [ ] Download the site: GitHub repo → green **Code → Download ZIP** → unzip
- [ ] Upload the **contents of `website/`** (all `.html` + the `assets/` folder) to the app's **webroot / public_html** (Cloudways File Manager or SFTP)
- [ ] Upload `landing-page.html` too (this is your ad Step-1 page)
- [ ] Open the Cloudways **temporary app URL** → click every page, check mobile, confirm Register/Apply hit the subdomains
- [ ] Cloudways → **add domain** `breakthroughokc.com` + `www` to the app → **enable SSL** (Let's Encrypt)

## PHASE 4 — DNS cutover (GoDaddy) — the only switch
*(A day before: lower the `www` CNAME TTL to 600s. `@` is already 600s.)*
- [ ] `@` (root) **A record**: `162.159.140.166` → **your Cloudways server IP**
- [ ] `www` **CNAME** `sites.ludicrous.cloud` → point to **Cloudways** (or make `www` an A record → Cloudways IP)
- [ ] **DO NOT TOUCH:** `registration`, `sponsorship` (funnels) · all `lc` / `email.lc` / `mx` / `_dmarc` / `_domainkey` (email)

Because the funnels already answer on their subdomains (Phase 1), checkout never goes dark.

## PHASE 5 — redirects + verify
- [ ] On Cloudways, add redirects for old root paths:
      `/home` → homepage · `/sponsors` → sponsors page · `/contact-info` → `registration.breakthroughokc.com/…`
- [ ] Test the full flow live: site → **Register** → checkout → payment · sponsors → **Apply** → sponsor funnel
- [ ] Update your **ad links** to the new landing-page URL
- [ ] After ~24h stable, raise TTLs back up; archive the old GHL root funnels

---

## Send me to finish the wiring
1. **Checkout URL** (registration subdomain) — I lock all Register buttons
2. **Sponsor funnel URL** (sponsorship subdomain) — I lock all Apply buttons
3. **Meta Pixel** snippet — I add to all pages
4. *(optional)* remaining sponsor/exhibitor logos, event/venue photos
