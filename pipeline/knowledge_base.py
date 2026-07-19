"""
TRACTIAN Funnel Intelligence knowledge base.

This is the MOFU/BOFU counterpart to the TOFU discovery demo: instead of
scoring whether an unknown company is worth targeting, everything here
answers "why does this account — already in the CRM — need action this
week?" Signals are sourced from the real GTM stack this role owns (6sense,
RollWorks, Demandbase, Segment, HubSpot, Salesforce), and the four "plays"
are fixed tactical buckets: an account's play determines the constant
channel mix, while messaging.py determines what's actually said, driven by
that account's specific signals.
"""

# ---------------------------------------------------------------------------
# ICP INDUSTRIES — unchanged from the discovery build; still the firmographic
# lens every account gets viewed through, regardless of funnel stage.
# ---------------------------------------------------------------------------
ICP_INDUSTRIES_TIER_A = [
    "Automotive & Parts",
    "Food & Beverage",
    "Manufacturing (General)",
    "Mining & Metals",
]
ICP_INDUSTRIES_TIER_B = [
    "Chemicals",
    "Oil & Gas",
    "Pulp & Paper",
    "Consumer Goods",
]
ICP_INDUSTRIES = ICP_INDUSTRIES_TIER_A + ICP_INDUSTRIES_TIER_B

US_STATES_SAMPLE = [
    "OH", "MI", "TX", "GA", "NC", "SC", "TN", "IN", "IL", "PA",
    "WI", "AL", "KY", "MO", "IA", "MN", "LA", "OK", "AZ", "CA",
]

# ---------------------------------------------------------------------------
# FUNCTIONAL AREAS — the buying-committee roles. Unchanged: these are the
# same people who matter whether an account is a cold prospect or a live
# deal — what changes is why we're reaching out to them.
# ---------------------------------------------------------------------------
FUNCTIONAL_AREAS = {
    "reliability_maintenance": {
        "label": "Reliability & Maintenance",
        "titles": [
            "Reliability Manager",
            "Reliability Director",
            "Maintenance Manager",
            "Reliability Engineer",
            "Maintenance Planner",
        ],
    },
    "plant_operations": {
        "label": "Plant Operations",
        "titles": [
            "Plant Manager",
            "Plant Engineer",
            "Continuous Improvement Leader",
        ],
    },
    "executive_buyer": {
        "label": "Executive / Economic Buyer",
        "titles": [
            "VP Operations",
            "COO",
            "VP Engineering",
            "Director of Manufacturing",
            "Head of Asset Management",
        ],
    },
    "digital_transformation": {
        "label": "Digital Transformation / IT",
        "titles": [
            "CIO",
            "VP Digital Transformation",
            "Industry 4.0 Program Lead",
        ],
    },
}

# ---------------------------------------------------------------------------
# LIFECYCLE — HubSpot's standard lifecycle stage field, since HubSpot is the
# backbone of this stack. MOFU = Lead through SQL, BOFU = Opportunity through
# Customer (and the post-sale expansion motion lives inside Customer).
# ---------------------------------------------------------------------------
LIFECYCLE_STAGES = ["Lead", "MQL", "SQL", "Opportunity", "Customer"]

# Typical days an account should spend in a stage before it's a velocity
# concern. No benchmark for Customer — that stage is scored on health +
# expansion opportunity instead of stage risk (see scorer.py).
STAGE_BENCHMARK_DAYS = {
    "Lead": 14,
    "MQL": 14,
    "SQL": 21,
    "Opportunity": 45,
}

DEAL_STAGES = ["Discovery", "Technical Validation", "Proposal", "Negotiation"]

# ---------------------------------------------------------------------------
# SIGNAL LIBRARY — 10 signal types, each tagged with the real tool that would
# plausibly surface it. points = base value out of 100 before recency decay.
# stage_scope controls which lifecycle stages a signal can fire for.
# ---------------------------------------------------------------------------
STAGE_SCOPE_ANY = "any"
STAGE_SCOPE_OPPORTUNITY = "opportunity_only"
STAGE_SCOPE_CUSTOMER = "customer_only"

