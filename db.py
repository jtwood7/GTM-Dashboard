"""SQLite persistence layer. Plain stdlib sqlite3, no ORM, so the schema
stays inspectable with `sqlite3 tractian_funnel.db`.

Architecturally different from the discovery build: accounts here are
PERSISTENT (one row per company, mutated across sprints — stage advances,
health/usage metrics drift, signals accumulate) rather than a new row
inserted per run. There's nothing to discover; the book already exists.
Scores/plays/tiers are never persisted — they're computed live from current
account + signal state every time they're needed (see pipeline/scorer.py),
the same pattern growth_metrics already used successfully in the other app.
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tractian_funnel.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL UNIQUE,
    industry TEXT NOT NULL,
    employee_count INTEGER NOT NULL,
    plant_count INTEGER NOT NULL,
    hq_state TEXT NOT NULL,
    hq_city TEXT NOT NULL DEFAULT '',
    lifecycle_stage TEXT NOT NULL,
    stage_entered_date TEXT NOT NULL,
    owner TEXT NOT NULL DEFAULT '[Assigned Rep]',
    deal_stage TEXT,
    deal_amount REAL,
    close_date TEXT,
    plants_live INTEGER,
    sensors_deployed INTEGER,
    assets_identified INTEGER,
    sensors_contracted INTEGER,
    renewal_date TEXT,
    active_user_ratio REAL,
    alert_to_workorder_rate REAL,
    days_since_last_login INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    signal_type TEXT NOT NULL,
    detail TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_tool TEXT NOT NULL,
    source_url TEXT,
    detected_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    functional_area TEXT NOT NULL,
    title TEXT NOT NULL,
    is_known_contact INTEGER NOT NULL DEFAULT 0,
    contact_name TEXT,
    contact_email TEXT,
    linkedin_url TEXT,
    last_engaged_date TEXT,
    email_subject TEXT,
    email_body TEXT,
    call_script_intro TEXT,
    call_script_notes TEXT,
    linkedin_inmail TEXT,
    gift_tier_low TEXT,
    gift_tier_mid TEXT,
    gift_tier_high TEXT,
    email_variant TEXT,
    simulated_replied INTEGER
);

CREATE TABLE IF NOT EXISTS gifts_sent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL REFERENCES contacts(id),
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    play TEXT NOT NULL,
    gift_tier TEXT NOT NULL,
    gift_name TEXT NOT NULL,
    sent_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audience_syncs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    company_name TEXT NOT NULL,
    sync_type TEXT NOT NULL CHECK(sync_type IN ('meta_audience', 'hubspot_nurture')),
    contact_count INTEGER NOT NULL DEFAULT 0,
    triggered_by TEXT NOT NULL CHECK(triggered_by IN ('manual', 'automatic')),
    play TEXT,
    campaign_name TEXT,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    trigger_type TEXT NOT NULL CHECK(trigger_type IN ('scheduled', 'manual')),
    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'failed')),
    content_mode TEXT NOT NULL DEFAULT 'template',
    accounts_needing_action INTEGER NOT NULL DEFAULT 0,
    error TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

DEFAULT_SETTINGS = {
    "sprint_auto_enabled": "false",
    "sprint_cadence_days": "14",
}

# Columns added after a table's original CREATE — see the discovery build's
# db.py for why this exists (CREATE TABLE IF NOT EXISTS never retrofits an
# existing table). Add here the moment a column gets added to an existing
# table, before it bites a long-running local db.
COLUMN_MIGRATIONS = {
    "audience_syncs": [
        ("campaign_name", "campaign_name TEXT"),
        ("creative_variant", "creative_variant TEXT"),
        ("simulated_impressions", "simulated_impressions INTEGER"),
        ("simulated_clicks", "simulated_clicks INTEGER"),
    ],
    "contacts": [
        ("content_mode", "content_mode TEXT"),
    ],
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _run_column_migrations(conn):
    for table, columns in COLUMN_MIGRATIONS.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for col_name, col_def in columns:
            if col_name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    _run_column_migrations(conn)
    for key, value in DEFAULT_SETTINGS.items():
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# settings
# ---------------------------------------------------------------------------
def get_setting(key: str, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def get_all_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


# ---------------------------------------------------------------------------
# sprints
# ---------------------------------------------------------------------------
def create_sprint(started_at: str, trigger_type: str) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO sprints (started_at, trigger_type, status, accounts_needing_action) "
        "VALUES (?, ?, 'running', 0)",
        (started_at, trigger_type),
    )
    conn.commit()
    sprint_id = cur.lastrowid
    conn.close()
    return sprint_id


def complete_sprint(sprint_id: int, completed_at: str, accounts_needing_action: int, content_mode: str):
    conn = get_db()
    conn.execute(
        "UPDATE sprints SET completed_at = ?, accounts_needing_action = ?, status = 'completed', "
        "content_mode = ? WHERE id = ?",
        (completed_at, accounts_needing_action, content_mode, sprint_id),
    )
    conn.commit()
    conn.close()


def fail_sprint(sprint_id: int, completed_at: str, error: str):
    conn = get_db()
    conn.execute(
        "UPDATE sprints SET completed_at = ?, status = 'failed', error = ? WHERE id = ?",
        (completed_at, error, sprint_id),
    )
    conn.commit()
    conn.close()


def get_sprint(sprint_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM sprints WHERE id = ?", (sprint_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_sprints():
    conn = get_db()
    rows = conn.execute("SELECT * FROM sprints ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# accounts (persistent — insert once, update thereafter)
# ---------------------------------------------------------------------------
def accounts_is_empty() -> bool:
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) as n FROM accounts").fetchone()
    conn.close()
    return row["n"] == 0


def insert_account(account: dict) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO accounts (company_name, industry, employee_count, plant_count, hq_state, hq_city, "
        "lifecycle_stage, stage_entered_date, owner, deal_stage, deal_amount, close_date, plants_live, "
        "sensors_deployed, assets_identified, sensors_contracted, renewal_date, active_user_ratio, "
        "alert_to_workorder_rate, days_since_last_login, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            account["company_name"], account["industry"], account["employee_count"], account["plant_count"],
            account["hq_state"], account.get("hq_city", ""), account["lifecycle_stage"],
            account["stage_entered_date"], account.get("owner", "[Assigned Rep]"),
            account.get("deal_stage"), account.get("deal_amount"), account.get("close_date"),
            account.get("plants_live"), account.get("sensors_deployed"), account.get("assets_identified"),
            account.get("sensors_contracted"), account.get("renewal_date"), account.get("active_user_ratio"),
            account.get("alert_to_workorder_rate"), account.get("days_since_last_login"), account["created_at"],
        ),
    )
    conn.commit()
    account_id = cur.lastrowid
    conn.close()
    return account_id


def update_account_fields(account_id: int, fields: dict):
    """Generic partial update — used by sprint mutation logic (stage
    advances, usage drift) so callers don't need a bespoke setter per field."""
    if not fields:
        return
    conn = get_db()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE accounts SET {set_clause} WHERE id = ?", (*fields.values(), account_id))
    conn.commit()
    conn.close()


