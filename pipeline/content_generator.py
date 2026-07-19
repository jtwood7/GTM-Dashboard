"""Generates the 4 outreach artifacts (email, call script, LinkedIn InMail,
gift suggestions) for every contact.

Every artifact follows the same hypothesis framework (see messaging.py):
signal -> operational implication -> this persona's specific priority ->
TRACTIAN value. The goal is never personalization for its own sake — it's a
credible, specific answer to "why does this person need to hear from us
this week?" on an account that's already warm, not a cold-outreach pitch.
Names we don't have (the rep, an unidentified contact) are always left as
literal "[Your Name]" / "[Contact Name]" placeholders rather than invented.

Uses the Anthropic API when ANTHROPIC_API_KEY is set (one structured-JSON
call per contact, carrying the same business context and framework as the
template path). Falls back to the templated generator — built directly
from messaging.py's lookup tables, so it's structurally specific by
construction — so the app fully works with zero API key.
"""
import json
import os
import random

from pipeline.knowledge_base import ANTHROPIC_MODEL, FUNCTIONAL_AREAS, PLAYS, SIGNAL_LIBRARY
from pipeline.messaging import (
    EMAIL_CTA_EXPERIMENT,
    INDUSTRY_CHALLENGE,
    SIGNAL_GERUND,
    SIGNAL_IMPLICATION,
    SIGNAL_TRIGGER_VERB,
    STAGE_FALLBACK_IMPLICATION,
    title_frame,
)

_anthropic_client = None
_anthropic_checked = False


def anthropic_available() -> bool:
    global _anthropic_client, _anthropic_checked
    if _anthropic_checked:
        return _anthropic_client is not None
    _anthropic_checked = True
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return False
    try:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
        return True
    except Exception:
        _anthropic_client = None
        return False


def content_mode() -> str:
    return "anthropic" if anthropic_available() else "template"


# ---------------------------------------------------------------------------
# Internal rep-facing language (call-script notes), not sent to the contact.
# ---------------------------------------------------------------------------
PERSONA_TONE = {
    "reliability_maintenance": "practical, peer-to-peer, technical",
    "plant_operations": "operational, ROI-and-timeline focused",
    "executive_buyer": "concise, business-outcome focused, no jargon",
    "digital_transformation": "systems/architecture focused, forward-looking",
}

OBJECTIONS = {
    "reliability_maintenance": [
        "\"We already have sensors on our most critical assets.\"",
        "\"Our CMMS already tracks this.\"",
    ],
    "plant_operations": [
        "\"I don't own the maintenance budget.\"",
        "\"We just don't have bandwidth for a new rollout right now.\"",
    ],
    "executive_buyer": [
        "\"We already have a reliability program underway.\"",
        "\"Need to see hard ROI before I'll sponsor another tool.\"",
    ],
    "digital_transformation": [
        "\"How does this integrate with what we already run?\"",
        "\"We're consolidating vendors, not adding one.\"",
    ],
}

NEXT_STEPS = [
    "a 15-minute call to see the platform against a real asset from their plant",
    "sending a 2-minute product walkthrough video, no meeting required yet",
    "a short call with their reliability lead to compare notes on current pain points",
]

