# TRACTIAN Funnel Intelligence Dashboard

A GTM system built for a **North American Growth Lead** interview — deliberately scoped to the
middle and bottom of the funnel, not top-of-funnel discovery. Every account is assumed already
known — a lead, an open opportunity, or an existing customer — and the app answers one question
per account: **why does this account need action this week?**

**Live**: https://gtm-dashboard-production-1bbe.up.railway.app (deployed via Railway, auto-deploys
from `main` on this repo). Note: the database resets on every redeploy, so click "Run Sprint Now"
on first load if the book looks empty.

Signals are modeled on the real stack this role owns: **6sense, RollWorks, Demandbase**
(third-party intent), **Segment** (first-party behavioral data), and **HubSpot / Salesforce**
(CRM stage and activity, HubSpot being the backbone). No external tool is actually connected —
everything runs on synthetic data generated locally, except optionally the Anthropic API for copy
generation. Every mocked integration (Meta sync, HubSpot nurture, Clay enrichment, Sendoso
gifting) is a real, working flow that logs what it would do — click any of them to see an actual
Mermaid flowchart of the integration it would follow.

## Run it

```bash
cd tractian_funnel_dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5051**. On macOS, double-clicking `run.command` does the same thing and
opens the browser automatically. Set `ANTHROPIC_API_KEY` before starting for AI-generated copy
instead of the templated fallback — the app works identically either way, and every generated
email/call-script/InMail is labeled "AI-drafted" or "Templated" depending on which actually ran.

## What this demonstrates

- **A persistent active book, not a discovery engine.** Accounts are inserted once and mutate
  across sprints (stage advances, usage drifts, signals accumulate) — there's nothing to
  "discover," it's a living CRM simulation.
- **A health-gated expansion model.** Customer accounts must clear a usage/adoption health gate
  before an expansion opportunity is scored at all — best practice (Gainsight/Totango-style):
  don't propose more product to an unhealthy account. Accounts that fail the gate are
  force-routed to Win-Back Risk regardless of usage signals.
- **Fixed plays, customized messaging, per-play channel mix.** Four tactical buckets (Velocity
  Rescue, Buying Committee Expanding, Renewal & Expansion, Win-Back Risk) each carry a *constant*
  channel mix — only Buying Committee Expanding actually spends on paid ads, since the others are
  sales-led or relationship-led by design. The Plays tab shows a full Content Overview per play
  (personas targeted, ad involvement, the actual opening line per driving signal, and the constant
  ad creative for ad-driven plays) so a launch decision doesn't require clicking into individual
  accounts.
- **Outbound copy that never reveals its own tracking.** Every signal is tagged
  customer-referenceable or not (`messaging.SIGNAL_CUSTOMER_REFERENCEABLE`). First-party/public
  signals (a customer's own usage, their own contract, a public facility announcement) are stated
  directly. Signals that only exist because of behavioral/intent tracking (a pricing-page visit,
  an ad click, competitor research, a LinkedIn role change) are never stated as an observed fact —
  that reads as surveillance, not insight — and instead drive a natural, generic reach-out reason.
  The Anthropic prompt path enforces the same rule.
- **Signals that stop mattering once they're stale.** A signal is scoped to the lifecycle stage
  it was generated for (e.g. Deal Stalled In Stage only applies to Opportunities) and that scope
  is re-validated at scoring time, not just generation time — so an old Opportunity-stage signal
  can't keep driving score or messaging after the account has already advanced to Customer.
- **A real auto-enrollment mechanic.** When a Single-Threaded Opportunity signal fires, the
  system checks which buying-committee functional areas aren't represented yet and adds new
  contacts to fill the gap — the "surround outreach" motion, not just a suggestion.
- **Momentum-gated, frequency-capped gifting**, tied to each play's tactical mix (Win-Back Risk
  deliberately withholds gifting until a positive re-engagement signal fires first).
- **Per-play Reporting, not one generic dashboard.** Each play's primary metric is the one that
  actually proves it worked for that play's objective — accounts moved stage (Velocity Rescue),
  net-new engaged contacts (Buying Committee Expanding), pipeline value in the campaign (Renewal &
  Expansion), health-gate pass rate (Win-Back Risk) — plus per-variant ad creative CTR and a
  computed (not scripted) Key Findings panel.
- **A running CTA experiment** (hypothesis → variant → simulated outcome → results), tracked
  per campaign in Reporting.
- **Conceptual Plays, honestly scoped.** Ten additional plays were brainstormed against the real
  JD; four turned out to already be covered by what's live, two became new live signals, one
  folded into an existing play's tactical mix, and three (Meeting Prep Brief, No-Show Recovery,
  Mutual Action Plan Builder) genuinely need infrastructure this app doesn't model (calendar data,
  meeting attendance). Rather than fake that data, each runs on one static hand-written example
  with a real integration flow diagram — visibly not live, but showing exactly how it would
  connect.
- **Honest metrics only** — every number on the dashboard is a direct query over real
  per-account fields (an Opportunity's own `deal_amount`, a Customer's own health ratios), not an
  estimate multiplied up after the fact.
- **Mobile-responsive** — nav, tables, grids, and modals all reflow correctly below 640px.

## File-by-file

| File | Purpose |
|---|---|
| `app.py` | Flask app: dashboard, plays, account report, reporting, conceptual plays, sprint/gift/sync/flow-diagram API routes |
| `db.py` | SQLite schema — persistent `accounts`/`contacts` tables (mutated, not re-inserted per sprint), `sprints`, `audience_syncs`, `gifts_sent` |
| `scheduler.py` | APScheduler `IntervalTrigger` for the sprint cadence job (default every 14 days) |
| `pipeline/knowledge_base.py` | Lifecycle stages, the 12 MOFU/BOFU signals (each tagged to its real source tool and stage scope), the 4 plays (`ads_involved`/`ad_angle` included), health-gate + Action Score constants |
| `pipeline/synthetic.py` | Generates the ~50-account active book across Lead→Customer, with realistic deal/usage fields |
| `pipeline/active_book.py` | Mutates the persistent book each sprint: stage advances, usage drift, fresh signal injection |
| `pipeline/scorer.py` | Action Score (stage risk or expansion opportunity + threading health + signal urgency), health gate, play assignment — re-validates each signal's stage scope against the account's *current* stage before it counts |
| `pipeline/contacts.py` | Persistent per-account contacts, engagement tracking, single-threaded surround-outreach enrollment |
| `pipeline/messaging.py` | The outbound-copy hypothesis framework — customer-referenceable signal flags, safe reach-out hooks for tracking-derived signals, persona value props |
| `pipeline/content_generator.py` | Assembles email/call-script/InMail/gift content — Anthropic API or templated fallback, tags each contact's content with which mode actually ran |
| `pipeline/ad_creative.py` | Mock Meta ad creative variants, assigned per sync with simulated impressions/clicks against a target CTR |
| `pipeline/gifting.py` | Gift-readiness scoring: momentum-triggered, frequency-capped, gated by play |
| `pipeline/flow_diagrams.py` | Mermaid flowchart content for every mocked integration |
| `pipeline/plays.py` | Scores the whole book live, groups accounts needing action by play, builds each play's Content Overview (personas, ad info, per-signal email hook previews) |
| `pipeline/audience_sync.py` | Mock reverse-ETL to Meta/HubSpot, tagged by play and campaign, only syncs to Meta for plays that actually involve ads |
| `pipeline/reporting.py` | Per-campaign reporting: play-specific primary metric, ad creative summary, computed Key Findings |
| `pipeline/conceptual_plays.py` | The 10-idea disposition table plus the 3 conceptual play examples |
| `pipeline/growth_metrics.py` | Dashboard metrics — every figure a direct computation, nothing estimated |
| `pipeline/sprint.py` | Orchestrates one sprint end to end |
| `templates/` | Jinja2 pages: dashboard, plays, account report, sprint detail, reporting, conceptual plays |
| `static/style.css` | TRACTIAN brand tokens, component styling, mobile breakpoint |
| `static/app.js` | Sprint trigger/polling, sync/gift actions, Mermaid flow-diagram modals, play explainer/filter interactions |
| `run.command` | Double-clickable local launcher (macOS) — activates the venv, starts the server, opens the browser |

## Ways to extend live (for the interview)

- **Add a new signal**: one entry in `SIGNAL_LIBRARY` (`pipeline/knowledge_base.py`, including
  `stage_scope` and `functional_areas`), a `SIGNAL_CUSTOMER_REFERENCEABLE` flag plus either a
  `SIGNAL_TRIGGER_VERB` or `SIGNAL_SAFE_HOOK` entry in `messaging.py`, and a detail-generation
  branch in `synthetic.generate_signal_detail` — it's live in scoring, play assignment, Content
  Overview previews, and messaging immediately.
- **Change a scoring weight**: `STAGE_BENCHMARK_DAYS`, the health-gate thresholds, or the
  expansion-opportunity point bands are all named constants in `knowledge_base.py`.
- **Add a 5th play**: add to `PLAYS` and `PLAY_ORDER` with a `tactical_mix`, `gifting_allowed`,
  and `ads_involved` flag — `plays.py`, Reporting, and the dashboard pick it up automatically.
- **Add a new mocked integration flow**: one entry in `pipeline/flow_diagrams.py` (a Mermaid
  flowchart string) and a button with `data-flow="your_key"` — no new JS needed.

## Notes

- The active book is generated once and persists in `tractian_funnel.db`; each sprint mutates it
  in place (some accounts advance a stage, signals accumulate, customer usage drifts) — deleting
  the db resets to a fresh 50-account book on the next run. On Railway specifically, this means
  every redeploy resets the book, since the filesystem isn't persistent there.
- Signals older than 90 days are excluded; 31-60 days apply an 80% decay, 61-90 days a 60% decay —
  funnel signals go stale faster than the old company-event signals did (30-day default lookback
  vs. 90).
- There's deliberately no per-sprint account snapshot — the book is persistent, so `/plays`
  always reflects current state, not a point-in-time list from any specific sprint.
