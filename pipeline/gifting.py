"""Gift-readiness scoring — momentum-triggered, frequency-capped. Real
Sendoso/Reachdesk best practice: gift AFTER a positive signal, never as a
cold opener, and never more than once per contact within the cap window.
Every eligibility check returns its reason, win or lose, so the logic is
never a black box in the UI.
"""
from datetime import datetime

import db
from pipeline.knowledge_base import (
    GIFT_FREQUENCY_CAP_DAYS,
    GIFT_MAX_CONTACT_ENGAGEMENT_AGE_DAYS,
    PLAYS,
)


def gift_eligibility(contact: dict, play_key: str, signal_types: set, today: datetime) -> tuple:
    """Returns (eligible: bool, reason: str)."""
    play = PLAYS[play_key]

    if not play.get("gifting_allowed"):
        return False, f"Gifting isn't used for {play['label']} — an unsolicited gift here reads as tone-deaf, not helpful."

    if play_key == "win_back_risk" and "reactivated_engagement" not in signal_types:
        return False, "Win-Back Risk gifting waits for a positive re-engagement signal first — it's never the opening move."

    if not contact.get("is_known_contact") or not contact.get("contact_name"):
        return False, "No known contact identified yet — nothing to send to."

    if not contact.get("last_engaged_date"):
        return False, "This contact hasn't engaged recently — gifting follows a positive interaction, it doesn't open one."

    days_since_engaged = (today - datetime.strptime(contact["last_engaged_date"], "%Y-%m-%d")).days
    if days_since_engaged > GIFT_MAX_CONTACT_ENGAGEMENT_AGE_DAYS:
        return False, (
            f"Last engaged {days_since_engaged} days ago — outside the "
            f"{GIFT_MAX_CONTACT_ENGAGEMENT_AGE_DAYS}-day momentum window."
        )

    last_gift = db.last_gift_for_contact(contact["id"]) if contact.get("id") else None
    if last_gift:
        days_since_gift = (today - datetime.strptime(last_gift["sent_at"][:10], "%Y-%m-%d")).days
        if days_since_gift < GIFT_FREQUENCY_CAP_DAYS:
            return False, (
                f"Already gifted {days_since_gift} days ago — inside the "
                f"{GIFT_FREQUENCY_CAP_DAYS}-day frequency cap that keeps this from reading as spam."
            )

    return True, f"Engaged {days_since_engaged} day(s) ago, no gift within the {GIFT_FREQUENCY_CAP_DAYS}-day cap, and {play['label']} allows gifting."


def record_gift(contact_id: int, account_id: int, play_key: str, gift_tier: str, gift_name: str, today: datetime):
    db.insert_gift(contact_id, account_id, play_key, gift_tier, gift_name, today.isoformat())
