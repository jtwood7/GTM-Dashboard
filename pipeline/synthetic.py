"""Generates the synthetic active book: ~50 accounts spread across the
HubSpot lifecycle (Lead through Customer), each carrying the deal or
customer-health/usage fields appropriate to its stage, plus the MOFU/BOFU
signal events that make some of them urgent this sprint. Every generated
number ties back to a real field on the account (days actually in stage,
actual sensor counts) rather than being fabricated independently at
signal-detail-writing time — see generate_signal_detail below.
"""
import random
from datetime import datetime, timedelta

from pipeline.knowledge_base import (
    DEAL_STAGES,
    ICP_INDUSTRIES,
    SIGNAL_LIBRARY,
    STAGE_BENCHMARK_DAYS,
    STAGE_SCOPE_ANY,
    STAGE_SCOPE_CUSTOMER,
    STAGE_SCOPE_OPPORTUNITY,
)

NAME_PREFIXES = [
    "Vantage", "Meridian", "Summit", "Ironclad", "Cornerstone", "Highland",
    "Redwood", "Anchor", "Granite", "Pioneer", "Sterling", "Bedrock",
    "Crestline", "Union", "Vector", "Atlas", "Beacon", "Cascade", "Frontier",
    "Harborview", "Keystone", "Lodestar", "Northgate", "Overland", "Pinnacle",
    "Ridgeline", "Sable", "Timberline", "Westfield", "Ashgrove",
]
NAME_SUFFIXES_BY_INDUSTRY = {
    "Automotive & Parts": ["Motors", "Drivetrain Systems", "Auto Components", "Powertrain Group"],
    "Food & Beverage": ["Foods", "Beverage Co.", "Provisions", "Dairy Group"],
    "Manufacturing (General)": ["Industries", "Manufacturing Co.", "Fabrication Group", "Works"],
    "Mining & Metals": ["Metals", "Mining Corp", "Ore & Alloy", "Resources"],
    "Chemicals": ["Chemical Co.", "Specialty Chemicals", "Compounds Inc."],
    "Oil & Gas": ["Energy Partners", "Petroleum Co.", "Midstream Group"],
    "Pulp & Paper": ["Paper Co.", "Pulp & Fiber", "Packaging Group"],
    "Consumer Goods": ["Consumer Brands", "Household Goods Co.", "Products Group"],
}
CITY_STATE = [
    ("Charlotte", "NC"), ("Toledo", "OH"), ("Detroit", "MI"), ("Houston", "TX"),
    ("Greenville", "SC"), ("Knoxville", "TN"), ("Indianapolis", "IN"),
    ("Rockford", "IL"), ("Allentown", "PA"), ("Green Bay", "WI"),
    ("Birmingham", "AL"), ("Louisville", "KY"), ("Springfield", "MO"),
    ("Cedar Rapids", "IA"), ("Duluth", "MN"), ("Lake Charles", "LA"),
    ("Tulsa", "OK"), ("Tucson", "AZ"), ("Fresno", "CA"), ("Akron", "OH"),
]

# Roughly funnel-shaped, but weighted toward the stages this tool actually
# acts on (Opportunity/Customer) rather than a pure top-heavy TOFU shape.
LIFECYCLE_WEIGHTS = {"Lead": 15, "MQL": 20, "SQL": 20, "Opportunity": 25, "Customer": 20}
ACTIVE_BOOK_SIZE = 50


def generate_company_name(industry: str, used_names: set) -> str:
    suffixes = NAME_SUFFIXES_BY_INDUSTRY.get(industry, ["Industries", "Group", "Co."])
    for _ in range(50):
        name = f"{random.choice(NAME_PREFIXES)} {random.choice(suffixes)}"
        if name not in used_names:
            used_names.add(name)
            return name
    name = f"{random.choice(NAME_PREFIXES)} {random.choice(suffixes)} {random.randint(2, 99)}"
    used_names.add(name)
    return name


def _random_lifecycle_stage() -> str:
    stages = list(LIFECYCLE_WEIGHTS.keys())
    weights = list(LIFECYCLE_WEIGHTS.values())
    return random.choices(stages, weights=weights)[0]


