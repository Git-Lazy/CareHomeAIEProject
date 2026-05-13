"""
Anomaly detection rules.
Each rule receives a raw sqlite3.Row event dict and the Flask app context,
then calls db.create_alert() when a condition is triggered.
"""
from datetime import datetime
import db


# ── per-event rules (called immediately when an event arrives) ────────────────

def check_panic(event):
    if event["event_type"] == "panic_pressed":
        db.create_alert(
            f"PANIC button pressed in {event['location']}!",
            "critical",
            event["device_id"],
        )


def check_night_door(event):
    """Front door opened between midnight and 06:00 is suspicious."""
    if event["device_id"] == "front_door" and event["event_type"] == "door_open":
        hour = datetime.now().hour
        if 0 <= hour < 6:
            db.create_alert(
                "Front door opened during night hours.",
                "high",
                "front_door",
            )


def check_temperature(event):
    if event["event_type"] == "temperature_reading":
        try:
            temp = float(event["value"])
        except (TypeError, ValueError):
            return
        if temp > 28:
            db.create_alert(
                f"High temperature {temp}°C detected in {event['location']}.",
                "medium",
                event["device_id"],
            )
        elif temp < 16:
            db.create_alert(
                f"Low temperature {temp}°C detected in {event['location']}.",
                "medium",
                event["device_id"],
            )


# Called for every incoming event
PER_EVENT_RULES = [check_panic, check_night_door, check_temperature]


def run_per_event_checks(event):
    for rule in PER_EVENT_RULES:
        rule(event)


# ── periodic rules (called by scheduler every few minutes) ───────────────────

NO_MOTION_THRESHOLD_MINS = 480   # 8 hours — no motion anywhere
BATHROOM_STUCK_MINS       = 30   # stuck in bathroom


def check_no_motion_anywhere():
    """Alert if there has been no motion from any sensor for N minutes."""
    motion_devices = ["bedroom_motion", "bathroom_motion", "living_motion"]
    any_recent = False
    for dev_id in motion_devices:
        mins = db.minutes_since_last_motion(dev_id)
        if mins is not None and mins < NO_MOTION_THRESHOLD_MINS:
            any_recent = True
            break
    if not any_recent:
        # Avoid flooding — only create if no unacknowledged alert of this type exists
        existing = [
            a for a in db.get_active_alerts()
            if "no motion" in a["message"].lower()
        ]
        if not existing:
            db.create_alert(
                f"No motion detected anywhere for over {NO_MOTION_THRESHOLD_MINS // 60} hours.",
                "high",
            )


def check_bathroom_duration():
    """Alert if motion was last detected in bathroom but not for a long time (resident may be stuck)."""
    bathroom_mins = db.minutes_since_last_motion("bathroom_motion")
    # Motion was recent in bathroom but nothing since — check if bathroom was last location
    last_bathroom = db.last_event_minutes_ago("bathroom_motion")
    last_bedroom  = db.last_event_minutes_ago("bedroom_motion")
    last_living   = db.last_event_minutes_ago("living_motion")

    if last_bathroom is None:
        return

    others = [m for m in [last_bedroom, last_living] if m is not None]
    if others and last_bathroom < min(others) and last_bathroom > BATHROOM_STUCK_MINS:
        existing = [
            a for a in db.get_active_alerts()
            if "bathroom" in a["message"].lower() and "stuck" in a["message"].lower()
        ]
        if not existing:
            db.create_alert(
                f"Resident may be stuck in bathroom — last motion {last_bathroom} min ago.",
                "high",
                "bathroom_motion",
            )


PERIODIC_RULES = [check_no_motion_anywhere, check_bathroom_duration]


def run_periodic_checks():
    for rule in PERIODIC_RULES:
        try:
            rule()
        except Exception as exc:
            print(f"[anomaly] {rule.__name__} error: {exc}")
