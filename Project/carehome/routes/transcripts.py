from flask import Blueprint, request, jsonify
import db

bp = Blueprint("transcripts", __name__)


@bp.post("/transcript")
def post_transcript():
    data      = request.get_json(force=True)
    text      = (data.get("text") or "").strip()
    device_id = data.get("device_id") or "tablet_mic"

    if not text:
        return jsonify({"error": "text is required"}), 400

    db.add_transcript(text, device_id)
    return jsonify({"status": "ok"}), 201


@bp.get("/transcripts")
def get_transcripts():
    limit = min(int(request.args.get("limit", 20)), 100)
    rows  = db.get_recent_transcripts(limit)
    return jsonify([dict(r) for r in rows])