GIFTS = {
    "reliability_maintenance": {
        "<$35": [
            {"gift_name": "Leatherman Wingman multi-tool", "why": "a durable multi-tool that earns a permanent spot in a maintenance kit, keeping the sender top of mind on the floor"},
            {"gift_name": "\"Reliability Centered Maintenance\" pocket field guide", "why": "a practical reference a reliability engineer would actually keep on their desk"},
        ],
        "$36-$85": [
            {"gift_name": "FLIR-style thermal imaging keychain camera", "why": "a novel, on-theme gadget for someone whose job is finding problems before they show up"},
            {"gift_name": "Milwaukee inspection camera", "why": "a genuinely useful field tool that reinforces the 'see problems before they escalate' pitch"},
        ],
        "$86-$150": [
            {"gift_name": "High-end mechanic's tool roll + engraved multitool set", "why": "a premium, personal-use gift that signals real investment in the relationship, not a generic swag drop"},
            {"gift_name": "Noise-cancelling headphones rated for industrial environments", "why": "practical for plant-floor walks and calls, a gift that gets used weekly"},
        ],
    },
    "plant_operations": {
        "<$35": [
            {"gift_name": "Insulated plant-branded travel mug + local coffee gift card", "why": "small, useful for someone who's on their feet moving between the floor and the office all day"},
            {"gift_name": "Pocket notebook + fine-tip marker set", "why": "practical for someone constantly taking notes on walkthroughs"},
        ],
        "$36-$85": [
            {"gift_name": "Portable phone charger/power bank, ruggedized", "why": "useful for a plant manager who's rarely at a desk near an outlet"},
            {"gift_name": "Noise-cancelling earbuds", "why": "practical for someone splitting time between a loud floor and calls"},
        ],
        "$86-$150": [
            {"gift_name": "Curated local restaurant gift card for a team lunch", "why": "lets them share the gesture with the floor team they lead, which lands better than a personal item at this level"},
            {"gift_name": "High-quality insulated cooler/lunch bag", "why": "a practical, daily-use item for someone who's rarely at a desk"},
        ],
    },
    "executive_buyer": {
        "<$35": [
            {"gift_name": "Well-reviewed business book on operational excellence", "why": "on-theme without being salesy, appropriate for a first touch with an economic buyer"},
            {"gift_name": "Premium notebook + pen set", "why": "understated and appropriate for an executive-level first gesture"},
        ],
        "$36-$85": [
            {"gift_name": "Curated coffee/tea gift box", "why": "a tasteful, low-pressure gesture appropriate for someone senior who gets a lot of vendor outreach"},
            {"gift_name": "Desk-plant or succulent arrangement for the office", "why": "understated, appropriate for an exec's office, not overtly promotional"},
        ],
        "$86-$150": [
            {"gift_name": "Private car service gift card for their next site visit or conference", "why": "practical for a traveling executive and memorable without being extravagant"},
            {"gift_name": "High-end desk accessory (leather portfolio or similar)", "why": "an executive-appropriate gesture that signals the relationship is worth investing in"},
        ],
    },
    "digital_transformation": {
        "<$35": [
            {"gift_name": "Smart LED desk lamp with USB charging", "why": "on-theme with a 'connected systems' pitch, useful at a desk"},
            {"gift_name": "\"The Fourth Industrial Revolution\" book", "why": "directly relevant to their Industry 4.0 mandate, a credible non-salesy gesture"},
        ],
        "$36-$85": [
            {"gift_name": "Wireless charging stand + portable hub", "why": "a small nod to 'connected systems' that's genuinely useful at a desk"},
            {"gift_name": "Mechanical keyboard, well-reviewed", "why": "a thoughtful, personal-use gift appropriate for a technical/IT persona"},
        ],
        "$86-$150": [
            {"gift_name": "Tablet stand + stylus bundle for on-floor system walkthroughs", "why": "useful for someone who has to demo or review dashboards live on the floor"},
            {"gift_name": "Noise-cancelling headphones, premium tier", "why": "a higher-end personal-use gift appropriate for a program-lead level contact"},
        ],
    },
}


def _clean_detail(detail: str) -> str:
    return detail.rstrip(".")


def _customer_facing_industry(industry: str) -> str:
    return industry.replace(" (General)", "").lower()


def _second_signal(account: dict, top_signal: dict) -> dict:
    sigs = account.get("decayed_signals", [])
    top_type = top_signal["signal_type"] if top_signal else None
    remaining = [s for s in sigs if s.get("signal_type") != top_type]
    remaining.sort(key=lambda s: s["points_awarded"], reverse=True)
    return remaining[0] if remaining else None


