"""Account brief: the tailored, TRACTIAN-branded one-pager the system builds
for a specific account — the asset attached to that account's outreach.

Content is assembled from the account's own fields (industry, footprint, the
signals driving it) and always includes a real, industry-relevant TRACTIAN
customer case study with a link. Rendered as a branded one-pager by the app
(templates/onepager.html) and served per account.
"""
from pipeline.messaging import INDUSTRY_CHALLENGE

# Real TRACTIAN customer case studies, mapped to the closest ICP industry.
# Sourced from tractian.com/en/case-studies — real customers, real metrics,
# real links, so the asset always cites relevant proof for the account.
INDUSTRY_CASE_STUDY = {
    "Automotive & Parts": {
        "customer": "Pirelli",
        "result": "identified 77 developing failures and recorded zero unplanned breakdowns on monitored systems",
        "url": "https://tractian.com/en/case-studies/pirelli",
    },
    "Food & Beverage": {
        "customer": "Ingredion",
        "result": "avoided 168 hours of downtime and over $1M in production losses at a single plant",
        "url": "https://tractian.com/en/case-studies/ingredion",
    },
    "Manufacturing (General)": {
        "customer": "Whirlpool",
        "result": "saved over $1M and reached 95% monitoring coverage on critical assets",
        "url": "https://tractian.com/en/case-studies/whirlpool",
    },
    "Mining & Metals": {
        "customer": "Höganäs",
        "result": "boosted field performance across its metals operations with real-time digital asset access",
        "url": "https://tractian.com/en/case-studies/hoganas",
    },
    "Chemicals": {
        "customer": "ICL",
        "result": "increased OEE by 41% and recovered 400+ tons of production",
        "url": "https://tractian.com/en/case-studies/icl",
    },
    "Oil & Gas": {
        "customer": "ICL",
        "result": "increased OEE by 41% and recovered 400+ tons of production on process-critical rotating equipment",
        "url": "https://tractian.com/en/case-studies/icl",
    },
    "Pulp & Paper": {
        "customer": "ICL",
        "result": "increased OEE by 41% and recovered 400+ tons of continuous-process production",
        "url": "https://tractian.com/en/case-studies/icl",
    },
    "Consumer Goods": {
        "customer": "Whirlpool",
        "result": "saved over $1M and reached 95% monitoring coverage across its plants",
        "url": "https://tractian.com/en/case-studies/whirlpool",
    },
}
_DEFAULT_CASE_STUDY = INDUSTRY_CASE_STUDY["Manufacturing (General)"]

# How TRACTIAN fits each industry's specific reliability reality.
_INDUSTRY_FIT = {
    "Oil & Gas": "remote, harsh-environment rotating assets that are expensive to inspect manually and carry real safety weight when they fail",
    "Automotive & Parts": "just-in-time lines where a single unplanned stop cascades through the whole supply chain",
    "Food & Beverage": "sanitation-driven downtime windows that leave no room for surprise failures on packaging and process equipment",
    "Mining & Metals": "remote, heavy rotating equipment where a manual inspection round can't scale across the site",
    "Chemicals": "safety-critical rotating equipment where a failure carries outsized process and safety risk",
    "Pulp & Paper": "continuous-process lines where one failure stops the entire line, not just one machine",
    "Consumer Goods": "high-mix production lines where frequent changeovers stress equipment unevenly",
    "Manufacturing (General)": "mixed equipment fleets where unplanned downtime tends to hit hardest and least predictably",
}


def case_study_for(industry: str) -> dict:
    return INDUSTRY_CASE_STUDY.get(industry, _DEFAULT_CASE_STUDY)


def _customer_industry(industry: str) -> str:
    return industry.replace(" (General)", "").lower()


def build_account_brief(account: dict, known_contact_count: int = 0) -> dict:
    company = account["company_name"]
    industry = account["industry"]
    industry_lower = _customer_industry(industry)
    plants = account.get("plant_count") or 0
    challenge_tail = INDUSTRY_CHALLENGE.get(industry, "unplanned downtime tends to hit hardest across mixed equipment fleets")
    fit = _INDUSTRY_FIT.get(industry, _INDUSTRY_FIT["Manufacturing (General)"])
    case = case_study_for(industry)
    footprint = f"across roughly {plants} facilities" if plants and plants > 1 else "across the operation"

    return {
        "title": f"TRACTIAN for {company}",
        "subtitle": f"Condition intelligence for {industry_lower}",
        "sections": [
            {
                "heading": "The challenge, as it looks at your sites",
                "body": (
                    f"{company} runs critical equipment {footprint}. That's exactly where unplanned "
                    f"downtime hides — degradation on an asset nobody checks weekly doesn't announce "
                    f"itself until it fails. In {industry_lower}, {challenge_tail}, and manual inspection "
                    f"can't scale to catch it in time."
                ),
            },
            {
                "heading": "What TRACTIAN does",
                "body": (
                    "Continuous condition monitoring on your critical assets — vibration, temperature, and "
                    "energy data per asset — paired with a modern CMMS and OEE analytics in one platform. "
                    "Developing issues surface early enough to land on the planned schedule instead of as an "
                    "emergency work order."
                ),
            },
            {
                "heading": f"Why it fits {industry_lower}",
                "body": (
                    f"Your environment means {fit}. TRACTIAN's sensors are built for it and deploy without "
                    "pulling equipment offline, so coverage expands without adding site visits or downtime "
                    "windows."
                ),
            },
            {
                "heading": "The first 90 days",
                "body": (
                    "Weeks 1–2: sensors on the highest-criticality assets at a few priority sites, no "
                    "downtime required. Weeks 3–6: baseline set, the first developing-fault alerts start "
                    "converting reactive tickets into planned work. Weeks 7–12: coverage expands and "
                    "reliability data rolls into one cross-site view for leadership."
                ),
            },
        ],
        "case_study": case,
        "known_contact_count": known_contact_count,
    }
