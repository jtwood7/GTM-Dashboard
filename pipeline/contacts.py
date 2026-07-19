"""Generates and maintains an account's contacts. Unlike the discovery
build, contacts here are PERSISTENT — generated once per account, then left
alone except for two things: engagement-date refresh (contacts don't get
new names every sprint, that would be unrealistic) and surround-outreach
enrollment, which appends new contacts when a single-threaded opportunity
signal fires and a relevant functional area isn't represented yet.
"""
import random
import re

from pipeline.knowledge_base import FUNCTIONAL_AREAS, SIGNAL_LIBRARY

CONTACT_COUNT_RANGE = (3, 5)

# Known-contact rate rises with funnel stage — you simply know more real
# names the further a deal has progressed; a cold Lead is mostly inferred
# titles, a Customer is almost entirely named people.
KNOWN_CONTACT_RATE_BY_STAGE = {
    "Lead": (0.15, 0.30),
    "MQL": (0.20, 0.35),
    "SQL": (0.35, 0.55),
    "Opportunity": (0.45, 0.65),
    "Customer": (0.70, 0.90),
}

FIRST_NAMES = [
    "James", "Maria", "David", "Linda", "Robert", "Karen", "Michael", "Susan",
    "William", "Jessica", "Carlos", "Angela", "Thomas", "Patricia", "Daniel",
    "Nancy", "Kevin", "Laura", "Brian", "Michelle",
]
LAST_NAMES = [
    "Whitfield", "Marsh", "Nakamura", "Bianchi", "Okafor", "Sullivan",
    "Reyes", "Larsen", "Petrov", "Boone", "Delgado", "Fischer", "Hartley",
    "Osei", "Caldwell", "Novak", "Ferreira", "Mackenzie", "Abbott", "Duarte",
]


def _company_domain(company_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]", "", company_name.lower())
    return f"{slug or 'company'}.com"


def _relevant_functional_areas(signal_types: set) -> list:
    areas = set()
    for st in signal_types:
        areas |= set(SIGNAL_LIBRARY.get(st, {}).get("functional_areas", []))
    # Reliability & Maintenance are the usual day-to-day pain owners
    # regardless of which specific signal fired — keep as a baseline.
    areas.add("reliability_maintenance")
    if not areas:
        areas = {"reliability_maintenance", "plant_operations"}
    return list(areas)


def _generate_identity(company_name: str, is_known: bool, engaged: bool, today_str: str) -> dict:
    if not is_known:
        return {"contact_name": None, "contact_email": None, "linkedin_url": None, "last_engaged_date": None}
    first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
    slug = f"{first}-{last}".lower()
    domain = _company_domain(company_name)
    last_engaged = None
    if engaged:
        from datetime import datetime, timedelta
        days_ago = random.randint(0, 30)
        last_engaged = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    return {
        "contact_name": f"{first} {last}",
        "contact_email": f"{first.lower()}.{last.lower()}@{domain}",
        "linkedin_url": f"linkedin.com/in/placeholder-{slug}",
        "last_engaged_date": last_engaged,
    }


def generate_contacts(account: dict, signal_types: set, today_str: str) -> list:
    """Initial contact generation for a brand-new account — called once,
    when the account first enters the book."""
    relevant_areas = _relevant_functional_areas(signal_types)
    total = random.randint(*CONTACT_COUNT_RANGE)

    area_pool = list(relevant_areas)
    weights = [3 if a in ("reliability_maintenance", "executive_buyer") else 1 for a in area_pool]
    assignments = list(relevant_areas)
    while len(assignments) < total:
        assignments.append(random.choices(area_pool, weights=weights)[0])
    assignments = assignments[:total]

    known_range = KNOWN_CONTACT_RATE_BY_STAGE.get(account["lifecycle_stage"], (0.3, 0.5))

    contacts = []
    used_titles_per_area = {}
    for area_key in assignments:
        titles = FUNCTIONAL_AREAS[area_key]["titles"]
        used = used_titles_per_area.setdefault(area_key, set())
        available = [t for t in titles if t not in used] or titles
        title = random.choice(available)
        used.add(title)

        is_known = random.random() < random.uniform(*known_range)
        engaged = is_known and random.random() < 0.6
        identity = _generate_identity(account["company_name"], is_known, engaged, today_str)

        contacts.append({
            "functional_area": area_key,
            "title": title,
            "is_known_contact": is_known,
            **identity,
        })
    return contacts


def enroll_surround_outreach(account: dict, existing_contacts: list, signal_types: set, today_str: str) -> list:
    """When a single-threaded opportunity signal fires, widen the committee:
    find functional areas the signal set says are relevant but that aren't
    represented among the account's existing contacts yet, and generate new
    contacts to fill them — the auto-enrollment mechanic. Returns only the
    NEW contacts to insert; existing ones are untouched."""
    if "single_threaded_opportunity" not in signal_types:
        return []
    existing_areas = {c["functional_area"] for c in existing_contacts}
    relevant_areas = _relevant_functional_areas(signal_types)
    missing_areas = [a for a in relevant_areas if a not in existing_areas]
    if not missing_areas:
        return []

    known_range = KNOWN_CONTACT_RATE_BY_STAGE.get(account["lifecycle_stage"], (0.3, 0.5))
    new_contacts = []
    for area_key in missing_areas:
        title = random.choice(FUNCTIONAL_AREAS[area_key]["titles"])
        is_known = random.random() < random.uniform(*known_range)
        # Freshly enrolled — not yet engaged, that's the point of surrounding them.
        identity = _generate_identity(account["company_name"], is_known, engaged=False, today_str=today_str)
        new_contacts.append({
            "functional_area": area_key,
            "title": title,
            "is_known_contact": is_known,
            **identity,
        })
    return new_contacts


def engaged_count_from_contacts(contacts: list, today_str: str, max_age_days: int = 30) -> int:
    """In-memory equivalent of db.engaged_contact_count, for use before
    contacts are persisted (e.g. scoring a brand-new account within the same
    sprint it was created)."""
    from datetime import datetime
    today = datetime.strptime(today_str, "%Y-%m-%d")
    count = 0
    for c in contacts:
        if not c.get("last_engaged_date"):
            continue
        days_ago = (today - datetime.strptime(c["last_engaged_date"], "%Y-%m-%d")).days
        if 0 <= days_ago <= max_age_days:
            count += 1
    return count
