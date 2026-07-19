"""The outbound-copy hypothesis framework: signal -> operational implication
-> persona priority -> TRACTIAN value.

The point of every generated email/call-script/InMail is to answer one
question: "why does this specific person, at this specific account, need to
hear from us this week?" — a warm-account nudge, not a cold-outreach pitch.
That answer is assembled from four layers, each a lookup table below:

  1. SIGNAL_TRIGGER_VERB / SIGNAL_GERUND / SIGNAL_SAFE_HOOK
     — how to open the copy without leaking internal tracking. Every signal
       is tagged in SIGNAL_CUSTOMER_REFERENCEABLE: signals that are
       first-party or public (their own product usage, their own contract,
       a public facility announcement) can be named directly via
       SIGNAL_TRIGGER_VERB/SIGNAL_GERUND ("Saw that {company} recently...").
       Signals that only exist because we're tracking them from outside
       (a pricing-page visit, an ad click, third-party intent data, a
       LinkedIn role change, a competitor search) are NOT safe to state to
       the recipient as an observed fact — that reads as surveillance, not
       insight. Those use SIGNAL_SAFE_HOOK instead: a natural reach-out
       reason that doesn't reveal the tracking mechanism.
  2. SIGNAL_IMPLICATION
     — why this matters TO THE RECIPIENT, in second-person customer voice.
       This is not "what does this mean for our pipeline" (that's internal
       sales analysis and belongs in call_script_notes, which really are
       rep-only) — it's "why should the person reading this email care."
  3. TITLE_FRAME
     — what THIS specific title (not just functional area) actually cares
       about day to day, and the TRACTIAN value tied to that. Unchanged from
       persona to persona regardless of funnel stage — a Plant Manager cares
       about the same things whether they're a lead or a live deal.
  4. INDUSTRY_CHALLENGE / STAGE_FALLBACK_IMPLICATION
     — supporting texture: an industry-specific pain point, and a
       stage-appropriate fallback for accounts with no fresh signal at all.
       STAGE_FALLBACK_IMPLICATION is customer-voiced too — it must never
       name our internal lifecycle-stage labels (Lead/MQL/SQL) to the
       recipient; nobody should read an email that implies "you are an SQL."

content_generator.py assembles these into the actual copy; this file only
holds the domain content so the messaging logic can be read/edited on its
own, the same way knowledge_base.py holds the scoring domain.
"""

# ---------------------------------------------------------------------------
# Which signals are safe to name directly to the recipient as an observed
# fact, vs. which ones would reveal that we're tracking them from outside.
# True  = first-party (their own usage/contract) or public (news) — fine to
#         say "we saw X" because X is something they'd expect us to know or
#         is public information.
# False = only exists because of ad/intent/behavioral tracking, or is a
#         claim about a specific person's behavior we can't be sure the
#         recipient is even aware of (e.g. "your champion went quiet") —
#         these use SIGNAL_SAFE_HOOK instead of naming the tracked behavior.
# ---------------------------------------------------------------------------
SIGNAL_CUSTOMER_REFERENCEABLE = {
    "usage_above_contracted_capacity": True,
    "deal_stalled_in_stage": False,
    "single_threaded_opportunity": False,
    "champion_engagement_drop": False,
    "account_surge_score_threshold": False,
    "pricing_page_revisit_new_contact": False,
    "intent_surge_category_keywords": False,
    "ad_engagement_spike": False,
    "renewal_window_approaching": True,
    "reactivated_engagement": False,
    "competitor_evaluation_activity": False,
    "company_expansion_event": True,
}

# ---------------------------------------------------------------------------
# Layer 1: how to state the trigger event itself, in plain sentences.
# SIGNAL_TRIGGER_VERB fits "{company} recently {verb}." Only ever used for
# signals marked customer-referenceable above.
# SIGNAL_GERUND fits "...while also {gerund}." — same restriction.
# ---------------------------------------------------------------------------
SIGNAL_TRIGGER_VERB = {
    "usage_above_contracted_capacity": "started running above its contracted sensor capacity",
    "renewal_window_approaching": "moved into its contract renewal window",
    "company_expansion_event": "announced a new or expanding facility",
}

SIGNAL_GERUND = {
    "usage_above_contracted_capacity": "running above its contracted sensor capacity",
    "renewal_window_approaching": "moving into its renewal window",
    "company_expansion_event": "standing up a new or expanding facility",
}

