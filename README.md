# TuneHub – paid tuning community (Django 5.2)

A members-only library where car tuners share **engine maps (ECU), gearbox maps (TCU), turbo settings and
modifications**: structured specs, before/after numbers, parameter tables, private file attachments,
comments, helpful votes and bookmarks. Access costs **$5 / month** (Stripe). UI in **PL / EN / DE**.

Visitors see a public landing page, the library list and teaser pages (good for SEO and conversion);
descriptions, parameters, files and discussion are for subscribers only.

## Quick start (Windows, local development)
```bash
python -m venv C:\Users\<you>\.venvs\tunehub          # keep the venv path SHORT on Windows
C:\Users\<you>\.venvs\tunehub\Scripts\python -m pip install -r requirements.txt
copy .env.example .env                                   # DEBUG=True, Stripe keys empty
python scripts/build_translations.py                     # compiles PL/DE messages (.mo)
python manage.py migrate
python manage.py seed_demo                               # fictional demo data + demo accounts
python manage.py runserver
```
Open http://localhost:8000. Demo accounts and their password are documented at the top of
`apps/core/management/commands/seed_demo.py` (admin/moderator, subscriber, free user).

**No Stripe keys?** With `DEBUG=True` and empty Stripe settings, the pricing page shows
*Activate test subscription*, which simulates a paid account. It is unreachable in production.

Run the tests (68): `python manage.py test`

## Features
| Area | What is built |
|---|---|
| Library | Filters (make → model, category, fuel, stage, content language, full-text), sort by newest / most helpful / most discussed, pagination, browse by make |
| Entries | Specs (engine, ECU, gearbox, turbo, boost, fuel, model year, stage), power/torque before → after, parameter table (e.g. boost per rpm), up to 5 attachments, edit/delete by author, SEO-friendly URLs with canonical redirects |
| Community | Comments (+ email notification to the author, opt-out), helpful votes (no self-voting) → reputation, bookmarks, public member profiles |
| Moderation | Reports (one open report per user), **auto-hide after 3 reports**, admin actions (hide/publish/resolve), open-report counter, "suggest a missing car" queue with one-click *add to catalogue* |
| Paywall | Teaser pages with schema.org paywall markup; files streamed only to subscribers |
| Billing | Stripe Checkout (+ Stripe Tax, VAT ID, promo codes), customer portal, signed + idempotent webhooks that re-read the subscription from Stripe (out-of-order safe) |
| Accounts | Email login, email verification (+ resend), password reset, profile settings, GDPR export (JSON) and account erasure |
| i18n | PL (default), EN, DE; `hreflang` alternates, translated emails in the user's language |
| SEO | `sitemap.xml` with language alternates, `robots.txt`, canonical URLs, meta descriptions |

## Security & privacy
- **Passwords:** Argon2id; validators (min 10 chars, common/numeric checks).
- **Brute force:** login throttling counts only *failed* attempts (per IP, per account+IP, and a high global per-account cap), so nobody can lock out a real user; rate limits on signup, password reset, comments, reports, votes, checkout (cache-based – use Redis in production).
- **Account takeover:** email-confirmation links never log anyone in (no login CSRF, no pre-registration takeover); a completed password reset confirms the address and replaces any password set by whoever registered it first.
- **Billing state:** access follows the customer's *best* subscription, so an old cancelled subscription can't lock out a paying member; past-due members are sent to the portal instead of a second checkout; account deletion cancels every live subscription.
- **Headers:** CSP without inline scripts, Permissions-Policy, HSTS (prod), `X-Frame-Options: DENY`, COOP, nosniff, strict referrer.
- **Uploads:** extension allow-list, size and count limits, content sniffing (rejects executables disguised as `.bin`), image verification, random file names, SHA-256 checksums, stored outside any public path, downloaded as `application/octet-stream` with `no-store`; files are deleted from disk also when entries are removed in bulk/cascade.
- **Proxy trust:** Docker publishes gunicorn on 127.0.0.1 only, because `X-Forwarded-For`/`-Proto` are trusted from exactly one reverse proxy.
- **Accounts:** no account enumeration on resend/reset, verification links signed and bound to the email.
- **Privacy:** minimal data (email, nickname, consents), essential cookies only, no trackers; card data never reaches the server.
- **Admin** URL configurable (`ADMIN_URL`).

## Stripe setup (test mode first)
1. Create a Product with a recurring **$5 / month** Price → `STRIPE_PRICE_ID`.
2. Enable **Stripe Tax** and the **Customer portal** (allow cancel + payment method update).
3. Webhook `https://<domain>/billing/webhook/stripe/` with events `checkout.session.completed`,
   `customer.subscription.created|updated|deleted|paused|resumed` → `STRIPE_WEBHOOK_SECRET`.
   Locally: `stripe listen --forward-to localhost:8000/billing/webhook/stripe/`.
4. Access is granted **only** by the verified webhook, never by the success page.

## Deployment (Docker)
```bash
copy .env.example .env.production    # DEBUG=False, real SECRET_KEY, ALLOWED_HOSTS, SITE_URL, Stripe, SMTP, ADMIN_URL
set POSTGRES_PASSWORD=<strong password>
docker compose up --build -d
```
The image runs migrations on start, serves static files via WhiteNoise and exposes `/healthz`.
Put a TLS reverse proxy (Caddy/Traefik/nginx) in front, back up the `pgdata` and `media` volumes.

## Project layout
```
apps/accounts   custom User (email login), signup/verification, profile, GDPR export/delete
apps/catalog    makes/models, entries, parameters, attachments, comments, votes, bookmarks, reports
apps/billing    Stripe checkout/portal/webhook, subscription mirror, dev-mode simulation
apps/core       landing, legal pages, rate limiter, security headers, sitemap/robots, seed_demo
scripts/build_translations.py   PL/DE dictionary → .po/.mo (no GNU gettext needed)
```

## Before going live (still to do)
- Replace the placeholder Terms/Privacy with lawyer-written texts (controller, legal bases, retention, processors, DPAs with Stripe / hosting / email provider), company data on invoices, VAT OSS registration.
- Decide the moderation policy for emission-related content (Terms placeholder prohibits DPF/EGR/AdBlue delete); DSA contact point.
- Licensing of user-uploaded ECU files (copyright of OEM software).
- Malware scanning of uploads (e.g. ClamAV) and object storage (private S3 + signed URLs) when traffic grows.
- Error monitoring (e.g. Sentry), uptime monitoring, database backups with restore tests.
