from flask import Blueprint, request, jsonify
import db

bp = Blueprint("devices", __name__)


@bp.get("/devices")
def get_devices():
    rows = db.get_all_devices()
    return jsonify([dict(r) for r in rows])


@bp.post("/device")
def register_device():
    data     = request.get_json(force=True)
    dev_id   = data.get("id")
    name     = data.get("name")
    dtype    = data.get("type")
    location = data.get("location")

    if not all([dev_id, name, dtype, location]):
        return jsonify({"error": "id, name, type, and location are required"}), 400

    db.get_db().execute(
        "INSERT OR REPLACE INTO devices (id, name, type, location) VALUES (?,?,?,?)",
        (dev_id, name, dtype, location),
    )
    db.get_db().commit()
    return jsonify({"status": "registered"}), 201


@bp.get("/device/<device_id>")
def get_device(device_id):
    row = db.get_db().execute(
        "SELECT * FROM devices WHERE id = ?", (device_id,)
    ).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))