# ---------------------------------------------------------------------------
# For signals NOT safe to name directly (SIGNAL_CUSTOMER_REFERENCEABLE is
# False): a natural, lowercase clause — no leading capital, no trailing
# period — that reads as a normal reason to reach out, without asserting we
# observed the recipient's specific behavior. Fits mid-sentence, e.g. after
# an em dash or "Reaching out because ...". May use {industry}.
# ---------------------------------------------------------------------------
SIGNAL_SAFE_HOOK = {
    "deal_stalled_in_stage": "it's been a little while since we last connected, and I wanted to check back in directly rather than let it sit",
    "single_threaded_opportunity": "I wanted to loop you in directly, rather than everything routing through a single point of contact",
    "champion_engagement_drop": "I wanted to reach back out and make sure this still has the right person driving it on your end",
    "account_surge_score_threshold": "a lot of {industry} teams are re-evaluating their approach to unplanned downtime right now, and it felt like the right time to reconnect",
    "pricing_page_revisit_new_contact": "I wanted to make sure you had a direct line to me as you look into TRACTIAN, rather than getting things secondhand",
    "intent_surge_category_keywords": "given where things are headed across {industry} on unplanned downtime, I wanted to make sure TRACTIAN was actually on your radar",
    "ad_engagement_spike": "there's been some renewed interest in TRACTIAN from your team recently, and I wanted to reach out directly rather than leave it passive",
    "reactivated_engagement": "it's been a bit since our last conversation, and I didn't want too much time to pass without checking back in",
    "competitor_evaluation_activity": "teams evaluating a few different options before deciding is normal, and I wanted to make sure you had the full picture on TRACTIAN specifically",
}

# ---------------------------------------------------------------------------
# Layer 2: why this matters TO THE RECIPIENT — second-person, no internal
# sales/CRM jargon ("deal stage," "buying committee," "champion"), and never
# a claim about specifically-tracked behavior for the not-customer-safe
# signals above (that's what made the old copy read like internal analysis
# leaking into a customer email).
# ---------------------------------------------------------------------------
SIGNAL_IMPLICATION = {
    "usage_above_contracted_capacity": "If your team's relying on more sensor coverage than what's on the contract, it's worth getting that formalized rather than running on borrowed capacity — the risk is losing visibility right when you need it most.",
    "deal_stalled_in_stage": "Evaluations that stretch on longer than expected usually aren't a sign the fit is wrong — it's usually just that priorities got pulled elsewhere for a while, which is exactly when a direct nudge helps more than another passive follow-up.",
    "single_threaded_opportunity": "Decisions like this tend to move faster and hold up better once more than one person on your team has direct visibility into it — looping others in earlier usually beats a round of catch-up later.",
    "champion_engagement_drop": "Plant and reliability priorities shift fast, and it's easy for a conversation like this to lose momentum through no fault of anyone's — a quick reconnect is usually all it takes to get it back on track.",
    "account_surge_score_threshold": "When more of the right people at a company start paying attention to the same problem around the same time, that's usually the moment worth actually getting in front of, not waiting for a formal ask.",
    "pricing_page_revisit_new_contact": "The more people on your team who have direct context on this, the smoother the actual decision tends to go later — worth making sure everyone's working from the same information.",
    "intent_surge_category_keywords": "Unplanned downtime tends to become a priority in waves across an industry — when it's actively on people's minds, that's usually the best time to actually solve it, not after the next outage forces the issue.",
    "ad_engagement_spike": "When a topic starts getting attention from more than one person on a team, it's usually because it's become genuinely relevant — worth addressing directly instead of letting it stay passive.",
    "renewal_window_approaching": "Renewals tend to go better as growth conversations than as pure negotiations — getting ahead of it now leaves room to talk about where things are headed, not just what it costs to keep things as they are.",
    "reactivated_engagement": "A little time passing doesn't usually mean the interest is gone — it just means something else took priority for a while, and reconnecting directly is usually enough to pick it back up.",
    "competitor_evaluation_activity": "Comparing options before committing is normal and expected — the goal isn't to rush that, it's to make sure whatever you land on is actually judged on what it does for your team, not just the pitch.",
    "company_expansion_event": "New capacity means new equipment and new failure modes before there's a reliability process in place to catch them — getting ahead of that before the line starts running is a lot cheaper than fixing it after the first outage.",
}

