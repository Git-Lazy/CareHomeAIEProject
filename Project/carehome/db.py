import sqlite3
from flask import g

DB_PATH = "carehome.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    id       TEXT PRIMARY KEY,
    name     TEXT NOT NULL,
    type     TEXT NOT NULL,
    location TEXT NOT NULL,
    last_seen DATETIME
);

CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id  TEXT NOT NULL,
    event_type TEXT NOT NULL,
    value      TEXT,
    timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    message      TEXT NOT NULL,
    severity     TEXT NOT NULL CHECK(severity IN ('low','medium','high','critical')),
    device_id    TEXT,
    acknowledged INTEGER NOT NULL DEFAULT 0,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

SEED_DEVICES = [
    ("bedroom_motion",   "Bedroom Motion",   "motion",       "Bedroom"),
    ("bathroom_motion",  "Bathroom Motion",  "motion",       "Bathroom"),
    ("living_motion",    "Living Room Motion","motion",       "Living Room"),
    ("front_door",       "Front Door",       "door",         "Entrance"),
    ("bedroom_temp",     "Bedroom Temp",     "temperature",  "Bedroom"),
    ("bed_sensor",       "Bed Occupancy",    "bed",          "Bedroom"),
    ("panic_button",     "Panic Button",     "panic",        "Living Room"),
]


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


def close_db(e=None):
    db = g.pop("_database", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    for device_id, name, dtype, location in SEED_DEVICES:
        conn.execute(
            "INSERT OR IGNORE INTO devices (id, name, type, location) VALUES (?,?,?,?)",
            (device_id, name, dtype, location),
        )
    conn.commit()
    conn.close()


# ── query helpers ─────────────────────────────────────────────────────────────

def log_event(device_id, event_type, value=None):
    db = get_db()
    db.execute(
        "INSERT INTO events (device_id, event_type, value) VALUES (?,?,?)",
        (device_id, event_type, value),
    )
    db.execute(
        "UPDATE devices SET last_seen = CURRENT_TIMESTAMP WHERE id = ?",
        (device_id,),
    )
    db.commit()


def create_alert(message, severity, device_id=None):
    db = get_db()
    db.execute(
        "INSERT INTO alerts (message, severity, device_id) VALUES (?,?,?)",
        (message, severity, device_id),
    )
    db.commit()


def get_recent_events(limit=50):
    return get_db().execute(
        """SELECT e.id, e.device_id, d.name AS device_name, d.location,
                  e.event_type, e.value, e.timestamp
           FROM events e JOIN devices d ON e.device_id = d.id
           ORDER BY e.timestamp DESC LIMIT ?""",
        (limit,),
    ).fetchall()


def get_active_alerts():
    return get_db().execute(
        "SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY created_at DESC"
    ).fetchall()


def acknowledge_alert(alert_id):
    db = get_db()
    db.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
    db.commit()


def get_all_devices():
    return get_db().execute("SELECT * FROM devices ORDER BY location").fetchall()


def minutes_since_last_motion(device_id):
    row = get_db().execute(
        """SELECT CAST((julianday('now') - julianday(MAX(timestamp))) * 1440 AS INTEGER) AS mins
           FROM events WHERE device_id = ? AND event_type = 'motion_detected'""",
        (device_id,),
    ).fetchone()
    return row["mins"] if row and row["mins"] is not None else None


def last_event_minutes_ago(device_id):
    row = get_db().execute(
        """SELECT CAST((julianday('now') - julianday(MAX(timestamp))) * 1440 AS INTEGER) AS mins
           FROM events WHERE device_id = ?""",
        (device_id,),
    ).fetchone()
    return row["mins"] if row and row["mins"] is not None else None