def get_account(account_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_account_by_name(company_name: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM accounts WHERE company_name = ?", (company_name,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_accounts():
    conn = get_db()
    rows = conn.execute("SELECT * FROM accounts ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_accounts_by_ids(account_ids: list):
    if not account_ids:
        return []
    conn = get_db()
    placeholders = ",".join("?" for _ in account_ids)
    rows = conn.execute(f"SELECT * FROM accounts WHERE id IN ({placeholders})", account_ids).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# signals (append-only)
# ---------------------------------------------------------------------------
def insert_signal(account_id: int, signal: dict):
    conn = get_db()
    conn.execute(
        "INSERT INTO signals (account_id, signal_type, detail, source_type, source_tool, source_url, "
        "detected_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            account_id, signal["signal_type"], signal["detail"], signal["source_type"],
            signal["source_tool"], signal.get("source_url"), signal["detected_date"],
        ),
    )
    conn.commit()
    conn.close()


def list_signals_for_account(account_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM signals WHERE account_id = ? ORDER BY detected_date DESC", (account_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def signal_type_counts(account_ids: list, n: int = 3):
    if not account_ids:
        return []
    conn = get_db()
    placeholders = ",".join("?" for _ in account_ids)
    rows = conn.execute(
        f"SELECT signal_type, COUNT(*) as n FROM signals WHERE account_id IN ({placeholders}) "
        f"GROUP BY signal_type ORDER BY n DESC LIMIT ?",
        (*account_ids, n),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# contacts (persistent per account)
# ---------------------------------------------------------------------------
def insert_contact(account_id: int, c: dict) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO contacts (account_id, functional_area, title, is_known_contact, contact_name, "
        "contact_email, linkedin_url, last_engaged_date, email_subject, email_body, call_script_intro, "
        "call_script_notes, linkedin_inmail, gift_tier_low, gift_tier_mid, gift_tier_high, email_variant, "
        "simulated_replied) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            account_id, c["functional_area"], c["title"], 1 if c["is_known_contact"] else 0,
            c.get("contact_name"), c.get("contact_email"), c.get("linkedin_url"), c.get("last_engaged_date"),
            c.get("email_subject"), c.get("email_body"), c.get("call_script_intro"),
            json.dumps(c.get("call_script_notes", [])), c.get("linkedin_inmail"),
            json.dumps(c.get("gift_tier_low", {})), json.dumps(c.get("gift_tier_mid", {})),
            json.dumps(c.get("gift_tier_high", {})), c.get("email_variant"),
            1 if c.get("simulated_replied") else 0,
        ),
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid


def update_contact_fields(contact_id: int, fields: dict):
    if not fields:
        return
    conn = get_db()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE contacts SET {set_clause} WHERE id = ?", (*fields.values(), contact_id))
    conn.commit()
    conn.close()


def _deserialize_contact(row) -> dict:
    d = dict(row)
    d["is_known_contact"] = bool(d["is_known_contact"])
    d["call_script_notes"] = json.loads(d["call_script_notes"] or "[]")
    d["gift_tier_low"] = json.loads(d["gift_tier_low"] or "{}")
    d["gift_tier_mid"] = json.loads(d["gift_tier_mid"] or "{}")
    d["gift_tier_high"] = json.loads(d["gift_tier_high"] or "{}")
    return d


def list_contacts_for_account(account_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM contacts WHERE account_id = ? ORDER BY functional_area, id", (account_id,)
    ).fetchall()
    conn.close()
    return [_deserialize_contact(r) for r in rows]


def get_contact(contact_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    conn.close()
    return _deserialize_contact(row) if row else None


def contacts_exist_for_account(account_id: int) -> bool:
    conn = get_db()
    row = conn.execute("SELECT 1 FROM contacts WHERE account_id = ? LIMIT 1", (account_id,)).fetchone()
    conn.close()
    return row is not None


def engaged_contact_count(account_id: int, today_str: str, max_age_days: int = 30) -> int:
    """Contacts engaged within the last max_age_days — the multi-threading
    health input. Computed in Python (not SQL date math) for clarity."""
    from datetime import datetime
    contacts = list_contacts_for_account(account_id)
    today = datetime.strptime(today_str, "%Y-%m-%d")
    count = 0
    for c in contacts:
        if not c["last_engaged_date"]:
            continue
        days_ago = (today - datetime.strptime(c["last_engaged_date"], "%Y-%m-%d")).days
        if 0 <= days_ago <= max_age_days:
            count += 1
    return count


# ---------------------------------------------------------------------------
# gifts_sent (frequency cap + history)
# ---------------------------------------------------------------------------
def insert_gift(contact_id: int, account_id: int, play: str, gift_tier: str, gift_name: str, sent_at: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO gifts_sent (contact_id, account_id, play, gift_tier, gift_name, sent_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (contact_id, account_id, play, gift_tier, gift_name, sent_at),
    )
    conn.commit()
    conn.close()


def last_gift_for_contact(contact_id: int):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM gifts_sent WHERE contact_id = ? ORDER BY sent_at DESC LIMIT 1", (contact_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_gifts_for_account(account_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM gifts_sent WHERE account_id = ? ORDER BY sent_at DESC", (account_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# audience_syncs
# ---------------------------------------------------------------------------
def insert_audience_sync(sync: dict):
    conn = get_db()
    conn.execute(
        "INSERT INTO audience_syncs (account_id, company_name, sync_type, contact_count, triggered_by, "
        "play, campaign_name, synced_at, creative_variant, simulated_impressions, simulated_clicks) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            sync["account_id"], sync["company_name"], sync["sync_type"], sync["contact_count"],
            sync["triggered_by"], sync.get("play"), sync.get("campaign_name"), sync["synced_at"],
            sync.get("creative_variant"), sync.get("simulated_impressions"), sync.get("simulated_clicks"),
        ),
    )
    conn.commit()
    conn.close()


def has_synced(company_name: str, sync_type: str) -> bool:
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM audience_syncs WHERE company_name = ? AND sync_type = ? LIMIT 1",
        (company_name, sync_type),
    ).fetchone()
    conn.close()
    return row is not None


def latest_sync(company_name: str, sync_type: str):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM audience_syncs WHERE company_name = ? AND sync_type = ? ORDER BY synced_at DESC LIMIT 1",
        (company_name, sync_type),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def accounts_in_active_campaign_count() -> int:
    conn = get_db()
    row = conn.execute("SELECT COUNT(DISTINCT company_name) as n FROM audience_syncs").fetchone()
    conn.close()
    return row["n"]


def auto_sync_count_for_sprint(sprint_started_at: str) -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as n FROM audience_syncs WHERE triggered_by = 'automatic' AND synced_at >= ?",
        (sprint_started_at,),
    ).fetchone()
    conn.close()
    return row["n"]


# ---------------------------------------------------------------------------
# campaign reporting — only syncs launched with a campaign_name (i.e.
# deliberate "Launch Play" actions, not the scheduler's quiet auto-fire)
# show up here.
# ---------------------------------------------------------------------------
def list_campaigns():
    conn = get_db()
    rows = conn.execute(
        "SELECT campaign_name, play, MIN(synced_at) as launched_at, "
        "COUNT(DISTINCT account_id) as account_count, SUM(contact_count) as total_contact_syncs "
        "FROM audience_syncs WHERE campaign_name IS NOT NULL "
        "GROUP BY campaign_name ORDER BY launched_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def campaign_account_ids(campaign_name: str) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT account_id FROM audience_syncs WHERE campaign_name = ?", (campaign_name,)
    ).fetchall()
    conn.close()
    return [r["account_id"] for r in rows]


def campaign_gift_count(campaign_name: str) -> int:
    account_ids = campaign_account_ids(campaign_name)
    if not account_ids:
        return 0
    conn = get_db()
    placeholders = ",".join("?" for _ in account_ids)
    row = conn.execute(
        f"SELECT COUNT(*) as n FROM gifts_sent WHERE account_id IN ({placeholders})", account_ids
    ).fetchone()
    conn.close()
    return row["n"]


def campaign_email_stats(campaign_name: str) -> dict:
    account_ids = campaign_account_ids(campaign_name)
    if not account_ids:
        return {"sent": 0, "replies": 0}
    conn = get_db()
    placeholders = ",".join("?" for _ in account_ids)
    row = conn.execute(
        f"SELECT COUNT(*) as n, SUM(simulated_replied) as replies FROM contacts "
        f"WHERE account_id IN ({placeholders}) AND email_body IS NOT NULL",
        account_ids,
    ).fetchone()
    conn.close()
    return {"sent": row["n"], "replies": row["replies"] or 0}


def campaign_email_variant_stats(campaign_name: str) -> dict:
    account_ids = campaign_account_ids(campaign_name)
    if not account_ids:
        return {}
    conn = get_db()
    placeholders = ",".join("?" for _ in account_ids)
    rows = conn.execute(
        f"SELECT email_variant, COUNT(*) as n, SUM(simulated_replied) as replies FROM contacts "
        f"WHERE account_id IN ({placeholders}) AND email_variant IS NOT NULL GROUP BY email_variant",
        account_ids,
    ).fetchall()
    conn.close()
    return {r["email_variant"]: {"n": r["n"], "replies": r["replies"] or 0} for r in rows}


def campaign_creative_stats(campaign_name: str) -> dict:
    conn = get_db()
    rows = conn.execute(
        "SELECT creative_variant, SUM(simulated_impressions) as impressions, "
        "SUM(simulated_clicks) as clicks, COUNT(*) as syncs FROM audience_syncs "
        "WHERE campaign_name = ? AND sync_type = 'meta_audience' AND creative_variant IS NOT NULL "
        "GROUP BY creative_variant",
        (campaign_name,),
    ).fetchall()
    conn.close()
    return {
        r["creative_variant"]: {"impressions": r["impressions"] or 0, "clicks": r["clicks"] or 0, "syncs": r["syncs"]}
        for r in rows
    }


def campaign_contacts_engaged_since(campaign_name: str, since_iso: str) -> int:
    account_ids = campaign_account_ids(campaign_name)
    if not account_ids:
        return 0
    conn = get_db()
    placeholders = ",".join("?" for _ in account_ids)
    since_date = since_iso[:10]
    row = conn.execute(
        f"SELECT COUNT(*) as n FROM contacts WHERE account_id IN ({placeholders}) "
        f"AND last_engaged_date IS NOT NULL AND last_engaged_date >= ?",
        (*account_ids, since_date),
    ).fetchone()
    conn.close()
    return row["n"]


def campaign_accounts_moved(campaign_name: str, since_iso: str) -> dict:
    account_ids = campaign_account_ids(campaign_name)
    if not account_ids:
        return {"moved": 0, "total": 0}
    conn = get_db()
    placeholders = ",".join("?" for _ in account_ids)
    since_date = since_iso[:10]
    row = conn.execute(
        f"SELECT COUNT(*) as n FROM accounts WHERE id IN ({placeholders}) AND stage_entered_date >= ?",
        (*account_ids, since_date),
    ).fetchone()
    conn.close()
    return {"moved": row["n"], "total": len(account_ids)}


def campaign_opportunity_pipeline_value(campaign_name: str) -> float:
    account_ids = campaign_account_ids(campaign_name)
    if not account_ids:
        return 0.0
    conn = get_db()
    placeholders = ",".join("?" for _ in account_ids)
    row = conn.execute(
        f"SELECT SUM(deal_amount) as total FROM accounts "
        f"WHERE id IN ({placeholders}) AND lifecycle_stage = 'Opportunity'",
        account_ids,
    ).fetchone()
    conn.close()
    return row["total"] or 0.0


# ---------------------------------------------------------------------------
# experiment results (CTA A/B test — same mechanic as the discovery build)
# ---------------------------------------------------------------------------
def experiment_results():
    conn = get_db()
    rows = conn.execute(
        "SELECT email_variant, COUNT(*) as n, SUM(simulated_replied) as replies "
        "FROM contacts WHERE email_variant IS NOT NULL GROUP BY email_variant"
    ).fetchall()
    conn.close()
    return {r["email_variant"]: {"n": r["n"], "replies": r["replies"] or 0} for r in rows}