def _deal_context_clause(account: dict) -> str:
    """Extra account-specific texture for Opportunity-stage accounts —
    naming the actual deal size/stage, not just the signal."""
    if account["lifecycle_stage"] == "Opportunity" and account.get("deal_amount"):
        return f" (currently a ${account['deal_amount']:,.0f} opportunity in {account['deal_stage']})"
    return ""


def _trigger_clause(company: str, account: dict, top_signal: dict) -> str:
    """Short clause naming the actual trigger — used standalone in the call
    script/InMail; the email uses the longer _trigger_paragraph below."""
    if not top_signal:
        return f"been in {account['lifecycle_stage']} without a fresh signal recently"
    verb = SIGNAL_TRIGGER_VERB.get(top_signal["signal_type"], "had some relevant recent activity")
    return f"{company} recently {verb}"


def _trigger_paragraph(company: str, account: dict, top_signal: dict, second_signal: dict) -> str:
    if not top_signal:
        return f"{company} has been sitting in {account['lifecycle_stage']} without a fresh signal in the last 30 days."
    verb = SIGNAL_TRIGGER_VERB.get(top_signal["signal_type"], "had some relevant recent activity")
    deal_context = _deal_context_clause(account)
    second_clause = ""
    if second_signal:
        gerund = SIGNAL_GERUND.get(second_signal["signal_type"])
        if gerund:
            second_clause = f", while also {gerund}"
    return f"Saw that {company} recently {verb}{deal_context}{second_clause}."


def _implication_sentence(account: dict, top_signal: dict) -> str:
    if top_signal:
        return SIGNAL_IMPLICATION.get(top_signal["signal_type"], "")
    return STAGE_FALLBACK_IMPLICATION.get(account["lifecycle_stage"], "")


def _template_content(contact: dict, account: dict, top_signal: dict, play_key: str, variant: dict) -> dict:
    area = contact["functional_area"]
    title = contact["title"]
    frame = title_frame(title)
    first_name = contact["contact_name"].split()[0] if contact.get("contact_name") else None
    greeting_name = first_name or "[Contact Name]"
    company = account["company_name"]
    industry_lower = _customer_facing_industry(account["industry"])
    second_signal = _second_signal(account, top_signal)
    signal_label = SIGNAL_LIBRARY.get(top_signal["signal_type"], {}).get("label") if top_signal else None

    # --- Email: trigger -> implication/persona priority -> TRACTIAN value -> CTA ---
    trigger_para = _trigger_paragraph(company, account, top_signal, second_signal)
    implication = _implication_sentence(account, top_signal)
    industry_challenge = INDUSTRY_CHALLENGE.get(account["industry"])
    implication_para = f"{implication} For a {title}, that usually comes down to {frame['cares_about']}."
    if industry_challenge:
        implication_para += f" That's especially true in {industry_lower}, where {industry_challenge}."
    value_para = f"That's the gap TRACTIAN closes for teams like yours — it {frame['value']}."

    cta_line = variant["cta_template"].format(short_focus=frame["short_focus"])
    subject = f"{frame['short_focus'][0].upper() + frame['short_focus'][1:]} at {company}"
    body = (
        f"Hi {greeting_name},\n\n"
        f"{trigger_para}\n\n"
        f"{implication_para}\n\n"
        f"{value_para}\n\n"
        f"{cta_line}\n\n"
        f"Best,\n[Your Name]\nTRACTIAN"
    )

    # --- Call script: one natural, punchy opening sentence + rep notes ---
    trigger_clause = _trigger_clause(company, account, top_signal)
    intro_line = (
        f"Hi {greeting_name}, this is [Your Name] with TRACTIAN — we help {industry_lower} plants "
        f"catch equipment problems before they cause downtime — saw that {trigger_clause}, so wanted "
        f"to check whether {frame['short_focus']} is on your plate right now — got 30 seconds?"
    )
    signal_detail_note = _clean_detail(top_signal["detail"]) if top_signal else "no fresh signal in the last 30 days"
    notes = [
        f"**Pain to probe:** {frame['cares_about']}.",
        f"**Signal to reference:** {signal_label or 'stage and account context'} — {signal_detail_note}.",
        f"**Likely objection:** {random.choice(OBJECTIONS[area])}",
        f"**Next step ask:** Propose {random.choice(NEXT_STEPS)}.",
        f"**Tone:** Keep it {PERSONA_TONE[area]}.",
    ]

    # --- LinkedIn InMail: short, same hypothesis, low-pressure ask ---
    inmail = (
        f"Hi {greeting_name} — saw that {trigger_clause}. {implication} "
        f"Curious whether {frame['short_focus']} is on your radar — worth a quick look?"
    )

    gift_low = random.choice(GIFTS[area]["<$35"])
    gift_mid = random.choice(GIFTS[area]["$36-$85"])
    gift_high = random.choice(GIFTS[area]["$86-$150"])

    return {
        "email_subject": subject,
        "email_body": body,
        "call_script_intro": intro_line,
        "call_script_notes": notes,
        "linkedin_inmail": inmail,
        "gift_tier_low": {"gift_name": gift_low["gift_name"], "justification": gift_low["why"].capitalize() + "."},
        "gift_tier_mid": {"gift_name": gift_mid["gift_name"], "justification": gift_mid["why"].capitalize() + "."},
        "gift_tier_high": {"gift_name": gift_high["gift_name"], "justification": gift_high["why"].capitalize() + "."},
    }


