"""Per-campaign reporting aggregation. Each play has a different objective
(see PLAYS[...]['angle'] in knowledge_base.py), so the metric that actually
proves a campaign worked differs by play — everything here reads back real
stored state (accounts, contacts, signals, syncs), nothing is fabricated for
display.
"""
from datetime import datetime

import db
from pipeline.ad_creative import AD_CREATIVE_VARIANTS
from pipeline.knowledge_base import PLAYS, passes_health_gate

EMAILS_SENT_COLD_THRESHOLD = 10
STALLED_DAYS_THRESHOLD = 7
HEALTH_GATE_ATTENTION_THRESHOLD = 50
CREATIVE_MIN_IMPRESSIONS_FOR_HIGHLIGHT = 500


def _primary_metric(play_key: str, campaign_name: str, launched_at: str, account_ids: list) -> dict:
    if play_key == "velocity_rescue":
        moved = db.campaign_accounts_moved(campaign_name, launched_at)
        return {
            "label": "Accounts Moved Since Launch",
            "value": f"{moved['moved']}/{moved['total']}",
            "detail": (
                "Accounts whose deal stage has changed since this play launched — the direct "
                "measure of whether it actually unstuck anything."
            ),
        }
    if play_key == "buying_committee_expanding":
        engaged = db.campaign_contacts_engaged_since(campaign_name, launched_at)
        return {
            "label": "Net-New Contacts Engaged Since Launch",
            "value": str(engaged),
            "detail": (
                "Contacts at these accounts who've engaged since the play launched — whether "
                "the buying committee is actually broadening, not just being targeted."
            ),
        }
    if play_key == "renewal_expansion":
        value = db.campaign_opportunity_pipeline_value(campaign_name)
        return {
            "label": "Opportunity Pipeline in Campaign",
            "value": f"${value:,.0f}",
            "detail": (
                "Sum of deal_amount across Opportunity-stage accounts in this campaign — the "
                "expansion/renewal revenue actually in motion, not an estimate."
            ),
        }
    if play_key == "win_back_risk":
        accounts = db.list_accounts_by_ids(account_ids)
        customers = [a for a in accounts if a["lifecycle_stage"] == "Customer"]
        if not customers:
            return {
                "label": "Health Gate Pass Rate",
                "value": "—",
                "detail": "No Customer-stage accounts in this campaign yet — nothing to gate-check.",
            }
        passing = sum(
            1 for a in customers
            if passes_health_gate(a["active_user_ratio"], a["alert_to_workorder_rate"], a["days_since_last_login"])
        )
        pct = round(100 * passing / len(customers))
        return {
            "label": "Health Gate Pass Rate (Customer accounts)",
            "value": f"{pct}%",
            "detail": (
                f"{passing} of {len(customers)} Customer-stage accounts in this campaign currently pass "
                "the health gate — the real test of whether re-engagement is actually working, not just "
                "whether outreach went out."
            ),
        }
    return {"label": "Accounts in Campaign", "value": str(len(account_ids)), "detail": ""}


def _creative_summary(campaign_name: str) -> dict:
    stats = db.campaign_creative_stats(campaign_name)
    if not stats:
        return None
    enriched = []
    for key, s in stats.items():
        variant = AD_CREATIVE_VARIANTS.get(key, {})
        ctr = round(100 * s["clicks"] / s["impressions"], 2) if s["impressions"] else 0.0
        enriched.append({
            "key": key,
            "label": variant.get("label", key),
            "headline": variant.get("headline", ""),
            "format": variant.get("format", ""),
            "mockup_bg": variant.get("mockup_bg", "#94a3b8"),
            "mockup_icon": variant.get("mockup_icon", "🖼"),
            "mockup_caption": variant.get("mockup_caption", ""),
            "impressions": s["impressions"],
            "clicks": s["clicks"],
            "ctr": ctr,
        })
    enriched.sort(key=lambda x: x["ctr"], reverse=True)
    return {"variants": enriched, "top": enriched[0]}


def build_campaign_report(c: dict) -> dict:
    play_key = c["play"]
    account_ids = db.campaign_account_ids(c["campaign_name"])
    c["play_label"] = PLAYS.get(play_key, {}).get("label", play_key)
    c["gift_count"] = db.campaign_gift_count(c["campaign_name"])
    email_stats = db.campaign_email_stats(c["campaign_name"])
    c["emails_sent"] = email_stats["sent"]
    c["email_replies"] = email_stats["replies"]
    c["reply_rate"] = round(100 * email_stats["replies"] / email_stats["sent"], 1) if email_stats["sent"] else None
    c["email_variants"] = db.campaign_email_variant_stats(c["campaign_name"])
    c["primary_metric"] = _primary_metric(play_key, c["campaign_name"], c["launched_at"], account_ids)
    c["creative"] = _creative_summary(c["campaign_name"])
    return c


def build_insights(campaigns: list) -> dict:
    needs_attention = []
    highlights = []
    today = datetime.utcnow()

    for c in campaigns:
        name = c["campaign_name"]

        if c["emails_sent"] and c["emails_sent"] >= EMAILS_SENT_COLD_THRESHOLD and c["email_replies"] == 0:
            needs_attention.append(
                f"“{name}” has sent {c['emails_sent']} emails with zero replies — worth "
                "revisiting the messaging."
            )

        if c["play"] == "velocity_rescue":
            try:
                moved, total = (int(v) for v in c["primary_metric"]["value"].split("/"))
            except (ValueError, KeyError):
                moved, total = 0, 0
            launched = datetime.fromisoformat(c["launched_at"])
            days_since = (today - launched).days
            if total > 0 and moved == 0 and days_since >= STALLED_DAYS_THRESHOLD:
                needs_attention.append(
                    f"“{name}” (Velocity Rescue) launched {days_since} days ago and none of "
                    f"its {total} accounts have moved stage yet."
                )

        if c["play"] == "win_back_risk":
            value = c["primary_metric"]["value"]
            if value.endswith("%"):
                pct = int(value.rstrip("%"))
                if pct < HEALTH_GATE_ATTENTION_THRESHOLD:
                    needs_attention.append(
                        f"“{name}” (Win-Back Risk) has only a {pct}% health-gate pass rate "
                        "among its Customer accounts — re-engagement hasn't translated to healthier "
                        "usage yet."
                    )

        if c["creative"] and c["creative"]["top"]["impressions"] >= CREATIVE_MIN_IMPRESSIONS_FOR_HIGHLIGHT:
            top = c["creative"]["top"]
            highlights.append(
                f"“{top['label']}” is the top-performing creative in “{name}” at "
                f"{top['ctr']}% CTR."
            )

        if c["reply_rate"] is not None and c["emails_sent"] >= EMAILS_SENT_COLD_THRESHOLD:
            highlights.append(
                f"“{name}” has a {c['reply_rate']}% simulated reply rate across "
                f"{c['emails_sent']} emails."
            )

    return {"needs_attention": needs_attention[:5], "highlights": highlights[:5]}
