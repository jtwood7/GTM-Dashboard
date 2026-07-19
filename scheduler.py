"""APScheduler wiring for the sprint cadence job (default every 14 days).
Reads sprint_auto_enabled and sprint_cadence_days from the settings table;
call refresh_schedule() any time those change so the job reschedules
without a server restart.
"""
import atexit
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

import db
from pipeline.sprint import run_sprint

JOB_ID = "sprint_cadence"
_scheduler = BackgroundScheduler(daemon=True)


def _run_scheduled_sprint():
    try:
        run_sprint(trigger_type="scheduled", today=datetime.utcnow())
    except Exception as e:
        print(f"[scheduler] scheduled sprint failed: {e}")


def _apply_job():
    if _scheduler.get_job(JOB_ID):
        _scheduler.remove_job(JOB_ID)
    if db.get_setting("sprint_auto_enabled", "false") != "true":
        return
    cadence_days = int(db.get_setting("sprint_cadence_days", "14"))
    _scheduler.add_job(_run_scheduled_sprint, IntervalTrigger(days=cadence_days), id=JOB_ID)


def start_scheduler():
    _apply_job()
    _scheduler.start()
    atexit.register(lambda: _scheduler.shutdown(wait=False))


def refresh_schedule():
    _apply_job()
