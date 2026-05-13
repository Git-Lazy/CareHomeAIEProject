from flask import Blueprint, jsonify
import db

bp = Blueprint("alerts", __name__)


@bp.get("/alerts")
def get_alerts():
    rows = db.get_active_alerts()
    return jsonify([dict(r) for r in rows])


@bp.post("/alerts/<int:alert_id>/ack")
def ack_alert(alert_id):
    db.acknowledge_alert(alert_id)
    return jsonify({"status": "acknowledged"})