ANTHROPIC_SYSTEM_PROMPT = """You are an experienced B2B growth/sales consultant writing outbound copy \
for TRACTIAN, an industrial AI/IoT platform (condition-monitoring sensors, a modern CMMS, and OEE \
analytics) for manufacturing plants. Every account you write for is ALREADY in the funnel — a known \
lead, an open opportunity, or an existing customer — never a cold prospect. Your only goal: build a \
credible, specific hypothesis for why THIS person, at THIS already-warm account, should hear from us \
THIS WEEK. Follow this process:

1. Read the full account context (lifecycle stage, deal data if applicable, every signal listed, not \
just the strongest one) and translate signals into what they actually imply about deal/account \
momentum. Bad: "Saw your deal has been open a while." Good: "Saw Company's deal has sat in Proposal for \
60 days with only one engaged contact — usually means the champion is trying to build a case alone."
2. Map: signal -> what it implies about deal/account momentum -> this persona's specific priority -> the \
TRACTIAN capability that addresses it. Use the persona hints provided rather than generic messaging — a \
Plant Manager and a VP Operations at the same account should get different emails.
3. Do not open with product features. Open with the account's specific situation: paragraph 1 is the \
trigger + account context (stage, deal size if relevant), paragraph 2 is what it implies and why it \
matters to this persona, paragraph 3 is the TRACTIAN value tied to that, then a low-friction question CTA.
4. This is a warm nudge, not a cold pitch — write like you already have a relationship with this account, \
not like you're introducing yourself for the first time. Avoid generic sales language unless grounded in \
this account's specific context.
5. Before finalizing, silently score your draft 1-10 on: specificity, business relevance, persona \
alignment, TRACTIAN relevance, credibility of the hypothesis. If anything scores below 8, rewrite it. \
Only output the final version — do not show your scoring.

Never invent a name you weren't given. If no contact name is provided, address them as "[Contact Name]" \
literally. Always introduce/sign the rep as "[Your Name]" literally — never invent a rep name. These are \
the only bracket placeholders allowed.

Respond with ONLY a JSON object matching this exact shape, no prose outside the JSON:
{
  "email_subject": str,
  "email_body": str,
  "call_script_intro": str,
  "call_script_notes": [str, str, str, str],
  "linkedin_inmail": str,
  "gift_tier_low": {"gift_name": str, "justification": str},
  "gift_tier_mid": {"gift_name": str, "justification": str},
  "gift_tier_high": {"gift_name": str, "justification": str}
}
email_body is 3 short paragraphs plus a CTA question, signed "[Your Name]" and "TRACTIAN". \
call_script_intro is ONE natural sentence a rep would actually say out loud — introduces "[Your Name]" \
and TRACTIAN, briefly explains what TRACTIAN does, references the account's specific trigger, ends in a \
soft ask. call_script_notes bullets each start with a bold micro-label (e.g. "**Probe:** ..."), covering: \
pain to probe, signal to reference, a likely objection, and a next-step ask. linkedin_inmail is under 80 \
words, not salesy, ends with a low-pressure ask. Gift suggestions must be hyper-specific to the persona, \
each with a one-sentence justification, at tiers "<$35", "$36-$85", "$86-$150". Proofread everything: \
correct grammar, no double punctuation, no sentence fragments, no subject-verb mismatches."""


