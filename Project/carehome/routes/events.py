from flask import Blueprint, request, jsonify
import db
from anomaly import run_per_event_checks

bp = Blueprint("events", __name__)


@bp.post("/event")
def post_event():
    data = request.get_json(force=True)
    device_id  = data.get("device_id")
    event_type = data.get("event_type")
    value      = data.get("value")

    if not device_id or not event_type:
        return jsonify({"error": "device_id and event_type are required"}), 400

    db.log_event(device_id, event_type, value)

    # Fetch the row we just inserted for anomaly checks
    row = db.get_db().execute(
        """SELECT e.device_id, e.event_type, e.value, d.location
        FROM events e JOIN devices d ON e.device_id = d.id
        WHERE e.device_id = ? ORDER BY e.id DESC LIMIT 1""",
        (device_id,),
    ).fetchone()

    if row:
        run_per_event_checks(row)

    return jsonify({"status": "ok"}), 201


@bp.get("/events")
def get_events():
    limit = min(int(request.args.get("limit", 50)), 200)
    rows  = db.get_recent_events(limit)
    return jsonify([dict(r) for r in rows])