SIGNAL_LIBRARY = {
    "usage_above_contracted_capacity": {
        "label": "Usage Above Contracted Capacity",
        "points": 93,
        "source_tool": "Segment (product telemetry)",
        "source_type": "intent_data",
        "stage_scope": STAGE_SCOPE_CUSTOMER,
        "functional_areas": ["executive_buyer", "reliability_maintenance"],
        "angle": "They're already using more than they're licensed for — the expansion conversation is overdue, not speculative.",
    },
    "deal_stalled_in_stage": {
        "label": "Deal Stalled In Stage",
        "points": 90,
        "source_tool": "HubSpot / Salesforce",
        "source_type": "crm_activity",
        "stage_scope": STAGE_SCOPE_OPPORTUNITY,
        "functional_areas": ["executive_buyer", "plant_operations"],
        "angle": "This deal has been sitting well past the typical time in stage — needs a deliberate push, not another passive check-in.",
    },
    "single_threaded_opportunity": {
        "label": "Single-Threaded Opportunity",
        "points": 88,
        "source_tool": "HubSpot / Salesforce",
        "source_type": "crm_activity",
        "stage_scope": STAGE_SCOPE_OPPORTUNITY,
        "functional_areas": ["reliability_maintenance", "plant_operations", "executive_buyer"],
        "angle": "Only one person is engaged on a deal this size — a single departure or reassignment could kill it. Widen the committee now.",
    },
    "champion_engagement_drop": {
        "label": "Champion Engagement Drop / Job Change",
        "points": 87,
        "source_tool": "HubSpot + LinkedIn",
        "source_type": "linkedin_update",
        "stage_scope": STAGE_SCOPE_ANY,
        "functional_areas": ["reliability_maintenance", "plant_operations"],
        "angle": "The primary relationship went quiet or changed roles — re-anchor to a new champion before the deal goes cold.",
    },
    "account_surge_score_threshold": {
        "label": "Account Surge Score Crossed Threshold",
        "points": 84,
        "source_tool": "Demandbase",
        "source_type": "intent_data",
        "stage_scope": STAGE_SCOPE_ANY,
        "functional_areas": ["executive_buyer", "digital_transformation"],
        "angle": "Buying-stage intent is both rising and spreading across more of the buying committee, not just one person browsing.",
    },
    "pricing_page_revisit_new_contact": {
        "label": "Pricing Page Revisit by New Contact",
        "points": 82,
        "source_tool": "Segment",
        "source_type": "intent_data",
        "stage_scope": STAGE_SCOPE_ANY,
        "functional_areas": ["executive_buyer", "plant_operations"],
        "angle": "Someone new at the account just looked at pricing — the buying committee is widening on its own; help it along.",
    },
    "intent_surge_category_keywords": {
        "label": "Intent Surge on Category Keywords",
        "points": 81,
        "source_tool": "6sense",
        "source_type": "intent_data",
        "stage_scope": STAGE_SCOPE_ANY,
        "functional_areas": ["reliability_maintenance", "digital_transformation"],
        "angle": "Third-party research on relevant category terms just spiked — reinforces that the timing question isn't 'if', it's 'how soon.'",
    },
    "ad_engagement_spike": {
        "label": "Ad Engagement Spike",
        "points": 80,
        "source_tool": "RollWorks",
        "source_type": "intent_data",
        "stage_scope": STAGE_SCOPE_ANY,
        "functional_areas": ["plant_operations", "digital_transformation"],
        "angle": "Multiple people at the account are engaging with running ads — the audience is paying attention, worth a direct follow-up.",
    },
    "renewal_window_approaching": {
        "label": "Renewal Window Approaching",
        "points": 79,
        "source_tool": "Salesforce",
        "source_type": "crm_activity",
        "stage_scope": STAGE_SCOPE_CUSTOMER,
        "functional_areas": ["executive_buyer"],
        "angle": "Renewal is close enough that an expansion conversation should be bundled into it, not raised separately later.",
    },
    "reactivated_engagement": {
        "label": "Reactivated Engagement",
        "points": 76,
        "source_tool": "HubSpot",
        "source_type": "crm_activity",
        "stage_scope": STAGE_SCOPE_ANY,
        "functional_areas": ["reliability_maintenance", "plant_operations"],
        "angle": "A contact who'd gone quiet just engaged again — the window to re-open the conversation is now, before it closes again.",
    },
    "competitor_evaluation_activity": {
        "label": "Competitor Evaluation Activity",
        "points": 85,
        "source_tool": "6sense",
        "source_type": "intent_data",
        "stage_scope": STAGE_SCOPE_ANY,
        "functional_areas": ["reliability_maintenance", "executive_buyer"],
        "angle": "Active competitive evaluation alongside an open deal — or inside an existing account — usually means the current approach isn't locked in yet, or isn't sticking. This is displacement messaging, not education.",
        "mock_competitors": ["Fiix", "MaintainX", "UpKeep", "Augury", "Limble", "AssetWatch"],
    },
    "company_expansion_event": {
        "label": "Company Facility Expansion Announced",
        "points": 88,
        "source_tool": "Demandbase",
        "source_type": "intent_data",
        "stage_scope": STAGE_SCOPE_ANY,
        "functional_areas": ["executive_buyer", "plant_operations"],
        "angle": "New capacity creates new downtime risk before the reliability processes that keep it running are in place — for an open deal that's a natural deadline, for an existing customer it's a clean second-site expansion conversation.",
    },
}

