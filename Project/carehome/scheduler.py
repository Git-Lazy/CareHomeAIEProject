from apscheduler.schedulers.background import BackgroundScheduler


_scheduler = None


def _periodic_job(app):
    with app.app_context():
        from anomaly import run_periodic_checks
        run_periodic_checks()


def start_scheduler(app):
    global _scheduler
    _scheduler = BackgroundScheduler(daemon=True)
    # Run anomaly checks every 5 minutes
    _scheduler.add_job(_periodic_job, "interval", minutes=5, args=[app])
    _scheduler.start()


def stop_scheduler():
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
