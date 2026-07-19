"""Mock Meta ad creative variants, assigned per Meta Custom Audience sync and
simulated against a CTR — same "hypothesis -> variant -> simulated outcome"
mechanic EMAIL_CTA_EXPERIMENT uses in messaging.py, applied to the paid-ads
side of a launch. No real ad platform connection exists in this demo, so
there's no real creative image to pull back — each variant carries a small
mockup spec (gradient + icon + caption) instead of a real ad image, rendered
as a lightweight preview card. If a real Meta connection existed, this is
exactly where the actual creative thumbnail URL from the Ads API would slot
in instead.
"""
import random

AD_CREATIVE_VARIANTS = {
    "downtime_cost": {
        "label": "Downtime Cost Callout",
        "headline": "Unplanned downtime costs more than the fix.",
        "format": "Static image + stat callout",
        "simulated_ctr": 0.014,
        "mockup_bg": "linear-gradient(135deg, #f97316, #dc2626)",
        "mockup_icon": "⚠️",
        "mockup_caption": "Stat callout: average cost-per-hour of unplanned downtime",
    },
    "before_after": {
        "label": "Before/After Reliability",
        "headline": "See the failure before it happens.",
        "format": "3-panel carousel: alert → work order → resolved",
        "simulated_ctr": 0.021,
        "mockup_bg": "linear-gradient(135deg, #0ea5e9, #1d4ed8)",
        "mockup_icon": "📈",
        "mockup_caption": "Carousel: sensor alert, work order created, issue resolved",
    },
    "customer_proof": {
        "label": "Customer Proof Point",
        "headline": "How similar plants cut downtime 30%.",
        "format": "Video testimonial clip",
        "simulated_ctr": 0.018,
        "mockup_bg": "linear-gradient(135deg, #16a34a, #0d9488)",
        "mockup_icon": "🎥",
        "mockup_caption": "15-second customer testimonial clip",
    },
}


def assign_creative(contact_count: int) -> dict:
    """Called once per Meta sync. Larger synced audiences see proportionally
    more impressions over the flight; clicks are simulated against the
    variant's CTR with some noise so individual syncs vary realistically."""
    key = random.choice(list(AD_CREATIVE_VARIANTS.keys()))
    variant = AD_CREATIVE_VARIANTS[key]
    impressions = max(50, int(max(contact_count, 1) * random.uniform(180, 420)))
    ctr = max(0.001, random.gauss(variant["simulated_ctr"], variant["simulated_ctr"] * 0.25))
    clicks = round(impressions * ctr)
    return {
        "creative_variant": key,
        "simulated_impressions": impressions,
        "simulated_clicks": clicks,
    }
