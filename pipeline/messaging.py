"""The outbound-copy hypothesis framework: signal -> operational implication
-> persona priority -> TRACTIAN value.

The point of every generated email/call-script/InMail is to answer one
question: "why does this specific person, at this specific account, need to
hear from us this week?" — a warm-account nudge, not a cold-outreach pitch.
That answer is assembled from four layers, each a lookup table below:

  1. SIGNAL_TRIGGER_VERB / SIGNAL_GERUND
     — how to state the actual trigger event in a natural sentence.
  2. SIGNAL_IMPLICATION
     — what that event typically means for the deal/account, independent of
       persona.
  3. TITLE_FRAME
     — what THIS specific title (not just functional area) actually cares
       about day to day, and the TRACTIAN value tied to that. Unchanged from
       persona to persona regardless of funnel stage — a Plant Manager cares
       about the same things whether they're a lead or a live deal.
  4. INDUSTRY_CHALLENGE / STAGE_FALLBACK_IMPLICATION
     — supporting texture: an industry-specific pain point, and a
       stage-appropriate fallback for accounts with no fresh signal at all.

content_generator.py assembles these into the actual copy; this file only
holds the domain content so the messaging logic can be read/edited on its
own, the same way knowledge_base.py holds the scoring domain.
"""

# ---------------------------------------------------------------------------
# Layer 1: how to state the trigger event itself, in plain sentences.
# SIGNAL_TRIGGER_VERB fits "{company} recently {verb}."
# SIGNAL_GERUND fits "...while also {gerund}."
# ---------------------------------------------------------------------------
SIGNAL_TRIGGER_VERB = {
    "usage_above_contracted_capacity": "started running above its contracted sensor capacity",
    "deal_stalled_in_stage": "stalled in its current deal stage",
    "single_threaded_opportunity": "settled into a single-threaded deal, with only one contact engaged",
    "champion_engagement_drop": "had its primary contact go quiet or change roles",
    "account_surge_score_threshold": "started showing a surge in buying-stage intent",
    "pricing_page_revisit_new_contact": "picked up a new contact browsing the pricing page",
    "intent_surge_category_keywords": "showed a spike in category research activity",
    "ad_engagement_spike": "had multiple contacts engage with our ads",
    "renewal_window_approaching": "moved into its contract renewal window",
    "reactivated_engagement": "had a dormant contact re-engage",
    "competitor_evaluation_activity": "started actively researching a competing solution",
    "company_expansion_event": "announced a new or expanding facility",
}

SIGNAL_GERUND = {
    "usage_above_contracted_capacity": "running above its contracted sensor capacity",
    "deal_stalled_in_stage": "stalling in its current deal stage",
    "single_threaded_opportunity": "showing only one engaged contact on the deal",
    "champion_engagement_drop": "losing engagement from its primary contact",
    "account_surge_score_threshold": "showing a surge in buying-stage intent",
    "pricing_page_revisit_new_contact": "picking up a new contact on the pricing page",
    "intent_surge_category_keywords": "showing a spike in category research",
    "ad_engagement_spike": "picking up ad engagement from multiple contacts",
    "renewal_window_approaching": "moving into its renewal window",
    "reactivated_engagement": "seeing a dormant contact re-engage",
    "competitor_evaluation_activity": "actively researching a competing solution",
    "company_expansion_event": "standing up a new or expanding facility",
}

# ---------------------------------------------------------------------------
# Layer 2: what the trigger typically means for the deal/account, persona-
# agnostic — grounded in real B2B sales/CS mechanics, not TOFU firmographics.
# ---------------------------------------------------------------------------
SIGNAL_IMPLICATION = {
    "usage_above_contracted_capacity": "When usage runs ahead of what's contracted, it's rarely a surprise to the account — they're already relying on more coverage than they're paying for, which makes the expansion conversation about formalizing reality, not proposing something new.",
    "deal_stalled_in_stage": "Deals that sit past the typical time in stage usually aren't dead, they're just missing a forcing function — a new stakeholder, a fresh proof point, or a deadline that makes inaction cost something.",
    "single_threaded_opportunity": "A deal riding on one relationship is one reassignment away from starting over. Widening the committee now is cheaper than rebuilding it after the champion leaves.",
    "champion_engagement_drop": "Losing your primary contact's engagement — whether they've gone quiet or moved roles — is usually the leading indicator of a stalled deal, not a lagging one.",
    "account_surge_score_threshold": "A surge that's both rising and spreading across the buying committee is a stronger signal than a single engaged browser — more than one person is now building a case internally.",
    "pricing_page_revisit_new_contact": "A net-new visitor on pricing content usually means someone was just looped in — often by the existing champion trying to build internal support.",
    "intent_surge_category_keywords": "Third-party research spikes on category terms tend to precede internal budget conversations, not follow them — the timing question is how soon, not if.",
    "ad_engagement_spike": "When more than one person at an account starts engaging with the same ads, it's usually because the topic came up internally, not coincidence.",
    "renewal_window_approaching": "Renewal conversations that arrive without an expansion angle already teed up tend to become pure price negotiations instead of growth conversations.",
    "reactivated_engagement": "A contact re-engaging after going quiet is a narrow window — whatever brought them back is fresh in their mind right now, and won't stay that way.",
    "competitor_evaluation_activity": "Active research on a competitor doesn't necessarily mean the deal is lost or the account is unhappy — it usually just means no one's made the case yet for why the alternative isn't actually better.",
    "company_expansion_event": "A new facility coming online means new equipment, new failure modes, and no reliability process in place yet — the easiest time to get ahead of downtime is before the line starts running, not after the first outage.",
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
    "Lead": "Leads that haven't shown fresh engagement usually just need a reason to re-open the conversation, not a harder pitch.",
    "MQL": "MQLs sitting quiet are often one relevant nudge away from moving — timing matters more than content at this stage.",
    "SQL": "SQLs without a fresh signal are usually still viable, just waiting on the next concrete reason to prioritize this over everything else on their plate.",
    "Opportunity": "An opportunity without a fresh signal is still a live deal — the absence of urgency is itself worth checking in on before it becomes a real stall.",
    "Customer": "A healthy account with no fresh signal doesn't need outreach right now — that's what the health gate is for.",
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