def generate_account(today: datetime, used_names: set) -> dict:
    industry = random.choice(ICP_INDUSTRIES)
    name = generate_company_name(industry, used_names)
    employee_count = random.choice([
        random.randint(150, 499), random.randint(500, 1500),
        random.randint(1500, 3000), random.randint(3000, 8000),
    ])
    plant_count = max(1, round(employee_count / random.randint(300, 900)))
    city, state = random.choice(CITY_STATE)
    stage = _random_lifecycle_stage()

    # Days already spent in the current stage — deliberately wide spread so
    # some accounts land well past benchmark (stalled) and most don't.
    benchmark = STAGE_BENCHMARK_DAYS.get(stage, 90)
    days_in_stage = random.choice([
        random.randint(0, benchmark),                      # on pace
        random.randint(benchmark, int(benchmark * 1.8)),    # a bit behind
        random.randint(int(benchmark * 1.8), benchmark * 3),  # stalled
    ]) if stage != "Customer" else random.randint(30, 720)
    stage_entered_date = (today - timedelta(days=days_in_stage)).strftime("%Y-%m-%d")

    account = {
        "company_name": name,
        "industry": industry,
        "employee_count": employee_count,
        "plant_count": plant_count,
        "hq_state": state,
        "hq_city": city,
        "lifecycle_stage": stage,
        "stage_entered_date": stage_entered_date,
        "owner": "[Assigned Rep]",
        "created_at": today.isoformat(),
    }

    if stage == "Opportunity":
        account["deal_stage"] = random.choice(DEAL_STAGES)
        account["deal_amount"] = round(plant_count * random.randint(15000, 30000), -3)
        account["close_date"] = (today + timedelta(days=random.randint(20, 120))).strftime("%Y-%m-%d")

    if stage == "Customer":
        plants_live = random.randint(1, plant_count)
        sensors_contracted = plants_live * random.randint(20, 80)
        # Assets identified as monitorable typically exceeds what's actually
        # instrumented — that gap is the in-site expansion axis.
        assets_identified = round(sensors_contracted / random.uniform(0.4, 0.9))
        # Most accounts sit at/under contracted capacity; a minority run hot,
        # which is exactly what should trigger the expansion signal.
        deployed_ratio = random.choice([random.uniform(0.5, 0.95), random.uniform(0.95, 1.25)])
        sensors_deployed = round(sensors_contracted * deployed_ratio)
        renewal_days_out = random.choice([
            random.randint(15, 75),    # near-term renewal window — deliberately common
            random.randint(76, 400),
        ])
        account.update({
            "plants_live": plants_live,
            "sensors_contracted": sensors_contracted,
            "assets_identified": assets_identified,
            "sensors_deployed": sensors_deployed,
            "renewal_date": (today + timedelta(days=renewal_days_out)).strftime("%Y-%m-%d"),
            "active_user_ratio": round(random.uniform(0.15, 0.95), 2),
            "alert_to_workorder_rate": round(random.uniform(0.2, 0.9), 2),
            "days_since_last_login": random.choice([random.randint(0, 10), random.randint(11, 45)]),
        })

    return account


def build_active_book(today: datetime, size: int = ACTIVE_BOOK_SIZE) -> list:
    used_names = set()
    return [generate_account(today, used_names) for _ in range(size)]


# ---------------------------------------------------------------------------
# signal generation — every detail string is computed FROM the account's own
# real fields (actual days in stage, actual sensor counts), not an
# independently-fabricated number, so the evidence is always traceable.
# ---------------------------------------------------------------------------
def _applicable_signal_types(account: dict) -> list:
    stage = account["lifecycle_stage"]
    types = []
    for signal_type, sdef in SIGNAL_LIBRARY.items():
        scope = sdef["stage_scope"]
        if scope == STAGE_SCOPE_ANY:
            types.append(signal_type)
        elif scope == STAGE_SCOPE_OPPORTUNITY and stage == "Opportunity":
            types.append(signal_type)
        elif scope == STAGE_SCOPE_CUSTOMER and stage == "Customer":
            types.append(signal_type)
    return types


