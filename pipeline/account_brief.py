"""Account brief: the tailored, customer-facing one-pager content the system
assembles for a specific account — the asset that would be rendered as a
branded PDF via Canva and attached to the outreach drafts for that account's
known contacts.

The content here is generated for real from the account's own fields
(industry, plant footprint, the signals driving it). In this demo the render
step (Canva Connect API) and the draft step (Gmail API) are represented by a
flow diagram rather than called live from the deployed app — but the exact
pipeline was run once for real against a real account; see ACCOUNT_BRIEF_DEMO
below for the resulting Canva asset and the note about the real Gmail drafts.
"""
from pipeline.messaging import INDUSTRY_CHALLENGE

# A real asset + real drafts this pipeline actually produced, run once against
# a real account (Ironclad Energy Partners, Oil & Gas, ~20 sites). The Canva
# link is a real, rendered one-pager; the four drafts are real Gmail drafts,
# one per known contact, each carrying that contact's tailored email plus this
# asset. Surfaced in the UI as proof the pipeline produces real output, not a
# mockup — kept as a static reference so it survives the demo DB resetting.
ACCOUNT_BRIEF_DEMO = {
    "account": "Ironclad Energy Partners",
    "industry": "Oil & Gas",
    "canva_view_url": "https://www.canva.com/d/3a8nbaC1TSamFRt",
    "drafts_created": 4,
    "draft_note": (
        "Four real Gmail drafts were created — one per known contact "
        "(Reliability Director, Reliability Engineer, Maintenance Manager, "
        "Maintenance Planner) — each carrying that contact's tailored email "
        "and a link to the asset above, ready to send."
    ),
}

# Industry-specific framing for the "challenge" and "why it fits" sections.
# Falls back to a generic manufacturing line when an industry isn't listed.
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


def _customer_industry(industry: str) -> str:
    return industry.replace(" (General)", "").lower()


def build_account_brief(account: dict, known_contact_count: int = 0) -> dict:
    company = account["company_name"]
    industry = account["industry"]
    industry_lower = _customer_industry(industry)
    plants = account.get("plant_count") or 0
    challenge_tail = INDUSTRY_CHALLENGE.get(industry, "unplanned downtime tends to hit hardest across mixed equipment fleets")
    fit = _INDUSTRY_FIT.get(industry, _INDUSTRY_FIT["Manufacturing (General)"])

    footprint = f"across roughly {plants} facilities" if plants and plants > 1 else "across the operation"

    return {
        "title": f"TRACTIAN for {company}",
        "subtitle": f"Condition intelligence tailored to {industry_lower}",
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
                    "TRACTIAN puts continuous condition monitoring on your critical assets — vibration, "
                    "temperature, and energy data per asset — paired with a modern CMMS and OEE analytics "
                    "in one platform. Developing issues surface early enough to land on the planned "
                    "schedule instead of as an emergency work order."
                ),
            },
            {
                "heading": f"Why it fits {industry_lower}",
                "body": (
                    f"Your environment means {fit}. TRACTIAN's sensors are built for it and deploy "
                    "without pulling equipment offline, so coverage expands without adding site visits "
                    "or downtime windows."
                ),
            },
            {
                "heading": "What the first 90 days look like",
                "body": (
                    "Weeks 1–2: sensors on the highest-criticality assets at a few priority sites, no "
                    "downtime required. Weeks 3–6: baseline set, the first developing-fault alerts start "
                    "converting reactive tickets into planned work. Weeks 7–12: coverage expands and "
                    "reliability data rolls into one cross-site view for leadership."
                ),
            },
        ],
        "known_contact_count": known_contact_count,
    }
