"""Mock reverse-ETL layer: pushes a qualified account's known contacts into
an external ad audience or nurture tool, tagged with the play driving the
push. No real Meta/HubSpot API calls happen anywhere in this file — every
"sync" is a row in audience_syncs, which the UI reads back to show what
would have happened. Auto-fires each sprint for accounts newly needing
action; manual per-account triggers are also available.
"""
from datetime import datetime

import db
from pipeline.ad_creative import assign_creative

SYNC_TYPES = {
    "meta_audience": "Meta Custom Audience",
    "hubspot_nurture": "HubSpot Nurture Sequence",
}


def known_contact_count(account_id: int) -> int:
    contacts = db.list_contacts_for_account(account_id)
    return sum(1 for c in contacts if c["is_known_contact"])


def record_sync(account_id: int, company_name: str, sync_type: str, triggered_by: str,
                 play: str = None, campaign_name: str = None) -> dict:
    count = known_contact_count(account_id)
    sync = {
        "account_id": account_id,
        "company_name": company_name,
        "sync_type": sync_type,
        "contact_count": count,
        "triggered_by": triggered_by,
        "play": play,
        "campaign_name": campaign_name,
        "synced_at": datetime.utcnow().isoformat(),
    }
    if sync_type == "meta_audience":
        sync.update(assign_creative(count))
    db.insert_audience_sync(sync)
    return {"contact_count": count, "sync_type": sync_type, "triggered_by": triggered_by}


def auto_sync_newly_qualified(today: datetime) -> int:
    """Called after each sprint. Any account currently needing action gets
    auto-enrolled on any channel it hasn't already been synced to — this is
    what makes the sprint scheduler actually run the loop end to end
    (mutate -> score -> enroll), not just re-score in the background."""
    from pipeline.plays import accounts_needing_action  # local import avoids a circular dependency with plays.py
    fired = 0
    for account in accounts_needing_action(today):
        for sync_type in SYNC_TYPES:
            if not db.has_synced(account["company_name"], sync_type):
                record_sync(account["id"], account["company_name"], sync_type, "automatic", play=account["play"])
                fired += 1
    return fired