# ---------------------------------------------------------------------------
# Layer 4a: one industry-specific pain point, for extra specificity and to
# avoid the email reading like it could've been sent to any manufacturer.
# Stage-agnostic — an automotive plant's line-down math doesn't change
# whether the account is a lead or a customer.
# ---------------------------------------------------------------------------
INDUSTRY_CHALLENGE = {
    "Automotive & Parts": "line-down costs cascade fast through a just-in-time supply chain",
    "Food & Beverage": "sanitation-driven downtime windows leave little room for surprise failures",
    "Manufacturing (General)": "unplanned downtime tends to hit hardest across mixed equipment fleets",
    "Mining & Metals": "remote, harsh-environment assets are expensive to inspect manually",
    "Chemicals": "failures on safety-critical rotating equipment carry outsized risk",
    "Oil & Gas": "aging rotating assets are often spread across remote, hard-to-staff sites",
    "Pulp & Paper": "one failure on a continuous-process line stops the entire line",
    "Consumer Goods": "high-mix production lines mean frequent changeovers stress equipment differently than a single-SKU line",
}

# ---------------------------------------------------------------------------
# Layer 4b: fallback hypothesis for accounts with no fresh signal at all —
# still grounded in real lifecycle-stage data, not generic filler.
# ---------------------------------------------------------------------------
STAGE_FALLBACK_IMPLICATION = {
    "Lead": "Interest doesn't always show up as a reply or a click — sometimes it just needs a reason to pick back up, not a harder pitch.",
    "MQL": "Timing matters more than content at this point — a well-timed, relevant nudge usually does more than a longer pitch would.",
    "SQL": "Going quiet for a stretch doesn't usually mean the interest is gone — it's more often a sign something else took priority for a while.",
    "Opportunity": "A quiet stretch on an active evaluation is worth a direct check-in before it turns into an actual stall.",
    "Customer": "Usage patterns already point to room to grow here — worth a direct conversation about it rather than waiting for a formal ask.",
}

