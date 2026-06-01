from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import db


_scheduler = None


def _periodic_job(app):
    with app.app_context():
        from anomaly import run_periodic_checks
        run_periodic_checks()


def _medication_job(app, name, dose):
    """Fire a medication reminder by creating a low-severity alert."""
    with app.app_context():
        label = f"{name} ({dose})" if dose else name
        db.create_alert(f"Medication reminder: {label} is due.", "low")


def _schedule_medication_reminders(app):
    """Add one cron job per active medication, firing daily at its set time."""
    with app.app_context():
        meds = db.get_active_medications()

    for med in meds:
        try:
            hour, minute = (int(p) for p in med["remind_at"].split(":"))
        except (ValueError, AttributeError):
            print(f"[scheduler] skipping medication {med['name']!r}: "
                  f"bad remind_at {med['remind_at']!r}")
            continue

        _scheduler.add_job(
            _medication_job,
            CronTrigger(hour=hour, minute=minute),
            args=[app, med["name"], med["dose"]],
            id=f"med_{med['id']}",
            replace_existing=True,
        )


def start_scheduler(app):
    global _scheduler
    _scheduler = BackgroundScheduler(daemon=True)
    # Run anomaly checks every 5 minutes
    _scheduler.add_job(_periodic_job, "interval", minutes=5, args=[app])
    # Fire medication reminders at their set times
    _schedule_medication_reminders(app)
    _scheduler.start()


def stop_scheduler():
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
