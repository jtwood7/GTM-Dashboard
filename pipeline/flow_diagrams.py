"""Realistic technical integration flows for every mocked action in the app.
Nothing here is called for real — every "Send Gift" / "Sync to Ad Audience"
click still just logs a row — but clicking through shows the actual
architecture that would sit behind it, so it's clear the gap is "no API
keys plugged in yet," not "we don't know how this would work."
"""

FLOW_DIAGRAMS = {
    "gift": {
        "title": "How automated gifting would actually work",
        "mermaid": """flowchart TD
    A[Signal fires: e.g. renewal window approaching] --> B[Gift-readiness check: engaged recently, frequency cap clear]
    B --> C[Clay enriches current mailing address]
    C --> D[Claude drafts a personalized note from account context]
    D --> E[Sendoso API creates the gift order]
    E --> F[Confirmation webhook received]
    F --> G[Logged to HubSpot / Salesforce as an activity]
    G --> H[Slack ping to the assigned AE]""",
    },
    "meta_audience": {
        "title": "How syncing to a Meta Custom Audience would actually work",
        "mermaid": """flowchart TD
    A[Account crosses Needs Action threshold] --> B[Pull known contacts' emails]
    B --> C[Hash emails client-side per Meta spec]
    C --> D[POST to Meta Marketing API customaudiences endpoint]
    D --> E[Meta matches hashed emails to user profiles]
    E --> F[Contacts added to the live ad audience]
    F --> G[Sync status logged back to HubSpot]""",
    },
    "hubspot_nurture": {
        "title": "How enrolling into a HubSpot nurture sequence would actually work",
        "mermaid": """flowchart TD
    A[Account assigned to a play] --> B[Contact upserted via HubSpot Contacts API]
    B --> C[Contact added to a static list scoped to the play]
    C --> D[List membership triggers the matching Workflow]
    D --> E[Workflow enrolls contact in the nurture sequence]
    E --> F[Engagement events flow back via HubSpot webhooks]""",
    },
    "clay_export": {
        "title": "How Clay enrichment would actually work",
        "mermaid": """flowchart TD
    A[Unknown contact: title known, person not identified] --> B[Row pushed to a Clay table]
    B --> C[Clay waterfall: LinkedIn plus data providers]
    C --> D[Clay finds the person currently holding that title]
    D --> E[Contact enriched: name, email, LinkedIn URL]
    E --> F[Synced back into HubSpot / Salesforce]
    F --> G[Contact enters the same outreach sequence]""",
    },
    "surround_outreach": {
        "title": "How single-threaded auto-enrollment would actually work",
        "mermaid": """flowchart TD
    A[HubSpot/Salesforce: single-threaded opportunity detected] --> B[Check functional areas missing from engaged contacts]
    B --> C[Clay finds the missing personas at the account]
    C --> D[New contacts enriched and added to the account]
    D --> E[Claude drafts intro content for each new contact]
    E --> F[Synchronized outreach wave scheduled across contacts]""",
    },
    "account_brief": {
        "title": "How account-brief generation + drafting would actually work",
        "mermaid": """flowchart TD
    A[Account flagged for a play that calls for an overview asset] --> B[Assemble tailored brief content from account industry, footprint, and driving signals]
    B --> C[Canva Connect API renders it into a branded one-pager PDF]
    C --> D[For each known contact: pull their persona-tailored email]
    D --> E[Gmail API creates a draft per contact, asset linked, ready to send]
    E --> F[Rep reviews and sends; logged back to HubSpot as an activity]""",
    },
    "meeting_prep": {
        "title": "How an auto-generated meeting prep brief would actually work",
        "mermaid": """flowchart TD
    A[Rep's calendar: meeting with a tracked account within 24h] --> B[Pull account context: CRM stage, open deal, recent signals]
    B --> C[Pull attendee context: titles, engagement history, prior touches]
    C --> D[Claude drafts a one-page prep brief: talking points, likely objections, suggested next step]
    D --> E[Attached to the calendar invite]
    E --> F[Slacked to the rep the morning of the meeting]""",
    },
    "no_show_recovery": {
        "title": "How automated no-show recovery would actually work",
        "mermaid": """flowchart TD
    A[Zoom/Meet API: host joined, invitee never joined] --> B[Wait-and-confirm: 10 min grace period, then mark no-show]
    B --> C[Pull deal/account context for framing]
    C --> D[Claude drafts a re-engagement email plus LinkedIn touch, reschedule link included]
    D --> E[Queued in HubSpot sequence within the hour]
    E --> F[Rep notified in Slack with a one-click reschedule option]""",
    },
    "mutual_action_plan": {
        "title": "How an auto-drafted Mutual Action Plan would actually work",
        "mermaid": """flowchart TD
    A[Salesforce: deal advances into late-stage Opportunity] --> B[Pull deal size, segment, and close-date target]
    B --> C[Claude assembles a MAP draft from typical milestones for this deal size/segment]
    C --> D[Shared as a live doc with the full buying committee, owners assigned per milestone]
    D --> E[Milestone due dates tracked against actual activity]
    E --> F[Slippage on any milestone triggers an AE alert]""",
    },
}


def get_flow(key: str) -> dict:
    return FLOW_DIAGRAMS.get(key)