SOURCE_TYPE_LABELS = {
    "intent_data": "Intent Data",
    "crm_activity": "CRM Activity",
    "linkedin_update": "LinkedIn Update",
}


def decay_multiplier(days_old: int) -> float:
    """Same recency decay as the discovery build: full value inside 30 days,
    80% at 31-60, 60% at 61-90, excluded past 90 — signals go stale fast in a
    fast-moving funnel."""
    if days_old <= 30:
        return 1.0
    if days_old <= 60:
        return 0.8
    if days_old <= 90:
        return 0.6
    return 0.0


# ---------------------------------------------------------------------------
# PLAYS — fixed tactical buckets. Every account in a play gets the same
# channel mix; messaging.py drives what's actually said, informed by that
# account's specific signals. Whichever play's driving signals contribute
# the most decayed points wins; ties break toward the play listed first.
# ---------------------------------------------------------------------------
PLAYS = {
    "velocity_rescue": {
        "label": "Velocity Rescue",
        "driving_signals": [
            "deal_stalled_in_stage", "single_threaded_opportunity",
            "competitor_evaluation_activity", "company_expansion_event",
        ],
        "angle": "the deal has stalled or is under-threaded — get it moving again",
        "tactical_mix": ["SDR outreach nudge", "Urgency email sequence", "Surround outreach if single-threaded"],
        "gifting_allowed": False,  # an unsolicited gift on a stalled deal reads as tone-deaf, not helpful
        "how_signals_work": (
            "Deal Stalled In Stage comes from HubSpot/Salesforce deal-stage data — comparing how long an "
            "opportunity has sat in its current stage against a typical benchmark for that stage. "
            "Single-Threaded Opportunity comes from the same CRM activity data — counting how many distinct "
            "contacts have actually engaged with the deal in the last 30 days; one or fewer trips this signal. "
            "Competitor Evaluation Activity comes from 6sense intent data — third-party research activity on "
            "a competitor's name or category, a sign the deal isn't locked in yet. Company Facility Expansion "
            "Announced comes from Demandbase firmographic/trigger-event data — new capacity coming online "
            "gives a stalled deal a natural deadline."
        ),
        "connections_required": ["HubSpot", "Salesforce", "6sense", "Demandbase"],
        "launch_explainer": (
            "Pushes every account in this group into a HubSpot nurture sequence themed around urgency and "
            "re-engagement — no paid ad spend here, this is a sales-led rescue, not an awareness play. For "
            "accounts flagged single-threaded, it also auto-enrolls any missing buying-committee contacts "
            "into a synchronized outreach wave."
        ),
        "ads_involved": False,
    },
    "buying_committee_expanding": {
        "label": "Buying Committee Expanding",
        "driving_signals": ["ad_engagement_spike", "pricing_page_revisit_new_contact", "account_surge_score_threshold"],
        "angle": "engagement is broadening across the buying committee — capitalize on the momentum",
        "tactical_mix": ["Expanded ad audience", "Multi-thread intro email", "Introduction gift for newly engaged contacts"],
        "gifting_allowed": True,
        "ads_involved": True,
        "ad_angle": (
            "The only play that spends on paid — the goal is awareness across a widening committee, not a "
            "single conversion, so the creative stays broad (downtime cost, before/after reliability, "
            "customer proof) rather than persona-specific. Same three creatives run for every account in "
            "this group; see Ad Creative Performance in Reporting for which one's actually winning."
        ),
        "how_signals_work": (
            "Ad Engagement Spike comes from RollWorks — how many distinct contacts at the account are "
            "engaging with running ABM ads. Pricing Page Revisit comes from Segment's first-party behavioral "
            "tracking — a net-new visitor (not previously tracked) engaging with pricing/ROI content. Account "
            "Surge Score comes from Demandbase, combining topic relevance, intent velocity, and how many "
            "distinct contacts are showing it — not just one person browsing."
        ),
        "connections_required": ["RollWorks", "Segment", "Demandbase"],
        "launch_explainer": (
            "Pushes the group into an expanded ad audience and a multi-thread intro email sequence, and "
            "flags newly-engaged contacts as eligible for an introduction gift."
        ),
    },
    "renewal_expansion": {
        "label": "Renewal & Expansion",
        "driving_signals": [
            "usage_above_contracted_capacity", "renewal_window_approaching",
            "intent_surge_category_keywords", "company_expansion_event",
        ],
        "angle": "usage and timing point to an expansion or renewal conversation",
        "tactical_mix": ["Email", "Milestone/relationship gifting", "AE-led business review ask"],
        "gifting_allowed": True,
        "how_signals_work": (
            "Usage Above Contracted Capacity comes from Segment product telemetry — comparing sensors "
            "actively reporting against sensors contracted. Renewal Window Approaching comes from Salesforce "
            "contract data. Intent Surge on Category Keywords comes from 6sense — third-party research "
            "activity on relevant category terms, independent of anything happening inside the account. "
            "Company Facility Expansion Announced comes from Demandbase firmographic/trigger-event data — a "
            "new or expanding site is a clean, low-pressure opening for a second-site expansion conversation."
        ),
        "connections_required": ["Segment", "Salesforce", "6sense", "Demandbase"],
        "launch_explainer": (
            "Pushes the group into an email sequence and flags contacts for milestone/relationship gifting, "
            "positioning the renewal conversation as an expansion conversation rather than a pure "
            "price negotiation."
        ),
        "ads_involved": False,
    },
    "win_back_risk": {
        "label": "Win-Back Risk",
        "driving_signals": ["champion_engagement_drop", "reactivated_engagement", "competitor_evaluation_activity"],
        "angle": "a key relationship weakened or engagement went cold — re-engage before it's lost",
        "tactical_mix": ["Personal outreach", "Re-engagement email", "Gift only after a positive re-engagement touch"],
        "gifting_allowed": True,  # gated further in gifting.py — never the opening move here
        "how_signals_work": (
            "Champion Engagement Drop comes from HubSpot engagement data cross-referenced with LinkedIn — "
            "detecting when a primary contact goes quiet or changes roles. Reactivated Engagement comes from "
            "HubSpot email engagement — a previously dormant contact opening or clicking again. Competitor "
            "Evaluation Activity comes from 6sense intent data — an existing customer researching a "
            "competitor is a churn-risk signal on its own. Customer accounts that fail the health gate (see "
            "Customer Health & Usage on their account page) are also force-routed here regardless of which "
            "signals fired."
        ),
        "connections_required": ["HubSpot", "LinkedIn", "6sense"],
        "launch_explainer": (
            "Pushes the group into personal outreach and a re-engagement email sequence. Gifting stays off "
            "until a contact shows an actual positive re-engagement signal first — never the opening move."
        ),
        "ads_involved": False,
    },
}
PLAY_ORDER = ["velocity_rescue", "buying_committee_expanding", "renewal_expansion", "win_back_risk"]

