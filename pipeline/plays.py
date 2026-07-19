"""Scores every account in the book live and groups whichever ones need
action right now by play — the plays-first dashboard's primary view. Real,
countable data throughout: no fabricated trend statistics, no cluster
invented after the fact.
"""
from datetime import datetime

import db
from pipeline.knowledge_base import ACTION_TIER_1_LABEL, PLAY_ORDER, PLAYS
from pipeline.scorer import score_account


def score_all_accounts(today: datetime = None) -> list:
    today = today or datetime.utcnow()
    today_str = today.strftime("%Y-%m-%d")
    results = []
    for account in db.list_accounts():
        raw_signals = db.list_signals_for_account(account["id"])
        engaged = db.engaged_contact_count(account["id"], today_str)
        scored = score_account(account, raw_signals, engaged, today)
        results.append({**account, **scored})
    return results


def accounts_needing_action(today: datetime = None) -> list:
    return [a for a in score_all_accounts(today) if a["tier"] == ACTION_TIER_1_LABEL]


def play_groups(today: datetime = None) -> list:
    today = today or datetime.utcnow()
    needing_action = accounts_needing_action(today)
    total = len(needing_action)
    if total == 0:
        return []

    groups = {}
    for a in needing_action:
        groups.setdefault(a["play"], []).append(a)

    result = []
    for play_key in PLAY_ORDER:
        accounts = groups.get(play_key)
        if not accounts:
            continue
        pdef = PLAYS[play_key]
        known_contacts_total = 0
        for a in accounts:
            contacts = db.list_contacts_for_account(a["id"])
            a["known_contacts"] = sum(1 for c in contacts if c["is_known_contact"])
            known_contacts_total += a["known_contacts"]
        result.append({
            "play": play_key,
            "label": pdef["label"],
            "angle": pdef["angle"],
            "tactical_mix": pdef["tactical_mix"],
            "gifting_allowed": pdef["gifting_allowed"],
            "how_signals_work": pdef["how_signals_work"],
            "connections_required": pdef["connections_required"],
            "launch_explainer": pdef["launch_explainer"],
            "count": len(accounts),
            "pct_of_needing_action": round(100 * len(accounts) / total, 1),
            "accounts": accounts,
            "known_contacts_total": known_contacts_total,
        })
    result.sort(key=lambda p: p["count"], reverse=True)
    return result
