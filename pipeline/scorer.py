"""Action Score = STAGE_RISK/EXPANSION_OPPORTUNITY (0-40) + THREADING_HEALTH
(0-20) + SIGNAL_URGENCY (0-40) -> total, tier, play.

Customer-stage accounts run through a health gate first (best practice:
don't score an expansion opportunity on an unhealthy account) — if the gate
fails, the account is force-routed to Win-Back Risk regardless of what
expansion signals are present, since fixing adoption comes before selling
more.
"""
from datetime import datetime

from pipeline.knowledge_base import (
    PLAY_ORDER,
    PLAYS,
    SIGNAL_LIBRARY,
    STAGE_SCOPE_ANY,
    STAGE_SCOPE_CUSTOMER,
    STAGE_SCOPE_OPPORTUNITY,
    action_tier_for_score,
    decay_multiplier,
    passes_health_gate,
    score_expansion_opportunity,
    score_stage_risk,
    score_threading_health,
)

# Same normalization approach as the discovery build: rescale each signal's
# decayed points down into its actual share of the 0-40 SIGNAL_URGENCY
# budget, so "Points Attributed" in the evidence table always sums to
# exactly the signal_urgency component of the total — no invisible
# normalization step happening behind the scenes.
SIGNAL_URGENCY_NORMALIZE_DIVISOR = 2.5
SIGNAL_URGENCY_MAX = 40


def _signal_applies_to_current_stage(signal_type: str, lifecycle_stage: str) -> bool:
    """Signals are generated once and are append-only (see db.py), but an
    account's lifecycle_stage can advance in a later sprint — a Deal Stalled
    In Stage signal from when an account was an Opportunity shouldn't keep
    scoring (or driving messaging) once that account is a Customer. Filtered
    here at scoring time rather than deleted, so the evidence trail stays
    intact; it just stops counting once it no longer applies."""
    scope = SIGNAL_LIBRARY[signal_type]["stage_scope"]
    if scope == STAGE_SCOPE_ANY:
        return True
    if scope == STAGE_SCOPE_OPPORTUNITY:
        return lifecycle_stage == "Opportunity"
    if scope == STAGE_SCOPE_CUSTOMER:
        return lifecycle_stage == "Customer"
    return True


def apply_recency_decay(signal_type: str, detected_date: str, today: datetime) -> float:
    detected = datetime.strptime(detected_date, "%Y-%m-%d")
    days_old = (today - detected).days
    base_points = SIGNAL_LIBRARY[signal_type]["points"]
    return round(base_points * decay_multiplier(days_old), 1)


def attribute_signal_points(decayed_signals: list) -> tuple:
    raw_sum = sum(s["points_awarded"] for s in decayed_signals)
    if raw_sum <= 0:
        return 0.0, decayed_signals
    normalized = raw_sum / SIGNAL_URGENCY_NORMALIZE_DIVISOR
    if normalized <= SIGNAL_URGENCY_MAX:
        scale = 1 / SIGNAL_URGENCY_NORMALIZE_DIVISOR
        signal_urgency = round(normalized, 1)
    else:
        scale = SIGNAL_URGENCY_MAX / raw_sum
        signal_urgency = float(SIGNAL_URGENCY_MAX)
    attributed = [{**s, "points_awarded": round(s["points_awarded"] * scale, 1)} for s in decayed_signals]
    return signal_urgency, attributed


def assign_play(decayed_signals: list, forced_play: str = None) -> str:
    """Whichever play's driving signals contribute the most decayed points
    wins; ties break toward the play listed first in PLAY_ORDER. forced_play
    overrides everything — used when a Customer account fails its health
    gate, which routes to Win-Back Risk regardless of other signals."""
    if forced_play:
        return forced_play

    play_scores = {p: 0.0 for p in PLAY_ORDER}
    for sig in decayed_signals:
        for play_key, pdef in PLAYS.items():
            if sig["signal_type"] in pdef["driving_signals"]:
                play_scores[play_key] += sig["points_awarded"]

    best = max(play_scores.values())
    if best > 0:
        for play_key in PLAY_ORDER:
            if play_scores[play_key] == best:
                return play_key
    return PLAY_ORDER[0]


def score_account(account: dict, raw_signals: list, engaged_contact_count: int, today: datetime) -> dict:
    """raw_signals: list of {signal_type, detail, source_type, source_tool,
    source_url, detected_date} (no points yet).

    Returns dict with: stage_risk_or_expansion, threading_health,
    signal_urgency, total_score, tier, play, health_gate_passed (None if not
    a Customer account), decayed_signals (attributed, expired ones removed).
    """
    decayed_signals = []
    for sig in raw_signals:
        if not _signal_applies_to_current_stage(sig["signal_type"], account["lifecycle_stage"]):
            continue
        points = apply_recency_decay(sig["signal_type"], sig["detected_date"], today)
        if points <= 0:
            continue
        decayed_signals.append({**sig, "points_awarded": points})

    forced_play = None
    health_gate_passed = None
    if account["lifecycle_stage"] == "Customer":
        health_gate_passed = passes_health_gate(
            account["active_user_ratio"], account["alert_to_workorder_rate"], account["days_since_last_login"]
        )
        if not health_gate_passed:
            forced_play = "win_back_risk"

    play = assign_play(decayed_signals, forced_play=forced_play)
    signal_urgency, attributed_signals = attribute_signal_points(decayed_signals)
    threading_health = score_threading_health(engaged_contact_count)

    if account["lifecycle_stage"] == "Customer":
        if health_gate_passed:
            stage_component = score_expansion_opportunity(
                account["plants_live"], account["plant_count"], account["sensors_deployed"],
                account["assets_identified"],
                account["sensors_deployed"] / account["sensors_contracted"] if account["sensors_contracted"] else 1.0,
            )
        else:
            stage_component = 40  # unhealthy customer = max urgency contribution, needs action now
    else:
        days_in_stage = (today - datetime.strptime(account["stage_entered_date"], "%Y-%m-%d")).days
        stage_component = score_stage_risk(days_in_stage, account["lifecycle_stage"])

    total_score = round(stage_component + threading_health + signal_urgency, 1)
    tier = action_tier_for_score(total_score)

    return {
        "stage_risk_or_expansion": stage_component,
        "threading_health": threading_health,
        "signal_urgency": signal_urgency,
        "total_score": total_score,
        "tier": tier,
        "play": play,
        "health_gate_passed": health_gate_passed,
        "decayed_signals": attributed_signals,
    }
