"""Cumulative growth metrics for the dashboard — every number is a direct
computation over real per-account fields (deal_amount, health-gate status,
days in stage), nothing estimated or multiplied-up after the fact.
"""
from datetime import datetime

import db
from pipeline.plays import score_all_accounts


def compute(today: datetime = None) -> dict:
    today = today or datetime.utcnow()
    scored = score_all_accounts(today)

    needing_action = [a for a in scored if a["tier"] == "Needs Action Now"]

    opportunities = [a for a in scored if a["lifecycle_stage"] == "Opportunity"]
    pipeline_value_in_motion = sum(a["deal_amount"] for a in opportunities if a.get("deal_amount"))

    customers = [a for a in scored if a["lifecycle_stage"] == "Customer"]
    healthy_customers = [a for a in customers if a.get("health_gate_passed")]
    customer_health_rate = round(100 * len(healthy_customers) / len(customers), 1) if customers else None

    mofu_stages = ("Lead", "MQL", "SQL", "Opportunity")
    mofu_accounts = [a for a in scored if a["lifecycle_stage"] in mofu_stages]
    if mofu_accounts:
        avg_days_in_stage = round(
            sum((today - datetime.strptime(a["stage_entered_date"], "%Y-%m-%d")).days for a in mofu_accounts)
            / len(mofu_accounts), 1,
        )
    else:
        avg_days_in_stage = None

    return {
        "needing_action_count": len(needing_action),
        "total_accounts": len(scored),
        "pipeline_value_in_motion": pipeline_value_in_motion,
        "customer_health_rate": customer_health_rate,
        "customer_count": len(customers),
        "accounts_in_campaign": db.accounts_in_active_campaign_count(),
        "avg_days_in_stage": avg_days_in_stage,
    }