def _anthropic_content(contact: dict, account: dict, top_signal: dict, play_key: str, variant: dict) -> dict:
    frame = title_frame(contact["title"])
    ordered_signals = sorted(account.get("decayed_signals", []), key=lambda s: s["points_awarded"], reverse=True)
    signals_text = "\n".join(
        f"- {SIGNAL_LIBRARY[s['signal_type']]['label']} ({s['detected_date']}, via {SIGNAL_LIBRARY[s['signal_type']]['source_tool']}): {s['detail']}"
        for s in ordered_signals
    ) or "- No fresh signal in the last 30 days."
    contact_line = (
        f"known contact named {contact['contact_name']}" if contact.get("contact_name")
        else 'no known contact yet — address them as "[Contact Name]"'
    )
    deal_line = (
        f"Deal: ${account['deal_amount']:,.0f}, stage {account['deal_stage']}, target close {account.get('close_date', 'TBD')}.\n"
        if account.get("deal_amount") else ""
    )
    example_cta = variant["cta_template"].format(short_focus=frame["short_focus"])
    play = PLAYS[play_key]
    user_prompt = (
        f"ACCOUNT: {account['company_name']}, industry: {account['industry']}, "
        f"{account['employee_count']} employees, {account['plant_count']} plants, "
        f"lifecycle stage: {account['lifecycle_stage']} (in stage since {account['stage_entered_date']}).\n"
        f"{deal_line}"
        f"PLAY: {play['label']} — {play['angle']}.\n"
        f"SIGNALS (all, strongest first):\n{signals_text}\n"
        f"CONTACT: {contact['title']} ({FUNCTIONAL_AREAS[contact['functional_area']]['label']}), {contact_line}.\n"
        f"What this persona typically cares about day to day: {frame['cares_about']}.\n"
        f"The TRACTIAN value most relevant to them: {frame['value']}.\n"
        f"CTA style for this email (A/B test arm \"{variant['label']}\"): close with something in this "
        f"style, adapted naturally, don't copy verbatim: \"{example_cta}\"\n"
        "Generate the 4 outreach artifacts as JSON, following the hypothesis framework."
    )
    response = _anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=650,
        system=ANTHROPIC_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def _assign_cta_variant() -> tuple:
    variants = EMAIL_CTA_EXPERIMENT["variants"]
    key = random.choice(list(variants.keys()))
    variant = variants[key]
    simulated_replied = random.random() < variant["simulated_reply_rate"]
    return key, variant, simulated_replied


def generate_content(contact: dict, account: dict, top_signal: dict, play_key: str) -> dict:
    variant_key, variant, simulated_replied = _assign_cta_variant()
    if anthropic_available():
        try:
            content = _anthropic_content(contact, account, top_signal, play_key, variant)
        except Exception as e:
            print(f"[content_generator] Anthropic call failed ({e}), falling back to template.")
            content = _template_content(contact, account, top_signal, play_key, variant)
    else:
        content = _template_content(contact, account, top_signal, play_key, variant)
    content["email_variant"] = variant_key
    content["simulated_replied"] = simulated_replied
    return content
