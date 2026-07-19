"""Conceptual plays: ideas that need infrastructure this demo doesn't model
(calendar/video-conferencing data, call transcripts, live document
collaboration) so they aren't wired into the live scoring engine. Each one
runs on a single hand-written example instead of the synthetic active book —
not live, not dynamic — paired with a real integration flow diagram so it's
clear exactly what would need to be connected to make it real.

SOURCE_IDEAS documents where all ten of the brainstormed plays landed: four
already exist as live plays, two became live signals, one folds into an
existing play's tactical mix, and three (below) are genuinely new mechanics.
"""

SOURCE_IDEAS = [
    {"idea": "Opportunity Intelligence Engine", "disposition": "Already live — this is what Velocity Rescue's stall detection plus the whole scoring engine already does."},
    {"idea": "Buying Committee Builder", "disposition": "Already live — this is Buying Committee Expanding, driven by ad/pricing/surge signals."},
    {"idea": "Stalled Opportunity Detector", "disposition": "Already live — this is Velocity Rescue's deal_stalled_in_stage signal."},
    {"idea": "Expansion Opportunity Engine", "disposition": "Already live — this is Renewal & Expansion."},
    {"idea": "Competitive Intelligence Trigger", "disposition": "Now live — added as the competitor_evaluation_activity signal, driving Velocity Rescue and Win-Back Risk."},
    {"idea": "Plant Expansion Trigger", "disposition": "Now live — added as the company_expansion_event signal, driving Velocity Rescue and Renewal & Expansion."},
    {"idea": "Proposal Follow-Up Engine", "disposition": "Folded in — a cadenced follow-up is part of Velocity Rescue's existing tactical mix, not a distinct play."},
    {"idea": "Meeting Prep Generator", "disposition": "Conceptual — needs calendar data this demo doesn't model. See below."},
    {"idea": "No-Show Recovery", "disposition": "Conceptual — needs video-conferencing attendance data this demo doesn't model. See below."},
    {"idea": "Mutual Action Plan Builder", "disposition": "Conceptual — a new content-artifact type (a live shared doc), not just a messaging sequence. See below."},
]

CONCEPTUAL_PLAYS = {
    "meeting_prep": {
        "label": "Meeting Prep Brief",
        "trigger": "A rep's calendar shows a meeting with a tracked account starting within 24 hours.",
        "why_conceptual": "This needs a calendar integration (Google/Outlook) this demo doesn't model — there's no meeting data anywhere in the active book to trigger off of.",
        "flow_key": "meeting_prep",
        "example_account": "Ashgrove Automotive Group",
        "example_meta": "Discovery call — tomorrow, 10:00am — Marcus Webb, Dana Reyes",
        "example_output": [
            {
                "heading": "Attendees",
                "items": [
                    "Marcus Webb — VP of Plant Operations. Champion. Engaged 4x in the last 30 days.",
                    "Dana Reyes — Head of Reliability & Maintenance. Added last week via surround outreach; hasn't seen a live demo yet.",
                ],
            },
            {
                "heading": "Recent signals",
                "items": [
                    "Deal stalled in stage — 38 days in Opportunity, 1.6x the typical time for this stage.",
                    "Single-threaded opportunity resolved this week by adding Reyes to the deal.",
                ],
            },
            {
                "heading": "Talking points",
                "items": [
                    "Ashgrove's stamping line has been called out for unplanned downtime twice in Q2 trade coverage — worth confirming if that's still top of mind.",
                    "Reyes owns reliability KPIs but joined the deal after the last product walkthrough — a 5-minute recap keeps her from feeling behind in the room.",
                    "Webb's original interest was line-down cost avoidance specifically on the stamping line, not the whole plant — keep the pitch scoped there.",
                ],
            },
            {
                "heading": "Anticipated objections",
                "items": [
                    "Budget cycle timing — Ashgrove's fiscal year started 3 months ago, so this may get pushed to next cycle. Worth asking directly.",
                    "\"We already have vibration sensors on critical assets\" — differentiate on condition-based analytics and prescriptive alerts, not sensor coverage alone.",
                ],
            },
            {
                "heading": "Suggested next step",
                "body": "Get a specific downtime-cost figure from Reyes to anchor the ROI conversation, then propose a scoped pilot on the stamping line only.",
            },
        ],
    },
    "no_show_recovery": {
        "label": "No-Show Recovery",
        "trigger": "A video-conferencing integration shows the host joined a scheduled meeting but the prospect never did.",
        "why_conceptual": "This needs a Zoom/Meet attendance-webhook integration this demo doesn't model — there's no meeting-attendance data in the active book.",
        "flow_key": "no_show_recovery",
        "example_account": "Cascade Dairy Group",
        "example_meta": "Discovery call — scheduled 2:00pm today — Priya Shah never joined",
        "example_output": [
            {
                "heading": "Re-engagement email",
                "body": (
                    "Subject: Missed you at 2pm — still want to find 20 minutes?\n\n"
                    "Hi Priya,\n\n"
                    "Looks like today's 2pm didn't connect — no worries, calendars get away from all of us. "
                    "I know Cascade's been dealing with unplanned line stops on the pasteurization side, "
                    "and that's exactly what I wanted to walk through.\n\n"
                    "Here's a link to grab whatever 20-minute window works this week: [reschedule link]\n\n"
                    "Talk soon,\n[Rep Name]"
                ),
            },
            {
                "heading": "LinkedIn touch (sent same day)",
                "body": "Hi Priya — looks like our call today didn't connect, totally understand how that goes. Sent a reschedule link over email whenever's easiest. Would still love to hear how the pasteurization-line downtime situation is trending.",
            },
        ],
    },
    "mutual_action_plan": {
        "label": "Mutual Action Plan Builder",
        "trigger": "A deal advances into late-stage Opportunity in Salesforce without a Mutual Action Plan already on file.",
        "why_conceptual": "This produces a new artifact type — a live, shared document tracked for slippage — not a messaging sequence, and needs a doc-collaboration integration (Notion/Google Docs) this demo doesn't model.",
        "flow_key": "mutual_action_plan",
        "example_account": "Redwood Pulp & Fiber",
        "example_meta": "$184,000 ARR opportunity — Late Opportunity stage",
        "example_output": [
            {
                "heading": "Buying committee",
                "items": [
                    "VP of Operations — economic buyer",
                    "Reliability Manager — champion",
                    "IT / Security — technical evaluator",
                ],
            },
            {
                "heading": "Milestones",
                "items": [
                    "Technical validation call — owner: TRACTIAN SE + Redwood IT — target: this week",
                    "Security review — owner: Redwood IT — target: +7 days",
                    "Pilot scope sign-off — owner: Reliability Manager — target: +10 days",
                    "Executive business case review — owner: VP of Operations — target: +17 days",
                    "Contract redlines — owner: Legal, both sides — target: +24 days",
                    "Signature — target: +30 days",
                ],
            },
            {
                "heading": "Tracking",
                "body": "Shared as a live doc with the full buying committee. Any milestone that slips past its target date triggers an AE alert instead of surfacing silently at the next check-in.",
            },
        ],
    },
}

CONCEPTUAL_PLAY_ORDER = ["meeting_prep", "no_show_recovery", "mutual_action_plan"]
