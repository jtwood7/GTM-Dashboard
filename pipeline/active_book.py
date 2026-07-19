"""Maintains the persistent active book and mutates it each sprint: some
accounts advance a lifecycle stage, customer usage/health drifts slightly,
and a handful of fresh signals get injected across the book — simulating a
living CRM, not a fresh discovery pass every time.
"""
import random
from datetime import datetime, timedelta

import db
from pipeline import contacts as contacts_module
from pipeline import synthetic
from pipeline.knowledge_base import DEAL_STAGES, LIFECYCLE_STAGES

STAGE_ADVANCE_PROBABILITY = 0.15
NEW_SIGNALS_PER_SPRINT_RANGE = (3, 8)


def ensure_active_book():
    if not db.accounts_is_empty():
        return
    today = datetime.utcnow()
    today_str = today.strftime("%Y-%m-%d")
    accounts = synthetic.build_active_book(today)
    for account in accounts:
        account_id = db.insert_account(account)
        initial_signals = synthetic.generate_signals_for_account(account, today, min_n=0, max_n=2)
        signal_types = set()
        for sig in initial_signals:
            db.insert_signal(account_id, sig)
            signal_types.add(sig["signal_type"])
        for c in contacts_module.generate_contacts(account, signal_types, today_str):
            db.insert_contact(account_id, c)


def _maybe_advance_stage(account: dict, today: datetime):
    stage = account["lifecycle_stage"]
    if stage == "Customer":
        return
    idx = LIFECYCLE_STAGES.index(stage)
    if idx >= len(LIFECYCLE_STAGES) - 1 or random.random() >= STAGE_ADVANCE_PROBABILITY:
        return
    new_stage = LIFECYCLE_STAGES[idx + 1]
    fields = {"lifecycle_stage": new_stage, "stage_entered_date": today.strftime("%Y-%m-%d")}
    if new_stage == "Opportunity":
        fields["deal_stage"] = DEAL_STAGES[0]
        fields["deal_amount"] = round(account["plant_count"] * random.randint(15000, 30000), -3)
        fields["close_date"] = (today + timedelta(days=random.randint(30, 120))).strftime("%Y-%m-%d")
    if new_stage == "Customer":
        plants_live = random.randint(1, account["plant_count"])
        sensors_contracted = plants_live * random.randint(20, 80)
        assets_identified = round(sensors_contracted / random.uniform(0.4, 0.9))
        fields.update({
            "plants_live": plants_live,
            "sensors_contracted": sensors_contracted,
            "assets_identified": assets_identified,
            "sensors_deployed": round(sensors_contracted * random.uniform(0.6, 0.95)),
            "renewal_date": (today + timedelta(days=365)).strftime("%Y-%m-%d"),
            "active_user_ratio": round(random.uniform(0.4, 0.9), 2),
            "alert_to_workorder_rate": round(random.uniform(0.4, 0.85), 2),
            "days_since_last_login": random.randint(0, 10),
        })
    db.update_account_fields(account["id"], fields)


def _drift_customer_usage(account: dict):
    """Small realistic movement sprint over sprint — adoption creeping up
    (or occasionally down), not a full regeneration."""
    if account["lifecycle_stage"] != "Customer":
        return
    fields = {}
    if account.get("sensors_deployed") is not None and random.random() < 0.4:
        fields["sensors_deployed"] = max(0, account["sensors_deployed"] + random.randint(-2, 6))
    if random.random() < 0.3:
        fields["days_since_last_login"] = random.choice([random.randint(0, 10), random.randint(11, 45)])
    if fields:
        db.update_account_fields(account["id"], fields)


def run_sprint_mutations(today: datetime):
    accounts = db.list_accounts()
    for account in accounts:
        _maybe_advance_stage(account, today)
        _drift_customer_usage(account)

    accounts = db.list_accounts()  # re-fetch: stage may have changed, affects which signals apply
    n_new = random.randint(*NEW_SIGNALS_PER_SPRINT_RANGE)
    for _ in range(n_new):
        account = random.choice(accounts)
        new_sigs = synthetic.generate_signals_for_account(account, today, min_n=1, max_n=1)
        if new_sigs:
            sig = new_sigs[0]
            sig["detected_date"] = today.strftime("%Y-%m-%d")
            db.insert_signal(account["id"], sig)