# ---------------------------------------------------------------------------
# SCORING MODEL — Action Score = STAGE_RISK/EXPANSION_OPPORTUNITY (0-40) +
# THREADING_HEALTH (0-20) + SIGNAL_URGENCY (0-40). Named sub-components on
# purpose, same as the discovery build, so any one weight can be pointed to
# and explained out loud.
# ---------------------------------------------------------------------------
STAGE_RISK_MAX = 40
THREADING_HEALTH_MAX = 20
SIGNAL_URGENCY_MAX = 40


def score_stage_risk(days_in_stage: int, lifecycle_stage: str) -> int:
    """Non-Customer stages only — how far past the typical time-in-stage
    this account is. Customer-stage accounts use score_expansion_opportunity
    instead (see scorer.py); there's no 'stalled' framing for a signed deal."""
    benchmark = STAGE_BENCHMARK_DAYS.get(lifecycle_stage, 30)
    ratio = days_in_stage / benchmark if benchmark else 1.0
    if ratio >= 2.0:
        return 40
    if ratio >= 1.5:
        return 28
    if ratio >= 1.0:
        return 16
    return 6


def score_threading_health(engaged_contact_count: int) -> int:
    """Fewer engaged contacts = higher urgency contribution (mirrors the old
    MATURITY_GAP logic: the bigger the gap, the more points)."""
    if engaged_contact_count <= 1:
        return 20
    if engaged_contact_count == 2:
        return 12
    return 4


