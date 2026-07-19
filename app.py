import os
import re
import threading
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from markupsafe import Markup, escape

import db
import scheduler
from pipeline import audience_sync, content_generator, gifting, growth_metrics
from pipeline.flow_diagrams import get_flow
from pipeline.knowledge_base import (
    ACTION_TIER_1_LABEL,
    FUNCTIONAL_AREAS,
    GIFT_TIERS,
    PLAY_ORDER,
    PLAYS,
    SIGNAL_LIBRARY,
    SOURCE_TYPE_LABELS,
)
from pipeline.conceptual_plays import CONCEPTUAL_PLAY_ORDER, CONCEPTUAL_PLAYS, SOURCE_IDEAS
from pipeline.plays import play_groups, score_all_accounts
from pipeline.reporting import build_campaign_report, build_insights
from pipeline.sprint import run_sprint

app = Flask(__name__)


@app.template_filter("bold_md")
def bold_md(text: str) -> Markup:
    escaped = escape(text)
    return Markup(re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", str(escaped)))


@app.route("/")
def dashboard():
    sprints = db.list_sprints()
    settings = db.get_all_settings()
    metrics = growth_metrics.compute()
    teaser = play_groups()[:2]
    return render_template(
        "dashboard.html", sprints=sprints, settings=settings, metrics=metrics, play_teaser=teaser,
    )


@app.route("/plays")
def plays_page():
    return render_template("plays.html", groups=play_groups())


@app.route("/sprint/<int:sprint_id>")
def sprint_detail(sprint_id):
    sprint = db.get_sprint(sprint_id)
    return render_template("sprint_detail.html", sprint=sprint)


@app.route("/account/<int:account_id>")
def account_report(account_id):
    account = db.get_account(account_id)
    if not account:
        return "Not found", 404

    today = datetime.utcnow()
    today_str = today.strftime("%Y-%m-%d")
    raw_signals = db.list_signals_for_account(account_id)
    engaged = db.engaged_contact_count(account_id, today_str)
    from pipeline.scorer import score_account
    scored = score_account(account, raw_signals, engaged, today)
    account.update(scored)

    signals = []
    for s in sorted(scored["decayed_signals"], key=lambda x: x["points_awarded"], reverse=True):
        signals.append({
            **s,
            "label": SIGNAL_LIBRARY[s["signal_type"]]["label"],
            "source_label": SOURCE_TYPE_LABELS.get(s["source_type"], s["source_type"]),
        })

    contacts = db.list_contacts_for_account(account_id)
    grouped = {}
    signal_types = {s["signal_type"] for s in scored["decayed_signals"]}
    for c in contacts:
        eligible, reason = gifting.gift_eligibility(c, account["play"], signal_types, today)
        c["gift_eligible"] = eligible
        c["gift_reason"] = reason
        area = c["functional_area"]
        grouped.setdefault(area, {"label": FUNCTIONAL_AREAS[area]["label"], "contacts": []})
        grouped[area]["contacts"].append(c)

    known_contacts = sum(1 for c in contacts if c["is_known_contact"])
    syncs = {st: db.latest_sync(account["company_name"], st) for st in audience_sync.SYNC_TYPES}
    play = PLAYS[account["play"]]

    return render_template(
        "account_report.html", account=account, signals=signals, grouped_contacts=grouped,
        known_contacts=known_contacts, syncs=syncs, sync_labels=audience_sync.SYNC_TYPES,
        play=play, gift_tiers=GIFT_TIERS,
    )


@app.route("/conceptual-plays")
def conceptual_plays_page():
    plays = [{"key": k, **CONCEPTUAL_PLAYS[k]} for k in CONCEPTUAL_PLAY_ORDER]
    return render_template("conceptual_plays.html", plays=plays, source_ideas=SOURCE_IDEAS)


@app.route("/reporting")
def reporting_page():
    campaigns = [build_campaign_report(c) for c in db.list_campaigns()]
    insights = build_insights(campaigns)
    play_filters = [{"key": k, "label": PLAYS[k]["label"]} for k in PLAY_ORDER]
    return render_template("reporting.html", campaigns=campaigns, insights=insights, play_filters=play_filters)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.route("/api/sprint/run", methods=["POST"])
def api_run_sprint():
    sprint_id = db.create_sprint(datetime.utcnow().isoformat(), "manual")

    def _worker():
        run_sprint(trigger_type="manual", sprint_id=sprint_id)

    threading.Thread(target=_worker, daemon=True).start()
    return jsonify({"sprint_id": sprint_id})


@app.route("/api/sprint/<int:sprint_id>/status")
def api_sprint_status(sprint_id):
    sprint = db.get_sprint(sprint_id)
    if not sprint:
        return jsonify({"error": "not found"}), 404
    return jsonify(sprint)


@app.route("/api/settings", methods=["POST"])
def api_settings():
    data = request.get_json(force=True) or {}
    reschedule_needed = False
    if "sprint_auto_enabled" in data:
        db.set_setting("sprint_auto_enabled", "true" if data["sprint_auto_enabled"] else "false")
        reschedule_needed = True
    if "sprint_cadence_days" in data:
        db.set_setting("sprint_cadence_days", str(int(data["sprint_cadence_days"])))
        reschedule_needed = True
    if reschedule_needed:
        scheduler.refresh_schedule()
    return jsonify(db.get_all_settings())


@app.route("/api/account/<int:account_id>/sync", methods=["POST"])
def api_account_sync(account_id):
    data = request.get_json(force=True) or {}
    sync_type = data.get("sync_type")
    if sync_type not in audience_sync.SYNC_TYPES:
        return jsonify({"error": "sync_type must be 'meta_audience' or 'hubspot_nurture'"}), 400
    account = db.get_account(account_id)
    if not account:
        return jsonify({"error": "not found"}), 404
    today = datetime.utcnow()
    raw_signals = db.list_signals_for_account(account_id)
    engaged = db.engaged_contact_count(account_id, today.strftime("%Y-%m-%d"))
    from pipeline.scorer import score_account
    scored = score_account(account, raw_signals, engaged, today)
    result = audience_sync.record_sync(account_id, account["company_name"], sync_type, "manual", play=scored["play"])
    return jsonify(result)


@app.route("/api/plays/<play_key>/launch", methods=["POST"])
def api_launch_play(play_key):
    data = request.get_json(force=True) or {}
    campaign_name = (data.get("campaign_name") or "").strip() or None
    groups = {g["play"]: g for g in play_groups()}
    group = groups.get(play_key)
    if not group:
        return jsonify({"synced_accounts": 0, "synced_pairs": 0}), 200
    synced_pairs = 0
    for account in group["accounts"]:
        for sync_type in audience_sync.sync_types_for_play(play_key):
            audience_sync.record_sync(
                account["id"], account["company_name"], sync_type, "manual",
                play=play_key, campaign_name=campaign_name,
            )
            synced_pairs += 1
    return jsonify({
        "synced_accounts": len(group["accounts"]), "synced_pairs": synced_pairs,
        "play": group["label"], "campaign_name": campaign_name,
    })


@app.route("/api/contact/<int:contact_id>/gift", methods=["POST"])
def api_send_gift(contact_id):
    data = request.get_json(force=True) or {}
    gift_tier = data.get("gift_tier")
    gift_name = data.get("gift_name", "Selected gift")
    contact = db.get_contact(contact_id)
    if not contact:
        return jsonify({"error": "not found"}), 404
    today = datetime.utcnow()
    gifting.record_gift(contact_id, contact["account_id"], data.get("play", ""), gift_tier, gift_name, today)
    return jsonify({"contact_name": contact.get("contact_name") or contact["title"], "gift_name": gift_name})


@app.route("/api/flow-diagram/<key>")
def api_flow_diagram(key):
    flow = get_flow(key)
    if not flow:
        return jsonify({"error": "not found"}), 404
    return jsonify(flow)


if __name__ == "__main__":
    db.init_db()
    scheduler.start_scheduler()
    mode = content_generator.content_mode()
    if mode == "anthropic":
        print("[startup] ANTHROPIC_API_KEY detected — content generation mode: Anthropic API")
    else:
        print("[startup] No ANTHROPIC_API_KEY set — content generation mode: templated fallback")
    port = int(os.environ.get("PORT", 5051))
    print(f"[startup] TRACTIAN Funnel Intelligence Dashboard running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