def generate_signal_detail(signal_type: str, account: dict, today: datetime) -> str:
    if signal_type == "deal_stalled_in_stage":
        days_in_stage = (today - datetime.strptime(account["stage_entered_date"], "%Y-%m-%d")).days
        benchmark = STAGE_BENCHMARK_DAYS.get(account["lifecycle_stage"], 30)
        multiple = round(days_in_stage / benchmark, 1) if benchmark else 1.0
        stage_label = account.get("deal_stage") or account["lifecycle_stage"]
        return f"HubSpot/Salesforce shows {days_in_stage} days in {stage_label}, {multiple}x the typical time in stage."
    if signal_type == "single_threaded_opportunity":
        if account.get("deal_amount"):
            return f"CRM activity shows only one engaged contact on a ${account['deal_amount']:,.0f} opportunity."
        return "CRM activity shows only one engaged contact on this opportunity."
    if signal_type == "usage_above_contracted_capacity":
        contracted = account.get("sensors_contracted") or 1
        deployed = account.get("sensors_deployed") or 0
        over_pct = round(100 * (deployed / contracted - 1))
        return f"Segment product telemetry shows utilization {over_pct}% over contracted sensor capacity."
    if signal_type == "renewal_window_approaching":
        if account.get("renewal_date"):
            days_out = (datetime.strptime(account["renewal_date"], "%Y-%m-%d") - today).days
            return f"Salesforce shows contract renewal in {days_out} days."
        return "Salesforce shows contract renewal approaching."
    if signal_type == "champion_engagement_drop":
        return "LinkedIn shows the primary contact changed roles; HubSpot engagement has gone quiet."
    if signal_type == "account_surge_score_threshold":
        return "Demandbase surge score crossed the in-market threshold — intent rising and spreading across contacts."
    if signal_type == "pricing_page_revisit_new_contact":
        return "Segment shows a net-new contact at the account engaging with pricing/ROI content."
    if signal_type == "intent_surge_category_keywords":
        return "6sense shows a spike in third-party research on predictive maintenance and related category terms."
    if signal_type == "ad_engagement_spike":
        return "RollWorks reports multiple distinct contacts engaging with running ABM ads this week."
    if signal_type == "reactivated_engagement":
        return "HubSpot shows a previously dormant contact opened and clicked an email this week."
    if signal_type == "competitor_evaluation_activity":
        competitors = SIGNAL_LIBRARY[signal_type].get("mock_competitors", ["a competing vendor"])
        competitor = random.choice(competitors)
        return f"6sense shows third-party research activity on {competitor}, a competing vendor."
    if signal_type == "company_expansion_event":
        return "Demandbase flags a newly announced or expanding facility for this company."
    return "Signal detected."


def _random_detected_date(today: datetime, max_days_back: int = 30) -> str:
    """Shorter default lookback than the discovery build (90 days) — funnel
    signals go stale faster than company-event signals do."""
    return (today - timedelta(days=random.randint(0, max_days_back))).strftime("%Y-%m-%d")


def generate_signals_for_account(account: dict, today: datetime, min_n: int = 0, max_n: int = 3) -> list:
    applicable = _applicable_signal_types(account)
    if not applicable:
        return []
    n = random.choices(
        range(min_n, min(max_n, len(applicable)) + 1),
        weights=[35, 30, 20, 15][: min(max_n, len(applicable)) - min_n + 1],
    )[0]
    if n == 0:
        return []
    chosen = random.sample(applicable, k=n)
    signals = []
    for signal_type in chosen:
        sdef = SIGNAL_LIBRARY[signal_type]
        signals.append({
            "signal_type": signal_type,
            "detail": generate_signal_detail(signal_type, account, today),
            "source_type": sdef["source_type"],
            "source_tool": sdef["source_tool"],
            "source_url": None,  # internal CRM/platform data — nothing public to link to, by design
            "detected_date": _random_detected_date(today),
        })
    return signals