# ---------------------------------------------------------------------------
# CUSTOMER HEALTH GATE — best practice (Gainsight/Totango-style): don't score
# an expansion opportunity on an unhealthy account. If the gate fails, the
# account gets force-routed to Win-Back Risk regardless of expansion signals.
# ---------------------------------------------------------------------------
HEALTH_GATE_MIN_ACTIVE_USER_RATIO = 0.4
HEALTH_GATE_MIN_ALERT_CONVERSION_RATE = 0.5
HEALTH_GATE_MAX_DAYS_SINCE_LOGIN = 21


def passes_health_gate(active_user_ratio: float, alert_to_workorder_rate: float, days_since_last_login: int) -> bool:
    return (
        active_user_ratio >= HEALTH_GATE_MIN_ACTIVE_USER_RATIO
        and alert_to_workorder_rate >= HEALTH_GATE_MIN_ALERT_CONVERSION_RATE
        and days_since_last_login <= HEALTH_GATE_MAX_DAYS_SINCE_LOGIN
    )


def score_expansion_opportunity(plants_live: int, plants_known: int, sensors_deployed: int,
                                 assets_identified: int, usage_vs_contracted_ratio: float) -> int:
    """Customer-stage only, and only meaningful once passes_health_gate() is
    True. Two independent expansion axes (site coverage, in-site density)
    plus a direct over-capacity flag — 'land and expand' made concrete."""
    coverage_ratio = plants_live / plants_known if plants_known else 1.0
    density_ratio = sensors_deployed / assets_identified if assets_identified else 1.0

    score = 0
    if coverage_ratio < 0.5:
        score += 18
    elif coverage_ratio < 0.8:
        score += 10
    else:
        score += 3

    if density_ratio < 0.6:
        score += 12
    elif density_ratio < 0.85:
        score += 6
    else:
        score += 2

    if usage_vs_contracted_ratio > 1.0:
        score += 10

    return min(STAGE_RISK_MAX, score)


# ---------------------------------------------------------------------------
# ACTION TIERS
# ---------------------------------------------------------------------------
ACTION_TIER_1_THRESHOLD = 75
ACTION_TIER_2_THRESHOLD = 45

ACTION_TIER_1_LABEL = "Needs Action Now"
ACTION_TIER_2_LABEL = "Monitor"
ACTION_TIER_3_LABEL = "Healthy"


def action_tier_for_score(total_score: float) -> str:
    if total_score >= ACTION_TIER_1_THRESHOLD:
        return ACTION_TIER_1_LABEL
    if total_score >= ACTION_TIER_2_THRESHOLD:
        return ACTION_TIER_2_LABEL
    return ACTION_TIER_3_LABEL


# ---------------------------------------------------------------------------
# GIFTING — momentum-triggered, frequency-capped. Real Sendoso/Reachdesk
# best practice: gift AFTER a positive signal, never as a cold opener, and
# never more than once per contact within the cap window.
# ---------------------------------------------------------------------------
GIFT_TIERS = ["<$35", "$36-$85", "$86-$150"]
GIFT_FREQUENCY_CAP_DAYS = 120
GIFT_MAX_CONTACT_ENGAGEMENT_AGE_DAYS = 30

ANTHROPIC_MODEL = "claude-sonnet-5"