# ---------------------------------------------------------------------------
# Layer 3: what THIS specific title cares about, and the TRACTIAN value tied
# to it. Keyed by exact title string (see knowledge_base.FUNCTIONAL_AREAS),
# so messaging differs within a functional area, not just across areas.
#   cares_about  — 1 sentence, what's actually on their plate day to day
#   value        — 1 clause, the specific TRACTIAN capability that helps
#   short_focus  — 3-6 words, used in the subject line and CTA
# ---------------------------------------------------------------------------
TITLE_FRAME = {
    # Reliability & Maintenance
    "Reliability Manager": {
        "cares_about": "building a proactive reliability program instead of reacting to the next breakdown",
        "value": "gives you condition data on every critical asset, so failures get caught before they hit the floor",
        "short_focus": "getting ahead of the next failure",
    },
    "Reliability Director": {
        "cares_about": "proving the reliability program is paying off across every site, not just the pilot plant",
        "value": "rolls asset health data up across sites, so you can show leadership where the program is actually cutting downtime",
        "short_focus": "proving reliability ROI across sites",
    },
    "Maintenance Manager": {
        "cares_about": "cutting down reactive work orders, improving PM compliance, and keeping the team ahead of recurring failures",
        "value": "flags developing issues early, so the team can convert reactive tickets into planned work instead of firefighting",
        "short_focus": "cutting down reactive work orders",
    },
    "Reliability Engineer": {
        "cares_about": "catching failure patterns early through condition data and root-cause work, not after-the-fact teardown reports",
        "value": "streams continuous vibration, temperature, and energy data per asset, so root cause is visible before the failure, not after it",
        "short_focus": "catching failure patterns earlier",
    },
    "Maintenance Planner": {
        "cares_about": "having enough lead time to actually plan work instead of getting blindsided by emergency orders",
        "value": "surfaces developing issues early enough that they land on the planned schedule instead of as an emergency work order",
        "short_focus": "getting ahead of emergency work orders",
    },
    # Plant Operations
    "Plant Manager": {
        "cares_about": "hitting production targets and not getting blindsided by equipment issues that were never on anyone's radar",
        "value": "gives you a live view of equipment health across the floor, so downtime risk shows up before it hits the schedule",
        "short_focus": "closing that visibility gap",
    },
    "Plant Engineer": {
        "cares_about": "keeping the line at rated throughput and tracking down the root cause of chronic downtime",
        "value": "pinpoints which specific assets are driving your downtime and production losses, down to the failure mode",
        "short_focus": "tracking down chronic downtime",
    },
    "Continuous Improvement Leader": {
        "cares_about": "finding the production losses that don't show up until someone digs into the data",
        "value": "connects equipment health data directly to OEE, so loss analysis doesn't rely on manual downtime logs",
        "short_focus": "finding hidden production losses",
    },
    # Executive / Economic Buyer
    "VP Operations": {
        "cares_about": "standardizing how every plant tracks reliability and turning that into one consistent, comparable metric",
        "value": "rolls plant-level reliability and OEE data into a single view, so performance is comparable across every site",
        "short_focus": "standardizing reliability across sites",
    },
    "COO": {
        "cares_about": "understanding where downtime is actually costing the business money across the network",
        "value": "quantifies downtime cost across every plant in one view, so it becomes a budget conversation instead of a plant-by-plant guess",
        "short_focus": "quantifying downtime cost network-wide",
    },
    "VP Engineering": {
        "cares_about": "getting ahead of asset failures before they turn into unplanned capital replacement decisions",
        "value": "surfaces asset condition trends, so failing equipment gets flagged before it becomes an unplanned capital expense",
        "short_focus": "avoiding surprise capital expense",
    },
    "Director of Manufacturing": {
        "cares_about": "hitting output targets without inheriting downtime surprises from sites that don't report reliability the same way",
        "value": "standardizes how every site reports asset health and downtime, so nothing gets lost between plants and headquarters",
        "short_focus": "standardizing reporting across plants",
    },
    "Head of Asset Management": {
        "cares_about": "extending asset life and basing repair-or-replace decisions on real condition data instead of a fixed schedule",
        "value": "tracks real condition data per asset, so repair-or-replace decisions are based on actual health, not a generic calendar",
        "short_focus": "moving to condition-based repair decisions",
    },
    # Digital Transformation / IT
    "CIO": {
        "cares_about": "making sure plant-floor systems actually integrate instead of becoming another disconnected point solution",
        "value": "acts as the data layer between plant-floor sensors and the systems of record you're already consolidating around",
        "short_focus": "avoiding another disconnected system",
    },
    "VP Digital Transformation": {
        "cares_about": "proving the digital initiative is producing real operational results, not just new dashboards",
        "value": "turns raw sensor data into OEE and reliability metrics leadership can see the impact of",
        "short_focus": "showing real operational results",
    },
    "Industry 4.0 Program Lead": {
        "cares_about": "connecting OT data across plants without a custom integration project for every site",
        "value": "deploys the same sensor and data layer across every plant, so there's no custom integration work per site",
        "short_focus": "connecting OT data across sites",
    },
}

DEFAULT_TITLE_FRAME = {
    "cares_about": "cutting unplanned downtime and getting better visibility into equipment health",
    "value": "gives your team real-time visibility into asset health, so issues get caught before they cause downtime",
    "short_focus": "cutting unplanned downtime",
}


def title_frame(title: str) -> dict:
    return TITLE_FRAME.get(title, DEFAULT_TITLE_FRAME)


# ---------------------------------------------------------------------------
# CTA experiment — a running A/B test on the email close, applied to every
# generated email regardless of persona/play. Each variant carries a "true"
# simulated reply rate (there's no real send/reply pipeline here, so outcomes
# are simulated at generation time against these rates) — the point is to
# demonstrate the hypothesis -> variant -> simulated-outcome -> results loop
# end to end, not to claim real engagement data. Aggregated per launched
# campaign at /reporting.
# ---------------------------------------------------------------------------
EMAIL_CTA_EXPERIMENT = {
    "name": "CTA Phrasing: Open Question vs. Concrete Ask",
    "hypothesis": (
        "On an already-warm account, a CTA that proposes a specific next step (a 15-minute "
        "call) will move faster than an open-ended question — they already have context on "
        "why we're reaching out, so the friction left to remove is deciding what to actually "
        "do about it, not whether to engage at all."
    ),
    "min_sample_per_variant": 20,
    "variants": {
        "A": {
            "label": "Open Question",
            "cta_template": "Curious whether {short_focus} is something you're actively working through right now?",
            "simulated_reply_rate": 0.08,
        },
        "B": {
            "label": "Concrete Ask",
            "cta_template": "Worth a 15-minute call this week to see whether {short_focus} is on your roadmap?",
            "simulated_reply_rate": 0.12,
        },
    },
}
