# TRACTIAN Funnel Intelligence Dashboard

A local demo app for a **North American Growth Lead** interview — deliberately scoped to the
middle and bottom of the funnel, not top-of-funnel discovery (that's a separate demo). This
one assumes every account is already known — a lead, an open opportunity, or an existing
customer — and answers one question per account: **why does this account need action this
week?**

Signals are modeled on the real stack this role owns: **6sense, RollWorks, Demandbase**
(third-party intent), **Segment** (first-party behavioral data), and **HubSpot / Salesforce**
(CRM stage and activity, HubSpot being the backbone). No external tool is actually connected —
everything runs on synthetic data generated locally, except optionally the Anthropic API for
copy generation. Every mocked integration (Meta sync, HubSpot nurture, Clay enrichment,
Sendoso gifting) is a real, working flow that logs what it would do — click any of them to see
an actual Mermaid flowchart of the integration it would follow.

## Run it

```bash
cd tractian_funnel_dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5051** (a different port from the discovery-build demo, so both can
run side by side). Set `ANTHROPIC_API_KEY` before starting for AI-generated copy instead of
the templated fallback — the app works identically either way.

## What this demonstrates

- **A persistent active book, not a discovery engine.** Accounts are inserted once and mutate
  across sprints (stage advances, usage drifts, signals accumulate) — there's nothing to
  "discover," it's a living CRM simulation.
- **A health-gated expansion model.** Customer accounts must clear a usage/adoption health
  gate before an expansion opportunity is scored at all — best practice (Gainsight/Totango-
  style): don't propose more product to an unhealthy account. Accounts that fail the gate are
  force-routed to Win-Back Risk regardless of usage signals.
- **Fixed plays, customized messaging.** Four tactical buckets (Velocity Rescue, Buying
  Committee Expanding, Renewal & Expansion, Win-Back Risk) each carry a constant channel mix;
  the actual email/call-script/InMail content is generated per account from whatever signals
  actually fired — same hypothesis framework (signal → implication → persona → value) as the
  discovery build, re-scoped to warm-account nudges instead of cold outreach.
- **A real auto-enrollment mechanic.** When a Single-Threaded Opportunity signal fires, the
  system checks which buying-committee functional areas aren't represented yet and adds new
  contacts to fill the gap — the "surround outreach" motion, not just a suggestion.
- **Momentum-gated, frequency-capped gifting**, tied to each play's tactical mix (Win-Back
  Risk deliberately withholds gifting until a positive re-engagement signal fires first).
- **A running CTA experiment** (hypothesis → variant → simulated outcome → results) at
  `/experiments`, same mechanic as the discovery build.
- **Honest metrics only** — every number on the dashboard is a direct query over real
  per-account fields (an Opportunity's own `deal_amount`, a Customer's own health ratios), not
  an estimate multiplied up after the fact.

## File-by-file

| File | Purpose |
|---|---|
| `app.py` | Flask app: dashboard, plays, account report, experiments, sprint/gift/sync/flow-diagram API routes |
| `db.py` | SQLite schema — persistent `accounts`/`contacts` tables (mutated, not re-inserted per sprint), `sprints`, `audience_syncs`, `gifts_sent` |
| `scheduler.py` | APScheduler `IntervalTrigger` for the sprint cadence job (default every 14 days) |
| `pipeline/knowledge_base.py` | Lifecycle stages, the 10 MOFU/BOFU signals (each tagged to its real source tool), the 4 plays, health-gate + Action Score constants |
| `pipeline/synthetic.py` | Generates the ~50-account active book across Lead→Customer, with realistic deal/usage fields |
| `pipeline/active_book.py` | Mutates the persistent book each sprint: stage advances, usage drift, fresh signal injection |
| `pipeline/scorer.py` | Action Score (stage risk or expansion opportunity + threading health + signal urgency), health gate, play assignment |
| `pipeline/contacts.py` | Persistent per-account contacts, engagement tracking, single-threaded surround-outreach enrollment |
| `pipeline/messaging.py` | The outbound-copy hypothesis framework, re-scoped for warm-account signals |
| `pipeline/content_generator.py` | Assembles email/call-script/InMail/gift content — Anthropic API or templated fallback |
| `pipeline/gifting.py` | Gift-readiness scoring: momentum-triggered, frequency-capped, gated by play |
| `pipeline/flow_diagrams.py` | Mermaid flowchart content for every mocked integration |
| `pipeline/plays.py` | Scores the whole book live, groups accounts needing action by play |
| `pipeline/audience_sync.py` | Mock reverse-ETL to Meta/HubSpot, tagged by play, auto-fires per sprint |
| `pipeline/growth_metrics.py` | Dashboard metrics — every figure a direct computation, nothing estimated |
| `pipeline/sprint.py` | Orchestrates one sprint end to end |
| `templates/` | Jinja2 pages: dashboard, plays, account report, sprint detail, experiments |
| `static/style.css` | TRACTIAN brand tokens + component styling |
| `static/app.js` | Sprint trigger/polling, sync/gift actions, Mermaid flow-diagram modals |

## Ways to extend live (for the interview)

- **Add a new signal**: one entry in `SIGNAL_LIBRARY` (`pipeline/knowledge_base.py`) plus a
  detail-generation branch in `synthetic.generate_signal_detail` — it's live in scoring, play
  assignment, and messaging immediately.
- **Change a scoring weight**: `STAGE_BENCHMARK_DAYS`, the health-gate thresholds, or the
  expansion-opportunity point bands are all named constants in `knowledge_base.py`.
- **Add a 5th play**: add to `PLAYS` and `PLAY_ORDER`, give it a `tactical_mix` and
  `gifting_allowed` flag — `plays.py` and the dashboard pick it up automatically.
- **Add a new mocked integration flow**: one entry in `pipeline/flow_diagrams.py` (a Mermaid
  flowchart string) and a button with `data-flow="your_key"` — no new JS needed.

## Notes

- The active book is generated once and persists in `tractian_funnel.db`; each sprint mutates
  it in place (some accounts advance a stage, signals accumulate, customer usage drifts) —
  deleting the db resets to a fresh 50-account book on the next run.
- Signals older than 90 days are excluded; 31-60 days apply an 80% decay, 61-90 days a 60%
  decay — funnel signals go stale faster than the old company-event signals did (30-day
  default lookback vs. 90).
- There's deliberately no per-sprint account snapshot — the book is persistent, so `/plays`
  always reflects current state, not a point-in-time list from any specific sprint.
