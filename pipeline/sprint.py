"""Orchestrates one sprint: mutate the active book, score every account
live, and for whoever currently needs action — (re)generate their contacts'
outreach content (so it always reflects the current top signal, not a
stale one from a previous sprint), run surround-outreach enrollment where a
single-threaded opportunity signal fired, and auto-sync qualifying accounts
to their play's channels.
"""
import json
from datetime import datetime

import db
from pipeline import active_book, audience_sync, content_generator
from pipeline import contacts as contacts_module
from pipeline.plays import score_all_accounts


def _top_signal(decayed_signals: list):
    if not decayed_signals:
        return None
    return max(decayed_signals, key=lambda s: s["points_awarded"])


def _persist_content(contact_id: int, content: dict):
    db.update_contact_fields(contact_id, {
        "email_subject": content["email_subject"],
        "email_body": content["email_body"],
        "call_script_intro": content["call_script_intro"],
        "call_script_notes": json.dumps(content["call_script_notes"]),
        "linkedin_inmail": content["linkedin_inmail"],
        "gift_tier_low": json.dumps(content["gift_tier_low"]),
        "gift_tier_mid": json.dumps(content["gift_tier_mid"]),
        "gift_tier_high": json.dumps(content["gift_tier_high"]),
        "email_variant": content["email_variant"],
        "simulated_replied": 1 if content["simulated_replied"] else 0,
    })


def run_sprint(trigger_type: str, today: datetime = None, sprint_id: int = None) -> int:
    today = today or datetime.utcnow()
    today_str = today.strftime("%Y-%m-%d")
    if sprint_id is None:
        sprint_id = db.create_sprint(today.isoformat(), trigger_type)

    try:
        active_book.ensure_active_book()
        active_book.run_sprint_mutations(today)

        scored = score_all_accounts(today)
        needing_action = [a for a in scored if a["tier"] == "Needs Action Now"]
        content_mode = content_generator.content_mode()

        for account in needing_action:
            account_id = account["id"]
            signal_types = {s["signal_type"] for s in account["decayed_signals"]}
            top_signal = _top_signal(account["decayed_signals"])

            existing_contacts = db.list_contacts_for_account(account_id)
            new_contacts = contacts_module.enroll_surround_outreach(
                account, existing_contacts, signal_types, today_str
            )
            for c in new_contacts:
                db.insert_contact(account_id, c)

            all_contacts = db.list_contacts_for_account(account_id)
            for contact in all_contacts:
                # Refresh every sprint an account needs action — the whole
                # point of a cadenced sprint is keeping the pitch current
                # with whatever's actually true about the account right now.
                content = content_generator.generate_content(contact, account, top_signal, account["play"])
                _persist_content(contact["id"], content)

        fired = audience_sync.auto_sync_newly_qualified(today)
        db.complete_sprint(sprint_id, datetime.utcnow().isoformat(), len(needing_action), content_mode)
        return sprint_id
    except Exception as e:
        db.fail_sprint(sprint_id, datetime.utcnow().isoformat(), str(e))
        raise
